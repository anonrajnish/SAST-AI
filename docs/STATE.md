# Current Project State

**Updated:** 2026-07-18 (Scan Pipeline Slice 0 — shared `contracts` package (M3); prior: deterministic framework stabilization pass; 6th/final analyzer reverse tabnabbing — MVP analyzer suite complete; 2026-07-15 multi-language MVP scope reconciliation; 2026-07-10 ARCHITECTURE_v2.3 + approved review)

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

## Completed — Eval single-corpus orchestration (TASK-020b, Slice 2 — 2026-07-17)
Second slice of TASK-020b on branch `feature/task-020a-evaluation-foundation`. Adds the
orchestration layer that connects the harness components for one corpus. Reuses the loader,
validator, and Slice-1 matcher **unchanged**; introduces the `Detector` seam **without any real
analyzer**. Analyzer-agnostic — **no analyzer, no AI, no metrics (TASK-020c), no CLI/API (TASK-021)**.
Purely additive: `models.py`, `loader.py`, `validator.py`, `runner.py`, `errors.py` are unchanged.

- **Orchestration** (`eval/harness/evaluation.py`): `Detector` protocol (`scan(corpus_root) ->
  list[Finding]`); `CorpusEvaluation` result model (`corpus_id`, `integrity`, `evaluation:
  EvaluationReport | None`, `evaluated` property); `run_evaluation(detector, corpus_id, *, registry,
  labels_dir, corpus_base_dir)`.
- **Flow**: loader loads labels + resolves the corpus root (path-safe) → validator gates integrity →
  if `ok`, the detector is invoked and its findings scored by the matcher; otherwise the detector is
  **not run**.
- **Integrity failure is a structured outcome, not an exception** (per approved design): a failed
  gate returns `CorpusEvaluation(evaluation=None)` with the `IntegrityReport` explaining why.
  Exceptions are reserved for genuine faults (unknown corpus id, unreadable/invalid labels, path
  escape), which propagate as `eval.harness.errors` types from the loader.
- **Tests** (`eval/harness/tests/test_evaluation.py`): 7 tests — scores the real committed
  `web_curated_js` corpus, empty-detector all-missed, detector receives the resolved corpus root,
  unknown corpus raises `CorpusRegistryError`, integrity failure returns a structured outcome with
  the detector skipped, and `CorpusEvaluation` frozen/`extra="forbid"`.
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean (17 files); `pytest eval/harness/tests` = 77 passed (7 new). Manual validation: scored the
  real `web_curated_js` corpus (TP=1, FP=1, FN=1) and confirmed an integrity-failure corpus returns
  `evaluated=False`, `evaluation=None`, `integrity.ok=False` with a `missing_file` issue and no
  exception raised.

## Completed — Eval metrics layer (TASK-020c — 2026-07-17)
Metrics layer on branch `feature/task-020a-evaluation-foundation`. Computes precision/recall/F1
from an `EvaluationReport`'s TP/FP/FN counts. Pure and analyzer-agnostic — **no scanning, corpus
loading, orchestration, AI, or CLI/API (TASK-021)**. `EvaluationReport` reused **unchanged**;
purely additive (no edits to `runner.py`/`evaluation.py`/`models.py`/`loader.py`/`validator.py`/
`errors.py`).

- **Metrics** (`eval/harness/metrics.py`): immutable `Metrics` model storing all six values —
  `true_positives`, `false_positives`, `false_negatives`, `precision`, `recall`, `f1` (derived
  values computed once at construction and **stored**, no `@computed_field`); `compute_metrics(
  report) -> Metrics`.
- **Definitions**: Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2·TP/(2·TP+FP+FN); each
  derived value is **0.0 when its denominator is 0** (documented convention — no `ZeroDivisionError`).
  True negatives out of scope; unmatched findings excluded from precision (label-centric).
- **Deferred (per approved design)**: `aggregate_metrics` (micro/macro/weighted across reports) and
  per-rule/per-language breakdowns (would need per-label CWE/language on `LabelOutcome`) — later slice.
- **Tests** (`eval/harness/tests/test_metrics.py`): 9 tests — worked example (0.75/0.6/0.667),
  perfect scores, all three zero-division edges, count pass-through, frozen/`extra="forbid"`, and a
  real-pipeline check via `run_evaluation` on `web_curated_js` (P=R=F1=0.5).
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean (19 files); `pytest eval/harness/tests` = 86 passed (9 new). Manual validation: metrics from
  a real `run_evaluation` output on `web_curated_js` (TP=FP=FN=1 → P=R=F1=0.5); empty report yields
  all-zero metrics with no exception; `model_dump` confirms all six are stored fields.

