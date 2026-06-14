"""Unit tests for the deep paid-social analytics layer (adpulse.logic).

Run with:  pytest
No Streamlit, no network — logic.py is pure, so these are fast and deterministic.
"""

import os

import pandas as pd
import pytest

from adpulse import data_io, logic

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "campaign_data.csv")


@pytest.fixture(scope="module")
def df():
    return data_io.load_csv(DATA)


@pytest.fixture(scope="module")
def roll(df):
    return logic.campaign_rollup(df)


def test_is_deep_format(df):
    assert logic.is_deep_format(df) is True
    assert logic.is_deep_format(pd.DataFrame({"Campaign name": [], "Amount spent (MYR)": []})) is False


def test_validation_passes_on_clean_data(df):
    levels = [lvl for lvl, _ in logic.validate(df)]
    assert "error" not in levels


def test_missing_column_is_an_error():
    bad = pd.DataFrame({"date": ["2025-05-01"], "campaign_name": ["x"]})
    levels = [lvl for lvl, _ in logic.validate(bad)]
    assert "error" in levels


def test_rollup_metrics_match_known_values(roll):
    md = roll.loc[roll["campaign_name"] == "Mother's Day Sale - Purchases"].iloc[0]
    assert md["conversions"] == 149
    assert round(md["ROAS"], 2) == 8.31
    assert round(md["CPA"], 0) == 14


def test_blended_roas(df):
    assert round(logic.account_totals(df)["blended_roas"], 2) == 2.82


def test_objective_rollup_shares_and_totals(df, roll):
    obj = logic.objective_rollup(df)
    assert round(obj["spend_share"].sum(), 6) == 1.0
    assert round(obj["spend"].sum(), 2) == round(roll["spend"].sum(), 2)
    aw = obj.loc[obj["objective"] == "Awareness"].iloc[0]
    assert aw["campaigns"] == 1
    assert round(aw["spend_share"], 2) == 0.41  # ~41% of budget


def test_objective_rollup_from_roll_matches_direct(df, roll):
    a = logic.objective_rollup(df).set_index("objective")["ROAS"]
    b = logic.objective_rollup_from_roll(roll).set_index("objective")["ROAS"]
    pd.testing.assert_series_equal(a.sort_index(), b.sort_index())


def test_retargeting_flagged_as_fatigue(df):
    t = logic.daily_trend(df, "Retargeting - Add to Cart")
    assert t["fatigue"] is True
    assert t["ctr_change_pct"] < -50  # CTR roughly halved over the period


def test_mothers_day_not_fatigued(df):
    assert logic.daily_trend(df, "Mother's Day Sale - Purchases")["fatigue"] is False


def test_recommendations_cover_scale_fatigue_awareness(df, roll):
    recs = " ".join(logic.recommendations(df, roll)).lower()
    assert "scale" in recs
    assert "fatigue" in recs
    assert "awareness" in recs


def test_objective_chart_builds(df):
    fig = logic.objective_chart(logic.objective_rollup(df))
    names = {t.name for t in fig.data}
    assert {"Awareness", "Conversions", "Traffic"} <= names
    assert any(getattr(s, "line", None) and s.y0 == s.y1 == 1 for s in fig.layout.shapes)


def test_prompt_guards_awareness_metric(df, roll):
    prompt = logic.build_prompt(logic.account_totals(df), roll, logic.fatigue_notes(df, roll))
    assert "Awareness" in prompt
    assert "NOT sales" in prompt or "not sales" in prompt.lower()
