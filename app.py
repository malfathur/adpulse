"""
app.py — Streamlit UI for AdPulse.

Thin presentation layer only. All data access lives in `adpulse/data_io.py`;
deep paid-social analytics in `adpulse/logic.py`; multi-channel breadth in
`adpulse/channels.py`. This file just routes inputs to functions to widgets.

Two analysis paths, chosen by the shape of the uploaded data:
  - DEEP mode   — objective-tagged paid-social data (validation, objective rollups,
                  audience-fatigue detection, evidence-based recommendations).
  - CHANNEL mode — single Meta/Google/SEO/Social/Influencer export, or several at
                  once for a combined monthly report (grade, KPIs, chart, insights,
                  budget optimizer).

Both paths end in an LLM report + a follow-up "Ask the Analyst" chat. The whole
dashboard renders even if every Groq key fails — only the AI sections degrade.

Run:  pip install -r requirements.txt && streamlit run app.py
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from adpulse import channels as ch
from adpulse import data_io as dio
from adpulse import logic

st.set_page_config(page_title="AdPulse — Marketing Performance", layout="wide")

DEEP_FILE = os.path.join("data", "campaign_data.csv")
ICON = {"ok": "✅", "warn": "⚠️", "error": "❌"}

# label -> ("deep" | channel fmt | "full")
SAMPLE_MAP = {
    "Paid Social — Deep Analysis": "deep",
    "Meta Ads": "meta",
    "Google Ads": "google",
    "SEO": "seo",
    "Social Media Organic": "social",
    "Influencer Campaign": "influencer",
    "Full Monthly Report (all channels)": "full",
}
FULL_MONTHLY_FORMATS = ["meta", "google", "seo", "social"]


@st.cache_data(show_spinner=False)
def _load(source):
    return dio.load_csv(source)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    client_mode = st.toggle("Client View", value=False,
                            help="Clean presentation mode — hides dev controls and raw data.")
    st.divider()

    if not client_mode:
        st.header("Data")
        uploaded_files = st.file_uploader(
            "Upload CSV(s)", type=["csv"], accept_multiple_files=True,
            help="One file = single channel. Several = combined monthly report.",
        )
        st.caption("Or load a bundled sample below.")
    else:
        uploaded_files = []

    sample_choice = st.selectbox("Sample data", ["—"] + list(SAMPLE_MAP.keys()),
                                 index=1 if client_mode else 0)
    st.divider()
    client_name = st.text_input("Client name", value="Client A")
    generate = st.button("Generate AI report", type="primary", use_container_width=True)


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
if client_mode:
    st.markdown(f"## Performance Report — {client_name}")
    st.caption(f"AdPulse · {pd.Timestamp.now().strftime('%B %Y')}")
else:
    st.title("AdPulse — Marketing Performance Tool")
    st.caption("Multi-channel campaign analytics with AI reporting, benchmark grading, and budget optimization.")


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _fmt_deep(g: pd.DataFrame) -> pd.DataFrame:
    """Human-readable currency / percentage formatting for a deep-mode rollup."""
    s = g.copy()
    s["CTR"] = (s["CTR"] * 100).round(2).astype(str) + "%"
    for col in ["spend", "revenue", "CPC", "CPM", "CPA"]:
        s[col] = s[col].map(lambda v: f"RM {v:,.2f}" if pd.notna(v) else "—")
    s["ROAS"] = s["ROAS"].map(lambda v: f"{v:.2f}×")
    if "spend_share" in s.columns:
        s["spend_share"] = (s["spend_share"] * 100).round(1).astype(str) + "%"
    return s


def _kpi_cards(kpis: dict):
    cols = st.columns(3)
    for i, (label, value) in enumerate(kpis.items()):
        cols[i % 3].metric(label, value)


def _grade_badge(grade: str, summary: str, color: str):
    st.markdown(f"**Performance Grade:** :{color}[**{grade}**] &nbsp; :{color}[{summary}]")


def render_chat(data_context: str, client_name: str):
    """Follow-up Q&A grounded in the current dataset's computed numbers."""
    st.divider()
    st.subheader("Ask the Analyst")
    st.caption("Ask follow-up questions about this data — answered by Groq over the computed metrics.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if question := st.chat_input("e.g. Which campaign should we pause next month?"):
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking…"):
                    prompt = ch.build_chat_prompt(
                        st.session_state.chat_history[:-1], data_context, question, client_name)
                    answer = dio.chat_groq(prompt)
            except Exception as e:
                answer = f"AI chat unavailable ({e}). The dashboard above is fully usable without it."
            st.markdown(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})


