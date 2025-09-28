from __future__ import annotations

import streamlit as st

from finance_health.storage.loader import load_normalized_df
from finance_health.storage.report_io import load_report, save_report
from finance_health.advice.graph import AdviceEngine
from finance_health.ui.state import get_session_id

st.title("🧠 Advice")

sid = get_session_id()
if not sid:
    st.warning("No active session. Go to Import to process files or Sessions to select one.")
    st.stop()

df = load_normalized_df(sid)
if df.is_empty():
    st.info("No data available for this session yet.")
    st.stop()

existing = load_report(sid)
if existing and existing.get("advice"):
    st.success("Advice already generated for this session.")
    st.metric("Health Score", f"{existing['health_score']['score']}")
    st.json(existing["health_score"]["components"])
    st.markdown(existing["advice"])
elif st.button("Generate Advice", type="primary"):
    with st.spinner("Generating local advice with Ollama..."):
        engine = AdviceEngine()
        try:
            result = engine.generate(df, session_id=sid)
        except Exception as e:
            st.error(f"Advice generation failed: {e}")
            st.stop()
        if result is None:
            st.error("Advice generation returned no result.")
            st.stop()
        rep = load_report(sid) or {}
        # Always update health_score from current df to avoid None
        from finance_health.analytics.scoring import compute_health_score
        hs = compute_health_score(df)
        rep["health_score"] = {"score": hs.score, "components": hs.components}
        rep["advice"] = result.advice_markdown
        save_report(sid, rep)
    st.success("Advice ready and saved.")
    st.metric("Health Score", f"{hs.score}")
    st.json(hs.components)
    st.markdown(result.advice_markdown)
else:
    st.caption("Click 'Generate Advice' to run the local model and see recommendations.")
