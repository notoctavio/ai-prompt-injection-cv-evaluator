from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_client import DEFAULT_MODEL, evaluate_cv
from pdf_utils import detect_suspicious_fragments, extract_text_from_pdf, highlight_suspicious_lines
from sample_cv_generator import SAMPLES_DIR, generate_samples


load_dotenv()

app = FastAPI(title="GuardianHR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SampleRequest(BaseModel):
    name: str


class ExtractResponse(BaseModel):
    file_name: str
    text: str
    highlighted_text: str
    suspicious_lines: list[str]
    page_count: int
    character_count: int


class EvaluateRequest(BaseModel):
    cv_text: str = Field(min_length=1)
    protected: bool
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    force_demo: bool = False


class EvaluateResponse(BaseModel):
    response: str
    provider: str
    used_demo_fallback: bool


class CompareRequest(BaseModel):
    cv_text: str = Field(min_length=1)
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    force_demo: bool = False


class CompareResponse(BaseModel):
    vulnerable: EvaluateResponse
    protected: EvaluateResponse


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "api_available": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "default_model": os.getenv("GROQ_MODEL", DEFAULT_MODEL),
    }


@app.get("/api/samples")
def list_samples() -> dict[str, list[str]]:
    return {"samples": _sample_names()}


@app.post("/api/samples/generate")
def generate_demo_samples() -> dict[str, list[str]]:
    generate_samples()
    return {"samples": _sample_names()}


@app.post("/api/extract/upload", response_model=ExtractResponse)
async def extract_upload(file: UploadFile = File(...)) -> ExtractResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    return _extract_response(pdf_bytes=await file.read(), file_name=filename)


@app.post("/api/extract/sample", response_model=ExtractResponse)
def extract_sample(request: SampleRequest) -> ExtractResponse:
    sample_path = (SAMPLES_DIR / request.name).resolve()
    samples_root = SAMPLES_DIR.resolve()
    if samples_root not in sample_path.parents or not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample not found.")

    return _extract_response(pdf_bytes=sample_path.read_bytes(), file_name=sample_path.name)


@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    result = evaluate_cv(
        cv_text=request.cv_text,
        protected=request.protected,
        model=request.model or os.getenv("GROQ_MODEL", DEFAULT_MODEL),
        temperature=request.temperature,
        force_demo=request.force_demo,
    )
    return EvaluateResponse(**result.__dict__)


@app.post("/api/compare", response_model=CompareResponse)
def compare(request: CompareRequest) -> CompareResponse:
    model = request.model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    vulnerable = evaluate_cv(
        cv_text=request.cv_text,
        protected=False,
        model=model,
        temperature=request.temperature,
        force_demo=request.force_demo,
    )
    protected = evaluate_cv(
        cv_text=request.cv_text,
        protected=True,
        model=model,
        temperature=request.temperature,
        force_demo=request.force_demo,
    )
    return CompareResponse(
        vulnerable=EvaluateResponse(**vulnerable.__dict__),
        protected=EvaluateResponse(**protected.__dict__),
    )


def _extract_response(pdf_bytes: bytes, file_name: str) -> ExtractResponse:
    extracted = extract_text_from_pdf(pdf_bytes)
    suspicious_lines = detect_suspicious_fragments(extracted.text)
    return ExtractResponse(
        file_name=file_name,
        text=extracted.text,
        highlighted_text=highlight_suspicious_lines(extracted.text),
        suspicious_lines=suspicious_lines,
        page_count=extracted.page_count,
        character_count=extracted.character_count,
    )


def _sample_names() -> list[str]:
    if not SAMPLES_DIR.exists():
        return []
    return sorted(path.name for path in SAMPLES_DIR.glob("*.pdf"))
