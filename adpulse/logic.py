"""
logic.py — deep paid-social analytics core (no Streamlit, no I/O).

Pure functions: validate -> compute metrics -> charts -> recommendations ->
LLM prompt. Everything here is unit-testable in isolation and reusable outside
the dashboard. This is AdPulse's "deep mode" for objective-tagged paid-social
data (the bundled campaign_data.csv schema). Broader single-channel exports are
handled by ``channels.py``.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

REQUIRED_COLS = [
    "date", "campaign_name", "objective", "impressions", "clicks",
    "ctr", "spend_rm", "conversions", "conversion_value_rm",
]

# Objectives whose success is NOT measured by conversions/ROAS. Awareness buys
# reach, so ranking it on ROAS is an apples-to-oranges mistake we guard against.
NON_RESPONSE_OBJECTIVES = {"Awareness"}

OBJ_COLORS = {"Conversions": "#2ecc71", "Awareness": "#9b59b6", "Traffic": "#f39c12"}


def is_deep_format(df: pd.DataFrame) -> bool:
    """True when the frame is the objective-tagged paid-social schema (deep mode)."""
    return set(REQUIRED_COLS).issubset(df.columns)


# --------------------------------------------------------------------------- #
# Validate — sanity-check the raw data before trusting any metric.
# --------------------------------------------------------------------------- #
def validate(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Return a list of (level, message). level in {ok, warn, error}."""
    checks: list[tuple[str, str]] = []

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        checks.append(("error", f"Missing expected columns: {missing}"))
        return checks  # nothing else is safe to check

    n_null = int(df[REQUIRED_COLS].isna().sum().sum())
    checks.append(
        ("ok", "No missing values in any required column.")
        if n_null == 0
        else ("warn", f"{n_null} missing value(s) found across required columns.")
    )

    num_cols = ["impressions", "clicks", "spend_rm", "conversions", "conversion_value_rm"]
    n_neg = int((df[num_cols] < 0).sum().sum())
    checks.append(
        ("ok", "No negative impressions / clicks / spend / conversions.")
        if n_neg == 0
        else ("error", f"{n_neg} negative value(s) in count/spend columns — investigate before reporting.")
    )

    # Recompute CTR and compare to the platform-reported value.
    ctr_calc = (df["clicks"] / df["impressions"]).replace([np.inf, -np.inf], np.nan)
    ctr_gap = (ctr_calc - df["ctr"]).abs()
    max_gap = float(ctr_gap.max())
    n_off = int((ctr_gap > 0.001).sum())
    checks.append(
        ("ok", f"Reported CTR matches clicks/impressions (max gap {max_gap:.5f}). Using recomputed CTR.")
        if n_off == 0
        else ("warn", f"{n_off} row(s) where reported CTR differs from clicks/impressions by >0.001 (max {max_gap:.4f}). Trusting recomputed CTR.")
    )

    bad_clicks = int((df["clicks"] > df["impressions"]).sum())
    bad_conv = int((df["conversions"] > df["clicks"]).sum())
    checks.append(
        ("ok", "Funnel intact: clicks ≤ impressions and conversions ≤ clicks on every row.")
        if (bad_clicks == 0 and bad_conv == 0)
        else ("error", f"Funnel anomaly: {bad_clicks} row(s) clicks>impressions, {bad_conv} row(s) conversions>clicks.")
    )

    # Zero-revenue days — expected for Awareness, flag only so it isn't mistaken for a bug.
    zero_rev = df[df["conversion_value_rm"] == 0]
    if not zero_rev.empty:
        by_obj = zero_rev["objective"].value_counts().to_dict()
        checks.append(
            ("ok", f"{len(zero_rev)} zero-revenue day(s) — all in {by_obj}; expected for non-conversion objectives, not an error.")
        )

    # The key analytical guard: don't judge Awareness on ROAS.
    aw = sorted(set(df["objective"]) & NON_RESPONSE_OBJECTIVES)
    if aw:
        checks.append(
            ("warn", f"Objective–metric mismatch: {aw} campaigns optimise for reach, not sales. "
                     "Evaluate them on CPM / reach, NOT ROAS or CPA.")
        )

    return checks


