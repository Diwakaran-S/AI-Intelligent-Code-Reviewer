"""
code_analyzer.py — Analysis orchestration with robust JSON parsing.

Coordinates the LLM call, parses the structured JSON response with
multiple fallback strategies, validates the schema, and computes
local code metrics.  No session-state caching — every click
triggers a fresh analysis.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from prompts.review_prompt import SYSTEM_PROMPT, build_user_prompt
from services.llm_service import LLMServiceError, get_llm_service

logger = logging.getLogger(__name__)


@dataclass
class LocalMetrics:
    """Metrics computed locally without LLM."""
    line_count: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    code_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    avg_line_length: float = 0.0
    max_line_length: int = 0
    comment_ratio: float = 0.0


@dataclass
class AnalysisResult:
    """Complete analysis output."""
    success: bool
    analysis: dict[str, Any] = field(default_factory=dict)
    local_metrics: LocalMetrics = field(default_factory=LocalMetrics)
    error_message: Optional[str] = None
    raw_response: Optional[str] = None


_FALLBACK: dict[str, Any] = {
    "overview": {
        "quality_score": 0, "complexity": "unknown", "total_bugs": 0,
        "security_risk": "unknown", "maintainability": "N/A",
        "summary": "Analysis could not be completed.",
    },
    "bug_analysis": [],
    "security_review": [],
    "explanation": {
        "high_level_summary": "Analysis could not be completed.",
        "functions": [], "workflow": "",
    },
    "optimization": [],
    "optimized_code": "",
}


def analyze(code: str, language: str, filename: str, line_count: int) -> AnalysisResult:
    """Run a full AI-powered code analysis (always fresh, never cached)."""
    local_metrics = compute_local_metrics(code, language)
    try:
        llm = get_llm_service()
        user_prompt = build_user_prompt(code, language, filename, line_count)
        raw_response = llm.analyze_code(SYSTEM_PROMPT, user_prompt)
        parsed = _parse_json_response(raw_response)
        validated = _validate_schema(parsed)
        return AnalysisResult(
            success=True, analysis=validated,
            local_metrics=local_metrics, raw_response=raw_response,
        )
    except LLMServiceError as exc:
        logger.error("LLM analysis failed: %s", exc)
        return AnalysisResult(
            success=False, analysis=_FALLBACK.copy(),
            local_metrics=local_metrics, error_message=str(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected analysis error")
        return AnalysisResult(
            success=False, analysis=_FALLBACK.copy(),
            local_metrics=local_metrics,
            error_message=f"Unexpected error: {type(exc).__name__} — {exc}",
        )


def compute_local_metrics(code: str, language: str) -> LocalMetrics:
    """Compute code metrics locally (no LLM needed)."""
    lines = code.splitlines()
    total = len(lines)
    if total == 0:
        return LocalMetrics()
    comment_pfx = {"Python": "#", "JavaScript": "//", "TypeScript": "//",
                    "Java": "//", "C": "//", "C++": "//"}.get(language, "#")
    blank = comments = 0
    lengths: list[int] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith(comment_pfx):
            comments += 1
        lengths.append(len(line))
    code_lines = total - blank - comments
    func_pats = {
        "Python": r"^\s*def\s+\w+", "JavaScript": r"function\s+\w+",
        "TypeScript": r"function\s+\w+", "Java": r"(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+\w+\s*\(",
        "C": r"^\w[\w\s\*]+\s+\w+\s*\(", "C++": r"^\w[\w\s\*:]+\s+\w+\s*\(",
    }
    class_pats = {
        "Python": r"^\s*class\s+\w+", "JavaScript": r"class\s+\w+",
        "TypeScript": r"class\s+\w+", "Java": r"class\s+\w+", "C++": r"class\s+\w+",
    }
    func_count = len(re.findall(func_pats.get(language, r"function\s+\w+"), code, re.MULTILINE))
    class_count = len(re.findall(class_pats.get(language, r"class\s+\w+"), code, re.MULTILINE))
    return LocalMetrics(
        line_count=total, blank_lines=blank, comment_lines=comments,
        code_lines=code_lines, function_count=func_count, class_count=class_count,
        avg_line_length=round(sum(lengths) / total, 1) if total else 0.0,
        max_line_length=max(lengths) if lengths else 0,
        comment_ratio=round(comments / max(code_lines, 1) * 100, 1),
    )


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Parse LLM response to dict with 4 fallback strategies."""
    text = raw.strip()
    # Strategy 1: Direct
    try:
        r = json.loads(text, strict=False)
        if isinstance(r, dict):
            return r
    except json.JSONDecodeError:
        pass
    # Strategy 2: Strip code fences
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text)
    stripped = re.sub(r"\n?```\s*$", "", stripped).strip()
    try:
        r = json.loads(stripped, strict=False)
        if isinstance(r, dict):
            return r
    except json.JSONDecodeError:
        pass
    # Strategy 3: Regex outermost { ... }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            r = json.loads(match.group(), strict=False)
            if isinstance(r, dict):
                return r
        except json.JSONDecodeError:
            pass
    # Strategy 4: Fix trailing commas
    try:
        fixed = re.sub(r",\s*([}\]])", r"\1", stripped)
        r = json.loads(fixed, strict=False)
        if isinstance(r, dict):
            return r
    except json.JSONDecodeError:
        pass
    logger.error("All JSON parsing strategies failed. Length: %d", len(raw))
    try:
        with open("latest_failed_response.txt", "w", encoding="utf-8") as f:
            f.write(raw)
        logger.info("Saved latest failed raw response to latest_failed_response.txt")
    except Exception as e:
        logger.error("Failed to write latest_failed_response.txt: %s", e)
        
    fb = _FALLBACK.copy()
    fb["overview"] = {**fb["overview"], "summary": "AI response could not be parsed as JSON. Please retry."}
    return fb


def _validate_schema(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure all required keys exist with proper types."""
    for key, default in _FALLBACK.items():
        if key not in data:
            data[key] = default
        elif isinstance(default, dict) and isinstance(data[key], dict):
            for sk, sv in default.items():
                if sk not in data[key]:
                    data[key][sk] = sv
    ov = data.get("overview", {})
    if isinstance(ov.get("quality_score"), (int, float)):
        ov["quality_score"] = max(0, min(100, int(ov["quality_score"])))
    return data
