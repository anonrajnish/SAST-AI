# Current Project State

**Updated:** 2026-07-19 (Reporting Layer Slice 2 — SARIF 2.1.0 export; prior: Reporting Layer Slice 1 — versioned JSON report export; Repository Upload Slice 3 — ZIP-bomb / resource-limit hardening; REST API Scan Endpoint Slice 2 — GET read side + typed-exception status mapping; Scan Endpoint Slice 1 — synchronous POST /api/v1/scans; Scan Job Lifecycle Slice 2 — thread-safe in-memory ScanJobStore; REST API Slice 1 — /version endpoint + API architecture; Scan Job Lifecycle Slice 1 — immutable in-memory scan-job models + transitions; Repository Upload Slice 2 — upload→scan orchestration; Upload Slice 1 — validated ZIP extraction; Scan Pipeline Slice 4 — triage-ready ordering / **MVP Scan Pipeline complete**; Slice 3 execution + aggregation; Slice 2 resolution + selection; Slice 1 language foundation; Slice 0 shared `contracts` package (M3))

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
Slices: **0 shared contract (M3) ✅** → **1 language foundation ✅** → **2 resolution + registry
selection ✅** → **3 execution + aggregation ✅** → **4 triage-ready shaping ✅**. **MVP Scan
Pipeline COMPLETE** (all five slices shipped; deterministic, registry-driven, triage-ready).

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

## Completed — Scan Pipeline Slice 1: language foundation (2026-07-18)
The target-language vocabulary and repository language-group detection, under the new
`backend/app/services/scan/` package. Foundation only — **no analyzer selection, no execution, no
AUTO/MANUAL resolution, no vulnerability scanning** (later slices).

- **Models** (`scan/models.py`): `LanguageGroup` (`PYTHON`, `WEB` — Web bundles JS/TS/HTML);
  `TargetMode` (`AUTO`, `MANUAL`); `ScanConfig` (frozen, `extra="forbid"`) with validation —
  **AUTO must carry no groups; MANUAL requires ≥1 group** — plus `ScanConfig.auto()` /
  `ScanConfig.manual(groups)` constructors (manual supports Python, Web, or both).
- **Detection** (`scan/detection.py`): `GROUP_BY_LANGUAGE` / `group_for_language` map the shared
  `contracts.Language` to a group (future-roadmap Java/C++/Go/C# map to nothing → ignored);
  `detect_language_groups(repo_root)` walks the tree by file extension (reusing `language_for` from
  the deterministic engine), skips symlinks/non-files, ignores unsupported types, and returns only
  the detected groups (empty for an empty/missing/unsupported tree). Read-only; no file contents read.
- **DoD gates green**: backend `ruff`/`mypy app` clean (33 files), `pytest` = **73 passed**, coverage
  **99.41%**; eval + contracts gates unaffected (still green). Manual validation: committed corpora →
  `{python, web}`, a Python-only corpus → `{python}`, an HTML corpus → `{web}`, `docs/` → `{}`; and
  the AUTO-with-groups / MANUAL-empty configs both raise `ValidationError`.

## Completed — Scan Pipeline Slice 2: resolution + registry-driven selection (2026-07-18)
AUTO/MANUAL target-group resolution and analyzer selection sourced entirely from the deterministic
registry. **No execution, no aggregation, no `scan_repository()`** (later slices). `ScanConfig` and
`PatternAnalyzer` unchanged.

- **`LanguageGroup` moved to `contracts`** (shared vocabulary, alongside `Language`) so the
  deterministic registry can carry group metadata without a `scan → deterministic → scan` import
  cycle; `scan` re-exports it, so `ScanConfig` and the Slice-1 public API are unchanged.
- **Registry enriched as the single source of truth** (`deterministic/registry.py`): new frozen
  `AnalyzerEntry` (analyzer + `language_groups` + `cwes`); `ANALYZER_REGISTRY` authors each analyzer's
  metadata (five analyzers → `{PYTHON, WEB}`; reverse-tabnabbing → `{WEB}` only; CWE coverage per
  analyzer). `DETERMINISTIC_ANALYZERS` / `ANALYZERS_BY_NAME` are now derived from it (backward
  compatible). **Language metadata lives in the registry, not on `PatternAnalyzer`.**
- **Resolution** (`scan/resolution.py`): `resolve_target_groups(config, detected_groups)` — AUTO →
  detected groups; MANUAL → the selected groups (detection ignored).
- **Selection** (`scan/selection.py`): `select_analyzers(groups, registry=ANALYZER_REGISTRY)` returns
  the registry analyzers whose metadata groups intersect `groups`, in **registry order** (empty groups
  → none); dependency-injectable registry; returns the registry's own analyzer instances.
- **DoD gates green**: backend `ruff`/`mypy app` clean (35 files), `pytest` = **84 passed**, coverage
  **99.45%**; eval + contracts `ruff`/`mypy --strict` clean (24 files), `pytest` = **104 passed**.
  Manual validation: AUTO resolves to detected, MANUAL ignores detected; `select_analyzers` →
  Python = 5 analyzers (Web-only reverse-tabnabbing excluded), Web / Python+Web = all 6, empty = none,
  all in registry order.

## Completed — Scan Pipeline Slice 3: execution + aggregation (2026-07-18)
The deterministic execution pipeline end to end: detect → resolve → select → execute → aggregate →
`ScanResult`. **No dedup, no `finding_id`, no AI triage, no SARIF, no GitNexus** (later/other work);
analyzer behavior unchanged.

- **Result models** (`scan/results.py`): `ScanStatus` (`COMPLETED` / `NO_SUPPORTED_LANGUAGES`);
  `AnalyzerRun` (detector_name + finding_count); `ScanResult` (frozen, `extra="forbid"`) with `status`,
  `detected_language_groups`, `resolved_language_groups`, `analyzer_runs`, `files_scanned`,
  `total_findings`, `findings` — JSON-serializable, ready for a future triage stage.
- **Entry point** (`scan/pipeline.py`): `scan_repository(repo_root, config, *, registry=ANALYZER_REGISTRY)`.
  Executes the selected analyzers in **registry order**, concatenating findings; findings are **scoped
  to the resolved language groups** (`_finding_in_scope`) so a MANUAL selection ignores other supported
  languages (analyzers unmodified). `files_scanned` = supported files in the resolved groups
  (`count_files_in_scope`, read-only, added to `detection.py`).
- **Structured no-language outcome**: AUTO detecting nothing supported returns `NO_SUPPORTED_LANGUAGES`
  with empty runs/findings (MANUAL always resolves to ≥1 group).
- **Errors** (`scan/errors.py`): `ScanError` base; `RepositoryError` (missing/not-a-directory root);
  `ScanExecutionError` (fail-fast wrap of an unexpected analyzer exception, carrying `detector_name`).
- **DoD gates green**: backend `ruff`/`mypy app` clean (38 files), `pytest` = **92 passed**, coverage
  **99.55%**; eval + contracts gates unaffected (still green). Manual validation over the committed
  weak-crypto corpus (mixed Python+JS): AUTO → both groups, 8 files, 4 findings, 6 analyzers; MANUAL
  Python → 4 files, 2 findings, 5 analyzers, all under `python/` (JS ignored); MANUAL Web → JS findings
  only; `docs/` AUTO → `NO_SUPPORTED_LANGUAGES`; missing root → `RepositoryError`.

## Completed — Scan Pipeline Slice 4: triage-ready ordering (2026-07-18) — MVP Scan Pipeline complete
Deterministic ordering of `ScanResult.findings` so the result is reproducible and diff-friendly for a
future triage stage. **Ordering only — no `finding_id`, no dedup, no AI/GitNexus/SARIF; the execution
pipeline (`pipeline.py`) and analyzers are unchanged** (ordering is applied by the result model, not
the pipeline).

- **Ordering** (`scan/ordering.py`): `finding_sort_key` = (file, start_line, end_line, detector,
  rule_id, cwe) — a total order over finding metadata; `order_findings(findings)` returns a stable
  sorted list (no dedup).
- **Applied in the result model** (`scan/results.py`): a `@field_validator("findings")` normalizes
  findings into deterministic order at `ScanResult` construction, so every result (pipeline-built or
  direct) is ordered without touching the pipeline. Added a `@field_serializer(..., when_used="json")`
  that emits the language-group sets as **sorted lists**, so the serialized result is stable across
  runs (frozenset iteration order can otherwise vary).
- **DoD gates green**: backend `ruff`/`mypy app` clean (39 files), `pytest` = **99 passed**, coverage
  **99.57%**; eval + contracts gates unaffected. Manual validation: findings globally path-ordered
  (not analyzer order); two runs over the same repo produce **byte-identical** serialized JSON; group
  sets serialize sorted (`["python","web"]`); result fully JSON-serializable.

**MVP Scan Pipeline (Slices 0–4) is complete**: `scan_repository(repo_root, config)` deterministically
detects languages, resolves AUTO/MANUAL targets, selects analyzers from the registry, executes them,
aggregates language-scoped findings, and returns a stable, triage-ready `ScanResult`. Not yet wired to
GitNexus, taint, REST, SARIF, persistence, or AI triage (future tasks).

## Completed — Repository Upload & Safe Extraction Slice 1: validated ZIP extraction (2026-07-18)
First slice of the Repository Upload & Safe Extraction subsystem (TASK-130 ZIP-upload module +
the pre-extraction security controls of TASK-131), under the new `backend/app/services/upload/`
package. Accepts a ZIP archive path, **fully validates it before writing anything**, safely
extracts it into a fresh temporary working directory, and returns the extracted repository root.
Deterministic; the archive is read read-only and no extracted file is ever imported or executed.
**Out of scope this slice** (later): ZIP-bomb / resource limits, ClamAV, cleanup scheduling,
language detection, scan-pipeline integration, REST/upload API, persistence/DB, Celery, Docker.

- **Entry point** (`upload/extractor.py`): `extract_zip(archive_path, *, workspace_dir=None) ->
  ExtractedRepository`. Validation → extraction pipeline: require a readable `.zip` container →
  open read-only → validate every entry → CRC integrity check → only then create a temp dir
  (`tempfile.mkdtemp`, `sast-upload-` prefix) and write. Manual entry-by-entry write (never
  `extractall`): only regular files and directory entries, no mode/exec bits carried over.
- **Security controls**: **Zip Slip / traversal** and **absolute paths** rejected (`..` component,
  absolute, Windows separator/drive, empty/NUL name → `PathTraversalError`); **symlink** entries
  (`SymlinkEntryError`) and **non-regular special files** — FIFO/device/socket (`SpecialFileError`)
  rejected via the entry's unix mode; **nested archives** (`.zip/.tar/.gz/.7z/.rar/…`, incl.
  compound `.tar.gz`) rejected (`NestedArchiveError`); **encrypted/password-protected** ZIPs
  rejected via GP-flag bit 0 (`EncryptedArchiveError`); **non-ZIP** types (`UnsupportedArchiveError`)
  and **invalid/corrupted/missing** ZIPs (`CorruptedArchiveError`, incl. bad-CRC via `testzip`).
  Because validation precedes any write, a rejected archive **leaves no partial extraction**; an
  unexpected mid-write failure removes the temp dir (`shutil.rmtree`).
