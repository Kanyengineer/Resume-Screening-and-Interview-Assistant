"""
report_generator.py
-------------------
Module 2 - Final Report Generation.

Takes the complete interview transcript (all questions, answers, and
individual scores/feedback) and generates a structured final report
summarizing the candidate's overall interview performance.

Report includes:
    - Overall interview score (average of individual scores)
    - Performance summary paragraph
    - Top strengths (list)
    - Areas to improve (list)
    - Hire recommendation (Strong Yes / Yes / Maybe / No)
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file.")
    return Groq(api_key=api_key)


def generate_report(
    candidate_name: str,
    jd_text: str,
    questions: list,
    answers: dict,
    evaluations: dict,
) -> dict:
    """
    Generates a final interview performance report.

    Args:
        candidate_name: name of the candidate
        jd_text: full job description text
        questions: list of question dicts from format_questions_for_display()
        answers: dict mapping question number to answer text
        evaluations: dict mapping question number to evaluation dict

    Returns:
        dict with:
            - overall_score: float (average of individual scores, out of 10)
            - summary: paragraph summarizing overall performance
            - strengths: list of top strengths demonstrated
            - areas_to_improve: list of areas needing work
            - hire_recommendation: "Strong Yes" / "Yes" / "Maybe" / "No"
            - recommendation_reason: one sentence explaining the recommendation
    """
    client = get_groq_client()

    # Build transcript
    transcript_lines = []
    scores = []

    for q in questions:
        num = q["number"]
        answer = answers.get(num, "No answer provided")
        evaluation = evaluations.get(num, {})
        score = evaluation.get("score", 0)
        scores.append(score)

        transcript_lines.append(f"""
Q{num} ({q['type']}): {q['question']}
Answer: {answer}
Score: {score}/10
Feedback: {evaluation.get('feedback', 'N/A')}
""")

    transcript = "\n".join(transcript_lines)
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    prompt = f"""You are a senior hiring manager writing a post-interview assessment report.

CANDIDATE: {candidate_name}
AVERAGE INTERVIEW SCORE: {avg_score}/10

JOB DESCRIPTION (summary):
{jd_text[:600]}

FULL INTERVIEW TRANSCRIPT:
{transcript}

Based on the complete interview transcript, write a structured hiring assessment.

Return ONLY a valid JSON object, no explanation, no markdown, no backticks:
{{
    "summary": "<3-4 sentences summarizing overall interview performance>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "areas_to_improve": ["<area 1>", "<area 2>"],
    "hire_recommendation": "<Strong Yes / Yes / Maybe / No>",
    "recommendation_reason": "<one sentence explaining the recommendation>"
}}

Base your hire recommendation on:
- Strong Yes: avg score 8+ and strong across all question types
- Yes: avg score 6.5-7.9 with no major gaps
- Maybe: avg score 5-6.4 or strong in some areas but weak in others
- No: avg score below 5 or critical skill gaps for this role"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    return {
        "candidate_name": candidate_name,
        "overall_score": avg_score,
        "summary": result.get("summary", "Summary not available."),
        "strengths": result.get("strengths", []),
        "areas_to_improve": result.get("areas_to_improve", []),
        "hire_recommendation": result.get("hire_recommendation", "Maybe"),
        "recommendation_reason": result.get("recommendation_reason", ""),
    }
