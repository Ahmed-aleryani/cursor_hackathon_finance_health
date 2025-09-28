from __future__ import annotations

import json
from collections import Counter
from typing import Any, Dict, List
from pathlib import Path

import polars as pl

from ..settings.config import get_config
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

CATEGORIES = [
    "income",
    "rent_mortgage",
    "utilities",
    "groceries",
    "dining",
    "transport",
    "subscriptions",
    "shopping",
    "healthcare",
    "fees",
    "transfer",
    "other",
]


def _build_prompt(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    system = (
        "You are a transaction categorizer. Classify each merchant into ONE category from the allowed list. "
        f"Allowed categories: {', '.join(CATEGORIES)}. "
        "Use 'income' for positive amounts. Use 'transfer' for internal transfers. If uncertain, use 'other'. "
        "Return strictly minified JSON only (no markdown fences)."
    )
    user = json.dumps(payload, ensure_ascii=False)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


class AICategorizer:
    def __init__(self):
        self.cfg = get_config()
        try:
            from ollama import Client  # type: ignore
            self.client = Client(host=self.cfg.ollama_host)
        except Exception as e:
            logger.warning("Ollama not available for categorization: %s", e)
            self.client = None

    def _examples_by_merchant(self, df: pl.DataFrame, max_merchants: int = 100) -> List[Dict[str, Any]]:
        if df.is_empty() or "merchant" not in df.columns:
            return []
        # Count by merchant and collect sample descriptions and sign of amounts
        counts = df.groupby("merchant").agg([
            pl.count().alias("n"),
            pl.col("description").first().alias("example_description"),
            pl.col("amount").mean().alias("mean_amount"),
        ]).sort("n", descending=True).head(max_merchants)
        items = []
        for row in counts.iter_rows(named=True):
            items.append({
                "merchant": row["merchant"],
                "example_description": row.get("example_description"),
                "mean_amount": row.get("mean_amount"),
            })
        return items

    def categorize(self, df: pl.DataFrame, session_dir: Path) -> pl.DataFrame:
        if self.client is None or df.is_empty():
            return df
        mapping_path = session_dir / "categories_map.json"
        mapping: Dict[str, str] = {}
        if mapping_path.exists():
            try:
                mapping = json.loads(mapping_path.read_text())
            except Exception:
                mapping = {}
        # If mapping is too small, try to build
        unique_merchants = df.select(pl.col("merchant")).drop_nulls().unique().height if "merchant" in df.columns else 0
        if len(mapping) < unique_merchants:
            payload = {"merchants": self._examples_by_merchant(df, max_merchants=200)}
            msgs = _build_prompt(payload)
            try:
                model_name = getattr(self.cfg, "ollama_model_ingest", None) or self.cfg.ollama_model
                resp = self.client.chat(model=model_name, messages=msgs, stream=False)
                content = resp.get("message", {}).get("content", "")
                data = json.loads(content)
                for item in data:
                    m = (item.get("merchant") or "").strip()
                    c = (item.get("category") or "").strip().lower()
                    if m:
                        mapping[m] = c if c in CATEGORIES else "other"
                mapping_path.write_text(json.dumps(mapping, indent=2))
            except Exception as e:
                logger.warning("Categorization LLM failed: %s", e)
        if not mapping:
            return df
        # Apply mapping
        map_series = pl.Series("merchant", list(mapping.keys()))
        cat_series = pl.Series("_cat", list(mapping.values()))
        map_df = pl.DataFrame({"merchant": map_series, "_cat": cat_series})
        df = df.join(map_df, on="merchant", how="left")
        df = df.with_columns(pl.col("category").fill_null(pl.col("_cat")))
        df = df.drop("_cat")
        return df
