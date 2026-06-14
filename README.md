# AdPulse — Marketing Performance Tool

**Live demo:** https://adpulse.streamlit.app/

AdPulse turns raw marketing exports into metrics, charts, benchmark grades,
evidence-based recommendations, and an LLM-written report a campaign manager can
act on — across paid social, paid search, SEO, organic social, and influencer
campaigns.

It has two analysis paths, chosen automatically by the shape of the data:

- **Deep mode** — objective-tagged paid-social data: validation-first metrics,
  spend-by-objective analysis, audience-fatigue detection, and recommendations
  that respect the goal of each campaign (Awareness is judged on reach/CPM, not ROAS).
- **Channel mode** — a single Meta / Google / SEO / Social / Influencer export
  (or several at once for a combined monthly report): A–F benchmark grade, KPI
  cards, a channel-appropriate chart, rule-based insights, and a CPA/CPE-weighted
  budget optimizer for paid channels.

Both paths finish with an AI report plus an **Ask the Analyst** follow-up chat.
The whole dashboard renders even with no Groq key — only the AI sections degrade.

> Origin: AdPulse grew out of a marketing-analytics technical assessment and was
> rebuilt into a general, multi-channel portfolio project.

## Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| UI | Streamlit |
| Data | pandas, numpy |
| Charts | Plotly |
| AI | Groq API (`llama-3.3-70b-versatile`), with key rotation |
| Test / lint | pytest, ruff |
| Hosting | Streamlit Cloud |

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # then add a Groq key (free: console.groq.com)
streamlit run app.py
```

Pick a bundled sample from the sidebar, or upload your own CSV(s). The dashboard
works without a Groq key — only the AI report and chat need one.

## How it works

```
ingest → detect format → (deep | channel) analysis → charts + grade + recs → AI report → chat
```

- A new **data source** touches `adpulse/data_io.py` only.
- A new **metric / chart / rule** touches `adpulse/logic.py` (deep) or
  `adpulse/channels.py` (channel) only.
- A new **screen** touches `app.py` only.

`logic.py` and `channels.py` are pure (no Streamlit, no I/O), so they are
unit-tested in isolation.

## Supported formats

| Format | Detected by | Grade · KPIs · Chart · Insights | Budget optimizer |
|---|---|---|---|
| Paid social (deep) | objective-tagged schema | objective rollups, fatigue, recs | — |
| Meta Ads | `Campaign name` + `Amount spent (MYR)` | ✓ | ✓ |
| Google Ads | `Campaign` + `Impr.` | ✓ | ✓ |
| SEO | `Query` + `Position` | ✓ | — |
| Social (organic) | `Post` + `Reach` | ✓ | — |
| Influencer | `Influencer` + `CPE (MYR)` | ✓ | ✓ |

Benchmarks (in `adpulse/channels.py → BENCHMARKS`) are tuned for the Malaysia
healthcare/clinic vertical; edit that table to retarget another industry.

## Project structure

```
AdPulse/
├── app.py                 # Streamlit UI — routes by detected format
├── adpulse/
│   ├── data_io.py         # I/O: CSV load + Groq calls (key rotation)
│   ├── logic.py           # deep paid-social analytics (validation, rollups, fatigue)
│   └── channels.py        # multi-channel: detection, grades, KPIs, charts, optimizer
├── data/                  # bundled samples (1 deep + 5 channel CSVs)
├── docs/                  # brief, glossary, insight note (project history)
├── tests/                 # pytest unit tests (logic + channels)
├── .streamlit/config.toml # dark theme
└── requirements.txt
```

## Testing

```bash
pip install pytest
pytest
```

Pure-function tests only — fast, deterministic, no Streamlit and no network.

## Deployment (Streamlit Cloud)

Deployed at **https://adpulse.streamlit.app/**. To deploy your own:

1. Push to GitHub.
2. Create a new Streamlit Cloud app pointing at `app.py`.
3. Add `GROQ_KEY_1` (and optionally `GROQ_KEY_2/3`) under **Settings → Secrets**.

## License

MIT — see [`LICENSE`](LICENSE).
