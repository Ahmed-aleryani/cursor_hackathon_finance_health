from __future__ import annotations

import json
import re
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import polars as pl

from ..settings.config import get_config
from ..utils.logging import setup_logger
from ..utils.text import clean_description, normalized_key

logger = setup_logger(__name__)


JSON_FALLBACK_SCHEMA = [
    "date",
    "description",
    "amount",
    "currency",
    "type",
    "account_name",
    "balance_after",
    "merchant",
    "category",
]


@dataclass
class LLMExtractor:
    def __post_init__(self):
        self.cfg = get_config()
        try:
            from ollama import Client  # type: ignore
            self.client = Client(host=self.cfg.ollama_host)
        except Exception as e:
            logger.warning("Ollama not available: %s. Using deterministic fallback.", e)
            self.client = None

    def _table_to_text(self, df: pl.DataFrame, max_rows: int = 500) -> str:
        # Prefer pandas to ensure consistent CSV as text
        pdf = df.head(max_rows).to_pandas()
        return pdf.to_csv(index=False)

    def _build_prompt(self, filename: str, table_text: str) -> List[Dict[str, str]]:
        system = (
            "You are a local financial statement extractor. Extract transactions from the provided table text. "
            "Identify columns automatically (date, description, amount, currency, type, account_name, balance_after, merchant, category). "
            "Return strictly minified JSON only (no markdown/code fences), as an array of objects. "
            "Dates must be ISO (YYYY-MM-DD). Amounts must be numbers (negative for debits). Currency default USD if unknown. "
            "Infer merchant from description when possible. Leave category null if unsure."
        )
        user = (
            f"File: {filename}\n"
            f"Table CSV:\n{table_text}\n\n"
            "Output JSON array with objects using keys: date, description, amount, currency, type, account_name, balance_after, merchant, category."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _parse_json_from_text(self, text: str) -> List[Dict[str, Any]]:
        # Try direct parse
        text = text.strip()
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except Exception:
            pass
        # Try to extract first JSON array via regex
        match = re.search(r"\[(?:.|\n|\r)*\]", text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        # Nothing parsable
        return []

    def _to_polars(self, items: List[Dict[str, Any]], source_file: Path, session_id: str) -> pl.DataFrame:
        if not items:
            return pl.DataFrame()
        # Normalize dicts to expected keys
        norm_items: List[Dict[str, Any]] = []
        for it in items:
            obj = {k: it.get(k) for k in JSON_FALLBACK_SCHEMA}
            norm_items.append(obj)
        df = pl.DataFrame(norm_items)
        # Coerce types
        if "date" in df.columns:
            df = df.with_columns(
                pl.col("date").cast(pl.String, strict=False).str.strptime(pl.Date, strict=False).cast(pl.Date)
            )
        if "amount" in df.columns:
            df = df.with_columns(
                pl.col("amount")
                .cast(pl.String, strict=False)
                .str.replace_all(",", "")
                .str.replace_all(r"\$", "")
                .cast(pl.Float64, strict=False)
            )
        # Defaults
        if "currency" not in df.columns:
            df = df.with_columns(pl.lit("USD").alias("currency"))
        else:
            df = df.with_columns(pl.col("currency").fill_null("USD"))
        if "description" in df.columns:
            df = df.with_columns(pl.col("description").cast(pl.String, strict=False))
            df = df.with_columns(pl.col("description").map_elements(clean_description).alias("description"))
            df = df.with_columns(pl.col("description").map_elements(normalized_key).alias("merchant"))
        # Ensure type and correct sign of amount based on type/heuristics
        if "type" not in df.columns:
            df = df.with_columns(
                pl.when(pl.col("amount") < 0).then(pl.lit("debit")).otherwise(pl.lit("credit")).alias("type")
            )
        else:
            # normalize type text
            df = df.with_columns(pl.col("type").cast(pl.String, strict=False).str.to_lowercase())

        # Heuristic: adjust sign by type when present
        df = df.with_columns(
            pl.when(pl.col("type").is_in(["debit", "dr", "withdrawal", "payment", "charge"]))
            .then(-pl.col("amount").abs())
            .when(pl.col("type").is_in(["credit", "cr", "deposit", "salary", "refund"]))
            .then(pl.col("amount").abs())
            .otherwise(pl.col("amount"))
            .alias("amount")
        )

        # Additional heuristic if type is unknown: use description keywords
        income_kw = ["salary", "payroll", "deposit", "refund", "rebate", "payment received", "payout", "income", "transfer in"]
        expense_kw = ["rent", "bill", "utility", "electric", "internet", "grocer", "market", "subscription", "spotify", "fee", "gas", "transport", "fuel", "restaurant", "dining", "coffee", "charge"]
        if "description" in df.columns:
            desc_lower = pl.col("description").cast(pl.String, strict=False).str.to_lowercase()
            df = df.with_columns(
                pl.when(desc_lower.str.contains("|".join(income_kw)))
                .then(pl.col("amount").abs())
                .when(desc_lower.str.contains("|".join(expense_kw)))
                .then(-pl.col("amount").abs())
                .otherwise(pl.col("amount"))
                .alias("amount")
            )
        # Align expected columns
        for col in [
            "merchant",
            "category",
            "account_name",
            "balance_after",
        ]:
            if col not in df.columns:
                df = df.with_columns(pl.lit(None).alias(col))
        df = df.with_columns([
            pl.lit(source_file.name).alias("source_file"),
            pl.lit(session_id).alias("session_id"),
        ])
        # transaction_id
        key_expr = pl.concat_str([
            pl.col("date").cast(pl.Utf8),
            pl.col("amount").round(2).cast(pl.Utf8),
            pl.col("merchant").cast(pl.Utf8),
            pl.col("account_name").fill_null("").cast(pl.Utf8),
        ], separator="|")
        df = df.with_columns(
            key_expr.map_elements(lambda s: hashlib.sha1(s.encode("utf-8")).hexdigest()).alias("transaction_id")
        )
        # Column order
        wanted = [
            "transaction_id",
            "date",
            "amount",
            "currency",
            "description",
            "merchant",
            "category",
            "type",
            "account_name",
            "balance_after",
            "source_file",
            "session_id",
        ]
        for col in wanted:
            if col not in df.columns:
                df = df.with_columns(pl.lit(None).alias(col))
        return df.select(wanted).drop_nulls(["date", "amount"])

    def extract_to_normalized(self, df_raw: pl.DataFrame, source_file: Path, session_id: str) -> pl.DataFrame:
        # Convert table to text
        table_text = self._table_to_text(df_raw)
        if self.client is None:
            logger.warning("Ollama client missing; passing through with minimal coercion.")
            # Fallback: best-effort map existing df
            return self._to_polars([], source_file, session_id)
        messages = self._build_prompt(source_file.name, table_text)
        try:
            model_name = getattr(self.cfg, "ollama_model_ingest", None) or self.cfg.ollama_model
            resp = self.client.chat(model=model_name, messages=messages, stream=False)
            content = resp.get("message", {}).get("content", "")
        except Exception as e:
            logger.error("LLM extraction failed: %s", e)
            content = ""
        items = self._parse_json_from_text(content)
        if not items:
            logger.warning("LLM returned no parsable items; falling back to empty result.")
        return self._to_polars(items, source_file, session_id)
