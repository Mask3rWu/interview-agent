# 单用户多画像智能模拟面试系统设计

## 1. 设计目标

本系统是一个面向单用户的智能模拟面试应用。用户可以维护多份简历画像、多个目标岗位画像和多份面试资料，在创建模拟面试时动态选择需要使用的简历、岗位和资料集合。系统通过 LangGraph 驱动面试流程，通过 RAG 引入用户上传资料，通过长期记忆建模用户对知识点的掌握情况。

第一版重点保证链路完整、状态清晰、实现成本可控。系统暂不引入完整用户认证、数据库级模型调用日志、复杂成本核算和分布式任务队列。

核心能力：

- 多简历画像：同一用户可维护多份简历解析结果。
- 多岗位画像：同一用户可维护多个目标岗位 JD 解析结果。
- 面试资料 RAG：支持上传资料、切分、向量化，面试时可选择全部资料、部分资料或不使用资料。
- 热选择上下文：创建面试时选择简历画像、岗位画像和资料集合。
- 状态机面试：使用 LangGraph 实现首问、追问、切题、评估和记忆更新。
- 知识掌握画像：记录考察过的知识点、薄弱项、掌握度、来源面试和复习时间。
- 混合模型配置：默认所有 Agent 使用主 LLM，允许在环境变量中为特定 Agent 覆盖模型。

## 2. 技术栈

| 层级 | 技术 | 说明 |
| --- | --- | --- |
| 前端 | Next.js / React / TailwindCSS | 页面、表单、SSE 流式展示 |
| 后端 | FastAPI / Python | API、文件处理、LangGraph 编排 |
| Agent 编排 | LangGraph | 面试状态机、条件边、节点流转 |
| 数据库 | Supabase PostgreSQL + pgvector | 元数据、向量检索、长期记忆 |
| 本地存储 | Markdown / log 文件 | 简历、JD、资料原文、面试记录、评估报告、模型调用日志 |
| LLM | OpenAI-compatible API / 本地模型 API | 通过环境变量配置默认模型和 Agent 专属模型 |

## 3. 推荐项目结构

