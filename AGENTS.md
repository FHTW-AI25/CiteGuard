# AGENTS.md

This file gives AI coding agents the context they need to work in this repository. It is tool-neutral: `CLAUDE.md` imports it, and other harnesses read it directly. Keep it factual and short, and change it through a pull request like any other shared file.

## Repository state

This repository is **pre-implementation**. It contains documentation only: the Technical Design Document (`docs/TDD.md`, architecture baseline v1.2), the implementation plan, the evaluation protocol, the ADRs, the contributing guide and the versioning files. There is no source code, build, lint or test setup yet, so there are no verified commands. When you add the first build/test tooling (task W1-01), record the real commands here.

`docs/TDD.md` is the source of truth for architecture, schemas, tool signatures, API routes and the compose file. Read the relevant section before implementing a component, and update the TDD when an implementation deliberately diverges from it.

`docs/IMPLEMENTATION_PLAN.md` gives the build order as task IDs (`W1-03`, `W2-10`, …) with dependencies and "done when" conditions. When asked to implement something, find its task there first and respect its dependencies and the cut order.

`CONTRIBUTING.md` holds the group's workflow rules. The ones that affect how changes are made here: branches are named after the task ID (`w2-04-chunk-search`), commit subjects are lower case and imperative with no trailing full stop, pull requests are titled `W2-04: …` and squash-merged, prompts live in version-controlled files rather than inline in code, database tests use real PostgreSQL 18 (not SQLite), and CI tests never call a live model or external API.

`docs/adr/` holds architecture decision records. Check the status before relying on one: a **Proposed** ADR is a recommendation, and the TDD still shows the old choice until it is **Accepted**. As of baseline v1.2, ADRs 0001 (models), 0002 (LangFuse) and 0003 (PDF parsing, proposing to drop PyMuPDF) are all Proposed, so the model names and "Docling/PyMuPDF" in the TDD are not final.

## Versioning and changelog

The project uses Semantic Versioning with one version for the whole repository, stored in `VERSION`. Rules, including what counts as a breaking change, are in `docs/VERSIONING.md`.

- Add a line under `## [Unreleased]` in `CHANGELOG.md` in the same change as any user- or deployer-visible modification (Keep a Changelog headings).
- Do not edit `VERSION` or released changelog sections by hand. Releases are cut with `scripts/bump-version.sh <major|minor|patch|X.Y.Z>`, which updates both files but does not commit or tag.
- When adding a package manifest (`pyproject.toml`, `package.json`), make it read from `VERSION` or extend the bump script to update it.

## What CiteGuard is

A multi-agent system that audits Master's thesis drafts (`.tex` / `.md`) sentence by sentence against the cited literature, detecting unsupported claims, numeric drift and citation-key swaps. It is a course group project with four mandatory requirements that the design must keep satisfying (TDD §1): at least 3 agents, at least 3 tools plus constrained decoding, hybrid (short- and long-term) agent memory, and a security and observability pipeline.

Non-goals: CiteGuard never mutates the thesis repository (it emits reviewable unified `.patch` diffs only) and does not compile LaTeX to PDF.

## Planned stack and layout (TDD §11)

- `backend/`: FastAPI API, Google ADK 2.x worker, SQLAlchemy 2.0 async models, Alembic. Python 3.12, dependencies managed with `uv` (`pyproject.toml` + `uv.lock`). The API and the `adk-worker` are the same image with different commands (`uvicorn app.main:app` vs `python -m app.workers.audit_worker`).
- `mcp-servers/{latex-mcp,corpus-rag-mcp,academic-search-mcp}/`: three FastMCP servers over Streamable HTTP on ports 8001, 8002, 8003.
- `frontend/`: Vite 6, React 19, strict TypeScript, Tailwind v4, shadcn/ui, managed with `pnpm`.
- `benchmarks/`: synthetic corruption generator and ablation runner (`benchmarks/run_eval.py`).
- `docker-compose.yml`: PostgreSQL 18 (`pgvector/pgvector:pg18`), Neo4j 5, RabbitMQ, LangFuse, the three MCP servers, `backend-api`, `adk-worker`, `frontend`.

## Architecture in brief

Request path: frontend → FastAPI (`/api/v1`) → RabbitMQ (`citeguard.commands`) → ADK worker → MCP servers → PostgreSQL / Neo4j. Progress flows back through the `citeguard.events` topic exchange (`audit.{run_id}.progress`) to an SSE endpoint. Failed messages dead-letter to `q.citeguard.dlq` after 3 retries and mark the `audit_runs` row `FAILED`.

Per-claim ADK `Workflow` (TDD §3), mixing `LlmAgent`s with deterministic `FunctionNode`s:

```
claim_extractor → cache_router ─ CACHE_HIT ──────────────────────────────→ result_emitter
                       └ CACHE_MISS → evidence_retriever → evidence_sanitizer
                                      → faithfulness_judge → quote_verifier
                                           ↑ RETRY_JUDGE (max 2) ┘
                         quote_verifier ─ VERIFIED_OK → cache_writer → result_emitter
                                        └ NEEDS_PATCH → revision_patcher → cache_writer
                                        └ UNGROUNDED (retries exhausted) → result_emitter, never cached
```

