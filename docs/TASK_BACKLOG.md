# TASK_BACKLOG.md

**Product:** AI‑Powered SAST Platform
**Companion to:** [ARCHITECTURE_v2.3.md](ARCHITECTURE_v2.3.md), [PROJECT_PLAN.md](PROJECT_PLAN.md), [AI_DEVELOPMENT_GUIDE.md](AI_DEVELOPMENT_GUIDE.md)
**Version:** 1.0
**Date:** 2026-07-09
**Status:** Living document — the single ordered source of "what to build next."

> This backlog is derived directly from the approved architecture (v2.3) and the phased
> project plan, with the architecture‑review feedback folded in as first‑class tasks
> (marked **[REVIEW]**). It does **not** invent requirements. Where the source docs
> conflict, a **DECISION** task captures the open question rather than guessing.
>
> **Per the [AI_DEVELOPMENT_GUIDE](AI_DEVELOPMENT_GUIDE.md): implement ONLY the requested
> task, one task = one commit, then STOP.** This file only defines and orders work; it
> does not authorize implementation.

---

## How to use this backlog

1. Work **top‑down within the current phase**; do not pull future‑phase tasks early.
2. A task is **startable** only when every `Depends on` task is `DONE`.
3. **Blocked / DECISION tasks gate the phase** — resolve them before dependent work.
4. Update `STATE.md` (`Last Completed Task`) after each merged task.

### Status legend
`TODO` · `IN‑PROGRESS` · `BLOCKED` · `DONE` · `DECISION` (needs a human/product call, not code)

### Priority legend
`P0` blocker (nothing dependent can proceed) · `P1` critical path · `P2` important · `P3` nice‑to‑have

### Effort legend
`S` ≤1 day · `M` 2–4 days · `L` ~1 week · `XL` multi‑week / R&D

---

## Baseline — already completed (from STATE.md, TASK‑001 … TASK‑012)

Recorded for continuity; **not re‑opened here**. STATE.md reports these as done:
backend scaffold, Docker Compose, PostgreSQL, Redis, health endpoint, JWT auth (see
**TASK‑013**, which reconciles the auth contradiction the review found). ZIP‑upload
module is `IN‑PROGRESS` (continued as **TASK‑130** in Phase 1).

> ⚠️ **[REVIEW] STATE.md is internally inconsistent** (claims JWT auth complete while
> the architecture §1 says "no auth in v1"; references branch `feature/upload-api` while
> git is on a clean `main`). Reconciled by **TASK‑010R** and **TASK‑013** below.

---

## Phase 0 — Foundations, Gates & Decisions (blocks everything)

> The project plan is explicit: each Gate‑0 item, if skipped, invalidates later work.
> The **DECISION** tasks below must be closed before the dependent build tasks start.

### Documentation reconciliation & governance — **[REVIEW]**

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑010R | Reconcile source‑of‑truth doc set | TODO | P0 | S | — |
| TASK‑011R | Author `docs/SECURITY.md` | TODO | P0 | M | TASK‑010R |
| TASK‑012R | Author `docs/API_SPEC.md` (OpenAPI) | TODO | P1 | M | TASK‑010R |
| TASK‑010S | Rewrite/repair `STATE.md` to reflect reality | TODO | P0 | S | TASK‑010R |

**TASK‑010R — Reconcile source‑of‑truth doc set**
- **Why:** The AI guide names `docs/Architecture.md`, `docs/API_SPEC.md`, `docs/SECURITY.md`
  as sources of truth; the repo has `ARCHITECTURE_v2.3.md` and neither spec doc. The guide
  says Python **3.13+**; the architecture says **3.12**.
- **Acceptance:** Guide's file references match real filenames; one authoritative Python
  version is chosen and consistent across all docs; a short "docs index" lists canonical files.
- **Notes:** Pure documentation. No code.

