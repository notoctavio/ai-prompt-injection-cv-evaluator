from __future__ import annotations

import re
from dataclasses import dataclass

import fitz


SUSPICIOUS_PATTERNS = [
    r"\bignore\b.*\b(previous|all|system|instructions)\b",
    r"\bdisregard\b.*\b(previous|all|system|instructions)\b",
    r"\bdo not mention\b",
    r"\bnew instruction\b",
    r"\bsystem prompt\b",
    r"\bprompt\b.*\binjection\b",
    r"\bscore\b.*\b10\s*/\s*10\b",
    r"\bgive\b.*\b10\s*/\s*10\b",
    r"\breturn\b.*\b10\s*/\s*10\b",
    r"\byou are now\b",
    r"\bforget\b.*\binstructions\b",
    r"\binstruc(tiune|tion)\b",
    r"\bignora\b.*\binstructiun",
]


@dataclass(frozen=True)
class ExtractedPdf:
    text: str
    page_count: int
    character_count: int


def extract_text_from_pdf(pdf_bytes: bytes) -> ExtractedPdf:
    """Extract text from a PDF, including text that may be visually hidden."""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        pages = [page.get_text("text") for page in document]

    text = "\n".join(page_text.strip() for page_text in pages if page_text.strip())
    return ExtractedPdf(
        text=text,
        page_count=len(pages),
        character_count=len(text),
    )


def detect_suspicious_fragments(text: str) -> list[str]:
    matches: list[str] = []
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(pattern.search(line) for pattern in compiled):
            matches.append(line)

    return matches


def highlight_suspicious_lines(text: str) -> str:
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]
    highlighted_lines = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if any(pattern.search(line) for pattern in compiled):
            highlighted_lines.append(f">>> POSSIBLE INJECTION: {line}")
        else:
            highlighted_lines.append(line)

    return "\n".join(highlighted_lines)
