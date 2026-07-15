# CHANGELOG.md

All notable **documentation** changes. This project logs doc changes here; application code
is tracked separately in git history.

Format loosely follows Keep a Changelog. Dates are ISO‑8601.

---

## [Unreleased] — 2026-07-15 (version roadmap finalized)

Planning-doc update recording the **finalized version roadmap** and **deferring OWASP Benchmark,
Juliet, and the external corpus fetcher to v2.0**. No application code changed; no architecture
doc changed (only planning docs + STATE.md per the DoD).

### Roadmap recorded
- **v1.0 (MVP):** Python (backend) + **Web** (JavaScript/TypeScript/HTML as one capability).
- **v2.0:** Java, C/C++ + **OWASP Benchmark** (Java) & **NIST Juliet** (C/C++) corpora + **external corpus fetcher**.
- **v3.0:** Go, C#.

### `docs/TASK_BACKLOG.md` (v1.2 → v1.3)
- Added a **Version roadmap** table; MVP scope reframed to **Python + Web**.
- Phase 2: **consolidated TASK‑260b/c/d (JS/TS/HTML) into a single TASK‑260b "Web"** capability;
  updated the exit gate, milestone **M2**, and the risk map accordingly.
- Post‑MVP/Deferred: versioned the language tasks — **TASK‑260e Java, 260f C/C++ (v2.0)**;
  **TASK‑260g Go, 260h C# (v3.0; was ".NET")**; and added **TASK‑020a‑F** (external fetcher),
  **TASK‑020a‑J** (OWASP Benchmark acquisition), **TASK‑020a‑C** (Juliet acquisition) — all
  **v2.0**, i.e. the remaining TASK‑020a external‑corpus work deferred out of the MVP.
- TASK‑020a row + note: MVP corpora = curated **Python + Web** (committed); external corpora → v2.0.

### `docs/PROJECT_PLAN.md` (rev 4)
- G0.2 corpora reframed to the MVP scope (Python + Web, curated/committed); OWASP/Juliet + fetcher → v2.0.
- Phase 2 capability breadth + exit gate + risk #5 updated to Python → Web; v2.0/v3.0 future.

### `docs/STATE.md`
- Resolved Decisions: replaced the language-scope bullet with the **finalized version roadmap**;
  MVP scope line now Python + Web.
- Pending: next MVP TASK‑020a step = author the curated **Web** corpus; external corpora → v2.0.
- Deferred‑beyond‑MVP re-bucketed into v2.0 / v3.0.

### Not changed
- No application code/implementation. No architecture-doc edits (instruction: planning docs only;
  STATE.md updated per the DoD).

---

## [Unreleased] — 2026-07-15

Documentation reconciliation of the **multi‑language project vision** (approved decision).
No application code changed. This **supersedes the language‑scope** of the 2026‑07‑10
"MVP reduced to: Python only" decision below — all other 2026‑07‑10 scope decisions
(single‑tenant, auth deferred, Docker Compose, Triage+Fix, SARIF/JSON) stand.

### Approved decisions recorded
- The platform is a **modular, multi‑language** SAST engine.
- **MVP languages:** Python (backend), JavaScript, TypeScript, HTML.
- **Future roadmap:** Java, C/C++, Go, .NET, and additional languages.
- **Evaluation harness is language‑agnostic.**
- Planned **future** corpora: **OWASP Benchmark (Java)**, **NIST Juliet (C/C++)** — not in the MVP.
- Each language eventually gets: deterministic analysis, language‑specific rulepacks,
  evaluation corpora, AI‑assisted triage, AI‑assisted remediation.

### `docs/ARCHITECTURE_v2.3.md`
- Added a dated **multi‑language amendment** note near the top.
- §1: added a **Language roadmap** note (Java/C‑C++/Go/.NET future) after the v1 language list.
- §12 Future Enhancements: added **Additional language support** and **Evaluation corpora
  (future languages)** rows. Architecture was already multi‑language (Python + JS/TS/HTML) —
  no schema or component change.

### `docs/PROJECT_PLAN.md` (rev 3)
- G0.2: reframed corpora as **MVP‑language** known‑answer corpora; harness **language‑agnostic**;
  OWASP Benchmark (Java) / Juliet (C/C++) marked **future**.
- Phase 2 step 6 + exit gate: JS/TS/HTML are **in the MVP** (Python first, then breadth);
  future languages listed. Risk #5 reframed (all four MVP languages in scope; per‑language targets).

### `docs/TASK_BACKLOG.md` (v1.1 → v1.2)
- MVP Scope: **Language: Python only → Languages: Python, JS, TS, HTML** (modular multi‑language).
- Phase 2: **moved TASK‑260b (JS), 260c (TS), 260d (HTML) from Post‑MVP/Deferred into the MVP**;
  updated the Phase 2 exit gate, milestone **M2**, and the risk map to span MVP languages;
  extended TASK‑290 agent‑skill authoring to JS/TS.
- Post‑MVP/Deferred: replaced the JS/TS/HTML rows with **future‑language roadmap** rows —
  **TASK‑260e Java (OWASP Benchmark), 260f C/C++ (Juliet), 260g Go, 260h .NET**.
- "First two weeks": harness noted as language‑agnostic (MVP corpora Python/JS/TS/HTML).

### `docs/STATE.md`
- Added a **Language scope** resolved decision; MVP scope line now Python + JS/TS/HTML.
- Deferred‑beyond‑MVP: JS/TS/HTML removed (now MVP); future languages + their corpora added.
- Known Issues: flagged the **implementation follow‑up** — the harness `Language` enum
  (Python‑only) and `eval/corpus_registry.json` (labels OWASP/Juliet as `python`) must be
  reconciled to the language‑agnostic decision; **no code changed** in this doc pass.

### `docs/AI_DEVELOPMENT_GUIDE.md`
- §2 source‑of‑truth pointer: **Python‑only → Python + JS/TS/HTML** (multi‑language; roadmap noted).

### Not changed (implementation — deliberately)
- `eval/harness/models.py` `Language` enum and `eval/corpus_registry.json` left unchanged;
  reconciling them is a **follow‑up backlog task** (no implementation touched here).

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
