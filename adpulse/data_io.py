"""
data_io.py — all I/O lives here (CSV in, LLM out).

Keeping the data layer separate from the analytics (`logic.py`, `channels.py`)
and the UI (`app.py`) means new sources — a new file format, a different LLM
provider, a live ad-platform API — are a change in THIS file only.
"""

import os

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# --- LLM config -------------------------------------------------------------
_KEY_NAMES = ["GROQ_KEY_1", "GROQ_KEY_2", "GROQ_KEY_3"]
_MODEL = "llama-3.3-70b-versatile"


def _groq_keys() -> list[str]:
    """Collect Groq keys from either source, resolved at call time.

    Local dev       -> environment / .env (loaded above by python-dotenv).
    Streamlit Cloud -> st.secrets (set under the app's Settings → Secrets).
    """
    keys = [os.getenv(n) for n in _KEY_NAMES]
    try:  # st.secrets raises if no secrets are configured — that's fine
        import streamlit as st

        keys += [st.secrets.get(n) for n in _KEY_NAMES]
    except Exception:
        pass
    # de-dupe while preserving order, drop blanks
    seen, out = set(), []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def load_csv(source) -> pd.DataFrame:
    """Read a marketing CSV from a path or an uploaded file object.

    Swap-point for other sources: add load_excel / load_pdf / load_api here and
    nothing downstream changes.
    """
    df = pd.read_csv(source)
    df.columns = [c.strip() for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def call_groq(prompt: str, temperature: float = 0.3, max_tokens: int = 1000) -> str:
    """Call Groq with key rotation. Raises if no key is set or all keys fail.

    Decoupled on purpose: if this raises, the dashboard still renders — only the
    AI sections degrade.
    """
    from groq import Groq

    keys = _groq_keys()
    if not keys:
        raise ValueError("No Groq API key found — set GROQ_KEY_1 in .env (local) or Streamlit secrets (cloud).")
    last_err = None
    for key in keys:
        try:
            resp = Groq(api_key=key).chat.completions.create(
                model=_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:  # try the next key
            last_err = e
            continue
    raise RuntimeError(f"All Groq keys failed: {last_err}")


def chat_groq(prompt: str) -> str:
    """Follow-up Q&A turn — slightly warmer, shorter than a full report."""
    return call_groq(prompt, temperature=0.4, max_tokens=600)
