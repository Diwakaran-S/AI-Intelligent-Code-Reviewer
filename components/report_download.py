"""
report_download.py — Markdown and PDF download buttons.

Renders styled download buttons for the analysis report in both
Markdown and PDF formats.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from services.report_generator import generate_markdown_report, generate_pdf_report


def render_report_downloads(
    analysis: dict[str, Any],
    filename: str,
    language: str,
) -> None:
    """
    Render download buttons for Markdown and PDF reports.

    Parameters
    ----------
    analysis : dict
        The parsed analysis JSON.
    filename : str
        Original source filename.
    language : str
        Detected programming language.
    """
    st.markdown(
        '<div class="section-header">'
        '<span class="section-icon">📥</span>'
        '<span class="section-title">Download Report</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        # Markdown download
        md_content: str = generate_markdown_report(analysis, filename, language)
        st.download_button(
            label="📄  Download Markdown",
            data=md_content,
            file_name=f"{_strip_ext(filename)}_review.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_md",
        )

    with col2:
        # PDF download
        try:
            pdf_bytes: bytes = generate_pdf_report(analysis, filename, language)
            st.download_button(
                label="📑  Download PDF",
                data=pdf_bytes,
                file_name=f"{_strip_ext(filename)}_review.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf",
            )
        except Exception as exc:
            st.warning(f"PDF generation failed: {exc}", icon="⚠️")


def _strip_ext(filename: str) -> str:
    """Remove the file extension from a filename."""
    dot_idx = filename.rfind(".")
    return filename[:dot_idx] if dot_idx != -1 else filename
