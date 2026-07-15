# Current Project State

**Updated:** 2026-07-15 (multi-language MVP scope reconciliation; prior: 2026-07-10 ARCHITECTURE_v2.3 + approved review)

## Resolved Decisions (v1 / MVP)
- **Tenancy:** Single-tenant (multi-tenancy deferred — TASK-014).
- **Authentication:** Deferred until after the core scanning MVP (TASK-013). Matches ARCHITECTURE §1 ("no login/auth in v1").
- **Deployment target:** Docker Compose (K8s manifests remain reference/future).
- **Code intelligence:** GitNexus, Path A (GitNexus-only) working default; Path B pending TASK-002 spike (TASK-003D open).
- **GitNexus licensing (TASK-001D — RESOLVED 2026-07-10):** This is a personal, non-commercial, public GitHub project; GitNexus is used under its PolyForm Noncommercial license, and no commercial use, SaaS offering, paid product, or enterprise deployment is planned at this stage.
  - **Decision:** GitNexus is approved for the current personal/non-commercial MVP.
  - **Future Action:** If this project is ever commercialized (SaaS, enterprise deployment, paid product, or proprietary distribution), the GitNexus license must be re-evaluated and either: obtain an appropriate commercial license, or replace GitNexus with an alternative implementation.
- **Version roadmap (FINALIZED 2026-07-15):** modular, multi-language SAST engine delivered in
  versions:
  - **v1.0 (MVP):** **Python** (backend) + **Web** — JavaScript, TypeScript, HTML treated as a
    **single "Web" analysis capability** for planning.
  - **v2.0:** Java, C/C++, and their known-answer corpora **OWASP Benchmark** (Java) + **NIST
    Juliet** (C/C++) — plus the **external corpus fetcher** those corpora require.
  - **v3.0:** Go, C#.
  The evaluation harness stays **language-agnostic**; each language eventually gets deterministic
  analysis, language-specific rulepacks, an evaluation corpus, AI-assisted triage, and AI-assisted
  remediation. **OWASP Benchmark, Juliet, and the external fetcher are deferred to v2.0** (not
  the MVP; MVP corpora are curated and committed in-repo). Supersedes the earlier "Python only"
  and "Python + JS/TS/HTML" wordings; consistent with ARCHITECTURE_v2.3 §1/§4/§5.7/§9/§12.
- **MVP scope:** Python + Web (JS/TS/HTML) · Ollama + one cloud provider · Triage + Fix agents · SARIF/JSON export.

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

## Completed — Evaluation corpora repository layout (TASK-020a, Slice 3 — 2026-07-10)
Third slice of TASK-020a on branch `feature/task-020a-evaluation-foundation` (awaiting human
review before merge; not merged to main). Implements the approved **distribution-by-directory**
corpus layout only — no corpus content authored, no dataset downloads, no runner/metrics/AI.

- **Layout**: `eval/corpus/` split into `committed/` (TRACKED — small, permissively-licensed
  corpora such as `project-curated`) and `downloaded/` (GIT-IGNORED cache for large/licensed
  corpora, fetched never vendored). Placeholders: `committed/.gitkeep`, `downloaded/.gitkeep`;
  obsolete flat `eval/corpus/.gitkeep` removed.
- **`.gitignore`** reorganized: ignores only `eval/corpus/downloaded/*` (keeps
  `downloaded/.gitkeep`); everything under `committed/` and all `eval/labels/**` stay tracked.
- **Deliberately unchanged** (per approval): `CorpusDescriptor`, `corpus_registry.json`, and
  `eval/README.md` — the registry schema stays as-is until downloaded corpora are actually
  introduced in a later slice; README reconciliation is deferred to that slice.
- **DoD gates green** (root `.venv`, harness code unchanged): `ruff` clean; `mypy --strict` clean;
  `pytest eval/harness/tests` = 44 passed. Manual validation via `git check-ignore`: committed
  corpus files + both `.gitkeep`s tracked; `downloaded/` corpus data ignored — all as designed.

## Completed — project_curated evaluation corpus (TASK-020a, Slice 4 — 2026-07-10)
Fourth slice of TASK-020a on branch `feature/task-020a-evaluation-foundation` (awaiting human
review before merge; not merged to main). Authors the initial in-repo curated corpus. Python
only; no downloads, no OWASP Benchmark, no Juliet, no rule/benchmark execution, no AI logic.

- **Corpus** (`eval/corpus/committed/project-curated/`): 20 small, realistic, inert Python
  examples (never imported or executed) across 5 categories — SQL injection (CWE-89), XSS
  (CWE-79), command injection (CWE-78), path traversal (CWE-22), hardcoded secrets (CWE-798) —
  each with **2 vulnerable + 2 secure** examples. Each file carries a single `# sast:vuln` /
  `# sast:safe` marker on the key line.
