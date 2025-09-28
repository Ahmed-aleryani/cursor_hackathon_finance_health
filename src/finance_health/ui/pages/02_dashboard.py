from __future__ import annotations

import streamlit as st
import polars as pl

from finance_health.storage.loader import load_normalized_df
from finance_health.analytics.metrics import compute_kpis, monthly_cashflow, category_breakdown, top_merchants
from finance_health.analytics.scoring import compute_health_score
from finance_health.ui.components.kpi import render_kpis
from finance_health.ui.components.charts import monthly_cashflow_chart, categories_chart
from finance_health.ui.state import get_session_id

st.title("📊 Dashboard")

sid = get_session_id()
if not sid:
    st.warning("No active session. Go to Import to process files or Sessions to select one.")
    st.stop()

with st.spinner("Loading data..."):
    df = load_normalized_df(sid)

if df.is_empty():
    st.info("No data available for this session yet.")
    st.stop()

kpis = compute_kpis(df)
render_kpis(kpis)

month_df = monthly_cashflow(df)
chart = monthly_cashflow_chart(month_df)
if chart is not None:
    st.subheader("Monthly Cashflow")
    st.altair_chart(chart, use_container_width=True)

cats = category_breakdown(df)
cat_chart = categories_chart(cats, title="Top Categories/Merchants")
if cat_chart is not None:
    st.subheader("Spending Breakdown")
    st.altair_chart(cat_chart, use_container_width=True)

merchants = top_merchants(df)
mer_chart = categories_chart(merchants, title="Top Merchants by Spend")
if mer_chart is not None:
    st.subheader("Top Merchants")
    st.altair_chart(mer_chart, use_container_width=True)

score = compute_health_score(df)
st.subheader("Health Score")
st.metric("Score", f"{score.score}")
st.json(score.components)
