# MYSense Assessment — Tool + Insight Note


## deployed link|

https://mysensetool.streamlit.app/

## How to run locally

```bash
pip install -r requirements.txt
# add a Groq key to .env (copy .env.example) — free at console.groq.com
streamlit run app.py
```

No upload needed — it loads the bundled `campaign_data.csv`. Drop a different CSV (same columns) in the sidebar to analyse another period. The dashboard works even if the Groq key is missing; only the AI summary needs it.

**Layered for extension** (data → analytics → UI):

| File | Responsibility | Extend it for… |
|---|---|---|
| `data_io.py` | I/O — CSV load, Groq call (key rotation) | a new file format, Excel/PDF, a different LLM, a live ad-API |
| `logic.py` | analytics — validation, metrics, charts, recommendations, prompt | new KPIs, new objective rules, new charts |
| `app.py` | Streamlit UI only — wires inputs to functions to widgets | new pages, client-view, exports |

---

## Headline metrics (2 weeks, 1–14 May 2025)

| Metric | Value |
|---|---|
| Total spend | **RM 10,804** |
| Revenue | **RM 30,454** |
| Blended ROAS | **2.82×** |
| Conversions | **266** |
| Account CTR | **1.0%** |

Per campaign:

| Campaign | Objective | Spend | ROAS | CPA | CPM |
|---|---|---|---|---|---|
| Mother's Day Sale | Conversions | RM 2,144 | **8.31×** | RM 14 | RM 9.36 |
| Retargeting – Add to Cart | Conversions | RM 1,692 | 4.97× | RM 22 | RM 20.50 |
| Cold Prospecting | Traffic | RM 2,536 | 1.15× | RM 87 | RM 7.21 |
| Always-On Brand Awareness | Awareness | RM 4,432 | 0.30× | RM 369 | RM 3.90 |

---

## Data validation (done before trusting any metric)

- **Reported `ctr` checks out** — it matches `clicks ÷ impressions` to within 5e-5 (rounding). The tool recomputes CTR from raw counts anyway rather than trusting the platform column.
- Funnel intact (clicks ≤ impressions, conversions ≤ clicks); no nulls, no negatives.
- Zero-revenue days exist but are all on the Awareness campaign — expected, not a bug.
- **The trap caught:** ranking all four campaigns by ROAS would label Awareness the "worst" performer. It isn't — it's a *reach* buy and must be judged on CPM/reach, so the tool segments by objective and flags this explicitly.

## The 2–3 things I'd do, and the evidence

1. **Scale Mother's Day Sale.** 8.31× ROAS (RM17,814 on RM2,144) at RM14 CPA — the most efficient line in the account, yet only ~20% of spend. Raise its cap and feed it budget from weaker lines.
2. **Refresh Retargeting — it's fatiguing.** Over the 14 days CTR fell **61%** (0.0301 → 0.0116) and daily conversions **67%** (9 → 3) in a steady, monotonic decline — classic audience burnout, not noise. Rotate creative / widen the pool before ROAS (still 4.97×) erodes.
3. **Re-justify Awareness on the right metric.** It's **41% of total spend (RM4,432)** at RM3.90 CPM. Its 0.30× ROAS is irrelevant; the question is whether the reach/brand-lift goal is real. If there's no brand-lift target behind it, part of that budget is better spent on Mother's Day. (Cold Prospecting at 1.15× ROAS / RM87 CPA is the next watch item — barely above break-even.)

## Sensible use of AI

The LLM never sees raw rows it could miscount — it receives the *computed* metric table and is instructed to use only those numbers, with an explicit rule never to judge Awareness on ROAS. Temperature 0.3, fixed markdown shape, key-rotation fallback. The dashboard is fully usable if the AI call fails.

## What I'd build / check next with more time

- **Statistical significance** of the fatigue trend (the slope is clear by eye, but I'd confirm it's not within daily variance).
- **CPM / reach + frequency data** for the Awareness campaign so it can be graded on its own objective instead of flagged as "n/a on ROAS".
- **Attribution window** assumptions behind `conversion_value_rm` — same-day vs 7-day click changes every ROAS here.
- **Period-over-period comparison** (vs the previous fortnight) to separate fatigue from seasonality, and a budget-reallocation simulator.
