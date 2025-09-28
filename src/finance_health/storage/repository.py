from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

from ..settings.config import get_config
from .schema import Session


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                title TEXT,
                notes TEXT
            )
            """
        )
        conn.commit()


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    cfg = get_config()
    _ensure_db(cfg.db_path)
    conn = sqlite3.connect(cfg.db_path)
    try:
        yield conn
    finally:
        conn.close()


class SessionRepository:
    def __init__(self, data_dir: Optional[Path] = None):
        self.cfg = get_config()
        self.data_dir = data_dir or self.cfg.data_dir

    def create(self, session_id: str, title: Optional[str] = None, notes: Optional[str] = None) -> Session:
        created_at = datetime.utcnow().isoformat()
        with _conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, created_at, title, notes) VALUES (?, ?, ?, ?)",
                (session_id, created_at, title, notes),
            )
            conn.commit()

        session = Session(
            id=session_id,
            created_at=datetime.fromisoformat(created_at),
            title=title,
            notes=notes,
            data_dir=self.data_dir,
        )
        # Ensure filesystem structure
        session.session_dir.mkdir(parents=True, exist_ok=True)
        session.originals_dir.mkdir(parents=True, exist_ok=True)
        session.logs_dir.mkdir(parents=True, exist_ok=True)
        return session

    def get(self, session_id: str) -> Optional[Session]:
        with _conn() as conn:
            row = conn.execute(
                "SELECT id, created_at, title, notes FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        id_, created_at, title, notes = row
        return Session(
            id=id_,
            created_at=datetime.fromisoformat(created_at),
            title=title,
            notes=notes,
            data_dir=self.data_dir,
        )

    def list(self) -> List[Session]:
        with _conn() as conn:
            rows = conn.execute(
                "SELECT id, created_at, title, notes FROM sessions ORDER BY created_at DESC"
            ).fetchall()
        sessions: List[Session] = []
        for id_, created_at, title, notes in rows:
            sessions.append(
                Session(
                    id=id_,
                    created_at=datetime.fromisoformat(created_at),
                    title=title,
                    notes=notes,
                    data_dir=self.data_dir,
                )
            )
        return sessions
