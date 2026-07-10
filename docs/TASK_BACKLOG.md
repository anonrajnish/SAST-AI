# TASK_BACKLOG.md

**Product:** AI‑Powered SAST Platform
**Companion to:** [ARCHITECTURE_v2.3.md](ARCHITECTURE_v2.3.md), [PROJECT_PLAN.md](PROJECT_PLAN.md), [AI_DEVELOPMENT_GUIDE.md](AI_DEVELOPMENT_GUIDE.md)
**Version:** 1.1 (post‑review; MVP scope applied)
**Date:** 2026-07-10
**Status:** Living document — the single ordered source of "what to build next."

> Derived from the approved architecture (v2.3) and phased plan, updated per the approved
> Principal‑Architect review: oversized tasks split, security controls moved to ship with
> the features they protect, MVP scope reduced, duplicates merged, missing tasks added.
> Task numbers are **preserved**; splits use suffixes (`020a/b/c`), no completed/existing
> task was renumbered. No requirements were invented.
>
> **Per the [AI_DEVELOPMENT_GUIDE](AI_DEVELOPMENT_GUIDE.md): implement ONLY the requested
> task, one task = one commit, then STOP.** This file defines and orders work only.

---

## MVP Scope (v1)

The MVP is the **core deterministic scanning engine, end to end**, single‑tenant, run via
Docker Compose. Deterministic‑first philosophy and the GitNexus code‑intelligence
architecture are **unchanged**.

**In MVP:**
- **Language:** Python only.
- **LLM providers:** Ollama (local, first‑class) **+ one** cloud provider.
- **Agents:** Triage + Fix only.
- **Delivery:** SARIF + JSON export; results UI with trace viewer.
- **Deployment:** Docker Compose, single‑tenant.
- **Security controls ship *with* the feature they protect** (not in a later hardening phase).

**Deferred beyond MVP** (see the consolidated list at the end): authentication, multi‑tenancy,
Hunter agent, JS/TS/HTML, cloud providers 3–9, PDF export, full observability (tracing/metrics),
webhook/git ingestion channels, CI/CD gating, SCA scanner, the gated skill‑learning loop.

---

## Decision Log (resolved Gate‑0 DECISION tasks)

| ID | Decision | Resolution (2026‑07‑10) |
|----|----------|-------------------------|
| TASK‑013D | Auth in v1? | **DEFERRED** until after the core scanning MVP. Aligns with ARCHITECTURE §1 ("no login/auth in v1"). → TASK‑013 is Post‑MVP. |
| TASK‑014D | Tenancy model | **SINGLE‑TENANT** for v1. Multi‑tenancy (TASK‑014) is Post‑MVP. No `tenant_id` in the MVP schema. |
| TASK‑015D | Deployment target | **Docker Compose** for v1. K8s manifests under `infra/k8s/` remain reference/future. |
| TASK‑001D | GitNexus license | **RESOLVED (2026‑07‑10)** — Approved for the current personal/non‑commercial MVP under PolyForm Noncommercial. **Future action:** if ever commercialized (SaaS, enterprise deployment, paid product, or proprietary distribution), re‑evaluate the GitNexus license — obtain an appropriate commercial license, or replace GitNexus with an alternative implementation. |
| TASK‑003D | Path A vs B | **OPEN** — pending the TASK‑002 spike. Path A (GitNexus‑only) is the working default. |
| TASK‑016D | Fix‑agent patch policy | **OPEN** — advisory‑only vs auto‑apply; decide before TASK‑330. |

---

## How to use this backlog

1. Work **top‑down within the current phase**; do not pull future‑phase or Post‑MVP tasks early.
2. A task is **startable** only when every `Depends on` task is `DONE`.
3. **BLOCKED / DECISION tasks gate the phase** — resolve them first.
4. Update `STATE.md` (`Last Completed Task`) after each merged task.
5. **Security controls are not separate later tasks** — each feature task owns its control
   (e.g., the SSRF guard lives inside the provider‑test task, HMAC inside the webhook task).

