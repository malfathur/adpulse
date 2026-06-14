"""
channels.py — multi-channel breadth (no Streamlit, no I/O).

Pure functions for single-channel marketing exports: format detection, A–F
benchmark grading, per-channel KPIs, charts, rule-based insights, a CPA-weighted
budget optimizer, and LLM prompt builders. This is AdPulse's "broad mode",
complementing the objective-aware deep analysis in ``logic.py``.

Supported formats: Meta Ads, Google Ads, SEO, Social Media (organic), Influencer.
Benchmarks below are tuned for the Malaysia healthcare/clinic vertical; edit the
``BENCHMARKS`` table to retarget another industry.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLUMN_MAPS = {
    "meta": {
        "campaign": "Campaign name",
        "spend": "Amount spent (MYR)",
        "impressions": "Impressions",
        "clicks": "Clicks (all)",
        "ctr": "CTR (all)",
        "cpc": "CPC (all)",
        "conversions": "Results",
        "cost_per_conversion": "Cost per result",
    },
    "google": {
        "campaign": "Campaign",
        "spend": "Cost",
        "impressions": "Impr.",
        "clicks": "Clicks",
        "ctr": "CTR",
        "cpc": "Avg. CPC",
        "conversions": "Conversions",
        "cost_per_conversion": "Cost / conv.",
    },
    "seo": {
        "keyword": "Query",
        "clicks": "Clicks",
        "impressions": "Impressions",
        "ctr": "CTR",
        "position": "Position",
        "page": "Page",
    },
    "social": {
        "post": "Post",
        "reach": "Reach",
        "impressions": "Impressions",
        "engagement": "Engagement",
        "likes": "Likes",
        "comments": "Comments",
        "shares": "Shares",
        "date": "Date",
    },
    "influencer": {
        "name": "Influencer",
        "platform": "Platform",
        "followers": "Followers",
        "reach": "Reach",
        "engagement_rate": "Engagement Rate (%)",
        "fee": "Fee (MYR)",
        "conversions": "Conversions",
        "cpe": "CPE (MYR)",
    },
}

FORMAT_LABELS = {
    "meta": "Meta Ads",
    "google": "Google Ads",
    "seo": "SEO",
    "social": "Social Media Organic",
    "influencer": "Influencer Campaign",
}

# Malaysia healthcare/clinic industry benchmarks
BENCHMARKS = {
    "meta":       {"ctr": 2.5,  "cpa": 30.0,  "cpc": 2.50},
    "google":     {"ctr": 4.0,  "cpa": 65.0,  "cpc": 3.00},
    "seo":        {"ctr": 5.0,  "position": 8.0},
    "social":     {"engagement_rate": 3.5},
    "influencer": {"engagement_rate": 3.0, "cpe": 120.0},
}

_GRADE_THRESHOLDS = [(88, "A"), (72, "B"), (55, "C"), (38, "D"), (0, "F")]
_GRADE_SUMMARIES = {
    "A": "Exceeding benchmarks",
    "B": "Above average",
    "C": "Meeting benchmarks",
    "D": "Below average",
    "F": "Needs immediate attention",
}
_GRADE_COLORS = {"A": "green", "B": "green", "C": "orange", "D": "red", "F": "red"}

# Channels where a CPA/CPE-weighted budget optimizer is meaningful.
BUDGET_FORMATS = {"meta", "google", "influencer"}


def detect_format(df: pd.DataFrame) -> str:
    cols = set(df.columns)
    if "Campaign name" in cols and "Amount spent (MYR)" in cols:
        return "meta"
    if "Campaign" in cols and "Impr." in cols:
        return "google"
    if "Query" in cols and "Position" in cols:
        return "seo"
    if "Influencer" in cols and "CPE (MYR)" in cols:
        return "influencer"
    if "Post" in cols and "Reach" in cols:
        return "social"
    return "unknown"


def _pct_to_float(series: pd.Series) -> pd.Series:
    try:
        return series.astype(float)
    except (ValueError, TypeError):
        return series.astype(str).str.rstrip("%").astype(float)


def _ratio_score(actual, benchmark, higher_is_better=True) -> float:
    """Returns 0–100 score. Capped so 2× benchmark = 100."""
    if benchmark == 0:
        return 50.0
    ratio = actual / benchmark if higher_is_better else benchmark / actual
    return min(ratio, 2.0) * 50.0


def score_channel(df: pd.DataFrame, fmt: str) -> tuple[str, str, str]:
    """Returns (grade, summary, color)."""
    b = BENCHMARKS.get(fmt, {})
    scores = []

    if fmt == "meta":
        scores.append(_ratio_score(_pct_to_float(df["CTR (all)"]).mean(), b["ctr"]))
        scores.append(_ratio_score(df["Cost per result"].mean(), b["cpa"], higher_is_better=False))
    elif fmt == "google":
        scores.append(_ratio_score(_pct_to_float(df["CTR"]).mean(), b["ctr"]))
        scores.append(_ratio_score(df["Cost / conv."].mean(), b["cpa"], higher_is_better=False))
    elif fmt == "seo":
        scores.append(_ratio_score(_pct_to_float(df["CTR"]).mean(), b["ctr"]))
        scores.append(_ratio_score(df["Position"].mean(), b["position"], higher_is_better=False))
    elif fmt == "social":
        scores.append(_ratio_score(_pct_to_float(df["Engagement Rate (%)"]).mean(), b["engagement_rate"]))
    elif fmt == "influencer":
        scores.append(_ratio_score(_pct_to_float(df["Engagement Rate (%)"]).mean(), b["engagement_rate"]))
        scores.append(_ratio_score(df["CPE (MYR)"].mean(), b["cpe"], higher_is_better=False))

    if not scores:
        return "N/A", "No benchmark", "gray"

    avg = sum(scores) / len(scores)
    for threshold, grade in _GRADE_THRESHOLDS:
        if avg >= threshold:
            return grade, _GRADE_SUMMARIES[grade], _GRADE_COLORS[grade]
    return "F", _GRADE_SUMMARIES["F"], "red"


def calculate_kpis(df: pd.DataFrame, fmt: str) -> dict:
    if fmt == "meta":
        ctr = _pct_to_float(df["CTR (all)"])
        return {
            "Total Spend (MYR)": f"RM {df['Amount spent (MYR)'].sum():,.2f}",
            "Total Impressions": f"{int(df['Impressions'].sum()):,}",
            "Total Clicks": f"{int(df['Clicks (all)'].sum()):,}",
            "Avg CTR": f"{ctr.mean():.2f}%",
            "Total Results": f"{int(df['Results'].sum()):,}",
            "Avg Cost/Result": f"RM {df['Cost per result'].mean():,.2f}",
        }

    if fmt == "google":
        ctr = _pct_to_float(df["CTR"])
        return {
            "Total Spend (MYR)": f"RM {df['Cost'].sum():,.2f}",
            "Total Impressions": f"{int(df['Impr.'].sum()):,}",
            "Total Clicks": f"{int(df['Clicks'].sum()):,}",
            "Avg CTR": f"{ctr.mean():.2f}%",
            "Total Conversions": f"{int(df['Conversions'].sum()):,}",
            "Avg CPA": f"RM {df['Cost / conv.'].mean():,.2f}",
        }

    if fmt == "seo":
        ctr = _pct_to_float(df["CTR"])
        top_kw = df.loc[df["Clicks"].idxmax(), "Query"]
        return {
            "Total Clicks": f"{int(df['Clicks'].sum()):,}",
            "Total Impressions": f"{int(df['Impressions'].sum()):,}",
            "Avg CTR": f"{ctr.mean():.2f}%",
            "Avg Position": f"{df['Position'].mean():.1f}",
            "Top Keyword": top_kw,
            "Keywords Tracked": str(len(df)),
        }

    if fmt == "social":
        er = _pct_to_float(df["Engagement Rate (%)"])
        best = df.loc[df["Engagement"].idxmax(), "Post"]
        return {
            "Total Reach": f"{int(df['Reach'].sum()):,}",
            "Total Impressions": f"{int(df['Impressions'].sum()):,}",
            "Total Engagement": f"{int(df['Engagement'].sum()):,}",
            "Avg Engagement Rate": f"{er.mean():.2f}%",
            "Best Post": best[:35] + "…",
            "Posts Published": str(len(df)),
        }

    if fmt == "influencer":
        er = _pct_to_float(df["Engagement Rate (%)"])
        roi = df["Revenue Generated (MYR)"] / df["Fee (MYR)"]
        best = df.loc[roi.idxmax(), "Influencer"]
        return {
            "Total Fees (MYR)": f"RM {df['Fee (MYR)'].sum():,.2f}",
            "Total Reach": f"{int(df['Reach'].sum()):,}",
            "Total Conversions": f"{int(df['Conversions'].sum()):,}",
            "Avg Engagement Rate": f"{er.mean():.2f}%",
            "Total Revenue (MYR)": f"RM {df['Revenue Generated (MYR)'].sum():,.2f}",
            "Best ROI Influencer": best,
        }

    return {}


def build_chart(df: pd.DataFrame, fmt: str):
    if fmt in ("meta", "google"):
        b = BENCHMARKS[fmt]
        bench_cpa = b["cpa"]

        if fmt == "meta":
            d = df.copy()
            d["CTR_num"] = _pct_to_float(d["CTR (all)"])
            d["CPA"] = d["Cost per result"]
            d["vs Benchmark"] = d["CPA"].apply(
                lambda x: "Below benchmark (efficient)" if x <= bench_cpa else "Above benchmark (costly)"
            )
            spend_col, result_col, name_col = "Amount spent (MYR)", "Results", "Campaign name"
        else:
            d = df.copy()
            d["CTR_num"] = _pct_to_float(d["CTR"])
            d["CPA"] = d["Cost / conv."]
            d["vs Benchmark"] = d["CPA"].apply(
                lambda x: "Below benchmark (efficient)" if x <= bench_cpa else "Above benchmark (costly)"
            )
            spend_col, result_col, name_col = "Cost", "Conversions", "Campaign"

        max_spend = d[spend_col].max() * 1.15
        bench_line_x = [0, max_spend]
        bench_line_y = [0, max_spend / bench_cpa]

        color_map = {
            "Below benchmark (efficient)": "#2ecc71",
            "Above benchmark (costly)": "#e74c3c",
        }
        d["Short Name"] = d[name_col].str[:22] + "…"
        label = "Meta Ads" if fmt == "meta" else "Google Ads"
        fig = px.scatter(
            d,
            x=spend_col,
            y=result_col,
            color="vs Benchmark",
            color_discrete_map=color_map,
            size="CTR_num",
            size_max=32,
            hover_name=name_col,
            title=f"{label} — Spend Efficiency (green = below RM{bench_cpa} CPA benchmark)",
            labels={spend_col: "Spend (MYR)", result_col: "Results / Conversions", "CTR_num": "CTR (%)"},
            hover_data={"CPA": ":.2f", "CTR_num": ":.2f", "vs Benchmark": False},
        )
        # Annotate each point with short name, offset upward
        for _, row in d.iterrows():
            fig.add_annotation(
                x=row[spend_col], y=row[result_col],
                text=row["Short Name"],
                showarrow=False,
                yshift=18,
                font=dict(size=10, color="white"),
                bgcolor="rgba(0,0,0,0.45)",
                borderpad=2,
            )
        fig.add_trace(go.Scatter(
            x=bench_line_x,
            y=bench_line_y,
            mode="lines",
            name=f"Benchmark CPA (RM{bench_cpa})",
            line=dict(dash="dash", color="rgba(255,255,255,0.4)", width=1.5),
        ))
        fig.update_layout(height=480, legend=dict(orientation="h", y=-0.15))
        return fig

    if fmt == "seo":
        d = df.copy()
        d["CTR_num"] = _pct_to_float(d["CTR"])
        bench_pos = BENCHMARKS["seo"]["position"]
        bench_ctr = BENCHMARKS["seo"]["ctr"]
        d["Quadrant"] = d.apply(
            lambda r: "Top performer" if r["Position"] <= bench_pos and r["CTR_num"] >= bench_ctr
            else ("High position, low CTR" if r["Position"] <= bench_pos
                  else ("Low position, high CTR" if r["CTR_num"] >= bench_ctr
                        else "Needs work")),
            axis=1,
        )
        color_map = {
            "Top performer": "#2ecc71",
            "High position, low CTR": "#f39c12",
            "Low position, high CTR": "#3498db",
            "Needs work": "#e74c3c",
        }
        fig = px.scatter(
            d,
            x="Position",
            y="CTR_num",
            size="Clicks",
            color="Quadrant",
            color_discrete_map=color_map,
            hover_name="Query",
            size_max=35,
            title="SEO — Position vs CTR Quadrant (size = clicks)",
            labels={"CTR_num": "CTR (%)", "Position": "Avg Position"},
        )
        fig.update_xaxes(autorange="reversed")
        fig.add_hline(y=bench_ctr, line_dash="dash", line_color="rgba(255,255,255,0.4)",
                      annotation_text=f"CTR benchmark {bench_ctr}%", annotation_position="top right")
        fig.add_vline(x=bench_pos, line_dash="dash", line_color="rgba(255,255,255,0.4)",
                      annotation_text=f"Position benchmark {bench_pos}", annotation_position="top left")
        fig.update_layout(height=450, legend=dict(orientation="h", y=-0.2))
        return fig

    if fmt == "social":
        d = df.copy().sort_values("Date").reset_index(drop=True)
        d["ER"] = _pct_to_float(d["Engagement Rate (%)"])
        bench_er = BENCHMARKS["social"]["engagement_rate"]
        d["vs Benchmark"] = d["ER"].apply(
            lambda x: "Above benchmark" if x >= bench_er else "Below benchmark"
        )
        d["Label"] = d["Post"].str[:32] + "…"
        if "Type" in d.columns:
            d["Label"] = "[" + d["Type"] + "] " + d["Post"].str[:24] + "…"
        color_map = {"Above benchmark": "#2ecc71", "Below benchmark": "#e74c3c"}

        # Horizontal bar — no x-axis label crowding
        fig = px.bar(
            d,
            y="Label",
            x="ER",
            color="vs Benchmark",
            color_discrete_map=color_map,
            orientation="h",
            title=f"Social Media — Engagement Rate by Post (benchmark: {bench_er}%)",
            labels={"ER": "Engagement Rate (%)", "Label": "Post"},
            hover_data={"Reach": True, "Engagement": True, "vs Benchmark": False},
        )

        # Trend line (horizontal orientation: x=trend values, y=labels)
        x_idx = np.arange(len(d))
        z = np.polyfit(x_idx, d["ER"], 1)
        trend_x = np.polyval(z, x_idx)
        slope = z[0]
        direction = "UP" if slope > 0 else "DOWN"
        trend_color = "#2ecc71" if slope > 0 else "#e74c3c"
        fig.add_trace(go.Scatter(
            y=d["Label"],
            x=trend_x,
            mode="lines+markers",
            name=f"Trend ({direction} {abs(slope):.2f}pp/post)",
            marker=dict(size=6, color=trend_color),
            line=dict(color=trend_color, width=2, dash="dot"),
        ))
        fig.add_vline(x=bench_er, line_dash="dash", line_color="rgba(255,255,255,0.5)",
                      annotation_text=f"Benchmark {bench_er}%", annotation_position="top right")
        fig.update_layout(height=420, legend=dict(orientation="h", y=-0.15),
                          yaxis=dict(categoryorder="array", categoryarray=d["Label"].tolist()))
        return fig

    if fmt == "influencer":
        d = df.copy()
        d["ROI"] = (d["Revenue Generated (MYR)"] / d["Fee (MYR)"]).round(2)
        bench_cpe = BENCHMARKS["influencer"]["cpe"]
        d["Label"] = d["Influencer"] + "\n(" + d["Platform"] + ")"
        colors = ["#2ecc71" if v <= bench_cpe else "#e74c3c" for v in d["CPE (MYR)"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Conversions",
            x=d["Label"],
            y=d["Conversions"],
            marker_color=colors,
            customdata=np.stack([d["CPE (MYR)"], d["Fee (MYR)"], d["ROI"], d["Platform"]], axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Conversions: %{y}<br>"
                "CPE: RM%{customdata[0]:.2f}<br>"
                "Fee: RM%{customdata[1]:,.0f}<br>"
                "ROI: %{customdata[2]:.1f}x<extra></extra>"
            ),
        ))
        fig.add_trace(go.Scatter(
            name="ROI (x)",
            x=d["Label"],
            y=d["ROI"],
            yaxis="y2",
            mode="lines+markers",
            marker=dict(color="#f39c12", size=9),
            line=dict(color="#f39c12", width=2),
        ))
        fig.update_layout(
            title=f"Influencer — Conversions & ROI (green = CPE ≤ RM{bench_cpe} benchmark)",
            yaxis=dict(title="Conversions"),
            yaxis2=dict(title="ROI (x)", overlaying="y", side="right"),
            height=440,
            legend=dict(orientation="h", y=-0.18),
            xaxis=dict(tickfont=dict(size=11)),
        )
        return fig

    return None


def calculate_budget_allocation(df: pd.DataFrame, fmt: str, total_budget: float) -> pd.DataFrame:
    """Returns optimised budget split based on CPA/CPE efficiency."""
    if fmt == "meta":
        d = df[["Campaign name", "Amount spent (MYR)", "Cost per result", "Results"]].copy()
        d.columns = ["Campaign", "Current Spend", "CPA", "Current Results"]
    elif fmt == "google":
        d = df[["Campaign", "Cost", "Cost / conv.", "Conversions"]].copy()
        d.columns = ["Campaign", "Current Spend", "CPA", "Current Results"]
    elif fmt == "influencer":
        d = df[["Influencer", "Fee (MYR)", "CPE (MYR)", "Conversions"]].copy()
        d.columns = ["Campaign", "Current Spend", "CPA", "Current Results"]
    else:
        return pd.DataFrame()

    d["Weight"] = 1.0 / d["CPA"]
    d["Recommended Spend"] = (d["Weight"] / d["Weight"].sum() * total_budget).round(2)
    d["Expected Results"] = (d["Recommended Spend"] / d["CPA"]).round(1)
    d["Change (MYR)"] = (d["Recommended Spend"] - d["Current Spend"]).round(2)
    d["Change (%)"] = ((d["Change (MYR)"] / d["Current Spend"]) * 100).round(1)

    return d[["Campaign", "Current Spend", "Recommended Spend", "Expected Results",
              "Change (MYR)", "Change (%)"]].sort_values("Recommended Spend", ascending=False).reset_index(drop=True)


def generate_insights(df: pd.DataFrame, fmt: str) -> list[str]:
    insights = []
    b = BENCHMARKS.get(fmt, {})

    if fmt == "meta":
        cpa = df["Cost per result"]
        best = df.loc[cpa.idxmin()]
        worst = df.loc[cpa.idxmax()]
        bench = b["cpa"]
        below = (cpa <= bench).sum()
        insights.append(
            f"**{below} of {len(df)} campaigns** beat the RM{bench} CPA benchmark — "
            f"best is *{best['Campaign name']}* at RM{best['Cost per result']:.2f}/result."
        )
        insights.append(
            f"**{worst['Campaign name']}** has the highest CPA at RM{worst['Cost per result']:.2f} — "
            f"{((worst['Cost per result']-bench)/bench*100):.0f}% above benchmark. Review targeting or creative."
        )
        paused = df[df["Delivery"] == "Paused"]
        if not paused.empty:
            insights.append(
                f"**{len(paused)} campaign(s) paused** with RM{paused['Amount spent (MYR)'].sum():,.0f} historical spend — "
                f"consider reactivating or reallocating budget."
            )
        ctr = _pct_to_float(df["CTR (all)"])
        best_ctr = df.loc[ctr.idxmax()]
        insights.append(
            f"Highest CTR: *{best_ctr['Campaign name']}* at {ctr.max():.2f}% "
            f"({'above' if ctr.max() >= b['ctr'] else 'below'} {b['ctr']}% benchmark)."
        )

    elif fmt == "google":
        cpa = df["Cost / conv."]
        best = df.loc[cpa.idxmin()]
        worst = df.loc[cpa.idxmax()]
        bench = b["cpa"]
        below = (cpa <= bench).sum()
        insights.append(
            f"**{below} of {len(df)} campaigns** beat the RM{bench} CPA benchmark — "
            f"best is *{best['Campaign']}* at RM{best['Cost / conv.']:.2f}/conv."
        )
        brand = df[df["Campaign"].str.contains("Brand", case=False, na=False)]
        nonbrand = df[~df["Campaign"].str.contains("Brand", case=False, na=False)]
        if not brand.empty and not nonbrand.empty:
            insights.append(
                f"Brand campaigns average RM{brand['Cost / conv.'].mean():.2f} CPA vs "
                f"RM{nonbrand['Cost / conv.'].mean():.2f} for non-brand — "
                f"brand terms are {((nonbrand['Cost / conv.'].mean()-brand['Cost / conv.'].mean())/nonbrand['Cost / conv.'].mean()*100):.0f}% cheaper per conversion."
            )
        paused = df[df["Status"] == "Paused"]
        if not paused.empty:
            insights.append(
                f"**{paused['Campaign'].iloc[0]}** is paused — RM{paused['Cost'].sum():,.0f} in historical spend. "
                f"Review before reactivating."
            )
        insights.append(
            f"Worst performer: *{worst['Campaign']}* at RM{worst['Cost / conv.']:.2f} CPA — "
            f"{((worst['Cost / conv.']-bench)/bench*100):.0f}% above benchmark. Pause or restructure."
        )

    elif fmt == "seo":
        ctr = _pct_to_float(df["CTR"])
        bench_pos, bench_ctr = b["position"], b["ctr"]
        top5 = (df["Position"] <= 5).sum()
        page1 = (df["Position"] <= 10).sum()
        insights.append(
            f"**{top5} keywords in top 5** positions, {page1} on page 1 — "
            f"{len(df)-page1} keyword(s) need position improvement."
        )
        low_ctr = df[(df["Position"] <= bench_pos) & (ctr < bench_ctr)]
        if not low_ctr.empty:
            kws = ", ".join(f"*{k}*" for k in low_ctr["Query"].head(2))
            insights.append(
                f"**{len(low_ctr)} keyword(s) rank well but underperform on CTR** ({kws}) — "
                f"rewrite meta titles/descriptions to improve click-through."
            )
        best_kw = df.loc[df["Clicks"].idxmax()]
        insights.append(
            f"Top traffic driver: *{best_kw['Query']}* with {int(best_kw['Clicks'])} clicks at position {best_kw['Position']:.1f}."
        )
        insights.append(
            f"Average CTR {ctr.mean():.2f}% vs {bench_ctr}% benchmark — "
            f"{'on track' if ctr.mean() >= bench_ctr else 'below target, focus on title tag optimisation'}."
        )

    elif fmt == "social":
        er = _pct_to_float(df["Engagement Rate (%)"])
        bench = b["engagement_rate"]
        above = (er >= bench).sum()
        insights.append(
            f"**{above} of {len(df)} posts** beat the {bench}% engagement benchmark — "
            f"avg ER is {er.mean():.2f}%."
        )
        if "Type" in df.columns:
            by_type = df.copy()
            by_type["ER"] = er
            type_avg = by_type.groupby("Type")["ER"].mean().sort_values(ascending=False)
            best_type = type_avg.index[0]
            insights.append(
                f"**{best_type}** is the top content format at {type_avg.iloc[0]:.2f}% avg ER — "
                f"prioritise this format in next month's content plan."
            )
        best_post = df.loc[df["Engagement"].idxmax()]
        insights.append(
            f"Best post: *{best_post['Post'][:40]}…* — {int(best_post['Engagement'])} engagements, "
            f"{_pct_to_float(pd.Series([best_post['Engagement Rate (%)']])).iloc[0]:.2f}% ER. Repurpose this content."
        )
        insights.append(
            f"Total reach of {int(df['Reach'].sum()):,} with {int(df['Impressions'].sum()):,} impressions — "
            f"avg {(df['Impressions']/df['Reach']).mean():.1f}x frequency per user."
        )

    elif fmt == "influencer":
        bench_cpe = b["cpe"]
        er = _pct_to_float(df["Engagement Rate (%)"])
        efficient = (df["CPE (MYR)"] <= bench_cpe).sum()
        insights.append(
            f"**{efficient} of {len(df)} influencers** beat the RM{bench_cpe} CPE benchmark — "
            f"best is *{df.loc[df['CPE (MYR)'].idxmin(), 'Influencer']}* at RM{df['CPE (MYR)'].min():.2f}/engagement."
        )
        roi = df["Revenue Generated (MYR)"] / df["Fee (MYR)"]
        best_roi = df.loc[roi.idxmax()]
        insights.append(
            f"Best ROI: *{best_roi['Influencer']}* returns RM{roi.max():.1f} for every RM1 spent — "
            f"RM{best_roi['Revenue Generated (MYR)']:,.0f} revenue on RM{best_roi['Fee (MYR)']:,.0f} fee."
        )
        if "Platform" in df.columns:
            by_plat = df.copy()
            by_plat["ER_num"] = er
            plat_avg = by_plat.groupby("Platform")["ER_num"].mean().sort_values(ascending=False)
            insights.append(
                f"**{plat_avg.index[0]}** leads on engagement rate ({plat_avg.iloc[0]:.2f}% avg) — "
                f"shift more budget here vs {plat_avg.index[-1]} ({plat_avg.iloc[-1]:.2f}%)."
            )
        worst_roi = df.loc[roi.idxmin()]
        insights.append(
            f"Lowest ROI: *{worst_roi['Influencer']}* at {roi.min():.1f}x — "
            f"RM{worst_roi['Fee (MYR)']:,.0f} fee yielded only {int(worst_roi['Conversions'])} conversions. Renegotiate or drop."
        )

    return insights


def build_prompt(kpis: dict, df: pd.DataFrame, fmt: str, client_name: str = "the client") -> str:
    kpi_lines = "\n".join(f"- {k}: {v}" for k, v in kpis.items())
    b = BENCHMARKS.get(fmt, {})
    bench_lines = "\n".join(f"- {k}: {v}" for k, v in b.items()) if b else "N/A"
    context = {
        "meta": "Meta Ads (Facebook/Instagram) paid media",
        "google": "Google Ads paid search",
        "seo": "SEO / organic search",
        "social": "Social media organic content",
        "influencer": "Influencer marketing",
    }.get(fmt, "digital marketing")

    return f"""You are a senior digital marketing analyst at a digital marketing agency in Petaling Jaya, Malaysia.

