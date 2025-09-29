from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


load_dotenv()  # load .env if present


@dataclass(frozen=True)
class AppConfig:
    app_env: str
    data_dir: Path
    db_path: Path
    ollama_host: str
    ollama_model: str
    ollama_model_ingest: str | None
    advice_backend: str  # 'langchain' | 'ollama_direct'
    ollama_num_predict: int
    ollama_num_ctx: int
    ollama_temperature: float


_config_singleton: Optional[AppConfig] = None


def _ensure_dirs(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "sessions").mkdir(parents=True, exist_ok=True)


def get_config() -> AppConfig:
    global _config_singleton
    if _config_singleton is not None:
        return _config_singleton

    app_env = os.getenv("APP_ENV", "dev")

    data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()
    db_path = Path(os.getenv("DB_PATH", str(data_dir / "metadata.db"))).resolve()

    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
    ollama_model_ingest = os.getenv("OLLAMA_MODEL_INGEST", "llama3.2:latest")
    advice_backend = os.getenv("ADVICE_BACKEND", "langchain").lower()
    if advice_backend not in {"langchain", "ollama_direct"}:
        advice_backend = "langchain"

    # Generation controls
    try:
        ollama_num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "1024"))
    except Exception:
        ollama_num_predict = 1024
    try:
        ollama_num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    except Exception:
        ollama_num_ctx = 8192
    try:
        ollama_temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))
    except Exception:
        ollama_temperature = 0.3

    _ensure_dirs(data_dir)

    _config_singleton = AppConfig(
        app_env=app_env,
        data_dir=data_dir,
        db_path=db_path,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        ollama_model_ingest=ollama_model_ingest,
        advice_backend=advice_backend,
        ollama_num_predict=ollama_num_predict,
        ollama_num_ctx=ollama_num_ctx,
        ollama_temperature=ollama_temperature,
    )
    return _config_singleton
