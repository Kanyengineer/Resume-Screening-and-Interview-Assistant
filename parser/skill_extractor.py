"""
skill_extractor.py
-------------------
Extracts structured information from cleaned resume text.

Week 6 fixes:
- extract_name(): skips section headers, contact info, bullet points
- extract_experience_years(): uses most recent year range (not earliest)
  to avoid picking up graduation year as work start year
"""

import re

try:
    from parser.skills_db import SKILLS_DB
except ImportError:
    from skills_db import SKILLS_DB

SECTION_HEADERS = {
    "contact", "summary", "objective", "skills", "experience",
    "education", "projects", "certifications", "awards", "languages",
    "interests", "references", "profile", "about", "work experience",
    "professional experience", "technical skills", "soft skills",
    "volunteer", "publications", "hobbies", "personal",
}


def extract_skills(text: str) -> list:
    text_lower = text.lower()
    found_skills = set()
    for canonical_name, variants in SKILLS_DB.items():
        for variant in variants:
            pattern = r"\b" + re.escape(variant) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.add(canonical_name)
                break
    return sorted(found_skills)


def extract_experience_years(text: str) -> int:
    # Direct mention: "3 years building X", "2+ years experience"
    direct_match = re.search(
        r"(\d+)\+?\s*(?:years?|yrs?)\b",
        text,
        re.IGNORECASE,
    )
    if direct_match:
        return int(direct_match.group(1))

    # Fallback: year ranges like "(2022 - Present)"
    # Use MOST RECENT start year to avoid picking up graduation year
    year_matches = re.findall(
        r"(20\d{2})\s*[-–]\s*(?:present|20\d{2})",
        text,
        re.IGNORECASE,
    )
    if year_matches:
        most_recent_start = max(int(y) for y in year_matches)
        current_year = 2026
        return max(0, current_year - most_recent_start)

    return 0


def extract_education(text: str) -> str:
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "education" in line.lower():
            following_lines = lines[i + 1: i + 3]
            education_info = " | ".join(l for l in following_lines if l.strip())
            return education_info
    return ""


def extract_name(text: str) -> str:
    """
    Extracts candidate name from resume text.
    Skips: section headers, contact info (email/phone/URL),
    bullet points, and overly long lines.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    for line in lines:
        # Skip known section headers
        if line.lower() in SECTION_HEADERS:
            continue
        # Skip contact info lines (email, phone, URL)
        if re.search(r"@|www\.|http|linkedin|github|\+\d{5,}|\d{8,}", line.lower()):
            continue
        # Skip bullet points
        if line.startswith("-") or line.startswith("•") or line.startswith("*"):
            continue
        # Skip very long lines (summary sentences, not names)
        if len(line) > 60:
            continue
        return line

    return lines[0] if lines else ""


def extract_resume_info(text: str) -> dict:
    return {
        "name": extract_name(text),
        "skills": extract_skills(text),
        "experience_years": extract_experience_years(text),
        "education": extract_education(text),
    }