`claim_extractor` runs once per chapter; the graph from `cache_router` onward is one workflow instance per claim. Nodes with several incoming edges must be plain nodes, not `JoinNode` (which waits for all predecessors). The import is `google.adk.workflow` (singular).

Library facts verified against the released packages (google-adk 2.15, lightrag-hku 1.5): LightRAG takes its PostgreSQL and Neo4j connections from `POSTGRES_*` and `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` environment variables and needs `embedding_func`, `llm_model_func` and `await rag.initialize_storages()`. The LangFuse server must be 4.59.0 or later to match Python SDK v5 (v2 has no OTLP endpoint, v3 only works with SDK v4); pin SDK and server together. Paper ingestion is a separate `ingest-worker` service that writes to PostgreSQL and Neo4j directly; `corpus-rag-mcp` is read-only.

## Design invariants

These are load-bearing for the security model and the benchmark ablations. Do not relax them without updating the TDD.

- **Least-privilege tools.** Each agent gets an explicit `tool_filter` list (table in TDD §3.2). `faithfulness_judge` has zero MCP tools, only the local constrained tool `record_audit_verdict`. `search_candidate_citations` is restricted to `revision_patcher`.
- **Evidence is untrusted.** Retrieved text must pass through `evidence_sanitizer` (strip invisible Unicode, flag instruction-like strings, wrap in `<untrusted_evidence>`) before the judge sees it.
- **Quote grounding is deterministic.** Every verdict other than `NOT_FOUND` requires `exact_source_quote` and `evidence_ref` (enforced by the `ClaimVerificationVerdict` validator) and `quote_verifier` checks the quote is verbatim in the retrieved chunks, retrying the judge at most twice.
- **Constrained decoding.** The judge's `output_schema` and `record_audit_verdict` use strict Pydantic schemas (TDD §3.3), not prompt-instructed JSON.
- **Thesis files are read-only.** `latex-mcp` mounts `/data/projects:ro`, and `generate_latex_diff` returns a diff without writing to disk.
- **Claim cache key.** `claim_fingerprint = sha256(norm_claim || cite_key || doc_sha256)`, unique per `(project_id, claim_fingerprint)` in `verified_claim_cache`.
- **UUID v7 everywhere.** Primary keys use PostgreSQL 18 `uuidv7()` as server default and `uuid_utils.uuid7()` in Python, through `UUIDv7TimestampMixin` (TDD §6.2).
- **Schema separation.** App tables in `public`, ADK session tables in `adk_sessions`, LightRAG tables in `lightrag`, so Alembic autogenerate does not drift. LightRAG reuses the existing Postgres and Neo4j (no extra vector store), with `workspace=project_id` for tenant isolation.
- **Auth strategy by `AUTH_MODE`.** `dev` mounts email/password routes, `prod` mounts Google OAuth (PKCE) routes. The other mode's routes are never registered. Startup fails closed if `AUTH_MODE=dev` with `ENVIRONMENT=production`. Every project-scoped route goes through `require_project_owner`.
- **Network boundary.** MCP servers sit on the internal Docker network only and validate a service token. Services run as non-root.
- **One trace per audit.** W3C `traceparent` is propagated through AMQP message properties so FastAPI, worker, ADK and MCP spans share a trace ID exported to LangFuse.

## Models

The TDD names `gemini-2.5-flash` for `claim_extractor` and `evidence_retriever` and `gemini-2.5-pro` for `faithfulness_judge` and `revision_patcher`. These are not final: ADR 0001 (Proposed) makes the model IDs configuration (`MODEL_FAST`, `MODEL_STRONG`, `MODEL_EMBEDDING`), so do not hard-code a model name. Embeddings are `vector(768)` with HNSW cosine indexes.

## Frontend direction

The UI follows the "Editorial Scholarly Studio" language in TDD §9.2 (warm paper canvas, serif for quoted passages, mono for LaTeX and diffs, muted status colors), not a dark-neon developer dashboard. The core view is a 3-pane audit workbench (thesis viewer, evidence and lineage inspector, patch and memory panel).

## Evaluation

`docs/EVALUATION.md` is the binding protocol for `benchmarks/`: dataset format (`claims.jsonl`, joined to system output by file and line number), scoring rules, metric definitions and the ablation profile names (`full`, `mono`, `free-json`, `dense-only`, `no-cache`, `unsanitized`). Never tune prompts or thresholds against the frozen benchmark; use the development set. The quote normalisation must be one shared function used by both `quote_verifier` and the evaluator.

The benchmark is a 180-claim suite (90 ground-truth, 90 controlled corruptions) run across a 5-axis ablation matrix (TDD §12). Each axis compares a control variant against the full system, so components such as the sanitizer, the claim cache, hybrid retrieval and constrained decoding need to be switchable per run (`ablation_profile` span attribute).
