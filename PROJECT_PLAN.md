# AI SAST Platform — Project Plan

**Companion to:** ARCHITECTURE_v2.3.md
**Date:** 2026-07-09  (rev 2 — aligned to v2.3 learnable agent skills)
**Planning basis:** phased, gate-driven, organized around the one genuinely hard,
schedule-defining component — the interprocedural taint engine.

> Durations are given in **relative weeks** and **rough team-weeks of effort**, not
> calendar dates, because the right calendar depends on team size and how much of the
> taint engine you build vs. lean on GitNexus for. Re-baseline after the Gate 0 spike.

---

## 1. The one fact that shapes this plan

Almost everything in v2.2 is well-understood engineering you can estimate confidently:
upload/scan orchestration, the provider/model settings, cost tracking, the portal,
CI/CD gating. **One thing is not:** the interprocedural taint engine (§5.4). It is real
static-analysis R&D, it is the critical path, and it is the *only* component that
decides whether the product actually competes with Fortify/Checkmarx.

Two consequences drive the whole plan:

1. **Build the measuring instrument before the thing it measures.** You cannot tune a
   SAST engine — or claim it beats anyone — without an evaluation harness producing
   precision/recall on known-answer corpora. The harness is Phase 0, not an afterthought.
2. **De-risk the taint engine as early as possible** with a narrow end-to-end slice
   (one vulnerability class, one language) before scaling breadth.

---

## 2. Phases at a glance

| Phase | Name | Rel. weeks | Gate to exit |
|------|------|-----------|--------------|
| 0 | Foundations & Gates | 1–5 | License cleared, eval harness runs, Path A/B decided |
| 1 | Walking Skeleton | 4–7 | One rule flows upload → GitNexus → taint → finding → UI |
| 2 | **Interprocedural Taint Engine** (critical path) | 7–16 | Precision/recall targets hit on eval corpus |
| 3 | AI Agent Layer | 10–18 (overlaps 2) | Triage cuts FP rate measurably; injection defense in place |
| 4 | Cost, Provider Config, Portal | 8–20 (parallel) | Model-select flow + per-scan/agent/model cost live |
| 4b | Gated Skill Learning Loop (post-GA) | after 24 | Candidate → eval-gate → approve → versioned promotion |
| 5 | Hardening & Scale | 18–24 | CI gates, concurrency, security review pass |
| 6 | Pilot → GA | 24–26+ | Design-partner scans real repos; success criteria met |

Phases 3 and 4 run **in parallel** with the back half of Phase 2 (different skills).
Phase 2 is the schedule spine; slipping it slips GA one-for-one.

---

## 3. Phase detail

### Phase 0 — Foundations & Gates (blocks everything)

The gates here are not paperwork; each one, if skipped, invalidates later work.

- **G0.1 GitNexus license clearance.** Resolve PolyForm-Noncommercial before ANY code
  depends on GitNexus. Outcomes: (a) commercial grant via akonlabs, or (b) confirmed
  noncommercial deployment, or (c) commit to the permissive fallback engine. *If this
  fails late, Phase 2 is partly wasted.*
- **G0.2 Evaluation harness.** Stand up OWASP Benchmark + NIST Juliet + a small curated
  internal corpus with known vulnerable/safe labels. Wire a runner that outputs
  precision, recall, F1 **per rule and per language**. This is the instrument every
  later phase steers by.
  **Build it callable, not batch-only:** the skill learning loop's `eval_gate` (§5.10)
  must invoke the harness **on demand against a trial skill/rule version** and return
  precision/recall **deltas vs. the current active version**. Design the interface as a
  library/service call parameterized by a candidate, not just a nightly CI job — else
  it gets refactored in Phase 3.
- **G0.3 Path A vs B spike.** Time-boxed (1 week): run GitNexus `--pdg` on 3–5
  representative repos in your target languages; confirm the intra-procedural PDG +
  call graph is good enough to build interprocedural taint on (Path A) or decide to
  keep Joern (Path B). *Decides the Phase 2 foundation.*
- **G0.4 Threat model for LLM-in-the-loop.** Design the defense for prompt injection via
  analyzed source (see §5). Non-negotiable given the Triage agent suppresses findings.
- Team/infra: repos, CI, Postgres/Redis/GitNexus containers, KEK secret-injection wired
  (the §5.8 custody model), skeleton FastAPI + React app.

**Exit:** license path chosen, harness produces a baseline number, spike decision made,
injection defense designed.

### Phase 1 — Walking Skeleton

One vulnerability class (SQL injection), one language (Python), flowing the *entire*
pipeline end to end — thin but complete:

