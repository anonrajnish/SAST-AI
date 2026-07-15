# SAST Scanner -- Architecture & Folder Structure (v2.3)

**Version:** 2.3.0  
**Date:** 2026-07-09  
**Status:** Updated Architecture -- Agentic AI + Deterministic Detection + GitNexus + Cost Tracking + Learnable Agent Skills

> **Amendment (2026-07-15) -- multi-language scope reconciliation:** This platform is a
> **modular, multi-language** SAST engine. **MVP languages:** Python, JavaScript, TypeScript,
> HTML (already reflected in §1, §4, §5.7, §9). **Future roadmap:** Java, C/C++, Go, .NET, and
> additional languages -- each gaining deterministic analysis, language-specific rulepacks, an
> evaluation corpus, AI-assisted triage, and AI-assisted remediation as it lands. The
> **evaluation harness is language-agnostic**; **OWASP Benchmark (Java)** and **NIST Juliet
> (C/C++)** are planned corpora for those future languages, not the MVP. See §12. No
> implementation or schema was changed by this amendment.

> **v2.1 changes (baked in, no manual edits needed):**
> - Replaced **Graphify** with **GitNexus** (github.com/abhigyanpatwari/GitNexus) as the offline code-intelligence engine.
> - GitNexus supplies structure + framework modeling (`routes` = taint sources, `orm` = sinks) + an **experimental intra-procedural PDG** (`gitnexus analyze --pdg`).
> - You still build ONE thing on top: an **interprocedural taint engine** (stitches GitNexus's per-function PDG across its call graph). GitNexus's PDG is intra-procedural and does not cross procedure/repo boundaries.
> - **Joern + Neo4j dropped** in the default (Path A) design; graph lives in GitNexus's embedded **LadybugDB**. See §3 for the optional Path B that keeps Joern.
> - Graph build is now **offline & keyless** (no `GRAPHIFY_BACKEND=openai`); LLM key only for optional GitNexus wiki/chat.
> - **License note:** GitNexus is **PolyForm Noncommercial 1.0.0** -- free for non-commercial use; commercial use requires licensing via akonlabs.com. Resolve before any commercial launch.
>
> **v2.2 changes (this revision):**
> - **Model selection flow:** after a successful `Test connection`, the provider's real model list populates a dropdown; Save is blocked until a model is chosen (see §5.8).
> - **Backend key custody hardened:** ciphertext moves to the DB (`api_key_meta.encrypted_key`); the KEK is injected at runtime from a separate secret, never co-located with ciphertext in `.env` (see §5.8 + §7).
> - **Cost & usage tracking:** token + $ cost captured **per scan, per agent, and per model**, rolled up to a portal-wide dashboard (see §5.9, §9, §13).
> - **Pricing catalog:** per-model price table **seeded from YAML, overridable in the portal UI** (see §13).
>
> **v2.3 changes (this revision):**
> - **Terminology split:** the old `sast-skills/` (deterministic YAML) is renamed **`rulepacks/`**; a new **`agent-skills/`** holds the LLM agents' reasoning knowledge. Two different artifacts, two lifecycles.
> - **Learnable agent skills (§5.10):** a **`common`** skill for all stacks + **tech-specific** skills (e.g. Python secure code review), composed per scan by detected stack.
> - **Gated learning loop:** analyst feedback becomes a *candidate*, is validated against the **eval harness** (precision/recall must not regress), then **human-approved** and promoted as a **versioned** skill. Agents never write their own skills. This is also the defense against skill-poisoning (a variant of the prompt-injection risk).

---

## Table of Contents

1. [Overview](#1-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Folder Structure](#4-folder-structure)
5. [Core Components](#5-core-components)
   - 5.1 [Input Channels](#51-input-channels)
   - 5.2 [Scan Orchestrator](#52-scan-orchestrator)
   - 5.3 [Code Intelligence Layer](#53-code-intelligence-layer)
   - 5.4 [Deterministic Detection Layer](#54-deterministic-detection-layer)
   - 5.5 [AI Agent Layer](#55-ai-agent-layer)
   - 5.6 [Project & Folder Management](#56-project--folder-management)
   - 5.7 [Tech Stack Auto-Detection](#57-tech-stack-auto-detection)
   - 5.8 [Provider & Model Configuration](#58-provider--model-configuration)
   - 5.9 [Cost & Usage Tracking](#59-cost--usage-tracking)
   - 5.10 [Agent Skills & Gated Learning](#510-agent-skills--gated-learning)
6. [Data Flow: Complete Scan Lifecycle](#6-data-flow-complete-scan-lifecycle)
7. [Security Design](#7-security-design)
8. [Frontend Pages & Components](#8-frontend-pages--components)
9. [Database Schema](#9-database-schema)
10. [Environment Configuration](#10-environment-configuration)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Future Enhancements](#12-future-enhancements)
13. [Pricing Catalog & Cost Model](#13-pricing-catalog--cost-model)

---

## 1. Overview

An agentic AI-powered Static Application Security Testing (SAST) platform for Python and JavaScript/TypeScript/HTML codebases. The platform combines **deterministic detection** (taint analysis, rulepacks, pattern matching) with **AI agent reasoning** to deliver high-confidence vulnerability findings.

### Key Differentiators

| Feature | Description |
|---------|-------------|
| **Hybrid Detection** | Deterministic engine emits candidates with traces; AI agents triage, hunt, and fix |
| **GitNexus code intelligence** | Offline structure + `routes`/`orm` framework modeling + experimental PDG, queried via MCP |
| **Interprocedural taint** | Custom engine stitches GitNexus intra-procedural PDG across the call graph (the core deliverable) |
| **Agentic AI** | Triage agent, Hunter agent, Fix agent -- each with specialized roles |
| **Multi-Channel Input** | Web upload, Git + CI/CD, REST API |
| **MCP Integration** | AI agents query GitNexus (17 MCP tools) + your taint traces via Model Context Protocol |
| **Per-Scan Isolation** | Sandboxed workers, isolated environments |

### Supported Languages (v1)
- Python 2, Python 3
- JavaScript, TypeScript
- HTML

> **Language roadmap:** the detection stack (rulepacks, taint models, agent skills) is
> organized per language so new languages plug in without re-architecting. **Java, C/C++,
> Go, and .NET** are planned future additions beyond v1 (see §12).

### No login/auth in v1 -- can be added later.

---

## 2. High-Level Architecture

```
+-----------------------------------------------------------------------------+
|                           INPUT CHANNELS                                     |
|  +--------------+  +------------------+  +------------------+              |
|  |  Web upload  |  |   Git + CI/CD    |  |    REST API      |              |
|  |  (ZIP/Drag)  |  |  (GitHub/GitLab) |  |  (Programmatic)  |              |
|  +--------------+  +------------------+  +------------------+              |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                        SCAN ORCHESTRATOR                                     |
|  queue | sandboxed workers | per-scan isolation | resource limits          |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                CODE INTELLIGENCE LAYER (GitNexus, offline)                   |
|  gitnexus analyze --pdg  ->  .gitnexus/ (LadybugDB)                          |
|  +------------------+  +------------------+  +-------------------------+   |
|  | Structure+calls  |  | routes -> SOURCES|  | PDG (experimental)      |   |
|  | imports, heritage|  | orm    -> SINKS  |  | intra-proc reaching-def |   |
|  | processes        |  | (framework model)|  | + control dependence    |   |
|  +------------------+  +------------------+  +-------------------------+   |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                    DETERMINISTIC DETECTION LAYER                             |
|  emits candidates with traces                                                |
|  +------------------+  +------------------+  +-------------------------+   |
|  | Interproc taint  |  |    Rulepacks     |  |   Pattern + SCA         |   |
|  | stitches PDG over|  |  augment routes/ |  |   secrets, deps (OSV)   |   |
|  | GitNexus calls   |  |  orm; sanitizers |  |                         |   |
|  +------------------+  +------------------+  +-------------------------+   |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                         AI AGENT LAYER                                       |
|  queries GitNexus (MCP: impact, context, trace, pdg_query) + taint traces    |
|  +------------------+  +------------------+  +-------------------------+   |
|  |  Triage agent    |  |   Hunter agent   |  |   Fix + report agent    |   |
|  | kills false      |  |  logic + authz   |  |   patch diffs,          |   |
|  | positives        |  |  flaws           |  |   severity scoring      |   |
|  +------------------+  +------------------+  +-------------------------+   |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
|                      RESULTS AND DELIVERY                                    |
|  +------------------+  +------------------+  +-------------------------+   |
|  |  Findings store  |  |    Dashboard     |  |   CI gates + reports    |   |
|  | SARIF, history,  |  |  trace viewer,   |  |   PR comments,          |   |
|  | diffs            |  |  filters         |  |   compliance            |   |
|  +------------------+  +------------------+  +-------------------------+   |
+-----------------------------------------------------------------------------+
```

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Tailwind CSS | UI |
| **Frontend Build** | Vite | Bundling & dev server |
| **Backend API** | FastAPI (Python 3.12) | REST API |
| **Async Tasks** | Celery + Redis | Background scan jobs |
| **Database** | PostgreSQL 16 | Persistent data |
| **Code Intelligence** | **GitNexus** (Tree-sitter + LadybugDB, offline) | Structure, `routes`/`orm` framework modeling, processes, PDG; 17 MCP tools |
| **Graph DB** | **LadybugDB** (bundled with GitNexus, in `.gitnexus/`) | Graph + full-text + embeddings storage & Cypher |
| **PDG / reaching-def** | **GitNexus `--pdg`** (experimental) | Intra-procedural data/control dependence |
| **Interprocedural Taint** | **Custom engine over GitNexus graph** | Source->sink across the call graph (core deliverable) |
| **Object Storage** | MinIO (S3-compatible) | ZIP file storage |
| **Reverse Proxy** | Nginx | Routing, SSL, rate limiting |
| **Container** | Docker + Docker Compose | Deployment |
| **Encryption** | Python `cryptography` (AES-256-GCM) | API key encryption |
| **MCP** | Model Context Protocol | AI agents query GitNexus + custom taint MCP tool |

> **Path A (default, recommended for v1):** GitNexus-only. Build the interprocedural
> taint layer directly on GitNexus's graph (Cypher / `pdg_query` / MCP). **Joern and
> Neo4j are dropped** -- fewer moving parts, fully offline, one embedded graph store.
>
> **Path B (fallback):** Keep **Joern + Neo4j** only if you need mature interprocedural
> taint on day one and a pilot shows GitNexus's experimental PDG is insufficient for your
> target languages. Then GitNexus = structure/framework/agent-assist, Joern = taint.
> This document uses **Path A** throughout; Path B deltas are called out where relevant.

---

## 4. Folder Structure

```
sast-scanner/
|
|-- .github/
|   |-- workflows/
|   |   |-- ci.yml
|   |   |-- security-scan.yml
|
|-- docker/
|   |-- docker-compose.yml
|   |-- docker-compose.dev.yml
|   |-- Dockerfile.backend
|   |-- Dockerfile.frontend
|   |-- Dockerfile.worker
|   |-- Dockerfile.gitnexus
|   |-- nginx/
|   |   |-- nginx.conf
|
|-- backend/
|   |
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- dependencies.py
|   |   |-- constants.py
|   |
|   |-- api/
|   |   |-- __init__.py
|   |   |-- router.py
|   |   |
|   |   |-- v1/
|   |   |   |-- __init__.py
|   |   |   |-- projects.py
|   |   |   |-- folders.py
|   |   |   |-- scans.py
|   |   |   |-- uploads.py
|   |   |   |-- settings.py
|   |   |   |-- skills.py
|   |   |   |-- health.py
|   |   |
|   |   |-- deps/
|   |   |   |-- db.py
|   |   |   |-- rate_limit.py
|   |
|   |-- core/
|   |   |-- __init__.py
|   |   |-- security.py
|   |   |-- env_manager.py
|   |   |-- encryption.py
|   |   |-- exceptions.py
|   |   |-- sandbox.py
|   |
|   |-- models/
|   |   |-- __init__.py
|   |   |-- base.py
|   |   |-- project.py
|   |   |-- folder.py
|   |   |-- scan.py
|   |   |-- finding.py
|   |   |-- api_key_meta.py
|   |   |-- llm_usage.py
|   |   |-- model_price.py
|   |   |-- skill.py
|   |   |-- user.py
|   |
|   |-- schemas/
|   |   |-- __init__.py
|   |   |-- project.py
|   |   |-- folder.py
|   |   |-- scan.py
|   |   |-- upload.py
|   |   |-- settings.py
|   |   |-- skill.py
|   |   |-- agent.py
|   |
|   |-- services/
|   |   |-- __init__.py
|   |   |
|   |   |-- project/
|   |   |   |-- __init__.py
|   |   |   |-- project_service.py
|   |   |   |-- folder_service.py
|   |   |
|   |   |-- scan/
|   |   |   |-- __init__.py
|   |   |   |-- scan_orchestrator.py
|   |   |   |-- zip_processor.py
|   |   |   |-- git_processor.py
|   |   |   |-- tech_detector.py
|   |   |   |-- file_mapper.py
|   |   |   |-- result_parser.py
|   |   |
|   |   |-- code_intelligence/
|   |   |   |-- __init__.py
|   |   |   |-- gitnexus_runner.py           # orchestrates `gitnexus analyze --pdg` per scan
|   |   |   |-- index_manager.py             # .gitnexus/ lifecycle, registry, staleness vs HEAD
|   |   |   |-- graph_facade.py              # unified read API over LadybugDB (structure+routes+orm+PDG)
|   |   |   |-- json_exporter.py             # LLM-context snapshot
|   |   |   |   # NOTE (Path B only): re-add tree_sitter_parsers/, cpg_builder.py,
|   |   |   |   # dataflow_graph.py, neo4j_exporter.py if keeping Joern+Neo4j.
|   |   |
|   |   |-- deterministic/
|   |   |   |-- __init__.py
|   |   |   |-- taint_engine.py
|   |   |   |-- rulepack_engine.py
|   |   |   |-- pattern_matcher.py
|   |   |   |-- sca_scanner.py
|   |   |   |-- secret_scanner.py
|   |   |   |-- candidate_emitter.py
|   |   |   |-- rulepacks/
|   |   |   |   |-- python/
|   |   |   |   |   |-- sources.yml
|   |   |   |   |   |-- sinks.yml
|   |   |   |   |   |-- sanitizers.yml
|   |   |   |   |-- javascript/
|   |   |   |   |   |-- sources.yml
|   |   |   |   |   |-- sinks.yml
|   |   |   |   |   |-- sanitizers.yml
|   |   |   |   |-- typescript/
|   |   |   |   |   |-- sources.yml
|   |   |   |   |   |-- sinks.yml
|   |   |   |   |   |-- sanitizers.yml
|   |   |   |   |-- html/
|   |   |   |   |   |-- sources.yml
|   |   |   |   |   |-- sinks.yml
|   |   |   |   |   |-- sanitizers.yml
|   |   |
|   |   |-- agents/
|   |   |   |-- __init__.py
|   |   |   |-- agent_orchestrator.py
|   |   |   |-- mcp_client.py
|   |   |   |-- triage_agent.py
|   |   |   |-- hunter_agent.py
|   |   |   |-- fix_agent.py
|   |   |   |-- prompts/
|   |   |   |   |-- triage_system.txt
|   |   |   |   |-- triage_user.txt
|   |   |   |   |-- hunter_system.txt
|   |   |   |   |-- hunter_user.txt
|   |   |   |   |-- fix_system.txt
|   |   |   |   |-- fix_user.txt
|   |   |
|   |   |-- cost/
|   |   |   |-- __init__.py
|   |   |   |-- usage_meter.py            # records tokens + cost per agent call
|   |   |   |-- price_catalog.py          # loads model_prices (YAML seed + UI override)
|   |   |   |-- rollup.py                 # refreshes usage_rollup materialized view
|   |   |
|   |   |-- code_graph/                      # was: graphify/
|   |   |   |-- __init__.py
|   |   |   |-- gitnexus_client.py           # subprocess: `gitnexus analyze --pdg`, staleness checks
|   |   |   |-- gitnexus_mcp_client.py       # MCP/HTTP client: query, context, impact, trace, pdg_query
|   |   |   |-- cypher_queries.py            # LadybugDB Cypher for sources/sinks/paths
|   |   |   |-- source_sink_model.py         # maps routes->sources, orm->sinks, merges rulepacks
|   |   |   |-- structure_context.py         # compact structure context for agents
|   |   |   |-- report_reader.py
|   |   |   |-- taint/
|   |   |   |   |-- interproc_engine.py      # stitches intra-proc PDG across call graph
|   |   |   |   |-- sanitizers.py            # sanitizer semantics (context-sensitive)
|   |   |   |   |-- trace_builder.py         # emits TaintTrace(source, sink, path, sanitizers)
|   |   |   |-- exporters/
|   |   |   |   |-- llm_context_exporter.py
|   |   |
|   |   |-- llm/
|   |   |   |-- __init__.py
|   |   |   |-- llm_router.py
|   |   |   |-- providers/
|   |   |   |   |-- base.py
|   |   |   |   |-- anthropic.py
|   |   |   |   |-- openai.py
|   |   |   |   |-- gemini.py
|   |   |   |   |-- azure_openai.py
|   |   |   |   |-- ollama.py
|   |   |   |-- prompt_engine.py
|   |   |   |-- token_manager.py
|   |   |
|   |   |-- agent_skills/                    # LLM agent reasoning knowledge (NOT rulepacks)
|   |   |   |-- __init__.py
|   |   |   |-- skill_loader.py              # reads agent-skills/ from disk
|   |   |   |-- skill_composer.py            # common + <detected-stack> (+ framework) -> agent context
|   |   |   |-- skill_registry.py            # active version per stack (registry.yaml <-> DB)
|   |   |   |-- learning/
|   |   |   |   |-- candidate_recorder.py    # analyst feedback -> skill_learning_candidates
|   |   |   |   |-- eval_gate.py             # runs candidate through eval harness (precision/recall)
|   |   |   |   |-- promoter.py              # human-approved candidate -> new versioned SKILL.md
|   |   |
|   |   |-- settings/
|   |   |   |-- __init__.py
|   |   |   |-- api_key_service.py
|   |
|   |-- tasks/
|   |   |-- __init__.py
|   |   |-- scan_tasks.py
|   |
|   |-- db/
|   |   |-- __init__.py
|   |   |-- session.py
|   |   |-- migrations/
|   |   |   |-- versions/
|   |
|   |-- templates/
|   |   |-- prompts/
|   |   |   |-- system/
|   |   |   |   |-- sast_analyst.txt
|   |   |   |   |-- graph_analyst.txt
|   |   |   |-- user/
|   |   |   |   |-- code_review.txt
|   |   |   |   |-- vulnerability_detect.txt
|   |   |   |   |-- source_sink_trace.txt
|   |
|   |-- tests/
|   |   |-- __init__.py
|   |   |-- conftest.py
|   |   |-- test_projects.py
|   |   |-- test_scans.py
|   |   |-- test_tech_detector.py
|   |   |-- test_gitnexus_integration.py
|   |   |-- test_interproc_taint.py
|   |   |-- test_llm_providers.py
|   |   |-- test_env_manager.py
|   |   |-- test_agents.py
|   |   |-- test_taint_engine.py
|   |
|   |-- alembic.ini
|   |-- requirements.txt
|   |-- pytest.ini
|
|-- frontend/
|   |
|   |-- public/
|   |   |-- index.html
|   |
|   |-- src/
|   |   |-- index.tsx
|   |   |-- App.tsx
|   |   |
|   |   |-- components/
|   |   |   |-- common/
|   |   |   |   |-- Button.tsx
|   |   |   |   |-- Card.tsx
|   |   |   |   |-- Modal.tsx
|   |   |   |   |-- Toast.tsx
|   |   |   |   |-- LoadingSpinner.tsx
|   |   |   |
|   |   |   |-- layout/
|   |   |   |   |-- Navbar.tsx
|   |   |   |   |-- Sidebar.tsx
|   |   |   |   |-- Layout.tsx
|   |   |   |
|   |   |   |-- project/
|   |   |   |   |-- ProjectCard.tsx
|   |   |   |   |-- ProjectForm.tsx
|   |   |   |   |-- ProjectList.tsx
|   |   |   |   |-- ProjectTagBadge.tsx
|   |   |   |
|   |   |   |-- folder/
|   |   |   |   |-- FolderCard.tsx
|   |   |   |   |-- FolderForm.tsx
|   |   |   |   |-- FolderTree.tsx
|   |   |   |   |-- TechStackSelector.tsx
|   |   |   |
|   |   |   |-- scan/
|   |   |   |   |-- ScanTrigger.tsx
|   |   |   |   |-- UploadZone.tsx
|   |   |   |   |-- ScanProgress.tsx
|   |   |   |   |-- ScanResults.tsx
|   |   |   |   |-- FindingCard.tsx
|   |   |   |   |-- CodeViewer.tsx
|   |   |   |   |-- GraphVisualizer.tsx
|   |   |   |   |-- TraceViewer.tsx
|   |   |   |   |-- AgentPanel.tsx
|   |   |   |
|   |   |   |-- settings/
|   |   |   |   |-- SettingsLayout.tsx
|   |   |   |   |-- ModelConfigCard.tsx
|   |   |   |   |-- ApiKeyInput.tsx
|   |   |   |   |-- RulepackEditor.tsx            # was: SkillEditor.tsx
|   |   |   |-- AgentSkillViewer.tsx
|   |   |   |-- LearningQueue.tsx
|   |   |   |   |-- AgentConfigCard.tsx
|   |   |
|   |   |-- pages/
|   |   |   |-- HomePage.tsx
|   |   |   |-- ProjectsPage.tsx
|   |   |   |-- ProjectDetailPage.tsx
|   |   |   |-- ScanPage.tsx
|   |   |   |-- ScanResultsPage.tsx
|   |   |   |-- SettingsPage.tsx
|   |   |   |-- SkillsPage.tsx
|   |   |   |-- AgentsPage.tsx
|   |   |   |-- UsagePage.tsx
|   |   |   |-- PricingPage.tsx
|   |   |
|   |   |-- hooks/
|   |   |   |-- useProjects.ts
|   |   |   |-- useFolders.ts
|   |   |   |-- useScans.ts
|   |   |   |-- useUpload.ts
|   |   |   |-- useSettings.ts
|   |   |   |-- useRulepacks.ts
|   |   |   |-- useAgentSkills.ts
|   |   |   |-- useAgents.ts
|   |   |   |-- useUsage.ts
|   |   |   |-- usePricing.ts
|   |   |
|   |   |-- services/
|   |   |   |-- api.ts
|   |   |   |-- projectApi.ts
|   |   |   |-- scanApi.ts
|   |   |   |-- uploadApi.ts
|   |   |   |-- settingsApi.ts
|   |   |   |-- agentApi.ts
|   |   |   |-- usageApi.ts
|   |   |   |-- pricingApi.ts
|   |   |
|   |   |-- types/
|   |   |   |-- project.ts
|   |   |   |-- folder.ts
|   |   |   |-- scan.ts
|   |   |   |-- settings.ts
|   |   |   |-- agent.ts
|   |   |
|   |   |-- utils/
|   |   |   |-- constants.ts
|   |   |   |-- validators.ts
|   |   |
|   |   |-- styles/
|   |   |   |-- tailwind.css
|   |
|   |-- package.json
|   |-- tailwind.config.js
|   |-- tsconfig.json
|   |-- vite.config.ts
|
|-- rulepacks/                               # was: sast-skills/ (deterministic YAML for the taint engine)
|   |
|   |-- builtin/
|   |   |-- python/
|   |   |   |-- sql_injection.yml
|   |   |   |-- xss.yml
|   |   |   |-- command_injection.yml
|   |   |   |-- path_traversal.yml
|   |   |   |-- ssrf.yml
|   |   |   |-- deserialization.yml
|   |   |   |-- hardcoded_secrets.yml
|   |   |
|   |   |-- javascript/
|   |   |   |-- xss.yml
|   |   |   |-- prototype_pollution.yml
|   |   |   |-- dom_based_xss.yml
|   |   |   |-- npm_audit.yml
|   |   |   |-- eval_danger.yml
|   |   |
|   |   |-- typescript/
|   |   |   |-- type_confusion.yml
|   |   |
|   |   |-- html/
|   |   |   |-- inline_event_handlers.yml
|   |   |   |-- unsafe_iframes.yml
|   |   |
|   |   |-- generic/
|   |   |   |-- hardcoded_credentials.yml
|   |   |   |-- insecure_crypto.yml
|   |   |   |-- insecure_http.yml
|   |
|   |-- custom/
|   |   |-- .gitkeep
|
|-- agent-skills/                            # LLM agent reasoning knowledge (composed per scan; git-versioned)
|   |-- common/
|   |   |-- SKILL.md                         # secure-review principles for ALL stacks
|   |   |-- examples/                        # tech-agnostic FP/TP few-shot cases
|   |   |-- version.yaml
|   |-- python/
|   |   |-- SKILL.md                         # Python secure code review
|   |   |-- frameworks/
|   |   |   |-- django.md
|   |   |   |-- flask.md
|   |   |   |-- fastapi.md
|   |   |-- examples/
|   |   |-- version.yaml
|   |-- javascript/
|   |   |-- SKILL.md
|   |   |-- version.yaml
|   |-- typescript/
|   |   |-- SKILL.md
|   |   |-- version.yaml
|   |-- _learning/
|   |   |-- candidates/                      # pending learnings awaiting eval + human approval
|   |   |-- rejected/                        # audit trail of declined candidates
|   |-- registry.yaml                        # active skill version per stack
|
|-- infra/
|   |-- k8s/
|   |   |-- namespace.yml
|   |   |-- backend-deployment.yml
|   |   |-- frontend-deployment.yml
|   |   |-- worker-deployment.yml
|   |   |-- gitnexus-deployment.yml
|   |   |-- postgres-deployment.yml
|   |   |-- redis-deployment.yml
|   |   |-- minio-deployment.yml
|   |   |-- ingress.yml
|   |
|   |-- secrets/
|   |   |-- encryption-key-secret.yml
|
|-- scripts/
|   |-- setup.sh
|   |-- seed.sh
|   |-- seed-prices.sh                     # loads config/model_prices.yml into model_prices
|   |-- eval-skill-candidate.sh            # runs a learning candidate through the eval harness
|   |-- migrate.sh
|   |-- install-gitnexus.sh
|
|-- docs/
|   |-- ARCHITECTURE.md
|   |-- API.md
|   |-- RULEPACKS.md                        # was: SAST_SKILLS.md
|   |-- AGENT_SKILLS.md                     # agent-skills format + gated learning loop
|   |-- GITNEXUS_INTEGRATION.md
|   |-- AGENT_DESIGN.md
|   |-- DEPLOYMENT.md
|
|-- .env
|-- .env.example
|-- .gitignore
|-- Makefile
|-- README.md
|-- LICENSE
```

---

## 5. Core Components

### 5.1 Input Channels

Three ways to feed code into the platform:

| Channel | Method | Use Case |
|---------|--------|----------|
| **Web Upload** | ZIP file, drag & drop, folder picker | Manual scans, ad-hoc testing |
| **Git + CI/CD** | Webhook from GitHub/GitLab, branch/PR trigger | Automated pipeline integration |
| **REST API** | Programmatic POST with ZIP or git URL | Third-party tools, automation |

**API Endpoints:**
```
POST /api/v1/folders/{id}/upload              # Web upload (multipart ZIP)
POST /api/v1/folders/{id}/git                 # Git clone + scan
POST /api/v1/scans/trigger                    # REST API trigger
POST /api/v1/webhooks/github                  # GitHub webhook
POST /api/v1/webhooks/gitlab                  # GitLab webhook
```

---

### 5.2 Scan Orchestrator

Manages scan lifecycle with isolation and resource control.

**Responsibilities:**
- Job queue management (Celery + Redis)
- Sandboxed worker execution
- Per-scan isolation (separate temp directories, network namespaces)
- Resource limits (CPU, memory, disk, time)
- Retry logic for failed scans
- Concurrent scan throttling

**Sandbox Configuration:**
```python
class ScanSandbox:
    # Per-scan isolated environment

    def __init__(self, scan_id: str):
        self.scan_id = scan_id
        self.work_dir = f"/tmp/scans/{scan_id}"
        self.max_memory_mb = 4096
        self.max_cpu_cores = 2
        self.max_disk_mb = 1024
        self.timeout_seconds = 600

    def enter(self):
        # Create isolated namespace
        # Mount tmpfs for work directory
        # Set cgroup limits
        # Drop capabilities
        pass

    def exit(self):
        # Clean up temp files
        # Preserve .gitnexus/ index and findings
        pass
```

---

### 5.3 Code Intelligence Layer (GitNexus)

Runs **GitNexus** per scan to build an offline code-intelligence graph. GitNexus is
zero-server (Tree-sitter + embedded LadybugDB); indexing makes **no network calls** and
needs **no API key**. Output lives in `.gitnexus/` and is queried via 17 MCP tools or Cypher.

**What GitNexus produces (14-phase pipeline):**

| Phase group | Produces | Used for |
|-------------|----------|----------|
| `scan`, `structure`, `parse` | files, symbols (fn/class/method), heritage | navigation, structure context |
| `routes` | framework **entry points** | seed **taint SOURCES** |
| `orm` | database/query call sites | seed **taint SINKS** |
| `tools` | tool/handler registrations | agent context |
| `crossFile`, `scopeResolution`, `mro` | resolved calls, field/return types, method-resolution order | interprocedural call graph |
| `communities`, `processes` | clusters + execution flows from entry points | reachability, Hunter agent |
| `--pdg` (experimental, opt-in) | intra-procedural **REACHING_DEF** + **CDG** | dataflow within a function |

**Construction Pipeline:**
```
Source Files
    |
    v
gitnexus analyze --pdg          (worker subprocess; offline, deterministic)
    |  writes .gitnexus/ (LadybugDB): graph + full-text + embeddings
    |
    +--> structure/calls/heritage/imports        (production)
    +--> routes  -> candidate taint SOURCES       (production, framework-aware)
    +--> orm     -> candidate taint SINKS         (production, framework-aware)
    +--> processes (entry-point execution flows)  (production)
    +--> PDG: intra-procedural REACHING_DEF + CDG (experimental, --pdg)
    |
    v
graph_facade.py                 (unified read API over LadybugDB)
    - exposes structure, routes, orm, processes, PDG segments to the taint engine & agents
    - json_exporter -> compact LLM-context snapshot
```

**Important boundary:** GitNexus's PDG dataflow is **intra-procedural** and does not cross
procedure/repo boundaries; its call edges are **confidence-scored** (exploration-grade).
Therefore GitNexus is used for structure, framework modeling, and per-function dataflow --
but the **interprocedural** taint stitching that yields findings is done by §5.4.

*(Path B only: if keeping Joern+Neo4j, this layer instead builds a full CPG in Neo4j and
GitNexus is used purely for framework modeling + agent-assist.)*

**CPG Node Types:**
```
- FILE          : Source file
- NAMESPACE     : Module/package
- TYPE_DECL     : Class, interface, enum
- METHOD        : Function, method
- METHOD_PARAMETER : Function parameter
- LOCAL         : Local variable
- LITERAL       : String, number literals
- CALL          : Function call
- IDENTIFIER    : Variable reference
- CONTROL_STRUCTURE : if, for, while, etc.
- RETURN        : Return statement
```

**CPG Edge Types:**
```
- AST       : Parent-child in AST
- CFG       : Control flow successor
- DFG       : Data flow (def -> use)
- CALL      : Caller -> callee
- IMPORT    : File -> imported module
- INHERITS  : Class -> parent class
- CONTAINS  : Parent scope -> child node
- REF       : Reference to declaration
```

---

### 5.4 Deterministic Detection Layer

Emits vulnerability candidates with traces. Runs before AI agents.

**Components:**

| Component | Purpose | Output |
|-----------|---------|--------|
| **Interprocedural Taint Engine** | Stitches GitNexus intra-proc PDG across the call graph | Taint traces (source->sink) with path |
| **Rulepacks** | YAML sources/sinks/sanitizers that *augment* GitNexus `routes`/`orm` | Rule matches |
| **Pattern Matcher** | Regex/AST patterns for secrets, dangerous APIs | Pattern hits |
| **SCA Scanner** | Dependency vulnerability scanning (OSV) | CVE list |

**Interprocedural Taint Engine** (the core deliverable -- built on GitNexus):
```python
class InterprocTaintEngine:
    # Stitches GitNexus's intra-procedural PDG segments across its call graph
    # to produce sound source->sink traces. GitNexus alone only gives per-function
    # reaching-def; crossing function boundaries is what we own.

    def __init__(self, gitnexus):
        self.gn = gitnexus  # MCP/Cypher facade over .gitnexus/ (LadybugDB)

    def trace(self, sources, sinks) -> list[TaintTrace]:
        # sources: from GitNexus `routes` + rulepack sources
        # sinks:   from GitNexus `orm` + rulepack sinks
        traces = []
        for src in sources:
            # worklist over the call graph, carrying taint state
            for tainted in self._propagate(src):
                for sink in sinks:
                    if self._reaches(tainted, sink):
                        path = self._materialize_path(src, tainted, sink)
                        if not self._sanitized(path):
                            traces.append(TaintTrace(
                                source=src, sink=sink, path=path,
                                sanitizers_checked=True,
                                confidence="high"))
        return traces

    def _propagate(self, node):
        # WITHIN a function: use GitNexus PDG reaching-def (pdg_query mode:flows)
        # ACROSS functions: walk GitNexus CALLS edges, bind args<->params,
        #   carry field-sensitivity (obj.a vs obj.b), respect MRO/return types
        ...

    def _sanitized(self, path):
        # apply context-sensitive sanitizer semantics from rulepacks
        ...
```

*(Path B: replace the GitNexus facade with Joern queries; the interface stays the same.)*

**Rulepack Format:**
```yaml
# deterministic/rulepacks/python/sources.yml
sources:
  - id: flask_request_args
    name: "Flask request arguments"
    pattern: "request\.(args|form|json|files)\.get"
    languages: [python]
    severity: info

  - id: input_function
    name: "Python input()"
    pattern: "input\s*\("
    languages: [python]
    severity: info

# deterministic/rulepacks/python/sinks.yml
sinks:
  - id: sql_execute
    name: "SQL execute"
    pattern: "(cursor|db)\.execute"
    languages: [python]
    severity: critical
    cwe: CWE-89

  - id: os_system
    name: "OS command execution"
    pattern: "os\.system|subprocess\.(call|run|Popen)"
    languages: [python]
    severity: critical
    cwe: CWE-78

# deterministic/rulepacks/python/sanitizers.yml
sanitizers:
  - id: sqlalchemy_text
    name: "SQLAlchemy parameterized query"
    pattern: "sqlalchemy\.text|parameterized"
    languages: [python]
```

**Candidate Emitter:**
```python
class CandidateEmitter:
    # Aggregates all deterministic findings into candidates for AI agents

    def emit_candidates(self, scan_id: str) -> list[Candidate]:
        candidates = []

        # Taint traces
        candidates.extend(self.taint_engine.find_all_traces())

        # Rulepack matches
        candidates.extend(self.rulepack_engine.evaluate_all())

        # Pattern matches (secrets, dangerous patterns)
        candidates.extend(self.pattern_matcher.scan())

        # SCA findings (dependency CVEs)
        candidates.extend(self.sca_scanner.scan())

        # Deduplicate and rank
        return self._deduplicate(candidates)
```

---

### 5.5 AI Agent Layer

Three specialized agents that query the CPG via MCP (Model Context Protocol).

**Agent Orchestrator:**
```python
class AgentOrchestrator:
    # Coordinates agent execution pipeline

    async def process_candidates(self, candidates: list[Candidate]) -> list[Finding]:
        findings = []

        for candidate in candidates:
            # Step 1: Triage agent filters false positives
            triage_result = await self.triage_agent.evaluate(candidate)
            if triage_result.is_false_positive:
                continue

            # Step 2: Hunter agent deep-dives into logic/authz flaws
            hunt_result = await self.hunter_agent.investigate(candidate)

            # Step 3: Fix agent generates patch and severity
            fix_result = await self.fix_agent.remediate(hunt_result)

            findings.append(Finding(
                candidate=candidate,
                triage=triage_result,
                hunt=hunt_result,
                fix=fix_result
            ))

        return findings
```

**MCP Client (Agent <-> GitNexus):** wraps GitNexus's MCP tools (via `gitnexus mcp`
stdio, or `gitnexus serve` HTTP on port 4747). Agents also receive the taint traces
from §5.4 as structured input.
```python
class GitNexusMCPClient:
    # Thin wrapper over GitNexus's 17 MCP tools for agent use.

    def __init__(self, endpoint: str, repo: str):
        self.client = MCPClient(endpoint)   # gitnexus serve / mcp
        self.repo = repo                    # per-repo id (or "@<group>" for group tools)

    def query(self, cypher_or_nl: str) -> dict:
        return self.client.call("query", repo=self.repo, q=cypher_or_nl)

    def context(self, symbol: str) -> dict:            # 360-degree symbol view
        return self.client.call("context", repo=self.repo, symbol=symbol)

    def impact(self, symbol: str) -> dict:             # blast radius up/downstream
        return self.client.call("impact", repo=self.repo, symbol=symbol)

    def trace(self, frm: str, to: str) -> list:        # call/flow path between symbols
        return self.client.call("trace", repo=self.repo, source=frm, target=to)

    def pdg_query(self, symbol: str, mode: str) -> dict:  # mode: "flows" | "controls"
        # requires an index built with `gitnexus analyze --pdg`
        return self.client.call("pdg_query", repo=self.repo, symbol=symbol, mode=mode)

    def cypher(self, q: str) -> dict:                  # raw LadybugDB Cypher
        return self.client.call("cypher", repo=self.repo, query=q)
```

**Triage Agent:**
- **Role:** Filter false positives from deterministic candidates
- **Input:** Candidate (with trace, code snippet, rule match)
- **Output:** True positive / False positive + reasoning
- **GitNexus tools:** `pdg_query(mode:flows)` + `trace` to confirm the path is reachable from a real `routes` entry point; `impact` to check dead/unused code -> kill FPs
- **Prompt Strategy:** Few-shot examples of false positives vs real bugs

**Hunter Agent:**
- **Role:** Deep-dive into logic flaws, authorization bypasses, business logic bugs
- **Input:** Triaged candidate
- **Output:** Enriched finding with attack scenario, impact analysis
- **GitNexus tools:** `trace`/`context` across `processes` (execution flows) and `communities` to find authz/business-logic flaws taint rules cannot encode
- **Prompt Strategy:** Chain-of-thought reasoning about attack paths

**Fix Agent:**
- **Role:** Generate patches, assign severity, create remediation advice
- **Input:** Hunter agent result
- **Output:** Patch diff, severity score, remediation steps, CWE mapping
- **GitNexus tools:** `impact` (upstream) so a patch at the sink will not break callers; `query` for safe-handling patterns elsewhere in the repo
- **Prompt Strategy:** Code generation with context from safe patterns in the same repo

> **Guardrail:** Agents may raise/lower confidence using GitNexus's (confidence-scored)
> graph, but every emitted **finding** must carry a concrete deterministic path from the
> §5.4 taint engine -- never a bare LLM/confidence claim. Treat GitNexus "unreachable"
> verdicts as confidence-down, not hard-suppress (esp. dynamically-typed JS).

---

### 5.6 Project & Folder Management

**Project:** Top-level container with environment tag.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String | Project name |
| `tag` | Enum | `uat`, `dev`, `production` |
| `description` | String | Optional |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

**Folder:** Organizes code within a project.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `project_id` | FK | Parent project |
| `name` | String | Folder name |
| `type` | Enum | `frontend`, `backend`, `microservice`, `other` |
| `tech_stack` | Enum | `python3`, `python2`, `javascript`, `typescript`, `html`, `auto_detect` |
| `created_at` | DateTime | Auto |

**API Endpoints:**
```
POST   /api/v1/projects              # Create project
GET    /api/v1/projects              # List all projects
GET    /api/v1/projects/{id}         # Get project detail
PUT    /api/v1/projects/{id}         # Update project
DELETE /api/v1/projects/{id}         # Delete project

POST   /api/v1/projects/{id}/folders   # Create folder
GET    /api/v1/projects/{id}/folders   # List folders
GET    /api/v1/folders/{id}            # Get folder detail
PUT    /api/v1/folders/{id}            # Update folder
DELETE /api/v1/folders/{id}            # Delete folder
```

---

### 5.7 Tech Stack Auto-Detection

**Detection Logic (`tech_detector.py`):**

```python
TECH_INDICATORS = {
    "python3": {
        "extensions": [".py"],
        "files": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "poetry.lock"],
        "snippets": ["print(", "async def", "f"", "typing."],
        "avoid": ["print ", "xrange", "import urllib2", "raw_input"]
    },
    "python2": {
        "extensions": [".py"],
        "files": [],
        "snippets": ["print ", "xrange", "import urllib2", "raw_input", "unicode("],
        "avoid": ["print(", "async def"]
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".mjs"],
        "files": ["package.json", "package-lock.json", "yarn.lock", ".eslintrc"],
        "snippets": ["const ", "let ", "require(", "module.exports"],
        "avoid": [": string", ": number", "interface ", "enum "]
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "files": ["tsconfig.json", "tsconfig.build.json"],
        "snippets": [": string", ": number", "interface ", "enum ", "type "],
        "avoid": []
    },
    "html": {
        "extensions": [".html", ".htm", ".xhtml"],
        "files": [],
        "snippets": ["<!DOCTYPE", "<html", "<script", "<style"],
        "avoid": []
    }
}

# Scoring algorithm:
# - File extension match: +2 points per file
# - Config file presence: +5 points
# - Snippet match: +1 point per occurrence
# - Avoid match: -3 points per occurrence
# - Winner: highest score above threshold (5)
# - Tie or below threshold: return "mixed" -> prompt user
```

---

### 5.8 Provider & Model Configuration

Analysts configure which LLM powers the agents. Supported providers:
**Ollama (local)**, Anthropic, OpenAI, Google Gemini, Azure OpenAI, OpenRouter,
DeepSeek, GLM (Z.AI), Groq. Local (Ollama) is first-class -- for customers whose
source code cannot leave their network, it is the only acceptable option.

**Custody model (why it differs from a browser tool):** the agents run in a backend
Celery worker and are triggered by webhooks/CI where no browser exists. Keys therefore
live on the **backend**, encrypted; the frontend only ever sees a masked last-4 and a
status badge. Raw keys are never returned by any API.

**Configure -> Test -> Select -> Save flow:**
```
1. Analyst picks a provider and enters an API key (or base URL for Ollama).
2. PUT /settings/providers/{id}  -> backend encrypts + stores (no echo back).
3. Analyst clicks "Test connection":
   POST /settings/providers/{id}/test
     -> backend lists models (provider /models, or Ollama /api/tags)
     -> returns { ok, model_count, models[] }
4. On success ONLY: the model dropdown is populated with the REAL available
   models; a custom-ID field remains as fallback (OpenAI/OpenRouter return
   hundreds -- filter to chat/coder-capable families).
5. Analyst selects a model. "Save settings" stays DISABLED until:
       provider configured  AND  test passed  AND  model chosen.
6. PUT /settings/providers/{id}  { model }  -> persisted; scans now use it.
```

**Hardened key custody (supersedes the v2.0/.env approach):**
- Ciphertext (AES-256-GCM) is stored in **PostgreSQL** (`api_key_meta.encrypted_key`),
  NOT in `.env`.
- The 32-byte **KEK (key-encryption key)** is injected at runtime from a **separate
  secret source** (Docker secret / K8s Secret / KMS / Vault) -- never the same file
  as the ciphertext.
- Rationale: the threat is file/DB disclosure. If the ciphertext and the key that
  decrypts it live in one file, the encryption protects nothing. Separation means a
  leaked DB is useless without the KEK, and a leaked KEK is useless without the DB.
- The settings write endpoints require **auth + admin role**. The backend no longer
  rewrites `.env` at runtime.

**`.env` File Layout (secrets removed; KEK injected, not stored here):**
```bash
# === Core App ===
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@postgres:5432/sastdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-app-secret-key-here

# === KEK is injected at runtime from a secret store -- do NOT store it here. ===
# Provided via Docker/K8s secret mounted to KEK_FILE, or fetched from KMS/Vault.
KEK_FILE=/run/secrets/sast_kek            # 32 raw bytes; read-only mount, perms 400
# (Provider API keys are NOT in .env -- ciphertext lives in Postgres api_key_meta.)

# === Azure OpenAI (non-secret endpoint config only) ===
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01

# === GitNexus (code intelligence -- offline, deterministic) ===
GITNEXUS_MODE=serve                      # serve (shared HTTP) | mcp (stdio) | cli
GITNEXUS_HTTP_URL=http://gitnexus:4747   # when MODE=serve
GITNEXUS_ANALYZE_ARGS=--pdg              # enable PDG so pdg_query/explain work
GITNEXUS_REGISTRY=/root/.gitnexus/registry.json
GITNEXUS_MAX_WORKERS=8
# No LLM key needed for indexing; LLM only for optional `gitnexus wiki`/chat.
```

**Encryption Module (`encryption.py`):**
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import os

class AESEncryption:
    # AES-256-GCM encryption for API keys.

    PREFIX = "enc:aes256gcm$"

    def __init__(self, master_key: bytes):
        if len(master_key) != 32:
            raise ValueError("Master key must be exactly 32 bytes")
        self.aesgcm = AESGCM(master_key)

    @classmethod
    def from_secret(cls):
        # KEK is injected at runtime, never stored beside the ciphertext.
        # Source: mounted Docker/K8s secret file (KEK_FILE) or a KMS/Vault fetch.
        path = os.environ["KEK_FILE"]              # e.g. /run/secrets/sast_kek
        with open(path, "rb") as fh:
            return cls(fh.read().strip()[:32].ljust(32, b"\\0")[:32])

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        ct = ciphertext[:-16]
        tag = ciphertext[-16:]
        return (
            f"{self.PREFIX}"
            f"{base64.b64encode(nonce).decode()}$"
            f"{base64.b64encode(ct).decode()}$"
            f"{base64.b64encode(tag).decode()}"
        )

    def decrypt(self, encrypted: str) -> str:
        if not encrypted.startswith(self.PREFIX):
            return encrypted
        parts = encrypted[len(self.PREFIX):].split("$")
        nonce = base64.b64decode(parts[0])
        ct = base64.b64decode(parts[1])
        tag = base64.b64decode(parts[2])
        ciphertext = ct + tag
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode()
```

> **Note:** ciphertext is read from / written to `api_key_meta.encrypted_key` in
> PostgreSQL (see §9), and the `AESEncryption` instance is created via
> `AESEncryption.from_secret()` so the KEK is never persisted next to the ciphertext.

---

### 5.9 Cost & Usage Tracking

Every LLM call the agents make is metered and priced, so the portal can show
**cost per scan**, **cost per agent**, **cost per model**, and a **portal-wide total**.
Local (Ollama) calls are metered for tokens but priced at **$0**.

**How it works:**
```
Each agent LLM call
  -> response includes usage { input_tokens, output_tokens }   (all providers report this)
  -> UsageMeter records ONE row in llm_usage:
       scan_id, agent_type (triage|hunter|fix), provider, model,
       input_tokens, output_tokens, cost_usd, created_at
  -> cost_usd = (input_tokens/1e6)*price_in + (output_tokens/1e6)*price_out
       price_in / price_out come from the model_prices catalog (§13)
       Ollama / local -> price_in = price_out = 0
```

**Why compute cost ourselves (not trust a live API):** providers do not return a
per-call dollar amount. The only reliable inputs are the token counts in each
response's `usage` field plus a **maintained price table**. Prices change and vary by
model, so the catalog is editable (§13), never hardcoded in the meter.

**Roll-ups (all derived from `llm_usage` -- single source of truth):**

| View | Query grain | Portal surface |
|------|-------------|----------------|
| Per scan | `SUM(cost_usd) WHERE scan_id = ?` | shown on the scan results header |
| Per scan x agent | `GROUP BY scan_id, agent_type` | breakdown chart on scan page |
| Per model | `GROUP BY model` | portal Usage dashboard |
| Per agent (global) | `GROUP BY agent_type` | portal Usage dashboard |
| Portal total | `SUM(cost_usd)` over a date range | Usage dashboard headline metric |

**UsageMeter (`usage_meter.py`):**
```python
class UsageMeter:
    # Records token usage + computed cost for every agent LLM call.

    def __init__(self, db, price_catalog):
        self.db = db
        self.prices = price_catalog          # loaded from model_prices (YAML-seeded, UI-override)

    def record(self, *, scan_id, agent_type, provider, model, usage) -> None:
        p_in, p_out = self.prices.get(provider, model)   # $/1M tokens; (0,0) for local
        cost = (usage["input_tokens"]  / 1_000_000) * p_in \
             + (usage["output_tokens"] / 1_000_000) * p_out
        self.db.insert("llm_usage", dict(
            scan_id=scan_id, agent_type=agent_type, provider=provider, model=model,
            input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
            cost_usd=round(cost, 6),
        ))
```

Wrap the agent LLM client so `record()` is called automatically after each completion --
agents never compute cost themselves. A per-scan **budget cap** (optional) can abort a
scan if cumulative `cost_usd` exceeds a configured limit (see §13 plans).

---

### 5.10 Agent Skills & Gated Learning

**Two different "skills" -- do not confuse them:**

| Artifact | Folder | Consumer | Form | Lifecycle |
|----------|--------|----------|------|-----------|
| **Rulepacks** | `rulepacks/` (was `sast-skills/`) | deterministic taint engine | YAML sources/sinks/sanitizers | edited by rule authors |
| **Agent skills** | `agent-skills/` | LLM agents (triage/hunter/fix) | Markdown reasoning knowledge | **learned + versioned via a gated loop** |

Agent skills give the agents *review expertise* a source/sink rule cannot encode --
e.g. "`pickle.loads` on untrusted data is RCE", "Django `.raw()` bypasses the ORM",
"MarkupSafe autoescaping downgrades reflected-XSS confidence".

**Composition (per scan, by detected stack):**
```
detected stack = Python (+ Django)
   agent context = common/SKILL.md            (base: applies to every stack)
                 + python/SKILL.md             (tech: extends/overrides base)
                 + python/frameworks/django.md (framework: if detected)
   -> injected into each agent's system context (as DATA, not instructions -- see below)
```
`common` is the floor every scan gets; tech and framework skills layer on top. The
active version of each is pinned in `agent-skills/registry.yaml` (mirrored in the
`agent_skills` DB table).

**Skill file shape (`python/SKILL.md`, illustrative):**
```markdown
# Python Secure Code Review -- SKILL.md  (v3, active)

## Sinks rulepacks under-catch
- pickle/marshal/shelve.loads on untrusted data -> RCE
- subprocess(..., shell=True), os.system -> command injection
- yaml.load without SafeLoader -> object instantiation

## Framework signals
- Django: .raw()/.extra() bypass the ORM; DEBUG=True in prod; SECRET_KEY in source
- Flask: debug=True; render_template_string with user input -> SSTI

## Triage guidance (reduce false positives)
- Django autoescaping / MarkupSafe in the template context -> downgrade reflected-XSS
- Verified parameterized query on the sink line -> likely FP even if taint reaches it

## Learned (promoted, eval-gated)
- v3: bleach.clean() default args NOT sufficient for attribute-context XSS  [#214, recall +0.4%]
```

**The gated learning loop (why it is gated, not automatic):**
```
1. Analyst overturns/annotates a verdict in the portal
      -> candidate_recorder writes a row to skill_learning_candidates
         { scope: common|python|..., proposed_guidance, triggering_finding,
           analyst_id, status: 'pending' }
      (this is a CANDIDATE, never a live edit)

2. eval_gate compiles the candidate into a trial skill version and runs the
   EVAL HARNESS (Phase 0) on the known-answer corpus:
      -> promote only if precision/recall do NOT regress (and ideally improve)
      -> a poisoning attempt ("suppress this real class") drops recall -> auto-REJECTED
         to _learning/rejected/ with the metrics, before any human sees it

3. A human (admin) reviews passing candidates and approves.

4. promoter writes a NEW versioned SKILL.md (git commit + registry.yaml bump).
   Fully audited; rollback = revert to the prior pinned version.
```

**Security properties (this loop IS a control, not just a feature):**
- **Agents never write their own skills.** Self-modification from untrusted input is
  the attack, not the goal. Only the eval-gated + human-approved `promoter` writes.
- **Skill content is DATA, not instructions.** Injected into agent context inside a
  data boundary; the same prompt-injection defense (G0.4 in the project plan) applies,
  so a repo comment cannot rewrite agent behavior via a "skill".
- **Skill-poisoning is defeated by the eval gate:** a change that teaches the scanner
  to ignore a real vulnerability class necessarily lowers recall on the corpus and is
  rejected automatically.
- **Everything is versioned and reversible** (git + `registry.yaml` + `agent_skills`
  table), so any regression is one revert away.

---

## 6. Data Flow: Complete Scan Lifecycle

```
Step 1: INPUT (Any Channel)
Web Upload -> POST /api/v1/folders/{id}/upload
Git + CI/CD -> Webhook POST /api/v1/webhooks/github
REST API -> POST /api/v1/scans/trigger

Step 2: SCAN ORCHESTRATOR
-> Enqueue job to Celery
-> Spawn sandboxed worker
-> Allocate resources (CPU, memory, disk)
-> Set timeout (10 min default)

Step 3: CODE INTELLIGENCE LAYER (GitNexus, offline)
-> Run `gitnexus analyze --pdg` in the sandboxed worker (no network, no API key)
-> Structure + calls + imports + heritage + MRO
-> routes  -> candidate taint SOURCES (framework entry points)
-> orm     -> candidate taint SINKS
-> processes (entry-point execution flows) + communities
-> PDG: intra-procedural reaching-def + control dependence
-> Persist to .gitnexus/ (LadybugDB); export JSON snapshot for agents

Step 4: DETERMINISTIC DETECTION
-> Interprocedural Taint Engine: stitch GitNexus intra-proc PDG across the call
   graph; seed sources from `routes`+rulepacks, sinks from `orm`+rulepacks;
   apply context-sensitive sanitizers -> source->sink traces
-> Rulepacks: match/augment sources, sinks, sanitizers
-> Pattern Matcher: regex/AST patterns (secrets, dangerous APIs)
-> SCA Scanner: check dependencies against OSV database
-> Candidate Emitter: aggregate all findings with traces

Step 5: AI AGENT LAYER (via GitNexus MCP)
-> Compose agent skills for the detected stack:
     common/SKILL.md + <stack>/SKILL.md (+ framework file) -> agent context (as DATA)
For each candidate:
  -> Triage Agent: pdg_query(mode:flows) + trace
     "Is this path reachable from a real routes entry point?"
     -> Filters false positives

  -> Hunter Agent: trace/context over processes + communities
     "What auth checks exist before this function?"
     -> Discovers logic flaws, authz bypasses

  -> Fix Agent: impact (upstream) + query
     "Will this patch break callers? How do other files handle this safely?"
     -> Generates patch, assigns severity

  (every agent LLM call -> UsageMeter.record(scan_id, agent_type, provider,
   model, usage) -> one llm_usage row with computed cost_usd; local=$0)

Step 6: RESULTS & DELIVERY
-> Roll up llm_usage: scan total + per-agent + per-model cost -> scan record
-> Any analyst verdict override -> skill_learning_candidates (status 'pending';
   later eval-gated + human-approved before it changes a skill -- see 5.10)
-> Store findings in PostgreSQL (SARIF format)
-> Dashboard: trace viewer, filters, history
-> CI Gates: PR comments, compliance reports
-> Export: SARIF, JSON, PDF

Step 7: CLEANUP
-> Worker exits sandbox
-> Preserve .gitnexus/ index + findings
-> Clean up temp files
-> Update scan status
```

---

## 7. Security Design

| Layer | Threat | Mitigation |
|-------|--------|------------|
| **API Keys** | Exposure in frontend | Backend-only access; never returned to FE |
| **API Keys** | Exposure in logs | Masked in logs; decrypted only in memory |
| **API Keys** | Exposure in DB | Ciphertext in DB; **KEK injected at runtime from a separate secret** -- leaked DB alone is useless |
| **API Keys** | KEK co-location | KEK never stored beside ciphertext (no key + lock in one file); mounted secret, perms 400 |
| **Settings API** | Unauth secret writes | `PUT/DELETE /settings/providers` require **auth + admin role**; backend never rewrites `.env` |
| **Cost** | Runaway LLM spend | Optional per-scan budget cap aborts a scan past its `cost_usd` limit (§13) |
| **ZIP Upload** | Malicious files | Virus scan (ClamAV), sandboxed extraction |
| **ZIP Upload** | Zip bomb | Size limits, depth limits, file count limits |
| **Code Execution** | Dynamic code | Static analysis only; no eval/exec |
| **Sandbox** | Container escape | Non-root user, seccomp, cgroup limits |
| **Graph Data** | Sensitive code leakage | GitNexus indexes **offline** (no egress); only metadata/snippets to LLM |
| **GitNexus image** | Supply-chain tampering | Verify signed image: `cosign verify ghcr.io/abhigyanpatwari/gitnexus:<ver>`; pin exact version tag |
| **Licensing** | PolyForm-NC violation | GitNexus is Noncommercial-licensed; obtain commercial grant (akonlabs.com) before any commercial deployment |
| **Network** | Man-in-the-middle | HTTPS only; TLS 1.3 |
| **.env / KEK File** | Unauthorized access | No API-key secrets in `.env`; KEK file perms 400, read-only mount |

---

## 8. Frontend Pages & Components

### Pages

| Page | Route | Description |
|------|-------|-------------|
| **Home** | `/` | Dashboard with stats, recent scans, quick actions |
| **Projects** | `/projects` | List all projects with tags |
| **Project Detail** | `/projects/:id` | Project overview, folders, scan history |
| **Scan** | `/scan/:folderId` | Upload ZIP, configure scan, trigger |
| **Scan Results** | `/results/:scanId` | Findings list, trace viewer, agent reasoning |
| **Settings** | `/settings` | API keys, model config, agent config |
| **Rulepacks** | `/rulepacks` | Manage deterministic detection rules (sources/sinks/sanitizers) |
| **Agent Skills** | `/agent-skills` | View/edit agent reasoning skills, review learning candidates |
| **Agents** | `/agents` | Agent behavior configuration, prompt tuning |
| **Usage** | `/usage` | Cost dashboard: portal total, per-model, per-agent, trends |
| **Pricing** | `/settings/pricing` | Per-model price catalog (view + override) |

### Key Components

**UploadZone:** Drag & drop, file picker, validation
**TechStackSelector:** Dropdown + auto-detect with confidence
**TraceViewer:** Interactive source -> sink path visualization
**AgentPanel:** Shows agent reasoning (triage, hunt, fix) per finding
**GraphVisualizer:** D3.js CPG exploration with highlighting
**CodeViewer:** Monaco Editor with vulnerability highlighting
**FindingCard:** Severity, CWE, agent confidence, expand for details
**ScanCostSummary:** Per-scan $ total with triage/hunter/fix breakdown (on scan results header)
**UsageDashboard:** Portal-wide cost -- headline total, per-model + per-agent charts, date range
**ModelPicker:** Dropdown populated from a successful Test connection; custom-ID fallback
**PriceCatalogTable:** Editable per-model $/1M in-out prices (admin); "modified" badge on overrides
**SkillViewer:** Renders composed common+tech skill for a stack; shows active versions
**LearningQueue:** Pending `skill_learning_candidates` with eval-gate metrics; approve/reject (admin)

---

## 9. Database Schema

```sql
-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tag VARCHAR(20) NOT NULL CHECK (tag IN ('uat', 'dev', 'production')),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Folders
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('frontend', 'backend', 'microservice', 'other')),
    tech_stack VARCHAR(50) NOT NULL CHECK (tech_stack IN ('python3', 'python2', 'javascript', 'typescript', 'html', 'auto_detect')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scans
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folder_id UUID NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    tech_stack_detected VARCHAR(50),
    graph_index_path VARCHAR(500),  -- path to .gitnexus/ (LadybugDB) for this scan
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    total_files INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    total_input_tokens BIGINT DEFAULT 0,   -- rolled up from llm_usage
    total_output_tokens BIGINT DEFAULT 0,
    total_cost_usd NUMERIC(12,6) DEFAULT 0,-- per-scan cost (portal + scan header)
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Candidates (from deterministic layer)
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    detector VARCHAR(50) NOT NULL,  -- taint, rulepack, pattern, sca
    rule_id VARCHAR(100),
    source_file VARCHAR(500),
    source_line INTEGER,
    sink_file VARCHAR(500),
    sink_line INTEGER,
    trace_path JSONB,  -- Array of node IDs
    confidence VARCHAR(20),
    raw_evidence TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Findings (after AI agent layer)
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES candidates(id),
    rule_id VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    confidence VARCHAR(20) NOT NULL CHECK (confidence IN ('extracted', 'inferred', 'ambiguous')),
    cwe VARCHAR(20),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    line_start INTEGER,
    line_end INTEGER,
    source_node VARCHAR(255),
    sink_node VARCHAR(255),
    data_flow_path JSONB,
    remediation TEXT,
    patch_diff TEXT,  -- Generated by Fix Agent
    agent_reasoning JSONB,  -- Triage + Hunter + Fix reasoning
    created_at TIMESTAMP DEFAULT NOW()
);

-- Provider config + encrypted key (ciphertext in DB; KEK injected at runtime)
CREATE TABLE api_key_meta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL UNIQUE,   -- ollama, anthropic, openai, gemini, azure_openai, openrouter, deepseek, glm, groq
    encrypted_key TEXT,                     -- AES-256-GCM ciphertext; NULL for keyless (Ollama)
    base_url VARCHAR(500),                  -- for Ollama / self-hosted endpoints
    masked_last4 VARCHAR(8),                -- shown in UI; raw key never returned
    selected_model VARCHAR(150),            -- chosen after a successful Test connection
    is_configured BOOLEAN DEFAULT FALSE,    -- key present AND model chosen
    is_active BOOLEAN DEFAULT TRUE,         -- the provider currently used by scans
    last_tested_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- LLM usage + cost, one row per agent LLM call (per scan, per agent, per model)
CREATE TABLE llm_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('triage', 'hunter', 'fix', 'other')),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(150) NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd NUMERIC(12,6) NOT NULL DEFAULT 0,  -- 0 for local (Ollama)
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_llm_usage_scan  ON llm_usage(scan_id);
CREATE INDEX idx_llm_usage_model ON llm_usage(model);
CREATE INDEX idx_llm_usage_agent ON llm_usage(agent_type);
CREATE INDEX idx_llm_usage_date  ON llm_usage(created_at);

-- Per-model price catalog (YAML-seeded, UI-overridable). Drives cost_usd.
CREATE TABLE model_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(150) NOT NULL,
    price_in_per_mtok  NUMERIC(10,4) NOT NULL DEFAULT 0,  -- USD per 1M input tokens
    price_out_per_mtok NUMERIC(10,4) NOT NULL DEFAULT 0,  -- USD per 1M output tokens
    source VARCHAR(20) NOT NULL DEFAULT 'yaml' CHECK (source IN ('yaml', 'override')),
    is_local BOOLEAN DEFAULT FALSE,         -- TRUE for Ollama -> always $0
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (provider, model)
);

-- Portal-wide usage roll-up (materialized view; refresh on scan completion)
CREATE MATERIALIZED VIEW usage_rollup AS
SELECT provider, model, agent_type,
       COUNT(*)                AS calls,
       SUM(input_tokens)       AS input_tokens,
       SUM(output_tokens)      AS output_tokens,
       SUM(cost_usd)           AS cost_usd,
       DATE_TRUNC('day', created_at) AS day
FROM llm_usage
GROUP BY provider, model, agent_type, DATE_TRUNC('day', created_at);

-- Rulepacks (deterministic detection config; was 'skills')
CREATE TABLE rulepacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rulepack_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    language VARCHAR(50),
    version VARCHAR(20) NOT NULL,
    is_builtin BOOLEAN DEFAULT FALSE,
    yaml_content TEXT NOT NULL,          -- sources/sinks/sanitizers
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent skills (LLM reasoning knowledge; versioned, git-mirrored)
CREATE TABLE agent_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope VARCHAR(60) NOT NULL,           -- 'common', 'python', 'python/django', 'javascript', ...
    version INTEGER NOT NULL,
    content_md TEXT NOT NULL,             -- the SKILL.md body
    is_active BOOLEAN DEFAULT FALSE,      -- exactly one active version per scope
    git_sha VARCHAR(40),                  -- commit that introduced this version
    promoted_from_candidate UUID,         -- provenance (nullable for hand-authored)
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (scope, version)
);
CREATE UNIQUE INDEX one_active_skill_per_scope
    ON agent_skills(scope) WHERE is_active;

-- Learning candidates (gated pipeline: pending -> eval -> approved/rejected -> promoted)
CREATE TABLE skill_learning_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope VARCHAR(60) NOT NULL,
    proposed_guidance TEXT NOT NULL,
    triggering_finding_id UUID REFERENCES findings(id) ON DELETE SET NULL,
    analyst_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','eval_running','eval_passed','eval_failed','approved','rejected','promoted')),
    eval_precision_delta NUMERIC(6,4),    -- vs current active skill on the corpus
    eval_recall_delta NUMERIC(6,4),
    eval_report JSONB,
    reviewed_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_skill_cand_status ON skill_learning_candidates(status);

-- Agent Configurations
CREATE TABLE agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(50) NOT NULL CHECK (agent_type IN ('triage', 'hunter', 'fix')),
    model VARCHAR(100) NOT NULL,
    temperature FLOAT DEFAULT 0.1,
    max_tokens INTEGER DEFAULT 4096,
    system_prompt TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users (placeholder for future auth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 10. Environment Configuration

### `.env.example`

```bash
# === Application ===
APP_ENV=development
DEBUG=true
SECRET_KEY=change-me-in-production-32-chars-long!!!

# === Database ===
DATABASE_URL=postgresql://sast_user:sast_pass@localhost:5432/sastdb

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === GitNexus (code intelligence -- offline; Path A default) ===
GITNEXUS_MODE=serve
GITNEXUS_HTTP_URL=http://gitnexus:4747
GITNEXUS_ANALYZE_ARGS=--pdg
GITNEXUS_REGISTRY=/root/.gitnexus/registry.json

# === Neo4j (Path B ONLY -- uncomment if keeping Joern+Neo4j) ===
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=neo4j-password

# === Object Storage (MinIO) ===
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=sast-scans

# === Encryption ===
# No ENCRYPTION_KEY here. The 32-byte KEK is injected at runtime from a secret
# store (see KEK_FILE below); provider API keys are stored as ciphertext in the
# api_key_meta DB table, entered via the portal -- never in .env.

# === Azure OpenAI (non-secret endpoint config only) ===
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_VERSION=2024-02-01

# === GitNexus workers ===
GITNEXUS_MAX_WORKERS=8
# No LLM key required for indexing; LLM only for optional `gitnexus wiki`.

# === Key Encryption Key (injected, not stored here) ===
KEK_FILE=/run/secrets/sast_kek            # 32 raw bytes; read-only mount, perms 400

# === Cost & Pricing ===
PRICING_YAML=config/model_prices.yml      # seeds model_prices table on startup
PRICING_ALLOW_UI_OVERRIDE=true            # admins can override prices in the portal
COST_PER_SCAN_BUDGET_USD=0                # 0 = no cap; >0 aborts a scan past this cost
USAGE_ROLLUP_REFRESH=on_scan_complete     # on_scan_complete | hourly

# === Scan Limits ===
MAX_ZIP_SIZE_MB=100
MAX_FILES_PER_SCAN=10000
MAX_LINES_PER_FILE=10000
SCAN_TIMEOUT_SECONDS=600
SANDBOX_MEMORY_MB=4096
SANDBOX_CPU_CORES=2
```

---

## 11. Deployment Architecture

> **Path A (shown below):** `gitnexus` service replaces `neo4j`/`joern`. Indexing is
> offline, so the container sits on an `internal`-only network. Pin an exact GitNexus
> version and verify the signed image (`cosign verify ghcr.io/abhigyanpatwari/gitnexus:<ver>`)
> before deploy. **Path B:** re-add the `neo4j` (and a `joern`) service and restore
> `NEO4J_*` in `.env`.

### Docker Compose

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sastdb
      POSTGRES_USER: sast_user
      POSTGRES_PASSWORD: sast_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  gitnexus:
    # Path A (default): offline code-intelligence engine + MCP/HTTP server.
    build:
      context: .
      dockerfile: docker/Dockerfile.gitnexus
    command: ["gitnexus", "serve", "--host", "0.0.0.0", "--port", "4747"]
    environment:
      GITNEXUS_REGISTRY: /root/.gitnexus/registry.json
    networks:
      - internal            # no egress needed; indexing is offline
    volumes:
      - gitnexus_index:/root/.gitnexus
      - scan_workspace:/workspace:ro

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    env_file: .env
    volumes:
      - type: bind
        source: ./.env
        target: /app/.env
        read_only: true
    depends_on:
      - postgres
      - redis
      - gitnexus
      - minio

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    env_file: .env
    volumes:
      - type: bind
        source: ./.env
        target: /app/.env
        read_only: true
    depends_on:
      - postgres
      - redis
      - gitnexus

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  gitnexus_index:
  scan_workspace:
  minio_data:

networks:
  internal:
    internal: true
```

---

## 12. Future Enhancements

| Feature | Description | Priority |
|---------|-------------|----------|
| **Authentication** | OAuth2 / SSO login, RBAC | High |
| **Git Integration** | Native git clone, branch scanning, PR diff scanning | High |
| **SARIF Export** | Standard format for security tool interoperability | High |
| **Incremental Scanning** | Only re-scan changed files using git diff | High |
| **GitNexus incremental re-index** | Use `detect_changes` / staleness vs HEAD to re-analyze changed files only | High |
| **Reachability gating** | Suppress taint candidates GitNexus proves unreachable from any `routes` entry point (confidence-down, not hard-suppress) | High |
| **License clearance** | Resolve PolyForm-NC before commercial launch: commercial grant (akonlabs) or keep deployment noncommercial | High |
| **Skill eval-gate automation** | Auto-run the eval harness on every learning candidate; surface precision/recall deltas in the review queue | High |
| **Per-org private skills** | Tenant-scoped agent skills + private eval corpora so learning stays isolated | Medium |
| **Upstream taint models** | Extend GitNexus's Python/Java source-sink models for more frameworks | Medium |
| **Additional language support** | Per-language rulepacks + taint models + agent skills + eval corpora for **Java, C/C++, Go, .NET** (modular; no re-architecture) | High |
| **Evaluation corpora (future languages)** | **OWASP Benchmark** (Java) and **NIST Juliet** (C/C++) as known-answer corpora for those languages; harness stays language-agnostic | Medium |
| **Path B unified store** | Optionally export GitNexus graph into Neo4j for single-Cypher queries across structure + dataflow | Low |
| **False Positive Learning** | Agent feedback loop to improve triage | Medium |
| **Custom Agent Prompts** | User-defined agent behaviors | Medium |
| **Multi-repo Cross-Reference** | Track vulnerabilities across services | Medium |
| **Baseline Mode** | Compare against previous scan | Medium |
| **Team Collaboration** | Comments, assignment, Jira integration | Low |
| **Compliance Reports** | OWASP Top 10, PCI-DSS mapping | Low |
| **GPU Acceleration** | Local LLM optimization | Low |

---

## 13. Pricing Catalog & Cost Model

### 13.1 How pricing is stored and resolved

Cost is computed from token counts x a per-model price. Prices live in a catalog that
is **seeded from YAML and overridable in the portal UI** (both, per configuration):

```
Startup:  config/model_prices.yml  ->  seed/upsert into model_prices (source='yaml')
Runtime:  admin edits a price in the portal
              -> row updated, source='override'  (UI override wins over YAML)
          POST /settings/pricing/reseed
              -> re-applies YAML to source='yaml' rows; 'override' rows are preserved
Resolve:  UsageMeter reads model_prices for (provider, model)
              -> is_local = TRUE (Ollama)  =>  price_in = price_out = 0
              -> unknown model             =>  price 0 + a "price missing" portal warning
```

**Seed file (`config/model_prices.yml`) -- illustrative; verify current vendor prices:**
```yaml
# USD per 1,000,000 tokens. Local runtimes are $0.
# NOTE: prices change often -- treat this as a starting seed, confirm before billing.
prices:
  - {provider: ollama,     model: "*",                       in: 0,    out: 0,  local: true}
  - {provider: anthropic,  model: claude-sonnet-4-5,         in: 3.00, out: 15.00}
  - {provider: openai,     model: gpt-4.1,                   in: 2.00, out: 8.00}
  - {provider: gemini,     model: gemini-2.5-flash,          in: 0.30, out: 2.50}
  - {provider: deepseek,   model: deepseek-chat,             in: 0.28, out: 0.42}
  - {provider: groq,       model: llama-3.3-70b-versatile,   in: 0.59, out: 0.79}
  - {provider: openrouter, model: "anthropic/claude-sonnet-4.5", in: 3.00, out: 15.00}
```
> These figures are indicative seeds only and will drift. The catalog is the single
> place to correct them; nothing else in the system hardcodes a price.

### 13.2 What the portal shows

| Surface | Grain | Source |
|---------|-------|--------|
| Scan results header (`ScanCostSummary`) | one scan: total + triage/hunter/fix split | `scans.total_cost_usd` + `llm_usage` group |
| Usage dashboard headline (`UsageDashboard`) | portal total over a date range | `SUM(llm_usage.cost_usd)` |
| Usage dashboard charts | per-model and per-agent cost + tokens | `usage_rollup` |
| Pricing page (`PriceCatalogTable`) | per-model in/out prices, override state | `model_prices` |

### 13.3 Deployment plans

The platform ships in three plans. **LLM/token spend is separate from the plan** --
with a local model (Ollama) or a customer-supplied API key, per-scan LLM cost can be
$0 or billed directly by the provider; the plan governs platform features/limits.

| Capability | **Community** (self-host) | **Team** | **Enterprise** |
|-----------|---------------------------|----------|----------------|
| License | Free, self-hosted | Per-seat subscription | Custom contract |
| Providers | All 9 incl. local Ollama | All 9 | All 9 + private/VPC endpoints |
| Concurrent scans | 1 | Up to 5 | Configurable / unlimited |
| Cost tracking | Per scan + portal total | + per agent + per model | + budgets, alerts, chargeback export |
| Per-scan budget cap | -- | Yes | Yes + org-level quotas |
| Price catalog override | YAML only | YAML + UI | YAML + UI + per-team catalogs |
| Agent skills | Built-in common + tech skills | + gated learning loop | + per-org private skills, custom corpora |
| History retention | 30 days | 12 months | Configurable |
| SSO / RBAC | Basic auth | Google/GitHub SSO | SAML/OIDC, fine-grained RBAC |
| CI/CD gating | Yes | Yes | Yes + policy-as-code |
| Air-gapped mode | Yes (Ollama + offline GitNexus) | -- | Yes (fully offline) |
| Support | Community | Business hours | SLA + dedicated |
| GitNexus license | Must self-clear PolyForm-NC | Included (commercial) | Included (commercial) |

> **GitNexus licensing carries into the plans:** because GitNexus is PolyForm
> Noncommercial, the Team/Enterprise (commercial) plans must include a GitNexus
> commercial license (via akonlabs) or ship the permissive fallback structure engine
> noted in §3. Community users self-clear their own noncommercial use.

### 13.4 Cost-control features

- **Per-scan budget cap** (`COST_PER_SCAN_BUDGET_USD`): the `UsageMeter` aborts a scan
  when cumulative `cost_usd` crosses the cap; partial findings are preserved.
- **Model routing by agent:** because cost is tracked per agent, you can route the
  cheap high-volume Triage agent to a small/local model and reserve a stronger model
  for the Hunter/Fix agents -- optimizing $/scan without losing verdict quality.
- **Local-first:** running Ollama makes token spend $0 and keeps code offline; the
  cost tables still record tokens so you can compare "what this would have cost" on a
  cloud model.

---

## Appendix A: API Endpoints Summary

```
# Projects
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{id}
PUT    /api/v1/projects/{id}
DELETE /api/v1/projects/{id}

# Folders
POST   /api/v1/projects/{id}/folders
GET    /api/v1/projects/{id}/folders
GET    /api/v1/folders/{id}
PUT    /api/v1/folders/{id}
DELETE /api/v1/folders/{id}

# Uploads & Scans
POST   /api/v1/folders/{id}/upload
POST   /api/v1/folders/{id}/git
POST   /api/v1/scans/trigger
GET    /api/v1/scans/{id}
GET    /api/v1/scans/{id}/status
GET    /api/v1/scans/{id}/candidates
GET    /api/v1/scans/{id}/findings
GET    /api/v1/scans/{id}/graph
DELETE /api/v1/scans/{id}

# Webhooks
POST   /api/v1/webhooks/github
POST   /api/v1/webhooks/gitlab

# Settings (provider config -- auth + admin role required on writes)
GET    /api/v1/settings/providers                 # list: configured?, masked_last4, selected_model
PUT    /api/v1/settings/providers/{id}            # set key/base_url and/or selected model
DELETE /api/v1/settings/providers/{id}            # remove stored key
POST   /api/v1/settings/providers/{id}/test       # -> { ok, model_count, models[] }
GET    /api/v1/settings/providers/{id}/models     # cached model list from last successful test
GET    /api/v1/settings/agents
PUT    /api/v1/settings/agents/{type}

# Pricing catalog (admin)
GET    /api/v1/settings/pricing                   # per-model prices (yaml + overrides)
PUT    /api/v1/settings/pricing/{provider}/{model}# override in/out price
POST   /api/v1/settings/pricing/reseed            # re-seed from PRICING_YAML

# Usage & cost
GET    /api/v1/usage/summary                       # portal total, per-model, per-agent (date range)
GET    /api/v1/usage/scans/{scan_id}               # per-scan total + per-agent breakdown
GET    /api/v1/usage/export                         # CSV export of llm_usage

# Rulepacks (deterministic detection config; was /skills)
GET    /api/v1/rulepacks
GET    /api/v1/rulepacks/{id}
POST   /api/v1/rulepacks
PUT    /api/v1/rulepacks/{id}
DELETE /api/v1/rulepacks/{id}
POST   /api/v1/rulepacks/{id}/validate

# Agent skills (LLM reasoning knowledge)
GET    /api/v1/agent-skills                        # scopes + active versions
GET    /api/v1/agent-skills/{scope}                # active SKILL.md (+ history)
GET    /api/v1/agent-skills/compose?stack=python   # preview composed context for a stack
PUT    /api/v1/agent-skills/{scope}                # hand-author a new version (admin)
POST   /api/v1/agent-skills/{scope}/rollback       # revert to a prior version

# Learning loop (gated)
POST   /api/v1/learning/candidates                 # analyst feedback -> candidate
GET    /api/v1/learning/candidates                 # queue (filter by status)
POST   /api/v1/learning/candidates/{id}/eval       # run eval-harness gate
POST   /api/v1/learning/candidates/{id}/approve    # admin approve -> promote (if eval passed)
POST   /api/v1/learning/candidates/{id}/reject

# Agents
GET    /api/v1/agents/config
PUT    /api/v1/agents/config/{type}
POST   /api/v1/agents/{finding_id}/rerun

# Health
GET    /api/v1/health
GET    /api/v1/health/ready
GET    /api/v1/health/live
```

---

*End of Architecture Document v2.3*