**TASK‑011R — Author `docs/SECURITY.md`**
- **Why:** It's a named source of truth and this is a security product; it must exist before security‑sensitive code.
- **Acceptance:** Documents the threat model, the key‑custody model (§5.8/§7), the untrusted‑code
  handling model, SSRF/webhook/prompt‑injection controls (cross‑refs TASK‑520, TASK‑140, TASK‑340),
  the auth/tenancy posture (TASK‑013, TASK‑014D), and a secret‑rotation procedure (TASK‑410).

**TASK‑010S — Rewrite/repair `STATE.md`**
- **Acceptance:** `STATE.md` reflects the true branch, the true auth status, and the true
  last‑completed task; no claims that contradict the architecture.

### Gate‑0 decisions (DECISION — product/human calls)

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑001D | **G0.1** GitNexus PolyForm‑NC license clearance | DECISION | P0 | — | — |
| TASK‑003D | **G0.3** Path A vs Path B spike + decision | DECISION | P0 | L | TASK‑002 |
| TASK‑013D | Auth in v1: yes/no — resolve the contradiction | DECISION | P0 | — | TASK‑010R |
| TASK‑014D | Tenancy model: single‑ vs multi‑tenant for v1 | DECISION | P0 | — | — |
| TASK‑015D | Deployment target for v1: Compose vs K8s | DECISION | P1 | — | — |
| TASK‑016D | Fix Agent patch: advisory‑only vs auto‑apply | DECISION | P1 | — | — |

- **TASK‑001D (G0.1):** Outcome = commercial grant (akonlabs), confirmed noncommercial
  deployment, or committed permissive fallback engine. *Start the conversation now — it is a
  calendar dependency outside the team's control.* Blocks any code that hard‑depends on GitNexus.
- **TASK‑003D (G0.3):** Time‑boxed 1‑week spike (**TASK‑002**), then decide. Decides the Phase‑2 foundation.
- **TASK‑013D [REVIEW]:** The custody/settings/skill‑promotion model requires "auth + admin
  role," but §1 says "no auth in v1." Either ship minimal auth in v1 (**TASK‑013**) or explicitly
  descope the security claims to "trusted‑network deployment only." **Cannot be left ambiguous.**
- **TASK‑014D [REVIEW]:** Multi‑tenant pricing tiers (per‑org skills, org quotas) imply a
  tenancy the schema can't express (`api_key_meta.provider` is globally `UNIQUE`; no owner
  columns). Decide now — retrofitting `tenant_id` later touches every table. Feeds **TASK‑014**.

### Gate‑0 build tasks

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑002 | GitNexus `--pdg` spike on 3–5 target repos | TODO | P0 | L | TASK‑001D |
| TASK‑020 | **G0.2** Evaluation harness (OWASP Bench + Juliet + internal corpus) | TODO | P0 | XL | TASK‑010R |
| TASK‑021 | Make eval harness **callable per‑candidate** (library/service API) | TODO | P0 | M | TASK‑020 |
| TASK‑022 | **G0.4** Threat model for LLM‑in‑the‑loop (prompt injection) | TODO | P0 | M | TASK‑011R |
| TASK‑030 | Infra bring‑up: repos, CI, Postgres/Redis/GitNexus containers | TODO | P1 | M | TASK‑003D |
| TASK‑031 | Wire KEK secret‑injection (the §5.8 custody model) | TODO | P1 | M | TASK‑030 |
| TASK‑013 | Minimal auth + admin role (or descope) per TASK‑013D | TODO | P0 | M | TASK‑013D |
| TASK‑014 | Tenancy scaffolding in schema (if multi‑tenant) per TASK‑014D | TODO | P0 | L | TASK‑014D |
| TASK‑032 | Remove default/hardcoded credentials from `.env.example` & compose | TODO | P1 | S | TASK‑030 |

**TASK‑020 — Evaluation harness (the measuring instrument)**
- **Why:** Per the plan, nothing else can be judged without it — it is Phase 0, not an afterthought.
- **Acceptance:** OWASP Benchmark + NIST Juliet + a small curated internal corpus with
  known vulnerable/safe labels; a runner that outputs **precision, recall, F1 per rule and per
  language**; produces a baseline number.
- **Notes:** This is the gate every later phase steers by.