## Completed — Callable evaluation interface (TASK-021 — 2026-07-17)
The single reusable entry point over the finished harness, on branch
`feature/task-020a-evaluation-foundation`. Given a dependency-injected `Detector` and a corpus id,
it delegates to the orchestrator and computes metrics, returning one serializable result. Fully DI
(the caller locates registry/labels/corpus dirs); analyzer-agnostic; **no CLI, no REST, no AI, no
analyzer, no orchestration duplicated**. Purely additive — no edits to any existing module
(`__init__.py` intentionally left unchanged until the public API stabilizes).

- **Interface** (`eval/harness/interface.py`): `EvaluationStatus` (`evaluated` / `integrity_failed`);
  `EvaluationResult` (frozen, `extra="forbid"`: `corpus_id`, `status`, `detector_name`, `integrity`,
  `evaluation`, `metrics`); `evaluate_corpus(detector, corpus_id, *, registry, labels_dir,
  corpus_base_dir, detector_name=None) -> EvaluationResult`.
- **Flow**: delegates to `run_evaluation` (loader → validator → matcher); on integrity pass computes
  `compute_metrics`; on integrity fail returns `status=INTEGRITY_FAILED` with `metrics`/`evaluation`
  = `None` and the detector not run. Operational faults (unknown corpus, unreadable/invalid labels)
  propagate as `eval.harness.errors` types; no new exception types added.
- **Deferred (per approved design)**: candidate-vs-baseline deltas / `eval_gate` (Phase 4b learning
  loop) — the interface returns `Metrics` as the diffable building block; the `evaluate_corpus_at`
  layout resolver and any `__init__` re-exports were declined this slice.
- **Tests** (`eval/harness/tests/test_interface.py`): 7 tests — happy path on real committed
  `web_curated_js` (status EVALUATED, P=R=F1=0.5, `detector_name` propagated), default `detector_name`,
  unknown corpus raises `CorpusRegistryError`, integrity failure returns a structured result with the
  detector skipped, JSON serializability (`model_dump(mode="json")`), frozen/`extra="forbid"`.
- **DoD gates green** (root `.venv`): `ruff check eval/harness` clean; `mypy --strict eval/harness`
  clean (21 files); `pytest eval/harness/tests` = 93 passed (7 new). Manual validation:
  `evaluate_corpus` on real `web_curated_js` → EvaluationResult (TP=FP=FN=1, P=R=F1=0.5), full result
  JSON-serialized (6 keys), and an integrity-failure corpus returned `status=integrity_failed`,
  `metrics=None` with no exception.

## Completed — First deterministic analyzer: hardcoded-secret scanner (2026-07-17)
The first analyzer in the deterministic detection layer, placed under the backend application
(`backend/app/services/deterministic/`) so future scan pipelines can reuse it. Detects **hardcoded
secrets (CWE-798)** — a simple, high-confidence, single-line class — and validates the complete
pipeline through the harness `Detector` seam. **Deterministic only; no taint / interprocedural /
data-flow / AI.** The eval harness (`eval/harness/*`) is unchanged.

- **Reusable scanning foundation** (`.../deterministic/rules.py`): `PatternRule` (frozen: id, name,
  cwe, `frozenset[Language]`, regex) + a rule-agnostic engine `scan_tree(root, rules, *,
  detector_name)` that walks a tree, selects files by extension→`Language`, applies rules per line,
  and emits `eval.harness.runner.Finding`s. Future pattern analyzers reuse this by supplying rules;
  the full YAML rule engine remains deferred (TASK-241).
- **Secret rule pack** (`.../deterministic/secret_rules.py`): one high-confidence rule — a
  secret-suggestive identifier (`password|secret|token|api_key|…`) assigned directly to a string
  literal — which flags the literal case and excludes environment reads. Applies to Python + Web.
- **Analyzer** (`.../deterministic/secret_scanner.py`): `SecretScanner.scan(corpus_root) ->
  list[Finding]` satisfies the harness `Detector` protocol; plugs straight into `evaluate_corpus`.
- **No secret leakage**: findings carry only file, location, `rule_id`, and CWE — never the matched
  value (test asserts the secret string is absent from the serialized finding).
- **Tooling extended**: backend `pytest.ini` (`pythonpath = . ..`) and `pyproject.toml`
  (`mypy_path = ".."`) so backend resolves the `eval.harness` contract. *(Coupling note: product
  code imports `eval.harness` for the `Finding`/`Detector` contract; a shared-contract relocation can
  be revisited when the backend scan pipeline lands.)*
- **DoD gates green**: backend `ruff check .` clean, `mypy app` clean (18 files), `pytest` = 27
  passed, coverage **98.86%** (gate 80%); eval harness gates still green (ruff/mypy clean; 93 passed).
  Manual validation via `evaluate_corpus`: `web_curated_ts` → TP=1/FP=0/FN=1, **P=1.0, R=0.5**;
  `project_curated` → TP=2/FP=0/FN=8, **P=1.0, R=0.2** (misses other CWE classes by design; env-read
  safe examples correctly not flagged). Corresponds to backlog TASK-270 (secret/pattern scanner).

