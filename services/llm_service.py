"""
llm_service.py — NVIDIA NIM API client with production-grade resilience.

Manages the OpenAI-compatible chat completion client targeting NVIDIA's
``integrate.api.nvidia.com`` endpoint.  Features:

* Safe secrets handling (``st.secrets`` → ``.env`` fallback)
* Granular ``httpx.Timeout`` (connect / read / write / pool)
* Tenacity retry with exponential back-off
* OpenAI client's internal retry disabled (``max_retries=0``)
* Response validation and structured error types
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx
import streamlit as st
from dotenv import load_dotenv
from openai import APIStatusError, APITimeoutError, OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ── Custom Exceptions ────────────────────────────────────────────────────────


class LLMServiceError(Exception):
    """Raised when the LLM service encounters a non-recoverable error."""


# ── Service Class ────────────────────────────────────────────────────────────


class LLMService:
    """
    Singleton-style LLM client for NVIDIA NIM.

    Instantiate via :func:`get_llm_service` to leverage Streamlit's
    ``@st.cache_resource`` for connection reuse across reruns.
    """

    def __init__(self) -> None:
        # ── API Key Resolution ───────────────────────────────────────────
        # Priority: st.secrets (Streamlit Cloud) → .env (local dev)
        api_key: str = _safe_secret("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY", "")

        if not api_key:
            raise LLMServiceError(
                "**NVIDIA_API_KEY** not found. "
                "Set it in `.env` (local) or Streamlit secrets (cloud)."
            )

        # ── Client Configuration ────────────────────────────────────────
        base_url: str = (
            _safe_secret("NVIDIA_BASE_URL")
            or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        )
        read_timeout: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "300"))

        self._client: OpenAI = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(
                connect=15.0,
                read=read_timeout,
                write=30.0,
                pool=10.0,
            ),
            # Disable the OpenAI client's own internal retry — tenacity
            # handles all retry logic so we avoid double-retry spam.
            max_retries=0,
        )

        self._model: str = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
        self._max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        self._temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))

        logger.info(
            "LLMService initialized — model=%s, max_tokens=%d, read_timeout=%.0fs",
            self._model,
            self._max_tokens,
            read_timeout,
        )

    # ── Public API ───────────────────────────────────────────────────────

    def analyze_code(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a chat completion request and return the raw response text.

        Parameters
        ----------
        system_prompt : str
            System-level instructions (role, schema, rules).
        user_prompt : str
            User-level prompt containing the code to analyze.

        Returns
        -------
        str
            Raw assistant response text.

        Raises
        ------
        LLMServiceError
            On API failure, empty response, or exhausted retries.
        """
        return self._chat(system_prompt, user_prompt)

    # ── Private Chat Method with Retry ───────────────────────────────────

    @retry(
        retry=retry_if_exception_type((
            APITimeoutError,
            APIStatusError,
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            httpx.RemoteProtocolError,
            ConnectionError,
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=5, max=30),
        reraise=True,
    )
    def _chat(self, system: str, user: str) -> str:
        """Execute chat completion against NVIDIA NIM with retry."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_p=0.7,
            )

            # ── Validate Response ────────────────────────────────────────
            if not response.choices:
                raise LLMServiceError("The model returned **no response**. Please try again.")

            content: str | None = response.choices[0].message.content

            if not content or not content.strip():
                raise LLMServiceError(
                    "The model returned an **empty response**. "
                    "This usually means the output was truncated — try a smaller file "
                    "or increase `LLM_MAX_TOKENS` in `.env`."
                )

            logger.info(
                "LLM response received — %d characters, finish_reason=%s",
                len(content),
                response.choices[0].finish_reason,
            )
            return content.strip()

        except APIStatusError as exc:
            status: int = exc.status_code
            if status == 404:
                raise LLMServiceError(
                    f"Model **'{self._model}'** not found. "
                    "Check `NVIDIA_MODEL` in `.env`. "
                    "Valid options: `meta/llama-3.3-70b-instruct`, `meta/llama-3.1-8b-instruct`."
                ) from exc
            if status == 401:
                raise LLMServiceError(
                    "**Invalid API key.** Check `NVIDIA_API_KEY` in `.env`."
                ) from exc
            if status == 429:
                logger.warning("Rate limited (429). Retrying via tenacity…")
                raise  # let tenacity retry
            # Other API errors — let tenacity retry on 5xx
            if 500 <= status < 600:
                logger.warning("Server error (%d). Retrying…", status)
                raise
            raise LLMServiceError(
                f"API error **{status}**: {exc.message}"
            ) from exc

        except (APITimeoutError, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
            logger.warning("Timeout during LLM call. Retrying…")
            raise  # tenacity will retry

        except LLMServiceError:
            raise  # don't wrap our own errors

        except Exception as exc:
            logger.exception("Unexpected LLM error")
            raise LLMServiceError(
                f"Unexpected error during analysis: **{type(exc).__name__}** — {exc}"
            ) from exc


# ── Module-Level Helpers ─────────────────────────────────────────────────────


def _safe_secret(key: str, default: str = "") -> str:
    """
    Safely read from ``st.secrets`` without crashing when no
    ``secrets.toml`` exists (common in local development).
    """
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


@st.cache_resource
def get_llm_service() -> LLMService:
    """
    Get or create the singleton :class:`LLMService` instance.

    Uses ``@st.cache_resource`` so the OpenAI client and connection
    pool are reused across Streamlit reruns.
    """
    return LLMService()