**TASK‑021 — Callable eval harness**
- **Why:** The skill‑learning `eval_gate` (§5.10) must invoke it **on demand against a trial
  skill/rule version** and return precision/recall **deltas vs. the active version** — not just a
  nightly CI job — or it gets refactored later.
- **Acceptance:** A library/service call parameterized by a candidate returns deltas vs. baseline.

**TASK‑022 — LLM‑in‑the‑loop threat model (G0.4)**
- **Why:** The Triage agent *suppresses* findings; injection via analyzed source is the #2 ranked risk.
- **Acceptance:** A written, testable design for data/instruction separation, "ignore in‑code
  instructions," and **trace‑required suppression** (no suppression without a machine‑checkable
  deterministic path). Concrete mechanism, not a property claim. Feeds **TASK‑340** red‑team tests.

**TASK‑032 — Remove default credentials [REVIEW]**
- **Why:** `minioadmin/minioadmin`, `sast_user/sast_pass`, and a placeholder `SECRET_KEY`
  ship in `.env.example`/compose, contradicting the guide's "no hardcoded credentials."
- **Acceptance:** Defaults are generated/injected; `.env.example` contains only non‑secret
  placeholders with clear "generate me" guidance.

**Phase 0 exit:** license path chosen (TASK‑001D), harness prints a baseline (TASK‑020/021),
Path A/B decided (TASK‑003D), injection defense designed (TASK‑022), auth & tenancy calls made
(TASK‑013D/014D), docs reconciled (TASK‑010R).

---

## Phase 1 — Walking Skeleton

> One vuln class (SQL injection), one language (Python), flowing the *entire* pipeline end
> to end — thin but complete. Runs against the eval harness from day one, even at low scores.

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑110 | Project & Folder CRUD (models, migrations, API, schemas) | TODO | P1 | M | TASK‑013/014 |
| TASK‑120 | Scan orchestrator + Celery job lifecycle (skeleton) | TODO | P1 | M | TASK‑110 |
| TASK‑130 | **ZIP upload module** (continues in‑progress work) | IN‑PROGRESS | P1 | M | TASK‑120 |
| TASK‑131 | ZIP hardening: slip/bomb/traversal/symlink + ClamAV + limits | TODO | P0 | M | TASK‑130 |
| TASK‑140 | Per‑scan sandbox: namespaces, cgroups, seccomp, tmpfs, drop caps | TODO | P0 | L | TASK‑120 |
| TASK‑150 | GitNexus runner: `gitnexus analyze --pdg` per scan + `.gitnexus/` lifecycle | TODO | P1 | M | TASK‑003D, TASK‑140 |
| TASK‑151 | `graph_facade` unified read API over LadybugDB | TODO | P1 | M | TASK‑150 |
| TASK‑160 | Minimal intra‑procedural taint check (routes→orm, SQLi/Python) | TODO | P1 | M | TASK‑151 |
| TASK‑161 | Candidate emitter + `candidates` table persistence | TODO | P1 | S | TASK‑160 |
| TASK‑170 | Findings storage (SARIF) + `findings` table | TODO | P1 | M | TASK‑161 |
| TASK‑180 | Frontend skeleton: upload → scan → results w/ trace viewer | TODO | P1 | L | TASK‑170 |
| TASK‑190 | Skeleton scored by the eval harness end‑to‑end | TODO | P1 | S | TASK‑020, TASK‑180 |

**TASK‑131 — ZIP hardening**
- **Acceptance:** ZIP Slip, ZIP bomb (size/depth/file‑count limits from `.env`), path traversal,
  and symlink attacks are blocked with negative tests; ClamAV scan on extraction; enforces
  `MAX_ZIP_SIZE_MB`, `MAX_FILES_PER_SCAN`, `MAX_LINES_PER_FILE`.

**TASK‑140 — Per‑scan sandbox [REVIEW]**
- **Why:** The mandate is "treat uploaded repos as hostile," but §5.2's `ScanSandbox` is a `pass`
  stub and the isolation *tier* is unchosen.
