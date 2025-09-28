from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import polars as pl


@dataclass(frozen=True)
class KPIs:
    total_income: float
    total_expense: float
    net_cashflow: float
    savings_rate: float


def compute_kpis(df: pl.DataFrame) -> KPIs:
    if df.is_empty():
        return KPIs(0.0, 0.0, 0.0, 0.0)

    income = df.filter(pl.col("amount") > 0)["amount"].sum() or 0.0
    expense = df.filter(pl.col("amount") < 0)["amount"].sum() or 0.0
    expense_abs = abs(expense)
    net = income - expense_abs
    savings_rate = (net / income) if income > 0 else 0.0
    return KPIs(
        total_income=float(income),
        total_expense=float(expense_abs),
        net_cashflow=float(net),
        savings_rate=float(savings_rate),
    )


def monthly_cashflow(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df
    return (
        df.with_columns(pl.col("date").dt.truncate("1mo").alias("month"))
        .group_by("month")
        .agg([
            pl.col("amount").filter(pl.col("amount") > 0).sum().alias("income"),
            (-pl.col("amount").filter(pl.col("amount") < 0).sum()).alias("expense"),
        ])
        .with_columns((pl.col("income") - pl.col("expense")).alias("net"))
        .sort("month")
    )


def category_breakdown(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df
    cat_col = "category" if "category" in df.columns else None
    if not cat_col:
        # fallback: merchant as pseudo-category
        return (
            df.group_by("merchant")
            .agg([
                (-pl.col("amount").filter(pl.col("amount") < 0).sum()).alias("spend"),
            ])
            .sort("spend", descending=True)
        )
    return (
        df.group_by("category")
        .agg([
            (-pl.col("amount").filter(pl.col("amount") < 0).sum()).alias("spend"),
        ])
        .sort("spend", descending=True)
    )


def top_merchants(df: pl.DataFrame, limit: int = 10) -> pl.DataFrame:
    if df.is_empty():
        return df
    return (
        df.group_by("merchant")
        .agg([
            (-pl.col("amount").filter(pl.col("amount") < 0).sum()).alias("spend"),
            pl.count().alias("tx_count"),
        ])
        .sort(["spend", "tx_count"], descending=[True, True])
        .head(limit)
    )
