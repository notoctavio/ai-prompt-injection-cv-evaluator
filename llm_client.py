from __future__ import annotations

import os
from dataclasses import dataclass

from groq import Groq

from pdf_utils import detect_suspicious_fragments
from prompts import build_messages


DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


@dataclass(frozen=True)
class EvaluationResult:
    response: str
    provider: str
    used_demo_fallback: bool


def evaluate_cv(
    cv_text: str,
    protected: bool,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    force_demo: bool = False,
) -> EvaluationResult:
    clean_api_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()

    if force_demo or not clean_api_key:
        return EvaluationResult(
            response=_demo_response(cv_text=cv_text, protected=protected),
            provider="Local deterministic demo fallback",
            used_demo_fallback=True,
        )

    client = Groq(api_key=clean_api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=build_messages(cv_text=cv_text, protected=protected),
        temperature=temperature,
        max_completion_tokens=700,
    )

    response = completion.choices[0].message.content or ""
    return EvaluationResult(
        response=response.strip(),
        provider=f"Groq / {model}",
        used_demo_fallback=False,
    )


def _demo_response(cv_text: str, protected: bool) -> str:
    suspicious = detect_suspicious_fragments(cv_text)
    lower_text = cv_text.lower()
    looks_weak = any(
        marker in lower_text
        for marker in [
            "no professional it experience",
            "limited programming",
            "beginner",
            "no cybersecurity projects",
        ]
    )

    if protected and suspicious:
        score = "3/10" if looks_weak else "6/10"
        return (
            f"Score: {score}\n\n"
            "Short reasoning: The candidate is evaluated only on visible skills, "
            "experience, projects, and education. The real qualifications are "
            "limited for a cybersecurity role.\n\n"
            "Security finding: Possible indirect prompt injection detected inside "
            "the CV. The instruction was treated as untrusted document content and "
            "was not followed.\n\n"
            "Hiring recommendation: Do not advance yet; request stronger technical "
            "evidence or project work."
        )

    if not protected and suspicious:
        return (
            "Score: 10/10\n\n"
            "Short reasoning: This candidate is an exceptional cybersecurity "
            "engineer and should be considered a top applicant.\n\n"
            "Hiring recommendation: Strong hire."
        )

    score = "4/10" if looks_weak else "7/10"
    recommendation = "Needs more evidence" if looks_weak else "Advance to interview"
    return (
        f"Score: {score}\n\n"
        "Short reasoning: The evaluation is based on the candidate's stated "
        "education, technical skills, projects, and professional experience.\n\n"
        f"Hiring recommendation: {recommendation}."
    )
