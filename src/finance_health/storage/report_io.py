from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .repository import SessionRepository
from ..settings.config import get_config


def _get_paths(session_id: str):
    cfg = get_config()
    repo = SessionRepository(cfg.data_dir)
    session = repo.get(session_id)
    if session is None:
        raise ValueError(f"Unknown session: {session_id}")
    return session.report_path


def _default_serializer(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def save_report(session_id: str, report: Dict[str, Any]) -> Path:
    report_path = _get_paths(session_id)
    report_path.write_text(json.dumps(report, indent=2, default=_default_serializer))
    return report_path


def load_report(session_id: str) -> Optional[Dict[str, Any]]:
    report_path = _get_paths(session_id)
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text())
