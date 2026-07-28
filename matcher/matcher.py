"""
matcher.py
----------
Core matching logic for Module 1.

Takes structured resume info (from skill_extractor.py) and structured JD
info (from jd_parser.py) and computes:
    - Overall match score (0-100)
    - Score breakdown (skill overlap vs semantic similarity)
    - Matched skills (resume has these, JD wants these)
    - Missing skills (JD wants these, resume doesn't have them)
    - Improvement suggestions (actionable, based on missing skills)

Scoring uses two signals combined:
    1. Skill overlap score (60% weight) - exact skill set comparison
    2. Semantic similarity score (40% weight) - meaning-level comparison
       using sentence-transformers embeddings + cosine similarity

The 60/40 weighting is intentional: skills are concrete, verifiable
requirements so they dominate. Semantic similarity catches meaning-level
matches but is noisier (similar-sounding jobs in the same industry can
score high without being a real fit), so it gets less weight.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_skill_overlap(resume_skills: list, jd_skills: list) -> dict:
    """
    Computes exact skill overlap between resume and JD skill lists.

    Args:
        resume_skills: list of skills extracted from the resume
        jd_skills: list of skills required by the JD

    Returns:
        dict with:
            - matched: skills present in both resume and JD
            - missing: skills in JD but not in resume
            - extra: skills in resume but not required by JD
            - overlap_score: percentage of JD skills covered (0-100)
    """
    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    extra = sorted(resume_set - jd_set)

    if len(jd_set) == 0:
        overlap_score = 0.0
    else:
        overlap_score = (len(matched) / len(jd_set)) * 100

    return {
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "overlap_score": round(overlap_score, 1),
    }


def compute_semantic_similarity(resume_text: str, jd_text: str) -> float:
    """
    Computes semantic similarity between resume text and JD text.

    Uses sentence-transformers (all-MiniLM-L6-v2) to generate embeddings
    and cosine similarity to compare them. Falls back to TF-IDF cosine
    similarity if sentence-transformers is not available.

    This catches meaning-level matches that exact skill matching misses —
    e.g. "built scalable distributed systems" matching "distributed systems
    experience required" even without exact phrase overlap.

    Args:
        resume_text: full cleaned resume text
        jd_text: full JD text

    Returns:
        Similarity score as a float between 0 and 100.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode([resume_text, jd_text])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return round(float(similarity) * 100, 1)

    except Exception:
        # Fallback: TF-IDF cosine similarity if sentence-transformers
        # is unavailable or model download fails
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([resume_text, jd_text])
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        return round(float(similarity) * 100, 1)


def compute_match_score(
    resume_info: dict,
    jd_info: dict,
    resume_text: str,
    jd_text: str,
) -> dict:
    """
    Main entry point for Week 4.

    Combines skill overlap and semantic similarity into one overall
    match score, and returns the full breakdown.

    Args:
        resume_info: structured dict from extract_resume_info()
            {name, skills, experience_years, education}
        jd_info: structured dict from extract_jd_info()
            {required_skills, experience_years_required, education_requirement}
        resume_text: full cleaned resume text (for semantic similarity)
        jd_text: full JD text (for semantic similarity)

    Returns:
        dict with:
            - overall_score: weighted final score (0-100)
            - skill_overlap_score: raw skill overlap percentage
            - semantic_similarity_score: raw semantic similarity percentage
            - weights: weights used in the final score
            - matched_skills: skills present in both
            - missing_skills: skills in JD but not in resume
            - extra_skills: skills in resume not required by JD
            - experience_match: whether resume meets experience requirement
    """
    skill_data = compute_skill_overlap(
        resume_info["skills"],
        jd_info["required_skills"],
    )

    semantic_score = compute_semantic_similarity(resume_text, jd_text)

    skill_weight = 0.6
    semantic_weight = 0.4

    overall_score = round(
        (skill_data["overlap_score"] * skill_weight)
        + (semantic_score * semantic_weight),
        1,
    )

    # Experience match check
    required_years = jd_info.get("experience_years_required", 0)
    candidate_years = resume_info.get("experience_years", 0)

    if required_years == 0:
        experience_match = "Not specified in JD"
    elif candidate_years >= required_years:
        experience_match = f"Met ({candidate_years} years, {required_years} required)"
    else:
        experience_match = f"Not met ({candidate_years} years, {required_years} required)"

    return {
        "overall_score": overall_score,
        "skill_overlap_score": skill_data["overlap_score"],
        "semantic_similarity_score": semantic_score,
        "weights": {
            "skill_overlap": skill_weight,
            "semantic_similarity": semantic_weight,
        },
        "matched_skills": skill_data["matched"],
        "missing_skills": skill_data["missing"],
        "extra_skills": skill_data["extra"],
        "experience_match": experience_match,
    }


def generate_suggestions(missing_skills: list, experience_match: str) -> list:
    """
    Generates actionable improvement suggestions based on skill gaps
    and experience match.

    These are template-based suggestions — specific, actionable, and
    directly tied to what the JD requires that the resume doesn't show.
    Not LLM-generated (that's a potential Week 5+ enhancement), but
    still genuinely useful as a starting point.

    Args:
        missing_skills: list of skills the JD requires but resume lacks
        experience_match: experience match string from compute_match_score

    Returns:
        List of suggestion strings.
    """
    suggestions = []

    for skill in missing_skills[:5]:  # Cap at 5 most important gaps
        suggestions.append(
            f"Consider adding '{skill}' to your resume — it is explicitly "
            f"required by this job description. If you have any exposure to "
            f"it, make sure it is mentioned."
        )

    if "Not met" in experience_match:
        suggestions.append(
            "Your experience level appears to be below the JD's stated "
            "requirement. Consider highlighting project work, internships, "
            "or freelance experience to compensate."
        )

    if not missing_skills and "Not met" not in experience_match:
        suggestions.append(
            "Strong match! Focus on tailoring your resume language to mirror "
            "the JD's specific phrasing — this improves both human and ATS "
            "readability."
        )

    return suggestions