```text
interviewAgent/                         # 项目根目录
  apps/                                 # 应用代码目录
    web/                                # Next.js 前端应用
      src/                              # 前端源码
        app/                            # Next.js App Router 页面入口
          layout.tsx                    # 根布局：全局 html/body 结构
          page.tsx                      # 首页
          globals.css                   # 全局样式
          resumes/                      # 简历画像管理页：上传、列表、详情
          jobs/                         # 岗位画像管理页：JD 输入、列表、详情
          materials/                    # 面试资料管理页：上传、处理状态、启用状态
          interview/                    # 模拟面试页：创建会话、对话、SSE 流式展示
          memory/                       # 记忆页：知识掌握画像 + 面试历史评估
          history/                      # 历史页：历史面试记录与重新评估
        lib/                            # 前端工具
          api.ts                        # HTTP API 封装
          sse.ts                        # SSE 流式客户端
        types/                          # 前端 TypeScript 类型
          index.ts                      # 类型定义，与后端响应结构保持一致
      package.json                      # 前端依赖与脚本
      tsconfig.json                     # TypeScript 配置
      next.config.ts                    # Next.js 配置

    api/                                # FastAPI 后端 (Python 包根目录)
      __init__.py                       # 包初始化
      main.py                           # FastAPI app、CORS、路由注册、启动入口
      requirements.txt                  # Python 依赖
      routes/                           # HTTP API 层，按业务拆分的 FastAPI router
        __init__.py
        resumes.py                      # 简历上传、简历画像列表和详情接口
        jobs.py                         # JD 提交、岗位画像列表和详情接口
        materials.py                    # 面试资料上传、切分、向量化和列表接口
        interviews.py                   # 面试创建、回答提交、SSE 输出、结束接口
        memory.py                       # 长期记忆查询/重建接口
      core/                             # 最底层基础设施，不依赖任何内部业务模块
        __init__.py
        config.py                       # 环境变量、路径、模型配置、数据库配置
        logging.py                      # 控制台日志和文件日志配置
        json_store.py                   # 本地 JSON 文件读写封装
      db/                               # 数据库访问层，不包含业务决策
        __init__.py
        client.py                       # Supabase/PostgreSQL client 初始化
        repositories.py                 # 表级 CRUD 和查询封装
      schemas/                          # Pydantic 数据结构层
        __init__.py
        resume.py                       # 简历 API 请求/响应、简历解析结构化输出
        job.py                          # 岗位 API 请求/响应、JD 解析结构化输出
        material.py                     # 资料 API 请求/响应、chunk 元数据结构
        interview.py                    # 面试创建请求、SSE 事件、会话 DTO
        memory.py                       # 长期记忆 DTO、记忆更新结构
        llm_outputs.py                  # LLM structured output 专用 Schema
      services/                         # 业务服务层，组合 db/rag/model/markdown 完成用例
        __init__.py
        model_router.py                 # 根据 Agent 名称选择默认模型或专属模型
        mock_llm.py                     # Mock LLM 回退，无 API 配置时使用
        markdown_store.py               # 本地 Markdown 读写、路径生成、文件命名
        resume_service.py               # 简历上传、转文本、调用解析模型、落库
        job_service.py                  # JD 解析、Markdown 保存、岗位画像落库
        material_service.py             # 资料保存、切分、embedding、chunk 落库
        memory_service.py               # 掌握度更新、遗忘曲线、历史重建、复习时间计算
        interview_service.py            # 面试会话管理、LangGraph 驱动、SSE 流式输出
      agents/                           # LangGraph 编排层，负责面试状态机
        __init__.py
        interview_graph.py              # 构建 StateGraph、注册节点和条件边
        state.py                        # LangGraph InterviewState TypedDict
        nodes/                          # Graph 节点，每个节点只负责一个状态转换步骤
          __init__.py
          initializer.py                # 加载会话、画像、资料选择和历史薄弱点记忆
          question_router.py            # 判断追问、切题或进入评估
          interviewer.py                # RAG 检索并流式生成面试官问题
          assessment.py                 # 生成复盘报告、评估状态和 memory_updates
          memory_updater.py             # 将评估结果写入长期记忆
        prompts/                        # Prompt 模板，便于单独调试和版本管理
          resume_analyzer.md            # 简历解析 Prompt
          job_analyzer.md               # JD 解析 Prompt
          question_router.md            # 追问/切题决策 Prompt
          interviewer.md                # 面试官提问 Prompt
          assessment.md                 # 复盘评估 Prompt
      rag/                              # RAG 子系统
        __init__.py
        chunking.py                     # Markdown/文本切分策略
        embeddings.py                   # embedding 模型调用封装
        retrieval.py                    # pgvector 检索和 top-k 结果整理
      data/                             # 本地 JSON 数据
        db.json                         # 本地文件数据库
      logs/                             # 本地日志目录 (运行时生成)

  data/                                 # 本地长文本和产物存储
    resumes/                            # 简历原文/解析结果 Markdown
    jobs/                               # JD 原文/岗位画像 Markdown
    materials/                          # 面试资料 Markdown
    interviews/                         # 面试完整转写 transcript
    reports/                            # 面试评估报告 Markdown

  supabase/                             # 数据库工程目录
    migrations/                         # PostgreSQL/pgvector 表结构迁移 SQL
      001_initial_schema.sql            # 初始表结构

  .env.example                          # 环境变量模板
  .gitignore                            # Git 忽略规则
  CLAUDE.md                             # Claude Code 项目指南
  SYSTEM_DESIGN.md                      # 当前完整系统设计文档
  plan.md                               # 原始项目计划草案
  agent.md                              # Agent 设计笔记
  question.md                           # 问题分析笔记
  README.md                             # 项目启动和开发说明
```

## 4. 工程分层与 Schema 规范

### 4.1 后端依赖层次

后端采用单向依赖，避免循环引用和业务逻辑散落。

```text
agents        # 最高层：依赖 services / rag / schemas / core，负责编排 LangGraph
routes        # HTTP 层：依赖 services / schemas / core，负责请求响应
services      # 业务层：依赖 db / rag / schemas / core，负责具体用例
rag           # 检索层：依赖 db / schemas / core，负责 chunk、embedding、retrieval
memory        # 记忆算法：放在 services/memory_service.py，依赖 db / schemas / core
db            # 数据访问层：依赖 schemas / core，封装数据库读写
schemas       # 数据结构层：依赖 pydantic，定义 API 和 LLM 输出结构
core          # 最底层：配置、日志、常量，不依赖任何内部业务模块
```

依赖约束：

