# Glossary & Context — MYSense Assessment

Quick-reference so you can think and talk like a campaign manager during the build and the interview.
Everything below is derived from `campaign_data.csv` (2025-05-01 → 05-14, one client, 4 campaigns).

---

## 1. The metrics (what to compute, formula, why it matters)

| Metric | Formula | Plain English | "Good" looks like |
|---|---|---|---|
| **CTR** (Click-Through Rate) | clicks ÷ impressions | How often people who saw the ad clicked it. A *creative/targeting* signal. | Paid social ~0.9–1.5%; >2% is strong. |
| **CPC** (Cost per Click) | spend ÷ clicks | What you pay for one click. | Lower = cheaper traffic. |
| **CPM** (Cost per Mille) | spend ÷ impressions × 1000 | Cost to show the ad 1,000 times. Auction-price signal. | Lower = cheaper reach. |
| **CPA / CPL** (Cost per Acquisition) | spend ÷ conversions | What one conversion costs you. | Must be **below** profit per sale. |
| **Conv. Rate** (CVR) | conversions ÷ clicks | Of the people who clicked, how many converted. *Landing-page/offer* signal. | The higher the better. |
| **ROAS** (Return on Ad Spend) | conversion_value ÷ spend | RM earned per RM1 spent. **The headline number for conversion campaigns.** | >1 = profitable on revenue; e-comm target often ≥3–4x. |
| **AOV** (Avg Order Value) | conversion_value ÷ conversions | Average revenue per conversion. | Context for whether CPA is OK. |

**Mental rule:** CTR is about *getting the click*, CVR is about *getting the sale*, ROAS is *did it make money*. A campaign can win one and lose another — that's where insight comes from.

---

## 1a. Understanding ROAS (the headline metric, in depth)

**ROAS = Return On Ad Spend = revenue ÷ spend.** "For every RM1 I put in, how many ringgit of sales came back?"

| ROAS | Meaning |
|---|---|
| **8.3×** | RM1 spent → RM8.30 back. Excellent. |
| **1.0×** | You earned back exactly what you spent — **break-even** (on revenue, before product cost). |
| **0.30×** | RM1 spent → 30 sen back. Losing money *if* the goal was sales. |

In code (`logic.py`): `ROAS = conversion_value_rm ÷ spend_rm`. Blended ROAS is the account-wide version: total revenue ÷ total spend (here 2.82×).

**The one nuance that matters.** ROAS only judges campaigns whose *job is to sell*. The **Awareness** campaign is buying *reach*, not purchases — scoring it on ROAS is like grading a billboard on units sold. So:
- **Conversions** campaigns → ROAS is the right scorecard.
- **Awareness** → judge on **CPM / reach** (RM3.90 CPM = very cheap reach), not ROAS.

**The break-even line on the objective chart** sits at ROAS = 1×. The chart is a scatter: x = share of spend, y = ROAS, bubble = conversions. A point *above* the line makes money on sales (Conversions 6.8×, Traffic 1.15×); *below* it does not (Awareness 0.30×). Read it by position — **bottom-right = big budget, below break-even** (the reallocation target); **top-left = efficient but under-funded**.

**Two honest caveats** (good to say out loud):
1. ROAS is built on **revenue, not profit** — 8× on a low-margin product is worth less than it looks; true break-even is usually *above* 1× once product cost is subtracted.
2. It depends entirely on the **attribution window** behind `conversion_value_rm` (was a sale credited to an ad clicked 7 days earlier?). Change that assumption and every ROAS here moves.

---

## 2. The objectives (this is the #1 trap in this dataset)

A campaign should be judged **against its own objective**, not on ROAS blindly. The platform optimises delivery toward whatever the objective is set to.

