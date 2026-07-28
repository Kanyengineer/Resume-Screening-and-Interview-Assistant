import streamlit as st
import tempfile
import os

from utils.edge_case_handler import (
    safe_parse_resume,
    validate_jd_text,
    validate_jd_info,
    safe_generate_questions,
    safe_evaluate_answer,
    safe_generate_report,
)

from parser.skill_extractor import extract_resume_info
from parser.jd_parser import extract_jd_info
from parser.jd_input import get_jd_text

st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0f1e; color: #e8eaf0; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1200px; }
section[data-testid="stSidebar"] { background: #0d1321; border-right: 1px solid #1e2d40; }
.page-title { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem; }
.page-sub { font-size: 0.9rem; color: #6b7a92; margin-bottom: 2rem; }
.question-card { background: #111827; border: 1px solid #1e2d40; border-radius: 14px; padding: 1.5rem 1.8rem; margin-bottom: 0.5rem; position: relative; }
.question-card::before { content: ''; position: absolute; top: 0; left: 0; bottom: 0; width: 3px; border-radius: 14px 0 0 14px; background: #00d4b4; }
.q-type-badge { display: inline-block; background: #0d2b22; border: 1px solid #00d4b4; color: #00d4b4; border-radius: 100px; padding: 0.2rem 0.75rem; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.8rem; }
.q-type-behavioral { background: #1a1a2e; border-color: #818cf8; color: #818cf8; }
.q-type-situational { background: #1a2b1a; border-color: #34d399; color: #34d399; }
.q-type-rolespecific { background: #2b1a1a; border-color: #f87171; color: #f87171; }
.q-number { font-family: 'Space Grotesk', sans-serif; font-size: 0.75rem; font-weight: 600; color: #3d5166; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.08em; }
.q-text { font-size: 1rem; color: #e8eaf0; line-height: 1.65; font-weight: 400; margin-bottom: 1rem; }
.score-badge { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.4rem 1rem; border-radius: 100px; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.8rem; }
.score-high { background: #0d2b22; border: 1px solid #00d4b4; color: #00d4b4; }
.score-mid  { background: #2b2200; border: 1px solid #f59e0b; color: #f59e0b; }
.score-low  { background: #2b1212; border: 1px solid #ef4444; color: #ef4444; }
.feedback-box { background: #0d1625; border-radius: 10px; padding: 1rem 1.2rem; margin-top: 0.8rem; font-size: 0.85rem; line-height: 1.6; }
.feedback-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #3d5166; margin-bottom: 0.3rem; }
.feedback-text { color: #c8d0de; }
.strength-text { color: #00d4b4; }
.improve-text  { color: #f59e0b; }
.report-card { background: #111827; border: 1px solid #1e2d40; border-radius: 16px; padding: 2rem; margin-bottom: 1rem; }
.report-score { font-family: 'Space Grotesk', sans-serif; font-size: 3.5rem; font-weight: 700; text-align: center; }
.rec-badge { display: inline-block; border-radius: 100px; padding: 0.5rem 1.5rem; font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 700; }
.rec-strong-yes { background: #0d2b22; border: 2px solid #00d4b4; color: #00d4b4; }
.rec-yes   { background: #0d2b22; border: 2px solid #34d399; color: #34d399; }
.rec-maybe { background: #2b2200; border: 2px solid #f59e0b; color: #f59e0b; }
.rec-no    { background: #2b1212; border: 2px solid #ef4444; color: #ef4444; }
.sidebar-logo { font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: #00d4b4; padding: 0.5rem 0 1.5rem; }
.sidebar-tip { background: #111827; border: 1px solid #1e2d40; border-radius: 10px; padding: 0.8rem 1rem; font-size: 0.78rem; color: #6b7a92; line-height: 1.5; margin-bottom: 0.5rem; }
.sidebar-tip strong { color: #e8eaf0; display: block; margin-bottom: 0.2rem; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-logo">📄 ResumeAI</div>', unsafe_allow_html=True)
    st.markdown("**🎤 Interview Prep**")
    st.caption("AI-generated questions tailored to your resume and target role.")
    st.divider()
    st.markdown("🔧 **Technical** — Your specific skills")
    st.markdown("🎯 **Role-Specific** — Job requirements")
    st.markdown("🧠 **Behavioral** — Past experience (STAR)")
    st.markdown("💡 **Situational** — Skill gap areas")
    st.divider()
    st.markdown('<div class="sidebar-tip"><strong>Be specific</strong>Give concrete examples from real experience — vague answers score lower.</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tip"><strong>STAR method</strong>For behavioral: Situation, Task, Action, Result.</div>', unsafe_allow_html=True)
    st.divider()
    st.caption("Groq API · LLaMA 3.3 70B")

st.markdown('<div class="page-title">🎤 Interview Prep</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Get personalized questions, answer them, and receive AI feedback + a final report.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Your Resume**")
    uploaded_file = st.file_uploader("Resume PDF", type=["pdf"], label_visibility="collapsed")
with col2:
    st.markdown("**Job Description**")
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

if uploaded_file and jd_text:
    # --- Edge case: empty / whitespace-only JD ---
    jd_error = validate_jd_text(jd_text)
    if jd_error:
        st.error(jd_error)
        st.stop()

    jd_info = extract_jd_info(jd_text)

    # --- Edge case: JD with no detectable skills (non-blocking warning) ---
    jd_warning = validate_jd_info(jd_info)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read()); tmp_path = tmp.name

    with st.spinner("Parsing resume..."):
        parsed = safe_parse_resume(tmp_path)
    os.remove(tmp_path)

    # --- Edge case: corrupted / scanned-image / unreadable PDF ---
    if not parsed["success"]:
        st.error(parsed["error"])
        st.stop()
    if parsed["warning"]:
        # --- Edge case: very short resume, parseable but thin ---
        st.warning(parsed["warning"])
    if jd_warning:
        st.warning(jd_warning)

    result = parsed["data"]
    resume_info = extract_resume_info(result["clean_text"])

    st.session_state.resume_text = result["clean_text"]
    st.session_state.jd_text = jd_text

    st.write(f"**Candidate:** {resume_info['name']} &nbsp;·&nbsp; {resume_info['experience_years']} years experience")
    num_q = st.slider("Number of questions", min_value=5, max_value=10, value=7)

    if st.button("🎯 Generate Interview Questions", type="primary"):
        with st.spinner("Generating personalized questions..."):
            # --- Edge case: Groq API failure (timeout/rate limit/bad JSON) ---
            gen_result = safe_generate_questions(
                resume_info, jd_info, result["clean_text"], jd_text, num_questions=num_q,
            )
            if not gen_result["success"]:
                st.error(gen_result["error"])
            else:
                st.session_state.questions = gen_result["data"]
                st.session_state.answers = {}
                st.session_state.evaluations = {}
                st.session_state.report = None
                st.session_state.candidate_name = resume_info["name"]

    if "questions" in st.session_state and st.session_state.questions:
        st.markdown("---")
        st.markdown(f"### {len(st.session_state.questions)} Personalized Questions")

        type_badge_class = {
            "Technical": "", "Behavioral": "q-type-behavioral",
            "Role-Specific": "q-type-rolespecific", "Situational": "q-type-situational", "General": "",
        }

        for q in st.session_state.questions:
            num = q["number"]
            badge_class = type_badge_class.get(q["type"], "")
            is_answered = num in st.session_state.get("evaluations", {})

            st.markdown(f"""
            <div class="question-card">
                <div class="q-number">Question {num}</div>
                <div class="q-type-badge {badge_class}">{q['type']}</div>
                <div class="q-text">{q['question']}</div>
            </div>
            """, unsafe_allow_html=True)

            if is_answered:
                ev = st.session_state.evaluations[num]
                score = ev["score"]
                score_class = "score-high" if score >= 7 else "score-mid" if score >= 5 else "score-low"
                st.markdown(f"""
                <div class="score-badge {score_class}">⭐ {score}/10</div>
                <div class="feedback-box">
                    <div class="feedback-label">Feedback</div>
                    <div class="feedback-text">{ev['feedback']}</div>
                    <br>
                    <div class="feedback-label">✅ Strength</div>
                    <div class="strength-text">{ev['strength']}</div>
                    <br>
                    <div class="feedback-label">📈 Improve</div>
                    <div class="improve-text">{ev['improvement']}</div>
                </div>
                <br>
                """, unsafe_allow_html=True)
            else:
                answer = st.text_area(
                    f"Your answer to Q{num}:", key=f"answer_{num}",
                    height=120, placeholder="Type your answer here...", label_visibility="collapsed",
                )
                if st.button(f"Submit Answer →", key=f"submit_{num}"):
                    with st.spinner("Evaluating your answer..."):
                        # --- Edge case: empty answer + Groq API failure ---
                        # (empty-answer check now lives inside safe_evaluate_answer,
                        # so this covers both cases with one call)
                        eval_result = safe_evaluate_answer(
                            question=q["question"], answer=answer,
                            question_type=q["type"],
                            jd_text=st.session_state.jd_text,
                            resume_text=st.session_state.resume_text,
                        )
                        if not eval_result["success"]:
                            st.warning(eval_result["error"])
                        else:
                            st.session_state.answers[num] = answer
                            st.session_state.evaluations[num] = eval_result["data"]
                            st.rerun()

        total_q = len(st.session_state.questions)
        answered_q = len(st.session_state.get("evaluations", {}))

        st.markdown("---")
        st.write(f"**Progress: {answered_q}/{total_q} questions answered**")
        st.progress(answered_q / total_q)

        if answered_q == total_q:
            if st.button("📋 Generate Final Report", type="primary"):
                with st.spinner("Generating your interview report..."):
                    # --- Edge case: Groq API failure during report generation ---
                    report_result = safe_generate_report(
                        candidate_name=st.session_state.candidate_name,
                        jd_text=st.session_state.jd_text,
                        questions=st.session_state.questions,
                        answers=st.session_state.answers,
                        evaluations=st.session_state.evaluations,
                    )
                    if not report_result["success"]:
                        st.error(report_result["error"])
                    else:
                        st.session_state.report = report_result["data"]

        if st.session_state.get("report"):
            report = st.session_state.report
            st.markdown("---")
            st.markdown("## 📋 Interview Report")

            rec = report["hire_recommendation"]
            rec_class = {"Strong Yes": "rec-strong-yes", "Yes": "rec-yes", "Maybe": "rec-maybe", "No": "rec-no"}.get(rec, "rec-maybe")
            score_color = "#00d4b4" if report["overall_score"] >= 7 else "#f59e0b" if report["overall_score"] >= 5 else "#ef4444"

            st.markdown(f"""
            <div class="report-card" style="text-align:center">
                <div style="font-size:0.8rem;color:#6b7a92;margin-bottom:0.5rem">OVERALL INTERVIEW SCORE</div>
                <div class="report-score" style="color:{score_color}">{report['overall_score']}/10</div>
                <div style="margin-top:1rem"><div class="rec-badge {rec_class}">{rec}</div></div>
                <div style="font-size:0.85rem;color:#6b7a92;margin-top:0.5rem">{report['recommendation_reason']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="report-card">
                <div style="font-family:'Space Grotesk',sans-serif;font-size:0.75rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#3d5166;margin-bottom:0.8rem">Performance Summary</div>
                <div style="font-size:0.95rem;color:#c8d0de;line-height:1.7">{report['summary']}</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                strengths_html = "".join([f'<li style="margin-bottom:0.5rem;color:#c8d0de">{s}</li>' for s in report["strengths"]])
                st.markdown(f'<div class="report-card"><div style="font-family:\'Space Grotesk\',sans-serif;font-size:0.75rem;font-weight:600;text-transform:uppercase;color:#00d4b4;margin-bottom:0.8rem">✅ Top Strengths</div><ul style="padding-left:1.2rem;margin:0">{strengths_html}</ul></div>', unsafe_allow_html=True)
            with c2:
                improve_html = "".join([f'<li style="margin-bottom:0.5rem;color:#c8d0de">{s}</li>' for s in report["areas_to_improve"]])
                st.markdown(f'<div class="report-card"><div style="font-family:\'Space Grotesk\',sans-serif;font-size:0.75rem;font-weight:600;text-transform:uppercase;color:#f59e0b;margin-bottom:0.8rem">📈 Areas to Improve</div><ul style="padding-left:1.2rem;margin:0">{improve_html}</ul></div>', unsafe_allow_html=True)

        elif answered_q > 0 and answered_q < total_q:
            st.info(f"Answer all {total_q} questions to generate your final report.")

elif not uploaded_file and not jd_text:
    st.markdown('<div style="text-align:center;padding:3rem;color:#3d5166;font-size:0.9rem">Upload your resume and provide a job description to get started.</div>', unsafe_allow_html=True)
elif not uploaded_file:
    st.markdown('<div style="text-align:center;padding:2rem;color:#3d5166;font-size:0.9rem">Upload your resume to continue.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="text-align:center;padding:2rem;color:#3d5166;font-size:0.9rem">Provide a job description to continue.</div>', unsafe_allow_html=True)