- **Acceptance:** Choose and implement an isolation tier appropriate for hostile input (evaluate
  gVisor/Kata/Firecracker microVM vs. plain namespaces and record the decision in `SECURITY.md`);
  non‑root user, seccomp profile, cgroup CPU/mem/disk limits, tmpfs work dir, dropped capabilities,
  **no worker egress except an allowlist** (LLM providers only). Verified by an escape‑attempt test.

**TASK‑160 — Minimal taint check**
- **Acceptance:** For a tiny real Python repo, a routes‑source → orm‑sink SQLi candidate is
  produced intra‑procedurally, stored, and rendered with its trace. Proves the seams, not the engine.

**Phase 1 exit:** a real finding on a real (tiny) repo, visible in the portal, measured by the harness.

---

## Phase 2 — Interprocedural Taint Engine ⚠ critical path

> **This is the product.** Build breadth‑first; **check the eval harness after each capability.**
> No hand‑wavy "done" — the harness number is the gate.

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑210 | Cross‑function propagation (walk CALLS, bind args↔params) | TODO | P1 | XL | Phase 1 |
| TASK‑220 | Field sensitivity (`obj.a` tainted vs `obj.b` clean) | TODO | P1 | L | TASK‑210 |
| TASK‑230 | Context‑sensitive sanitizer semantics (SQL≠XSS) | TODO | P1 | L | TASK‑220 |
| TASK‑240 | Source/sink modeling: seed `routes`/`orm` + rulepacks for top CWEs | TODO | P1 | L | TASK‑230 |
| TASK‑241 | Rulepack engine + `rulepacks` table + YAML validation endpoint | TODO | P1 | M | TASK‑240 |
| TASK‑250 | Path materialization → concrete, explainable source→sink trace | TODO | P1 | L | TASK‑240 |
| TASK‑260 | Language expansion: Python quality first, then JS/TS (measure) | TODO | P1 | XL | TASK‑250 |
| TASK‑270 | Pattern matcher (secrets, dangerous APIs) + secret scanner | TODO | P2 | M | Phase 1 |
| TASK‑280 | SCA scanner (OSV dependency CVEs) | TODO | P2 | M | Phase 1 |
| TASK‑290 | **Agent skills authoring** (`common` + `python` + Django/Flask) — parallel, writing not code | TODO | P2 | L | TASK‑021 |

**Top CWEs in scope (TASK‑240):** SQLi, XSS, command injection, path traversal, SSRF, deserialization.

**TASK‑260 — Language expansion**
- **Acceptance [REVIEW]:** JS/TS precision is **measured and disclosed separately**; weaker type
  resolution is expected → do **not** block Python GA on JS parity. Per‑language targets recorded.

**Phase 2 exit gate:** agreed precision/recall targets hit on the eval corpus for the top CWEs in
**Python**, with **JS/TS measured and documented** (even if lower). Slipping this slips GA one‑for‑one.

---

## Phase 3 — AI Agent Layer (overlaps Phase 2 back half)

> Starts as soon as candidates flow (mid‑Phase 2). **Triage first** (highest ROI). Skills are
> **LIVE but STATIC** here (hand‑authored, versioned files) — the automated loop ships in Phase 4b.

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑310 | Agent orchestrator + MCP client over GitNexus (17 tools) | TODO | P1 | L | TASK‑210 |
| TASK‑311 | **[REVIEW]** Concurrent, budget‑bounded agent pipeline | TODO | P1 | L | TASK‑310 |
| TASK‑312 | **[REVIEW]** Candidate dedup/pre‑filter before the LLM stage | TODO | P1 | M | TASK‑161 |
| TASK‑320 | Triage agent (kill false positives) | TODO | P1 | L | TASK‑310 |
| TASK‑321 | Skill composer/loader/registry (common+tech+framework as DATA) | TODO | P1 | M | TASK‑290 |
| TASK‑330 | Fix agent (patch + severity + CWE) per TASK‑016D | TODO | P1 | L | TASK‑320 |
| TASK‑331 | **[REVIEW]** Strict schema validation of all LLM output | TODO | P0 | M | TASK‑320 |
| TASK‑340 | **[REVIEW]** Prompt‑injection defense ships **with** Triage + red‑team suite | TODO | P0 | L | TASK‑022, TASK‑320 |
| TASK‑350 | Hunter agent (logic/authz/business‑logic flaws) — last | TODO | P2 | XL | TASK‑330 |
| TASK‑360 | LLM router + provider adapters (all 9 providers) | TODO | P1 | L | TASK‑310 |

