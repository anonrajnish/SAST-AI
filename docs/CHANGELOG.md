# CHANGELOG.md

All notable **documentation** changes. This project logs doc changes here; application code
is tracked separately in git history.

Format loosely follows Keep a Changelog. Dates are ISO‑8601.

---

## [Unreleased] — 2026-07-10

Documentation update applying the **approved Principal‑Architect review** of the task backlog
and the **MVP scope decisions**. No application code changed. Architecture (v2.3) was left
unchanged (one possible minor §9 enum edit is flagged, not applied — TASK‑595).

### Scope decisions recorded
- **Single‑tenant** MVP (multi‑tenancy deferred).
- **Authentication deferred** until after the core scanning MVP (aligns with ARCHITECTURE §1).
- **Docker Compose** confirmed as the v1 deployment target.
- **MVP reduced to:** Python only · Ollama + one cloud provider · Triage + Fix agents ·
  SARIF/JSON export.

### `docs/AI_DEVELOPMENT_GUIDE.md`
- Fixed source‑of‑truth reference `docs/Architecture.md` → `docs/ARCHITECTURE_v2.3.md` (canonical).
- Aligned backend Python version `3.13+` → `3.12` to match the architecture (avoids editing architecture).
- Annotated `API_SPEC.md` / `SECURITY.md` as to‑be‑authored (TASK‑012R / TASK‑011R).
- Added a pointer that MVP scope and resolved decisions live in `TASK_BACKLOG.md` / `STATE.md`.

### `docs/TASK_BACKLOG.md` (v1.0 → v1.1)
- **Added** an MVP Scope section and a Decision Log (TASK‑013D/014D/015D resolved; 001D/003D/016D open).
- **Split oversized tasks** (numbers preserved via suffixes):
  - `020` → `020a` corpus · `020b` runner · `020c` metrics reporter.
  - `210` → `210a` traversal · `210b` arg↔param · `210c` returns · `210d` recursion/summaries.
  - `260` → `260a` Python (MVP); `260b/c/d` JS/TS/HTML (deferred).
  - `360` → `360a` router+Ollama · `360b` one cloud (MVP); `360c` providers 3–9 (deferred).
  - `420` → `420a` test/model‑list · `420b` select/persist.
  - `140` → `140a` isolation‑tier spike · `140b` implementation.
  - `180` → `180a` upload/trigger · `180b` results/trace viewer.
  - `450` → results filters + SARIF/JSON (MVP); PDF export split out as `451` (deferred).
- **Moved security controls to ship with their feature:**
  - Fail‑closed KEK handling moved from `411` into `031` (where the KEK is first read).
  - SSRF guard (`421`) implemented **inside** provider‑test task `420a`.
  - `llm_usage` partition scheme moved into table‑creation task `430` (retro‑partitioning is costly).
  - Idempotency (`521`) moved to Phase 1 with the trigger endpoints.
  - Webhook HMAC folded into a single webhook‑ingestion task (`520`, Post‑MVP) instead of a separate late task.
- **Moved earlier:** pagination convention (`460`) and structured logging (`113`) to Phase 1.
- **Merged duplicates:** `520`/`521` idempotency overlap resolved (520 = webhook HMAC+idempotency, 521 = trigger idempotency); clarified `560` (deterministic) vs Triage agent reachability boundary.
- **Added missing tasks:** `023` testing/CI convention · `024` Alembic baseline · `033` cosign image verification · `112` API middleware (rate‑limit/headers/CORS/TLS) · `113` structured logging · `121` scan cancellation · `322` agent‑config surface. Git‑clone ingestion added as `532` (Post‑MVP).
- **Deferred beyond MVP** (IDs preserved, consolidated list): `013` auth, `014` tenancy, `350` Hunter, `260b/c/d`, `360c`, `451` PDF, `570` full observability, `280` SCA, `520` webhook ingestion, `532` git ingestion, `530` CI/CD gating, Phase 4b learning loop.
- **Dependency corrections:** `110` no longer blocked by auth/tenancy; `290` (skill authoring) no longer hard‑blocked by `021`.
- **Updated** milestones (M4 = MVP complete), the risk→task map, and the "first two weeks" list.
- **Preserved** deterministic‑first philosophy and the GitNexus architecture unchanged.

### `docs/STATE.md`
- Corrected current branch `feature/upload-api` → `main`.
- Added a Resolved Decisions section (tenancy, auth, deployment, Path A, MVP scope).
- Reconciled the stale "JWT authentication complete" entry: authentication is out of MVP scope,
  any JWT scaffold is parked/unenforced and its code state must be verified before TASK‑013.
- Refreshed Pending list to the MVP critical path; added a Deferred‑beyond‑MVP summary.
- Recorded known issues: GitNexus license (TASK‑001D), missing SECURITY.md/API_SPEC.md.

### `docs/CHANGELOG.md`
- New file (this document).

### Not changed
- `docs/ARCHITECTURE_v2.3.md` — unchanged (deliberately). Any `findings.confidence` enum change
  (TASK‑595) will be raised before editing architecture.
- `docs/PROJECT_PLAN.md` — unchanged; the backlog remains its execution companion.
- No application code was written or modified.
