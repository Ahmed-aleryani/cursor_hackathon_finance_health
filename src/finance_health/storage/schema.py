from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Session:
    id: str
    created_at: datetime
    title: Optional[str]
    notes: Optional[str]
    data_dir: Path

    @property
    def session_dir(self) -> Path:
        return self.data_dir / "sessions" / self.id

    @property
    def originals_dir(self) -> Path:
        return self.session_dir / "originals"

    @property
    def logs_dir(self) -> Path:
        return self.session_dir / "logs"

    @property
    def normalized_path(self) -> Path:
        return self.session_dir / "normalized.parquet"

    @property
    def report_path(self) -> Path:
        return self.session_dir / "report.json"
