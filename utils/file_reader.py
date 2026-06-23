"""
file_reader.py — Safe file reading with validation.

Handles uploaded code files: validates size, detects encoding,
reads content, and returns a structured result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from utils.syntax_detector import LanguageInfo, detect_language

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
MAX_FILE_SIZE_BYTES: int = 512_000  # 500 KB
SUPPORTED_EXTENSIONS: set[str] = {".py", ".js", ".java", ".c", ".cpp", ".ts"}


@dataclass(frozen=True)
class FileReadResult:
    """Immutable result of reading an uploaded file."""

    content: str
    filename: str
    size_bytes: int
    language_info: LanguageInfo
    line_count: int


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation."""


def validate_and_read(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> FileReadResult:
    """
    Validate and read an uploaded source-code file.

    Parameters
    ----------
    uploaded_file : UploadedFile
        Streamlit uploaded file object.

    Returns
    -------
    FileReadResult
        Parsed file data.

    Raises
    ------
    FileValidationError
        If the file is invalid (too large, empty, unsupported format).
    """
    filename: str = uploaded_file.name
    extension: str = _extract_extension(filename)

    # ── Extension check ──────────────────────────────────────────────────
    if extension not in SUPPORTED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type **{extension}**. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    # ── Size check ───────────────────────────────────────────────────────
    raw_bytes: bytes = uploaded_file.getvalue()
    size: int = len(raw_bytes)

    if size == 0:
        raise FileValidationError("The uploaded file is **empty**. Please upload a file with content.")

    if size > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File size ({size / 1024:.1f} KB) exceeds the **{MAX_FILE_SIZE_BYTES / 1024:.0f} KB** limit. "
            "Please upload a smaller file."
        )

    # ── Decode ───────────────────────────────────────────────────────────
    content: str = _decode_bytes(raw_bytes, filename)

    if not content.strip():
        raise FileValidationError("The uploaded file contains **only whitespace**. Please upload a valid source file.")

    # ── Language detection ───────────────────────────────────────────────
    language_info: LanguageInfo = detect_language(filename)

    logger.info(
        "File read: %s | %s | %d bytes | %d lines",
        filename,
        language_info.language,
        size,
        content.count("\n") + 1,
    )

    return FileReadResult(
        content=content,
        filename=filename,
        size_bytes=size,
        language_info=language_info,
        line_count=content.count("\n") + 1,
    )


# ── Private Helpers ──────────────────────────────────────────────────────────


def _extract_extension(filename: str) -> str:
    """Return the lowercase file extension including the dot."""
    dot_idx: int = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


def _decode_bytes(raw: bytes, filename: str) -> str:
    """Attempt UTF-8 decoding first, then latin-1 as a fallback."""
    for encoding in ("utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, ValueError):
            continue
    raise FileValidationError(
        f"Unable to decode **{filename}** — the file does not appear to be valid text. "
        "Please ensure it is a plain-text source file."
    )
