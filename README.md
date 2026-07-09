# AI-Powered SAST Platform

An agentic AI-powered Static Application Security Testing (SAST) platform. This repository
currently contains the **engineering foundation** only — no business logic, scanning,
GitNexus integration, taint engine, AI agents, or authentication yet. See
[docs/TASK_BACKLOG.md](docs/TASK_BACKLOG.md) for the ordered plan and
[docs/ARCHITECTURE_v2.3.md](docs/ARCHITECTURE_v2.3.md) for the design.

> **Status:** Phase-0 engineering foundation. The next feature task is **TASK-020a**
> (eval corpus acquisition). This foundation exists to make that — and the rest of Phase 0
> — startable. Do not exceed MVP scope without a backlog task.

## Stack (fixed by the architecture)

- **Backend:** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.x · Alembic · PostgreSQL 16 · Redis
- **Frontend:** React 18 · TypeScript · Vite · Tailwind (app shell only; feature pages arrive in Phase 1, TASK-180a)
- **Infra:** Docker Compose (single-tenant MVP)
- **Eval harness:** top-level [`eval/`](eval/)

## Repository layout (current)

```
backend/    FastAPI app skeleton, config, logging, DB/Alembic foundation, tests
frontend/   Vite + React + TS + Tailwind app shell
docker/     Dockerfiles + dev compose (postgres, redis, backend, frontend)
eval/       eval harness home (corpus fetched, not vendored)
scripts/    dev/ops scripts (migrate, ...)
docs/       approved baseline documentation
.github/    CI workflow
```

## Quick start

Prerequisites: Python 3.12, Node 20+, Docker (for the full stack).

```bash
make install      # create backend venv, install backend + frontend deps
make lint         # ruff (backend) + eslint (frontend)
make typecheck    # mypy (backend) + tsc (frontend)
make test         # pytest (backend)
make up           # docker compose: postgres + redis + backend + frontend
make migrate      # alembic upgrade head
```

Copy `.env.example` to `.env` and fill in values before running the stack. **Never commit
`.env` or real secrets** — see `.env.example` for guidance.

## Contributing conventions

- One task = one commit (see [docs/AI_DEVELOPMENT_GUIDE.md](docs/AI_DEVELOPMENT_GUIDE.md)).
- Lint, type-check, and tests must pass (CI enforces this).
- No hardcoded secrets, URLs, or credentials.