- **Labels** (`eval/labels/project-curated.labels.json`): 20 `GroundTruthLabel`s (10 vulnerable,
  10 safe) with exact `start_line`/`end_line` and per-category CWE, generated from the markers
  and validated before commit. `CorpusDescriptor`/`corpus_registry.json` unchanged (registry
  already describes `project_curated`); `eval/README.md` unchanged.
- **Regression test** (`eval/harness/tests/test_project_curated_corpus.py`): loads the labels via
  the public loader and asserts the integrity validator passes against the committed corpus, plus
  the 5×(2+2) category balance — so corpus and labels cannot drift apart.
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean; `pytest eval/harness/tests` = 46 passed (2 new). Manual validator check: 20 labels
  (10 vulnerable / 10 safe, 2+2 per CWE), validator `ok` with 0 issues; corpus + labels git-tracked.

## Completed — Evaluation harness language-agnostic reconciliation (2026-07-15)
Reconciles the harness implementation with the approved multi-language MVP scope, on branch
`feature/task-020a-evaluation-foundation`. No new features, no corpus fetcher, no downloaded
corpora; `project_curated` behavior is unchanged (backward-compatible).

- **`Language` enum expanded** (`eval/harness/models.py`): kept as a `StrEnum`, now covering the
  approved roadmap — `python`, `javascript`, `typescript`, `html` (MVP) plus `java`, `cpp`, `go`,
  `csharp` (future). Docstring updated; the harness privileges no single language.
- **Registry corrected** (`eval/corpus_registry.json`): OWASP Benchmark `python`→`java`, NIST
  Juliet `python`→`cpp` (C/C++); both notes marked future-roadmap/descriptor-only. `project_curated`
  stays `python`.
- **Tests** (`eval/harness/tests/test_models.py`): added positive coverage for roadmap languages
  (label→`javascript`, descriptor→`java`) and a negative test rejecting an unsupported language.
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean; `pytest eval/harness/tests` = 49 passed (3 new). Manual validation: registry loads with
  `java`/`cpp`/`python`; `project_curated` labels load (10 vuln / 10 safe) and the integrity
  validator reports `ok` with 0 issues.

## Completed — curated Web evaluation corpus (TASK-020a, Web slice — 2026-07-15)
Authors the MVP **Web** analysis capability's known-answer corpus on branch
`feature/task-020a-evaluation-foundation`. JavaScript/TypeScript/HTML, treated as one "Web"
capability. No analyzers, no AI, no eval runner; the existing harness architecture is unchanged
(reused `CorpusKind.project_curated`, models, loader, validator — no code changes to them).

- **Corpus** (`eval/corpus/committed/web-curated/`): 12 small, realistic, inert examples across
  three single-language sub-corpora — `javascript/` (DOM XSS CWE-79, eval injection CWE-95),
  `typescript/` (DOM XSS CWE-79, hardcoded secret CWE-798), `html/` (javascript: URI XSS CWE-79,
  reverse tabnabbing CWE-1022). Each language has **2 vulnerable + 2 safe**; each key line carries
  a `sast:vuln` / `sast:safe` marker. Files are never imported or executed.
- **Labels** (`eval/labels/web-curated.{js,ts,html}.labels.json`): three `LabelSet`s (4 labels
  each; 6 vulnerable / 6 safe total) with exact `start_line`/`end_line` and per-category CWE.
  Single-language per set (harness models one corpus = one language), so the Web capability is
  three registry descriptors: `web_curated_js`, `web_curated_ts`, `web_curated_html`
  (`kind = project_curated`).
- **Registry** (`eval/corpus_registry.json`): three new Web descriptors added; existing entries
  unchanged.
- **Regression test** (`eval/harness/tests/test_web_curated_corpus.py`): loads each Web corpus via
  the public loader/registry, asserts the integrity validator passes against the committed tree,
  the 2+2 vulnerable/safe balance, and the expected CWEs. `test_loader.py` shipped-registry
  assertion updated for the three new ids.
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean (13 files); `pytest eval/harness/tests` = 55 passed (6 new). Manual validation: all three
  corpora load, validator `ok` with 0 issues, and every labeled line was confirmed to carry its
  intended `sast:vuln`/`sast:safe` marker.

## Completed — Eval runner result contract + matching (TASK-020b, Slice 1 — 2026-07-15)
First slice of TASK-020b on branch `feature/task-020a-evaluation-foundation`. Establishes the
runner's **scoring core** only: what a detector reports and how each ground-truth label is
classified against findings. Read-only and analyzer-agnostic — **no analyzers, no AI, no metrics
(TASK-020c), no corpus/detector orchestration** (a later 020b slice). Existing harness modules
(`models.py`, `loader.py`, `validator.py`, `errors.py`) are unchanged; the slice is purely additive.

