from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import polars as pl


NORMALIZED_COLUMNS = [
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


@dataclass(frozen=True)
class ParseResult:
    dataframe: pl.DataFrame
    source_file: Path
    errors: Optional[List[str]] = None


class Reader:
    def can_read(self, path: Path) -> bool:
        raise NotImplementedError

    def read(self, path: Path) -> pl.DataFrame:
        raise NotImplementedError


class Normalizer:
    def normalize(self, df: pl.DataFrame, source_file: Path, session_id: str) -> pl.DataFrame:
        raise NotImplementedError
