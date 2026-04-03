import streamlit as st
from openai import OpenAI
import json
import time
import zipfile
import io
from pathlib import Path

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SLR Analyser",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: #f8fafc !important; }

.main-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 50%, #1d4ed8 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 24px rgba(30,64,175,0.25);
}
.main-header h1 { color: #f0f9ff; font-size: 2rem; font-weight: 700; margin: 0; }
.main-header p  { color: #bae6fd; margin: 0.5rem 0 0; font-size: 1rem; }

.paper-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.meta-badge {
    display: inline-block;
    background: #dbeafe;
    color: #1e40af;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 3px 4px 3px 0;
}
.meta-badge.green  { background: #dcfce7; color: #166534; }
.meta-badge.purple { background: #f3e8ff; color: #6b21a8; }
.meta-badge.amber  { background: #fef3c7; color: #92400e; }

.step-bar { display: flex; gap: 8px; margin-bottom: 1.5rem; align-items: center; }
.step {
    display: flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 600;
}
.step.done    { background:#dcfce7; color:#166534; }
.step.active  { background:#dbeafe; color:#1e40af; }
.step.pending { background:#f1f5f9; color:#94a3b8; }

div[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Text extraction helpers ────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = [p.extract_text() or "" for p in reader.pages]
        text = "\n\n".join(pages).strip()
        return text if text else "[PDF contained no extractable text — may be scanned]"
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


def extract_text(file_name: str, file_bytes: bytes) -> str:
    ext = Path(file_name).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    else:
        return file_bytes.decode("utf-8", errors="replace")


# ── OpenAI helpers ─────────────────────────────────────────────────────────────

def get_client() -> OpenAI:
    return OpenAI(api_key=st.session_state.api_key)


def call_gpt(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    """Call GPT-4o-mini and return text response."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=max_tokens,
        temperature=0.2,
        messages=messages,
    )
    return resp.choices[0].message.content.strip()


def abstract_paper(title: str, text: str) -> dict:
    system = (
        "You are an expert systematic literature review assistant. "
        "Extract structured metadata from academic papers. "
        "Always respond with valid JSON only — no markdown fences, no commentary."
    )
    prompt = f"""Extract the following fields from this paper. If a field cannot be determined, use null.

Return ONLY a raw JSON object with these exact keys:
- "title": string (use paper's actual title if found, otherwise use the filename)
- "authors": list of strings
- "year": string or null
- "journal_or_venue": string or null
- "methodology_design": string (e.g., RCT, qualitative, systematic review, survey, case study, mixed methods)
- "sample_size": string or null
- "main_findings": string (2-4 sentences)
- "contributions": string (1-3 key contributions as a single string)
- "limitations": string or null
- "keywords": list of strings (up to 8)

PAPER FILENAME: {title}

PAPER TEXT (first 6000 chars):
{text[:6000]}
"""
    raw = call_gpt(prompt, system=system, max_tokens=1200)
    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()
    try:
        data = json.loads(raw)
    except Exception:
        data = {
            "title": title, "authors": [], "year": None,
            "journal_or_venue": None, "methodology_design": "Unknown",
            "sample_size": None, "main_findings": raw[:500],
            "contributions": "", "limitations": None, "keywords": []
        }
    # Fallback title
    if not data.get("title") or str(data.get("title")).lower() == "null":
        data["title"] = title
    return data


def identify_themes(abstractions: list) -> str:
    system = (
        "You are an expert systematic review analyst. "
        "Synthesise findings across multiple studies into coherent thematic narratives."
    )
    summaries = []
    for i, p in enumerate(abstractions, 1):
        summaries.append(
            f"Paper {i}: {p.get('title','N/A')}\n"
            f"  Year: {p.get('year','?')} | Method: {p.get('methodology_design','?')}\n"
            f"  Findings: {p.get('main_findings','')}\n"
            f"  Contributions: {p.get('contributions','')}\n"
            f"  Keywords: {', '.join(p.get('keywords') or [])}"
        )
    combined = "\n\n".join(summaries)
    prompt = f"""You have been given data abstractions from {len(abstractions)} academic papers.

{combined}

Perform a thematic synthesis:
1. Identify 4-7 major themes that cut across these papers.
2. For each theme: give it a clear title, explain it in 3-5 sentences citing which papers (by number) support it, and note any contradictions or gaps.
3. Write a concluding paragraph about overall research trajectory and future directions.

Format your response in clean markdown with ## headings for each theme.
"""
    return call_gpt(prompt, system=system, max_tokens=3000)


def write_synthesis_report(abstractions: list, themes_text: str) -> str:
    system = "You are an expert academic writer specialising in systematic literature reviews."
    years = sorted({str(p.get('year','?')) for p in abstractions if p.get('year')})
    metadata_summary = f"{len(abstractions)} papers | Years: {', '.join(years) if years else 'N/A'}"
    prompt = f"""Write a comprehensive synthesis section for a systematic literature review.

METADATA OVERVIEW: {metadata_summary}

THEMATIC ANALYSIS:
{themes_text}

Write the synthesis in formal academic prose (600-900 words). Include:
- An opening paragraph contextualising the body of literature
- A paragraph for each major theme weaving evidence from multiple papers
- Discussion of methodological diversity and notable limitations across studies
- A concluding paragraph on implications and research gaps

Use hedged academic language. Do not use first person. Use markdown formatting.
"""
    return call_gpt(prompt, system=system, max_tokens=3000)


def build_export(abstractions: list, themes: str, synthesis: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("abstractions.json", json.dumps(abstractions, indent=2))
        zf.writestr("themes.md", themes)
        zf.writestr("synthesis_report.md", synthesis)
        import csv
        csv_buf = io.StringIO()
        fields = ["title","authors","year","journal_or_venue","methodology_design",
                  "sample_size","main_findings","contributions","limitations","keywords"]
        writer = csv.DictWriter(csv_buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for p in abstractions:
            row = {k: (", ".join(v) if isinstance(v, list) else (v or "")) for k, v in p.items()}
            writer.writerow(row)
        zf.writestr("abstractions_summary.csv", csv_buf.getvalue())
    return buf.getvalue()


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "api_key": "",
    "step": 0,
    "abstractions": [],
    "themes": "",
    "synthesis": "",
    # ✅ FIX: store file bytes immediately at upload time, keyed by name
    "file_store": {},   # { filename: bytes }
    "file_names": [],   # ordered list of filenames
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 SLR Analyser")
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-...",
        help="Get your key at platform.openai.com"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input

    st.markdown("---")
    st.markdown("### 📋 What this tool does")
    st.markdown("""
- **Extracts** text from PDF, DOCX, TXT
- **Abstracts** each paper: authors, year, method, findings, contributions, limitations, keywords
- **Identifies** 4–7 key themes across the corpus
- **Writes** a formal academic synthesis
- **Exports** JSON, CSV & Markdown reports
""")
    st.markdown("---")
    st.markdown("### 🤖 Model")
    st.markdown("`gpt-4o-mini` · fast & cost-efficient")
    st.markdown("### 📄 Supported formats")
    st.markdown("`.pdf` · `.docx` · `.txt`")

    if st.session_state.step > 0:
        st.markdown("---")
        if st.button("🔄 Start New Review", use_container_width=True):
            for k in ["step","abstractions","themes","synthesis","file_store","file_names"]:
                st.session_state[k] = {} if k == "file_store" else ([] if k in ("abstractions","file_names") else ("" if k in ("themes","synthesis") else 0))
            st.rerun()


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🔬 Systematic Literature Review Analyser</h1>
  <p>Upload your papers · Extract structured data · Identify themes · Generate synthesis</p>
</div>
""", unsafe_allow_html=True)

# Step bar
steps = ["📤 Upload", "🔍 Abstract", "🧵 Themes", "✅ Results"]
step_html = '<div class="step-bar">'
for i, label in enumerate(steps):
    cls = "done" if i < st.session_state.step else ("active" if i == st.session_state.step else "pending")
    step_html += f'<div class="step {cls}">{label}</div>'
    if i < len(steps) - 1:
        step_html += '<span style="color:#cbd5e1">›</span>'
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 0 — Upload
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 0:
    st.markdown("### Step 1 — Upload Papers")
    st.caption("Select one or more PDF, DOCX, or TXT files. You can upload as many as you need.")

    uploaded = st.file_uploader(
        "Drop your papers here",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # ✅ FIX: Read bytes immediately when files are uploaded — before any rerun
    if uploaded:
        file_store = {}
        file_names = []
        for f in uploaded:
            # getvalue() reads the full buffer safely regardless of position
            file_store[f.name] = f.getvalue()
            file_names.append(f.name)

        st.success(f"✅ {len(uploaded)} file(s) loaded and ready")

        # Preview grid
        cols = st.columns(3)
        for i, fname in enumerate(file_names):
            size_kb = len(file_store[fname]) / 1024
            cols[i % 3].markdown(
                f'<div class="paper-card">'
                f'<b style="font-size:.85rem">📄 {fname}</b><br>'
                f'<span style="font-size:.75rem;color:#64748b">{size_kb:.1f} KB · '
                f'{Path(fname).suffix.upper()[1:]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("")
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if not st.session_state.api_key:
                st.warning("⚠️ Enter your OpenAI API key in the sidebar first")
            else:
                if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                    # Persist bytes into session state before rerun
                    st.session_state.file_store = file_store
                    st.session_state.file_names = file_names
                    st.session_state.step = 1
                    st.rerun()
    else:
        # Friendly empty state
        st.markdown("""
        <div style="border:2px dashed #cbd5e1;border-radius:12px;padding:3rem;text-align:center;color:#94a3b8;margin-top:1rem">
            <div style="font-size:2.5rem">📂</div>
            <div style="font-size:1rem;font-weight:600;margin-top:.5rem">Drag & drop your papers here</div>
            <div style="font-size:0.85rem;margin-top:.25rem">PDF · DOCX · TXT · Multiple files supported</div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Abstraction
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 1:
    st.markdown("### Step 2 — Data Abstraction")
    st.info("Extracting structured metadata from each paper using GPT-4o-mini…")

    file_store = st.session_state.file_store
    file_names = st.session_state.file_names

    if not file_names:
        st.error("No files found — please go back and upload your papers.")
        if st.button("← Back to Upload"):
            st.session_state.step = 0
            st.rerun()
    else:
        progress_bar = st.progress(0)
        status_box   = st.empty()
        abstractions = []

        for idx, fname in enumerate(file_names):
            status_box.markdown(
                f"**Processing** `{fname}` — paper {idx+1} of {len(file_names)}…"
            )
            fbytes = file_store[fname]
            text = extract_text(fname, fbytes)

            # Show extraction preview
            if text.startswith("["):
                st.warning(f"⚠️ {fname}: {text}")

            try:
                data = abstract_paper(fname, text)
            except Exception as e:
                st.warning(f"⚠️ Could not abstract `{fname}`: {e}")
                data = {
                    "title": fname, "authors": [], "year": None,
                    "journal_or_venue": None, "methodology_design": "Error",
                    "sample_size": None, "main_findings": f"Error during abstraction: {e}",
                    "contributions": "", "limitations": None, "keywords": []
                }

            abstractions.append(data)
            progress_bar.progress((idx + 1) / len(file_names))
            time.sleep(0.2)

        st.session_state.abstractions = abstractions
        status_box.success(f"✅ Successfully abstracted {len(abstractions)} paper(s)!")
        st.session_state.step = 2
        time.sleep(1)
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Theme identification & synthesis
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown("### Step 3 — Theme Identification & Synthesis")
    st.info("Identifying cross-cutting themes and generating synthesis narrative…")

    with st.spinner("🧵 Analysing themes across papers…"):
        try:
            themes = identify_themes(st.session_state.abstractions)
            st.session_state.themes = themes
        except Exception as e:
            st.session_state.themes = f"Theme analysis error: {e}"
            st.error(f"Theme analysis failed: {e}")

    with st.spinner("✍️ Writing synthesis report…"):
        try:
            synthesis = write_synthesis_report(
                st.session_state.abstractions, st.session_state.themes
            )
            st.session_state.synthesis = synthesis
        except Exception as e:
            st.session_state.synthesis = f"Synthesis error: {e}"
            st.error(f"Synthesis failed: {e}")

    st.session_state.step = 3
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Results
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    abstractions = st.session_state.abstractions
    themes       = st.session_state.themes
    synthesis    = st.session_state.synthesis

    # ── Metrics row
    years = [p.get("year") for p in abstractions if p.get("year")]
    methods = [p.get("methodology_design","") for p in abstractions]
    all_kws = [k for p in abstractions for k in (p.get("keywords") or [])]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📄 Papers Analysed", len(abstractions))
    m2.metric("📅 Year Range",
              f"{min(years, default='?')} – {max(years, default='?')}" if years else "N/A")
    m3.metric("🧪 Study Designs",
              len({m for m in methods if m and m not in ("Unknown","Error")}))
    m4.metric("🔑 Unique Keywords", len(set(all_kws)))

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📑 Paper Abstractions", "🧵 Themes & Synthesis", "📊 Overview Table"])

    # ── Tab 1
    with tab1:
        st.markdown(f"#### {len(abstractions)} Paper Abstractions")
        for p in abstractions:
            with st.expander(f"📄 {p.get('title','Untitled')}", expanded=False):
                c1, c2 = st.columns([3, 1])
                with c1:
                    authors = p.get("authors") or []
                    if authors:
                        st.markdown(f"**Authors:** {', '.join(authors[:5])}{'…' if len(authors)>5 else ''}")
                    st.markdown(f"**Journal/Venue:** {p.get('journal_or_venue') or '_Not identified_'}")
                with c2:
                    badges = ""
                    if p.get("year"):
                        badges += f'<span class="meta-badge amber">{p["year"]}</span>'
                    if p.get("methodology_design"):
                        badges += f'<span class="meta-badge purple">{p["methodology_design"]}</span>'
                    if p.get("sample_size"):
                        badges += f'<span class="meta-badge green">n={p["sample_size"]}</span>'
                    if badges:
                        st.markdown(badges, unsafe_allow_html=True)

                st.markdown("**Main Findings:**")
                st.markdown(p.get("main_findings") or "_Not available_")
                st.markdown("**Contributions:**")
                st.markdown(p.get("contributions") or "_Not available_")
                if p.get("limitations"):
                    st.markdown("**Limitations:**")
                    st.markdown(p["limitations"])
                kws = p.get("keywords") or []
                if kws:
                    kw_html = " ".join(f'<span class="meta-badge">{k}</span>' for k in kws)
                    st.markdown(f"**Keywords:** {kw_html}", unsafe_allow_html=True)

    # ── Tab 2
    with tab2:
        sub1, sub2 = st.tabs(["🧵 Key Themes", "✍️ Synthesis Narrative"])
        with sub1:
            st.markdown(themes)
        with sub2:
            st.markdown(synthesis)

    # ── Tab 3
    with tab3:
        st.markdown("#### Corpus Overview")
        import pandas as pd
        rows = []
        for p in abstractions:
            title = p.get("title","")
            rows.append({
                "Title": title[:65] + ("…" if len(title) > 65 else ""),
                "Year": p.get("year") or "?",
                "Method": p.get("methodology_design") or "?",
                "First Author": (p.get("authors") or ["?"])[0],
                "Venue": (p.get("journal_or_venue") or "?")[:45],
                "Keywords": ", ".join((p.get("keywords") or [])[:4]),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Export
    st.markdown("---")
    st.markdown("### 📦 Export Results")
    col1, col2 = st.columns([2, 3])
    with col1:
        zip_bytes = build_export(abstractions, themes, synthesis)
        st.download_button(
            label="⬇️ Download Full Package (.zip)",
            data=zip_bytes,
            file_name="slr_results.zip",
            mime="application/zip",
            use_container_width=True,
        )
    with col2:
        st.caption(
            "Zip contains: `abstractions.json` · `abstractions_summary.csv` "
            "· `themes.md` · `synthesis_report.md`"
        )
