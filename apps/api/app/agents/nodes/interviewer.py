"""
Interviewer node: generates the next interviewer question.
Uses RAG context (mock keyword search for now) and current topic.
"""
from app.agents.state import InterviewState
from app.services.mock_llm import mock_interviewer_question
from app.services.model_router import (
    get_llm,
    is_llm_available,
    log_llm_failure,
    log_llm_success,
    now_ms,
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

TOPIC_POOL = [
    "技术栈与项目经验",
    "系统设计",
    "数据库与存储",
    "编程基础与算法",
    "架构与设计模式",
    "团队协作与流程",
]


async def interviewer_node(state: InterviewState) -> dict:
    action = state.get("action", "initial_question")
    current_topic = state.get("current_topic", "")
    messages = list(state.get("messages", []))
    weakness_memory = state.get("weakness_memory", [])

    # Simple keyword retrieval from materials (placeholder for RAG)
    context = _keyword_retrieve(current_topic, state)

    # Try real LLM first
    if is_llm_available():
        llm = get_llm("interviewer")
        if llm:
            started_ms = now_ms()
            try:
                question_text = await _generate_with_llm(
                    llm,
                    action,
                    current_topic,
                    context,
                    messages,
                    weakness_memory,
                )
                if not question_text:
                    raise ValueError("empty response content")
                log_llm_success("interviewer", started_ms)
                return {
                    "messages": [AIMessage(content=question_text)],
                    "current_round": state.get("current_round", 0) + 1,
                }
            except Exception as exc:
                log_llm_failure("interviewer", exc, started_ms)

    # Mock fallback
    question_text = mock_interviewer_question(action, current_topic)
    return {
        "messages": [AIMessage(content=question_text)],
        "current_round": state.get("current_round", 0) + 1,
    }


async def _generate_with_llm(
    llm,
    action: str,
    topic: str,
    context: str,
    messages: list,
    weakness_memory: list[dict],
) -> str | None:
    system_prompt = _build_system_prompt(action, topic, context, weakness_memory)
    prompt_messages = [SystemMessage(content=system_prompt)]
    # Include last few messages for context
    for m in messages[-6:]:
        prompt_messages.append(m)

    response = await llm.ainvoke(prompt_messages)
    return response.content if response else None


def _build_system_prompt(action: str, topic: str, context: str, weakness_memory: list[dict]) -> str:
    base = "你是一位专业的面试官。请根据以下信息生成面试问题。用中文提问，保持自然、专业。"
    if action == "initial_question":
        base += f"\n这是一场面试的开场。请结合以下主题提问: {topic}"
    elif action == "follow_up":
        base += f"\n请针对候选人上一轮的回答进行深入追问。当前话题: {topic}"
    elif action == "switch_topic":
        base += f"\n请平滑切换到新话题并提问。新话题: {topic}"
    if context:
        base += f"\n\n参考资料:\n{context}"
    if weakness_memory:
        base += "\n\n历史薄弱点画像:\n"
        for memory in weakness_memory[:5]:
            base += (
                f"- {memory.get('topic', '')}: 掌握度 {memory.get('mastery_score', 0):.2f}, "
                f"薄弱次数 {memory.get('weakness_count', 0)}\n"
            )
        base += "请优先围绕目标岗位相关且历史掌握度较低的话题提问，避免生硬重复。"
    base += "\n\n只输出问题本身，不要加任何说明文字。"
    return base


def _keyword_retrieve(topic: str, state: InterviewState) -> str:
    """Simple keyword-based retrieval. Replaced by pgvector in Step 5."""
    material_ids = state.get("selected_material_ids", [])
    if not material_ids:
        return ""

    from app.core import json_store

    chunks = []
    for mid in material_ids:
        m = json_store.get("materials", mid)
        if m is None:
            continue
        raw = m.get("raw_text", "")
        # Very naive keyword match
        keywords = topic.lower().split()
        for kw in keywords:
            if len(kw) >= 2 and kw in raw.lower():
                # Return a snippet around the keyword
                idx = raw.lower().find(kw)
                start = max(0, idx - 100)
                end = min(len(raw), idx + 300)
                chunk = raw[start:end]
                if chunk:
                    chunks.append(chunk)
                break

    if chunks:
        return "\n---\n".join(chunks[:2])
    return ""
