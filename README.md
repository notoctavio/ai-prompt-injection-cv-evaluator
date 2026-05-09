# Prompt Injection CV Evaluator

Small Proof of Concept for a university digital security project. It shows how
hidden text inside a PDF CV can manipulate an AI evaluator through indirect
prompt injection, then compares the result with a protected prompt.

The primary app is now a professional React + FastAPI interface. The older
Streamlit prototype is still available in `app.py` if you want a simple fallback.

## What The Demo Shows

- A normal-looking PDF can contain hidden text.
- PDF extraction reveals the hidden instruction in the app's X-Ray view.
- Vulnerable mode mixes trusted app instructions with untrusted CV content.
- Protected mode treats the CV as untrusted data and ignores commands inside it.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install the React frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

Create a `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

The app also includes a deterministic demo fallback, so the interface can be
tested without an API key.

## Run

Backend:

```bash
.venv/bin/uvicorn backend:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm run dev -- --port 8501
```

Open:

```text
http://localhost:8501
```

Optional Streamlit fallback:

```bash
streamlit run app.py
```

## Generate Sample PDFs

Inside the app, click `Generate sample PDFs`, or run:

```bash
python3 sample_cv_generator.py
```

Generated files:

- `samples/clean_candidate.pdf`
- `samples/weak_candidate.pdf`
- `samples/poisoned_hidden_prompt.pdf`

## Suggested Presentation Flow

1. Generate the sample PDFs.
2. Load `poisoned_hidden_prompt.pdf`.
3. Show the X-Ray view and the hidden instruction.
4. Run `Vulnerable` mode.
5. Run `Protected` mode on the same PDF.
6. Compare the two answers.