- **Typed models & errors** (`upload/models.py`, `upload/errors.py`): frozen `ExtractedRepository`
  (`root`, `file_count`, `directory_count`; JSON-serializable); `UploadError` base with the typed
  subclasses above (`UnsafeArchiveEntryError` carries the offending `entry_name`/`reason`).
- **Tests** (`backend/tests/test_upload_extraction.py`, 16 tests): valid ZIP (content + counts +
  root under workspace + files not executable), empty ZIP, Zip Slip, absolute path, Windows
  separator, empty entry name, no-partial-extraction on rejection, symlink, special file, nested
  `.zip`, nested `.tar.gz`, directory named like an archive (allowed), encrypted (byte-patched GP
  flag), garbage/corrupted, bad-CRC, non-`.zip` extension, missing file, and cleanup-on-failure.
- **Backward compatible**: no change to `scan`, `deterministic`, `contracts`, or `eval`; the
  scan pipeline is unaffected.
- **DoD gates green**: backend `ruff`/`mypy app` clean (43 files), `pytest` = **118 passed** (+15),
  coverage **99.65%** (upload package 100%); eval + contracts gates unaffected. Manual validation:
  every control exercised end-to-end (valid/empty extract correctly; all 11 rejection classes raise
  their typed error; rejected archives create no temp dir).

## Completed — Repository Upload Slice 2: upload→scan orchestration (2026-07-18)
Second slice of the Repository Upload & Safe Extraction subsystem (TASK-130/131). Adds the
**minimal orchestration layer** that connects the two completed subsystems into a one-call
"scan a ZIP" flow — `ZIP -> extract_zip() -> scan_repository() -> ArchiveScanResult` — reusing
both unchanged. No extraction or scan logic is duplicated; the orchestrator only coordinates.
**Out of scope this slice** (later/other work): REST/upload API, DB/persistence, cleanup
scheduling, GitNexus, AI, SARIF export, ZIP-bomb protection.

- **Public API** (`upload/orchestration.py`): `scan_archive(archive_path, config, *,
  workspace_dir=None) -> ArchiveScanResult`. Calls the existing `extract_zip` then the existing
  `scan_repository(extraction.root, config)` and returns both together. `workspace_dir` is a
  dependency-injection seam forwarded to extraction (keeps tests hermetic); the documented
  required signature is `scan_archive(archive_path, config)`.
- **Combined result** (`ArchiveScanResult`, frozen `extra="forbid"`): composes the two existing
  immutable models unchanged — `extraction: ExtractedRepository` + `scan: ScanResult`.
  JSON-serializable. No new fields, no re-shaping of either result.
- **Error handling — no wrapper exceptions**: `UploadError` subclasses (extraction) and
  `RepositoryError` / `ScanExecutionError` (scanning) propagate **unchanged** (the orchestrator
  catches nothing). On an extraction failure the scan stage is not run.
