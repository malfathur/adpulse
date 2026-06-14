# MYSense — AI Automation Engineer · Practical Assessment

**Time:** ~1 hour · **Tools:** anything you like · **Deliverable:** one working file + a short note

---

## About this exercise

MYSense is a digital and influencer marketing agency. A big part of this role is building small internal tools that turn raw paid-media data into something a campaign manager can act on — fast, accurate, and automated.

This exercise is a miniature of that job. We care more about **clear thinking and correct, useful output** than about polish. A simple tool that works and produces a genuine insight beats an ambitious one that's half-built.

**Use any AI tools you want** — ChatGPT, Claude, Cursor, Copilot, Gemini, whatever you're fastest in. Using AI well *is* the job, so we expect you to lean on it. We're evaluating the result and your understanding of it, not whether you typed every line yourself.

---

## The task

You're given `campaign_data.csv` — two weeks of (anonymised) performance data for one client's paid social campaigns.

Build a small tool that:

1. **Ingests** the CSV.
2. **Computes the key performance metrics** a campaign manager would actually use.
3. **Uses an LLM** (any provider) to generate a short, plain-English performance summary.
4. **Surfaces 2–3 concrete recommendations** — what to optimise, scale, fix, or cut, and why.

You may build it as a **single HTML file** (open in a browser) or a **Python script / small Streamlit app** — your choice. Whatever you can get running cleanly and hand over.

---

## The data

`campaign_data.csv` — one row per campaign per day. Columns:

| Column | Meaning |
|---|---|
| `date` | Reporting day |
| `campaign_name` | Campaign |
| `objective` | What the campaign is optimised for (Conversions, Awareness, Traffic) |
| `impressions` | Times the ad was shown |
| `clicks` | Link clicks |
| `ctr` | Click-through rate as recorded by the ad platform |
| `spend_rm` | Spend in Malaysian Ringgit |
| `conversions` | Purchases / completed actions |
| `conversion_value_rm` | Revenue attributed to those conversions (RM) |

> Treat this like real client data: **validate it before you trust it.** Sanity-check anything that looks off before you build a metric on top of it.

---

## What to hand back

1. **Your tool** — the file(s), with a one-line note on how to run it.
2. **A short insight note** (about half a page, or be ready to walk us through it in 3–5 minutes):
   - The headline metrics you'd report to the client.
   - The 2–3 things you'd do to improve performance, and the evidence in the data behind each.
   - What you'd build or check next if you had more time.

---

## How we'll evaluate it

- **Correctness** — are the metrics right, and did you catch anything misleading in the raw data?
- **Insight** — do your recommendations actually follow from the numbers? Do you understand *why* a campaign is winning or losing, not just *that* it is?
- **Sensible use of AI** — is the LLM prompted in a focused, constrained way, with output you've checked rather than blindly trusted?
- **Engineering judgement** — does it run, handle bad input gracefully, and stay readable under time pressure?
- **Scope discipline** — shipping something solid and finished within the hour.

---

## Submitting

Reply to this email with your file(s) attached and your insight note (in the email body or as a short doc). If anything is ambiguous, make a reasonable assumption, note it, and keep moving — that's exactly what we'd want on the job.

Good luck.