upload ZIP → sandboxed worker → `gitnexus analyze --pdg` → a minimal taint check
(routes source → orm sink, intra-procedural only) → one candidate → stored finding →
rendered in the UI with its trace.

Purpose: prove the seams (orchestration, GitNexus integration, MCP wiring, DB, UI
contract) before pouring effort into the hard engine. Runs against the eval harness
from day one, even at low scores.

**Exit:** a real finding on a real (tiny) repo, visible in the portal, measured.

### Phase 2 — Interprocedural Taint Engine  ⚠ critical path

This is the product. Build breadth-first over these capabilities, checking the eval
harness after each:

1. **Cross-function propagation** — walk GitNexus CALLS edges, bind args↔params, carry
   taint state across boundaries (this is the core gap GitNexus's intra-proc PDG leaves).
2. **Field sensitivity** — distinguish `obj.a` (tainted) from `obj.b` (clean).
3. **Sanitizer semantics** — context-sensitive; a sanitizer valid for SQL isn't for XSS.
4. **Source/sink modeling** — seed from GitNexus `routes`/`orm`, extend via rulepacks
   for the top CWEs (SQLi, XSS, command injection, path traversal, SSRF, deserialization).
5. **Path materialization** — produce the concrete, explainable source→sink trace that
   becomes the finding (explainability is the competitive point vs. a black box).
6. **Language expansion** — Python first to target quality, then JS/TS (weaker type
   resolution → expect lower precision; measure it).

**Exit gate:** hit agreed precision/recall targets on the eval corpus for the top CWEs
in Python, with JS/TS measured and documented (even if lower). *No hand-wavy "done" —
the harness number is the gate.*

**Parallel authoring (no engineering dependency):** a security engineer drafts the
**agent skills** — `common/SKILL.md` and `python/SKILL.md` (+ Django/Flask framework
files) — during Phases 1–2, so they are ready, versioned, and eval-checked when the
agents need them in Phase 3. This is writing, not code; it should not sit on the
critical path.

### Phase 3 — AI Agent Layer (overlaps Phase 2's back half)

Once candidates are flowing (mid-Phase 2), build the agents against them:

- **Triage first** (highest ROI — directly attacks the false-positive rate that kills
  SAST adoption). Measure FP reduction on the eval corpus before/after.
- **Fix** (patch + severity + CWE), then **Hunter** (business-logic/authz flaws beyond
  taint) last — it's the fuzziest and benefits from the others being stable.
- **Prompt-injection defense (from G0.4) ships with Triage, not after.** Treat analyzed
  code as untrusted: strong system/data separation, ignore in-code instructions,
  require a machine-checkable trace before a suppression is honored.
- **Agent skills are LIVE here but STATIC:** agents load the composed `common` +
  tech skill (§5.10) as versioned, hand-authored files. The **automated gated learning
  loop does NOT ship in this phase** (see Phase 4b / GA decision below) — skills are
  updated by humans editing versioned files, validated through the harness manually.

**Exit:** Triage measurably cuts FP rate without dropping true positives past an agreed
threshold; injection red-team tests pass; agents compose the correct skill per stack.

### Phase 4 — Cost, Provider Config, Portal (fully parallel)

Independent of the engine — a frontend/backend track can run this from Phase 1 onward:

- Provider settings with the **Configure → Test → Select → Save** model flow (§5.8).
- Hardened key custody: ciphertext in DB, KEK injected (§5.8/§7).
- **Cost tracking**: `llm_usage` metering per scan/agent/model, `model_prices` catalog
  (YAML-seeded, UI-override), Usage dashboard, per-scan budget cap (§5.9, §13).
- Project/folder management, scan results UI, trace viewer, SARIF export.

**Exit:** an analyst can configure a provider, pick a model, run a scan, and see the
cost broken down by agent and model.

### Phase 4b — Gated Skill Learning Loop (deferred; post-GA recommended)

The automated loop from §5.10 — analyst feedback → candidate → eval-gate → human
approval → versioned promotion. Distinct workstream, **not on the GA critical path**:

- Backend: `candidate_recorder`, `eval_gate` (calls the G0.2 harness per candidate),
  `promoter`; the three DB tables (`agent_skills`, `skill_learning_candidates`, and the
  `rulepacks` rename); promotion/rollback endpoints.
- Frontend: `LearningQueue` review UI with per-candidate precision/recall deltas.
- Depends on: the harness being **callable** (G0.2) and, ideally, **proven on real
  pilot scans** so the gate's numbers are trustworthy.

**Why deferred:** hand-authored versioned skills (Phase 3) deliver most of the value.
The loop adds a service, a review workflow, a UI surface, and a **new persistent attack
surface** (skill-poisoning). Shipping it after GA keeps the first release earlier and
lets the loop bake against a harness validated on real code. In §13 it is a Team-tier
feature, not Community — consistent with post-GA delivery.

### Phase 5 — Hardening & Scale

- Concurrency/throughput (queue tuning, worker isolation under load).
- CI/CD gating: PR comments, policy-as-code, SARIF into GitHub/GitLab.
- Security review of the whole platform (sandbox escape, ZIP bombs, the injection
  defense, the custody model).
- Incremental re-index via GitNexus `detect_changes`; reachability-based FP suppression.

### Phase 6 — Pilot → GA

- One or two design partners scan real repositories.
- Success = the plan's target precision/recall on *their* code (not just benchmarks),
  acceptable scan time, and analyst-judged usefulness of triage + fixes.
- Iterate on rulepacks/prompts from pilot findings; then GA.

---

## 4. Critical path & parallelism

```
Gate 0 ──> Phase 1 ──> Phase 2 (taint engine) ─────────────> Phase 5 ──> Phase 6
                           │                                    ▲
                           ├── Phase 3 (agents, overlaps) ──────┤
                           │                                    │
   Phase 4 (cost/portal, parallel from Phase 1) ───────────────┘
```

- **Critical path:** Gate 0 → Phase 1 → **Phase 2** → Phase 5 → Phase 6.
- Phase 4 is parallelizable immediately (separate skill set) — staff it alongside.
- Phase 3 starts as soon as candidates flow, not after Phase 2 fully closes.
- **Fastest way to move GA earlier:** narrow Phase 2 scope (fewer CWEs/languages at v1),
  not compress it. Quality on a few classes beats breadth that fails the harness.
- **Phase 4b (skill learning loop) is intentionally OFF the GA critical path.** Agent
  skills ship at GA as hand-authored, versioned files; the automated loop follows post-GA.

---

## 5. Top risks (ranked) & mitigations

| # | Risk | Impact | Mitigation |
|---|------|--------|-----------|
| 1 | Taint engine accuracy misses targets | Product doesn't compete | Eval harness from Phase 0; narrow-slice de-risk in Phase 1; breadth-first with per-CWE gates |
| 2 | **Prompt injection via analyzed source** blinds Triage | Security hole in a security product | Threat model in G0.4; data/instruction separation; trace-required suppression; red-team in Phase 3 |
| 3 | GitNexus PolyForm-NC license | Legal/commercial block | G0.1 clears before dependency; pluggable engine keeps Path B/permissive fallback open |
| 4 | GitNexus PDG insufficient for target langs | Rework of Phase 2 foundation | G0.3 spike decides Path A vs B before committing |
| 5 | JS/TS precision below Python (weak types) | Uneven product quality | Measure and disclose per-language; set separate targets; don't block Python GA on JS parity |
| 6 | LLM cost runs away on large repos | Unit economics | Per-scan budget cap + per-agent model routing (cheap model for Triage) from Phase 4 |
| 7 | No ground-truth eval → unfalsifiable claims | Can't steer or sell | Same as #1 — the harness is the mitigation and it's Phase 0 |
| 8 | Sandbox escape / ZIP bomb on hostile upload | Platform compromise | Isolation + limits in Phase 1; dedicated security review in Phase 5 |
| 9 | **Skill-poisoning** — a bad "learning" teaches the scanner to ignore a real vuln class | Persistent, cross-scan, cross-tenant blindness (worse than per-scan injection #2) | Gated loop only (never auto-writeback); eval-gate auto-rejects recall-lowering candidates; human approval; versioned + reversible; defer loop to Phase 4b |

---

## 6. Milestones (verifiable, not date-bound)

- **M0** Gate 0 passed: license path chosen, eval harness prints a baseline, Path A/B decided.
- **M1** Walking skeleton: one real finding, end to end, measured in the portal.
- **M2** Taint engine v1: precision/recall targets met on top CWEs (Python) — *the* milestone.
- **M3** Triage agent cuts FP rate past threshold; injection tests green.
- **M4** Provider/model flow + per-scan/agent/model cost live in the portal.
- **M4b** (post-GA) Gated learning loop: a candidate passes the eval-gate and is promoted to a new skill version, fully audited.
- **M5** CI/CD gating + security review passed; runs at target concurrency.
- **M6** Pilot success on a design partner's real repo → GA.

---

## 7. What I recommend building first (next two weeks)

1. **The evaluation harness (G0.2).** Nothing else can be judged without it.
2. **The GitNexus `--pdg` spike (G0.3).** One week, decides your Phase 2 foundation.
3. **Start the license conversation (G0.1)** in parallel — it's a calendar dependency
   outside your control, so begin it now.

Everything else waits behind these three. They're cheap, fast, and each one prevents a
category of expensive late rework.