# --------------------------------------------------------------------------- #
# Compute metrics
# --------------------------------------------------------------------------- #
def campaign_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """One row per campaign with the metrics a campaign manager actually uses."""
    g = (
        df.groupby(["campaign_name", "objective"], as_index=False)
        .agg(
            spend=("spend_rm", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            revenue=("conversion_value_rm", "sum"),
            days=("date", "nunique"),
        )
    )
    return _add_ratios(g).sort_values("spend", ascending=False).reset_index(drop=True)


def _add_ratios(g: pd.DataFrame) -> pd.DataFrame:
    """Derive the rate/efficiency metrics shared by every rollup level."""
    g["CTR"] = g["clicks"] / g["impressions"]
    g["CPC"] = g["spend"] / g["clicks"].replace(0, np.nan)
    g["CPM"] = g["spend"] / g["impressions"] * 1000
    g["CPA"] = g["spend"] / g["conversions"].replace(0, np.nan)
    g["ROAS"] = g["revenue"] / g["spend"].replace(0, np.nan)
    return g


def objective_rollup(df: pd.DataFrame) -> pd.DataFrame:
    """One row per objective (Conversions / Awareness / Traffic).

    Shows where the budget goes by *goal*, not just by campaign — the lens that
    makes the Awareness-vs-Conversions trade-off explicit. ROAS/CPA are still
    computed for every objective, but for Awareness they should be read with the
    objective–metric guard in mind (judge on CPM/reach).
    """
    return objective_rollup_from_roll(campaign_rollup(df))


def objective_rollup_from_roll(roll: pd.DataFrame) -> pd.DataFrame:
    """Same objective-level table, derived from an existing campaign rollup.

    Lets callers that already have ``campaign_rollup`` (e.g. build_prompt) get the
    objective view without re-reading the raw rows.
    """
    g = (
        roll.groupby("objective", as_index=False)
        .agg(
            campaigns=("campaign_name", "nunique"),
            spend=("spend", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            revenue=("revenue", "sum"),
        )
    )
    g = _add_ratios(g)
    g["spend_share"] = g["spend"] / g["spend"].sum()
    return g.sort_values("spend", ascending=False).reset_index(drop=True)


def account_totals(df: pd.DataFrame) -> dict:
    spend = df["spend_rm"].sum()
    rev = df["conversion_value_rm"].sum()
    impr = df["impressions"].sum()
    clicks = df["clicks"].sum()
    return {
        "spend": spend,
        "revenue": rev,
        "blended_roas": rev / spend if spend else np.nan,
        "conversions": int(df["conversions"].sum()),
        "ctr": clicks / impr if impr else np.nan,
        "impressions": int(impr),
        "days": df["date"].nunique(),
    }


def daily_trend(df: pd.DataFrame, campaign: str) -> dict:
    """Linear slope of CTR and conversions over the period for one campaign."""
    d = df[df["campaign_name"] == campaign].sort_values("date")
    x = np.arange(len(d))
    ctr = (d["clicks"] / d["impressions"]).to_numpy()
    conv = d["conversions"].to_numpy()
    ctr_slope = float(np.polyfit(x, ctr, 1)[0]) if len(d) > 1 else 0.0
    conv_slope = float(np.polyfit(x, conv, 1)[0]) if len(d) > 1 else 0.0
    ctr_chg = (ctr[-1] - ctr[0]) / ctr[0] if len(d) > 1 and ctr[0] else 0.0
    conv_chg = (conv[-1] - conv[0]) / conv[0] if len(d) > 1 and conv[0] else 0.0
    return {
        "ctr_slope": ctr_slope,
        "conv_slope": conv_slope,
        "ctr_change_pct": ctr_chg * 100,
        "conv_change_pct": conv_chg * 100,
        # Fatigue: both engagement and response trending down over the window.
        "fatigue": bool(ctr_slope < 0 and conv_slope < 0 and ctr_chg < -0.15),
    }


def fatigue_notes(df: pd.DataFrame, roll: pd.DataFrame) -> list[str]:
    """One note per fatiguing campaign — feeds both the UI and the LLM prompt."""
    notes = []
    for c in roll["campaign_name"]:
        t = daily_trend(df, c)
        if t["fatigue"]:
            notes.append(
                f"{c}: CTR {t['ctr_change_pct']:.0f}% and conversions {t['conv_change_pct']:.0f}% over the period (fatigue)."
            )
    return notes


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def objective_chart(obj: pd.DataFrame):
    """Budget allocation vs efficiency by objective — single-axis scatter.

    x = share of spend, y = ROAS, bubble size = conversions. One y-axis, so the
    break-even line (ROAS = 1×) is unambiguous. The story reads off position:
      - top-left  = efficient, gets little budget (under-funded winners)
      - bottom-right = big budget, below break-even (the reallocation target)
    """
    d = obj.copy()
    d["spend_pct"] = d["spend_share"] * 100
    fig = px.scatter(
        d, x="spend_pct", y="ROAS", size="conversions", color="objective",
        color_discrete_map=OBJ_COLORS, text="objective", size_max=55,
        title="Budget vs efficiency by objective (bubble = conversions)",
        labels={"spend_pct": "Share of spend (%)", "ROAS": "ROAS (×)"},
        hover_data={"objective": False, "spend": ":,.0f", "CPM": ":.2f",
                    "conversions": True, "spend_pct": ":.0f"},
    )
    fig.update_traces(textposition="top center")
    fig.add_hline(y=1, line_dash="dash", line_color="rgba(231,76,60,0.8)",
                  annotation_text="ROAS break-even (1×)", annotation_position="bottom right")
    fig.update_yaxes(range=[0, max(float(d["ROAS"].max()) * 1.25, 1.3)])
    fig.update_xaxes(range=[0, float(d["spend_pct"].max()) * 1.25])
    fig.update_layout(height=380, legend=dict(orientation="h", y=-0.2))
    return fig


def roas_chart(roll: pd.DataFrame):
    d = roll.copy()
    d["label"] = d["campaign_name"].str.slice(0, 26)
    fig = px.bar(
        d, x="ROAS", y="label", orientation="h", color="objective",
        color_discrete_map=OBJ_COLORS, text=d["ROAS"].map(lambda v: f"{v:.1f}×"),
        title="Return on Ad Spend by campaign (break-even = 1×)",
        labels={"ROAS": "ROAS (revenue ÷ spend)", "label": ""},
        hover_data={"spend": ":.0f", "revenue": ":.0f", "CPA": ":.2f"},
    )
    fig.add_vline(x=1, line_dash="dash", line_color="rgba(255,255,255,0.5)",
                  annotation_text="break-even", annotation_position="top")
    fig.update_layout(height=340, legend=dict(orientation="h", y=-0.25),
                      yaxis=dict(categoryorder="total ascending"))
    return fig


def trend_chart(df: pd.DataFrame, campaign: str):
    d = df[df["campaign_name"] == campaign].sort_values("date")
    ctr = d["clicks"] / d["impressions"] * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["date"], y=ctr, name="CTR (%)", mode="lines+markers",
                             line=dict(color="#6C63FF"), yaxis="y"))
    fig.add_trace(go.Scatter(x=d["date"], y=d["conversions"], name="Conversions",
                             mode="lines+markers", line=dict(color="#2ecc71"), yaxis="y2"))
    fig.update_layout(
        title=f"Daily trend — {campaign}",
        yaxis=dict(title="CTR (%)", color="#6C63FF"),
        yaxis2=dict(title="Conversions", overlaying="y", side="right", color="#2ecc71"),
        height=340, legend=dict(orientation="h", y=-0.2),
    )
    return fig


