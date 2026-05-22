* 直接结束，调用总结agent

* ![image-20260521212824427](C:\Users\Wu\AppData\Roaming\Typora\typora-user-images\image-20260521212824427.png)

* ![image-20260521213438275](C:\Users\Wu\AppData\Roaming\Typora\typora-user-images\image-20260521213438275.png)

* ![image-20260521213654417](C:\Users\Wu\AppData\Roaming\Typora\typora-user-images\image-20260521213654417.png)

* ![image-20260521213854243](C:\Users\Wu\AppData\Roaming\Typora\typora-user-images\image-20260521213854243.png)

  > with_structrued_output

* ![image-20260521214211132](C:\Users\Wu\AppData\Roaming\Typora\typora-user-images\image-20260521214211132.png)

* ![image-20260521214604876](C:\Users\Wu\AppData\Roaming\Typora\typora-user-images\image-20260521214604876.png)

* 

  





# 项目设计说明书：基于 LangGraph 的解耦式多智能体智能模拟面试系统

## 1. 项目概述与核心目标

本项目是一款全栈 Web 模拟面试应用，旨在通过大模型技术为求职者提供高度真实的个性化面试对练体验。

### 核心设计原则

- **页面功能解耦**：简历分析、岗位分析、模拟面试作为独立功能页，互不干扰，通过后端数据库进行状态持久化。
- **状态机驱动面试**：模拟面试环节摒弃传统的单向 Pipeline，采用 **LangGraph** 构建有状态的、具备“动态追问”与“话题切换”能力的复杂多智能体协同网络。
- **千人千面（长期记忆）**：系统能够持久化用户的“技术弱点画像”，并在跨 Session 的新面试中引导面试官进行针对性提问。
- **FinOps 混合模型架构**：根据节点对认知能力（多模态/低延迟/高推理）的需求，路由至不同的商业或开源模型。

## 2. 系统技术栈选型

| **归属层级**          | **选型技术**                                              | **备注 / 选用理由**                               |
| --------------------- | --------------------------------------------------------- | ------------------------------------------------- |
| **前端 (Frontend)**   | React / Next.js / TailwindCSS                             | 构建响应式页面，处理流式文本输出（Streaming）     |
| **后端 (Backend)**    | FastAPI (Python)                                          | 与 LangGraph 深度集成，支持原生异步（Async）处理  |
| **图流控引擎**        | LangGraph (LangChain 生态)                                | 核心状态机引擎，管理 Agent 间的节点跳转与状态保持 |
| **数据库 (Database)** | Supabase (PostgreSQL + pgvector)                          | 统一处理结构化数据存储与面试资料的向量检索        |
| **混合 LLM 路由**     | API调用（不同Agent可以调用不同llm，设置有默认调用的主llm) | 兼顾多模态、低延迟路由与深度复盘推理              |

## 3. 数据库设计 (Schema)

AI 开发者请在 Supabase/PostgreSQL 中初始化以下核心表结构：

SQL

```
-- 1. 用户画像表（简历解析结果）
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    skills_matrix JSONB,          -- 技术栈分级: {"精通": [...], "熟练": [...]}
    project_highlights JSONB,    -- 项目核心亮点与难点提炼
    experience_level VARCHAR(50), -- 级别评估：校招/初级/高级
    potential_questions JSONB    -- 简历自带的被问盲区预估
);

-- 2. 目标岗位表（JD解析结果）
CREATE TABLE job_profiles (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(user_id),
    raw_jd TEXT,
    must_have_skills JSONB,       -- 核心硬性要求矩阵
    business_domain VARCHAR(100), -- 业务领域（如电商、金融、多模态CV）
    job_level VARCHAR(50)         -- 岗位职级
);

-- 3. 历史弱点记忆表（长期记忆网络）
CREATE TABLE weakness_memories (
    user_id UUID REFERENCES user_profiles(user_id),
    tech_stack VARCHAR(100),      -- 技术标签（如：Redis集群、Dijkstra算法）
    mastery_score FLOAT,          -- 掌握度评分 (0.0 - 1.0)
    audit_summary TEXT,           -- 具体的薄弱点表现描述
    last_tested_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, tech_stack)
);

-- 4. 面试会话表
CREATE TABLE interview_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(user_id),
    job_id UUID REFERENCES job_profiles(job_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    chat_history JSONB            -- 完整的面试对话流备份
);
```

## 4. 各功能页与 Agent 详细设计

### 4.1 页面 A：简历画像构建页 (Resume Profiler)

- **输入**：用户上传 PDF / 图片格式的简历。

- **后端 Agent**：`Resume Analyzer Agent`

- **模型路由**：多模态模型（如 `Qwen2.5-VL` 或 `GPT-4o-mini` 视觉版）。

- **提示词工程要点 (Prompt Core)**：

  > 使用系统的 `Structured Output` 功能，严禁输出任何 Markdown 格式的解释文本。必须将输入的简历图像/文本，精准转化为符合 `user_profiles` 表定义的 JSON 结构。重点识别项目描述中缺乏量化指标、技术栈描述模糊的潜在漏洞，写入 `potential_questions` 字段。

### 4.2 页面 B：岗位画像分析页 (JD Targeter)

- **输入**：用户粘贴的 JD 纯文本。

- **后端 Agent**：`Job Analyzer Agent`

- **模型路由**：轻量级低成本模型（如 `DeepSeek-V3` 或本地 `Qwen2.5-7B-Instruct`）。