- **Reuse**: no changes to `upload/extractor.py`, `scan/`, `deterministic/`, `contracts`, or
  `eval`; `upload/__init__` now also exports `scan_archive` + `ArchiveScanResult`.
- **Tests** (`backend/tests/test_upload_scan_orchestration.py`, 8 tests): real end-to-end extract
  +scan (Python weak-crypto finding surfaced), empty ZIP → `NO_SUPPORTED_LANGUAGES`, MANUAL
  Python scoping through the orchestrator (JS excluded; detected `{python,web}` vs resolved
  `{python}`), frozen + `extra="forbid"` + JSON-serializable result, and four propagation tests
  (real Zip Slip `PathTraversalError` with the scan stage proven un-run; `UnsupportedArchiveError`,
  `RepositoryError`, `ScanExecutionError` propagate the exact instance unchanged).
- **DoD gates green**: backend `ruff`/`mypy app` clean (44 files), `pytest` = **126 passed** (+8),
  coverage **99.66%** (upload package 100%); eval + contracts gates unaffected. Manual validation:
  ZIP→extract→scan returns one `ArchiveScanResult` (findings from `a.py`, JSON-serializable);
  MANUAL scoping honored; empty ZIP → `NO_SUPPORTED_LANGUAGES`; Zip Slip `PathTraversalError`
  propagates unchanged.

## Completed — Scan Job Lifecycle Slice 1: immutable in-memory scan-job models (2026-07-18)
First slice of the Scan Job Lifecycle (skeleton portion of TASK-120 "Scan orchestrator + job
lifecycle"), under the new `backend/app/services/jobs/` package. Introduces the **Scan Job**
concept — an immutable lifecycle *around* an `ArchiveScanResult` — **without changing the upload
subsystem or scan pipeline**. Synchronous today; the model shape prepares for future async.
**In-memory only** — no DB, persistence, Celery, background workers, queues, REST/WebSockets,
progress reporting, cancellation, or retries (all explicitly out of scope this slice).

- **Status vocabulary** (`jobs/models.py` `ScanJobStatus`, StrEnum): `PENDING`, `RUNNING`,
  `COMPLETED`, `FAILED` — a subset of the architecture's `scans.status`
  (pending/running/completed/failed/cancelled); **`RUNNING` is reserved** so a future async
  executor can mark a job in progress without a model change, and **`cancelled` is deferred**
  with cancellation.
- **Immutable models** (frozen, `extra="forbid"`, fully typed, JSON-serializable, deterministic):
  `ScanJobResult` wraps the successful `ArchiveScanResult` (kept distinct so job-level result
  metadata can grow independently); `ScanJob` = `job_id`, `status`, `created_at`, optional
  `completed_at` / `result` / `error`, plus an `is_terminal` property. A `model_validator`
  enforces the state machine's invariants (terminal ⇒ `completed_at`; `COMPLETED` ⇒ `result`
  and no `error`; `FAILED` ⇒ non-empty `error` and no `result`; non-terminal ⇒ none of these),
  so no inconsistent job can be constructed.
- **Transitions** (`jobs/lifecycle.py`, pure & deterministic — each returns a **new** snapshot):
  `create_scan_job(*, job_id=None, created_at=None) -> PENDING`; `complete_scan_job(job, result,
  *, completed_at=None) -> COMPLETED`; `fail_scan_job(job, error, *, completed_at=None) ->
  FAILED`. `job_id`/timestamps are injectable for full determinism (defaults: `uuid4` / UTC now).
  `complete`/`fail` accept any non-terminal job (PENDING **or** RUNNING → forward-compatible);
  transitioning a terminal job raises the typed `InvalidScanJobTransitionError`
  (`jobs/errors.py`, `ScanJobError` base; carries `current_status` + `attempted`).
- **Existing code unchanged**: no edits to `upload/`, `scan/`, `deterministic/`, `contracts`, or
  `eval`. `ArchiveScanResult` remains the scan output; `ScanJob` only owns the lifecycle around it.
- **Tests** (`backend/tests/test_scan_job_lifecycle.py`, 23 tests): creation (PENDING; unique UUID
  + tz-aware defaults), successful completion (result attached, `created_at` carried, defaults),
  completion **from RUNNING** (forward-compat), transition returns a new snapshot leaving the
  original untouched, failed completion, invalid transitions (complete/fail on COMPLETED or
  FAILED → `InvalidScanJobTransitionError` with status/verb), parametrized state-consistency
  invariants (6 inconsistent constructions rejected) incl. empty-error rejection, JSON round-trip
  + deterministic serialization, immutability, and an integration test running a **real**
  `scan_archive` output through `create -> complete`.
- **DoD gates green**: backend `ruff`/`mypy app` clean (48 files), `pytest` = **149 passed** (+23),
  coverage **99.70%** (jobs package 100%); eval + contracts gates unaffected. Manual validation:
  create→complete (real scan output, 1 finding; original job unchanged), create→fail, invalid
  transition rejected with typed error, JSON round-trip equal, and attribute mutation blocked.

## Completed — REST API Slice 1: /version endpoint + API architecture (2026-07-18)
First slice of the incremental REST API build-out. The FastAPI **application skeleton, versioned
router structure, `/health` (+ `/live`/`/ready`), and DI wiring (`SettingsDep`/`SessionDep`)
already exist from the Engineering Foundation** — this slice **reuses them unchanged** and adds the
one genuinely-missing piece, the **`/version` endpoint**, while establishing the API architecture
for future scan endpoints. No scan/upload/job endpoints, no auth, no DB/persistence, no workers,
WebSockets, AI, or GitNexus (all out of scope).

- **App metadata single source of truth** (`app/meta.py`, new): `APP_NAME` / `APP_VERSION` /
  `API_VERSION`. The application factory now reads `APP_NAME`/`APP_VERSION` from it (was hardcoded
  in `main.py`), so the FastAPI title/version and the `/version` payload **cannot drift**.
- **`/version` endpoint** (`app/api/v1/version.py`, new): `GET /api/v1/version` → typed
  `VersionResponse` (`name`, `version`, `api_version`, `app_env`). Read-only; touches no datastore
  and **no business subsystem** (upload/scan/jobs) — it reads static metadata plus the injected
  settings, demonstrating the DI pattern future feature routers reuse.
- **Router wiring** (`app/api/router.py`): the version router is mounted alongside health on the
  `api_router` aggregator (the single `/api/v1` extension point where future scan routers will be
  added). No new prefixes beyond health/version.
- **Existing code**: `main.py` edited only to source title/version from `app/meta.py`; `router.py`
  gains the version include + an extension-point docstring. `config.py`, `health.py`,
  `dependencies.py`, and every service package (`upload`/`scan`/`jobs`/`deterministic`/`contracts`/
  `eval`) are **unchanged**.
- **Tests** (`backend/tests/test_version.py`, 6 tests): `/version` returns the metadata and its
  exact field set; the reported version equals the OpenAPI/app version (drift guard); health routes
  still 200; **no scan/upload endpoints are exposed**; and the OpenAPI path set is exactly
  `{/health, /health/live, /health/ready, /version}` (architecture-only guarantee).
