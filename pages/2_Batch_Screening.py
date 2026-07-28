import streamlit as st
import tempfile
import os

from parser.jd_parser import extract_jd_info
from parser.jd_input import get_jd_text
from matcher.batch_screener import screen_multiple_resumes
from utils.edge_case_handler import validate_jd_text, validate_jd_info

st.set_page_config(page_title="Batch Screening", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0f1e; color: #e8eaf0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1200px; }
section[data-testid="stSidebar"] { background: #0d1321; border-right: 1px solid #1e2d40; }
.page-title { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem; }
.page-sub { font-size: 0.9rem; color: #6b7a92; margin-bottom: 2rem; }
.rank-card { background: #111827; border: 1px solid #1e2d40; border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 1.5rem; }
.rank-num { font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: #1e2d40; min-width: 2.5rem; text-align: center; }
.rank-num-top { color: #00d4b4; }
.rank-name { font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 600; color: #fff; }
.rank-file { font-size: 0.75rem; color: #6b7a92; margin-top: 0.1rem; }
.rank-score { font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; text-align: right; }
.rank-label { font-size: 0.75rem; font-weight: 500; text-align: right; }
.score-strong { color: #00d4b4; }
.score-partial { color: #f59e0b; }
.score-weak { color: #ef4444; }
.pill { border-radius: 100px; padding: 0.25rem 0.75rem; font-size: 0.75rem; font-weight: 500; }
.pill-match { background: #0d2b22; border: 1px solid #00d4b4; color: #00d4b4; }
.pill-miss { background: #2b1212; border: 1px solid #ef4444; color: #ef4444; }
.pill-grid { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
.sidebar-logo { font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: #00d4b4; padding: 0.5rem 0 1.5rem; }
.sidebar-section { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #3d5166; margin: 1.2rem 0 0.6rem; }
.sidebar-tip { background: #111827; border: 1px solid #1e2d40; border-radius: 10px; padding: 0.8rem 1rem; font-size: 0.78rem; color: #6b7a92; line-height: 1.5; margin-bottom: 0.5rem; }
.sidebar-tip strong { color: #e8eaf0; display: block; margin-bottom: 0.2rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-logo">📄 ResumeAI</div>', unsafe_allow_html=True)
    st.markdown("**📊 Batch Screening**")
    st.caption("Screen multiple candidates against one job description and rank them by AI match score.")
    st.divider()

    st.markdown('<div class="sidebar-section">How to use</div>', unsafe_allow_html=True)
    st.markdown("1. Paste or upload the **Job Description**")
    st.markdown("2. Upload **multiple resume PDFs**")
    st.markdown("3. Click **Run Batch Screening**")
    st.markdown("4. Review the ranked candidate table")

    st.divider()
    st.markdown('<div class="sidebar-section">Score guide</div>', unsafe_allow_html=True)
    st.markdown("🟢 **70%+** — Strong Match")
    st.markdown("🟡 **45–69%** — Partial Match")
    st.markdown("🔴 **Below 45%** — Weak Match")

    st.divider()
    st.markdown('<div class="sidebar-section">Tips</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>Multi-select files</strong>Hold Ctrl (Windows) or Cmd (Mac) to select multiple resume PDFs at once.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>Best results</strong>Works most accurately with structured JDs that list explicit skill requirements.</div>', unsafe_allow_html=True)

st.markdown('<div class="page-title">📊 Batch Screening</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Upload multiple resumes and rank all candidates against one job description instantly.</div>', unsafe_allow_html=True)

st.subheader("Job Description")
jd_input_mode = st.radio("JD format", ["Paste Text", "Upload PDF", "Upload Image"], horizontal=True, label_visibility="collapsed")
jd_text = None

if jd_input_mode == "Paste Text":
    pasted = st.text_area("Paste JD", height=160, label_visibility="collapsed", placeholder="Paste the job description here...")
    if pasted: jd_text = get_jd_text("text", pasted)
elif jd_input_mode == "Upload PDF":
    jd_pdf = st.file_uploader("JD PDF", type=["pdf"], key="jd_pdf", label_visibility="collapsed")
    if jd_pdf:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(jd_pdf.read()); tmp_path = tmp.name
        jd_text = get_jd_text("pdf", tmp_path); os.remove(tmp_path)
elif jd_input_mode == "Upload Image":
    jd_img = st.file_uploader("JD Image", type=["png","jpg","jpeg"], key="jd_img", label_visibility="collapsed")
    if jd_img:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(jd_img.read()); tmp_path = tmp.name
        with st.spinner("Running OCR..."): jd_text = get_jd_text("image", tmp_path)
        os.remove(tmp_path)

st.divider()
st.subheader("Resumes")
uploaded_files = st.file_uploader("Upload multiple PDFs", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")

if uploaded_files and jd_text:
    # --- Edge case: empty / whitespace-only JD ---
    jd_error = validate_jd_text(jd_text)
    if jd_error:
        st.error(jd_error)
        st.stop()

    jd_info = extract_jd_info(jd_text)

    # --- Edge case: JD with no detectable skills (non-blocking warning) ---
    jd_warning = validate_jd_info(jd_info)
    if jd_warning:
        st.warning(jd_warning)

    st.write(f"**{len(uploaded_files)} resume(s)** ready — **{len(jd_info['required_skills'])} required skills** detected in JD.")

    if st.button("🚀 Run Batch Screening", type="primary"):
        tmp_paths = []
        for f in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(f.read()); tmp_paths.append(tmp.name)

        with st.spinner(f"Screening {len(uploaded_files)} resumes..."):
            results = screen_multiple_resumes(tmp_paths, jd_info, jd_text)
        for path in tmp_paths: os.remove(path)

        st.markdown("---")
        st.markdown(f"### 🏆 Ranked Results — {len(results)} Candidates")

        for i, r in enumerate(results):
            rank = i + 1
            score = r["overall_score"]
            score_class = "score-strong" if score >= 70 else "score-partial" if score >= 45 else "score-weak"
            label = "Strong Match" if score >= 70 else "Partial Match" if score >= 45 else "Weak Match"
            num_class = "rank-num-top" if rank <= 3 else ""

            st.markdown(f"""
            <div class="rank-card">
                <div class="rank-num {num_class}">#{rank}</div>
                <div style="flex:1">
                    <div class="rank-name">{r['name']}</div>
                    <div class="rank-file">{r['filename']}</div>
                </div>
                <div>
                    <div class="rank-score {score_class}">{score}%</div>
                    <div class="rank-label {score_class}">{label}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"View details — {r['name']}"):
                if r["error"]:
                    # --- Edge case: corrupted / scanned / unreadable PDF ---
                    # r["error"] is now a friendly message from safe_parse_resume(),
                    # not a raw exception string.
                    st.error(f"⚠️ {r['error']}")
                else:
                    if r.get("warning"):
                        # --- Edge case: very short resume, parseable but thin ---
                        st.warning(r["warning"])

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Skill Overlap:** {r['skill_overlap_score']}%")
                        st.write(f"**Semantic:** {r['semantic_similarity_score']}%")
                        st.write(f"**Experience:** {r['experience_match']}")
                    with col2:
                        st.markdown("**Matched Skills:**")
                        pills = "".join([f'<span class="pill pill-match">{s}</span>' for s in r["matched_skills"]]) or "None"
                        st.markdown(f'<div class="pill-grid">{pills}</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown("**Missing Skills:**")
                        pills = "".join([f'<span class="pill pill-miss">{s}</span>' for s in r["missing_skills"]]) or "None"
                        st.markdown(f'<div class="pill-grid">{pills}</div>', unsafe_allow_html=True)

elif not jd_text:
    st.markdown('<div style="text-align:center;padding:3rem;color:#3d5166;font-size:0.9rem">Provide a job description above first.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center;padding:2rem;color:#3d5166;font-size:0.9rem">Upload resumes to begin batch screening.</div>', unsafe_allow_html=True)