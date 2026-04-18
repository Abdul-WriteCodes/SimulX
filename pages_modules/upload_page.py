"""
Upload logic — extraction is triggered from the sidebar Extract button.
This module provides run_extraction_from_queue() called by app.py.
"""
import streamlit as st
from utils.parser import extract_text, smart_truncate
from core.extractor import extract_paper


def run_extraction_from_queue():
    """Process all queued files that haven't been extracted yet."""
    queued = st.session_state.get("queued_files", [])
    extracted = st.session_state.get("extracted_papers", [])
    extracted_names = {p.get("_source_file") for p in extracted}

    pending = [f for f in queued if f["name"] not in extracted_names]
    if not pending:
        return

    total = len(pending)
    progress = st.progress(0.0)
    status   = st.empty()
    log_box  = st.container()
    errors   = []

    for i, finfo in enumerate(pending):
        fname = finfo["name"]
        fobj  = finfo.get("obj")

        with log_box:
            st.markdown(f"""
            <div class="proc-step">
                <span class="proc-icon">🔍</span>
                Parsing <strong>{fname}</strong>…
            </div>
            """, unsafe_allow_html=True)

        try:
            raw_bytes = fobj.read() if fobj else b""
            if not raw_bytes:
                raise ValueError("File is empty or could not be read.")

            text = extract_text(raw_bytes, fname)
            if len(text.strip()) < 150:
                raise ValueError("Too little text extracted — file may be image-based.")

            text = smart_truncate(text, max_tokens=12000)

            with log_box:
                st.markdown(f"""
                <div class="proc-step">
                    <span class="proc-icon">🧠</span>
                    Extracting empirical data from <strong>{fname}</strong>…
                </div>
                """, unsafe_allow_html=True)

            result = extract_paper(text, filename=fname)
            extracted.append(result)

            with log_box:
                st.markdown(f"""
                <div class="proc-step">
                    <span class="proc-icon">✅</span>
                    <strong>{fname}</strong> — complete
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            errors.append(f"**{fname}**: {e}")
            with log_box:
                st.markdown(f"""
                <div class="proc-step">
                    <span class="proc-icon">⚠️</span>
                    Skipped <strong>{fname}</strong>: {e}
                </div>
                """, unsafe_allow_html=True)

        progress.progress((i + 1) / total)

    st.session_state["extracted_papers"] = extracted
    st.session_state["synthesis_result"] = None
    st.session_state["processing_errors"] = errors
    progress.empty()

    if extracted:
        status.success(f"✅  {len(extracted)} paper(s) extracted and ready.")
    if errors:
        for e in errors:
            st.warning(e)
