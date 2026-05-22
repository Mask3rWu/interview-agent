"""
Question router node: decides next action based on user's latest answer.
Uses structured LLM output when available, otherwise falls back to rule-based mock.
"""
from app.agents.state import InterviewState
from app.schemas.llm_outputs import RouterDecision
from app.services.model_router import (
    get_llm,
    is_llm_available,
    log_llm_failure,
    log_llm_success,
    now_ms,
)
from app.services.mock_llm import mock_router_decision
from langchain_core.messages import HumanMessage, SystemMessage


async def question_router_node(state: InterviewState) -> dict:
    # If first run (no user messages yet), stay with initial_question
    user_messages = [m for m in state.get("messages", []) if isinstance(m, HumanMessage)]
    if not user_messages:
        return {"action": state.get("action", "initial_question")}

    latest_answer = user_messages[-1].content
    follow_up_count = state.get("follow_up_count", 0)
    unclear_count = state.get("unclear_count", 0)
    current_round = state.get("current_round", 0)
    max_rounds = state.get("max_rounds", 8)

    if is_llm_available():
        llm = get_llm("question_router")
        if llm:
            started_ms = now_ms()
            try:
                structured_llm = llm.with_structured_output(RouterDecision)
                decision = await structured_llm.ainvoke([
                    SystemMessage(content=(
                        "你是面试路由器。根据用户最新回答，决定下一步动作。\n"
                        f"当前轮次: {current_round}/{max_rounds}, 追问次数: {follow_up_count}\n"
                        "规则: 回答含糊→follow_up, 回答充分→switch_topic, 达到最大轮次→assess\n"
                        "用户连续说不知道→switch_topic, follow_up_count>=3→switch_topic"
                    )),
                    HumanMessage(content=latest_answer),
                ])
                if not decision:
                    raise ValueError("empty structured response")
                log_llm_success("question_router", started_ms)
                return _apply_decision(decision, follow_up_count, unclear_count, current_round, max_rounds)
            except Exception as exc:
                log_llm_failure("question_router", exc, started_ms)

    # Mock decision
    decision = mock_router_decision(latest_answer, follow_up_count, current_round, max_rounds)
    return _apply_decision(decision, follow_up_count, unclear_count, current_round, max_rounds)


def _apply_decision(decision, follow_up_count: int, unclear_count: int,
                    current_round: int, max_rounds: int) -> dict:
    action = decision if isinstance(decision, dict) else decision.model_dump()

    # Force assess if max rounds reached
    if current_round >= max_rounds:
        return {
            "action": "assess",
            "follow_up_count": follow_up_count,
            "unclear_count": unclear_count,
        }

    result = {"action": action["action"]}

    if action["action"] == "follow_up":
        result["follow_up_count"] = follow_up_count + 1
        result["unclear_count"] = unclear_count
    elif action["action"] == "switch_topic":
        result["follow_up_count"] = 0
        result["unclear_count"] = unclear_count
    else:
        result["follow_up_count"] = follow_up_count
        result["unclear_count"] = unclear_count

    if action["action"] == "switch_topic" and action.get("next_topic"):
        result["current_topic"] = action["next_topic"]

    if action.get("quality") in ("unknown", "wrong"):
        result["unclear_count"] = unclear_count + 1

    return result
