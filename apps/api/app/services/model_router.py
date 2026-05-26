"""
Model router: selects the appropriate LLM client per agent name.
When no API key is configured, falls back to mock responses.
"""
import logging
import time

from app.core.config import (
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_API_KEY,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    RESUME_ANALYZER_MODEL,
    JOB_ANALYZER_MODEL,
    QUESTION_ROUTER_MODEL,
    INTERVIEWER_MODEL,
    ASSESSMENT_MODEL,
)

console_logger = logging.getLogger("model_calls.console")
file_logger = logging.getLogger("model_calls.file")

AGENT_MODEL_MAP = {
    "resume_analyzer": RESUME_ANALYZER_MODEL,
    "job_analyzer": JOB_ANALYZER_MODEL,
    "question_router": QUESTION_ROUTER_MODEL,
    "interviewer": INTERVIEWER_MODEL,
    "assessment": ASSESSMENT_MODEL,
}


def now_ms() -> float:
    return time.perf_counter() * 1000


def get_model_name(agent: str) -> str:
    """Return the model name for a given agent, falling back to default."""
    return AGENT_MODEL_MAP.get(agent, "") or DEFAULT_LLM_MODEL


def is_llm_available() -> bool:
    return bool(DEFAULT_LLM_API_KEY and DEFAULT_LLM_BASE_URL.strip() and DEFAULT_LLM_MODEL)


def get_llm(agent: str):
    """
    Return a LangChain chat model for the given agent.
    When no LLM is configured, returns None (callers should use mock).
    """
    if not is_llm_available():
        return None

    from langchain_openai import ChatOpenAI

    model = get_model_name(agent)
    return ChatOpenAI(
        base_url=DEFAULT_LLM_BASE_URL.strip(),
        api_key=DEFAULT_LLM_API_KEY,
        model=model,
        temperature=0.7,
        streaming=True,
        timeout=DEFAULT_LLM_TIMEOUT_SECONDS,
    )


def log_llm_success(agent: str, started_ms: float | None = None) -> None:
    model = get_model_name(agent)
    elapsed = _elapsed_text(started_ms)
    console_logger.info("agent=%s model=%s status=success%s", agent, model, elapsed)
    file_logger.info(
        "agent=%s model=%s status=success base_url=%s%s",
        agent,
        model,
        DEFAULT_LLM_BASE_URL,
        elapsed,
    )


def log_llm_failure(agent: str, exc: Exception, started_ms: float | None = None) -> None:
    model = get_model_name(agent)
    elapsed = _elapsed_text(started_ms)
    reason = f"{type(exc).__name__}: {exc}"
    console_logger.info(
        "agent=%s model=%s status=failure reason=%s%s",
        agent,
        model,
        _compact_reason(reason),
        elapsed,
    )
    file_logger.exception(
        "agent=%s model=%s status=failure base_url=%s reason=%s%s",
        agent,
        model,
        DEFAULT_LLM_BASE_URL,
        reason,
        elapsed,
    )


def _elapsed_text(started_ms: float | None) -> str:
    if started_ms is None:
        return ""
    return f" elapsed_ms={int(now_ms() - started_ms)}"


def _compact_reason(reason: str, limit: int = 240) -> str:
    reason = " ".join(reason.split())
    if len(reason) <= limit:
        return reason
    return reason[: limit - 3] + "..."
