from __future__ import annotations

import json
from typing import Any
import polars as pl

from langchain_core.tools import tool

from ..storage.loader import load_normalized_df
from ..analytics.metrics import compute_kpis, monthly_cashflow, category_breakdown, top_merchants
from ..analytics.scoring import compute_health_score as _compute_health_score
from ..storage.report_io import load_report, save_report


def _df_to_csv(df: pl.DataFrame, limit: int | None = None) -> str:
    if df.is_empty():
        return ""
    if limit is not None:
        df = df.head(limit)
    return df.to_pandas().to_csv(index=False)


@tool("get_kpis", return_direct=False)
def get_kpis(session_id: str) -> str:
    """Return basic KPIs for the given session as JSON string with keys: total_income, total_expense, net_cashflow, savings_rate."""
    df = load_normalized_df(session_id)
    k = compute_kpis(df)
    return json.dumps({
        "total_income": k.total_income,
        "total_expense": k.total_expense,
        "net_cashflow": k.net_cashflow,
        "savings_rate": k.savings_rate,
    })


@tool("get_monthly_cashflow_csv", return_direct=False)
def get_monthly_cashflow_csv(session_id: str, months: int = 12) -> str:
    """Return monthly cashflow table as CSV with columns: month, income, expense, net."""
    df = load_normalized_df(session_id)
    m = monthly_cashflow(df)
    if months:
        m = m.tail(months)
    return _df_to_csv(m)


@tool("get_top_categories_csv", return_direct=False)
def get_top_categories_csv(session_id: str, limit: int = 10) -> str:
    """Return top categories/merchants by spend as CSV with columns: category_or_merchant, spend."""
    df = load_normalized_df(session_id)
    c = category_breakdown(df)
    if limit:
        c = c.head(limit)
    return _df_to_csv(c)


@tool("get_top_merchants_csv", return_direct=False)
def get_top_merchants_csv(session_id: str, limit: int = 10) -> str:
    """Return top merchants by spend as CSV with columns: merchant, spend, tx_count."""
    df = load_normalized_df(session_id)
    t = top_merchants(df, limit=limit)
    return _df_to_csv(t)


@tool("compute_health_score", return_direct=False)
def compute_health_score(session_id: str) -> str:
    """Compute overall health score and return JSON with keys: score and components."""
    df = load_normalized_df(session_id)
    hs = _compute_health_score(df)
    return json.dumps({"score": hs.score, "components": hs.components})


@tool("save_advice", return_direct=True)
def save_advice(session_id: str, advice_markdown: str, score_json: str | None = None) -> str:
    """Persist the generated advice and optional score JSON into the session's report.json and return 'OK'."""
    report = load_report(session_id) or {}
    report["advice"] = advice_markdown
    if score_json:
        try:
            report["health_score"] = json.loads(score_json)
        except Exception:
            pass
    save_report(session_id, report)
    return "OK"
