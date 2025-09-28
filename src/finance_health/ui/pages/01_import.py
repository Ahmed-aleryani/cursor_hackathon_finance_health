from __future__ import annotations

from pathlib import Path
import sys
from pathlib import Path
_p = Path(__file__).resolve()
for _ in range(6):
    if _p.name == "src":
        break
    _p = _p.parent
if _p.name == "src" and str(_p) not in sys.path:
    sys.path.insert(0, str(_p))
import tempfile
import streamlit as st

from finance_health.parsing.ingest import Ingestor
from finance_health.storage.sessions import create_session
from finance_health.ui.state import set_session_id

st.title("📥 Import Statements")
st.info("CSV and XLSX supported in MVP. PDF/DOCX coming in Phase 2.")

uploaded_files = st.file_uploader(
    "Upload one or more files", type=["csv", "xlsx"], accept_multiple_files=True
)

def _persist_uploaded(tmp_dir: Path, files):
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_paths = []
    for f in files:
        p = tmp_dir / f.name
        with open(p, "wb") as fp:
            fp.write(f.getbuffer())
        out_paths.append(p)
    return out_paths

if uploaded_files:
    col1, col2 = st.columns([1,1])
    with col1:
        title = st.text_input("Optional session title", placeholder="e.g., Chase Jan–Mar 2025")
    with col2:
        notes = st.text_input("Optional notes")

    if st.button("Process Files", type="primary"):
        with st.spinner("Creating session and processing files..."):
            sid = create_session(title=title or None, notes=notes or None)
            set_session_id(sid)
            with tempfile.TemporaryDirectory(prefix=f"fh_{sid}_") as d:
                tmp_dir = Path(d)
                paths = _persist_uploaded(tmp_dir=tmp_dir, files=uploaded_files)
                ingestor = Ingestor(session_id=sid)
                parquet_path = ingestor.ingest_files(paths)
        st.success(f"Processed {len(paths)} file(s). Session: {sid}")
        st.caption(f"Saved normalized data: {parquet_path}")
        if hasattr(st, "page_link"):
            st.page_link("pages/02_dashboard.py", label="Go to Dashboard", icon="👉")
        else:
            st.info("Use the sidebar to open Dashboard.")
