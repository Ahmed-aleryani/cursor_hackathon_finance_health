from __future__ import annotations

from pathlib import Path
import polars as pl


class XLSXReader:
    def can_read(self, path: Path) -> bool:
        return path.suffix.lower() in {".xlsx", ".xls"}

    def read(self, path: Path) -> pl.DataFrame:
        # Use first sheet by default; infer headers
        try:
            return pl.read_excel(path, sheet_name=0)
        except Exception:
            # Some files might need engine fallback; try openpyxl via pandas backend
            import pandas as pd
            df = pd.read_excel(path, sheet_name=0, engine="openpyxl")
            return pl.from_pandas(df)