## MVP deterministic analyzer roadmap (approved 2026-07-17)
Pattern-based, high-confidence analyzers only (no taint/interprocedural/data-flow/AI), each paired
with a small curated corpus (2 vulnerable + 2 safe). Order: **#1 Hardcoded secrets (CWE-798) ✅ →
#2 Dynamic code execution (CWE-95) ✅ → #3 Weak cryptography (CWE-327/328) ✅ → #4 Unsafe
deserialization (CWE-502) ✅ → #5 TLS verification disabled (CWE-295) ✅ → #6 Reverse tabnabbing
(CWE-1022) ✅**. **MVP deterministic pattern-analyzer suite is now COMPLETE** (all six analyzers
shipped and harness-measured). (Weak crypto was pulled ahead of tabnabbing, then — at the reviewer's
direction — unsafe deserialization and then TLS-verify-off were prioritized ahead of tabnabbing.)
The **partial
DOM-XSS detector was deliberately dropped** — CWE-79 (and SQLi/CWE-89,
command injection/CWE-78, path traversal/CWE-22, SSRF/CWE-918) are owned by the future taint engine
(Phase 2: TASK-210/240/250/260), not by lower-precision pattern rules.

## Completed — Second deterministic analyzer: dynamic code execution + PatternAnalyzer (2026-07-17)
Roadmap item #2 (CWE-95/94), under `backend/app/services/deterministic/`. Introduces the reusable
`PatternAnalyzer` abstraction so analyzers differ only by their `PatternRule` list. **Deterministic
only; no taint/interprocedural/data-flow/AI.** Harness logic (`eval/harness/*` models/loader/
validator/runner/evaluation/metrics/interface) unchanged; only corpus data + the loader id-set test
were touched.

- **Reusable `PatternAnalyzer`** (`.../deterministic/analyzer.py`): a `Detector` implementation
  parameterized by a rule list + name; `SecretScanner` (CWE-798) was **refactored** to subclass it,
  and `CodeExecutionScanner` (CWE-95) is a second subclass — both differ only by their rulepack.
- **Code-execution rulepack** (`.../deterministic/code_execution_rules.py`): high-confidence
  dangerous-API rules — Python `eval`/`exec`, JS/TS `eval` / `new Function` — with a look-behind that
  excludes method-qualified safe forms (e.g. `ast.literal_eval`, `JSON.parse`).
- **Curated corpus** (`eval/corpus/committed/code-exec-curated/python/`, 2 vuln + 2 safe, CWE-95) +
  labels (`eval/labels/code-exec-curated.py.labels.json`) + registry descriptor `code_exec_py` +
  an eval regression test (`test_code_exec_corpus.py`); `test_loader.py` id-set updated.
- **DoD gates green**: backend `ruff`/`mypy app` clean (21 files), `pytest` = **35 passed**, coverage
  **99.00%** (gate 80%); eval harness `ruff`/`mypy --strict` clean (22 files), `pytest` = **94 passed**.
  Manual validation via `evaluate_corpus`: `code_exec_py` → TP=2/FP=0/FN=0, **P=1.0, R=1.0**;
  `web_curated_js` → TP=1/FP=0/FN=1, **P=1.0, R=0.5**; refactored `SecretScanner` behaviour unchanged
  (`project_curated` P=1.0, R=0.2).

## Completed — Third deterministic analyzer: weak cryptography (2026-07-18)
Weak-cryptography analyzer (CWE-327 broken cipher / CWE-328 weak hash), under
`backend/app/services/deterministic/`. Reuses `PatternAnalyzer` **unchanged** and the scanning engine
**unmodified** — a new rulepack + thin `WeakCryptoScanner` wrapper only. **Deterministic; no
taint/interprocedural/data-flow/AI/YAML rulepacks.** Harness logic unchanged (only corpus data + the
loader id-set test touched).

- **Rulepack** (`.../deterministic/weak_crypto_rules.py`): 4 `PatternRule`s covering **MD5, SHA-1**
  (weak hash → CWE-328) and **DES, 3DES, RC4** (weak cipher → CWE-327) across Python and JS/TS.
  Algorithm tokens are anchored to real crypto calls (`hashlib.md5(`, `createHash("md5")`, `DES.new(`,
  `createCipheriv("des…")`, `CryptoJS.*`, …) so names/comments are not flagged; SHA-256/512 and AES
  are structurally excluded. **Blowfish is deliberately excluded** — it is reserved for a future
  Security Best-Practices category (migrate-to-AES recommendation), not a CWE-327/328 vulnerability.
