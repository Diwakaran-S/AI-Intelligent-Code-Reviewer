"""
markdown_parser.py — Safe Markdown rendering and sanitization helpers.

Provides utilities for rendering code blocks, sanitizing HTML output,
and formatting analysis results for display.
"""

from __future__ import annotations

import html
import re
from typing import Optional


def render_code_block(code: str, language: str = "text") -> str:
    """
    Wrap *code* in a Markdown fenced code block.

    Parameters
    ----------
    code : str
        Raw source code to render.
    language : str
        Syntax-highlight language key (e.g. ``"python"``).

    Returns
    -------
    str
        Markdown-formatted code block.
    """
    safe_code: str = code.rstrip("\n")
    return f"```{language}\n{safe_code}\n```"


def sanitize_html(text: str) -> str:
    """
    Escape HTML entities in *text* to prevent XSS injection.

    Parameters
    ----------
    text : str
        Raw text that may contain HTML.

    Returns
    -------
    str
        Escaped, safe text.
    """
    return html.escape(text, quote=True)


def severity_badge(severity: str) -> str:
    """
    Return a colored Markdown badge for a severity level.

    Parameters
    ----------
    severity : str
        One of ``"critical"``, ``"high"``, ``"major"``, ``"medium"``,
        ``"minor"``, ``"low"``.

    Returns
    -------
    str
        HTML span styled with the appropriate color.
    """
    colors: dict[str, str] = {
        "critical": "#ef4444",
        "high":     "#f97316",
        "major":    "#f97316",
        "medium":   "#eab308",
        "minor":    "#22c55e",
        "low":      "#22c55e",
    }
    color: str = colors.get(severity.lower(), "#94a3b8")
    label: str = severity.upper()
    return (
        f'<span style="background:{color}; color:#fff; padding:2px 10px; '
        f'border-radius:12px; font-size:0.75rem; font-weight:600; '
        f'letter-spacing:0.5px;">{label}</span>'
    )


def truncate_text(text: str, max_length: int = 300) -> str:
    """
    Truncate *text* to *max_length* characters, appending an ellipsis.

    Parameters
    ----------
    text : str
        Text to truncate.
    max_length : int
        Maximum character count.

    Returns
    -------
    str
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def format_score_color(score: int) -> str:
    """
    Return a hex color code based on a 0–100 quality score.

    Parameters
    ----------
    score : int
        Quality score (0–100).

    Returns
    -------
    str
        Hex color string.
    """
    if score >= 80:
        return "#22c55e"   # green
    if score >= 60:
        return "#eab308"   # yellow
    if score >= 40:
        return "#f97316"   # orange
    return "#ef4444"       # red


def strip_markdown_fences(text: str) -> str:
    """
    Remove Markdown code fences (````...```) from the outside of *text*.

    Useful for cleaning LLM output that wraps JSON in code blocks.

    Parameters
    ----------
    text : str
        Text potentially wrapped in code fences.

    Returns
    -------
    str
        Text with outer fences stripped.
    """
    cleaned: str = text.strip()
    # Remove opening fence  ```json  or  ```
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    # Remove closing fence
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return cleaned.strip()
