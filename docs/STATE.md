# Current Project State

**Updated:** 2026-07-10 (reconciled with ARCHITECTURE_v2.3 + approved review)

## Resolved Decisions (v1 / MVP)
- **Tenancy:** Single-tenant (multi-tenancy deferred — TASK-014).
- **Authentication:** Deferred until after the core scanning MVP (TASK-013). Matches ARCHITECTURE §1 ("no login/auth in v1").
- **Deployment target:** Docker Compose (K8s manifests remain reference/future).
- **Code intelligence:** GitNexus, Path A (GitNexus-only) working default; Path B pending TASK-002 spike (TASK-003D open).
- **MVP scope:** Python only · Ollama + one cloud provider · Triage + Fix agents · SARIF/JSON export.

## Completed (baseline, TASK-001 … TASK-012)
- Backend initialized
- Docker Compose
- PostgreSQL configured
- Redis configured
- Health endpoint

> Note: an earlier baseline entry listed "JWT authentication" as complete. Per the auth-deferral
> decision (TASK-013D), authentication is **not** part of MVP scope. Any JWT scaffold from early
> work is **parked and unenforced**; its actual code state must be verified before TASK-013 is
> scheduled. It is not counted as delivered MVP functionality.

## In Progress
- ZIP upload module (TASK-130)

## Pending (next up — MVP critical path)
- Evaluation harness (TASK-020a/b/c, TASK-021)
- GitNexus `--pdg` spike (TASK-002 → TASK-003D)
- Testing + Alembic migration conventions (TASK-023, TASK-024)
- GitNexus integration (TASK-150/151)
- Interprocedural Taint Engine (TASK-210a–d …)
- AI Triage + Fix Agents (TASK-320, TASK-330)
- Cost tracking + provider config (TASK-430, TASK-360a/b)

## Deferred beyond MVP
Authentication, multi-tenancy, Hunter agent, JS/TS/HTML, cloud providers 3–9, PDF export,
full observability (tracing/metrics), webhook/git ingestion, CI/CD gating, SCA scanner,
gated skill-learning loop. See TASK_BACKLOG.md → "Post-MVP / Deferred".

## Known Issues
- GitNexus PolyForm-NC license not yet cleared (TASK-001D) — blocks commercial use.
- `docs/SECURITY.md` and `docs/API_SPEC.md` not yet authored (TASK-011R, TASK-012R).

## Current Branch
main

## Last Completed Task
TASK-012 (baseline). Documentation reconciliation TASK-010R / TASK-010S applied 2026-07-10.