- `core` 不能 import 任何业务模块。
- `schemas` 不能 import `services`、`agents`、`routes`。
- `db` 不能 import `agents`、`routes`。
- `services` 不能 import `routes`。
- `agents` 可以调用 `services`，但 `services` 不反向调用 `agents`。
- `routes` 只做请求校验、调用 service、返回响应，不直接写数据库或调用模型。

### 4.2 Pydantic 使用规范

FastAPI 请求体、响应体、数据库 DTO、LLM 结构化输出都使用 Pydantic `BaseModel`。普通 Python class 只用于内部无校验需求的轻量工具。

使用 Pydantic 的原因：

- 自动校验 API 输入输出，减少手写参数检查。
- 自动生成 OpenAPI/Swagger 文档。
- 通过 `Field(description=...)` 描述字段语义，可复用于 LLM structured output。
- 支持 UUID、时间、枚举、嵌套对象等类型转换。
- 让 service、agent、db 之间的数据契约更稳定。

示例：

```python
from typing import Literal
from pydantic import BaseModel, Field


class RouterDecision(BaseModel):
    action: Literal["follow_up", "switch_topic", "assess"] = Field(
        description="下一步动作：追问、切题或进入评估"
    )
    quality: Literal["excellent", "adequate", "vague", "wrong", "unknown"] = Field(
        description="用户上一轮回答质量"
    )
    next_topic: str | None = Field(default=None, description="切题时建议的新话题")
    reason: str = Field(description="做出该决策的简短原因")
```

Schema 拆分建议：

- `schemas/resume.py`：简历 API 和简历解析结果。
- `schemas/job.py`：岗位 API 和 JD 解析结果。
- `schemas/material.py`：资料 API、chunk 元数据。
- `schemas/interview.py`：面试创建请求、SSE 事件、会话 DTO。
- `schemas/memory.py`：长期记忆、记忆更新。
- `schemas/llm_outputs.py`：跨模块复用的 LLM 输出结构，例如 `RouterDecision`、`AssessmentResult`。

### 4.3 Structured Output 使用规范

`llm.with_structured_output(...)` 用于需要稳定 JSON 结果的 LLM 调用，但不替代 LangGraph node。正确关系是：Graph node 负责流程控制，node 内部可以调用 structured LLM。

适合使用 structured output 的场景：

- 简历解析：输出 `ResumeAnalysisResult`。
- JD 解析：输出 `JobAnalysisResult`。
- 问题路由：输出 `RouterDecision`。
- 复盘评估：输出 `AssessmentResult` 和 `MemoryUpdate[]`。

不适合使用 structured output 的场景：

- 面试官自然语言提问，尤其需要 SSE token 流式输出时。
- RAG 检索、Markdown 读写、数据库 CRUD 等非 LLM 任务。

示例：

```python
async def question_router_node(state: InterviewState) -> dict:
    llm = model_router.get_llm("question_router")
    structured_llm = llm.with_structured_output(RouterDecision)
    decision = await structured_llm.ainvoke(build_router_messages(state))

    return {
        "action": decision.action,
        "current_topic": decision.next_topic or state["current_topic"],
    }
```

## 5. 数据存储策略

系统采用“数据库保存索引和结构化摘要，本地 Markdown 保存长文本”的方式，减少数据库表数量和复杂度。

### 5.1 本地 Markdown 文件

以下内容保存为本地 Markdown：

```text
data/resumes/{resume_id}.md
data/jobs/{job_id}.md
data/materials/{material_id}.md
data/interviews/{session_id}.md
data/reports/{session_id}.md
```

建议 Markdown 内容包含：

- 原始输入或可读转写文本。
- 模型解析出的结构化 JSON。
- 人类可读摘要。
- 创建时间和来源信息。

数据库只保存这些 Markdown 文件的路径、摘要字段和检索所需数据。

### 5.2 最小数据库表

第一版建议使用 6 张核心表。

#### resume_profiles

保存多份简历画像的元数据和结构化摘要。

```sql
CREATE TABLE resume_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    source_file_path TEXT,
    markdown_path TEXT NOT NULL,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    skills_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    potential_questions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### job_profiles

保存多个岗位画像的元数据和结构化摘要。

```sql
CREATE TABLE job_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    company TEXT,
    markdown_path TEXT NOT NULL,
    must_have_skills_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    domain TEXT,
    level TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### materials

保存面试资料元信息。资料正文保存在本地 Markdown。

