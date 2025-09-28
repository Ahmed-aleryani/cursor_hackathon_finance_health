from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import polars as pl

from .metrics import compute_kpis, monthly_cashflow, category_breakdown, top_merchants
from .scoring import compute_health_score


def build_report(session_id: str, df: pl.DataFrame) -> Dict[str, Any]:
    kpis = compute_kpis(df)
    month = monthly_cashflow(df)
    cats = category_breakdown(df)
    merchants = top_merchants(df)
    score = compute_health_score(df)

    report = {
        "version": 1,
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "total_income": kpis.total_income,
            "total_expense": kpis.total_expense,
            "net_cashflow": kpis.net_cashflow,
            "savings_rate": kpis.savings_rate,
        },
        # Cast potential date columns to strings to ensure JSON serializable values
        "monthly_cashflow": month.with_columns(
            [
                pl.when(pl.col("month").is_not_null()).then(pl.col("month").cast(pl.Utf8)).otherwise(pl.lit(None)).alias("month")
            ]
        ).to_dicts(),
        "categories": cats.to_dicts(),
        "top_merchants": merchants.to_dicts(),
        "health_score": {
            "score": score.score,
            "components": score.components,
        },
        "advice": None,
    }
    return report
