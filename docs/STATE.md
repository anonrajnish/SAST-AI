# Current Project State

**Updated:** 2026-07-10 (reconciled with ARCHITECTURE_v2.3 + approved review)

## Resolved Decisions (v1 / MVP)
- **Tenancy:** Single-tenant (multi-tenancy deferred — TASK-014).
- **Authentication:** Deferred until after the core scanning MVP (TASK-013). Matches ARCHITECTURE §1 ("no login/auth in v1").
- **Deployment target:** Docker Compose (K8s manifests remain reference/future).
- **Code intelligence:** GitNexus, Path A (GitNexus-only) working default; Path B pending TASK-002 spike (TASK-003D open).
- **GitNexus licensing (TASK-001D — RESOLVED 2026-07-10):** This is a personal, non-commercial, public GitHub project; GitNexus is used under its PolyForm Noncommercial license, and no commercial use, SaaS offering, paid product, or enterprise deployment is planned at this stage.
  - **Decision:** GitNexus is approved for the current personal/non-commercial MVP.
  - **Future Action:** If this project is ever commercialized (SaaS, enterprise deployment, paid product, or proprietary distribution), the GitNexus license must be re-evaluated and either: obtain an appropriate commercial license, or replace GitNexus with an alternative implementation.
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

## Completed — Engineering Foundation (validated 2026-07-10)
Phase-0 engineering skeleton built and **runtime-validated** on branch
`feature/engineering-foundation` (awaiting human review before merge; not merged to main):

- **Backend startup validated** — FastAPI app boots via uvicorn (app factory + config wiring).
- **Health endpoints validated** — `GET /api/v1/health` and `/api/v1/health/live` return HTTP 200.
- **Readiness behaves correctly without PostgreSQL** — `/api/v1/health/ready` fails closed with
  HTTP 503 `{"status":"not_ready","database":"unavailable"}` when the database is unavailable.
- **OpenAPI verified** — schema exposes only the three health routes; no business endpoints leaked.
- **Structured logging verified** — JSON/structlog output emitted; the readiness failure logged as
  `readiness_check_failed` with no secret/DSN leakage (AI_DEVELOPMENT_GUIDE §11).

> Also green offline: backend ruff + mypy + pytest (99% coverage) and the Alembic empty baseline.
> **Docker Compose runtime validated (2026-07-10):** all four services (postgres, redis, backend,
> frontend) start; postgres + redis report healthy; `GET /api/v1/health`, `/health/live`, and
> `/health/ready` all return HTTP 200; backend↔PostgreSQL connectivity confirmed over the compose
> network; frontend served by `vite preview` loads; stack tears down cleanly. Two engineering fixes
> applied on this branch: the Makefile now passes `--env-file $(CURDIR)/.env` to every Compose
> command (root `.env` was previously not picked up for `${POSTGRES_PASSWORD}` interpolation), and a
> root `.dockerignore` was added (build context shrank from ~300 MB to <200 kB).

## Completed — Evaluation Harness foundation (TASK-020a, Slice 1 — 2026-07-10)
First slice of TASK-020a on branch `feature/task-020a-evaluation-foundation` (awaiting human
review before merge; not merged to main). Establishes the **ground-truth data contract** only —
no dataset downloads, no runner, no metrics, no AI logic (those remain in TASK-020a later
slices / 020b / 020c).

- **Typed models** (`eval/harness/models.py`, Pydantic v2, frozen, `extra="forbid"`):
  `SourceLocation`, `GroundTruthLabel`, `LabelSet`, `CorpusDescriptor` (with optional
  `checksum` for future dataset integrity), `CorpusRegistry`; enums `Language` (Python only),
  `CorpusKind` (`owasp_benchmark`/`nist_juliet`/`project_curated`), `Verdict`.
- **Read-only loader** (`eval/harness/loader.py`): `load_label_set`, `load_corpus_registry`,
  `load_labels_for_corpus`, `resolve_within_directory`; relative-path/anti-traversal validation;
  typed errors in `eval/harness/errors.py`. No network, no execution, no `backend/app` coupling.
- **Corpus registry** (`eval/corpus_registry.json`): descriptors for the three MVP Python
  corpora — descriptors only, corpus data still fetched (never vendored) in a later slice.
- **DoD gates green** (foundation toolchain via root `.venv`): `ruff check eval/harness` clean;
  `mypy --strict eval/harness` clean; `pytest eval/harness/tests` = 34 passed. Manual
  validation: loader smoke-run over the shipped registry + a sample label set succeeded.

## Completed — Evaluation Harness label-integrity validator (TASK-020a, Slice 2 — 2026-07-10)
Second slice of TASK-020a on branch `feature/task-020a-evaluation-foundation` (awaiting human
review before merge; not merged to main). Adds referential-integrity checking of labels against
a corpus tree. Still no dataset downloads, no rule/benchmark execution, no metrics, no AI logic.

- **Validator** (`eval/harness/validator.py`): `validate_label_set_against_corpus(label_set,
  corpus_root) -> IntegrityReport`. Read-only — files are stat-ed and their lines stream-counted,
  never imported or executed. Reuses `resolve_within_directory` for path-safety.
- **Structured results**: `IntegrityReport` (`ok`, `n_issues`) and `IntegrityIssue`
  (`kind`, `detail`, optional `label_id`/`file`/`line`); `IntegrityIssueKind` covers
  `invalid_corpus_root`, `missing_file`, `not_a_file`, `line_out_of_range`, `undecodable_file`,
  `path_escape`. An unusable corpus root is **reported as an issue, not raised** (per review
  refinement), so callers always get one inspectable report; `errors.py` was left unchanged.
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean; `pytest eval/harness/tests` = 44 passed (10 new). Manual validation: validator smoke-run
  over the fixture corpus (ok), an invalid root (reported), and a mismatched root (structured
  missing-file issues) all behaved as designed.

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
- ~~GitNexus PolyForm-NC license not yet cleared (TASK-001D)~~ — **RESOLVED 2026-07-10:** approved for the personal/non-commercial MVP; re-evaluate only if the project is ever commercialized (see Resolved Decisions → GitNexus licensing).
- `docs/SECURITY.md` and `docs/API_SPEC.md` not yet authored (TASK-011R, TASK-012R).

## Current Branch
feature/task-020a-evaluation-foundation (TASK-020a Slice 2; awaiting human review before merge)

## Last Completed Task
TASK-020a Slice 2 — evaluation-harness label-integrity validator (`validator.py` +
`IntegrityReport`/`IntegrityIssue` + tests + fixture corpus) on
`feature/task-020a-evaluation-foundation` (2026-07-10); DoD gates green; awaiting human review
before merge. Prior: TASK-020a Slice 1 — ground-truth contract (models + loader + corpus registry).
Prior: Engineering Foundation built and runtime-validated (2026-07-10) on
`feature/engineering-foundation`. Earlier: TASK-010R / TASK-010S doc reconciliation; TASK-012 baseline.
