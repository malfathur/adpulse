# Operations Documentation

Audience: whoever runs or deploys AdPulse.

## Local run
```bash
pip install -r requirements.txt
cp .env.example .env          # add a Groq key (free: console.groq.com)
streamlit run app.py
```
Pick a bundled sample from the sidebar, or upload your own CSV(s). Works without a Groq key —
only the AI report + chat need one.

## Credentials
| Var | Purpose |
|---|---|
| `GROQ_KEY_1` | primary LLM key |
| `GROQ_KEY_2`, `GROQ_KEY_3` | optional fallbacks (rate-limit rotation) |

Store in a secrets manager / Streamlit Cloud Secrets — never commit `.env`.

## Deployment (Streamlit Cloud)
Live at https://adpulse.streamlit.app/. To deploy your own:
1. Push to GitHub.
2. New Streamlit Cloud app → point at `app.py`.
3. Add `GROQ_KEY_1` (and optionally `2/3`) under Settings → Secrets.

## Monitoring & health
- App is stateless (no DB) — health = "does it load and render a sample".
- If AI sections are blank, it's a key/quota issue, not an app failure (by design).

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| AI report/chat blank | No/invalid Groq key or all keys rate-limited | Add/rotate `GROQ_KEY_*` |
| Upload not recognised | Schema doesn't match any detector | Check column names vs the detection table in TECHNICAL.md |
| Wrong grades for my industry | Benchmarks tuned for MY healthcare | Edit `BENCHMARKS` in `channels.py` |
| Chart looks off | Unexpected data shape | Validate the export; compare to a bundled sample |

## Maintenance cadence
- Review `BENCHMARKS` when retargeting industries or when norms shift.
- Rotate Groq keys if quotas are hit frequently.
