from __future__ import annotations

import streamlit as st
from ...analytics.metrics import KPIs


def render_kpis(kpis: KPIs) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Income", f"${kpis.total_income:,.0f}")
    c2.metric("Total Expense", f"${kpis.total_expense:,.0f}")
    c3.metric("Net Cashflow", f"${kpis.net_cashflow:,.0f}")
    c4.metric("Savings Rate", f"{kpis.savings_rate*100:.1f}%")
