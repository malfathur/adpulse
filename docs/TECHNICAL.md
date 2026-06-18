# Technical Documentation

Audience: engineers maintaining or extending AdPulse.

## Architecture

```
ingest → detect format → (deep | channel) analysis → charts + grade + recs → AI report → chat
```

Change-isolation seams:
- New **data source** → `adpulse/data_io.py` only.
- New **metric / chart / rule** → `adpulse/logic.py` (deep) or `adpulse/channels.py` (channel).
- New **screen** → `app.py` only.

`logic.py` and `channels.py` are **pure** (no Streamlit, no I/O) → unit-tested in isolation.

## Stack
Python 3.11+ · Streamlit (UI) · pandas/numpy · Plotly · Groq API (`llama-3.3-70b-versatile`,
with key rotation) · pytest/ruff · Streamlit Cloud.

## Module map
| File | Responsibility |
|---|---|
| `app.py` | Streamlit UI; routes by detected format |
| `adpulse/data_io.py` | CSV load + Groq calls (key rotation across `GROQ_KEY_1..3`) |
| `adpulse/logic.py` | deep paid-social analytics (validation, rollups, fatigue) |
| `adpulse/channels.py` | detection, grades, KPIs, charts, budget optimizer, `BENCHMARKS` |

## Format detection
| Format | Detected by |
|---|---|
| Paid social (deep) | objective-tagged schema |
| Meta Ads | `Campaign name` + `Amount spent (MYR)` |
| Google Ads | `Campaign` + `Impr.` |
| SEO | `Query` + `Position` |
| Social (organic) | `Post` + `Reach` |
| Influencer | `Influencer` + `CPE (MYR)` |

## AI integration
- Provider: Groq (OpenAI-compatible). Model `llama-3.3-70b-versatile`.
- **Key rotation:** tries `GROQ_KEY_1`, then `2`, then `3` — first success wins (rate-limit
  resilience). Implemented in `data_io.py`.
- **Graceful degradation:** with no key, the dashboard fully renders; only the AI report + chat
  are disabled.

## Testing
```bash
pytest        # pure-function tests for logic + channels; fast, deterministic, no network
```

## Extending
- Retarget industry → edit `BENCHMARKS` in `channels.py`.
- New channel → add a detector + grade/KPI/chart path in `channels.py`.
- New deep metric → add to `logic.py` and a unit test.
