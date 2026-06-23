"""
upload_section.py — File upload component with validation and code preview.

Renders the drag-and-drop file uploader, validates uploaded files,
displays syntax-highlighted code preview, and manages the analyze button.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from utils.file_reader import FileReadResult, FileValidationError, validate_and_read
from utils.syntax_detector import get_supported_extensions


def render_upload_section() -> None:
    """Render the file upload section with code preview and analyze button."""

    st.markdown(
        '<div class="section-header">'
        '<span class="section-icon">📁</span>'
        '<span class="section-title">Upload Source Code</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Supported formats info ───────────────────────────────────────────
    extensions = get_supported_extensions()
    ext_display = "  •  ".join(f"`{e}`" for e in extensions)
    st.caption(f"Supported: {ext_display}  •  Max 500KB")

    # ── File Uploader ────────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "Drop your code file here",
        type=[e.lstrip(".") for e in extensions],
        label_visibility="collapsed",
        key="code_file_uploader",
    )

    if uploaded_file is not None:
        # Only process if it is a new file to prevent resetting analysis on reruns
        if (
            st.session_state.get("uploaded_filename") != uploaded_file.name
            or st.session_state.get("uploaded_size") != uploaded_file.size
        ):
            _process_upload(uploaded_file)
    else:
        # Reset session state if the file was removed
        if st.session_state.get("uploaded_content") is not None:
            st.session_state["uploaded_content"] = None
            st.session_state["uploaded_filename"] = None
            st.session_state["uploaded_language"] = None
            st.session_state["uploaded_highlight"] = None
            st.session_state["uploaded_icon"] = None
            st.session_state["uploaded_line_count"] = 0
            st.session_state["uploaded_size"] = 0
            st.session_state["analysis_result"] = None
            st.session_state["analysis_error"] = None

    # ── Code Preview ─────────────────────────────────────────────────────
    if st.session_state.get("uploaded_content"):
        _render_code_preview()
        _render_analyze_button()


def _process_upload(uploaded_file) -> None:
    """Validate and process the uploaded file."""
    try:
        result: FileReadResult = validate_and_read(uploaded_file)

        # Store in session state
        st.session_state["uploaded_content"] = result.content
        st.session_state["uploaded_filename"] = result.filename
        st.session_state["uploaded_language"] = result.language_info.language
        st.session_state["uploaded_highlight"] = result.language_info.highlight_key
        st.session_state["uploaded_icon"] = result.language_info.icon
        st.session_state["uploaded_line_count"] = result.line_count
        st.session_state["uploaded_size"] = result.size_bytes

        # Clear previous analysis when a new file is uploaded
        st.session_state["analysis_result"] = None
        st.session_state["analysis_error"] = None

    except FileValidationError as exc:
        st.error(f"⚠️ {exc}", icon="🚫")


def _render_code_preview() -> None:
    """Display the uploaded code with syntax highlighting."""
    filename: str = st.session_state.get("uploaded_filename", "file")
    language: str = st.session_state.get("uploaded_language", "Unknown")
    icon: str = st.session_state.get("uploaded_icon", "📄")
    highlight: str = st.session_state.get("uploaded_highlight", "text")
    line_count: int = st.session_state.get("uploaded_line_count", 0)
    size_bytes: int = st.session_state.get("uploaded_size", 0)

    st.markdown("---")

    # File info bar
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"**{icon} {filename}** — {language}")
    with col2:
        st.caption(f"📏 {line_count} lines")
    with col3:
        st.caption(f"💾 {size_bytes / 1024:.1f} KB")

    # Code display
    with st.expander("📝 View Source Code", expanded=False):
        st.code(
            st.session_state["uploaded_content"],
            language=highlight,
            line_numbers=True,
        )


def _render_analyze_button() -> None:
    """Render the Analyze Code button."""
    st.markdown("")  # spacing

    if st.button(
        "🔍  Analyze Code",
        use_container_width=True,
        type="primary",
        key="analyze_btn",
    ):
        st.session_state["trigger_analysis"] = True