- **DoD gates green**: backend `ruff`/`mypy app` clean (50 files), `pytest` = **155 passed** (+6),
  coverage **99.70%** (new `version.py`/`meta.py` 100%); eval + contracts gates unaffected. Manual
  validation: `GET /api/v1/version` → 200 `{name, version, api_version, app_env}`, app title/version
  sourced from the shared constant, only health+version paths exposed, health intact.

## Completed — Scan Job Lifecycle Slice 2: thread-safe in-memory ScanJobStore (2026-07-18)
Second slice of the Scan Job Lifecycle (TASK-120 skeleton). Adds `ScanJobStore` — a **thread-safe
in-memory registry** of immutable `ScanJob` snapshots, the intended **single source of truth** for
job state that future REST endpoints will read/write. **In-memory only** — no DB, persistence,
Redis, Celery, background workers, REST/upload/scan-pipeline/GitNexus/AI changes (all out of scope).
The Slice-1 `ScanJob`/`ScanJobResult`/`ScanJobStatus` models and lifecycle functions are **reused
unchanged**.

- **Store** (`jobs/store.py` `ScanJobStore`): a `dict[str, ScanJob]` guarded by a single
  `threading.Lock`. `create(job)` (rejects a duplicate `job_id`), `get(job_id)` (raises if absent),
  `update(job)` (replaces an existing snapshot; raises if absent — never creates), `list()`
  (returns an immutable `tuple` in a **deterministic** order: `created_at` then `job_id`). The store
  holds the frozen snapshots by reference and returns them directly — it does not copy, wrap, or
  mutate jobs, and does **not** police transition validity (that stays with the lifecycle functions).
- **Typed store errors** (`jobs/errors.py`, extended): `DuplicateScanJobError` and
  `ScanJobNotFoundError` (both `ScanJobError` subclasses carrying `job_id`) — ready to map to
  409/404 when REST endpoints arrive.
- **Tests** (`backend/tests/test_scan_job_store.py`, 13 tests): create/get (stored by reference),
  duplicate-id rejection, missing get/update, update replaces snapshot + never creates, empty list,
  deterministic ordering (inserted out of order), list returns an independent immutable snapshot,
  serialization compatibility (completed job with nested `ArchiveScanResult` round-trips; every
  `list()` item round-trips), a full-lifecycle integration (store tracks PENDING→COMPLETED), and
  **thread safety** (500 concurrent unique creates all recorded; 500 concurrent updates leave
  exactly one uncorrupted job).
- **DoD gates green**: backend `ruff`/`mypy app` clean (51 files), `pytest` = **168 passed** (+13),
  coverage **99.72%** (jobs package 100%); eval + contracts gates unaffected. Manual validation:
  create/get/update/duplicate/missing/list-ordering behave as designed; 1000 concurrent creates →
  1000 recorded (no loss); stored jobs remain JSON-serializable.

## Completed — REST API Scan Endpoint Slice 1: synchronous POST /api/v1/scans (2026-07-18)
First scan endpoint — the **vertical slice that converges upload + scan + jobs** over REST. It only
orchestrates existing components (no new extraction/scan/job logic) and runs **synchronously**. No
multipart upload, background workers, Celery/Redis, DB persistence, auth, WebSockets, GitNexus, AI,
SARIF/JSON export, progress, cancellation, or retries.

- **Endpoint** (`app/api/v1/scans.py`): `POST /api/v1/scans` → `create_scan_job()` → `store.create` →
  `scan_archive(archive_path, config)` → `complete_scan_job` / `fail_scan_job` → `store.update` →
  returns the final `ScanJob` (`response_model=ScanJob`). Reuses `ScanJob`, `ScanJobStore`,
  `scan_archive`, the upload subsystem, and the scan pipeline **unchanged**.
- **Request model** `ScanRequest` (`extra="forbid"`): `archive_path: Path` + `config: ScanConfig`
  (the **existing** `ScanConfig`, reused as a nested model so its AUTO/MANUAL validation applies to
  the request; defaults to AUTO). No multipart — uses the established archive-path approach.
- **Outcome contract**: a **known** upload/scan failure (`UploadError` / `ScanError`) is a recorded
  *outcome* — the job is marked `FAILED` and returned with **HTTP 200** (status/error in the body),
  not an HTTP error. Malformed requests (missing/extra fields, invalid `ScanConfig` combos) are
  rejected by request validation with **HTTP 422 before any job is created**. Unexpected exceptions
  are not swallowed (would surface as 500).
- **Shared store wiring** (`app/dependencies.py`): `get_scan_job_store()` — an `lru_cache`
  process-wide `ScanJobStore` singleton (the single source of truth) exposed as `ScanJobStoreDep`;
  tests override it via `app.dependency_overrides` for isolation. Router mounts the scans router on
  `api_router` (`app/api/router.py`).
- **Tests** (`backend/tests/test_scan_endpoint.py`, 11 tests): successful scan (COMPLETED + finding +
  store updated), MANUAL scoping through the API, three failure paths (missing archive, Zip Slip,
  and a monkeypatched `ScanExecutionError` → FAILED/200 with diagnostic), four invalid-request 422s
  (missing field, unknown field, AUTO-with-groups, MANUAL-without-groups — each leaving the store
  empty), response serialization round-trip (body reconstructs the stored `ScanJob`), and the
  singleton store provider. `test_version.py` route-set guard updated to include `/api/v1/scans`.
- **DoD gates green**: backend `ruff`/`mypy app` clean (52 files), `pytest` = **178 passed** (+10),
  coverage **99.73%** (`scans.py`/`dependencies.py` 100%); eval + contracts gates unaffected. Manual
  validation (live TestClient): success → COMPLETED (1 finding, stored); MANUAL python scopes to
  `a.py`; missing archive → FAILED/200 with `CorruptedArchiveError` diagnostic; AUTO-with-groups →
  422 with no job created.

## Completed — REST API Scan Endpoint Slice 2: GET read side + exception mapping (2026-07-19)
The REST **read side**, completing the minimal scan surface. Reuses `ScanJobStore` **unchanged**;
adds no extraction/scan/job logic. No multipart, persistence, auth, workers, WebSockets, GitNexus,
AI, or export.

- **`GET /api/v1/scans`** (`app/api/v1/scans.py` `list_scans`): returns `store.list()` — the
  deterministic job list (by `created_at`, then `job_id`) — as `list[ScanJob]`.
- **`GET /api/v1/scans/{job_id}`** (`get_scan`): returns `store.get(job_id)`; an unknown id raises
  `ScanJobNotFoundError`, mapped to **404**. No per-endpoint try/except — the endpoint just lets the
  typed error propagate.
- **App-level exception mapping** (`app/api/exception_handlers.py`, new; wired in `create_app`):
  `register_exception_handlers(app)` maps `ScanJobNotFoundError → 404` and `DuplicateScanJobError →
  409` (JSON `{"detail": ...}`). Request-validation errors keep FastAPI's default **422**. The
  mapping is app-wide, so the existing POST path's `store.create` collision now surfaces as 409 too.
