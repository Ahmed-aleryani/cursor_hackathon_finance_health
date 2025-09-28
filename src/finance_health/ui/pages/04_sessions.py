from __future__ import annotations

import streamlit as st

from finance_health.storage.sessions import list_sessions
from finance_health.storage.loader import get_session
from finance_health.ui.state import set_session_id

st.title("🗂️ Sessions")

sessions = list_sessions()
if not sessions:
    st.info("No sessions yet. Go to Import to create one.")
    st.stop()

selected = st.selectbox(
    "Select a session",
    options=[s.id for s in sessions],
    format_func=lambda sid: f"{sid} — {get_session(sid).title if get_session(sid) else ''}",
)

if st.button("Activate Session", type="primary"):
    set_session_id(selected)
    st.success(f"Activated session {selected}. Navigate to Dashboard/Advice.")