```sql
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    source_file_path TEXT,
    markdown_path TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### material_chunks

保存 RAG 切片和向量。

```sql
CREATE TABLE material_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(material_id, chunk_index)
);
```

`VECTOR(1536)` 需要根据实际 embedding 模型维度调整。

#### interview_sessions

保存面试会话的最小状态。完整对话和报告保存到本地 Markdown。

```sql
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_profile_id UUID REFERENCES resume_profiles(id) ON DELETE SET NULL,
    job_profile_id UUID REFERENCES job_profiles(id) ON DELETE SET NULL,
    selected_material_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    transcript_path TEXT NOT NULL,
    report_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);
```

#### knowledge_memories

以知识点为单位记录长期记忆。

```sql
CREATE TABLE knowledge_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL UNIQUE,
    category TEXT,
    mastery_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    exposure_count INTEGER NOT NULL DEFAULT 0,
    weakness_count INTEGER NOT NULL DEFAULT 0,
    last_tested_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,
    evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 5.3 建议索引

```sql
CREATE INDEX idx_material_chunks_material_id ON material_chunks(material_id);
CREATE INDEX idx_knowledge_memories_mastery ON knowledge_memories(mastery_score);
CREATE INDEX idx_knowledge_memories_next_review ON knowledge_memories(next_review_at);
CREATE INDEX idx_interview_sessions_created_at ON interview_sessions(created_at DESC);
```

向量索引根据 Supabase pgvector 实际配置选择 `ivfflat` 或 `hnsw`。

## 6. 前端页面设计

### 6.1 简历画像页

能力：

- 上传 PDF、图片或文本简历。
- 展示已解析的简历画像列表。
- 查看每份简历的 Markdown 摘要、技能矩阵、项目亮点和潜在追问点。
- 允许重命名画像。

### 6.2 岗位画像页

能力：

- 粘贴 JD 文本。
- 生成岗位画像。
- 展示岗位列表，包括公司、岗位名、业务领域、级别和核心要求。
- 查看岗位 Markdown 摘要。

### 6.3 面试资料页

能力：

- 上传 PDF、Markdown、TXT 等资料。
- 后端转换为 Markdown、切 chunk、写入向量表。
- 展示资料处理状态和启用状态。
- 支持在创建面试时选择全部资料、部分资料或不使用资料。

### 6.4 模拟面试页

能力：

- 创建面试前选择：
  - 简历画像：可选。
  - 岗位画像：可选。
  - 面试资料：全部、部分或不使用。
  - 最大轮次：默认 8。
- 面试过程中显示对话流。
- 用户提交回答后，通过 SSE 流式展示面试官下一问。
- 支持手动结束面试并生成评估报告。

### 6.5 长期记忆页

能力：

- 展示知识点、分类、掌握度、考察次数、薄弱次数、最近考察时间和下次建议复习时间。
- 支持按掌握度和复习时间排序。
- 上方提供“从历史重建”按钮，清空当前 `knowledge_memories` 后，按历史面试重新评估并重建记忆。
- 下方合并面试历史评估列表，展示每场面试的评估状态。
- 未成功评估的历史面试支持单独触发重新评估。

## 7. API 设计

### 7.1 简历

```http
POST /resumes
```

上传简历文件，解析后创建 `resume_profiles` 记录和本地 Markdown 文件。

```http
GET /resumes
GET /resumes/{resume_id}
```

返回简历画像列表或详情。

### 7.2 岗位

```http
POST /jobs
```

提交 JD 文本，解析后创建 `job_profiles` 记录和本地 Markdown 文件。

```http
GET /jobs
GET /jobs/{job_id}
```

返回岗位画像列表或详情。

### 7.3 面试资料

```http
POST /materials
```

上传资料，转换为 Markdown，切分并写入 `material_chunks`。

```http
GET /materials
GET /materials/{material_id}
```

返回资料列表或详情。

### 7.4 面试

```http
POST /interviews
```

创建面试会话。

请求体：

```json
{
  "resume_profile_id": "optional uuid",
  "job_profile_id": "optional uuid",
  "material_ids": ["optional uuid"],
  "use_all_materials": false,
  "max_rounds": 8
}
```

返回：

```json
{
  "session_id": "uuid",
  "status": "active"
}
```

```http
POST /interviews/{session_id}/answer
```

提交用户回答，后端驱动 LangGraph，使用 SSE 流式返回下一问或评估结果。

