import streamlit as st
import tempfile
import os

from utils.edge_case_handler import (
    safe_parse_resume,
    validate_jd_text,
    validate_jd_info,
)

from parser.skill_extractor import extract_resume_info
from parser.jd_parser import extract_jd_info
from parser.jd_input import get_jd_text
from matcher.matcher import compute_match_score, generate_suggestions

st.set_page_config(page_title="Resume Screening", page_icon="🔍", layout="wide")

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
.score-wrapper { background: #111827; border: 1px solid #1e2d40; border-radius: 20px; padding: 2.5rem; text-align: center; margin: 2rem 0 1.5rem; }
.score-number { font-family: 'Space Grotesk', sans-serif; font-size: 5rem; font-weight: 700; line-height: 1; }
.score-label { font-size: 1rem; font-weight: 500; margin-top: 0.5rem; margin-bottom: 0.3rem; }
.score-sub { font-size: 0.8rem; color: #6b7a92; }
.score-strong { color: #00d4b4; }
.score-partial { color: #f59e0b; }
.score-weak { color: #ef4444; }
.pill-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.8rem; }
.pill { border-radius: 100px; padding: 0.3rem 0.85rem; font-size: 0.78rem; font-weight: 500; }
.pill-match { background: #0d2b22; border: 1px solid #00d4b4; color: #00d4b4; }
.pill-miss  { background: #2b1212; border: 1px solid #ef4444; color: #ef4444; }
.pill-extra { background: #1a2535; border: 1px solid #3d5166; color: #8892a4; }
.skill-section-title { font-family: 'Space Grotesk', sans-serif; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem; }
.title-match { color: #00d4b4; }
.title-miss  { color: #ef4444; }
.title-extra { color: #6b7a92; }
.suggestion { background: #111827; border-left: 3px solid #00d4b4; border-radius: 0 10px 10px 0; padding: 0.9rem 1.2rem; margin-bottom: 0.7rem; font-size: 0.875rem; color: #c8d0de; line-height: 1.6; }
.breakdown-row { display: flex; gap: 1.5rem; background: #0d1625; border-radius: 12px; padding: 1rem 1.5rem; margin: 1rem 0; font-size: 0.85rem; }
.breakdown-label { color: #6b7a92; font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }
.breakdown-value { color: #e8eaf0; font-weight: 600; }

/* Sidebar */
.sidebar-logo { font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: #00d4b4; padding: 0.5rem 0 1.5rem; }
.sidebar-section { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #3d5166; margin: 1.2rem 0 0.6rem; }
.sidebar-tip { background: #111827; border: 1px solid #1e2d40; border-radius: 10px; padding: 0.8rem 1rem; font-size: 0.78rem; color: #6b7a92; line-height: 1.5; margin-bottom: 0.5rem; }
.sidebar-tip strong { color: #e8eaf0; display: block; margin-bottom: 0.2rem; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">📄 ResumeAI</div>', unsafe_allow_html=True)
    st.markdown("**🔍 Resume Screening**")
    st.caption("Match your resume against a job description and see exactly where you stand.")
    st.divider()

    st.markdown('<div class="sidebar-section">How scoring works</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>Skill Overlap (60%)</strong>Exact skill matches between your resume and the JD requirements.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>Semantic Similarity (40%)</strong>Meaning-level match using AI embeddings — catches related experience even without exact keywords.</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="sidebar-section">Score guide</div>', unsafe_allow_html=True)
    st.markdown("🟢 **70%+** — Strong Match")
    st.markdown("🟡 **45–69%** — Partial Match")
    st.markdown("🔴 **Below 45%** — Weak Match")

    st.divider()
    st.markdown('<div class="sidebar-section">Tips</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>Better results</strong>Use single-column PDF resumes for most accurate text extraction.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>JD format</strong>Structured JDs with clear requirement sections score more accurately than narrative-style ones.</div>', unsafe_allow_html=True)

# ── MAIN CONTENT ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🔍 Resume Screening</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Upload your resume and a job description — get your match score, skill gaps, and suggestions instantly.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Your Resume**")
    uploaded_file = st.file_uploader("Upload resume PDF", type=["pdf"], label_visibility="collapsed")

with col2:
    st.markdown("**Job Description**")
    jd_input_mode = st.radio("JD format", ["Paste Text", "Upload PDF", "Upload Image"], horizontal=True, label_visibility="collapsed")
    jd_text = None

    if jd_input_mode == "Paste Text":
        pasted = st.text_area("Paste JD here", height=160, label_visibility="collapsed", placeholder="Paste the job description here...")
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
            st.caption("⚠️ OCR accuracy depends on image quality.")

st.divider()

# if uploaded_file and jd_text:
#     jd_info = extract_jd_info(jd_text)
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
#         tmp.write(uploaded_file.read()); tmp_path = tmp.name
#     with st.spinner("Analyzing your resume..."):
#         result = parse_resume(tmp_path)
#         resume_info = extract_resume_info(result["clean_text"])
#         match = compute_match_score(resume_info, jd_info, result["clean_text"], jd_text)
#         suggestions = generate_suggestions(match["missing_skills"], match["experience_match"])
#     os.remove(tmp_path)

if uploaded_file and jd_text:
    jd_error = validate_jd_text(jd_text)
    if jd_error:
        st.error(jd_error)
        st.stop()

    jd_info = extract_jd_info(jd_text)
    jd_warning = validate_jd_info(jd_info)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read()); tmp_path = tmp.name

    with st.spinner("Analyzing your resume..."):
        parsed = safe_parse_resume(tmp_path)
    os.remove(tmp_path)

    if not parsed["success"]:
        st.error(parsed["error"])
        st.stop()
    if parsed["warning"]:
        st.warning(parsed["warning"])
    if jd_warning:
        st.warning(jd_warning)

    result = parsed["data"]
    resume_info = extract_resume_info(result["clean_text"])
    match = compute_match_score(resume_info, jd_info, result["clean_text"], jd_text)
    suggestions = generate_suggestions(match["missing_skills"], match["experience_match"])

    score = match["overall_score"]
    score_class = "score-strong" if score >= 70 else "score-partial" if score >= 45 else "score-weak"
    label = "Strong Match" if score >= 70 else "Partial Match" if score >= 45 else "Weak Match"

    st.markdown(f"""
    <div class="score-wrapper">
        <div class="score-number {score_class}">{score}%</div>
        <div class="score-label {score_class}">{label}</div>
        <div class="score-sub">{resume_info['name']} &nbsp;·&nbsp; {resume_info['experience_years']} yrs experience &nbsp;·&nbsp; {resume_info['education'] or 'Education not found'}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="breakdown-row">
        <div>
            <div class="breakdown-label">Skill Overlap</div>
            <div class="breakdown-value">{match['skill_overlap_score']}% <span style="color:#3d5166;font-weight:400">(60%)</span></div>
        </div>
        <div>
            <div class="breakdown-label">Semantic Similarity</div>
            <div class="breakdown-value">{match['semantic_similarity_score']}% <span style="color:#3d5166;font-weight:400">(40%)</span></div>
        </div>
        <div>
            <div class="breakdown-label">Experience</div>
            <div class="breakdown-value">{match['experience_match']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="skill-section-title title-match">✅ Matched Skills</div>', unsafe_allow_html=True)
        pills = "".join([f'<span class="pill pill-match">{s}</span>' for s in match["matched_skills"]]) or "<span style='color:#3d5166;font-size:0.85rem'>None matched</span>"
        st.markdown(f'<div class="pill-grid">{pills}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="skill-section-title title-miss">❌ Missing Skills</div>', unsafe_allow_html=True)
        pills = "".join([f'<span class="pill pill-miss">{s}</span>' for s in match["missing_skills"]]) or "<span style='color:#00d4b4;font-size:0.85rem'>None — great coverage!</span>"
        st.markdown(f'<div class="pill-grid">{pills}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="skill-section-title title-extra">📌 Extra Skills</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;color:#3d5166;margin-bottom:0.5rem">You have these — not required by this JD</div>', unsafe_allow_html=True)
        pills = "".join([f'<span class="pill pill-extra">{s}</span>' for s in match["extra_skills"]]) or "<span style='color:#3d5166;font-size:0.85rem'>None</span>"
        st.markdown(f'<div class="pill-grid">{pills}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="skill-section-title title-match">💡 Improvement Suggestions</div>', unsafe_allow_html=True)
    for s in suggestions:
        st.markdown(f'<div class="suggestion">{s}</div>', unsafe_allow_html=True)

elif not uploaded_file and not jd_text:
    st.markdown('<div style="text-align:center;padding:3rem;color:#3d5166;font-size:0.9rem">Upload your resume and provide a job description above to get started.</div>', unsafe_allow_html=True)
elif not uploaded_file:
    st.markdown('<div style="text-align:center;padding:2rem;color:#3d5166;font-size:0.9rem">Upload your resume to continue.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center;padding:2rem;color:#3d5166;font-size:0.9rem">Provide a job description to continue.</div>', unsafe_allow_html=True)
