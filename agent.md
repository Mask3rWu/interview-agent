# agent.md

## Role

You are working on `interviewAgent`, a single-user mock interview system.

## Source Of Truth

- `SYSTEM_DESIGN.md` is the authoritative design document.
- `plan.md` is historical context only.

## Current Product Shape

- `memory` page combines knowledge mastery and interview history.
- `POST /memory/rebuild` clears `knowledge_memories` and rebuilds from all historical interviews.
- `POST /interviews/{session_id}/assess` re-evaluates a single interview.

## Working Rules

- Prefer the existing code style and local patterns.
- Keep edits tightly scoped to the requested feature.
- Do not revert unrelated user changes.
- When changing backend behavior, update matching frontend types and views.
- When changing state or API contracts, update docs in `SYSTEM_DESIGN.md`.

## Validation

- Run Python syntax checks for touched backend files.
- Run frontend typecheck for touched frontend files.
- Note any repo-existing lint issues separately from new ones.

