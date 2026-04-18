import streamlit as st
from core.extractor import synthesize_papers

SECTIONS = [
    ("common_findings",      "Common Findings",          "dot-teal"),
    ("conflicting_results",  "Conflicting Results",       "dot-red"),
    ("methodology_patterns", "Methodology Patterns",      "dot-teal"),
    ("research_gaps",        "Research Gaps Identified",  "dot-amber"),
    ("common_weaknesses",    "Common Weaknesses",         "dot-red"),
    ("future_directions",    "Future Research Directions","dot-green"),
]

def render():
    papers    = st.session_state.get("extracted_papers", [])
    synthesis = st.session_state.get("synthesis_result")

    st.markdown("""
    <div class="ph-wrap anim-up">
      <div class="ph-eye">Step 02 · Synthesize</div>
      <h1 class="ph-title">Cross-Paper <em>Intelligence</em></h1>
      <p class="ph-sub">Patterns, conflicts, and research gaps synthesized across your
      entire paper set — turning weeks of manual review into minutes of strategic insight.</p>
    </div>""", unsafe_allow_html=True)

    if not papers:
        st.markdown("""
        <div class="empty-st">
          <div class="empty-st-icon">🔗</div>
          <div class="empty-st-title">No papers loaded</div>
          <div class="empty-st-desc">Upload and extract at least 2 papers to run synthesis.</div>
        </div>""", unsafe_allow_html=True)
        return

    if len(papers) < 2:
        st.warning("Add at least 2 papers for meaningful cross-paper synthesis.")
        return

    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown(
            f'<p style="color:var(--ink-2);font-size:var(--tx-sm);margin:0;font-weight:500">'
            f'<span style="color:var(--teal);font-family:var(--f-display);'
            f'font-size:var(--tx-lg)">{len(papers)}</span>'
            f'&nbsp;&nbsp;papers ready for synthesis</p>', unsafe_allow_html=True)
    with c2:
        run = st.button("Run →" if not synthesis else "Re-run →",
                        type="primary", use_container_width=True)

    if run:
        with st.spinner("Synthesizing across papers…"):
            try:
                synthesis = synthesize_papers(papers)
                st.session_state["synthesis_result"] = synthesis
            except Exception as e:
                st.error(f"Synthesis failed: {e}"); return

    if not synthesis:
        st.markdown("---")
        st.markdown('<p style="color:var(--ink-3);font-size:var(--tx-sm)">'
                    'Click <strong style="color:var(--teal)">Run →</strong> to generate intelligence.</p>',
                    unsafe_allow_html=True)
        return

    _render(synthesis)


def _render(s):
    st.markdown("---")
    if s.get("overall_summary"):
        st.markdown(f"""
        <div class="x-card x-card-teal anim-up" style="margin-bottom:var(--gap-md)">
          <div class="detail-lbl">Overview</div>
          <div style="font-size:var(--tx-md);color:var(--ink-2);line-height:1.75;
                      font-weight:400;margin-top:4px">
            {s['overall_summary']}
          </div>
        </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    left  = ["common_findings","methodology_patterns","common_weaknesses"]
    right = ["conflicting_results","research_gaps","future_directions"]
    sm    = {k:(t,d) for k,t,d in SECTIONS}

    with c1:
        for k in left:
            _block(sm[k][0], s.get(k,[]), sm[k][1])
    with c2:
        for k in right:
            _block(sm[k][0], s.get(k,[]), sm[k][1])

    unexplored = s.get("underexplored_variables", [])
    if unexplored:
        tags = "".join(f'<span class="var-tag">{v}</span>' for v in unexplored)
        st.markdown(f"""
        <div class="syn-section" style="margin-top:0.25rem">
          <div class="syn-head">🔮&nbsp;&nbsp;Underexplored Variables</div>
          <div style="margin-top:4px">{tags}</div>
        </div>""", unsafe_allow_html=True)

    dom = s.get("dominant_methodology","")
    if dom:
        st.markdown(f"""
        <div class="x-card" style="display:flex;align-items:center;gap:18px;margin-top:0.5rem">
          <div style="font-size:2rem;flex-shrink:0">⚙️</div>
          <div>
            <div class="detail-lbl">Dominant Methodology</div>
            <div style="font-family:var(--f-display);font-size:var(--tx-lg);
                        color:var(--teal);margin-top:4px;font-variation-settings:'opsz' 36;
                        font-weight:600;letter-spacing:-0.02em">{dom}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📥  Export Synthesis Report →", type="primary"):
        st.session_state["page"] = "export"; st.rerun()


def _block(title, items, dot_cls):
    if not items: return
    rows = "".join(
        f'<div class="syn-item"><div class="syn-dot {dot_cls}"></div><div>{i}</div></div>'
        for i in items)
    st.markdown(f"""
    <div class="syn-section">
      <div class="syn-head">{title}</div>
      {rows}
    </div>""", unsafe_allow_html=True)
