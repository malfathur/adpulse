# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com); this project adheres to
[Semantic Versioning](https://semver.org).

## [2.0.0] — 2026-06-14

Rebuilt the single-dataset paid-social assessment tool into **AdPulse**, a
general multi-channel marketing-performance dashboard.

### Added
- **Multi-channel ingestion** — auto-detects Meta Ads, Google Ads, SEO, organic
  Social, and Influencer CSV exports (`adpulse/channels.py → detect_format`).
- **A–F benchmark grading** — per-channel grade vs Malaysia industry benchmarks
  (`score_channel`).
- **Budget optimizer** — CPA/CPE-weighted spend reallocation for paid channels
  (`calculate_budget_allocation`).
- **Client View** — clean presentation mode that hides dev controls and raw data.
- **Ask the Analyst** — Groq-powered follow-up chat grounded in the computed metrics.
- **Combined monthly report** — analyze several channels at once with an executive
  summary (`build_combined_prompt`).
- Channel KPI cards, channel-specific Plotly charts, and rule-based insights.
- `tests/test_channels.py` covering detection, grading, KPIs, charts, and optimizer.

### Changed
- Renamed package `mysense` → `adpulse`; bumped version to `2.0.0`.
- `app.py` now routes between deep (objective-aware paid-social) and channel modes
  by the shape of the uploaded data.
- Genericized AI-prompt and UI branding (no employer name in the product surface).
- Added portfolio scaffolding: README, this changelog, MIT license, `.github/`
  templates + CI, and the standard `.gitignore` pattern.

### Retained from v1
- Validation-first deep analysis, objective rollups, audience-fatigue detection,
  evidence-based recommendations, Groq key rotation, and graceful degradation when
  the LLM is unavailable.
