# interviewAgent Development Guide

## Environment

- **Conda environment**: `agent-py311`
- Always activate before running any Python commands:
  ```bash
  conda activate agent-py311
  ```

## Design Document

- **Primary reference**: `SYSTEM_DESIGN.md` — the authoritative design document for this project. All implementation decisions should be based on this document.
- **Secondary reference**: `plan.md` — an early-stage draft. It may diverge significantly from `SYSTEM_DESIGN.md`. When conflicts arise, `SYSTEM_DESIGN.md` always takes precedence.

## Project Overview

A single-user multi-persona intelligent mock interview system built with:
- **Frontend**: Next.js / React / TailwindCSS
- **Backend**: FastAPI / Python
- **Agent Orchestration**: LangGraph
- **Database**: Supabase PostgreSQL + pgvector
- **LLM**: OpenAI-compatible API

The system allows a user to maintain multiple resume profiles, job profiles, and interview materials, then create mock interviews by dynamically selecting which resources to use.
