# Business Documentation

Audience: campaign managers, marketing leads, non-technical stakeholders.

## Objective

Turn raw marketing exports into an actionable read in minutes: metrics, benchmark grades,
evidence-based recommendations, and an LLM-written report a campaign manager can act on — across
paid social, paid search, SEO, organic social, and influencer campaigns.

## What it delivers

- **Two analysis paths, auto-selected by the data shape:**
  - *Deep mode* — objective-tagged paid-social: validation-first metrics, spend-by-objective,
    audience-fatigue detection, goal-aware recs (Awareness judged on reach/CPM, not ROAS).
  - *Channel mode* — a single Meta/Google/SEO/Social/Influencer export (or several for a combined
    monthly report): A–F grade, KPI cards, channel-appropriate chart, rule-based insights, and a
    CPA/CPE-weighted budget optimizer.
- An **AI report** plus an **Ask the Analyst** follow-up chat.

## Process overview

```
upload export(s) → auto-detect format → deep or channel analysis
   → grade + KPIs + chart + recommendations → AI report → follow-up Q&A
```

## Outcomes & success criteria

| Goal | Measure |
|---|---|
| Faster read of campaign health | Grade + KPIs on upload, no manual spreadsheeting |
| Goal-appropriate judgement | Awareness vs conversion judged on the right metric |
| Actionable | Concrete recs + budget reallocation suggestions |
| Resilient | Whole dashboard renders even with no AI key (only AI sections degrade) |

## Scope

**In scope:** Meta, Google, SEO, organic social, influencer; grading, insights, budget optimizer,
AI report + chat.

**Out of scope:** live ad-platform API pulls (works on exports), automated campaign changes,
attribution modelling.

> Benchmarks are tuned for the Malaysia healthcare/clinic vertical; retarget by editing the
> `BENCHMARKS` table. Origin: grew out of a marketing-analytics technical assessment.
