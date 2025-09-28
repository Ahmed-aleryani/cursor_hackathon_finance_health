from __future__ import annotations

import streamlit as st

SESSION_KEY = "session_id"


def get_session_id() -> str | None:
    return st.session_state.get(SESSION_KEY)


def set_session_id(session_id: str) -> None:
    st.session_state[SESSION_KEY] = session_id
