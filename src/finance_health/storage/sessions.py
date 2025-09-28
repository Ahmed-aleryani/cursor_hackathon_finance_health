from __future__ import annotations

import secrets
from pathlib import Path
from typing import Optional

from ..utils.logging import setup_logger, attach_file_handler
from ..settings.config import get_config
from .repository import SessionRepository

logger = setup_logger(__name__)


def generate_session_id() -> str:
    return secrets.token_hex(8)


def create_session(title: Optional[str] = None, notes: Optional[str] = None) -> str:
    cfg = get_config()
    repo = SessionRepository(cfg.data_dir)
    session_id = generate_session_id()
    session = repo.create(session_id=session_id, title=title, notes=notes)

    # attach a file handler for this session
    attach_file_handler(logger, session.logs_dir / "session.log")
    logger.info("Created session %s", session_id)

    return session_id


def list_sessions():
    cfg = get_config()
    repo = SessionRepository(cfg.data_dir)
    return repo.list()