# --------------------------------------------------------------------------- #
# DEEP mode — objective-aware paid-social analysis
# --------------------------------------------------------------------------- #
def render_deep(df: pd.DataFrame, client_name: str, generate: bool, client_mode: bool):
    checks = logic.validate(df)
    errors = [m for lvl, m in checks if lvl == "error"]
    if not client_mode:
        with st.expander("Data validation  " + ("— ❌ issues found" if errors else "— ✅ passed"),
                         expanded=bool(errors)):
            for lvl, msg in checks:
                st.markdown(f"{ICON[lvl]} {msg}")
    if errors:
        st.error("Validation found blocking issues — fix the data before trusting the metrics.")
        return

    roll = logic.campaign_rollup(df)
    totals = logic.account_totals(df)
    notes = logic.fatigue_notes(df, roll)
    obj = logic.objective_rollup(df)

    st.subheader("Headline metrics")
    c = st.columns(5)
    c[0].metric("Total spend", f"RM {totals['spend']:,.0f}")
    c[1].metric("Revenue", f"RM {totals['revenue']:,.0f}")
    c[2].metric("Blended ROAS", f"{totals['blended_roas']:.2f}×")
    c[3].metric("Conversions", f"{totals['conversions']:,}")
    c[4].metric("Account CTR", f"{totals['ctr']*100:.2f}%")

    st.divider()
    st.subheader("Where the budget goes — by objective")
    st.plotly_chart(logic.objective_chart(obj), use_container_width=True)
    st.dataframe(
        _fmt_deep(obj)[["objective", "campaigns", "spend", "spend_share", "impressions",
                        "CTR", "CPM", "conversions", "CPA", "revenue", "ROAS"]],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.subheader("Campaign performance")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(logic.roas_chart(roll), use_container_width=True)
    with right:
        default_idx = int(np.argmax([logic.daily_trend(df, c)["fatigue"]
                                     for c in roll["campaign_name"]])) if notes else 0
        pick = st.selectbox("Daily trend for", roll["campaign_name"].tolist(), index=default_idx)
        st.plotly_chart(logic.trend_chart(df, pick), use_container_width=True)

    if not client_mode:
        with st.expander("Per-campaign metrics table", expanded=False):
            st.dataframe(
                _fmt_deep(roll)[["campaign_name", "objective", "spend", "impressions", "clicks",
                                 "CTR", "CPC", "CPM", "conversions", "CPA", "revenue", "ROAS"]],
                use_container_width=True, hide_index=True,
            )

    st.divider()
    st.subheader("Recommendations")
    for r in logic.recommendations(df, roll):
        st.markdown(f"- {r}")

    st.divider()
    st.subheader("AI performance summary")
    if generate:
        try:
            with st.spinner("Asking the analyst…"):
                report = dio.call_groq(logic.build_prompt(totals, roll, notes, obj))
            st.markdown(report)
            st.download_button("Download summary (.md)", report,
                               file_name=f"{client_name}_paid_social_summary.md", mime="text/markdown")
        except Exception as e:
            st.warning(f"AI summary unavailable ({e}). The dashboard above is fully usable without it.")
    else:
        st.caption("Click **Generate AI report** in the sidebar for a written summary.")

    # Chat context: the per-objective and per-campaign numbers, as text.
    ctx = "Account: " + ", ".join(f"{k}={v}" for k, v in totals.items()) + "\n"
    ctx += roll[["campaign_name", "objective", "spend", "conversions", "revenue",
                 "CPA", "ROAS"]].round(2).to_csv(index=False)
    render_chat(ctx, client_name)


# --------------------------------------------------------------------------- #
# CHANNEL mode — single export or combined monthly report
# --------------------------------------------------------------------------- #
def _budget_section(df: pd.DataFrame, fmt: str):
    if fmt not in ch.BUDGET_FORMATS:
        return
    st.divider()
    st.subheader("Budget Optimizer")
    st.caption("Enter next month's budget — allocation is optimized by campaign efficiency (CPA/CPE).")

    current_total = (df["Amount spent (MYR)"].sum() if fmt == "meta"
                     else df["Cost"].sum() if fmt == "google"
                     else df["Fee (MYR)"].sum())
    total_budget = st.number_input("Total budget next month (MYR)", min_value=100.0,
                                   value=round(float(current_total), 2), step=500.0, format="%.2f")

    alloc = ch.calculate_budget_allocation(df, fmt, total_budget)
    if alloc.empty:
        return

    def _highlight(val):
        if isinstance(val, (int, float)):
            return "color: #2ecc71" if val > 0 else "color: #e74c3c" if val < 0 else ""
        return ""

    st.dataframe(alloc.style.map(_highlight, subset=["Change (MYR)", "Change (%)"]),
                 use_container_width=True, hide_index=True)

    alloc["Short Campaign"] = alloc["Campaign"].str[:28] + "…"
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Current Spend", y=alloc["Short Campaign"], x=alloc["Current Spend"],
                         orientation="h", marker_color="#4C78A8"))
    fig.add_trace(go.Bar(name="Recommended Spend", y=alloc["Short Campaign"], x=alloc["Recommended Spend"],
                         orientation="h", marker_color="#2ecc71"))
    fig.update_layout(barmode="group", title="Current vs Recommended Budget Allocation",
                      xaxis_title="Spend (MYR)", height=max(300, len(alloc) * 60),
                      legend=dict(orientation="h", y=-0.2),
                      yaxis=dict(categoryorder="array", categoryarray=alloc["Short Campaign"].tolist()[::-1]))
    st.plotly_chart(fig, use_container_width=True)

    total_expected = alloc["Expected Results"].sum()
    st.info(f"At RM{total_budget:,.0f} budget, the model projects **{total_expected:.0f} total results**, "
            "allocated purely by CPA/CPE efficiency.")