- **Result contract** (`eval/harness/runner.py`): `Finding` (reuses `SourceLocation`, so findings
  carry the same relative-path/anti-traversal validation); `MatchOutcome` enum = **TP / FP / FN
  only** (true negatives intentionally out of scope — not well-defined for SAST, not needed for
  precision/recall/F1); `LabelOutcome`; `EvaluationReport` (per-label outcomes + `unmatched_findings`
  + raw `n_true_positive`/`n_false_positive`/`n_false_negative` counts).
- **Matching** (`match_findings_to_labels`): deterministic, location-based (same file + overlapping
  line range; a location without `start_line` = whole file). Vulnerable label → TP (matched) / FN
  (unmatched); safe label → FP (matched) / **no outcome** (unmatched). Findings matching no label
  are collected separately. Aggregation into metrics is left to TASK-020c.
- **Tests** (`eval/harness/tests/test_runner.py`): 15 tests — TP/FP/FN, safe-unmatched yields no
  outcome, out-of-range/other-file misses, whole-file & range overlap, multiple findings per label,
  unmatched collection, enum has no true-negative member, frozen/`extra="forbid"` enforcement.
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean (15 files); `pytest eval/harness/tests` = 70 passed (15 new). Manual validation: ran the
  matcher against the real committed `web_curated_js` labels with a simulated finding list →
  TP=1, FP=1, FN=1, one safe label correctly produced **no** outcome (3 outcomes for 4 labels),
  and the unmatched finding was collected.

## In Progress
- ZIP upload module (TASK-130)

## Pending (next up — MVP critical path)
- Evaluation harness (TASK-020a/b/c, TASK-021). MVP corpora complete (Python `project_curated` +
  Web `web_curated_js`/`_ts`/`_html`); **TASK-020b Slice 1 (result contract + matching) done.**
  **Next:** TASK-020b Slice 2 — `Detector` protocol + `run_evaluation` orchestration over a corpus
  (load labels, validate, invoke detector, match) — then TASK-020c metrics, then TASK-021. OWASP
  Benchmark, Juliet, and the external fetcher remain **deferred to v2.0** (TASK-020a-F/J/C).
- GitNexus `--pdg` spike (TASK-002 → TASK-003D)
- Testing + Alembic migration conventions (TASK-023, TASK-024)
- GitNexus integration (TASK-150/151)
- Interprocedural Taint Engine (TASK-210a–d …)
- AI Triage + Fix Agents (TASK-320, TASK-330)
- Cost tracking + provider config (TASK-430, TASK-360a/b)

## Deferred beyond MVP
Authentication, multi-tenancy, Hunter agent, **v2.0** (Java, C/C++, OWASP Benchmark, Juliet, and
the external corpus fetcher) and **v3.0** (Go, C#), cloud providers 3–9, PDF export, full
observability (tracing/metrics), webhook/git ingestion, CI/CD gating, SCA scanner, gated
skill-learning loop. See TASK_BACKLOG.md → "Post-MVP / Deferred".

## Known Issues
- ~~GitNexus PolyForm-NC license not yet cleared (TASK-001D)~~ — **RESOLVED 2026-07-10:** approved for the personal/non-commercial MVP; re-evaluate only if the project is ever commercialized (see Resolved Decisions → GitNexus licensing).
- `docs/SECURITY.md` and `docs/API_SPEC.md` not yet authored (TASK-011R, TASK-012R).
- ~~Eval harness language artifacts pending reconciliation~~ — **RESOLVED 2026-07-15:** the
  harness `Language` enum now covers the approved roadmap (`python`, `javascript`, `typescript`,
  `html`, `java`, `cpp`, `go`, `csharp`) and `eval/corpus_registry.json` labels OWASP Benchmark
  as `java` and NIST Juliet as `cpp` (C/C++). The harness stays language-agnostic;
  `project_curated` remains `python` (backward-compatible). See the reconciliation note below.

## Current Branch
feature/task-020a-evaluation-foundation (TASK-020b Slice 1; awaiting human review before merge)

## Last Completed Task
TASK-020b Slice 1 — eval runner result contract + matching: `eval/harness/runner.py` (`Finding`,
`MatchOutcome` = TP/FP/FN only, `LabelOutcome`, `EvaluationReport`, `match_findings_to_labels`) +
`eval/harness/tests/test_runner.py` (15 tests), on `feature/task-020a-evaluation-foundation`
(2026-07-15); read-only, analyzer-agnostic; no analyzers/AI/metrics/orchestration; existing harness
modules unchanged. DoD gates green (ruff/mypy clean; pytest 70 passed); awaiting human review before
merge. Prior: TASK-020a complete for MVP — Web corpus slice (`web_curated_*`); language-agnostic
reconciliation; Slice 4 `project_curated` (Python) corpus; Slice 3 layout; Slice 2 validator;
Slice 1 ground-truth contract.
Prior: Engineering Foundation built and runtime-validated (2026-07-10) on
`feature/engineering-foundation`. Earlier: TASK-010R / TASK-010S doc reconciliation; TASK-012 baseline.