- **Do-not-modify honored**: no changes to the upload subsystem, scan pipeline, orchestration, scan
  jobs, `ScanJobStore`, analyzer registry, or deterministic analyzers. Only additive API wiring
  (`main.py` registers handlers; `router.py` already mounts the scans router).
- **Tests** (`backend/tests/test_scan_endpoint.py`, +7): empty list, deterministic ordering (seeded
  out of order), list reflects a submitted scan, get existing job (round-trips to the stored job),
  missing job → 404 (detail carries the id), and duplicate → 409 (POST forced to collide via a
  monkeypatched id). `test_version.py` route-set guard updated with `/api/v1/scans/{job_id}`.
- **DoD gates green**: backend `ruff`/`mypy app` clean (53 files), `pytest` = **184 passed** (+6),
  coverage **99.74%** (`scans.py`/`exception_handlers.py`/`main.py` 100%); eval + contracts
  unaffected. Manual validation (live TestClient): empty list `[]`; ordering `[a,b]` (seeded b,a);
  get existing → 200; missing → 404 `{"detail":"scan job not found: 'nope'"}`; POST then GET reflects
  the completed job; forced collision → 409 `{"detail":"scan job already exists: 'a'"}`.

## Completed — Repository Upload Slice 3: ZIP-bomb / resource-limit hardening (2026-07-19)
Hardens the existing extractor against resource-exhaustion attacks (TASK-131, P0), landing **with**
the feature now that it is reachable through the REST API. Reuses the Slice-1 extractor structure;
the scan pipeline, upload orchestration, REST API, scan jobs, deterministic analyzers, and eval
harness are **unchanged**. No ClamAV, persistence, cleanup scheduler, workers, GitNexus, or AI.

- **Configurable limits** (`upload/limits.py` `ExtractionLimits`, frozen, all `> 0`):
  `max_archive_bytes`, `max_total_uncompressed_bytes`, `max_file_count`, `max_compression_ratio`.
  Defaults live in **`app.config.Settings`** (env-overridable, e.g. `EXTRACTION_MAX_ARCHIVE_BYTES`):
  100 MiB archive / 1 GiB extracted / 10 000 entries / 100:1 ratio. `extract_zip` gained an optional
  `limits` param; when omitted it sources them from settings (`_default_limits`), so the bounds are
  configurable through the existing configuration system **without** threading a param through the
  (unchanged) orchestration/REST layers.
- **Enforcement — before and during extraction** (`upload/extractor.py`): before opening, the
  on-disk archive size is checked (`ArchiveTooLargeError`); from the central directory (pre-write),
  member count (`FileCountLimitError`), total declared uncompressed size (`ExtractedSizeLimitError`),
  and the overall compression ratio (`CompressionRatioLimitError`) are checked — so a bomb is
  rejected **before any temp dir is created** and CRC/`testzip` never runs on it. During streaming,
  `_copy_with_limit` caps the **actual** bytes written at `max_total_uncompressed_bytes`, so a lying
  central-directory header cannot bypass the extracted-size limit; a mid-stream abort cleans up.
- **Typed exceptions** (`upload/errors.py`): `ResourceLimitError(UploadError)` base (carries
  `actual`/`limit`) + one subclass per limit (above). Being `UploadError` subclasses, they propagate
  through `scan_archive` and map to a **FAILED job at HTTP 200** at the REST layer unchanged.
- **Tests** (`backend/tests/test_upload_limits.py`, 10 new; + propagation/REST tests): valid archive
  within limits; oversized archive; excessive file count; excessive extracted size; ZIP-bomb ratio
  (~1000:1 deflated payload); the streaming cap unit (`_copy_with_limit` aborts / returns total);
  all limit errors are `ResourceLimitError`; limits default from settings (patched `get_settings`);
  propagation through `scan_archive` (`test_upload_scan_orchestration.py`); and unchanged REST
  behavior — a limit violation → FAILED/200 (`test_scan_endpoint.py`). Updated the Slice-1
  cleanup-on-failure test to patch `_copy_with_limit` (extraction no longer uses `shutil.copyfileobj`).
- **DoD gates green**: backend `ruff`/`mypy app` clean (54 files), `pytest` = **195 passed** (+11),
  coverage **99.76%** (upload package + config 100%); eval + contracts gates unaffected. Manual
  validation: valid extract OK; oversized/file-count/extracted-size/ratio each raise their typed
  error (bomb caught at ~1014:1); rejected archives leave **no** temp dir; config defaults active.

## Completed — Reporting Layer Slice 1: versioned JSON report export (2026-07-19)
First slice of the Reporting Layer (TASK-170/450 export surface). A **pure, deterministic library**
that projects a `ScanResult` (+ caller-supplied `ReportMetadata`) into a dedicated, **versioned JSON
report envelope**. Read-only; carries only finding metadata (no source snippets). Design approved with
adjustments (single library; `ScanResult`+`ReportMetadata` input; dedicated envelope; failed-job
reports out of scope; the summary section added; `REPORT_SCHEMA_VERSION` name; `detector_counts`
added). **No SARIF, REST export, persistence, or other formats** (later slices).

- **Package** (`backend/app/services/reporting/`): `metadata.py` (`ReportMetadata` — tool
  name/version + optional scan id/timestamps/target label, built by the caller); `models.py`
  (`REPORT_SCHEMA_VERSION="1.0"`; frozen `ReportTool`/`ReportScanInfo`/`ReportAnalyzerRun`/
  `ReportSummary`/`ReportFinding`/`ScanReport`); `reporter.py` (`build_json_report` → envelope,
  `render_json_report` → canonical JSON string).
- **Envelope**: `report_schema_version`, `tool{name,version}`, `scan{id,status,created_at,
  completed_at,target_label}`, `summary{...}`, `findings[]` (flattened to file/start_line/end_line/
  rule_id/cwe/detector — decoupled from the internal `Finding`/`SourceLocation` nesting).
- **Summary**: `total_findings`, `files_scanned`, `analyzers[{detector,finding_count}]` (registry
  order), sorted `detected/resolved_language_groups`, and three sorted-key count maps —
  `cwe_counts`, `rule_counts`, **`detector_counts`** — each counting findings by that field and
  omitting nulls (null-valued findings still appear in `findings[]`).
- **Deterministic & no-leakage**: findings consumed in `ScanResult`'s order; group lists sorted;
  count-map keys inserted sorted; canonical `json.dumps(indent=2, ensure_ascii=False)` + trailing
  newline → byte-identical re-renders. Only metadata is emitted (no snippets/matched text). Pure
  library — imports only `contracts` + `app.services.scan` (no jobs/upload/app.meta/config coupling).
- **`NO_SUPPORTED_LANGUAGES`** → valid empty report (zero totals, empty analyzers/count maps).
  Failed jobs (no `ScanResult`) are out of scope.
- **Tests** (`backend/tests/test_reporting_json.py`, 14): structure/metadata, ISO timestamps, the
  three count maps, sorted groups + sorted count keys, null-metadata excluded-from-counts, findings
  order preserved, finding key-set (no-leakage), valid-JSON round-trip, deterministic render,
  `NO_SUPPORTED_LANGUAGES`, immutability, and a real-scan integration.