# --------------------------------------------------------------------------- #
# Recommendations — computed in Python so the numbers are trustworthy.
# --------------------------------------------------------------------------- #
def recommendations(df: pd.DataFrame, roll: pd.DataFrame) -> list[str]:
    recs: list[str] = []
    response = roll[~roll["objective"].isin(NON_RESPONSE_OBJECTIVES)]

    # 1. Scale the strongest ROAS conversion campaign.
    best = None
    if not response.empty:
        best = response.loc[response["ROAS"].idxmax()]
        recs.append(
            f"**Scale _{best['campaign_name']}_.** It returns **{best['ROAS']:.1f}× ROAS** "
            f"(RM{best['revenue']:,.0f} on RM{best['spend']:,.0f}) at just **RM{best['CPA']:.0f} CPA** — "
            f"the most efficient line in the account. Shift budget here from weaker campaigns and test raising its daily cap."
        )

    # 2. Fatigue flag.
    for _, row in response.sort_values("spend", ascending=False).iterrows():
        t = daily_trend(df, row["campaign_name"])
        if t["fatigue"]:
            recs.append(
                f"**Refresh _{row['campaign_name']}_ — audience fatigue.** Over the 2 weeks its CTR fell "
                f"**{t['ctr_change_pct']:.0f}%** and daily conversions **{t['conv_change_pct']:.0f}%**, "
                f"a steady decline (not noise). Rotate in new creative and/or widen the audience before ROAS erodes further."
            )
            break

    # 3. Awareness budget — judged on the RIGHT metric (CPM), plus weakest response campaign.
    aw = roll[roll["objective"].isin(NON_RESPONSE_OBJECTIVES)]
    if not aw.empty:
        a = aw.loc[aw["spend"].idxmax()]
        share = a["spend"] / roll["spend"].sum() * 100
        target = best["campaign_name"].split(" - ")[0] if best is not None else "the top"
        recs.append(
            f"**Re-justify _{a['campaign_name']}_ on reach, not sales.** It is **{share:.0f}% of total spend "
            f"(RM{a['spend']:,.0f})** at **RM{a['CPM']:.2f} CPM**. Its {a['ROAS']:.1f}× ROAS is irrelevant — it's an awareness buy. "
            f"Confirm the reach/brand-lift goal is being met; if there's no brand-lift target behind it, reallocate part of this budget to the {target} line."
        )
    elif not response.empty:
        worst = response.loc[response["ROAS"].idxmin()]
        recs.append(
            f"**Fix or cut _{worst['campaign_name']}_.** At **{worst['ROAS']:.1f}× ROAS** and "
            f"RM{worst['CPA']:.0f} CPA it's the weakest responder — optimise the landing page / targeting or reallocate."
        )

    return recs


