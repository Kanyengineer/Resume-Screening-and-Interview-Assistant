"""
jd_parser.py
------------
Extracts structured information from job description (JD) text.

This is the Week 3 deliverable. JDs are phrased differently from resumes -
they describe REQUIREMENTS ("3+ years required", "Bachelor's degree
preferred") rather than a candidate's actual biographical facts. So while
we reuse the same skill-matching logic from Week 2 (the skills database
stays the same broad, JD-independent vocabulary), the experience and
education extraction need patterns tuned to requirement-style phrasing.
"""

import re

try:
    from parser.skill_extractor import extract_skills
except ImportError:
    # Allows running this file directly as well as importing it as part
    # of the parser package from app.py
    from skill_extractor import extract_skills


def extract_required_experience(text: str) -> int:
    """
    Extracts the minimum years of experience required from JD text.

    Looks for common requirement phrasings:
        "minimum 3 years of professional experience"
        "3+ years required"
        "at least 5 years experience"
        "2-4 years of experience"

    For ranges (e.g. "2-4 years"), returns the lower bound, since that's
    the minimum a candidate needs to be considered.

    Args:
        text: raw or cleaned job description text.

    Returns:
        Minimum years of experience required as an integer.
        Returns 0 if no experience requirement is mentioned.
    """
    # Range pattern: "2-4 years", "2 to 4 years"
    range_match = re.search(
        r"(\d+)\s*(?:-|to)\s*\d+\s*\+?\s*(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )
    if range_match:
        return int(range_match.group(1))

    # Single number pattern: "minimum 3 years", "3+ years", "at least 5 years"
    single_match = re.search(
        r"(\d+)\+?\s*(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )
    if single_match:
        return int(single_match.group(1))

    return 0


def extract_education_requirement(text: str) -> str:
    """
    Extracts the education requirement from JD text.

    JDs don't have a fixed "EDUCATION" section header like resumes do -
    instead the requirement is usually a single line/sentence mentioning
    a degree level. This searches for common degree-related keywords and
    returns the full line they appear in.

    Args:
        text: raw or cleaned job description text.

    Returns:
        The line containing the education requirement, or an empty
        string if none is found.
    """
    degree_keywords = [
        "bachelor", "b.tech", "btech", "b.sc", "bsc",
        "master", "m.tech", "mtech", "m.sc", "msc", "mba",
        "degree", "phd",
    ]

    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower()
        for keyword in degree_keywords:
            # Use word boundaries so short keywords like "bsc" or "mba"
            # don't match as a substring inside unrelated words
            # (e.g. "bsc" incorrectly matching inside "subscription").
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, line_lower):
                return line.strip()

    return ""


def extract_jd_info(text: str) -> dict:
    """
    Main entry point for Week 3.
    Takes raw job description text and returns a structured dict.

    Reuses extract_skills() from Week 2 - the same skills database is
    used for both resumes and JDs, since the database is a fixed,
    broad vocabulary. The JD-specific relevance only comes into play
    later when comparing this output against a parsed resume (Week 4).

    Args:
        text: raw job description text (pasted by the user).

    Returns:
        dict with keys: required_skills, experience_years_required,
        education_requirement
    """
    return {
        "required_skills": extract_skills(text),
        "experience_years_required": extract_required_experience(text),
        "education_requirement": extract_education_requirement(text),
    }


if __name__ == "__main__":
    # Quick manual test - run this file directly against a sample JD
    import sys

    if len(sys.argv) < 2:
        print("Usage: python jd_parser.py <path_to_jd.txt>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        jd_text = f.read()

    info = extract_jd_info(jd_text)
    print("Required Skills:", info["required_skills"])
    print("Experience Required (years):", info["experience_years_required"])
    print("Education Requirement:", info["education_requirement"])
