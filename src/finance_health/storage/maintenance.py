from __future__ import annotations

import shutil
from pathlib import Path

from ..settings.config import get_config


def reset_database_and_sessions() -> None:
    cfg = get_config()
    # Remove DB file
    if cfg.db_path.exists():
        cfg.db_path.unlink()
    # Remove sessions directory
    sessions_dir = cfg.data_dir / "sessions"
    if sessions_dir.exists():
        shutil.rmtree(sessions_dir)
    # Recreate base directories
    sessions_dir.mkdir(parents=True, exist_ok=True)
