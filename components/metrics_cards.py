"""
metrics_cards.py — Animated glassmorphism metric cards.

Renders the top-level overview metrics as styled HTML cards
with icons, color-coding, and hover animations.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_metrics_cards(analysis: dict[str, Any]) -> None:
    """
    Render the 5 overview metric cards in a responsive row.

    Parameters
    ----------
    analysis : dict
        The parsed analysis JSON containing an ``"overview"`` key.
    """
    overview: dict[str, Any] = analysis.get("overview", {})

    score: int = overview.get("quality_score", 0)
    complexity: str = str(overview.get("complexity", "N/A")).title()
    total_bugs: int = overview.get("total_bugs", 0)
    security: str = str(overview.get("security_risk", "N/A")).title()
    maintainability: str = str(overview.get("maintainability", "N/A"))

    # Determine score classes
    score_class = "score-high" if score >= 70 else ("score-mid" if score >= 40 else "score-low")
    bug_class = "score-high" if total_bugs == 0 else ("score-mid" if total_bugs <= 3 else "score-low")
    sec_class = _risk_class(security)
    maint_class = _grade_class(maintainability)
    complex_class = _risk_class(complexity)

    cols = st.columns(5)

    cards = [
        (cols[0], "📊", str(score) + "/100", "Quality Score", score_class),
        (cols[1], "🧩", complexity, "Complexity", complex_class),
        (cols[2], "🐛", str(total_bugs), "Bugs Found", bug_class),
        (cols[3], "🛡️", security, "Security Risk", sec_class),
        (cols[4], "📐", maintainability, "Maintainability", maint_class),
    ]

    for col, icon, value, label, css_class in cards:
        with col:
            st.markdown(
                f"""
                <div class="metric-card {css_class}">
                    <span class="metric-icon">{icon}</span>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _risk_class(level: str) -> str:
    """Map a risk/complexity level to a CSS class."""
    level_lower = level.lower()
    if level_lower in ("low",):
        return "score-high"
    if level_lower in ("medium",):
        return "score-mid"
    return "score-low"


def _grade_class(grade: str) -> str:
    """Map a maintainability grade to a CSS class."""
    if grade in ("A", "B"):
        return "score-high"
    if grade in ("C",):
        return "score-mid"
    return "score-low"
