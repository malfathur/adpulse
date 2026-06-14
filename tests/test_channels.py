"""Unit tests for the multi-channel breadth layer (adpulse.channels).

Run with:  pytest
Loads the bundled sample CSVs; no Streamlit, no network.
"""

import os

import pytest

from adpulse import channels as ch
from adpulse import data_io

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _sample(fmt):
    return data_io.load_csv(os.path.join(DATA_DIR, f"sample_{fmt}.csv"))


@pytest.fixture(scope="module")
def samples():
    return {fmt: _sample(fmt) for fmt in ["meta", "google", "seo", "social", "influencer"]}


def test_detect_format_each_channel(samples):
    for fmt, df in samples.items():
        assert ch.detect_format(df) == fmt


def test_detect_format_unknown():
    import pandas as pd
    assert ch.detect_format(pd.DataFrame({"foo": [1], "bar": [2]})) == "unknown"


def test_calculate_kpis_returns_expected_keys(samples):
    assert "Total Spend (MYR)" in ch.calculate_kpis(samples["meta"], "meta")
    assert "Avg CPA" in ch.calculate_kpis(samples["google"], "google")
    assert "Avg Position" in ch.calculate_kpis(samples["seo"], "seo")
    assert "Avg Engagement Rate" in ch.calculate_kpis(samples["social"], "social")
    assert "Best ROI Influencer" in ch.calculate_kpis(samples["influencer"], "influencer")


def test_score_channel_returns_valid_grade(samples):
    for fmt, df in samples.items():
        grade, summary, color = ch.score_channel(df, fmt)
        assert grade in {"A", "B", "C", "D", "F"}
        assert isinstance(summary, str) and summary
        assert color in {"green", "orange", "red"}


def test_build_chart_builds_for_every_channel(samples):
    for fmt, df in samples.items():
        assert ch.build_chart(df, fmt) is not None


def test_generate_insights_non_empty(samples):
    for fmt, df in samples.items():
        insights = ch.generate_insights(df, fmt)
        assert isinstance(insights, list) and len(insights) >= 1


def test_budget_allocation_paid_channels(samples):
    for fmt in ch.BUDGET_FORMATS:
        alloc = ch.calculate_budget_allocation(samples[fmt], fmt, 10000.0)
        assert not alloc.empty
        # recommended spend reallocates the full budget
        assert round(alloc["Recommended Spend"].sum(), 0) == 10000
        assert {"Change (MYR)", "Change (%)", "Expected Results"} <= set(alloc.columns)


def test_budget_allocation_empty_for_non_budget_channel(samples):
    assert ch.calculate_budget_allocation(samples["seo"], "seo", 10000.0).empty


def test_prompts_reference_client_and_numbers(samples):
    kpis = ch.calculate_kpis(samples["meta"], "meta")
    p = ch.build_prompt(kpis, samples["meta"], "meta", "Acme Clinic")
    assert "Acme Clinic" in p
    assert "markdown format" in p

    datasets = {fmt: (samples[fmt], ch.calculate_kpis(samples[fmt], fmt))
                for fmt in ["meta", "google", "seo", "social"]}
    combined = ch.build_combined_prompt(datasets, "Acme Clinic")
    assert "Executive Summary" in combined

    chat = ch.build_chat_prompt([{"role": "user", "content": "hi"}],
                                "Meta Ads: spend RM1000", "Which channel wins?", "Acme Clinic")
    assert "Acme Clinic" in chat
    assert "Which channel wins?" in chat