**TASK‑311 — Concurrent, budget‑bounded pipeline [REVIEW]**
- **Why:** §5.5 runs Triage→Hunter→Fix strictly sequentially per candidate; on large repos this is a
  latency and $ blow‑up, and the per‑scan budget cap isn't wired into the loop.
- **Acceptance:** Bounded concurrency (semaphore); `COST_PER_SCAN_BUDGET_USD` enforced **inside**
  the orchestration loop (aborts past cap, preserves partial findings); per‑agent model routing
  (cheap/local model for high‑volume Triage).

**TASK‑331 — LLM output validation [REVIEW]**
- **Acceptance:** Every agent response is parsed against a strict schema; malformed output is
  rejected, never trusted; enforces the guardrail that **every finding carries a concrete
  deterministic path** (LLM adjusts confidence, never invents a finding).

**TASK‑340 — Prompt‑injection defense [REVIEW]**
- **Acceptance:** Ships **with** Triage (not after); analyzed code treated as untrusted data;
  in‑code instructions ignored; a suppression is honored only with a machine‑checkable trace;
  a red‑team test corpus passes in CI.

**Phase 3 exit:** Triage measurably cuts FP rate without dropping TP past the agreed threshold;
injection red‑team tests pass; agents compose the correct skill per stack.

---

## Phase 4 — Cost, Provider Config, Portal (fully parallel from Phase 1)

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑410 | Hardened key custody: ciphertext in DB, KEK injected | TODO | P1 | M | TASK‑031 |
| TASK‑411 | **[REVIEW]** Crypto hardening: fail‑closed KEK, AES‑GCM AAD, key rotation | TODO | P0 | M | TASK‑410 |
| TASK‑420 | Provider settings: **Configure → Test → Select → Save** flow (§5.8) | TODO | P1 | L | TASK‑410 |
| TASK‑421 | **[REVIEW]** SSRF guard on provider `base_url` (Ollama/self‑hosted) | TODO | P0 | M | TASK‑420 |
| TASK‑430 | Cost metering: `usage_meter`, `llm_usage`, computed `cost_usd` | TODO | P1 | M | TASK‑360 |
| TASK‑431 | Price catalog: `model_prices` (YAML seed + UI override) | TODO | P1 | M | TASK‑430 |
| TASK‑432 | **[REVIEW]** Cost rollup without lock contention | TODO | P1 | M | TASK‑430 |
| TASK‑440 | Usage dashboard: per‑scan/agent/model + portal total, date range | TODO | P2 | L | TASK‑431 |
| TASK‑450 | Results UI, trace viewer, findings filters, SARIF/JSON/PDF export | TODO | P2 | L | TASK‑170 |
| TASK‑460 | **[REVIEW]** Pagination on findings/candidates/usage list endpoints | TODO | P2 | S | TASK‑170 |

**TASK‑411 — Crypto hardening [REVIEW]**
- **Acceptance:** `from_secret()` **fails closed** on a short/invalid KEK (no silent `ljust` padding);
  AES‑GCM binds the `provider` id as **associated data (AAD)** to prevent ciphertext substitution;
  a documented **key‑rotation / re‑encryption** procedure exists (cross‑ref `SECURITY.md`).

**TASK‑421 — SSRF guard [REVIEW]**
- **Why:** The backend calls a user‑supplied `base_url` on *Test connection* → classic SSRF
  (e.g. `169.254.169.254`, internal services). §8 lists SSRF in scope but no control is specified.
- **Acceptance:** `base_url` and any outbound test/clone target is validated against a
  deny‑internal / allowlist policy; DNS‑rebinding‑aware; covered by negative tests.