Client: {client_name}
Channel: {context}

KPI Summary:
{kpi_lines}

Malaysia Healthcare Industry Benchmarks:
{bench_lines}

Raw Data:
{df.to_csv(index=False)}

Write a structured performance report using EXACTLY this markdown format:

## Performance Summary
[2–3 sentences on overall performance vs benchmarks]

## Wins
- **[specific metric or campaign]**: [finding with exact number]
- **[specific metric or campaign]**: [finding with exact number]

## Opportunities
- **[issue]**: [specific, actionable recommendation]
- **[issue]**: [specific, actionable recommendation]

## Next Month Action Plan
| Action | Priority | Est. Impact |
|--------|----------|-------------|
| [action] | High/Med/Low | [impact] |
| [action] | High/Med/Low | [impact] |
| [action] | High/Med/Low | [impact] |

Use MYR for currency. Reference benchmarks. Be specific with numbers. No fluff."""


def build_combined_prompt(datasets: dict, client_name: str = "the client") -> str:
    sections = []
    for fmt, (df, kpis) in datasets.items():
        label = FORMAT_LABELS.get(fmt, fmt.upper())
        kpi_lines = "\n".join(f"  - {k}: {v}" for k, v in kpis.items())
        b = BENCHMARKS.get(fmt, {})
        bench = ", ".join(f"{k}={v}" for k, v in b.items())
        sections.append(f"### {label}\n{kpi_lines}\n  Benchmarks: {bench}")

    return f"""You are a senior digital marketing analyst at a digital marketing agency in Petaling Jaya, Malaysia.