### Legends
- **Status:** `TODO` · `IN‑PROGRESS` · `BLOCKED` · `DONE` · `DECISION` · `⏭ POST‑MVP`
- **Priority:** `P0` blocker · `P1` critical path · `P2` important · `P3` nice‑to‑have
- **Effort:** `S` ≤1d · `M` 2–4d · `L` ~1wk · `XL` multi‑week/R&D
- **MVP:** ✅ in MVP · ⏭ deferred beyond MVP

---

## Baseline — already completed (STATE.md, TASK‑001 … TASK‑012)

Recorded for continuity; **not re‑opened**. Backend scaffold, Docker Compose, PostgreSQL,
Redis, health endpoint. (The prior "JWT authentication" baseline entry is reconciled by the
auth‑deferral decision — see STATE.md and TASK‑013.) ZIP‑upload module was `IN‑PROGRESS` and
continues as **TASK‑130** in Phase 1.

---

## Phase 0 — Foundations, Gates & Decisions (blocks everything) — ✅ MVP

### Documentation reconciliation & governance — [REVIEW]

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑010R | Reconcile source‑of‑truth doc set (filenames + Python 3.12) | **DONE** | P0 | S | — |
| TASK‑010S | Repair `STATE.md` to reflect reality + decisions | **DONE** | P0 | S | TASK‑010R |
| TASK‑011R | Author `docs/SECURITY.md` | TODO | P0 | M | TASK‑010R |
| TASK‑012R | Author `docs/API_SPEC.md` (OpenAPI, MVP surface only) | TODO | P1 | M | TASK‑010R |

> TASK‑010R/010S applied in this documentation pass (guide filename fix, Python 3.12, STATE rewrite).

### Gate‑0 decisions — resolved above (see Decision Log)

TASK‑013D, TASK‑014D, TASK‑015D, TASK‑001D **resolved**. TASK‑003D, TASK‑016D remain **OPEN**.

### Gate‑0 build & convention tasks

| ID | Title | Status | Pri | Effort | MVP | Depends on |
|----|-------|--------|-----|--------|-----|-----------|
| TASK‑002 | GitNexus `--pdg` spike on 3–5 Python repos | TODO | P0 | L | ✅ | TASK‑001D |
| TASK‑020a | Eval corpus acquisition + labeling (OWASP Bench, Juliet, curated internal) | TODO | P0 | L | ✅ | TASK‑010R |
| TASK‑020b | Eval runner (execute rules over corpus) | TODO | P0 | M | ✅ | TASK‑020a |
| TASK‑020c | Metrics reporter: precision/recall/F1 **per rule & per language** | TODO | P0 | M | ✅ | TASK‑020b |
| TASK‑021 | Callable eval interface (per‑candidate deltas vs active version) | TODO | P0 | M | ✅ | TASK‑020c |
| TASK‑022 | LLM‑in‑the‑loop threat model (prompt injection, G0.4) | TODO | P0 | M | ✅ | TASK‑011R |
| TASK‑023 | **[REVIEW +NEW]** Testing & CI coverage‑gate convention (unit/integration/negative) | TODO | P0 | S | ✅ | — |
| TASK‑024 | **[REVIEW +NEW]** Alembic baseline migration + migration convention | TODO | P0 | S | ✅ | — |
| TASK‑030 | Infra bring‑up: repos, CI, Postgres/Redis/GitNexus containers (Compose) | TODO | P1 | M | ✅ | TASK‑015D |
| TASK‑031 | KEK secret‑injection **+ fail‑closed KEK handling** (moved from 411) | TODO | P1 | M | ✅ | TASK‑030 |
| TASK‑032 | Remove default/hardcoded credentials from `.env.example` & compose | TODO | P1 | S | ✅ | TASK‑030 |
| TASK‑033 | **[REVIEW +NEW]** GitNexus image signature verification (cosign) + pinned tag | TODO | P2 | S | ✅ | TASK‑030 |

