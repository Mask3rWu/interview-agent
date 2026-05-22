"""
Assessment node: generates interview evaluation report and memory updates.
"""
import json
import re

from app.agents.state import InterviewState
from app.schemas.llm_outputs import AssessmentResult
from app.services.model_router import (
    get_llm,
    is_llm_available,
    log_llm_failure,
    log_llm_success,
    now_ms,
)
from langchain_core.messages import SystemMessage, HumanMessage


async def assessment_node(state: InterviewState) -> dict:
    messages = state.get("messages", [])
    conversation = _build_conversation(messages)

    if is_llm_available():
        llm = get_llm("assessment")
        if llm:
            started_ms = now_ms()
            try:
                result = await evaluate_conversation(llm, conversation)
                if not result:
                    raise ValueError("empty structured response")
                log_llm_success("assessment", started_ms)
                return {
                    "assessment": result,
                    "assessment_status": "success",
                    "assessment_error": "",
                    "memory_updates": result.get("memory_updates", []),
                }
            except Exception as exc:
                log_llm_failure("assessment", exc, started_ms)
                return {
                    "assessment": None,
                    "assessment_status": "failed",
                    "assessment_error": f"{type(exc).__name__}: {exc}",
                    "memory_updates": [],
                }

    return {
        "assessment": None,
        "assessment_status": "failed",
        "assessment_error": "LLM is not configured",
        "memory_updates": [],
    }


async def evaluate_conversation(llm, conversation: str) -> dict:
    try:
        structured_llm = llm.with_structured_output(AssessmentResult)
        assessment = await structured_llm.ainvoke([
            SystemMessage(content=(
                "你是面试评估专家。请根据以下面试对话，给出结构化评估报告。\n"
                "包括: 总评分(0-100)、技术评分、沟通评分、亮点、薄弱项、建议复习知识点、\n"
                "以及每个相关知识点的 memory_updates (topic, category, performance, evidence)。"
            )),
            HumanMessage(content=conversation),
        ])
        return assessment.model_dump() if hasattr(assessment, 'model_dump') else assessment
    except Exception:
        return await _assess_with_json_prompt(llm, conversation)


def _build_conversation(messages: list) -> str:
    return "\n".join([
        f"{'面试官' if m.type == 'ai' else '候选人'}: {m.content}"
        for m in messages
    ])


async def _assess_with_json_prompt(llm, conversation: str) -> dict:
    prompt = _json_prompt(conversation)
    try:
        response = await _invoke_json_llm(llm, prompt)
        content = response.content if response else ""
        parsed = _parse_json_object(content)
        return AssessmentResult.model_validate(parsed).model_dump()
    except Exception:
        repair_response = await _repair_json_llm(llm, content if 'content' in locals() else "", conversation)
        repair_content = repair_response.content if repair_response else ""
        parsed = _parse_json_object(repair_content)
        return AssessmentResult.model_validate(parsed).model_dump()


async def _invoke_json_llm(llm, prompt: list) -> object:
    json_llm = llm.bind(response_format={"type": "json_object"})
    return await json_llm.ainvoke(prompt)


async def _repair_json_llm(llm, raw_content: str, conversation: str):
    repair_prompt = [
        SystemMessage(content=(
            "你是一个JSON修复器。把下面的内容整理成严格合法的 JSON 对象，只输出 JSON，不要输出任何额外文字。"
        )),
        HumanMessage(content=(
            f"原始面试内容:\n{conversation}\n\n"
            f"原始模型输出:\n{raw_content}\n\n"
            "请输出符合以下字段的 JSON：total_score, tech_score, communication_score, highlights, weaknesses, suggested_review, memory_updates."
        )),
    ]
    return await _invoke_json_llm(llm, repair_prompt)


def _json_prompt(conversation: str) -> list:
    return [
        SystemMessage(content=(
            "你是面试评估专家。必须只输出一个合法 JSON 对象，不要输出 Markdown、解释或代码块。\n"
            "JSON schema:\n"
            "{\n"
            '  "total_score": 0-100的整数,\n'
            '  "tech_score": 0-100的整数,\n'
            '  "communication_score": 0-100的整数,\n'
            '  "highlights": ["字符串"],\n'
            '  "weaknesses": ["字符串"],\n'
            '  "suggested_review": ["字符串"],\n'
            '  "memory_updates": [\n'
            "    {\n"
            '      "topic": "被考察的具体知识点",\n'
            '      "category": "分类",\n'
            '      "performance": "excellent|adequate|vague|wrong|unknown",\n'
            '      "evidence": "来自本场对话的简短依据"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "只允许基于对话中实际出现或明确考察的内容生成 memory_updates。"
        )),
        HumanMessage(content=conversation),
    ]


def _parse_json_object(content: str) -> dict:
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)
