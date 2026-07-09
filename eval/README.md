# Evaluation Harness

This is the home for the SAST evaluation harness — the measuring instrument the project
plan requires **before** the taint engine (PROJECT_PLAN §1, Gate G0.2). It exists so that
**TASK-020a** (corpus acquisition + labeling), then **TASK-020b/020c** (runner + metrics),
and **TASK-021** (callable per-candidate interface) have a designated location to start.

> The architecture (§4) does not define a folder for the harness. Per the approved
> Engineering Foundation Plan it lives here, at the repository root, so the corpus and the
> harness stay together and the harness remains importable/packageable for the later
> `eval_gate` (TASK-021 / Phase 4b).

## Layout

```
eval/
├── corpus/    # known-answer corpora (OWASP Benchmark, NIST Juliet, curated internal)
│              # DATA IS NOT COMMITTED — fetched by a script authored in TASK-020a.
├── labels/    # known vulnerable/safe labels per corpus (schema defined in TASK-020a)
└── harness/   # runner + precision/recall/F1 metrics (TASK-020b/020c) — Python package
```

## Scope now (engineering foundation)

Only the **structure** exists. No corpus data, no runner, and no metrics code have been
implemented — those are the TASK-020 series. The MVP target language is **Python**.

## Corpus data policy

Corpora are **fetched, never vendored** (size + licensing). `eval/corpus/` is git-ignored
except for its `.gitkeep`. The fetch script and license verification are part of TASK-020a.
