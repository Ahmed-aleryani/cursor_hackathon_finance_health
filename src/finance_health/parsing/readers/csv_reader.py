from __future__ import annotations

from pathlib import Path
import polars as pl

from ...utils.logging import setup_logger

logger = setup_logger(__name__)


class CSVReader:
    def can_read(self, path: Path) -> bool:
        return path.suffix.lower() == ".csv"

    def read(self, path: Path) -> pl.DataFrame:
        try:
            return pl.read_csv(path, infer_schema_length=1000)
        except Exception:
            logger.info("Retrying CSV read with semicolon delimiter for %s", path)
            return pl.read_csv(path, separator=";", infer_schema_length=1000)