**TASK‑020a/b/c — Eval harness (split from TASK‑020).** The measuring instrument; MVP targets Python.
**TASK‑021 — Callable interface.** Library/service call returning precision/recall **deltas** vs. the active version (needed later by the deferred learning loop; the interface is built now so it isn't refactored).
**TASK‑031 — now also owns fail‑closed KEK.** `from_secret()` must reject a short/invalid KEK (no silent `ljust` padding). AES‑GCM AAD + rotation remain in TASK‑411 (Phase 4, with custody).

**Phase 0 exit:** license resolved (001D), Path A/B spike done (002→003D), eval harness
prints a Python baseline (020a‑c/021), injection defense designed (022), testing + migration
conventions set (023/024), docs reconciled (010R/010S). Auth/tenancy/deploy **decided** (see log).

---

## Phase 1 — Walking Skeleton — ✅ MVP

> One vuln class (SQL injection), Python, full pipeline end to end. **Cross‑cutting API
> conventions and their security controls are established here, not retrofitted later.**

| ID | Title | Status | Pri | Effort | MVP | Depends on |
|----|-------|--------|-----|--------|-----|-----------|
| TASK‑110 | Project & Folder CRUD (models, migrations, API, schemas) | TODO | P1 | M | ✅ | TASK‑024 |
| TASK‑112 | **[REVIEW +NEW]** API middleware: rate limiting, security headers, CORS, TLS (nginx) | TODO | P1 | M | ✅ | TASK‑030 |
| TASK‑113 | **[REVIEW +NEW]** Structured logging convention (no secrets/PII; req/project/scan IDs) | TODO | P1 | S | ✅ | TASK‑030 |
| TASK‑120 | Scan orchestrator + Celery job lifecycle (skeleton) | TODO | P1 | M | ✅ | TASK‑110 |
| TASK‑121 | Scan cancellation (`DELETE /scans/{id}`, `cancelled` status) | TODO | P3 | S | ✅ | TASK‑120 |
| TASK‑130 | **ZIP upload module** (continues in‑progress work) | IN‑PROGRESS | P1 | M | ✅ | TASK‑120 |
| TASK‑131 | ZIP hardening: slip/bomb/traversal/symlink + ClamAV + limits | TODO | P0 | M | ✅ | TASK‑130 |
| TASK‑140a | Sandbox isolation‑tier spike/decision (gVisor/Kata/microVM vs namespaces) | TODO | P0 | M | ✅ | TASK‑120 |
| TASK‑140b | Per‑scan sandbox implementation (cgroups, seccomp, tmpfs, drop caps, egress allowlist) | TODO | P0 | L | ✅ | TASK‑140a |
| TASK‑150 | GitNexus runner: `gitnexus analyze --pdg` per scan + `.gitnexus/` lifecycle | TODO | P1 | M | ✅ | TASK‑003D, TASK‑140b |
| TASK‑151 | `graph_facade` unified read API over LadybugDB (+ `json_exporter` snapshot) | TODO | P1 | M | ✅ | TASK‑150 |
| TASK‑160 | Minimal intra‑procedural taint check (routes→orm, SQLi/Python) | TODO | P1 | M | ✅ | TASK‑151 |
| TASK‑161 | Candidate emitter + `candidates` table persistence | TODO | P1 | S | ✅ | TASK‑160 |
| TASK‑170 | Findings storage (SARIF) + `findings` table | TODO | P1 | M | ✅ | TASK‑161 |
| TASK‑460 | Pagination convention on all list endpoints (moved earlier from Phase 4) | TODO | P2 | S | ✅ | TASK‑170 |
| TASK‑521 | Idempotency keys on `POST /scans/trigger` (upload/REST triggers) | TODO | P1 | S | ✅ | TASK‑120 |
| TASK‑180a | Frontend: upload + scan trigger flow | TODO | P1 | M | ✅ | TASK‑170 |
| TASK‑180b | Frontend: results list + trace viewer | TODO | P1 | M | ✅ | TASK‑180a |
| TASK‑190 | Skeleton scored by the eval harness end‑to‑end | TODO | P1 | S | ✅ | TASK‑020c, TASK‑180b |

> **Note:** TASK‑110 no longer depends on auth/tenancy (single‑tenant, auth deferred). It depends
> only on the migration convention (TASK‑024).

**Phase 1 exit:** a real SQLi finding on a tiny Python repo, visible in the portal, measured by the harness; API conventions (rate‑limit, headers, logging, pagination, idempotency) in place.

---

## Phase 2 — Interprocedural Taint Engine ⚠ critical path — ✅ MVP (Python)

> **The product.** Build breadth‑first; **check the eval harness after each capability.** The
> hard cross‑function work (TASK‑210) is split so each increment is independently gatable.

| ID | Title | Status | Pri | Effort | MVP | Depends on |
|----|-------|--------|-----|--------|-----|-----------|
| TASK‑210a | Call‑graph worklist traversal (walk GitNexus CALLS) | TODO | P1 | L | ✅ | Phase 1 |
| TASK‑210b | Arg↔param binding across boundaries | TODO | P1 | L | ✅ | TASK‑210a |
| TASK‑210c | Return‑value propagation | TODO | P1 | M | ✅ | TASK‑210b |
| TASK‑210d | Recursion/cycle handling + function summaries/caching | TODO | P1 | L | ✅ | TASK‑210c |
| TASK‑220 | Field sensitivity (`obj.a` tainted vs `obj.b` clean) | TODO | P1 | L | ✅ | TASK‑210d |
| TASK‑230 | Context‑sensitive sanitizer semantics (SQL≠XSS) | TODO | P1 | L | ✅ | TASK‑220 |
| TASK‑240 | Source/sink modeling: seed `routes`/`orm` + rulepacks, top Python CWEs | TODO | P1 | L | ✅ | TASK‑230 |
| TASK‑241 | Rulepack engine + `rulepacks` table + YAML validation endpoint | TODO | P1 | M | ✅ | TASK‑240 |
| TASK‑250 | Path materialization → concrete, explainable source→sink trace | TODO | P1 | L | ✅ | TASK‑240 |
| TASK‑260a | **Python** hardening to precision/recall targets | TODO | P1 | XL | ✅ | TASK‑250 |
| TASK‑270 | Pattern matcher + secret scanner (cheap, high‑value) | TODO | P2 | M | ✅ | Phase 1 |
| TASK‑290 | Agent‑skills authoring: `common` + `python` (+ Django/Flask) — writing, parallel | TODO | P2 | L | ✅ | — |

**Top Python CWEs (TASK‑240):** SQLi, XSS, command injection, path traversal, SSRF, deserialization.
**TASK‑290 dependency relaxed:** authoring is writing and starts immediately; only *eval‑checking* a skill needs TASK‑021.

**Phase 2 exit gate:** agreed precision/recall targets met on the eval corpus for the top CWEs in **Python**. (JS/TS/HTML deferred — see Post‑MVP.)

---

## Phase 3 — AI Agent Layer (Triage + Fix) — ✅ MVP (overlaps Phase 2 back half)

> Starts as soon as candidates flow. **Triage first.** Skills are **LIVE but STATIC**
> (hand‑authored, versioned). Hunter agent and the automated learning loop are Post‑MVP.

| ID | Title | Status | Pri | Effort | MVP | Depends on |
|----|-------|--------|-----|--------|-----|-----------|
| TASK‑310 | Agent orchestrator + MCP client over GitNexus | TODO | P1 | L | ✅ | TASK‑210a |
| TASK‑311 | **[REVIEW]** Concurrent, budget‑bounded agent pipeline (enforce per‑scan cap) | TODO | P1 | L | ✅ | TASK‑310 |
| TASK‑312 | **[REVIEW]** Candidate dedup/pre‑filter before the LLM stage | TODO | P1 | M | ✅ | TASK‑161 |
| TASK‑321 | Skill composer/loader/registry (common+python as DATA, not instructions) | TODO | P1 | M | ✅ | TASK‑290 |
| TASK‑320 | Triage agent (kill false positives) | TODO | P1 | L | ✅ | TASK‑310, TASK‑321 |
| TASK‑331 | **[REVIEW]** Strict schema validation of all LLM output (deterministic path required) | TODO | P0 | M | ✅ | TASK‑320 |
| TASK‑340 | **[REVIEW]** Prompt‑injection defense ships **with** Triage + red‑team suite | TODO | P0 | L | ✅ | TASK‑022, TASK‑320 |
| TASK‑330 | Fix agent (patch + severity + CWE) per TASK‑016D | TODO | P1 | L | ✅ | TASK‑320, TASK‑016D |
| TASK‑322 | **[REVIEW +NEW]** Agent config surface (`agent_configs`, `/agents/config`) | TODO | P2 | M | ✅ | TASK‑310 |

**TASK‑311** enforces `COST_PER_SCAN_BUDGET_USD` **inside** the orchestration loop (aborts past cap, preserves partial findings); bounded concurrency; cheap/local model routed to high‑volume Triage.
**TASK‑340** ships with Triage (not after); trace‑required suppression; red‑team corpus in CI.

**Phase 3 exit:** Triage measurably cuts FP rate without dropping TP past threshold; injection tests green; agents compose the correct Python skill.

---

## Phase 4 — Cost, Provider Config, Results UI — ✅ MVP (parallel from Phase 1)

| ID | Title | Status | Pri | Effort | MVP | Depends on |
|----|-------|--------|-----|--------|-----|-----------|
| TASK‑360a | LLM base/router + **Ollama** adapter | TODO | P1 | M | ✅ | TASK‑310 |
| TASK‑360b | **One cloud** provider adapter | TODO | P1 | M | ✅ | TASK‑360a |
| TASK‑410 | Hardened key custody: ciphertext in DB, KEK injected | TODO | P1 | M | ✅ | TASK‑031 |
| TASK‑411 | **[REVIEW]** Crypto hardening: AES‑GCM AAD (bind provider) + key rotation | TODO | P1 | M | ✅ | TASK‑410 |
| TASK‑420a | Provider settings: test‑connection + model‑list | TODO | P1 | M | ✅ | TASK‑410 |
| TASK‑420b | Provider settings: select + persist (Save gated on test+model) | TODO | P1 | M | ✅ | TASK‑420a |
| TASK‑421 | **[REVIEW]** SSRF guard on provider `base_url` (inside 420a) | TODO | P0 | M | ✅ | TASK‑420a |
| TASK‑430 | Cost metering: `usage_meter`, `llm_usage`, computed `cost_usd` **+ partition scheme at table creation** | TODO | P1 | M | ✅ | TASK‑360b |
| TASK‑431 | Price catalog: `model_prices` (YAML seed + UI override) | TODO | P1 | M | ✅ | TASK‑430 |
| TASK‑432 | **[REVIEW]** Cost rollup without lock contention (CONCURRENTLY or incremental) | TODO | P1 | M | ✅ | TASK‑430 |
| TASK‑440 | Usage view: per‑scan/agent/model + portal total | TODO | P2 | M | ✅ | TASK‑431 |
| TASK‑450 | Results UI polish: filters + SARIF/JSON export | TODO | P2 | M | ✅ | TASK‑180b |

> **TASK‑430** now defines the `llm_usage` **partition scheme at creation time** (moved earlier from the Phase‑5 retention task — retro‑partitioning a hot table is costly). Purge/enforcement stays in Phase 5 (TASK‑580).
> **TASK‑421** is not a standalone late task — it is implemented **inside** TASK‑420a (the feature that introduces the outbound call).

**Phase 4 exit:** an analyst configures Ollama or the one cloud provider, picks a model, runs a scan, and sees cost broken down by agent and model. **This closes the MVP.**

---

## Phase 5 — Hardening & Scale (toward GA)

| ID | Title | Status | Pri | Effort | MVP | Depends on |
|----|-------|--------|-----|--------|-----|-----------|
| TASK‑510 | Concurrency/throughput tuning; worker isolation under load | TODO | P1 | L | ⏭ | Phase 2 |
| TASK‑511 | **[REVIEW]** Remove GitNexus single‑service SPOF/bottleneck | TODO | P1 | L | ⏭ | TASK‑150 |
| TASK‑512 | **[REVIEW]** Shared/object‑backed `.gitnexus/` index storage | TODO | P1 | M | ⏭ | TASK‑150 |
| TASK‑540 | Full platform security review (sandbox escape, ZIP bombs, injection, custody) | TODO | P0 | L | ⏭ | Phase 3 |
| TASK‑550 | Incremental re‑index via GitNexus `detect_changes` | TODO | P2 | M | ⏭ | TASK‑150 |
| TASK‑560 | Reachability‑based FP suppression (deterministic; distinct from Triage's agent check) | TODO | P2 | M | ⏭ | TASK‑250 |
| TASK‑580 | **[REVIEW]** Data retention + purge (uses the TASK‑430 partition scheme) | TODO | P1 | M | ⏭ | TASK‑430 |
| TASK‑590 | **[REVIEW]** Backup/DR for Postgres, MinIO, index volume | TODO | P1 | M | ⏭ | TASK‑030 |
| TASK‑595 | **[REVIEW]** Reconcile `findings.confidence` vocabulary with SAST semantics | TODO | P2 | S | ⏭ | TASK‑170 |

> Note: `findings.confidence` reconciliation (TASK‑595) is small; if it forces a schema/enum change,
> that is the **one** place a minor architecture §9 edit may be required — raise before acting.

---

## Phase 6 — Pilot → GA

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑610 | Onboard 1–2 design partners; scan their real Python repos | TODO | P1 | L | Phase 5 |
| TASK‑620 | Measure precision/recall on *their* code; tune rulepacks/prompts | TODO | P1 | L | TASK‑610 |
| TASK‑630 | GA readiness checklist (security review passed, targets met) | TODO | P0 | M | TASK‑540, TASK‑620 |

---

## Post‑MVP / Deferred (consolidated) — ⏭

Preserved IDs; each carries its own security control inline when built.

| ID | Task | Why deferred |
|----|------|-------------|
| TASK‑013 | Authentication + admin role (JWT/OAuth2, RBAC) | Decision TASK‑013D: after core scanning MVP |
| TASK‑014 | Multi‑tenancy scaffolding (`tenant_id`, per‑org isolation) | Decision TASK‑014D: MVP is single‑tenant |
| TASK‑350 | Hunter agent (logic/authz/business‑logic flaws) | Plan: fuzziest/last; Triage delivers core value |
| TASK‑260b | JS language support (engine + rulepacks + eval) | Plan: Python first; weaker JS type resolution |
| TASK‑260c | TS language support | Post‑MVP GA breadth |
| TASK‑260d | HTML support | Post‑MVP GA breadth |
| TASK‑360c | Cloud providers 3–9 (Anthropic/OpenAI/Gemini/Azure/OpenRouter/DeepSeek/GLM/Groq set) | MVP = Ollama + one cloud |
| TASK‑451 | PDF export (SARIF/JSON is the MVP export) | Gold‑plating for MVP |
| TASK‑570 | Full observability stack (Prometheus + OTel tracing + aggregation) | MVP keeps structured logging only (TASK‑113) |
| TASK‑280 | SCA scanner (OSV dependency CVEs) | Not the differentiator; secret/pattern (TASK‑270) stays in MVP |
| TASK‑520 | Webhook ingestion (GitHub/GitLab) **incl. HMAC verification + idempotency** | Input channel beyond the MVP upload path; control ships with it |
| TASK‑532 | Git‑clone ingestion channel (`/folders/{id}/git`) **incl. SSRF/URL guard** | Input channel beyond MVP; control ships with it |
| TASK‑530 | CI/CD gating: PR comments, policy‑as‑code, SARIF into GitHub/GitLab | GA feature, not an MVP blocker |
| Phase 4b | Gated skill‑learning loop (candidate→eval‑gate→approve→promote) | Plan: post‑GA; new attack surface (skill‑poisoning); Team tier |

**Phase 4b tasks retained for later:** TASK‑4b10 `candidate_recorder`, TASK‑4b20 `eval_gate`
(reuses TASK‑021), TASK‑4b30 `promoter`, TASK‑4b40 `LearningQueue` UI, TASK‑4b50 poisoning
safeguards. Security invariants unchanged: agents never write their own skills; skills are DATA;
recall‑lowering candidates auto‑rejected; versioned + reversible.

---

## Milestones (verifiable, not date‑bound)

| Milestone | Definition | Key tasks |
|-----------|-----------|-----------|
| **M0** | Gate 0 passed: license resolved, harness baseline, Path A/B decided, injection defense designed, conventions set, docs reconciled | 001D, 002/003D, 020a‑c/021, 022, 023/024, 010R |
| **M1** | Walking skeleton: one real Python finding, end to end, measured; API conventions in place | 190 |
| **M2** | Taint engine v1: precision/recall targets met on top Python CWEs — *the* milestone | 260a exit gate |
| **M3** | Triage cuts FP rate past threshold; injection tests green | 320, 340, 331 |
| **M4** | Ollama + one cloud provider flow + per‑scan/agent/model cost live — **MVP complete** | 360a/b, 420a/b, 430, 440 |
| **M5** | Security review passed; runs at target concurrency (GA hardening) | 540, 510 |
| **M6** | Pilot success on a partner's real Python repo → GA | 630 |

---

## Risk → mitigating‑task map (PROJECT_PLAN §5 + review)

| Risk | Mitigating tasks |
|------|-----------------|
| Taint engine misses accuracy targets | 020a‑c/021, 160 (narrow slice), 210a‑d + 260a per‑CWE gates |
| Prompt injection via analyzed source | 022, 340, 331 |
| GitNexus PolyForm‑NC license | 001D (+ Path B/permissive fallback) |
| GitNexus PDG insufficient | 002 / 003D spike |
| LLM cost runaway | 311 (budget cap + routing), 430/431 |
| No ground‑truth eval | 020a‑c |
| Sandbox escape / ZIP bomb | 131, 140a/b, 540 |
| SSRF via base_url (+ git URL when built) | 421 (inside 420a); 532 for git ingestion (Post‑MVP) |
| GitNexus single‑service SPOF | 511, 512 (Phase 5) |
| Skill‑poisoning | Phase 4b gated loop only; never auto‑writeback |

---

## Recommended first two weeks (updated)

1. **TASK‑020a/b/c + TASK‑021** — the evaluation harness (Python). Nothing is judgeable without it.
2. **TASK‑002 → TASK‑003D** — the GitNexus `--pdg` spike (decides the Phase‑2 foundation).
3. **TASK‑001D** — **RESOLVED:** GitNexus is approved under PolyForm Noncommercial for this personal, non‑commercial MVP; re‑evaluate the license only if the project is ever commercialized.
4. **TASK‑023 / TASK‑024** — lock the testing + migration conventions before the first model/endpoint.

Decisions on auth, tenancy, and deployment are **already made** (single‑tenant, auth deferred,
Docker Compose) — no longer blockers.

---

*End of TASK_BACKLOG.md v1.1 — definitions and ordering only. No implementation is authorized by this file.*
