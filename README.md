# Finance Health (Local)

## Cursor Hackathon

- Built during the Cursor hackathon; we used Cursor CLI to plan and build this project end-to-end.
- Event: [Cursor community event on Luma](https://luma.com/52oq8z1t)

Local-first finance health checker: import bank statements (CSV/XLSX now; PDF/DOCX next), analyze with fast analytics (Polars) and local AI advice (LangChain/LangGraph + Ollama), and view dashboards in Streamlit.

## Requirements
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended)
- [Ollama](https://ollama.com/) for local LLM (advice phase)

## Setup
```bash
# from project root
uv venv
source .venv/bin/activate
uv pip install -e .[dev]

# optional: pull models
ollama pull deepseek-r1:8b
ollama pull llama3.2:latest

# copy env and adjust
cp .env.example .env
```

## Run
```bash
# ensure env is loaded
source .venv/bin/activate
export $(grep -v '^#' .env | xargs -I{} echo {})

streamlit run src/finance_health/ui/app.py
```

## Project layout
```
finance_health/
  src/finance_health/
    ui/
      pages/
    parsing/
    analytics/
    advice/
    storage/
    settings/
    utils/
  data/
    sessions/
  samples/
  tests/
```

## Modes
- **INGEST_MODE**:
  - `ai` (default): AI extracts structure from free-form CSV/XLSX text via Ollama
- **ADVICE_BACKEND**:
  - `langchain` (default): LangChain ReAct agent calling tools to fetch metrics and save advice
  - `ollama_direct`: direct chat with system+user prompt

## Configuration
Copy `.env.example` to `.env` and adjust if needed. By default, data is stored under `./data` with Parquet per session and a SQLite metadata DB.

Key envs:

```
APP_ENV=dev
DATA_DIR=./data
DB_PATH=./data/metadata.db
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_MODEL_INGEST=llama3.2:latest
INGEST_MODE=ai
ADVICE_BACKEND=langchain
```

Notes:
- Use smaller models if needed, e.g. `qwen2.5:7b`.
- Ensure `ollama serve` is running and the model is pulled.

# cursor_hackathon_finance_health