请求体：

```json
{
  "answer": "用户回答文本"
}
```

SSE 事件：

- `token`: 面试官输出 token。
- `message_end`: 当前问题输出结束。
- `assessment`: 面试结束后的结构化评估。
- `error`: 异常信息。

```http
POST /interviews/{session_id}/finish
```

手动结束面试并触发评估。

```http
GET /interviews/{session_id}
```

返回会话详情、Markdown 路径和报告路径。

### 7.5 长期记忆

```http
GET /memory
```

返回知识点掌握情况。

```http
POST /memory/rebuild
```

清空当前 `knowledge_memories`，按所有历史面试记录重新评估并重建记忆。

```http
POST /interviews/{session_id}/assess
```

对单场历史面试重新评估。评估成功后可写入长期记忆。

## 8. LangGraph 面试设计

### 8.1 State 定义

```python
from typing import Annotated, Literal, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class InterviewState(TypedDict):
    session_id: str
    resume_profile: dict | None
    job_profile: dict | None
    selected_material_ids: list[str]
    retrieved_context: list[dict]
    weakness_memory: list[dict]

    messages: Annotated[list[BaseMessage], add_messages]
    current_topic: str | None
    covered_topics: list[str]
    action: Literal["initial_question", "follow_up", "switch_topic", "assess"]

    follow_up_count: int
    unclear_count: int
    current_round: int
    max_rounds: int

    assessment: dict | None
    assessment_status: Literal["pending", "success", "failed"]
    assessment_error: str
    memory_updates: list[dict]
```

### 8.2 节点

#### initializer

职责：

- 根据 `session_id` 加载会话。
- 加载所选简历画像和岗位画像。
- 加载长期记忆中的弱点画像。
- 根据资料选择策略确定可检索的 `material_ids`。
- 选择首个 `current_topic`。

首个话题优先级：

1. 岗位核心要求。
2. 简历项目亮点。
3. 掌握度低于 0.6 的长期记忆知识点。
4. 已到复习时间的知识点。
5. 面试资料中高相关主题。

#### question_router

职责：

- 判断是否结束面试。
- 判断追问或切题。
- 更新 `follow_up_count`、`unclear_count`、`covered_topics` 和 `current_topic`。
- 在节点内部使用 `llm.with_structured_output(RouterDecision)` 获取稳定的路由判断结果。

规则：

- `current_round >= max_rounds` 时进入 `assessment`。
- `follow_up_count >= 3` 时强制切题。
- 用户连续两次表达“不知道”“不清楚”“忘了”“没了解过”时强制切题。
- 用户回答提到核心概念但缺少原因、边界、权衡或实现细节时追问。
- 用户回答充分或当前话题已覆盖时切题。

#### interviewer

职责：

- 根据 `action` 和 `current_topic` 生成问题。
- 使用 `current_topic` 检索所选资料的 top-k chunks，默认 top 2。
- 通过 SSE 流式输出问题。
- 将面试官问题追加到 transcript Markdown。

生成策略：

- `initial_question`: 开场问题，结合简历、岗位和资料。
- `follow_up`: 针对上一轮回答漏洞深入追问。
- `switch_topic`: 平滑切换到新主题，避免生硬跳转。

#### assessment

职责：

- 读取完整对话。
- 使用 `llm.with_structured_output(AssessmentResult)` 生成结构化评估。
- 写入 `data/reports/{session_id}.md`。
- 生成 `memory_updates`。
- 记录 `assessment_status` 和 `assessment_error`。

报告内容：

- 总评分。
- 技术能力评分。
- 沟通表达评分。
- 表现亮点。
- 答错或不完整清单。
- 建议复习知识点。
- 本次新增或更新的知识记忆。

#### memory_updater

职责：

- 读取 `memory_updates`。
- 对 `knowledge_memories` 执行插入或更新。
- 应用掌握度更新和遗忘曲线规则。
- `evidence_json` 只保存来源面试 ID、表现和时间戳。

## 9. 追问、切题和话题选择

### 9.1 回答质量判断

第一版由 `question_router` 使用轻量模型和 Pydantic structured output 输出结构化判断：

```json
{
  "quality": "excellent | adequate | vague | wrong | unknown",
  "should_follow_up": true,
  "reason": "简短原因",
  "suggested_next_topic": "可选"
}
```

### 9.2 强制切题规则

满足任一条件时切题：

