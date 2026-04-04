import streamlit as st
from openai import OpenAI
import json, time, zipfile, io, csv
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SLR Analyser", page_icon="🔬", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION  (must happen before anything else)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "api_key":       "",
    "files":         {},          # {name: bytes}
    "abstractions":  None,        # list[dict] | None
    "themes":        None,        # str | None
    "synthesis":     None,        # str | None
    "stage":         "upload",    # upload | abstract | themes | results
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*, html, body { font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0f172a,#1e293b);
    border-right:1px solid #334155;
}
[data-testid="stSidebar"] * { color:#e2e8f0 !important; }

.header-box {
    background:linear-gradient(135deg,#1e3a5f,#1e40af,#1d4ed8);
    border-radius:16px; padding:2rem 2.5rem; margin-bottom:1.5rem;
    box-shadow:0 4px 24px rgba(30,64,175,.25);
}
.header-box h1 { color:#f0f9ff; font-size:2rem; font-weight:700; margin:0; }
.header-box p  { color:#bae6fd; margin:.4rem 0 0; font-size:1rem; }

.stage-bar { display:flex; gap:6px; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; }
.stage-pill {
    padding:5px 14px; border-radius:20px; font-size:.8rem; font-weight:600;
}
.stage-pill.done    { background:#dcfce7; color:#166534; }
.stage-pill.active  { background:#dbeafe; color:#1e40af; }
.stage-pill.pending { background:#f1f5f9; color:#94a3b8; }

.file-chip {
    display:inline-flex; align-items:center; gap:6px;
    background:#f8fafc; border:1px solid #e2e8f0;
    border-radius:8px; padding:6px 12px;
    font-size:.82rem; font-weight:500; color:#334155;
    margin:4px;
}
.file-chip .sz { color:#94a3b8; font-size:.75rem; }

.info-box {
    background:#eff6ff; border:1.5px solid #93c5fd;
    border-radius:10px; padding:.85rem 1.1rem;
    color:#1e40af; font-size:.9rem; margin-bottom:1rem;
}
.success-box {
    background:#f0fdf4; border:1.5px solid #86efac;
    border-radius:10px; padding:.85rem 1.1rem;
    color:#166534; font-size:.9rem; margin-bottom:1rem;
}
.meta-badge {
    display:inline-block; background:#dbeafe; color:#1e40af;
    border-radius:6px; padding:2px 10px; font-size:.78rem;
    font-weight:600; margin:3px 4px 3px 0;
}
.meta-badge.g { background:#dcfce7; color:#166534; }
.meta-badge.p { background:#f3e8ff; color:#6b21a8; }
.meta-badge.a { background:#fef3c7; color:#92400e; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 SLR Analyser")
    st.markdown("---")
    st.markdown("**OpenAI API Key**")
    key_in = st.text_input("", type="password",
                           value=st.session_state.api_key,
                           placeholder="sk-...", label_visibility="collapsed")
    if key_in:
        st.session_state.api_key = key_in
    if st.session_state.api_key:
        st.success("✅ API key set")
    else:
        st.warning("⚠️ Enter your API key above")

    st.markdown("---")
    st.markdown("""**Supported formats**
`.pdf` · `.docx` · `.txt` · `.zip`

**Pipeline**
1. Upload papers
2. Data abstraction (GPT)
3. Theme identification (GPT)
4. Synthesis & export
""")
    st.markdown("---")
    if st.button("🔄 Reset / Start Over", use_container_width=True):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v if not isinstance(v, dict) else {}
        st.rerun()

    # Show file count if loaded
    if st.session_state.files:
        st.markdown(f"**📁 {len(st.session_state.files)} file(s) loaded**")
        for nm in st.session_state.files:
            sz = len(st.session_state.files[nm]) / 1024
            st.markdown(f"<div class='file-chip'>📄 {nm} <span class='sz'>{sz:.0f} KB</span></div>",
                        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER + STAGE BAR
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
  <h1>🔬 Systematic Literature Review Analyser</h1>
  <p>Upload papers → Extract data → Identify themes → Generate synthesis</p>
</div>""", unsafe_allow_html=True)

STAGES = [("upload","📤 Upload"), ("abstract","🔍 Abstract"),
          ("themes","🧵 Themes"), ("results","✅ Results")]
cur = st.session_state.stage
order = [s for s,_ in STAGES]
cur_idx = order.index(cur)

bar = '<div class="stage-bar">'
for i,(sid,label) in enumerate(STAGES):
    cls = "done" if i < cur_idx else ("active" if i == cur_idx else "pending")
    bar += f'<span class="stage-pill {cls}">{label}</span>'
    if i < len(STAGES)-1:
        bar += '<span style="color:#cbd5e1;font-size:.9rem">›</span>'
bar += '</div>'
st.markdown(bar, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
SUPPORTED = {".pdf", ".docx", ".doc", ".txt"}

def read_uploaded(uploaded_list):
    """Expand ZIPs and return {name: bytes} from a list of UploadedFile."""
    out = {}
    for f in uploaded_list:
        raw = f.getvalue()          # read bytes NOW before any rerun
        if f.name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for mem in zf.namelist():
                        if mem.endswith("/") or "__MACOSX" in mem:
                            continue
                        if Path(mem).suffix.lower() not in SUPPORTED:
                            continue
                        nm = Path(mem).name
                        if nm not in out:
                            out[nm] = zf.read(mem)
            except Exception as e:
                st.warning(f"Could not read ZIP `{f.name}`: {e}")
        else:
            out[f.name] = raw
    return out

def extract_text(name: str, data: bytes) -> str:
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        try:
            import pypdf
            r = pypdf.PdfReader(io.BytesIO(data))
            txt = "\n\n".join(p.extract_text() or "" for p in r.pages).strip()
            return txt or "[PDF has no extractable text — may be scanned]"
        except Exception as e:
            return f"[PDF error: {e}]"
    elif ext in (".docx", ".doc"):
        try:
            import docx
            d = docx.Document(io.BytesIO(data))
            return "\n\n".join(p.text for p in d.paragraphs if p.text.strip())
        except Exception as e:
            return f"[DOCX error: {e}]"
    else:
        return data.decode("utf-8", errors="replace")

def gpt(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    client = OpenAI(api_key=st.session_state.api_key)
    msgs = []
    if system:
        msgs.append({"role":"system","content":system})
    msgs.append({"role":"user","content":prompt})
    r = client.chat.completions.create(
        model="gpt-4o-mini", max_tokens=max_tokens,
        temperature=0.2, messages=msgs)
    return r.choices[0].message.content.strip()

def abstract_one(name: str, text: str) -> dict:
    sys = ("You are an expert SLR assistant. Extract structured metadata. "
           "Reply with ONLY raw JSON — no fences, no commentary.")
    prompt = f"""Extract from this paper. Use null for unknown fields.
Return a JSON object with keys:
title, authors (list), year, journal_or_venue,
methodology_design, sample_size, main_findings (2-4 sentences),
contributions (1-3 key points as one string),
limitations, keywords (list, max 8)

FILENAME: {name}
TEXT (first 6000 chars):
{text[:6000]}"""
    raw = gpt(prompt, sys, 1200).strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1][4:] if parts[1].startswith("json") else parts[1]
    raw = raw.strip()
    try:
        d = json.loads(raw)
    except Exception:
        d = {"title":name,"authors":[],"year":None,"journal_or_venue":None,
             "methodology_design":"Unknown","sample_size":None,
             "main_findings":raw[:400],"contributions":"","limitations":None,"keywords":[]}
    if not d.get("title") or str(d.get("title")).lower()=="null":
        d["title"] = name
    return d

def run_themes(abstractions: list) -> str:
    sys = "You are an expert systematic review analyst."
    sums = []
    for i,p in enumerate(abstractions,1):
        sums.append(f"Paper {i}: {p.get('title')}\n"
                    f"  Year:{p.get('year')} Method:{p.get('methodology_design')}\n"
                    f"  Findings:{p.get('main_findings')}\n"
                    f"  Keywords:{', '.join(p.get('keywords') or [])}")
    prompt = f"""Thematic synthesis across {len(abstractions)} papers:

{chr(10).join(sums)}

1. Identify 4-7 major cross-cutting themes (cite papers by number).
2. For each: clear title, 3-5 sentence explanation, note contradictions/gaps.
3. Concluding paragraph on research trajectory and future directions.

Format with ## headings per theme. Use clean markdown."""
    return gpt(prompt, sys, 3000)

def run_synthesis(abstractions: list, themes_txt: str) -> str:
    sys = "You are an expert academic writer in systematic literature reviews."
    years = sorted({str(p.get("year","?")) for p in abstractions if p.get("year")})
    prompt = f"""Write a comprehensive synthesis / discussion section (600-900 words).

Corpus: {len(abstractions)} papers, years: {', '.join(years) or 'N/A'}

THEMATIC ANALYSIS:
{themes_txt}

Include:
- Opening paragraph contextualising the literature
- Paragraph per major theme, weaving evidence from multiple papers
- Methodological diversity and limitations across studies
- Concluding paragraph on implications and research gaps

Formal academic prose. No first person. Markdown formatting."""
    return gpt(prompt, sys, 3000)

def build_zip(abstractions, themes, synthesis) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,"w") as zf:
        zf.writestr("abstractions.json", json.dumps(abstractions, indent=2))
        zf.writestr("themes.md", themes or "")
        zf.writestr("synthesis.md", synthesis or "")
        csv_buf = io.StringIO()
        fields = ["title","authors","year","journal_or_venue","methodology_design",
                  "sample_size","main_findings","contributions","limitations","keywords"]
        w = csv.DictWriter(csv_buf, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for p in abstractions:
            w.writerow({k:(", ".join(v) if isinstance(v,list) else (v or ""))
                        for k,v in p.items()})
        zf.writestr("summary_table.csv", csv_buf.getvalue())
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# STAGE: UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.stage == "upload":
    st.markdown("### 📤 Step 1 — Upload Your Papers")
    st.caption("Accepts PDF, DOCX, TXT — or a ZIP bundle. Multiple files OK.")

    uploaded = st.file_uploader(
        "Upload files",
        type=["pdf","docx","txt","zip"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # ── KEY FIX: read bytes immediately into session state every time files change
    if uploaded:
        fresh = read_uploaded(uploaded)
        if fresh:
            st.session_state.files = fresh   # persist immediately

    # ── Show what's loaded (from session state, not the uploader widget)
    if st.session_state.files:
        files = st.session_state.files
        st.markdown(
            f'<div class="success-box">✅ <b>{len(files)} file(s) loaded and ready</b></div>',
            unsafe_allow_html=True)

        # File chips
        chips = ""
        for nm, data in files.items():
            sz = len(data)/1024
            ext = Path(nm).suffix.upper().lstrip(".")
            chips += f'<span class="file-chip">📄 {nm} <span class="sz">{sz:.0f} KB · {ext}</span></span>'
        st.markdown(chips, unsafe_allow_html=True)
        st.markdown("")

        if not st.session_state.api_key:
            st.warning("⚠️ Please enter your OpenAI API key in the sidebar to continue.")
        else:
            st.markdown(
                '<div class="info-box">👇 Ready! Click <b>Start Analysis</b> to extract structured data from each paper.</div>',
                unsafe_allow_html=True)
            if st.button("🚀 Start Analysis — Analyse Documents", type="primary"):
                st.session_state.stage = "abstract"
                st.rerun()
    else:
        st.markdown("""
        <div style="border:2px dashed #cbd5e1;border-radius:14px;padding:3rem;
                    text-align:center;color:#94a3b8;margin-top:1rem">
            <div style="font-size:3rem">📂</div>
            <div style="font-size:1.05rem;font-weight:600;margin-top:.5rem">
                Drop your papers here or click Browse</div>
            <div style="font-size:.85rem;margin-top:.3rem">
                PDF · DOCX · TXT · ZIP (batch) · Multiple files at once</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# STAGE: ABSTRACT
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "abstract":
    st.markdown("### 🔍 Step 2 — Data Abstraction")

    files = st.session_state.files
    if not files:
        st.error("No files found. Please go back and upload papers.")
        if st.button("← Back to Upload"):
            st.session_state.stage = "upload"
            st.rerun()
        st.stop()

    # If abstraction already done, show results + next button
    if st.session_state.abstractions is not None:
        abs_list = st.session_state.abstractions
        st.markdown(
            f'<div class="success-box">✅ <b>Data abstraction complete — {len(abs_list)} paper(s) processed.</b></div>',
            unsafe_allow_html=True)

        # Summary preview table
        import pandas as pd
        rows = [{"#":i+1,
                 "Title": p.get("title","")[:60],
                 "Year":  p.get("year") or "?",
                 "Method":p.get("methodology_design") or "?",
                 "Author":(p.get("authors") or ["?"])[0]}
                for i,p in enumerate(abs_list)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        # Expandable detail per paper
        with st.expander("🔎 View full abstractions"):
            for p in abs_list:
                st.markdown(f"**📄 {p.get('title','Untitled')}**")
                c1, c2 = st.columns([3,1])
                with c1:
                    if p.get("authors"):
                        st.markdown(f"Authors: {', '.join(p['authors'][:4])}")
                    st.markdown(f"Venue: {p.get('journal_or_venue') or '_N/A_'}")
                    st.markdown(f"**Findings:** {p.get('main_findings') or '_N/A_'}")
                    st.markdown(f"**Contributions:** {p.get('contributions') or '_N/A_'}")
                    if p.get("limitations"):
                        st.markdown(f"**Limitations:** {p['limitations']}")
                with c2:
                    b = ""
                    if p.get("year"):
                        b += f'<span class="meta-badge a">{p["year"]}</span>'
                    if p.get("methodology_design"):
                        b += f'<span class="meta-badge p">{p["methodology_design"]}</span>'
                    if p.get("sample_size"):
                        b += f'<span class="meta-badge g">n={p["sample_size"]}</span>'
                    if b:
                        st.markdown(b, unsafe_allow_html=True)
                    kws = p.get("keywords") or []
                    if kws:
                        st.markdown(" ".join(f'<span class="meta-badge">{k}</span>' for k in kws),
                                    unsafe_allow_html=True)
                st.markdown("---")

        st.markdown(
            '<div class="info-box">👇 Click <b>Find Key Themes</b> to identify cross-cutting themes across all papers.</div>',
            unsafe_allow_html=True)
        col1, col2 = st.columns([2,5])
        with col1:
            if st.button("🧵 Find Key Themes", type="primary", use_container_width=True):
                st.session_state.stage = "themes"
                st.rerun()
        with col2:
            if st.button("← Re-upload / Change Files", use_container_width=False):
                st.session_state.stage = "upload"
                st.session_state.abstractions = None
                st.rerun()

    else:
        # Run abstraction now
        st.markdown(
            '<div class="info-box">⏳ Extracting structured metadata from each paper using GPT-4o-mini — please wait…</div>',
            unsafe_allow_html=True)
        prog = st.progress(0, text="Starting…")
        results = []
        names = list(files.keys())
        for i, nm in enumerate(names):
            prog.progress((i)/len(names), text=f"Processing {i+1}/{len(names)}: {nm}")
            txt = extract_text(nm, files[nm])
            if txt.startswith("["):
                st.warning(f"⚠️ `{nm}`: {txt}")
            try:
                d = abstract_one(nm, txt)
            except Exception as e:
                st.warning(f"⚠️ Abstraction failed for `{nm}`: {e}")
                d = {"title":nm,"authors":[],"year":None,"journal_or_venue":None,
                     "methodology_design":"Error","sample_size":None,
                     "main_findings":f"Error: {e}","contributions":"",
                     "limitations":None,"keywords":[]}
            results.append(d)
        prog.progress(1.0, text=f"✅ Done — {len(results)} paper(s) abstracted")
        st.session_state.abstractions = results
        time.sleep(0.5)
        st.rerun()   # rerun to show results view above

# ─────────────────────────────────────────────────────────────────────────────
# STAGE: THEMES
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "themes":
    st.markdown("### 🧵 Step 3 — Key Themes & Discussion")

    abstractions = st.session_state.abstractions
    if not abstractions:
        st.error("No abstraction data. Please complete Step 2 first.")
        if st.button("← Back"):
            st.session_state.stage = "abstract"
            st.rerun()
        st.stop()

    # If both already done, show them + next button
    if st.session_state.themes is not None and st.session_state.synthesis is not None:
        st.markdown(
            '<div class="success-box">✅ <b>Theme identification and synthesis complete.</b></div>',
            unsafe_allow_html=True)

        t1, t2 = st.tabs(["🧵 Key Themes", "✍️ Discussion / Synthesis"])
        with t1:
            st.markdown(st.session_state.themes)
        with t2:
            st.markdown(st.session_state.synthesis)

        st.markdown(
            '<div class="info-box">👇 Click <b>View Full Results</b> to see all abstractions, the summary table, and download your export.</div>',
            unsafe_allow_html=True)
        col1, col2 = st.columns([2,5])
        with col1:
            if st.button("📊 View Full Results & Export", type="primary", use_container_width=True):
                st.session_state.stage = "results"
                st.rerun()
        with col2:
            if st.button("← Back to Abstraction"):
                st.session_state.stage = "abstract"
                st.rerun()

    else:
        # Run themes + synthesis
        st.markdown(
            '<div class="info-box">⏳ Identifying themes and writing discussion — please wait…</div>',
            unsafe_allow_html=True)

        with st.spinner("🧵 Finding cross-cutting themes across all papers…"):
            try:
                themes = run_themes(abstractions)
                st.session_state.themes = themes
            except Exception as e:
                st.error(f"Theme identification failed: {e}")
                st.stop()

        with st.spinner("✍️ Writing academic synthesis / discussion section…"):
            try:
                synthesis = run_synthesis(abstractions, st.session_state.themes)
                st.session_state.synthesis = synthesis
            except Exception as e:
                st.error(f"Synthesis writing failed: {e}")
                st.stop()

        st.rerun()   # rerun to show results view above

# ─────────────────────────────────────────────────────────────────────────────
# STAGE: RESULTS
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "results":
    abstractions = st.session_state.abstractions
    themes       = st.session_state.themes
    synthesis    = st.session_state.synthesis

    # ── Metrics
    years   = [p.get("year") for p in abstractions if p.get("year")]
    methods = [p.get("methodology_design","") for p in abstractions]
    kws     = [k for p in abstractions for k in (p.get("keywords") or [])]

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("📄 Papers",          len(abstractions))
    m2.metric("📅 Year Range",      f"{min(years)}–{max(years)}" if years else "N/A")
    m3.metric("🧪 Study Designs",   len({m for m in methods if m not in ("","Unknown","Error")}))
    m4.metric("🔑 Unique Keywords", len(set(kws)))

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📑 All Abstractions",
        "🧵 Key Themes",
        "✍️ Discussion",
        "📊 Summary Table",
    ])

    with tab1:
        st.markdown(f"#### {len(abstractions)} Paper Abstractions")
        for p in abstractions:
            with st.expander(f"📄 {p.get('title','Untitled')}"):
                c1,c2 = st.columns([3,1])
                with c1:
                    if p.get("authors"):
                        st.markdown(f"**Authors:** {', '.join(p['authors'][:5])}")
                    st.markdown(f"**Journal/Venue:** {p.get('journal_or_venue') or '_Not identified_'}")
                    st.markdown(f"**Main Findings:** {p.get('main_findings') or '_N/A_'}")
                    st.markdown(f"**Contributions:** {p.get('contributions') or '_N/A_'}")
                    if p.get("limitations"):
                        st.markdown(f"**Limitations:** {p['limitations']}")
                with c2:
                    b = ""
                    if p.get("year"):       b += f'<span class="meta-badge a">{p["year"]}</span>'
                    if p.get("methodology_design"): b += f'<span class="meta-badge p">{p["methodology_design"]}</span>'
                    if p.get("sample_size"): b += f'<span class="meta-badge g">n={p["sample_size"]}</span>'
                    if b: st.markdown(b, unsafe_allow_html=True)
                    kw_list = p.get("keywords") or []
                    if kw_list:
                        st.markdown(" ".join(f'<span class="meta-badge">{k}</span>' for k in kw_list),
                                    unsafe_allow_html=True)

    with tab2:
        st.markdown(themes or "_No themes generated._")

    with tab3:
        st.markdown(synthesis or "_No synthesis generated._")

    with tab4:
        st.markdown("#### Corpus Summary — All Papers")
        import pandas as pd
        rows = []
        for p in abstractions:
            t = p.get("title","")
            rows.append({
                "Title":       t[:60]+("…" if len(t)>60 else ""),
                "Year":        p.get("year") or "?",
                "Method":      p.get("methodology_design") or "?",
                "First Author":(p.get("authors") or ["?"])[0],
                "Venue":       (p.get("journal_or_venue") or "?")[:40],
                "Keywords":    ", ".join((p.get("keywords") or [])[:4]),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Export
    st.markdown("---")
    st.markdown("### 📦 Download Results")
    col1, col2 = st.columns([1,3])
    with col1:
        st.download_button(
            "⬇️ Download Full Package (.zip)",
            data=build_zip(abstractions, themes, synthesis),
            file_name="slr_results.zip",
            mime="application/zip",
            use_container_width=True,
        )
    with col2:
        st.caption("Contains: `abstractions.json` · `summary_table.csv` · `themes.md` · `synthesis.md`")

    st.markdown("")
    if st.button("← Back to Themes"):
        st.session_state.stage = "themes"
        st.rerun()
