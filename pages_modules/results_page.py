import streamlit as st
import pandas as pd
from collections import Counter

DISPLAY_COLS = [
    ("author_year","Author & Year"),("research_context","Research Context"),
    ("methodology","Methodology"),("independent_variables","IVs"),
    ("dependent_variable","DV"),("findings","Key Findings"),
    ("strengths","Strengths"),("limitations","Limitations"),
]

def render():
    papers = st.session_state.get("extracted_papers", [])

    st.markdown("""
    <div class="ph-wrap anim-up">
      <div class="ph-eye">Step 01 · Analyse</div>
      <h1 class="ph-title">Extraction <em>Results</em></h1>
      <p class="ph-sub">Structured empirical data extracted from each paper.
      Browse the full table or drill into any paper for complete detail.</p>
    </div>""", unsafe_allow_html=True)

    if not papers:
        st.markdown("""
        <div class="empty-st">
          <div class="empty-st-icon">📭</div>
          <div class="empty-st-title">No papers extracted yet</div>
          <div class="empty-st-desc">Upload papers using the sidebar, then click
          <strong>⚡ Extract</strong> to begin analysis.</div>
        </div>""", unsafe_allow_html=True)
        return

    # Metrics
    methods = [p.get("methodology","") for p in papers if p.get("methodology")]
    cnt     = Counter(methods)
    top_m   = cnt.most_common(1)[0][0][:24] if cnt else "—"

    st.markdown(f"""
    <div class="m-row anim-up anim-up-d1">
      <div class="m-chip">
        <div class="m-val">{len(papers)}</div>
        <div class="m-lbl">Papers</div>
      </div>
      <div class="m-chip">
        <div class="m-val">{len(set(methods))}</div>
        <div class="m-lbl">Methods</div>
      </div>
      <div class="m-chip">
        <div class="m-val" style="font-size:clamp(1rem,3vw,1.3rem);padding-top:5px">{top_m}</div>
        <div class="m-lbl">Top Method</div>
      </div>
    </div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["TABLE VIEW", "PAPER DETAIL"])
    with tab1:
        _table(papers)
    with tab2:
        _detail(papers)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔗  Run Cross-Paper Synthesis →", type="primary", use_container_width=True):
            st.session_state["page"] = "synthesis"; st.rerun()
    with c2:
        if st.button("📥  Export Data →", use_container_width=True):
            st.session_state["page"] = "export"; st.rerun()


def _table(papers):
    rows = [{lbl: p.get(key,"—") for key,lbl in DISPLAY_COLS} for p in papers]
    df   = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True,
        height=min(640, 90+65*len(papers)),
        column_config={
            "Author & Year":    st.column_config.TextColumn(width="small"),
            "Research Context": st.column_config.TextColumn(width="medium"),
            "Methodology":      st.column_config.TextColumn(width="small"),
            "IVs":              st.column_config.TextColumn(width="medium"),
            "DV":               st.column_config.TextColumn(width="small"),
            "Key Findings":     st.column_config.TextColumn(width="large"),
            "Strengths":        st.column_config.TextColumn(width="medium"),
            "Limitations":      st.column_config.TextColumn(width="medium"),
        }, hide_index=True)


def _detail(papers):
    opts = [f"{i+1}. {p.get('author_year','?')} — {p.get('_source_file','')}" for i,p in enumerate(papers)]
    idx  = st.selectbox("Select paper", range(len(opts)), format_func=lambda i: opts[i],
                        label_visibility="collapsed")
    p = papers[idx]

    st.markdown(f"""
    <div class="x-card x-card-teal" style="margin-bottom:1.4rem">
      <div class="ph-eye" style="margin-bottom:8px">{p.get("author_year","")}</div>
      <div style="font-family:var(--f-display);font-size:clamp(1.1rem,3.5vw,1.5rem);
                  font-weight:700;color:var(--ink);line-height:1.2;
                  letter-spacing:-0.02em;font-variation-settings:'opsz' 40;margin-bottom:6px">
        {p.get("title","Untitled")}
      </div>
      <div style="font-family:var(--f-mono);font-size:var(--tx-2xs);color:var(--ink-3)">
        {p.get("_source_file","")}
      </div>
    </div>""", unsafe_allow_html=True)

    labels = {
        "research_context":"📍 Research Context","methodology":"⚙️ Methodology",
        "independent_variables":"📌 Independent Variables","dependent_variable":"🎯 Dependent Variable",
        "control_variables":"🔧 Control Variables","findings":"📊 Key Findings",
        "theoretical_contributions":"💡 Theoretical Contributions",
        "practical_contributions":"🏭 Practical Implications",
        "strengths":"✅ Strengths","limitations":"⚠️ Limitations",
    }
    c1, c2 = st.columns(2)
    with c1:
        for k in ["research_context","methodology","independent_variables","dependent_variable","control_variables"]:
            _db(labels[k], p.get(k,"—"))
    with c2:
        for k in ["findings","theoretical_contributions","practical_contributions","strengths","limitations"]:
            _db(labels[k], p.get(k,"—"))

    with st.expander("📚  Citations (APA · MLA · Harvard)"):
        for fmt, key in [("APA 7th","citation_apa"),("MLA 9th","citation_mla"),("Harvard","citation_harvard")]:
            st.markdown(f"**{fmt}**")
            st.code(p.get(key,"Not available"), language=None)


def _db(label, content):
    st.markdown(f"""
    <div class="detail-block">
      <div class="detail-lbl">{label}</div>
      <div class="detail-val">{content}</div>
    </div>""", unsafe_allow_html=True)
