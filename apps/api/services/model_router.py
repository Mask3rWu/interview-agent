"""
Model router: selects the appropriate LLM client per agent name.
When no API key is configured, falls back to mock responses.
"""
import logging
import time

from api.core.config import (
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_API_KEY,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    MLLM_BASE_URL,
    MLLM_API_KEY,
    MLLM_MODEL,
    MLLM_TIMEOUT_SECONDS,
    RESUME_ANALYZER_MODEL,
    JOB_ANALYZER_MODEL,
    QUESTION_ROUTER_MODEL,
    INTERVIEWER_MODEL,
    ASSESSMENT_MODEL,
    RESUME_ANALYZER_LLM_BACKEND,
    JOB_ANALYZER_LLM_BACKEND,
    QUESTION_ROUTER_LLM_BACKEND,
    INTERVIEWER_LLM_BACKEND,
    ASSESSMENT_LLM_BACKEND,
    PDF_VISION_AGENT_MODEL,
)

console_logger = logging.getLogger("model_calls.console")
file_logger = logging.getLogger("model_calls.file")

AGENT_MODEL_MAP = {
    "resume_analyzer": RESUME_ANALYZER_MODEL,
    "job_analyzer": JOB_ANALYZER_MODEL,
    "question_router": QUESTION_ROUTER_MODEL,
    "interviewer": INTERVIEWER_MODEL,
    "assessment": ASSESSMENT_MODEL,
    "pdf_vision": PDF_VISION_AGENT_MODEL,
}

AGENT_CAPABILITIES = {
    "resume_analyzer": {"multimodal": False},
    "job_analyzer": {"multimodal": False},
    "question_router": {"multimodal": False},
    "interviewer": {"multimodal": False},
    "assessment": {"multimodal": False},
    "pdf_vision": {"multimodal": True},
}

AGENT_BACKEND_MAP = {
    "resume_analyzer": RESUME_ANALYZER_LLM_BACKEND,
    "job_analyzer": JOB_ANALYZER_LLM_BACKEND,
    "question_router": QUESTION_ROUTER_LLM_BACKEND,
    "interviewer": INTERVIEWER_LLM_BACKEND,
    "assessment": ASSESSMENT_LLM_BACKEND,
    "pdf_vision": "mllm",
}


def now_ms() -> float:
    return time.perf_counter() * 1000


def get_model_name(agent: str) -> str:
    """Return the model name for a given agent, falling back to default."""
    if _uses_mllm_backend(agent):
        return AGENT_MODEL_MAP.get(agent, "") or MLLM_MODEL
    return AGENT_MODEL_MAP.get(agent, "") or DEFAULT_LLM_MODEL


def requires_multimodal(agent: str) -> bool:
    return bool(AGENT_CAPABILITIES.get(agent, {}).get("multimodal"))


def get_model_config(agent: str) -> dict:
    if _uses_mllm_backend(agent):
        return {
            "base_url": MLLM_BASE_URL.strip(),
            "api_key": MLLM_API_KEY,
            "model": get_model_name(agent),
            "timeout": MLLM_TIMEOUT_SECONDS,
        }
    return {
        "base_url": DEFAULT_LLM_BASE_URL.strip(),
        "api_key": DEFAULT_LLM_API_KEY,
        "model": get_model_name(agent),
        "timeout": DEFAULT_LLM_TIMEOUT_SECONDS,
    }


def _uses_mllm_backend(agent: str) -> bool:
    return AGENT_BACKEND_MAP.get(agent, "text").lower() in {"mllm", "multimodal", "vision"}


def is_llm_available() -> bool:
    return bool(DEFAULT_LLM_API_KEY and DEFAULT_LLM_BASE_URL.strip() and DEFAULT_LLM_MODEL)


def is_agent_llm_available(agent: str) -> bool:
    config = get_model_config(agent)
    return bool(config["api_key"] and config["base_url"] and config["model"])


def get_llm(agent: str):
    """
    Return a LangChain chat model for the given agent.
    When no LLM is configured, returns None (callers should use mock).
    """
    if not is_agent_llm_available(agent):
        return None

    from langchain_openai import ChatOpenAI

    config = get_model_config(agent)
    return ChatOpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"],
        model=config["model"],
        temperature=0.7,
        streaming=True,
        timeout=config["timeout"],
    )


def log_llm_success(agent: str, started_ms: float | None = None) -> None:
    model = get_model_name(agent)
    config = get_model_config(agent)
    elapsed = _elapsed_text(started_ms)
    console_logger.info("agent=%s model=%s status=success%s", agent, model, elapsed)
    file_logger.info(
        "agent=%s model=%s status=success base_url=%s%s",
        agent,
        model,
        config["base_url"],
        elapsed,
    )


def log_llm_failure(agent: str, exc: Exception, started_ms: float | None = None) -> None:
    model = get_model_name(agent)
    config = get_model_config(agent)
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
        config["base_url"],
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