Client: {client_name}
Report Type: Full Monthly Performance Report

{chr(10).join(sections)}

Write a structured executive report using EXACTLY this markdown format:

## Executive Summary
[3–4 sentences on overall performance across all channels]

## Channel Highlights
- **Meta Ads**: [1–2 sentences with numbers]
- **Google Ads**: [1–2 sentences with numbers]
- **SEO**: [1–2 sentences with numbers]
- **Social Media**: [1–2 sentences with numbers]

## Top 3 Wins This Month
1. **[win]**: [specific number/result]
2. **[win]**: [specific number/result]
3. **[win]**: [specific number/result]

## Top 3 Priorities for Next Month
1. **[priority]**: [specific action]
2. **[priority]**: [specific action]
3. **[priority]**: [specific action]

## Budget Recommendation
[2–3 sentences on where to shift spend and why, with MYR amounts]

Use MYR. Reference benchmarks where relevant. Be specific and data-driven."""


def build_chat_prompt(history: list[dict], data_context: str, question: str, client_name: str) -> str:
    history_text = ""
    if history:
        lines = [
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history[-6:]
        ]
        history_text = "Previous conversation:\n" + "\n".join(lines) + "\n\n"

    return f"""You are a senior digital marketing analyst. Answer questions about performance data concisely and specifically.

Client: {client_name}

Performance Data:
{data_context}

{history_text}Question: {question}

Answer in 2–4 sentences. Be specific with numbers. Use MYR for currency. If the question is outside the data, say so."""
