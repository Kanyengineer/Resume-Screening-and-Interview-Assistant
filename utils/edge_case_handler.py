"""
utils/edge_case_handler.py
---------------------------
Centralized edge-case validation and friendly error handling for the
whole app. This does NOT change any logic in parser/, matcher/, or
interview/ — it wraps those modules so pages get back a simple, safe
result instead of a raw exception or a silent garbage output.

Covers the 5 known failure points:
    1. Empty / corrupted / password-protected / scanned-image PDF resumes
    2. Empty answer submissions (centralized here so it's consistent
       everywhere it's checked, not just inline in the page)
    3. Groq API failures (timeouts, rate limits, malformed JSON) —
       translated from raw SDK exceptions into friendly messages
    4. Empty / whitespace-only / no-skill JDs
    5. Very short resumes that give the matcher almost nothing to work with

Usage pattern in a page:
    result = safe_parse_resume(tmp_path)
    if not result["success"]:
        st.error(result["error"]); st.stop()
    if result["warning"]:
        st.warning(result["warning"])
    data = result["data"]   # same shape parse_resume() normally returns
"""

import json
from typing import Optional

from parser.resume_parser import parse_resume
from interview.question_generator import (
    generate_interview_questions,
    format_questions_for_display,
)
from interview.answer_evaluator import evaluate_answer
from interview.report_generator import generate_report


# ---------------------------------------------------------------------------
# Thresholds — tune these if needed
# ---------------------------------------------------------------------------
MIN_CHARS_EMPTY = 20     # below this -> "no extractable text" (blocking)
MIN_CHARS_SHORT = 150    # below this -> "too short to score reliably" (warning)
MIN_JD_SKILLS = 1        # below this -> "no detectable requirements" (warning)


# ---------------------------------------------------------------------------
# 1. Resume PDF validation
# ---------------------------------------------------------------------------
def safe_parse_resume(pdf_path: str) -> dict:
    """
    Wraps parse_resume() with corruption handling and content-quality checks.

    Returns:
        {
            "success": bool,        # False = blocking failure, stop the page
            "error": str | None,    # show with st.error() when success=False
            "warning": str | None,  # show with st.warning(), then continue
            "data": dict | None,    # normal parse_resume() output if success
        }
    """
    try:
        result = parse_resume(pdf_path)
    except Exception as e:
        msg = str(e).lower()
        if "password" in msg or "encrypt" in msg:
            return _fail(
                "This PDF is password-protected. Please upload an unlocked file."
            )
        return _fail(
            "This file couldn't be read as a PDF. It may be corrupted, "
            "not a real PDF, or in an unsupported format — try re-exporting "
            "it (e.g. from Word or Google Docs) and upload again."
        )

    char_count = result.get("char_count", 0)

    # Scanned/image-only PDF — pdfplumber opened the file fine but found
    # no real text layer to extract.
    if char_count < MIN_CHARS_EMPTY:
        return _fail(
            "No readable text was found in this PDF. It's likely a scanned "
            "image rather than a text-based file. Try exporting the resume "
            "directly from Word/Google Docs instead of scanning a printed copy."
        )

    # Very short resume — parseable, but almost nothing to score against.
    warning = None
    if char_count < MIN_CHARS_SHORT:
        warning = (
            "This resume is very short, so the match score and interview "
            "questions may be less accurate than usual. For best results, "
            "upload a more complete resume."
        )

    return {"success": True, "error": None, "warning": warning, "data": result}


def _fail(message: str) -> dict:
    return {"success": False, "error": message, "warning": None, "data": None}


# ---------------------------------------------------------------------------
# 2. Answer submission validation
# ---------------------------------------------------------------------------
def validate_answer(answer: str) -> Optional[str]:
    """Returns an error message if the answer is empty/whitespace, else None."""
    if not answer or not answer.strip():
        return "Please type an answer before submitting."
    return None


# ---------------------------------------------------------------------------
# 3. Groq API failure handling
# ---------------------------------------------------------------------------
def _friendly_groq_error(e: Exception) -> str:
    """Translates a raw exception from a Groq call into a friendly message."""
    if isinstance(e, json.JSONDecodeError):
        return (
            "The AI returned a response we couldn't understand. "
            "This sometimes happens — please try again."
        )

    name = type(e).__name__.lower()
    msg = str(e).lower()

    if "ratelimit" in name or "429" in msg or "rate_limit" in msg:
        return (
            "The AI service is receiving too many requests right now. "
            "Please wait a moment and try again."
        )
    if "authenticat" in name or "401" in msg or "api key" in msg or "api_key" in msg:
        return "There's a problem with the AI service configuration. Please contact the app owner."
    if "timeout" in name or "timed out" in msg:
        return "The AI service took too long to respond. Please try again."
    if "connection" in name or "connect" in msg:
        return "Couldn't reach the AI service. Please check your internet connection and try again."

    return "Something went wrong talking to the AI service. Please try again in a moment."


def safe_generate_questions(resume_info, jd_info, resume_text, jd_text, num_questions=7) -> dict:
    """Wraps generate_interview_questions() with friendly error handling."""
    try:
        raw_questions = generate_interview_questions(
            resume_info, jd_info, resume_text, jd_text, num_questions=num_questions,
        )
        questions = format_questions_for_display(raw_questions)
        if not questions:
            return {"success": False, "error": "No questions could be generated. Please try again.", "data": None}
        return {"success": True, "error": None, "data": questions}
    except Exception as e:
        return {"success": False, "error": _friendly_groq_error(e), "data": None}


def safe_evaluate_answer(question, answer, question_type, jd_text, resume_text) -> dict:
    """Wraps evaluate_answer() with input validation + friendly error handling."""
    err = validate_answer(answer)
    if err:
        return {"success": False, "error": err, "data": None}
    try:
        evaluation = evaluate_answer(
            question=question, answer=answer, question_type=question_type,
            jd_text=jd_text, resume_text=resume_text,
        )
        return {"success": True, "error": None, "data": evaluation}
    except Exception as e:
        return {"success": False, "error": _friendly_groq_error(e), "data": None}


def safe_generate_report(candidate_name, jd_text, questions, answers, evaluations) -> dict:
    """Wraps generate_report() with friendly error handling."""
    try:
        report = generate_report(
            candidate_name=candidate_name, jd_text=jd_text,
            questions=questions, answers=answers, evaluations=evaluations,
        )
        return {"success": True, "error": None, "data": report}
    except Exception as e:
        return {"success": False, "error": _friendly_groq_error(e), "data": None}


# ---------------------------------------------------------------------------
# 4. JD validation
# ---------------------------------------------------------------------------
def validate_jd_text(jd_text: str) -> Optional[str]:
    """Returns an error message if the JD text is empty/whitespace-only, else None."""
    if not jd_text or not jd_text.strip():
        return "The job description appears to be empty. Please paste or upload one."
    return None


def validate_jd_info(jd_info: dict) -> Optional[str]:
    """
    Returns a WARNING (not a blocker) if no skills were detected in the JD.
    A JD with 0 detected skills is still technically usable, but skill
    overlap divides by JD skill count — so 0 required skills means every
    resume scores 0% on that component regardless of fit.
    """
    if len(jd_info.get("required_skills", [])) < MIN_JD_SKILLS:
        return (
            "No recognizable skills were detected in this job description. "
            "The match score below may not be meaningful — try pasting the "
            "full JD text, including the requirements/qualifications section."
        )
    return None
