from __future__ import annotations

from pathlib import Path
import hashlib
import polars as pl
from datetime import datetime

from ...utils.text import clean_description, normalized_key


class BaseNormalizer:
    REQUIRED = ["date", "amount", "description"]

    def normalize(self, df: pl.DataFrame, source_file: Path, session_id: str) -> pl.DataFrame:
        # Standardize column names
        df = df.rename({c: c.strip().lower() for c in df.columns})

        # Try to find date/amount/description columns with common aliases
        date_col = self._pick_column(df, ["date", "transaction date", "posted date"]) or "date"
        amt_col = self._pick_column(df, ["amount", "amt", "value", "transaction amount"]) or "amount"
        desc_col = self._pick_column(df, ["description", "desc", "narrative", "details"]) or "description"

        # Coerce types
        df = df.with_columns([
            pl.col(date_col)
            .cast(pl.String, strict=False)
            .str.strip_chars()
            .str.replace_all(r"\.", "-")
            .str.replace_all(r"/", "-")
            .str.strptime(pl.Date, strict=False, format=None)
            .cast(pl.Date)
            .alias("date"),
            pl.col(amt_col)
            .cast(pl.String, strict=False)
            .str.replace_all(",", "")
            .str.replace_all(r"\$", "")
            .cast(pl.Float64, strict=False)
            .alias("amount"),
            pl.col(desc_col).cast(pl.String, strict=False).alias("description"),
        ]).drop_nulls(["date", "amount"])  # keep if description is null

        # Optional fields
        currency_col = self._pick_column(df, ["currency", "curr", "ccy"]) or None
        account_col = self._pick_column(df, ["account", "account name", "account number"]) or None
        balance_col = self._pick_column(df, ["balance", "running balance", "balance after"]) or None
        type_col = self._pick_column(df, ["type", "debit/credit", "dr/cr"]) or None

        df = df.with_columns([
            (pl.col(currency_col) if currency_col in df.columns else pl.lit("USD")).alias("currency"),
            (pl.col(account_col) if account_col in df.columns else pl.lit(None)).alias("account_name"),
            (pl.col(balance_col).cast(pl.Float64) if balance_col in df.columns else pl.lit(None)).alias("balance_after"),
            (
                pl.col(type_col)
                if type_col in df.columns
                else pl.when(pl.col("amount") < 0).then(pl.lit("debit")).otherwise(pl.lit("credit"))
            ).alias("type"),
        ])

        # Clean description and derive merchant key
        df = df.with_columns([
            pl.col("description").map_elements(clean_description).alias("description"),
            pl.col("description").map_elements(normalized_key).alias("merchant"),
        ])

        # Category placeholder (later rules/ML)
        df = df.with_columns(pl.lit(None).alias("category"))

        # Deterministic transaction id
        key_expr = pl.concat_str([
            pl.col("date").cast(pl.Utf8),
            pl.col("amount").round(2).cast(pl.Utf8),
            pl.col("merchant").cast(pl.Utf8),
            pl.col("account_name").fill_null("").cast(pl.Utf8),
        ], separator="|")
        df = df.with_columns(
            key_expr.map_elements(lambda s: hashlib.sha1(s.encode("utf-8")).hexdigest()).alias("transaction_id")
        )

        df = df.with_columns([
            pl.lit(str(source_file.name)).alias("source_file"),
            pl.lit(session_id).alias("session_id"),
        ])

        # Select and order columns
        wanted = [
            "transaction_id", "date", "amount", "currency", "description", "merchant",
            "category", "type", "account_name", "balance_after", "source_file", "session_id"
        ]
        for col in wanted:
            if col not in df.columns:
                df = df.with_columns(pl.lit(None).alias(col))
        df = df.select(wanted)

        # Dedupe
        df = df.unique(subset=["transaction_id"], keep="first")
        return df

    def _pick_column(self, df: pl.DataFrame, candidates: list[str]) -> str | None:
        for c in candidates:
            if c in df.columns:
                return c
        # try slightly different forms
        lowered = {c.lower(): c for c in df.columns}
        for c in candidates:
            if c.lower() in lowered:
                return lowered[c.lower()]
        return None