- **DoD gates green**: backend `ruff`/`mypy app` clean (58 files), `pytest` = **208 passed** (+14),
  coverage **99.78%** (reporting package 100%); eval + contracts gates unaffected. Manual validation:
  rendered a report from a real mixed Python+Web scan (3 findings; `cwe_counts`/`rule_counts`/
  `detector_counts` correct), byte-identical re-render, valid JSON, and no source/secret text present.

## Completed — Reporting Layer Slice 2: SARIF 2.1.0 export (2026-07-19)
Second reporting serializer: exports `ScanResult` + `ReportMetadata` as a valid **SARIF 2.1.0** log.
Pure library, **independent of the JSON report** (both consume `ScanResult` directly; SARIF never
serializes `ScanReport`). No changes to scan pipeline, analyzers, upload, jobs, or REST.

- **SARIF object model** (`reporting/sarif_models.py`): frozen typed subset — `SarifLog` (`$schema`
  via serialization alias, `version="2.1.0"`, `runs`), `SarifRun`/`SarifTool`/`SarifToolComponent`,
  `SarifReportingDescriptor`, `SarifResult`, `SarifLocation`/`SarifPhysicalLocation`/
  `SarifArtifactLocation`/`SarifRegion`, `SarifMessage`, and the property bags.
- **Builder/renderer** (`reporting/sarif.py`): `build_sarif_report` / `render_sarif_report`
  (`json.dumps(..., by_alias=True, exclude_none=True)` + trailing newline → byte-deterministic).
- **Rule catalog — detector-grained (intentional MVP compromise, documented)**: one
  `reportingDescriptor` per registry analyzer (`id = detector_name`, CWE `tags` from `entry.cwes` +
  `security`, sorted), in registry order, injectable registry. Because the deterministic registry
  exposes analyzer metadata (not per-rule metadata), `result.ruleId = finding.detector`; the finer
  `rule_id` is preserved in `result.properties` + the fingerprint. Future versions may migrate to
  rule-level descriptors once the registry surfaces rule metadata.
- **Approved decisions applied**: every result `level: "warning"` (no per-rule severity); CWE via
  tags only (no taxonomy objects); `result.properties = {rule_id, cwe}`; **invocations omitted**;
  partial-fingerprint key **`aiSastFindingHash/v1`** = SHA-256 over
  `detector|rule_id|file|start_line|end_line|cwe`; **generic message** `"Potential security issue
  detected (CWE-XXX)."` (no rule names); `tool.driver.informationUri` sourced from a new nullable
  `ReportMetadata.information_uri` (omitted when absent). Region omitted when a finding has no line.
- **Tests** (`backend/tests/test_reporting_sarif.py`, 19): log skeleton, informationUri present/
  omitted, registry-mirrored catalog + CWE tags, full catalog with zero results, injected registry,
  result mapping (ruleId/ruleIndex/level/uri/region/properties), region-omitted, generic message
  (with/without CWE, hides rule name), unknown/null detector fallbacks, fingerprint key+value and
  per-component sensitivity, determinism, valid JSON, independence from the JSON envelope,
  immutability, and a real-scan no-leakage integration.
- **DoD gates green**: backend `ruff`/`mypy app` clean (60 files), `pytest` = **227 passed** (+19),
  coverage **99.80%** (reporting package 100%); eval + contracts unaffected. Manual validation:
  SARIF from a real mixed scan — valid 2.1.0, 6 detector rules, all `warning`, `aiSastFindingHash/v1`
  fingerprints, no invocations, byte-identical re-render, and no source/secret text present.

## In Progress
- Repository Upload & Safe Extraction subsystem (TASK-130/131) — **Slices 1–3 complete** (validated
  ZIP extraction; upload→scan orchestration; ZIP-bomb / resource-limit hardening). Later: ClamAV,
  extraction cleanup lifecycle, multipart upload + persistence.
- Reporting Layer (TASK-170/450 export) — **Slices 1–2 complete** (versioned JSON report + SARIF
  2.1.0, both pure-library). Next (separate): a REST `GET /api/v1/scans/{id}/report?format=json|sarif`
  endpoint; later, rule-level SARIF descriptors once the registry surfaces rule metadata.
- Scan Job Lifecycle (TASK-120 skeleton) — **Slices 1–2 complete** (immutable models + transitions;
  thread-safe `ScanJobStore`). Later slices: async execution (Celery), progress, cancellation.
- REST API (TASK-110/112 surface) — **Slice 1 (foundation) + Scan Endpoint Slices 1–2 complete**
  (`/version`; synchronous `POST /api/v1/scans`; `GET /api/v1/scans` + `GET /api/v1/scans/{id}`;
  typed-exception → 404/409 mapping). Next candidates: **ZIP-bomb / resource-limit hardening
  (Upload Slice 3, TASK-131, P0 — should land before real network exposure)**, then API middleware
  (rate-limit, security headers, CORS), then multipart upload.
- Scan Job Lifecycle (TASK-120 skeleton) — **Slice 1 complete** (immutable in-memory models +
  transitions, above). Later slices: an in-memory job store/registry, wiring `create → run
  scan_archive → complete/fail`, then (much later) async execution (Celery), progress, cancellation.

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
feature/task-020a-evaluation-foundation (Reporting Layer Slice 2 — SARIF 2.1.0 export; awaiting human review before merge)

