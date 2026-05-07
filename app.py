from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from llm_client import DEFAULT_MODEL, evaluate_cv
from pdf_utils import detect_suspicious_fragments, extract_text_from_pdf, highlight_suspicious_lines
from sample_cv_generator import generate_samples


load_dotenv()


def main() -> None:
    st.set_page_config(
        page_title="Prompt Injection CV Evaluator",
        layout="wide",
    )

    _apply_styles()

    st.title("Prompt Injection CV Evaluator")
    st.caption("Indirect prompt injection demo for a digital security project")

    with st.sidebar:
        st.header("Run")
        api_key = st.text_input(
            "Groq API key",
            value="",
            type="password",
            placeholder="Uses GROQ_API_KEY if empty",
        )
        model = st.text_input("Model", value=os.getenv("GROQ_MODEL", DEFAULT_MODEL))
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
        force_demo = st.toggle("Force demo fallback", value=False)
        if api_key or os.getenv("GROQ_API_KEY"):
            st.caption("Live Groq path available.")
        else:
            st.caption("No API key detected. The app will use local demo fallback.")

        if st.button("Generate sample PDFs", use_container_width=True):
            generated = generate_samples()
            st.success(f"Generated {len(generated)} PDFs in ./samples")

    uploaded_file = st.file_uploader("Upload CV PDF", type=["pdf"])

    sample_paths = sorted(Path("samples").glob("*.pdf"))
    selected_sample = None
    if sample_paths:
        selected_name = st.selectbox(
            "Or load sample",
            [""] + [path.name for path in sample_paths],
            index=0,
        )
        if selected_name:
            selected_sample = next(path for path in sample_paths if path.name == selected_name)

    pdf_bytes: bytes | None = None
    source_name = ""
    if uploaded_file is not None:
        pdf_bytes = uploaded_file.getvalue()
        source_name = uploaded_file.name
    elif selected_sample is not None:
        pdf_bytes = selected_sample.read_bytes()
        source_name = selected_sample.name

    if pdf_bytes is None:
        st.info("Upload a CV PDF or generate the sample PDFs from the sidebar.")
        return

    try:
        extracted = extract_text_from_pdf(pdf_bytes)
    except Exception as exc:
        st.error(f"Could not read PDF: {exc}")
        return

    suspicious_lines = detect_suspicious_fragments(extracted.text)

    top_cols = st.columns(3)
    top_cols[0].metric("Document", source_name)
    top_cols[1].metric("Pages", extracted.page_count)
    top_cols[2].metric("Extracted characters", extracted.character_count)

    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("X-Ray Extracted Text")
        if suspicious_lines:
            st.warning(f"Possible injection lines detected: {len(suspicious_lines)}")
        else:
            st.success("No obvious prompt-injection phrases detected.")
        st.text_area(
            "Text visible to the AI",
            value=highlight_suspicious_lines(extracted.text),
            height=520,
        )

    with right:
        st.subheader("AI Evaluation")
        mode = st.radio(
            "Mode",
            options=["Vulnerable", "Protected"],
            index=0,
            horizontal=True,
        )
        protected = mode == "Protected"

        if st.button("Evaluate CV", type="primary", use_container_width=True):
            with st.spinner("Evaluating..."):
                try:
                    result = evaluate_cv(
                        cv_text=extracted.text,
                        protected=protected,
                        api_key=api_key,
                        model=model,
                        temperature=temperature,
                        force_demo=force_demo,
                    )
                except Exception as exc:
                    st.error(f"AI request failed: {exc}")
                else:
                    st.session_state["last_result"] = result
                    st.session_state["last_mode"] = mode

        if "last_result" in st.session_state:
            result = st.session_state["last_result"]
            st.caption(f"{st.session_state.get('last_mode', mode)} mode | {result.provider}")
            if result.used_demo_fallback:
                st.info("Demo fallback is active. Add a Groq API key to run the live LLM path.")
            st.markdown(result.response)


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .stTextArea textarea {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.86rem;
            line-height: 1.38;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.35);
            border-radius: 8px;
            padding: 0.8rem 1rem;
            background: transparent;
            color: inherit;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
