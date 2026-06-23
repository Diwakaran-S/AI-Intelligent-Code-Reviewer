"""
app.py — Intelligent Code Reviewer & Explainer

Main Streamlit application entry point.  Orchestrates the full user
flow: Upload → Preview → Analyze → Results.

Author: AI Engineer
Stack:  Streamlit · NVIDIA NIM · OpenAI SDK · Python 3.11+
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import streamlit as st

from components.analysis_tabs import render_analysis_tabs
from components.metrics_cards import render_metrics_cards
from components.upload_section import render_upload_section
from services.code_analyzer import AnalysisResult, analyze

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
APP_DIR: Path = Path(__file__).parent
CSS_PATH: Path = APP_DIR / "assets" / "styles.css"
LOGO_PATH: Path = APP_DIR / "assets" / "logo.png"


# ── Page Configuration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="Code Reviewer AI — Intelligent Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "## Intelligent Code Reviewer & Explainer\n"
            "AI-powered code analysis platform built with "
            "Streamlit and NVIDIA NIM."
        ),
    },
)


# ── Session State Initialization ─────────────────────────────────────────────


def _init_session_state() -> None:
    """Initialize all session state keys with safe defaults."""
    defaults: dict[str, Any] = {
        "uploaded_content": None,
        "uploaded_filename": None,
        "uploaded_language": None,
        "uploaded_highlight": None,
        "uploaded_icon": None,
        "uploaded_line_count": 0,
        "uploaded_size": 0,
        "analysis_result": None,
        "analysis_error": None,
        "trigger_analysis": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_session_state()


# ── CSS Injection ────────────────────────────────────────────────────────────


def _inject_css() -> None:
    """Load and inject the custom CSS stylesheet."""
    if CSS_PATH.exists():
        css: str = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        logger.warning("CSS file not found at %s", CSS_PATH)


_inject_css()


# ── Sidebar ──────────────────────────────────────────────────────────────────


def _render_sidebar() -> None:
    """Render the sidebar with branding and info."""
    with st.sidebar:
        # Logo
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=80)

        st.markdown(
            """
            # 🔍 Code Reviewer AI
            **Intelligent Code Analysis Platform**

            ---

            #### How It Works
            1. 📁 **Upload** your source code file
            2. 👁️ **Preview** the uploaded code
            3. 🔍 **Analyze** with AI-powered review
            4. 📊 **Explore** results across 7 tabs
            5. 📥 **Download** the full report

            ---

            #### Supported Languages
            - 🐍 Python (`.py`)
            - 🟨 JavaScript (`.js`)
            - 🔷 TypeScript (`.ts`)
            - ☕ Java (`.java`)
            - ⚙️ C (`.c`)
            - ⚙️ C++ (`.cpp`)

            ---

            #### Analysis Includes
            - 📊 Quality Score & Metrics
            - 🐛 Bug Detection
            - 🔒 Security Audit
            - 📖 Code Explanation
            - ⚡ Optimization Tips
            - ✨ Refactored Code
            - 📄 Downloadable Report

            ---
            """
        )

        st.caption("Powered by NVIDIA NIM · LLaMA 3.3 70B")
        st.caption("Built with ❤️ using Streamlit")


_render_sidebar()


# ── Main Content ─────────────────────────────────────────────────────────────


def _render_header() -> None:
    """Render the main page header."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;" class="animate-fade-in">
            <h1 style="margin-bottom: 0.3rem;">Intelligent Code Reviewer & Explainer</h1>
            <p style="color: #94a3b8; font-size: 1.05rem; max-width: 600px; margin: 0 auto;">
                Upload your source code and get AI-powered bug detection,
                security audits, code explanations, and optimization suggestions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _run_analysis() -> None:
    """Execute the AI analysis on the uploaded code."""
    content: str = st.session_state["uploaded_content"]
    filename: str = st.session_state["uploaded_filename"]
    language: str = st.session_state["uploaded_language"]
    line_count: int = st.session_state["uploaded_line_count"]

    with st.spinner("🔍 Analyzing your code with AI... This may take 30–60 seconds."):
        result: AnalysisResult = analyze(
            code=content,
            language=language,
            filename=filename,
            line_count=line_count,
        )

    if result.success:
        st.session_state["analysis_result"] = result
        st.session_state["analysis_error"] = None
        logger.info("Analysis completed successfully for %s", filename)
    else:
        st.session_state["analysis_result"] = result  # still show what we have
        st.session_state["analysis_error"] = result.error_message
        logger.error("Analysis failed for %s: %s", filename, result.error_message)


def _render_results() -> None:
    """Render the analysis results section."""
    result: AnalysisResult | None = st.session_state.get("analysis_result")

    if result is None:
        return

    # Show error banner if there was an issue
    error_msg: str | None = st.session_state.get("analysis_error")
    if error_msg:
        st.error(f"⚠️ Analysis encountered an issue: {error_msg}", icon="🚨")
        if not result.success:
            st.info("Showing partial results where available.", icon="ℹ️")

    st.markdown("---")
    st.markdown(
        '<div class="animate-fade-in-up">',
        unsafe_allow_html=True,
    )

    # Metrics cards
    render_metrics_cards(result.analysis)

    st.markdown("")

    # Analysis tabs
    render_analysis_tabs(
        analysis=result.analysis,
        local_metrics=result.local_metrics,
        language=st.session_state.get("uploaded_language", "Unknown"),
        highlight_key=st.session_state.get("uploaded_highlight", "text"),
        filename=st.session_state.get("uploaded_filename", "file"),
    )

    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    """Main application entry point."""
    _render_header()

    # Upload section
    render_upload_section()

    # Trigger analysis if button was clicked
    if st.session_state.get("trigger_analysis"):
        st.session_state["trigger_analysis"] = False
        if st.session_state.get("uploaded_content"):
            _run_analysis()
            st.rerun()

    # Results section
    _render_results()

    # Footer
    st.markdown(
        """
        <div class="app-footer">
            <p>
                🔍 <strong>Intelligent Code Reviewer & Explainer</strong> •
                Powered by <strong>NVIDIA NIM</strong> & <strong>LLaMA 3.3</strong> •
                Built with <strong>Streamlit</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