**TASK‑432 — Cost rollup [REVIEW]**
- **Why:** `REFRESH MATERIALIZED VIEW usage_rollup` (non‑CONCURRENTLY) locks and full‑scans the
  highest‑write table on every scan completion → contention under concurrency.
- **Acceptance:** `REFRESH … CONCURRENTLY` (with the required unique index) **or** an incremental
  rollup table; verified under concurrent scans.

**Phase 4 exit:** an analyst can configure a provider, pick a model, run a scan, and see the cost
broken down by agent and model.

---

## Phase 4b — Gated Skill‑Learning Loop (deferred; post‑GA)

> **Off the GA critical path.** Hand‑authored versioned skills (Phase 3) deliver most of the value;
> the loop adds a new persistent attack surface (**skill‑poisoning**) and should bake against a
> harness validated on real pilot scans. Team‑tier feature.

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑4b10 | `candidate_recorder` + `skill_learning_candidates` table | TODO | P3 | M | Phase 3, Pilot |
| TASK‑4b20 | `eval_gate` (runs TASK‑021 harness per candidate, precision/recall deltas) | TODO | P3 | M | TASK‑021 |
| TASK‑4b30 | `promoter`: human‑approved → new versioned `SKILL.md` (git + `registry.yaml`) | TODO | P3 | M | TASK‑4b20 |
| TASK‑4b40 | `LearningQueue` review UI with eval deltas; approve/reject (admin) | TODO | P3 | L | TASK‑4b30 |
| TASK‑4b50 | Skill‑poisoning safeguards: auto‑reject recall‑lowering; versioned + reversible | TODO | P3 | M | TASK‑4b20 |

**Security invariants (must hold):** agents never write their own skills; skill content is DATA
not instructions; a recall‑lowering candidate is **auto‑rejected before any human sees it**;
everything is versioned and one revert away.

---

## Phase 5 — Hardening & Scale

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑510 | Concurrency/throughput tuning; worker isolation under load | TODO | P1 | L | Phase 2 |
| TASK‑511 | **[REVIEW]** Remove GitNexus single‑service SPOF/bottleneck | TODO | P1 | L | TASK‑150 |
| TASK‑512 | **[REVIEW]** Shared/object‑backed `.gitnexus/` index storage for multi‑node workers | TODO | P1 | M | TASK‑150 |
| TASK‑520 | **[REVIEW]** Webhook HMAC verification (GitHub/GitLab) + idempotency | TODO | P0 | M | TASK‑120 |
| TASK‑521 | **[REVIEW]** Idempotency keys on `POST /scans/trigger` & webhooks | TODO | P1 | S | TASK‑120 |
| TASK‑530 | CI/CD gating: PR comments, policy‑as‑code, SARIF into GitHub/GitLab | TODO | P1 | L | TASK‑450 |
| TASK‑540 | Full platform security review (sandbox escape, ZIP bombs, injection, custody) | TODO | P0 | L | Phase 3 |
| TASK‑550 | Incremental re‑index via GitNexus `detect_changes` | TODO | P2 | M | TASK‑150 |
| TASK‑560 | Reachability‑based FP suppression (confidence‑down, not hard‑suppress) | TODO | P2 | M | TASK‑250 |
| TASK‑570 | **[REVIEW]** Observability: structured logs → aggregation, Prometheus, OTel tracing | TODO | P1 | L | Phase 1 |
| TASK‑580 | **[REVIEW]** Data retention + partitioning (`llm_usage`, `findings`, `scans`) | TODO | P1 | M | TASK‑430 |
| TASK‑590 | **[REVIEW]** Backup/DR for Postgres, MinIO, index volume | TODO | P1 | M | TASK‑030 |
| TASK‑595 | **[REVIEW]** Reconcile `findings.confidence` vocabulary with SAST semantics | TODO | P2 | S | TASK‑170 |

**TASK‑570 — Observability [REVIEW]**
- **Why:** The guide mandates "observable" + structured logging, but no metrics/tracing/aggregation
  components exist. Enforces the logging rules (never log secrets/PII; log request/project/scan IDs,
  execution time, errors, server‑side stack traces).

