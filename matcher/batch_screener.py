"""
batch_screener.py
-----------------
Handles batch resume screening - takes multiple resume PDFs and one JD,
runs the full matching pipeline on each, and returns a ranked list of
candidates sorted by match score (highest first).

This is what turns Module 1 from a single-candidate tool into a real
recruiter tool - upload 10 resumes, get a ranked table instantly.

Edge case handling: uses safe_parse_resume() from utils/edge_case_handler
so that corrupted/scanned/very-short resumes get a friendly, specific
message instead of a raw exception string, and don't silently produce a
misleading 0% score indistinguishable from a genuinely weak candidate.
"""

import os

try:
    from parser.resume_parser import parse_resume
    from parser.skill_extractor import extract_resume_info
    from matcher.matcher import compute_match_score, generate_suggestions
    from utils.edge_case_handler import safe_parse_resume
except ImportError:
    from resume_parser import parse_resume
    from skill_extractor import extract_resume_info
    from matcher import compute_match_score, generate_suggestions
    from edge_case_handler import safe_parse_resume


def _empty_result(filename: str, error: str, warning=None) -> dict:
    return {
        "filename": filename,
        "name": "Unknown",
        "overall_score": 0,
        "skill_overlap_score": 0,
        "semantic_similarity_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "experience_match": "N/A",
        "suggestions": [],
        "warning": warning,
        "error": error,
    }


def screen_multiple_resumes(resume_paths: list, jd_info: dict, jd_text: str) -> list:
    """
    Runs the full matching pipeline on multiple resumes against one JD.

    Args:
        resume_paths: list of file paths to resume PDFs
        jd_info: structured JD dict from extract_jd_info()
        jd_text: raw JD text (for semantic similarity)

    Returns:
        List of result dicts, sorted by overall_score descending.
        Each dict contains:
            - filename: original PDF filename
            - name: candidate name extracted from resume
            - overall_score: match score (0-100)
            - skill_overlap_score: skill overlap component
            - semantic_similarity_score: semantic component
            - matched_skills: list of matched skills
            - missing_skills: list of missing skills
            - experience_match: experience match status string
            - suggestions: list of improvement suggestions
            - warning: non-blocking note (e.g. "resume very short"), or None
            - error: friendly error message if parsing failed, or None
    """
    results = []

    for path in resume_paths:
        filename = os.path.basename(path)

        # Corrupted / password-protected / scanned-image / unreadable PDFs
        # are caught here with a friendly, specific message instead of
        # letting a raw exception (or a silent empty parse) through.
        parsed = safe_parse_resume(path)

        if not parsed["success"]:
            results.append(_empty_result(filename, parsed["error"]))
            continue

        resume = parsed["data"]

        try:
            resume_info = extract_resume_info(resume["clean_text"])
            match = compute_match_score(
                resume_info,
                jd_info,
                resume["clean_text"],
                jd_text,
            )
            suggestions = generate_suggestions(
                match["missing_skills"],
                match["experience_match"],
            )

            results.append({
                "filename": filename,
                "name": resume_info["name"],
                "overall_score": match["overall_score"],
                "skill_overlap_score": match["skill_overlap_score"],
                "semantic_similarity_score": match["semantic_similarity_score"],
                "matched_skills": match["matched_skills"],
                "missing_skills": match["missing_skills"],
                "experience_match": match["experience_match"],
                "suggestions": suggestions,
                # e.g. "resume very short, score may be less accurate" - non-blocking
                "warning": parsed["warning"],
                "error": None,
            })

        except Exception:
            # Don't let one bad resume crash the whole batch. This is a
            # genuinely unexpected failure past the parsing stage, so we
            # keep the message generic rather than guessing at a cause.
            results.append(_empty_result(
                filename,
                "Something went wrong analyzing this resume. Please check "
                "the file and try again.",
            ))

    # Sort by overall score, highest first
    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results