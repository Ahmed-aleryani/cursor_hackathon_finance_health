from __future__ import annotations

import polars as pl

SUBSCRIPTION_KEYWORDS = [
    "subscription", "netflix", "spotify", "hulu", "apple music", "prime", "youtube",
    "membership", "audible", "xbox", "playstation", "icloud", "dropbox", "patreon",
]


def top_expense_transactions(df: pl.DataFrame, limit: int = 10) -> pl.DataFrame:
    if df.is_empty():
        return df
    return (
        df.filter(pl.col("amount") < 0)
        .select(["date", "merchant", "description", "amount"]) 
        .sort(pl.col("amount"))  # most negative first
        .head(limit)
    )


def recurring_candidates(df: pl.DataFrame, min_count: int = 3, limit: int = 15) -> pl.DataFrame:
    if df.is_empty() or "merchant" not in df.columns:
        return pl.DataFrame()
    # Group by merchant and rounded absolute amount to detect repeated similar charges
    rounded = (
        df.filter(pl.col("amount") < 0)
        .with_columns(pl.col("amount").abs().round(2).alias("abs_amount"))
        .group_by(["merchant", "abs_amount"]).agg([
            pl.count().alias("count"),
            pl.col("date").min().alias("first_date"),
            pl.col("date").max().alias("last_date"),
        ])
        .filter(pl.col("count") >= min_count)
        .sort(["count", "abs_amount"], descending=[True, True])
        .head(limit)
    )
    return rounded


def subscription_merchants(df: pl.DataFrame, limit: int = 15) -> pl.DataFrame:
    if df.is_empty():
        return df
    desc_lower = pl.col("description").cast(pl.String, strict=False).str.to_lowercase()
    pattern = "|".join(SUBSCRIPTION_KEYWORDS)
    subs = (
        df.filter((pl.col("amount") < 0) & desc_lower.str.contains(pattern))
        .group_by("merchant")
        .agg([(-pl.col("amount").sum()).alias("spend"), pl.count().alias("tx_count")])
        .sort(["spend", "tx_count"], descending=[True, True])
        .head(limit)
    )
    return subs