- **`WeakCryptoScanner`** (`.../deterministic/weak_crypto_scanner.py`): a `PatternAnalyzer` subclass.
- **Two curated corpora** (both 2 vuln + 2 safe, CWE-327/328) so Python **and** Web rules are
  measurable: `weak_crypto_py` (`weak-crypto-curated/python/`) and `weak_crypto_js`
  (`weak-crypto-curated/javascript/`) + labels + registry descriptors + eval regression test
  (`test_weak_crypto_corpus.py`); `test_loader.py` id-set updated. Corpus files are inert (never
  imported/executed) — no runtime crypto dependency.
- **No sensitive-data leakage**: findings carry only file/location/rule_id/CWE — never key material,
  hashed data, or matched text.
- **DoD gates green**: backend `ruff`/`mypy app` clean (23 files), `pytest` = **42 passed**, coverage
  **99.10%** (gate 80%); eval harness `ruff`/`mypy --strict` clean (23 files), `pytest` = **96 passed**.
  Manual validation via `evaluate_corpus`: `weak_crypto_py` and `weak_crypto_js` both →
  TP=2/FP=0/FN=0, **P=1.0, R=1.0**; Blowfish confirmed **not** flagged.

## Completed — Fourth deterministic analyzer: unsafe deserialization (2026-07-18)
Unsafe-deserialization analyzer (CWE-502 deserialization of untrusted data), under
`backend/app/services/deterministic/`. Reuses `PatternAnalyzer` **unchanged** and the scanning engine
**unmodified** — a new rulepack + thin `UnsafeDeserializationScanner` wrapper only. **Deterministic;
no taint/interprocedural/data-flow/AI/YAML rulepacks.** Harness logic unchanged (only corpus data +
the loader id-set test touched).

- **Rulepack** (`.../deterministic/unsafe_deserialization_rules.py`): 2 `PatternRule`s covering the
  highest-confidence sinks whose safe counterpart is a syntactically distinct API — Python
  `pickle.load`/`pickle.loads` and `yaml.load`/`yaml.load_all`; JS/TS `unserialize` /
  `serialize.unserialize` (node-serialize). The safe forms `yaml.safe_load`, `json.loads`, and
  `JSON.parse` are **structurally excluded** (not matched). Extended sinks (`dill`, `marshal`,
  `jsonpickle`, `js-yaml`) are **deferred to a future enhancement** to keep the pack focused.
- **`UnsafeDeserializationScanner`** (`.../deterministic/unsafe_deserialization_scanner.py`): a
  `PatternAnalyzer` subclass (detector name `unsafe-deserialization-scanner`).
- **Two curated corpora** (both 2 vuln + 2 safe, CWE-502) so Python **and** Web rules are measurable:
  `unsafe_deserialization_py` (`unsafe-deserialization-curated/python/`) and
  `unsafe_deserialization_js` (`unsafe-deserialization-curated/javascript/`) + labels + registry
  descriptors + eval regression test (`test_unsafe_deserialization_corpus.py`); `test_loader.py`
  id-set updated. Corpus files are inert (never imported/executed) — no runtime deserialization.
- **No sensitive-data leakage**: findings carry only file/location/rule_id/CWE — never payloads or
  matched text.
- **DoD gates green**: backend `ruff`/`mypy app` clean (25 files), `pytest` = **49 passed**, coverage
  **99.16%** (gate 80%); eval harness `ruff`/`mypy --strict` clean (24 files), `pytest` = **98 passed**.
  Manual validation via `evaluate_corpus`: `unsafe_deserialization_py` and `unsafe_deserialization_js`
  both → TP=2/FP=0/FN=0, **P=1.0, R=1.0**; safe `yaml.safe_load`/`json.loads`/`JSON.parse` confirmed
  **not** flagged.

## Completed — Fifth deterministic analyzer: TLS verification disabled (2026-07-18)
Disabled-TLS-certificate-verification analyzer (CWE-295 improper certificate validation), under
`backend/app/services/deterministic/`. Reuses `PatternAnalyzer` **unchanged** and the scanning engine
**unmodified** — a new rulepack + thin `TlsVerificationScanner` wrapper only. **Deterministic;
no taint/interprocedural/data-flow/AI/YAML rulepacks.** Harness logic unchanged (only corpus data +
the loader id-set test touched).

