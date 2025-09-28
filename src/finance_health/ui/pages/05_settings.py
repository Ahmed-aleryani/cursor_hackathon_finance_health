import streamlit as st
from finance_health.settings.config import get_config
from finance_health.storage.maintenance import reset_database_and_sessions

st.title("⚙️ Settings")
st.caption("Configure data directory, model, thresholds, and category rules.")

cfg = get_config()
st.subheader("Runtime Configuration")
st.code(
    f"""
APP_ENV={cfg.app_env}
DATA_DIR={cfg.data_dir}
DB_PATH={cfg.db_path}
OLLAMA_HOST={cfg.ollama_host}
OLLAMA_MODEL={cfg.ollama_model}
INGEST_MODE={cfg.ingest_mode}
ADVICE_BACKEND={cfg.advice_backend}
""".strip()
)

st.caption("Edit your .env to change values, then restart the app.")

st.divider()
st.subheader("Maintenance")
if st.button("Reset database and sessions", type="secondary"):
    reset_database_and_sessions()
    st.success("Database and sessions reset. Go to Import to start fresh.")
