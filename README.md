# interviewAgent

单用户多画像智能模拟面试系统。

## 快速启动

### 1. 环境准备

```bash
conda activate agent-py311
cd apps/api && pip install -r requirements.txt
cd ../web && npm install
```

### 2. 配置 LLM（可选，无配置时使用 mock）

```bash
cp .env.example .env
# 编辑 .env，填入 API Key 和模型名称
```

### 3. 启动后端

```bash
conda activate agent-py311
cd apps/api
python -m app.main
# API 运行在 http://localhost:8000
# Swagger 文档: http://localhost:8000/docs
```

### 4. 启动前端

```bash
cd apps/web
npm run dev
# 前端运行在 http://localhost:3000
```

## 项目结构

参见 `SYSTEM_DESIGN.md`。
