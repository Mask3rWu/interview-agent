"""
Mock LLM responses for when no real LLM is configured.
Returns canned but reasonable responses for each agent role.
"""
import random

MOCK_QUESTIONS = {
    "initial_question": [
        "你好！欢迎参加今天的模拟面试。首先请你简单介绍一下自己，以及你最有代表性的一个项目经历？",
        "我们开始吧。请先分享一下你的技术背景，你主要使用哪些技术栈？",
    ],
    "follow_up": [
        "你刚才提到的方案，能具体说说实现细节和取舍吗？",
        "你提到了性能优化，能详细展开一下你做了哪些优化吗？具体提升了多少？",
        "这个方案有什么局限性吗？如果重新设计你会怎么改？",
        "你提到了高并发处理，能说说你用的具体方案和它的原理吗？",
    ],
    "switch_topic": [
        "好的，我们换个话题。请结合目标岗位，说说你最有把握的一项核心能力？",
        "了解了。接下来我们聊聊系统设计吧。如果让你设计一个短链接系统，你会怎么考虑？",
        "那我们聊聊编程基础。能说说 Python 的 GIL 是什么，以及它如何影响并发？",
        "接下来谈一谈你简历里提到的微服务经验。服务之间是怎么通信的？",
    ],
}

MOCK_ASSESSMENT = {
    "total_score": 72,
    "tech_score": 70,
    "communication_score": 75,
    "highlights": ["表达清晰", "有实际项目经验"],
    "weaknesses": ["对底层原理理解不够深入", "部分回答缺少量化数据"],
    "suggested_review": [],
    "memory_updates": [],
}


def mock_interviewer_question(action: str, current_topic: str | None = None) -> str:
    """Generate a mock interviewer question based on action type."""
    if action == "initial_question":
        return random.choice(MOCK_QUESTIONS["initial_question"])
    elif action == "follow_up":
        return random.choice(MOCK_QUESTIONS["follow_up"])
    else:
        return random.choice(MOCK_QUESTIONS["switch_topic"])


def mock_router_decision(answer: str, follow_up_count: int, current_round: int, max_rounds: int) -> dict:
    """Mock the question router decision."""
    if current_round >= max_rounds:
        return {"action": "assess", "quality": "adequate", "next_topic": None, "reason": "达到最大轮次"}

    lower = answer.lower().strip()
    vague_keywords = ["不知道", "不清楚", "忘了", "没了解过", "不太懂", "不会", "不了解"]

    if any(kw in lower for kw in vague_keywords):
        return {"action": "switch_topic", "quality": "unknown", "next_topic": None, "reason": "用户表示不了解"}

    if follow_up_count >= 2:
        return {"action": "switch_topic", "quality": "adequate", "next_topic": None, "reason": f"已追问{follow_up_count}次"}

    if len(answer) < 20:
        return {"action": "follow_up", "quality": "vague", "next_topic": None, "reason": "回答过于简短"}

    return {"action": "follow_up", "quality": "adequate", "next_topic": None, "reason": "继续深入"}


def mock_assessment() -> dict:
    """Return a mock assessment result."""
    return MOCK_ASSESSMENT