- **Rulepack** (`.../deterministic/tls_verification_rules.py`): 2 `PatternRule`s covering
  explicit verification-disabling flags whose safe counterpart is a distinct token — Python
  `verify=False` (requests/httpx kwarg **and** the `session.verify = False` attribute form) and
  `ssl._create_unverified_context(`; JS/TS `rejectUnauthorized: false`. The `verify` pattern matches
  **assignment forms only** and never the comparison `verify == False`; safe forms (`verify=True`,
  `ssl.create_default_context`, `rejectUnauthorized: true`, omitted) are structurally excluded.
  **Deliberately excluded** (need contextual/data-flow analysis or belong elsewhere):
  `urllib3.disable_warnings()`, `http://` vs `https://` (CWE-319), self-signed/custom-store handling,
  and `NODE_TLS_REJECT_UNAUTHORIZED=0` (environment config → future enhancement).
- **`TlsVerificationScanner`** (`.../deterministic/tls_verification_scanner.py`): a `PatternAnalyzer`
  subclass (detector name `tls-verification-scanner`).
- **Two curated corpora** (both 2 vuln + 2 safe, CWE-295) so Python **and** Web rules are measurable:
  `tls_verification_py` (`tls-verification-curated/python/`) and `tls_verification_js`
  (`tls-verification-curated/javascript/`) + labels + registry descriptors + eval regression test
  (`test_tls_verification_corpus.py`); `test_loader.py` id-set updated. Corpus files are inert (never
  imported/executed) — no real network or TLS calls.
- **No sensitive-data leakage**: findings carry only file/location/rule_id/CWE — never surrounding
  configuration or matched text.
- **DoD gates green**: backend `ruff`/`mypy app` clean (27 files), `pytest` = **56 passed**, coverage
  **99.21%** (gate 80%); eval harness `ruff`/`mypy --strict` clean (25 files), `pytest` = **100 passed**.
  Manual validation via `evaluate_corpus`: `tls_verification_py` and `tls_verification_js` both →
  TP=2/FP=0/FN=0, **P=1.0, R=1.0**; safe `verify=True`/`ssl.create_default_context`/
  `rejectUnauthorized: true` confirmed **not** flagged.

## Completed — Sixth (final) deterministic analyzer: reverse tabnabbing (2026-07-18)
Reverse-tabnabbing analyzer (CWE-1022 use of web link to untrusted target with `window.opener`
access), under `backend/app/services/deterministic/`. **Final analyzer in the MVP deterministic
pattern-analyzer suite.** Reuses `PatternAnalyzer` **unchanged** and the scanning engine
**unmodified** — a new rulepack + thin `ReverseTabnabbingScanner` wrapper only. **Deterministic;
no taint/interprocedural/data-flow/AI/YAML rulepacks; no contextual browser-behavior analysis.**
Harness logic unchanged (only corpus data + the loader id-set test touched).

- **Rulepack** (`.../deterministic/reverse_tabnabbing_rules.py`): 2 `PatternRule`s. HTML — an `<a>`
  tag with `target="_blank"` but no `rel="noopener"`/`rel="noreferrer"` in the same tag, matched
  **case-insensitively** (`(?i)`, so `TARGET`/`Target`/`_BLANK` are detected). JS/TS —
  `window.open(..., "_blank")` without `noopener` in the call. Negative-lookaheads are bounded to
  the tag (`[^>]`) / statement (`[^;]`), so mitigated forms (`rel="noopener"`, `rel="noreferrer"`,
  `rel="noopener noreferrer"`, `window.open(..., "noopener")`) are structurally excluded and a
  trailing `<!-- ... noopener ... -->` marker comment does not suppress a genuine finding. Scope is
  limited to `<a>` links and `window.open` (non-link `<form>`/`<area>` out of scope). ReDoS-safe.
- **`ReverseTabnabbingScanner`** (`.../deterministic/reverse_tabnabbing_scanner.py`): a
  `PatternAnalyzer` subclass (detector name `reverse-tabnabbing-scanner`).
- **Two curated corpora** (both 2 vuln + 2 safe, CWE-1022) so HTML **and** JS rules are measurable:
  `reverse_tabnabbing_html` (`reverse-tabnabbing-curated/html/`) and `reverse_tabnabbing_js`
  (`reverse-tabnabbing-curated/javascript/`) + labels + registry descriptors + eval regression test
  (`test_reverse_tabnabbing_corpus.py`); `test_loader.py` id-set updated. HTML `vulnerable_2.html`
  uses mixed-case `Target="_blank"` to exercise the case-insensitive rule through the harness. Corpus
  files are inert (never rendered/opened/executed); external URLs are `example.com`/`.org` placeholders.
- **Single-line limitation documented** (per approval): multi-line `<a>` tags and opener-nulling on a
  later line are out of scope by design (no data-flow).
- **No sensitive-data leakage**: findings carry only file/location/rule_id/CWE — never the href/URL
  or matched markup.