| Objective | What it's buying | Judge it on | Do NOT judge it on |
|---|---|---|---|
| **Conversions** | Purchases / actions | ROAS, CPA, conversions | — |
| **Awareness** | Cheap reach / impressions | CPM, reach, impressions | ROAS / conversions (it was never trying to sell) |
| **Traffic** | Clicks to site | CPC, CTR, clicks | ROAS (weakly — it's top-of-funnel) |

> **The trap:** "Always-On Brand Awareness" has the biggest spend (RM4,432) and a ROAS of 0.30x. A naive read says "cut it — it loses money." But it's an **Awareness** campaign — its job is cheap reach, and at **RM3.90 CPM it's the cheapest reach in the account**. Judging it on ROAS is the wrong yardstick. If you say "cut the awareness campaign because ROAS is low" in the interview, that's the mistake they're watching for. The *right* critique is more nuanced (see §4).

---

## 3. The four campaigns at a glance (computed totals, full 2 weeks)

| Campaign | Objective | Spend | CTR | CPC | CPM | CPA | ROAS | Read |
|---|---|---|---|---|---|---|---|---|
| **Mother's Day Sale – Purchases** | Conversions | RM2,144 | 2.00% | RM0.47 | RM9.36 | RM14.39 | **8.31x** | ⭐ Star. Scale it. |
| **Retargeting – Add to Cart** | Conversions | RM1,692 | 2.15% | RM0.95 | RM20.50 | RM22.26 | 4.97x | Profitable but **fatiguing fast** (see §4). |
| **Cold Prospecting – Traffic** | Traffic | RM2,536 | 1.51% | RM0.48 | RM7.21 | RM87.44 | 1.15x | Top-of-funnel; barely breaks even on last-click. |
| **Always-On Brand Awareness** | Awareness | RM4,432 | 0.60% | RM0.65 | RM3.90 | RM369 | 0.30x | Cheapest reach; don't judge on ROAS. |

Account totals: spend ≈ **RM10,804**, revenue ≈ **RM30,455**, blended **ROAS ≈ 2.82x**.

---

## 4. The insights actually hiding in the data (your recommendations come from here)

1. **Scale Mother's Day.** ROAS 8.31x, lowest CPA (RM14), strong 2% CTR, and conversions are *flat-to-rising* across the two weeks (no fatigue). This is the clearest "give it more budget" case. (Caveat to mention: it's a seasonal/holiday campaign — Mother's Day was 11 May — so expect it to cool after the event.)

2. **Retargeting is fatiguing — act now.** Day-by-day it decays almost monotonically:
   - CTR **3.01% → 1.16%** (down ~60%)
   - Conversions **9 → 3/day**
   - ROAS **8.6x → ~2.6x**
   This is classic **ad fatigue / small audience over-frequency** (retargeting pools are small, so the same people see it repeatedly). Still profitable overall (4.97x) but the *trend* is the story. Fix = refresh creative and/or cap frequency, don't just pour in budget.

3. **Reframe the Awareness spend.** It's the single biggest line item (41% of spend) on the cheapest CPM. The right question isn't "ROAS?" but "is RM4.4k of *reach* the best use of 41% of budget right now, during a high-ROAS sale window?" Defensible rec: **trim awareness, reallocate to Mother's Day/Retargeting** while ROAS is hot — without claiming awareness "lost money."

4. **Traffic campaign is the weak converter.** CTR is fine (1.51%) and CPC cheap (RM0.48), so it's *delivering clicks* as intended — but those clicks barely convert (ROAS 1.15x, CPA RM87). That points to a **landing-page / audience-quality** gap, not a creative one. "Check next" material rather than a confident cut.

---

## 5. Data-validation notes (the brief explicitly tests this)

- **Recorded `ctr` is consistent** with clicks ÷ impressions on every row — no fabricated/contradictory CTR. (Good: say you checked, don't assume it's wrong.)
- **Zero-conversion rows** exist for Awareness (`conversions=0`, `conversion_value_rm=0.0`) — that's legitimate, not missing data. Your CPA/ROAS code must **guard against divide-by-zero** (return n/a, don't crash).
- **Currency is RM** throughout; no nulls, no negative values, dates are contiguous (14 days × 4 campaigns = 56 rows). 
- Watch the **objective ≠ metric** mismatch (the real "misleading" thing in this data) — that's the §2 trap, and it's the validation point they care about more than dirty numbers.

---

## 6. How to keep the LLM "focused & constrained" (eval criterion)

Don't dump the CSV into the model. Compute the metrics in code first, then pass the model **only the aggregated table + objectives** and ask for: (a) a plain-English summary and (b) 2–3 recommendations *each tied to a specific number*. Constrain it: "Use only the figures provided. Judge each campaign against its stated objective. Do not call the Awareness campaign a failure for low ROAS." Then read its output and fix anything wrong — that "I checked it" step is half the marks.

---

## 7. One-line interview cheat-sheet

> "Blended ROAS 2.8x. **Scale Mother's Day (8.3x, no fatigue)**, **rescue Retargeting (profitable but CTR/ROAS decaying ~60% — creative refresh)**, and **reallocate some Awareness budget (41% of spend, but that's reach not revenue — fine, just maybe too much right now)**. Traffic converts poorly — landing-page check next. Data was clean; the real catch is not scoring Awareness on ROAS."
