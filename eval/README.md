# Evaluation Harness

The SAST evaluation harness — the measuring instrument the project plan requires **before**
the taint engine (PROJECT_PLAN §1, Gate G0.2). Every analyzer is judged here: it turns
ground-truth labels + a detector's findings into precision / recall / F1.

> The architecture (§4) does not define a folder for the harness. Per the approved Engineering
> Foundation Plan it lives at the repository root, so the corpora and the harness stay together
> and the harness remains importable/packageable for the later `eval_gate` (Phase 4b).

## Status

Complete for the MVP: **TASK-020a** (corpora + labels + integrity validator), **TASK-020b**
(matching + single-corpus orchestration), **TASK-020c** (metrics), and **TASK-021** (the callable
`evaluate_corpus` interface). The harness is **language-agnostic** and depends only on the
`Detector` protocol (`scan(corpus_root) -> list[Finding]`) — the concrete deterministic analyzers
live in the backend (`app.services.deterministic`).

## Layout

```
eval/
├── corpus/
│   ├── committed/    # small, permissively-licensed corpora — TRACKED in git
│   └── downloaded/   # cache for large/licensed corpora — GIT-IGNORED (fetched, never vendored)
├── labels/           # known vulnerable/safe labels per corpus (one LabelSet per file)
├── corpus_registry.json   # descriptors: id -> kind, language, local_path, labels_path
└── harness/          # loader, validator, runner (matching), evaluation, metrics, interface
```

## Corpora (committed)

MVP corpora are **curated and committed in-repo** (Python + Web):

- `project_curated` — 20 broad Python cases across 5 CWE categories (2 vuln + 2 safe each).
- `web_curated_{js,ts,html}` — the Web capability's cases (XSS, eval, secret, tabnabbing).
- Per-analyzer micro-corpora (2 vuln + 2 safe), one CWE each, for the deterministic suite:
  `code_exec_py`, `weak_crypto_{py,js}`, `unsafe_deserialization_{py,js}`,
  `tls_verification_{py,js}`, `reverse_tabnabbing_{html,js}`.

`owasp_benchmark` (Java) and `nist_juliet` (C/C++) are **descriptor-only, v2.0** roadmap entries —
they, and the external corpus fetcher they need, are not part of the MVP.

## Corpus data policy

`committed/` corpora and all `labels/**` are tracked. `corpus/downloaded/*` is git-ignored
(kept only by its `.gitkeep`): large/licensed corpora are **fetched, never vendored**. Corpus
files are treated as inert text — the harness and analyzers **read them, never import or execute
them**.

## Using it

```python
from eval.harness.interface import evaluate_corpus
from eval.harness.loader import load_corpus_registry

registry = load_corpus_registry(Path("eval/corpus_registry.json"))
result = evaluate_corpus(
    detector,                 # anything satisfying the Detector protocol
    "weak_crypto_py",
    registry=registry,
    labels_dir=Path("eval/labels"),
    corpus_base_dir=Path("eval/corpus/committed"),
)
# result.status, result.metrics (precision/recall/f1), result.integrity
```

Integrity failure (labels not matching the corpus tree) is an **expected, structured outcome**
(`status = integrity_failed`, `metrics = None`), not an exception; operational faults (unknown
corpus id, unreadable/invalid labels) raise `eval.harness.errors` types.