- **DoD gates green**: backend `ruff`/`mypy app` clean (29 files), `pytest` = **63 passed**, coverage
  **99.26%** (gate 80%); eval harness `ruff`/`mypy --strict` clean (26 files), `pytest` = **102 passed**.
  Manual validation via `evaluate_corpus`: `reverse_tabnabbing_html` and `reverse_tabnabbing_js` both
  → TP=2/FP=0/FN=0, **P=1.0, R=1.0** (incl. the mixed-case `Target=_blank` case); safe
  `rel="noopener"`/`rel="noreferrer"`/`window.open(..., "noopener")` confirmed **not** flagged.

## Completed — Deterministic framework stabilization (2026-07-18)
Post-milestone stabilization of the deterministic analyzer framework (approved review items
M1, M2, S1, S2, S3, S4, S6 — **no new analyzers, no architecture redesign**). Deferred by the
reviewer: M3 (shared `Finding`/`Detector` contract relocation → the Scan Pipeline milestone)
and S5 (`code_exec`→`code_execution` rename → not worth the churn). Nice-to-Have items left
for later. The scanning engine (`rules.py`) and `PatternAnalyzer` (`analyzer.py`) are unchanged.

- **S4 — analyzer registry** (`backend/app/services/deterministic/registry.py`): single source of
  truth `DETERMINISTIC_ANALYZERS` (all six analyzer instances, stable order) + `ANALYZERS_BY_NAME`;
  re-exported from the package `__init__`. Replaces ad-hoc scanner instantiation.
- **S1 — no more `detector_name` duplication**: `evaluate_corpus` now defaults `detector_name`
  from the detector's own `detector_name` attribute (explicit arg still overrides). Callers/tests
  no longer repeat the name string. `interface.py` was the only harness-logic module changed
  (authorized under S1); `runner`/`evaluation`/`metrics`/`loader`/`validator`/`models` logic unchanged.
- **S2 — shared test helper**: `write_file` fixture in `backend/tests/conftest.py`; the seven
  deterministic unit-test files dropped their duplicated local `_write`.
- **S3 — test consolidation**: five per-analyzer eval corpus-integrity tests collapsed into one
  parametrized `eval/harness/tests/test_deterministic_corpora.py`; six per-analyzer backend harness
  tests collapsed into one parametrized `backend/tests/test_deterministic_harness.py` (driven by the
  S4 registry; also asserts the S1 default). `project_curated`/`web_curated` corpus tests kept
  (different shape). Eleven superseded test files deleted.
- **M1/M2/S6 — documentation**: rewrote `eval/README.md` to steady state (committed corpora,
  runner/metrics/interface complete, Python+Web, the analyzer micro-corpora); refreshed the stale
  "no implementation exists / no real analyzer in this slice / later slice" docstrings in
  `eval/harness/__init__.py`, `evaluation.py`, and `runner.py`.
- **DoD gates green**: backend `ruff`/`mypy app` clean (30 files), `pytest` = **58 passed**, coverage
  **99.30%**; eval harness `ruff`/`mypy --strict` clean (22 files), `pytest` = **104 passed**. Manual
  validation: registry enumerates all six analyzers (`ANALYZERS_BY_NAME` consistent); `evaluate_corpus`
  called **without** `detector_name` correctly defaults it from each analyzer; all analyzer corpora
  still P=1.0/R=1.0.

## MVP Scan Pipeline — approved design (2026-07-18)
Deterministic scan pipeline over an extracted repo root, built in incremental slices. Accepts a
repo root + Target Languages selection (Auto Detect / Python / Web / both); Auto detects supported
languages and runs the matching analyzer groups (structured "no supported languages" result when
none); obtains analyzers **exclusively from the deterministic registry**; runs them deterministically
(fail-fast via `ScanExecutionError`); aggregates findings (language-scoped to the resolved groups)
into one triage-ready `ScanResult` with summary info (detected/selected groups, analyzers executed,
files scanned, findings count). **No** GitNexus / taint / REST / SARIF / resource budgets / finding_id
in this milestone. Approved adjustments: analyzer metadata (language groups, CWE coverage) lives in
the **registry** (not on `PatternAnalyzer`); manual selection supports Python, Web, or both.
Slices: **0 shared contract (M3) ✅** → 1 language foundation → 2 resolution + registry selection →
3 execution + aggregation → 4 triage-ready shaping.

## Completed — Scan Pipeline Slice 0: shared `contracts` package (M3, 2026-07-18)
Relocated the shared analysis contract out of the eval package so the backend no longer depends on
`eval.*` for its core value types (review item M3, done at the Scan Pipeline milestone as planned).

- **New neutral repo-root `contracts/` package** (with `py.typed`): owns `Language`,
  `SourceLocation`, `Finding`, the `Detector` protocol, and the validated field types
  (`NonEmptyStr`/`RelativePath`/`CweStr`). Both the backend and the eval harness import from here, so
  a `Finding` is **one class across the boundary** (verified: `eval.harness.runner.Finding is
  contracts.Finding`).