## Last Completed Task
Reporting Layer **Slice 2** — SARIF 2.1.0 export (`reporting/sarif_models.py` + `reporting/sarif.py`;
`build_sarif_report`/`render_sarif_report`). Pure library, independent of the JSON report (both
consume `ScanResult` directly). Detector-grained `tool.driver.rules` from the deterministic registry
(id=detector_name, CWE tags from registry `cwes`) — an **intentional, documented MVP compromise**
(registry exposes analyzer, not rule, metadata), so `result.ruleId=finding.detector` with `rule_id`
kept in `properties` + fingerprint; future migration to rule-level descriptors noted. Applied approved
decisions: `level:"warning"` for all findings, CWE tags only (no taxonomies), `properties={rule_id,cwe}`,
**invocations omitted**, fingerprint key **`aiSastFindingHash/v1`** = SHA-256 over
detector|rule_id|file|start_line|end_line|cwe, generic message `"Potential security issue detected
(CWE-XXX)."`, and nullable `tool.driver.informationUri` (new `ReportMetadata.information_uri`, omitted
when absent); region omitted when no line. Byte-deterministic (`by_alias`+`exclude_none`); no source/
secret leakage. No scan/analyzer/upload/jobs/REST changes; no persistence/GitNexus/AI. Backend gates
green (ruff/mypy clean, 60 files; pytest 227 passed; coverage 99.80%, reporting package 100%);
eval+contracts unaffected; manual validation: valid SARIF from a real mixed scan (6 rules, all warning,
`aiSastFindingHash/v1`, no invocations, byte-identical re-render, no leakage); awaiting human review
before merge. Prior: Reporting Layer **Slice 1** — versioned JSON report export, under the new
`backend/app/services/reporting/` package. A pure, deterministic library projecting a `ScanResult`
+ caller-supplied `ReportMetadata` into a dedicated versioned envelope `ScanReport`
(`report_schema_version` + `tool` + `scan` + `summary` + flattened `findings`). Summary carries
`total_findings`, `files_scanned`, `analyzers`, sorted `detected/resolved_language_groups`, and
sorted-key `cwe_counts`/`rule_counts`/`detector_counts` (null-valued fields excluded from counts but
kept in findings). `build_json_report` / `render_json_report` (canonical `json.dumps`, trailing
newline) are byte-deterministic and leak no source/matched text (metadata only). Imports only
`contracts` + `app.services.scan` (pure library — no jobs/upload/meta/config coupling); `NO_SUPPORTED_
LANGUAGES` → valid empty report; failed jobs out of scope. No SARIF/REST/persistence/other formats.
Backend gates green (ruff/mypy clean, 58 files; pytest 208 passed; coverage 99.78%, reporting package
100%); eval+contracts unaffected; manual validation: real mixed scan → correct counts, byte-identical
re-render, valid JSON, no leakage; awaiting human review before merge. Prior:
Repository Upload **Slice 3** — ZIP-bomb / resource-limit hardening (TASK-131). Added configurable
`ExtractionLimits` (`upload/limits.py`; `max_archive_bytes` / `max_total_uncompressed_bytes` /
`max_file_count` / `max_compression_ratio`) with defaults in `app.config.Settings` (env-overridable);
`extract_zip` gained an optional `limits` param, defaulting from settings (`_default_limits`) so the
bounds are config-driven without changing the (untouched) orchestration/REST layers. Enforcement:
on-disk archive size before opening; member count / declared uncompressed total / compression ratio
from the central directory before any temp dir is created; plus a streaming `_copy_with_limit` cap on
actual bytes so a lying header can't bypass the extracted-size limit (mid-stream abort cleans up).
Typed `ResourceLimitError(UploadError)` base + `ArchiveTooLargeError`/`ExtractedSizeLimitError`/
`FileCountLimitError`/`CompressionRatioLimitError` (carry actual/limit) — propagate through
scan_archive and map to a FAILED job/200 at REST unchanged. Scan pipeline/orchestration/REST/jobs/
analyzers/eval unchanged; no ClamAV/persistence/cleanup-scheduler/workers/GitNexus/AI. Backend gates
green (ruff/mypy clean, 54 files; pytest 195 passed; coverage 99.76%, upload+config 100%);
eval+contracts unaffected; manual validation: each guard raises its typed error (bomb ~1014:1), no
partial extraction, config defaults active; awaiting human review before merge. Prior:
REST API **Scan Endpoint Slice 2** — the GET read side + exception mapping. `GET /api/v1/scans`
(`list_scans` → `store.list()` as `list[ScanJob]`, deterministic order) and `GET /api/v1/scans/{job_id}`
(`get_scan` → `store.get`, unknown id → `ScanJobNotFoundError`). Added app-level exception handlers
(`app/api/exception_handlers.py`, wired in `create_app`) mapping `ScanJobNotFoundError → 404` and
`DuplicateScanJobError → 409` (`{"detail": ...}`); request-validation stays 422. `ScanJobStore` and
all services reused unchanged; additive API wiring only. No multipart/persistence/auth/workers/
WebSockets/GitNexus/AI/export. Backend gates green (ruff/mypy clean, 53 files; pytest 184 passed;
coverage 99.74%, new code 100%); eval+contracts unaffected; manual validation (live TestClient):
empty list, deterministic ordering, get existing, missing→404, POST-then-GET reflects completed job,
forced collision→409; awaiting human review before merge. Prior:
REST API **Scan Endpoint Slice 1** — synchronous `POST /api/v1/scans` (`app/api/v1/scans.py`), the
vertical slice converging upload+scan+jobs. `ScanRequest{archive_path, config: ScanConfig=auto}`
(`extra="forbid"`, reuses `ScanConfig` validation → 422 on bad input); handler runs
`create_scan_job → store.create → scan_archive → complete/fail → store.update → return ScanJob`
(response_model=`ScanJob`), reusing all existing components unchanged and staying synchronous. Known
`UploadError`/`ScanError` failures → job `FAILED`, HTTP 200 (outcome in body); malformed requests →
422 before any job is created. Wired a process-wide `ScanJobStore` singleton via
`get_scan_job_store` (`lru_cache`) / `ScanJobStoreDep` (`app/dependencies.py`), overridable in tests;
mounted the scans router. No multipart/workers/Celery/Redis/DB/auth/WebSockets/GitNexus/AI/export/
progress/cancellation. Backend gates green (ruff/mypy clean, 52 files; pytest 178 passed; coverage
99.73%, scans.py/dependencies.py 100%); eval+contracts unaffected; manual validation (live
TestClient): success→COMPLETED+stored, MANUAL scoping, missing-archive→FAILED/200, AUTO+groups→422
no job; awaiting human review before merge. Prior: Scan Job Lifecycle **Slice 2** — thread-safe
in-memory `ScanJobStore` (`jobs/store.py`): a
`dict[str, ScanJob]` under a `threading.Lock` with `create` (duplicate-id → `DuplicateScanJobError`),
`get` / `update` (absent → `ScanJobNotFoundError`; update never creates), and `list()` (immutable
tuple ordered by `created_at` then `job_id`). Holds the immutable Slice-1 `ScanJob` snapshots by
reference (no copy/wrap/mutate) and doesn't police transitions — the single source of truth for
future REST endpoints. Added typed store errors (`DuplicateScanJobError`/`ScanJobNotFoundError`).
In-memory only (no DB/persistence/Redis/Celery/workers); no REST/upload/scan/GitNexus/AI changes;
Slice-1 models + lifecycle reused unchanged. Backend gates green (ruff/mypy clean, 51 files; pytest
168 passed; coverage 99.72%, jobs package 100%); eval+contracts unaffected; manual validation:
create/get/update/duplicate/missing/ordering correct, 1000 concurrent creates all recorded, stored
jobs JSON-serializable; awaiting human review before merge. Prior: REST API **Slice 1** — `/version`
endpoint + API architecture. Reused the existing Engineering-
Foundation FastAPI skeleton (app factory, `/api/v1` router aggregator, `/health` + `/live`/`/ready`,
`SettingsDep`/`SessionDep`) **unchanged** and added the missing pieces: `app/meta.py` (single source
of truth for `APP_NAME`/`APP_VERSION`/`API_VERSION`) and `app/api/v1/version.py` (`GET /api/v1/version`
→ typed `VersionResponse{name, version, api_version, app_env}`, DI-wired via `SettingsDep`, touching
no datastore or business subsystem); mounted the version router on `api_router`; `main.py` now sources
the FastAPI title/version from `app/meta.py` (drift-proof). No scan/upload/job endpoints, auth, DB,
persistence, workers, WebSockets, AI, or GitNexus. Backend gates green (ruff/mypy clean, 50 files;
pytest 155 passed; coverage 99.70%, new modules 100%); eval+contracts unaffected; manual validation:
`/api/v1/version` → 200 with correct metadata, OpenAPI path set exactly `{health, health/live,
health/ready, version}`, no scan endpoints exposed; awaiting human review before merge. Prior:
Scan Job Lifecycle **Slice 1** — immutable in-memory scan-job models + transitions, under the new
`backend/app/services/jobs/` package. `ScanJobStatus` (PENDING/RUNNING/COMPLETED/FAILED; RUNNING
reserved for future async, cancelled deferred); frozen `ScanJobResult` (wraps `ArchiveScanResult`)
and `ScanJob` (job_id/status/created_at/completed_at/result/error + `is_terminal`) with a
`model_validator` enforcing state-machine invariants; pure deterministic transitions
`create_scan_job` (→PENDING) / `complete_scan_job` (→COMPLETED) / `fail_scan_job` (→FAILED), each
returning a new snapshot, injectable job_id/timestamps, non-terminal→terminal only (else the typed
`InvalidScanJobTransitionError`). In-memory only (no DB/persistence/Celery/workers/queues/REST/
WebSockets/progress/cancellation/retries). Upload subsystem + scan pipeline unchanged;
`ArchiveScanResult` stays the scan output. Backend gates green (ruff/mypy clean, 48 files; pytest
149 passed; coverage 99.70%, jobs package 100%); eval+contracts unaffected; manual validation
exercised create→complete/fail, invalid transitions, JSON round-trip, and immutability; awaiting
human review before merge. Prior: Repository Upload **Slice 2** — upload→scan orchestration. Added the minimal orchestration layer
`scan_archive(archive_path, config, *, workspace_dir=None) -> ArchiveScanResult` (`upload/
orchestration.py`) that coordinates the two completed subsystems unchanged — `ZIP -> extract_zip()
-> scan_repository()` — and returns both results in one frozen `ArchiveScanResult` (`extraction:
ExtractedRepository` + `scan: ScanResult`; JSON-serializable). No extraction/scan logic duplicated;
`UploadError` and `RepositoryError`/`ScanExecutionError` propagate unchanged (no wrapper
exceptions; scan stage not run on an extraction failure). No changes to extractor/scan/
deterministic/contracts/eval. Backend gates green (ruff/mypy clean, 44 files; pytest 126 passed;
coverage 99.66%, upload package 100%); eval+contracts unaffected; manual validation exercised the
full flow (extract+scan, manual scoping, empty→NO_SUPPORTED_LANGUAGES, Zip-Slip propagation);
awaiting human review before merge. Prior: Repository Upload **Slice 1** — validated ZIP extraction, under the new
`backend/app/services/upload/` package. `extract_zip(archive_path, *, workspace_dir=None) ->
ExtractedRepository` fully validates a ZIP **before** writing (reject Zip Slip/traversal,
absolute paths, symlink/special-file entries, nested archives, encrypted and corrupted/non-ZIP
archives — each a typed `UploadError` subclass), then safely extracts regular files + directories
into a fresh temp dir (no `extractall`, no exec bits, nothing imported/executed) and returns the
repo root; rejected archives leave no partial extraction. ZIP-bomb/resource limits, ClamAV,
cleanup scheduling, and scan-pipeline integration are deferred to later slices. Backward
compatible (no change to `scan`/`deterministic`/`contracts`/`eval`). Backend gates green (ruff/mypy
clean, 43 files; pytest 118 passed; coverage 99.65%, upload package 100%); eval+contracts
unaffected; manual validation exercised every control end-to-end; awaiting human review before
merge. Prior: Scan Pipeline **Slice 4** — triage-ready ordering (**completes the MVP Scan Pipeline, Slices 0–4**).
`scan/ordering.py` (`finding_sort_key` over file/line/detector/rule_id/cwe + `order_findings`);
`ScanResult` normalizes findings into deterministic order via a `field_validator` (pipeline and
analyzers unchanged — ordering owned by the result model) and serializes the language-group sets as
sorted lists so the JSON result is stable across runs. Ordering only — no finding_id/dedup/AI/GitNexus/
SARIF. Backend gates green (ruff/mypy clean, 39 files; pytest 99 passed; coverage 99.57%);
eval+contracts unaffected; manual validation: findings globally path-ordered, byte-identical serialized
JSON across runs, groups serialize sorted, fully JSON-serializable; awaiting human review before merge.
Prior: Slice 3 — deterministic execution + aggregation (`scan_repository`, `ScanResult`). `scan_repository(repo_root, config)`
runs detect → resolve → select → execute (registry order) → aggregate → `ScanResult` (`ScanStatus`,
`AnalyzerRun`, detected/resolved groups, files_scanned, total_findings, findings). Findings scoped to
resolved groups so MANUAL ignores other languages (analyzers unmodified); AUTO with nothing supported →
`NO_SUPPORTED_LANGUAGES`; missing root → `RepositoryError`; unexpected analyzer failure →
`ScanExecutionError` (fail-fast). No dedup/finding_id/AI/SARIF/GitNexus. Backend gates green (ruff/mypy
clean, 38 files; pytest 92 passed; coverage 99.55%); eval+contracts unaffected; manual validation over
the committed corpora passed; awaiting human review before merge. Next: Scan Pipeline Slice 4
(triage-ready result shaping). Prior: Slice 2 — AUTO/MANUAL resolution + registry-driven analyzer
selection.
`resolve_target_groups(config, detected)` (AUTO→detected, MANUAL→selected); `select_analyzers(groups)`
returns registry analyzers whose metadata groups intersect, in registry order. Enriched the
deterministic registry as the single source of truth: `AnalyzerEntry` (analyzer + `language_groups` +
`cwes`) + `ANALYZER_REGISTRY`, with `DETERMINISTIC_ANALYZERS`/`ANALYZERS_BY_NAME` derived from it;
moved `LanguageGroup` to `contracts` to avoid an import cycle (scan re-exports it; `ScanConfig` and
`PatternAnalyzer` unchanged — no language metadata on the analyzer). No execution/aggregation/
`scan_repository` (later slices). Backend gates green (ruff/mypy clean, 35 files; pytest 84 passed;
coverage 99.45%); eval+contracts gates green (ruff/mypy --strict clean, 24 files; pytest 104 passed);
manual validation passed; awaiting human review before merge. Next: Scan Pipeline Slice 3 (execution +
aggregation → `scan_repository`, `ScanResult`). Prior: Slice 1 — language foundation, under new
`backend/app/services/scan/`:
`LanguageGroup` (PYTHON/WEB), `TargetMode` (AUTO/MANUAL), `ScanConfig` (AUTO→no groups, MANUAL→≥1
group; `auto()`/`manual()` constructors), and `detect_language_groups(repo_root)` (extension-based,
read-only, symlink-skipping; future-roadmap languages ignored). No analyzer selection/execution/
resolution/scanning (later slices). Backend gates green (ruff/mypy clean, 33 files; pytest 73 passed;
coverage 99.41%); eval+contracts gates still green; manual validation passed; awaiting human review
before merge. Next: Scan Pipeline Slice 2 (AUTO/MANUAL resolution + registry-driven analyzer
selection). Prior: Slice 0 — shared `contracts` package (M3 relocation). Moved `Language`,
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