# --------------------------------------------------------------------------- #
# LLM prompt — constrained, over the *computed* numbers.
# --------------------------------------------------------------------------- #
def build_prompt(totals: dict, roll: pd.DataFrame, notes: list[str],
                 obj: pd.DataFrame | None = None) -> str:
    table = roll[["campaign_name", "objective", "spend", "conversions",
                  "revenue", "CTR", "CPA", "ROAS", "CPM"]].copy()
    table["CTR"] = (table["CTR"] * 100).round(2)
    metric_csv = table.round(2).to_csv(index=False)
    fatigue = "\n".join(f"- {n}" for n in notes) if notes else "- none detected"

    if obj is None:
        obj = objective_rollup_from_roll(roll)
    obj_lines = "\n".join(
        f"- {r['objective']}: {r['spend_share']*100:.0f}% of spend (RM{r['spend']:,.0f}), "
        f"ROAS {r['ROAS']:.2f}x, CPM RM{r['CPM']:.2f}"
        for _, r in obj.iterrows()
    )

    return f"""You are a senior paid-media analyst at a Malaysian digital marketing agency.
Write a short, plain-English performance summary for a campaign manager. Currency is Malaysian Ringgit (RM).

GROUND RULES — follow exactly:
- Use ONLY the numbers given below. Do NOT invent or estimate any figure.
- "Awareness" objective campaigns are optimised for reach, NOT sales. Judge them on CPM/reach.
  Never call an Awareness campaign a failure for having low ROAS or CPA.
- Be specific and cite the exact numbers. No fluff, no generic advice.

ACCOUNT TOTALS (period: {totals['days']} days)
- Total spend: RM{totals['spend']:,.0f}
- Total revenue: RM{totals['revenue']:,.0f}
- Blended ROAS: {totals['blended_roas']:.2f}x
- Total conversions: {totals['conversions']}
- Account CTR: {totals['ctr']*100:.2f}%

SPEND BY OBJECTIVE:
{obj_lines}

PER-CAMPAIGN METRICS (CTR shown in %):
{metric_csv}
TREND FLAGS:
{fatigue}

Respond in EXACTLY this markdown structure:

## Headline
[2-3 sentences: overall account health, the standout winner, and the one thing to fix.]

## What's working
- **[campaign]**: [finding with exact numbers]
- **[campaign]**: [finding with exact numbers]

## What to fix
- **[campaign/issue]**: [specific action + the numbers that justify it]
- **[campaign/issue]**: [specific action + the numbers that justify it]

## Why it matters
[1-2 sentences tying the recommendations to spend efficiency / revenue.]"""
