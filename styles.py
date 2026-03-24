# styles.py
import streamlit as st

CUSTOM_CSS = """
<style>
:root {
  /* Tell the browser to support both themes */
  color-scheme: light dark;
}

/* Global tweaks */
html, body, [class^="css"]  {
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}

/* Top title spacing */
h1 { margin-bottom: .5rem; }

/* --- Light-mode defaults (also used as fallback) --- */

/* Subtle card styling */
.card {
  padding: 1.1rem 1.2rem;
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}

/* Result chip colors */
.chip {
  display:inline-block;
  padding:.35rem .7rem;
  border-radius:999px;
  font-weight:600;
  font-size:.9rem;
  border:1px solid rgba(0,0,0,.08);
}
.chip-fake { background:#fff5f5; color:#b42318; }
.chip-real { background:#f1fff4; color:#057a55; }

/* Footer */
.footer {
  color:#6b7280;
  font-size:.85rem;
  margin-top:1.5rem;
}

/* --- Dark-mode overrides --- */
@media (prefers-color-scheme: dark) {
  body {
    background-color: #020617;
    color: #e5e7eb;
  }

  .card {
    background: rgba(15,23,42,0.96);
    border: 1px solid rgba(148,163,184,0.35);
    box-shadow:
      0 18px 45px rgba(15,23,42,0.85),
      0 0 0 1px rgba(15,23,42,0.9);
  }

  .footer {
    color:#9ca3af;
  }

  .chip {
    border: 1px solid rgba(148,163,184,0.5);
  }
  .chip-fake {
    background: rgba(248,113,113,0.16);
    color: #fecaca;
  }
  .chip-real {
    background: rgba(34,197,94,0.14);
    color: #bbf7d0;
  }
}
</style>
"""

def inject_custom_css() -> None:
    """Inject global CSS into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