- **提示词工程要点 (Prompt Core)**：

  > 提取该岗位的前 5 核心硬性指标（Must-have）。结合 JD 文本语义，推断面试官在考察该岗位时最关心的业务场景（如高并发、数据清洗、低功耗部署），输出标准 JSON 格式。

### 4.3 页面 C：核心功能——模拟面试对练舱 (Interview Cabin)

#### 4.3.1 全局状态定义 (LangGraph State)

Python

```
from typing import Annotated, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class InterviewState(TypedDict):
    # 基础上下文（从DB拉取）
    user_profile: Dict[str, Any]
    job_profile: Dict[str, Any]
    weakness_memory: List[Dict[str, Any]]
    
    # 实时对话状态
    messages: Annotated[List[BaseMessage], "Add messages"] -- 对话历史流
    current_topic: str          -- 当前正在考察的技术/项目点
    follow_up_count: int       -- 当前话题的连续追问次数
    current_round: int         -- 总提问轮次
    max_rounds: int            -- 设定最大轮次限制（如 8 轮）
```

#### 4.3.2 节点（Nodes）与路由（Edges）拓扑逻辑

请 AI 开发者使用 `langgraph.graph.StateGraph` 实现以下拓扑结构：

##### 节点 1：`Initializer_Node`

- **逻辑**：根据前端传入的 `user_id` 和 `job_id`，查询数据库，将用户画像、目标岗位要求以及过往的历史弱点拼装加载到 `InterviewState` 中。如果用户此页面上传了新增参考资料，调用 `pgvector` 进行实时索引挂载。

##### 节点 2：`Question_Router_Node` (核心智能路由器)

- **模型路由**：极低延迟模型（如 `Qwen2.5-7B-Instruct` 或 `GPT-4o-mini`）。
- **工作逻辑**：
  1. 接收用户最新的一条回答。
  2. 审查当前状态：若 `current_round >= max_rounds`，将路由导向 `Assessment_Node`。
  3. 若未到上限，分析用户的回答深度。若用户提到核心技术概念但未展开细节，且 `follow_up_count < 3`，则将状态中的 `follow_up_count` 加 1，保持 `current_topic` 不变，将路由条件导向 `Interviewer_Node` 并附带指令 `[Action: Follow_Up]`。
  4. 若用户回答完美，或者 `follow_up_count >= 3`，或者用户主动表达“不了解”，则将 `follow_up_count` 清零，从 `job_profile` 的未覆盖技术点与 `weakness_memory` 的历史弱点中，选取下一个最高优先级的话题，更新 `current_topic`，将路由条件导向 `Interviewer_Node` 并附带指令 `[Action: Switch_Topic]`。

##### 节点 3：`Interviewer_Node` (虚拟面试官)

- **模型路由**：拟人化长文本模型（如 `DeepSeek-V3`）。
- **工作逻辑**：
  1. 接收 Router 传来的 Action 指令与 `current_topic`。
  2. **RAG 介入**：利用 `current_topic` 作为关键词，异步检索用户上传的面试资料知识库，召回前 2 块最相关的知识分片（Chunks）作为 Context。
  3. **生成提问**：
     - 若是 `Follow_Up`：结合上下文，针对用户上一轮回答的漏洞进行高难度追问。
     - 若是 `Switch_Topic`：结合历史弱点或新知识点，平滑地切换面试风向（如：“我看你的简历里提到了 X，我们聊聊这个。在你的参考资料里提到了 Y 场景，如果是你，你会怎么设计？”）。

##### 节点 4：`Assessment_Node` (深度复盘评估)

- **模型路由**：高推理解性模型（如 `DeepSeek-R1` 完整版）。
- **工作逻辑**：
  1. 在总轮次达到后触发。解析全场完整的 `messages` 对话流。
  2. 生成结构化复盘报告：包括技术总评分（0-100）、表现亮点、答错清单。
  3. **知识提炼**：提炼出本次面试中暴露出的全新技术弱点，转化为标准 K-V 结构（如：`{"技术标签": "Redis脑裂", "掌握度": 0.3, "表现审计": "知道哨兵机制，但对网络分区导致的数据丢失解决方案完全没有概念"}`）。

##### 节点 5：`Memory_Updater_Node` (长期记忆写入)

- **逻辑**：无模型调用。作为一个纯后台数据处理节点，接收 `Assessment_Node` 提炼出的全新弱点 JSON，对 `weakness_memories` 数据表执行 `UPSERT` 操作，完成系统长期记忆的闭环。

## 5. 面试高频问题防御机制 (AI 开发防错检查)

为防止大模型生成代码时引入常见 Agent Bug，开发时必须实现以下防御机制：

1. **防止追问死循环 (Deadlock Prevention)**：

   Router 节点的条件边（Conditional Edge）必须严格校验 `follow_up_count` 计数器和用户文本语义。一旦检测到用户连续两次使用“不清楚”、“不知道”、“忘了”等词汇，**必须强制**将 Action 设为 `Switch_Topic`，无条件截断追问。

2. **Context 长度控制 (Token Control)**：

   加载 `user_profile` 和 `job_profile` 时，严禁将全量解析文本塞入 System Prompt。必须在页面 A 和页面 B 阶段完成高密度特征提取，控制单次初始化塞入的 JSON 字段长度在 1000 Token 以内。

3. **流式响应 (Streaming API)**：

   `Interviewer_Node` 节点的输出必须支持 Web 通信的 `stream` 模式。FastAPI 侧需使用 `EventSourceResponse` (SSE)，配合 LangGraph 的 `graph.astream_events()`，确保前端页面能像真实大模型聊天一样逐字打字输出面试官的提问。