- 当前话题追问次数达到 3。
- 用户连续 2 次表示不会。
- 当前话题已经形成明确评估。
- 模型判断继续追问收益低。

### 9.3 话题优先级

候选话题分数：

```text
score =
  岗位核心要求权重
  + 简历相关性权重
  + 长期记忆薄弱权重
  + 遗忘复习权重
  + 资料相关性权重
  - 已覆盖惩罚
```

默认权重：

- 岗位核心要求：+40
- 简历项目相关：+25
- `mastery_score < 0.6`：+30
- 到达 `next_review_at`：+20
- RAG 资料相关：+15
- 已覆盖：-100

## 10. 长期记忆设计

长期记忆在本项目中更准确地说是“知识掌握画像”。它不是对话记忆，也不是用户偏好记忆，而是把面试中暴露出的知识点抽象成可重建的结构化状态。

### 10.1 记忆对象

每条记忆对应一个知识点，例如：

- Redis 脑裂
- MySQL 索引失效
- React 状态管理
- Transformer Attention
- FastAPI 异步处理

### 10.2 掌握度更新

每次评估输出知识点表现：

```json
{
  "topic": "Redis 脑裂",
  "category": "backend",
  "performance": "wrong",
  "evidence": "知道哨兵机制，但无法解释网络分区下的数据一致性风险"
}
```

更新规则：

- `excellent`: `mastery_score += 0.12`
- `adequate`: `mastery_score += 0.05`
- `vague`: `mastery_score -= 0.08`
- `wrong`: `mastery_score -= 0.15`
- `unknown`: `mastery_score -= 0.18`

最终分数限制在 `[0.0, 1.0]`。

同时更新：

- `exposure_count += 1`
- `wrong/vague/unknown` 时 `weakness_count += 1`
- `last_tested_at = now()`
- `evidence_json` 追加最近证据，最多保留 10 条
- `source_interview_ids` 记录来源面试 ID

### 10.3 遗忘曲线

面试初始化或记忆页刷新时，可以对长期未考察知识点应用轻量衰减。

公式：

```text
decayed_score = mastery_score * exp(-days_since_tested / half_life_days)
```

半衰期：

- `mastery_score < 0.4`: 3 天
- `0.4 <= mastery_score < 0.7`: 7 天
- `mastery_score >= 0.7`: 21 天

衰减后的低分知识点优先进入面试候选话题。

### 10.4 历史重建

`POST /memory/rebuild` 的语义是：

1. 清空当前 `knowledge_memories`。
2. 遍历所有已结束的历史面试。
3. 对每场面试重新执行评估。
4. 只有评估成功的面试才把 `memory_updates` 合并进新的 `knowledge_memories`。

单场历史面试可以通过 `POST /interviews/{session_id}/assess` 重新评估。成功后会按同一套记忆聚合规则写入长期记忆。

### 10.5 复习时间

更新后设置 `next_review_at`：

- `mastery_score < 0.4`: 1 天后。
- `0.4 <= mastery_score < 0.6`: 3 天后。
- `0.6 <= mastery_score < 0.8`: 7 天后。
- `mastery_score >= 0.8`: 21 天后。

## 11. RAG 设计

### 11.1 资料处理流程

1. 上传资料。
2. 转为 Markdown 或纯文本。
3. 保存到 `data/materials/{material_id}.md`。
4. 按标题和长度切 chunk。
5. 生成 embedding。
6. 写入 `material_chunks`。

### 11.2 切分策略

默认：

- chunk 大小：800 到 1200 中文字符。
- overlap：100 到 150 中文字符。
- 保留标题路径到 `metadata_json`。

### 11.3 检索策略

面试时只检索本次选择的资料：

- 选择全部资料：检索所有 `enabled = true` 的资料。
- 选择部分资料：只检索指定 `material_ids`。
- 不使用资料：跳过 RAG。

默认 top-k 为 2。检索 query 由 `current_topic + job_profile domain + latest user answer` 组成。

## 12. 模型路由设计

### 12.1 环境变量

```env
DEFAULT_LLM_PROVIDER=openai_compatible
DEFAULT_LLM_BASE_URL=
DEFAULT_LLM_API_KEY=
DEFAULT_LLM_MODEL=deepseek-chat

RESUME_ANALYZER_MODEL=
JOB_ANALYZER_MODEL=
QUESTION_ROUTER_MODEL=
INTERVIEWER_MODEL=
ASSESSMENT_MODEL=

EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=
EMBEDDING_API_KEY=
EMBEDDING_MODEL=
EMBEDDING_DIMENSIONS=1536
```