- **`eval` is now a package** (`eval/__init__.py`) so both import roots resolve `contracts` under a
  single top-level (repo root). `eval.harness.models`/`runner`/`evaluation` import the moved types
  from `contracts` and re-export them (via `__all__`) for backward compatibility; `Verdict`,
  `CorpusKind`, `ChecksumStr`, and the corpus/label models stay in `eval.harness.models`.
- **Backend `app/` no longer imports `eval.*`** — the deterministic engine, `PatternAnalyzer`, all
  six rule packs, and the registry now import `Finding`/`SourceLocation`/`CweStr`/`Language` from
  `contracts`. Engine/analyzer **logic is unchanged** (import source only). The eval harness still
  owns scoring; backend harness *tests* legitimately import harness APIs from `eval.harness`.
- **DoD gates green**: backend `ruff`/`mypy app` clean (30 files), `pytest` = **58 passed**, coverage
  **99.30%**; eval + contracts `ruff`/`mypy --strict` clean (24 files), `pytest` = **104 passed**.
  Manual validation: `Finding`/`SourceLocation`/`Language` are a single class across the boundary,
  analyzers emit `contracts.Finding`, `grep` confirms no `from eval` in `app/`, and end-to-end
  `evaluate_corpus` scoring is unchanged (weak_crypto_py P=1.0/R=1.0).

## Deferred (was In Progress)
- ZIP upload module (TASK-130) — **deferred**, not actively in progress. Parked Phase-1 item
  (see TASK_BACKLOG Phase 1); resumes when Phase 1 is scheduled. Current active work stream is the
  deterministic analyzer suite on `feature/task-020a-evaluation-foundation`.

## Pending (next up — MVP critical path)
- Deterministic analyzers: **MVP pattern-analyzer suite COMPLETE** — secrets (CWE-798) +
  code-execution (CWE-95) + weak crypto (CWE-327/328) + unsafe deserialization (CWE-502) + TLS
  verification disabled (CWE-295) + reverse tabnabbing (CWE-1022), each with its own curated corpus
  and all harness-measured at P=1.0/R=1.0 on their corpora.
  Evaluation harness complete (TASK-020a/b/c + TASK-021). Deferred: YAML rulepack engine (TASK-241);
  harness deltas (Phase 4b)/aggregation/grouping; CWE-79/89/78/22/918 to the Phase-2 taint engine;
  Blowfish to a future Security Best-Practices category. OWASP Benchmark, Juliet, and the external
  fetcher remain **v2.0**.
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
feature/task-020a-evaluation-foundation (Scan Pipeline Slice 0 — shared contracts package / M3; awaiting human review before merge)