def render_channel(fmt: str, df: pd.DataFrame, client_mode: bool, show_budget: bool = True) -> dict:
    kpis = ch.calculate_kpis(df, fmt)
    grade, summary, color = ch.score_channel(df, fmt)
    _grade_badge(grade, summary, color)
    _kpi_cards(kpis)

    fig = ch.build_chart(df, fmt)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    insights = ch.generate_insights(df, fmt)
    if insights:
        with st.expander("Key insights", expanded=True):
            for ins in insights:
                st.markdown(f"- {ins}")

    if show_budget:
        _budget_section(df, fmt)

    if not client_mode:
        with st.expander("Raw data"):
            st.dataframe(df, use_container_width=True)
    return kpis


def _chat_context(datasets: dict) -> str:
    parts = []
    for fmt, (df, kpis) in datasets.items():
        label = ch.FORMAT_LABELS.get(fmt, fmt)
        parts.append(f"{label}: " + " | ".join(f"{k}: {v}" for k, v in kpis.items()))
    return "\n".join(parts)


def render_channels(datasets: dict, is_full: bool, client_name: str, generate: bool, client_mode: bool):
    if is_full:
        st.subheader("Full Monthly Report — all channels")
        st.divider()
        for fmt, (df, _) in datasets.items():
            st.markdown(f"### {ch.FORMAT_LABELS.get(fmt, fmt.upper())}")
            datasets[fmt] = (df, render_channel(fmt, df, client_mode, show_budget=False))
            st.divider()
        if generate:
            try:
                with st.spinner("Generating combined AI report…"):
                    report = dio.call_groq(ch.build_combined_prompt(datasets, client_name))
                st.subheader("AI Monthly Performance Report")
                st.markdown(report)
                st.download_button("Download report (.md)", report,
                                   file_name=f"{client_name}_monthly_report.md", mime="text/markdown")
            except Exception as e:
                st.warning(f"AI report unavailable ({e}). The dashboard above is fully usable without it.")
    else:
        fmt, (df, _) = next(iter(datasets.items()))
        st.subheader(ch.FORMAT_LABELS.get(fmt, fmt))
        datasets[fmt] = (df, render_channel(fmt, df, client_mode))
        if generate:
            try:
                with st.spinner("Generating AI report…"):
                    report = dio.call_groq(ch.build_prompt(datasets[fmt][1], df, fmt, client_name))
                st.subheader("AI Performance Report")
                st.markdown(report)
                st.download_button("Download report (.md)", report,
                                   file_name=f"{client_name}_{fmt}_report.md", mime="text/markdown")
            except Exception as e:
                st.warning(f"AI report unavailable ({e}). The dashboard above is fully usable without it.")

    render_chat(_chat_context(datasets), client_name)


# --------------------------------------------------------------------------- #
# Resolve datasets from upload or sample selection
# --------------------------------------------------------------------------- #
deep_df: pd.DataFrame | None = None
datasets: dict | None = None
is_full = False

if uploaded_files:
    raw = {}
    for f in uploaded_files:
        df = _load(f)
        if logic.is_deep_format(df):
            deep_df = df
            break
        fmt = ch.detect_format(df)
        if fmt != "unknown":
            raw[fmt] = df
    if deep_df is None and raw:
        datasets = {fmt: (df, ch.calculate_kpis(df, fmt)) for fmt, df in raw.items()}
        is_full = len(raw) > 1

elif sample_choice != "—":
    key = SAMPLE_MAP[sample_choice]
    if key == "deep":
        if os.path.exists(DEEP_FILE):
            deep_df = _load(DEEP_FILE)
        else:
            st.error(f"Bundled sample not found: {DEEP_FILE}")
    elif key == "full":
        is_full = True
        datasets = {}
        for fmt in FULL_MONTHLY_FORMATS:
            df = _load(os.path.join("data", f"sample_{fmt}.csv"))
            datasets[fmt] = (df, ch.calculate_kpis(df, fmt))
    else:
        df = _load(os.path.join("data", f"sample_{key}.csv"))
        datasets = {key: (df, ch.calculate_kpis(df, key))}


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
if deep_df is not None:
    render_deep(deep_df, client_name, generate, client_mode)
elif datasets:
    render_channels(datasets, is_full, client_name, generate, client_mode)
else:
    st.info("Upload a CSV or pick a bundled sample from the sidebar to begin.")
    if not client_mode:
        st.markdown(
            "**Supported inputs:** objective-tagged paid-social (deep analysis), "
            "or single-channel Meta / Google / SEO / Social / Influencer exports "
            "(upload several at once for a combined monthly report)."
        )
