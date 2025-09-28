from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import polars as pl

from ..settings.config import get_config
from ..storage.repository import SessionRepository
from ..storage.sessions import create_session
from ..analytics.report import build_report
from ..storage.report_io import save_report
from ..utils.logging import setup_logger
from .readers.csv_reader import CSVReader
from .readers.xlsx_reader import XLSXReader
from .normalizers.base_normalizer import BaseNormalizer
from .llm_extractor import LLMExtractor
from ..analytics.categorize import AICategorizer

logger = setup_logger(__name__)


class Ingestor:
    def __init__(self, session_id: str | None = None):
        self.cfg = get_config()
        self.repo = SessionRepository(self.cfg.data_dir)
        self.session_id = session_id or create_session()
        self.readers = [CSVReader(), XLSXReader()]
        self.normalizer = BaseNormalizer()
        self.llm = LLMExtractor()
        self.categorizer = AICategorizer()

    def ingest_files(self, files: Iterable[Path]) -> Path:
        session = self.repo.get(self.session_id)
        assert session is not None

        dfs: List[pl.DataFrame] = []
        for f in files:
            reader = next((r for r in self.readers if r.can_read(f)), None)
            if reader is None:
                logger.warning("No reader for file %s", f)
                continue
            logger.info("Reading %s", f)
            df_raw = reader.read(f)
            # AI-only ingestion
            df_norm = self.llm.extract_to_normalized(df_raw, source_file=f, session_id=self.session_id)
            # Fallback to deterministic if AI returns empty
            if df_norm.is_empty():
                df_norm = self.normalizer.normalize(df_raw, source_file=f, session_id=self.session_id)
            dfs.append(df_norm)

            # Save original
            target = session.originals_dir / f.name
            if f.resolve() != target.resolve():
                target.write_bytes(Path(f).read_bytes())

        if not dfs:
            raise ValueError("No readable files provided")

        df_all = pl.concat(dfs, how="vertical", rechunk=True)
        # AI categorize merchants into categories (best-effort)
        try:
            df_all = self.categorizer.categorize(df_all, session.session_dir)
        except Exception:
            pass
        # Ensure expected columns even if readers provided minimal schema
        for col, dtype in {
            "transaction_id": pl.String,
            "date": pl.Date,
            "amount": pl.Float64,
            "currency": pl.String,
            "description": pl.String,
            "merchant": pl.String,
            "category": pl.String,
            "type": pl.String,
            "account_name": pl.String,
            "balance_after": pl.Float64,
            "source_file": pl.String,
            "session_id": pl.String,
        }.items():
            if col not in df_all.columns:
                df_all = df_all.with_columns(pl.lit(None).cast(dtype).alias(col))
        df_all.write_parquet(session.normalized_path)
        logger.info("Wrote normalized parquet to %s", session.normalized_path)

        # Build and persist report skeleton
        report = build_report(self.session_id, df_all)
        save_report(self.session_id, report)
        logger.info("Saved report.json for session %s", self.session_id)
        return session.normalized_path