## Last Completed Task
Scan Pipeline **Slice 0** — shared `contracts` package (M3 relocation). Moved `Language`,
`SourceLocation`, `Finding`, and the `Detector` protocol (+ validated field types) into a new
neutral repo-root `contracts/` package (with `py.typed`); made `eval` a package (`eval/__init__.py`)
so both roots resolve `contracts` under one import root; `eval.harness` re-exports the moved types
for backward compatibility; backend `app/` now imports the contract from `contracts` and **no longer
imports `eval.*`** (engine/analyzer logic unchanged — import source only). `Finding` is a single
class across the boundary (verified). Backend gates green (ruff/mypy clean; pytest 58 passed; coverage
99.30%); eval + contracts gates green (ruff/mypy --strict clean, 24 files; pytest 104 passed); manual
validation passed; awaiting human review before merge. Next: Scan Pipeline Slice 1 (language
foundation). Prior: deterministic framework stabilization pass (approved review items M1/M2/S1/S2/S3/
S4/S6; S5 deferred). Added the analyzer registry (`registry.py`: `DETERMINISTIC_ANALYZERS` /
`ANALYZERS_BY_NAME`, re-exported from the package `__init__`) as the single source of truth;
`evaluate_corpus` now defaults `detector_name` from the detector's own attribute (removed the
duplicated name string from every caller/test); added a shared `write_file` conftest fixture and
dropped seven local `_write` copies; consolidated five eval corpus tests + six backend harness
tests into two registry-driven parametrized tests and deleted eleven superseded files; rewrote
`eval/README.md` and refreshed stale slice-oriented docstrings (`eval/harness/__init__.py`,
`evaluation.py`, `runner.py`) (2026-07-18). Scanning engine (`rules.py`) and `PatternAnalyzer`
(`analyzer.py`) unchanged; `interface.py` changed only for the S1 default. Backend gates green
(ruff/mypy clean; pytest 58 passed; coverage 99.30%); eval harness gates green (ruff/mypy --strict
clean; 104 passed); manual validation: registry enumerates all six analyzers and the `detector_name`
default resolves from each analyzer, all corpora still P=1.0/R=1.0; awaiting human review before
merge. Prior: sixth and final MVP deterministic analyzer — reverse tabnabbing (CWE-1022): rulepack
`reverse_tabnabbing_rules.py` (HTML `<a target="_blank">` without `rel=noopener`/`noreferrer`,
case-insensitive; JS/TS `window.open(..., "_blank")` without `noopener`; `<form>`/`<area>` and
multi-line/data-flow cases out of scope) + thin `ReverseTabnabbingScanner` (a `PatternAnalyzer`
subclass), under `backend/app/services/deterministic/`; two new curated corpora
`reverse_tabnabbing_html` + `reverse_tabnabbing_js` (each 2 vuln + 2 safe; HTML `vulnerable_2` uses
mixed-case `Target=_blank`) + labels + registry entries + eval regression test; backend tests
(`test_reverse_tabnabbing_scanner.py`, `test_reverse_tabnabbing_harness.py`) (2026-07-18).
`PatternAnalyzer` and the scanning engine reused unchanged; deterministic only (no
taint/interproc/data-flow/AI/YAML/browser-context). **This completes the MVP deterministic
pattern-analyzer suite (6 analyzers).** Backend gates green (ruff/mypy clean; pytest 63 passed;
coverage 99.26%); eval harness gates green (ruff/mypy --strict clean; 102 passed); manual validation
`reverse_tabnabbing_html` and `reverse_tabnabbing_js` both P=1.0/R=1.0, safe forms not flagged;
awaiting human review before merge. Prior: 5th analyzer — TLS certificate verification disabled
(CWE-295): rulepack
`tls_verification_rules.py` (Python `verify=False` incl. `session.verify = False`, assignment-only
not the `==` comparison, + `ssl._create_unverified_context()`; JS/TS `rejectUnauthorized: false`;
`urllib3.disable_warnings`/`NODE_TLS_REJECT_UNAUTHORIZED` excluded) + thin `TlsVerificationScanner`
(a `PatternAnalyzer` subclass), under `backend/app/services/deterministic/`; two new curated corpora
`tls_verification_py` + `tls_verification_js` (each 2 vuln + 2 safe) + labels + registry entries + eval
regression test; backend tests (`test_tls_verification_scanner.py`, `test_tls_verification_harness.py`)
(2026-07-18). `PatternAnalyzer` and the scanning engine reused unchanged; deterministic only (no
taint/interproc/data-flow/AI/YAML). Backend gates green (ruff/mypy clean; pytest 56 passed; coverage
99.21%); eval harness gates green (ruff/mypy --strict clean; 100 passed); manual validation
`tls_verification_py` and `tls_verification_js` both P=1.0/R=1.0, safe forms not flagged; awaiting
human review before merge. Prior: 4th analyzer — unsafe deserialization (CWE-502): rulepack
`unsafe_deserialization_rules.py` (Python `pickle.load`/`pickle.loads` + `yaml.load`/`yaml.load_all`;
JS/TS node-serialize `unserialize`/`serialize.unserialize`; safe `yaml.safe_load`/`json.loads`/
`JSON.parse` excluded; `dill`/`marshal`/`jsonpickle` deferred) + thin `UnsafeDeserializationScanner`
(a `PatternAnalyzer` subclass), under `backend/app/services/deterministic/`; two new curated corpora
`unsafe_deserialization_py` + `unsafe_deserialization_js` (each 2 vuln + 2 safe) + labels + registry
entries + eval regression test; backend tests (`test_unsafe_deserialization_scanner.py`,
`test_unsafe_deserialization_harness.py`) (2026-07-18). `PatternAnalyzer` and the scanning engine
reused unchanged; deterministic only (no taint/interproc/data-flow/AI/YAML). Also marked TASK-130
(ZIP upload) as deferred rather than in progress. Backend gates green (ruff/mypy clean; pytest 49
passed; coverage 99.16%); eval harness gates green (ruff/mypy --strict clean; 98 passed); manual
validation `unsafe_deserialization_py` and `unsafe_deserialization_js` both P=1.0/R=1.0, safe forms
not flagged; awaiting human review before merge. Prior: 3rd analyzer — weak cryptography
(CWE-327/328); 2nd analyzer — dynamic code execution (CWE-95) + reusable `PatternAnalyzer`; 1st
analyzer — hardcoded-secret scanner (CWE-798); **MVP evaluation harness complete** — TASK-021
interface, TASK-020c metrics, TASK-020b orchestration+matching, TASK-020a corpora+validator.
Prior: Engineering Foundation built and runtime-validated (2026-07-10) on
`feature/engineering-foundation`. Earlier: TASK-010R / TASK-010S doc reconciliation; TASK-012 baseline.
