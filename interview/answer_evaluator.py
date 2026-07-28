"""
answer_evaluator.py
-------------------
Module 2 - Answer Evaluation.

Takes a question + candidate's answer + job context and uses Groq
(llama-3.3-70b-versatile) to evaluate the answer on:
    - Score: 1-10
    - Feedback: what was good, what was missing
    - Strength: the strongest part of the answer
    - Improvement: one specific thing to improve

This runs after each answer is submitted, giving the candidate
immediate, specific feedback rather than waiting until the end.
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


def evaluate_answer(
    question: str,
    answer: str,
    question_type: str,
    jd_text: str,
    resume_text: str,
) -> dict:
    """
    Evaluates a candidate's answer to an interview question.

    Args:
        question: the interview question that was asked
        answer: the candidate's answer
        question_type: Technical / Behavioral / Role-Specific / Situational
        jd_text: full job description text (for context)
        resume_text: full resume text (for context)

    Returns:
        dict with:
            - score: int 1-10
            - feedback: overall feedback string
            - strength: what the candidate did well
            - improvement: one specific thing to improve
    """
    client = get_groq_client()

    prompt = f"""You are an expert technical interviewer evaluating a candidate's answer.

JOB DESCRIPTION SUMMARY:
{jd_text[:800]}

CANDIDATE RESUME SUMMARY:
{resume_text[:600]}

QUESTION TYPE: {question_type}
QUESTION: {question}
CANDIDATE'S ANSWER: {answer}

Evaluate this answer strictly and fairly. Consider:
- Depth and specificity of the answer
- Technical accuracy (for technical questions)
- Use of concrete examples (for behavioral questions)
- Relevance to the role requirements
- Clarity and communication

Return ONLY a valid JSON object, no explanation, no markdown, no backticks:
{{
    "score": <integer 1-10>,
    "feedback": "<2-3 sentences of overall feedback>",
    "strength": "<one specific thing the candidate did well>",
    "improvement": "<one specific, actionable thing to improve>"
}}

Scoring guide:
1-3: Poor - vague, incorrect, or completely off-topic
4-5: Below average - some relevant points but lacks depth
6-7: Good - solid answer with room for improvement
8-9: Strong - detailed, specific, well-structured
10: Exceptional - could not be meaningfully improved"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)

    # Ensure all keys exist with safe defaults
    return {
        "score": int(result.get("score", 5)),
        "feedback": result.get("feedback", "No feedback available."),
        "strength": result.get("strength", "Not specified."),
        "improvement": result.get("improvement", "Not specified."),
    }
