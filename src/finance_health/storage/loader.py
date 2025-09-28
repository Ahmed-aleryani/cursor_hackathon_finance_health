from __future__ import annotations

from pathlib import Path
import polars as pl

from .repository import SessionRepository
from ..settings.config import get_config


def get_session(session_id: str):
    cfg = get_config()
    repo = SessionRepository(cfg.data_dir)
    return repo.get(session_id)


def load_normalized_df(session_id: str) -> pl.DataFrame:
    session = get_session(session_id)
    if session is None or not session.normalized_path.exists():
        return pl.DataFrame()
    return pl.read_parquet(session.normalized_path)