**TASK‑595 — Confidence vocabulary [REVIEW]**
- **Why:** `findings.confidence CHECK ('extracted','inferred','ambiguous')` reads as copied from a
  different domain and doesn't match the SAST confidence/severity semantics used elsewhere.
- **Acceptance:** One coherent confidence model across candidates, findings, and agent output;
  migration if the enum changes.

---

## Phase 6 — Pilot → GA

| ID | Title | Status | Pri | Effort | Depends on |
|----|-------|--------|-----|--------|-----------|
| TASK‑610 | Onboard 1–2 design partners; scan their real repositories | TODO | P1 | L | Phase 5 |
| TASK‑620 | Measure precision/recall on *their* code; tune rulepacks/prompts | TODO | P1 | L | TASK‑610 |
| TASK‑630 | GA readiness checklist (security review passed, targets met) | TODO | P0 | M | TASK‑540, TASK‑620 |

**GA success:** target precision/recall on a design partner's real repo (not just benchmarks),
acceptable scan time, and analyst‑judged usefulness of triage + fixes.

---

## Milestones (verifiable, not date‑bound)

| Milestone | Definition | Key tasks |
|-----------|-----------|-----------|
| **M0** | Gate 0 passed: license path chosen, harness baseline, Path A/B decided, injection defense designed, auth/tenancy decided, docs reconciled | TASK‑001D, 020, 003D, 022, 013D, 014D, 010R |
| **M1** | Walking skeleton: one real finding, end to end, measured | TASK‑190 |
| **M2** | Taint engine v1: precision/recall targets met on top CWEs (Python) — *the* milestone | TASK‑260 exit gate |
| **M3** | Triage cuts FP rate past threshold; injection tests green | TASK‑320, 340 |
| **M4** | Provider/model flow + per‑scan/agent/model cost live | TASK‑420, 430, 440 |
| **M4b** | (post‑GA) A candidate passes the eval‑gate and is promoted, fully audited | TASK‑4b30 |
| **M5** | CI/CD gating + security review passed; runs at target concurrency | TASK‑530, 540, 510 |
| **M6** | Pilot success on a partner's real repo → GA | TASK‑630 |

---

## Risk → mitigating‑task map (from PROJECT_PLAN §5)

| Risk | Mitigating tasks |
|------|-----------------|
| Taint engine misses accuracy targets | TASK‑020/021 (harness), TASK‑160 (narrow slice), Phase 2 per‑CWE gates |
| Prompt injection via analyzed source | TASK‑022, TASK‑340, TASK‑331 |
| GitNexus PolyForm‑NC license | TASK‑001D (+ Path B/permissive fallback) |
| GitNexus PDG insufficient for target langs | TASK‑002 / TASK‑003D spike |
| JS/TS precision below Python | TASK‑260 (measure & disclose per‑language) |
| LLM cost runs away on large repos | TASK‑311 (budget cap + routing), TASK‑430/431 |
| No ground‑truth eval | TASK‑020 |
| Sandbox escape / ZIP bomb | TASK‑131, TASK‑140, TASK‑540 |
| Skill‑poisoning | Phase 4b gated loop only (TASK‑4b20/4b50); never auto‑writeback |
| **[REVIEW]** SSRF via base_url/git/webhook | TASK‑421, TASK‑520 |
| **[REVIEW]** No auth/tenancy in a security product | TASK‑013D/013, TASK‑014D/014 |
| **[REVIEW]** GitNexus single‑service SPOF | TASK‑511, TASK‑512 |

---

## Recommended first two weeks (from PROJECT_PLAN §7, + review P0s)

1. **TASK‑020/021** — the evaluation harness (nothing else can be judged without it).
2. **TASK‑002 → TASK‑003D** — the GitNexus `--pdg` spike (one week; decides the Phase‑2 foundation).
3. **TASK‑001D** — start the license conversation now (calendar dependency outside the team).
4. **TASK‑010R / TASK‑013D / TASK‑014D** — close the doc/auth/tenancy contradictions before feature code.

---

*End of TASK_BACKLOG.md — definitions and ordering only. No implementation is authorized by this file.*
