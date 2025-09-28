import os
import sys
from pathlib import Path
import streamlit as st

# Ensure `src` is on sys.path for absolute imports when running via Streamlit
_p = Path(__file__).resolve()
for _ in range(6):
    if _p.name == "src":
        break
    _p = _p.parent
if _p.name == "src" and str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

st.set_page_config(page_title="Finance Health", layout="wide")

st.title("🏦 Finance Health (Local)")
st.caption("Import CSV/XLSX → analyze with Polars → local AI advice → Streamlit dashboards")

if hasattr(st, "page_link"):
    st.page_link("pages/01_import.py", label="Import", icon="📥")
    st.page_link("pages/02_dashboard.py", label="Dashboard", icon="📊")
    st.page_link("pages/03_advice.py", label="Advice", icon="🧠")
    st.page_link("pages/04_sessions.py", label="Sessions", icon="🗂️")
    st.page_link("pages/05_settings.py", label="Settings", icon="⚙️")
else:
    st.write("Use the left sidebar 'Pages' to navigate.")

st.divider()
st.write("Use the left sidebar to navigate. Start with Import.")