### 12.2 路由规则

- Agent 专属模型为空时，使用 `DEFAULT_LLM_MODEL`。
- Agent 专属模型不为空时，使用专属模型。
- `model_router.py` 统一负责读取配置和创建客户端。
- 每次调用输出控制台日志：

```text
[model_call] agent=interviewer model=deepseek-chat duration_ms=1234 status=ok
```

- 同步追加到：

```text
apps/api/logs/model_calls.log
```

第一版不实现复杂 fallback、成本估算和监控平台。

### 12.3 Structured Output 调用方式

`model_router.py` 只负责返回指定 Agent 对应的基础 LLM client，不直接绑定输出结构。需要结构化输出的节点或 service 自行调用 `with_structured_output`。

```python
llm = model_router.get_llm("resume_analyzer")
structured_llm = llm.with_structured_output(ResumeAnalysisResult)
result = await structured_llm.ainvoke(messages)
```

约定：

- `resume_service.py` 使用 `ResumeAnalysisResult`。
- `job_service.py` 使用 `JobAnalysisResult`。
- `question_router.py` 使用 `RouterDecision`。
- `assessment.py` 使用 `AssessmentResult`。
- `interviewer.py` 不使用 structured output，保留自然语言流式输出。

## 13. 日志策略

应用日志：

```text
apps/api/logs/app.log
```

模型调用日志：

```text
apps/api/logs/model_calls.log
```

面试转写：

```text
data/interviews/{session_id}.md
```

评估报告：

```text
data/reports/{session_id}.md
```

日志只用于本地调试，不作为第一版功能页面的数据源。

## 14. 第一版实现顺序

### 阶段 1：基础工程和存储

- 初始化 Next.js 和 FastAPI 项目结构。
- 配置 Supabase 连接。
- 创建 6 张核心表。
- 实现 Markdown 本地存储服务。
- 实现 `.env` 配置读取。

### 阶段 2：画像和资料处理

- 实现简历上传和解析。
- 实现 JD 输入和解析。
- 实现资料上传、Markdown 转换、chunk 和 embedding。
- 实现列表页和详情页。

### 阶段 3：面试主链路

- 实现 `interview_sessions` 创建。
- 实现 LangGraph `initializer`、`question_router`、`interviewer`。
- 实现 SSE 流式回答。
- 将对话写入 transcript Markdown。

### 阶段 4：评估和长期记忆

- 实现 `assessment` 节点。
- 生成评估报告 Markdown。
- 实现 `memory_updater`。
- 实现长期记忆列表页。

### 阶段 5：稳定性和体验

- 加入追问死循环防护。
- 加入 RAG 空结果处理。
- 加入模型调用日志。
- 完善错误提示和 loading 状态。

## 15. 测试计划

### 单元测试

- Markdown 存储路径生成和写入。
- RAG chunk 切分。
- 长期记忆掌握度更新。
- 遗忘曲线衰减。
- 模型路由配置选择。
- Pydantic schema 对非法输入的校验。
- structured output schema 字段缺失时的错误处理。

### 集成测试

- 上传简历后生成 `resume_profiles` 和 Markdown。
- 提交 JD 后生成 `job_profiles` 和 Markdown。
- 上传资料后生成 `materials` 和 `material_chunks`。
- 创建面试时可以选择简历、岗位和资料。
- 用户回答后可以通过 SSE 收到下一问。
- 达到最大轮次后生成评估报告。
- 评估后更新 `knowledge_memories`。

### 关键场景测试

- 不选择简历，只选择岗位开始面试。
- 不选择岗位，只选择简历开始面试。
- 不选择资料，RAG 跳过但面试正常。
- 选择部分资料，只检索指定资料。
- 连续两次回答“不知道”，系统强制切题。
- 同一话题追问达到 3 次，系统强制切题。
- 模型专属环境变量为空时回退默认模型。
- `question_router` 返回非法 action 时能够被 schema 校验拦截。

## 16. 明确暂不实现

第一版暂不实现：

- 多用户认证和权限隔离。
- 数据库级模型调用日志。
- 复杂成本核算。
- 自动模型 fallback。
- 分布式任务队列。
- 在线编辑长期记忆。
- 多人协作或团队空间。
