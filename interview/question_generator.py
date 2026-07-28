"""
question_generator.py
---------------------
Module 2 - Interview Question Generation.

Uses Groq (llama-3.3-70b-versatile) to generate personalized interview
questions based on the candidate's resume and the target job description.

Questions are tailored to the specific candidate - not a generic question
bank. If the resume mentions "built REST APIs using Django" and the JD
requires backend experience, the system generates questions that probe
exactly that experience rather than asking generic "tell me about yourself"
questions.

Question mix (6-8 total):
- 2 technical questions (based on skills the candidate claims to have)
- 2 role-specific questions (based on JD requirements)
- 2 behavioral questions (based on past experience mentioned in resume)
- 1-2 situational/gap questions (probing skills the JD needs but resume lacks)
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def get_groq_client() -> Groq:
    """
    Returns an authenticated Groq client using the API key from .env
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Make sure it is set in your .env file."
        )
    return Groq(api_key=api_key)


def generate_interview_questions(
    resume_info: dict,
    jd_info: dict,
    resume_text: str,
    jd_text: str,
    num_questions: int = 7,
) -> list:
    """
    Generates personalized interview questions using the Groq LLM.

    Args:
        resume_info: structured resume dict from extract_resume_info()
        jd_info: structured JD dict from extract_jd_info()
        resume_text: full cleaned resume text
        jd_text: full JD text
        num_questions: number of questions to generate (default 7)

    Returns:
        List of question dicts, each with:
            - question: the question text
            - type: one of "Technical", "Behavioral", "Role-Specific", "Situational"
            - rationale: why this question is relevant to this candidate/role
    """
    client = get_groq_client()

    prompt = f"""You are an expert technical interviewer. Based on the candidate's resume and the job description below, generate {num_questions} personalized interview questions.

CANDIDATE RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

CANDIDATE'S SKILLS: {", ".join(resume_info.get("skills", []))}
REQUIRED SKILLS: {", ".join(jd_info.get("required_skills", []))}
MISSING SKILLS: {", ".join(set(jd_info.get("required_skills", [])) - set(resume_info.get("skills", [])))}

Generate exactly {num_questions} interview questions. Mix the types:
- 2 Technical questions (probe specific technologies/skills the candidate claims to have)
- 2 Role-Specific questions (based on what this particular job requires)
- 2 Behavioral questions (based on past experience mentioned in the resume, use STAR format prompts)
- 1 Situational/Gap question (probe a skill the JD needs but the resume doesn't clearly show)

Rules:
- Questions must be SPECIFIC to this candidate and role, not generic
- Reference actual things from the resume (projects, technologies, companies)
- Do not ask "Tell me about yourself" or other completely generic questions
- Each question should be something a real technical interviewer would ask

Return ONLY a valid JSON array, no explanation, no markdown, no backticks.
Format:
[
  {{
    "question": "question text here",
    "type": "Technical",
    "rationale": "why this question is relevant"
  }}
]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if model wraps output in them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    questions = json.loads(raw)
    return questions


def format_questions_for_display(questions: list) -> list:
    """
    Ensures all questions have the expected keys, filling in defaults
    for any missing fields (defensive against partial LLM responses).

    Args:
        questions: raw list of question dicts from generate_interview_questions()

    Returns:
        Cleaned list of question dicts with guaranteed keys.
    """
    cleaned = []
    for i, q in enumerate(questions):
        cleaned.append({
            "number": i + 1,
            "question": q.get("question", "Question not available"),
            "type": q.get("type", "General"),
            "rationale": q.get("rationale", ""),
        })
    return cleaned
