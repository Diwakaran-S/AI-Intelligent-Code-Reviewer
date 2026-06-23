"""
analysis_tabs.py — 7-tab analysis results display.

Renders the analysis output across seven distinct tabs:
1. Overview  2. Bug Analysis  3. Security Review
4. Code Explanation  5. Optimization  6. Optimized Code  7. AI Report
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from components.report_download import render_report_downloads
from services.code_analyzer import LocalMetrics
from utils.markdown_parser import severity_badge


def render_analysis_tabs(
    analysis: dict[str, Any],
    local_metrics: LocalMetrics,
    language: str,
    highlight_key: str,
    filename: str,
) -> None:
    """Render all 7 analysis result tabs."""

    tabs = st.tabs([
        "📊 Overview",
        "🐛 Bug Analysis",
        "🔒 Security Review",
        "📖 Code Explanation",
        "⚡ Optimization",
        "✨ Optimized Code",
        "📄 AI Report",
    ])

    with tabs[0]:
        _render_overview(analysis, local_metrics)

    with tabs[1]:
        _render_bugs(analysis)

    with tabs[2]:
        _render_security(analysis)

    with tabs[3]:
        _render_explanation(analysis)

    with tabs[4]:
        _render_optimization(analysis)

    with tabs[5]:
        _render_optimized_code(analysis, highlight_key)

    with tabs[6]:
        _render_report(analysis, filename, language)


# ── Tab 1: Overview ──────────────────────────────────────────────────────────


def _render_overview(analysis: dict[str, Any], metrics: LocalMetrics) -> None:
    """Render the overview tab with summary and local metrics."""
    overview = analysis.get("overview", {})

    # Summary
    summary = overview.get("summary", "No summary available.")
    st.markdown(f"> {summary}")
    st.markdown("")

    # Score display
    score = overview.get("quality_score", 0)
    score_color = "#22c55e" if score >= 70 else ("#eab308" if score >= 40 else "#ef4444")

    # Render interactive charts using Plotly
    import plotly.graph_objects as go

    col1, col2 = st.columns(2)

    with col1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Quality Score", 'font': {'size': 16, 'color': "#f1f5f9", 'weight': 'bold'}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
                'bar': {'color': score_color},
                'bgcolor': "rgba(30, 41, 59, 0.3)",
                'borderwidth': 1,
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.05)'},
                    {'range': [40, 70], 'color': 'rgba(234, 179, 8, 0.05)'},
                    {'range': [70, 100], 'color': 'rgba(34, 197, 94, 0.05)'}
                ],
                'threshold': {
                    'line': {'color': "#ffffff", 'width': 3},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#f1f5f9", 'family': "Inter"},
            height=240,
            margin=dict(l=30, r=30, t=50, b=10)
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with col2:
        labels = ['Code Lines', 'Comment Lines', 'Blank Lines']
        values = [metrics.code_lines, metrics.comment_lines, metrics.blank_lines]
        colors = ['#7c3aed', '#10b981', '#4b5563']

        fig_donut = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.6,
            marker_colors=colors,
            textinfo='percent',
            hoverinfo='label+value',
            textfont_size=12,
        )])
        fig_donut.update_layout(
            title={'text': "Code Line Composition", 'font': {'size': 16, 'color': "#f1f5f9", 'weight': 'bold'}, 'x': 0.5, 'xanchor': 'center'},
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(color="#94a3b8")
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#f1f5f9", 'family': "Inter"},
            height=240,
            margin=dict(l=20, r=20, t=50, b=10)
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")

    # Local metrics
    st.markdown("#### 📏 Code Metrics (Local Analysis)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Lines", metrics.line_count)
    c2.metric("Code Lines", metrics.code_lines)
    c3.metric("Functions", metrics.function_count)
    c4.metric("Classes", metrics.class_count)

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Comment Lines", metrics.comment_lines)
    c6.metric("Comment Ratio", f"{metrics.comment_ratio}%")
    c7.metric("Avg Line Length", f"{metrics.avg_line_length}")
    c8.metric("Max Line Length", metrics.max_line_length)


# ── Tab 2: Bug Analysis ─────────────────────────────────────────────────────


def _render_bugs(analysis: dict[str, Any]) -> None:
    """Render the bug analysis tab."""
    bugs = analysis.get("bug_analysis", [])

    if not bugs:
        st.success("✅ No bugs detected! Your code looks clean.", icon="🎉")
        return

    # Count by severity
    critical = [b for b in bugs if b.get("severity", "").lower() == "critical"]
    major = [b for b in bugs if b.get("severity", "").lower() == "major"]
    minor = [b for b in bugs if b.get("severity", "").lower() == "minor"]

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Critical", len(critical))
    c2.metric("🟠 Major", len(major))
    c3.metric("🟢 Minor", len(minor))

    st.markdown("---")

    for bug in bugs:
        sev = bug.get("severity", "minor").lower()
        badge = severity_badge(sev)

        st.markdown(
            f"""
            <div class="issue-card">
                <div class="issue-title">
                    {badge} &nbsp; {_safe(bug.get('title', 'Untitled'))}
                </div>
                <div class="issue-desc">
                    <strong>📍 Lines:</strong> {_safe(bug.get('line_numbers', 'N/A'))}<br>
                    <strong>📝 Description:</strong> {_safe(bug.get('description', 'N/A'))}<br>
                    <strong>💥 Impact:</strong> {_safe(bug.get('impact', 'N/A'))}<br>
                    <strong>🔧 Fix:</strong> {_safe(bug.get('suggested_fix', 'N/A'))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Tab 3: Security Review ──────────────────────────────────────────────────


def _render_security(analysis: dict[str, Any]) -> None:
    """Render the security review tab."""
    issues = analysis.get("security_review", [])

    if not issues:
        st.success("✅ No security vulnerabilities detected!", icon="🛡️")
        return

    # Categories to check
    categories = [
        "hardcoded_secrets", "sql_injection", "xss",
        "unsafe_file_ops", "auth_issues", "data_exposure",
    ]
    cat_labels = {
        "hardcoded_secrets": "🔑 Hardcoded Secrets",
        "sql_injection": "💉 SQL Injection",
        "xss": "🌐 XSS Risks",
        "unsafe_file_ops": "📂 Unsafe File Ops",
        "auth_issues": "🔐 Auth Issues",
        "data_exposure": "📋 Data Exposure",
    }

    for issue in issues:
        sev = issue.get("severity", "low").lower()
        badge = severity_badge(sev)
        cat = issue.get("category", "other")
        cat_label = cat_labels.get(cat, f"⚠️ {cat.replace('_', ' ').title()}")

        st.markdown(
            f"""
            <div class="issue-card">
                <div class="issue-title">
                    {badge} &nbsp; {_safe(issue.get('title', 'Untitled'))}
                </div>
                <div class="issue-desc">
                    <strong>📂 Category:</strong> {cat_label}<br>
                    <strong>📝 Description:</strong> {_safe(issue.get('description', 'N/A'))}<br>
                    <strong>✅ Recommendation:</strong> {_safe(issue.get('recommendation', 'N/A'))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Tab 4: Code Explanation ─────────────────────────────────────────────────


def _render_explanation(analysis: dict[str, Any]) -> None:
    """Render the code explanation tab."""
    explanation = analysis.get("explanation", {})

    # High-level summary
    st.markdown("#### 🎯 High-Level Summary")
    st.info(explanation.get("high_level_summary", "No summary available."), icon="💡")

    # Function breakdown
    functions = explanation.get("functions", [])
    if functions:
        st.markdown("---")
        st.markdown("#### 🔍 Function-by-Function Breakdown")

        for func in functions:
            with st.expander(f"⚙️ `{func.get('name', 'unknown')}`", expanded=False):
                st.markdown(f"**Purpose:** {func.get('purpose', 'N/A')}")
                st.markdown(f"**Logic:** {func.get('logic', 'N/A')}")

    # Workflow
    workflow = explanation.get("workflow", "")
    if workflow:
        st.markdown("---")
        st.markdown("#### 🔄 Workflow & Control Flow")
        st.markdown(workflow)


# ── Tab 5: Optimization ─────────────────────────────────────────────────────


def _render_optimization(analysis: dict[str, Any]) -> None:
    """Render the optimization suggestions tab."""
    opts = analysis.get("optimization", [])

    if not opts:
        st.success("✅ No optimization suggestions — your code is well-written!", icon="⚡")
        return

    # Group by category
    cat_icons = {
        "performance": "🚀",
        "readability": "👓",
        "refactoring": "🔄",
        "scalability": "📈",
    }

    for opt in opts:
        cat = opt.get("category", "general").lower()
        icon = cat_icons.get(cat, "💡")

        st.markdown(
            f"""
            <div class="issue-card">
                <div class="issue-title">
                    {icon} [{cat.upper()}] {_safe(opt.get('title', 'Untitled'))}
                </div>
                <div class="issue-desc">
                    {_safe(opt.get('description', 'N/A'))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        before = opt.get("before", "")
        after = opt.get("after", "")

        if before or after:
            c1, c2 = st.columns(2)
            if before:
                with c1:
                    st.markdown("**Before:**")
                    st.code(before, language="text")
            if after:
                with c2:
                    st.markdown("**After:**")
                    st.code(after, language="text")


# ── Tab 6: Optimized Code ───────────────────────────────────────────────────


def _render_optimized_code(analysis: dict[str, Any], highlight_key: str) -> None:
    """Render the optimized code tab."""
    code = analysis.get("optimized_code", "")

    if not code or not code.strip():
        st.info(
            "💡 No optimized code was generated. This can happen when:\n"
            "- The model's response was truncated due to token limits\n"
            "- The original code is already well-optimized\n\n"
            "Check the **Optimization** tab for specific improvement suggestions.",
            icon="ℹ️",
        )
        return

    st.markdown("#### ✨ Refactored & Optimized Code")
    st.caption("Review the improved version below. Use the copy button to grab the code.")

    st.code(code, language=highlight_key, line_numbers=True)


# ── Tab 7: AI Report ────────────────────────────────────────────────────────


def _render_report(analysis: dict[str, Any], filename: str, language: str) -> None:
    """Render the AI report tab with download buttons."""
    from services.report_generator import generate_markdown_report

    st.markdown("#### 📋 AI-Generated Review Report")
    st.caption("A comprehensive summary of all findings, ready to share with your team.")

    # Download buttons
    render_report_downloads(analysis, filename, language)

    st.markdown("---")

    # Show the report inline
    md_report = generate_markdown_report(analysis, filename, language)
    st.markdown(md_report)


# ── Utility ──────────────────────────────────────────────────────────────────


def _safe(text: str) -> str:
    """Basic HTML-safe text for rendering in markdown HTML blocks."""
    import html
    return html.escape(str(text))
