"""
syntax_detector.py — Automatic programming language detection.

Maps file extensions to language metadata used for syntax highlighting,
prompt context, and UI display.
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Language Info ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class LanguageInfo:
    """Metadata about a detected programming language."""

    language: str        # Human-readable name, e.g. "Python"
    highlight_key: str   # Key for syntax highlighting (Streamlit / Prism)
    icon: str            # Emoji/icon for UI display
    extension: str       # Original file extension


# ── Extension → Language Mapping ─────────────────────────────────────────────

_LANGUAGE_MAP: dict[str, tuple[str, str, str]] = {
    # extension: (language_name, highlight_key, icon)
    ".py":   ("Python",     "python",     "🐍"),
    ".js":   ("JavaScript", "javascript", "🟨"),
    ".java": ("Java",       "java",       "☕"),
    ".c":    ("C",          "c",          "⚙️"),
    ".cpp":  ("C++",        "cpp",        "⚙️"),
    ".ts":   ("TypeScript", "typescript", "🔷"),
}

_DEFAULT_LANGUAGE: tuple[str, str, str] = ("Plain Text", "text", "📄")


def detect_language(filename: str) -> LanguageInfo:
    """
    Detect the programming language from a filename.

    Parameters
    ----------
    filename : str
        Name of the uploaded file (e.g. ``"main.py"``).

    Returns
    -------
    LanguageInfo
        Detected language metadata.
    """
    ext: str = _extract_extension(filename)
    lang_name, hl_key, icon = _LANGUAGE_MAP.get(ext, _DEFAULT_LANGUAGE)

    return LanguageInfo(
        language=lang_name,
        highlight_key=hl_key,
        icon=icon,
        extension=ext,
    )


def get_supported_extensions() -> list[str]:
    """Return a sorted list of supported file extensions."""
    return sorted(_LANGUAGE_MAP.keys())


# ── Private Helpers ──────────────────────────────────────────────────────────


def _extract_extension(filename: str) -> str:
    """Return the lowercase file extension including the dot."""
    dot_idx: int = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()
