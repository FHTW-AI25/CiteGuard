# Changelog

All notable changes to CiteGuard are recorded in this file.

The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and the project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). The versioning rules for this project are in [docs/VERSIONING.md](docs/VERSIONING.md).

## [Unreleased]

### Added

- Contributing guide (`CONTRIBUTING.md`) covering tasks and issues, branches, commit and pull-request rules, review pairs and project-specific code rules.
- Evaluation protocol (`docs/EVALUATION.md`) defining the benchmark construction, labelling rules, metric definitions, ablation profiles, injection suite and reporting rules.
- Implementation plan (`docs/IMPLEMENTATION_PLAN.md`) with per-week tasks, dependencies, milestones, cut order and risks.

### Changed

- Technical Design Document revised to architecture baseline v1.1:
  - The deployment stack now uses LangFuse v3 with ClickHouse, Redis and MinIO, because LangFuse v2 cannot receive OpenTelemetry traces.
  - Paper ingestion is a dedicated `ingest-worker` service with a shared `paper_storage` volume. The earlier compose file had no consumer for the ingestion queue.
  - The per-claim workflow has a new `UNGROUNDED` route for when the judge's quote still cannot be verified after 2 retries. Such claims are reported for manual review and never cached.
  - `get_page_window` takes a `project_id`, MCP servers authenticate with `Authorization: Bearer`, and `latex-mcp` rejects paths outside the project directory.
  - Added `auth/refresh`, `auth/logout` and `auth/dev/register` to the API table.
  - Named the embedding model (`gemini-embedding-001` at 768 dimensions) and described how the `adk_sessions` and `lightrag` schemas are separated.

### Fixed

- Technical Design Document: corrected the ADK import path to `google.adk.workflow`, the LightRAG configuration (required `embedding_func`, `llm_model_func`, `initialize_storages()` and the `POSTGRES_*` / `NEO4J_USERNAME` environment variables), the backend Dockerfile (the virtualenv was built at a different path than it ran from) and the retry limit on RabbitMQ queues (quorum queues with `x-delivery-limit`).

## [0.1.0] - 2026-11-27

Design baseline. No runnable code yet.

### Added

- Technical Design Document (`docs/TDD.md`, architecture baseline v1.0) covering the agent workflow, MCP tool servers, data model, API, authentication, frontend, security, deployment and evaluation plan.
- `README.md` with a project overview based on the design.
- `CLAUDE.md` with guidance for Claude Code.
- Semantic versioning policy (`docs/VERSIONING.md`), `VERSION` file, this changelog and the release helper `scripts/bump-version.sh`.

[Unreleased]: https://github.com/FHTW-AI25/CiteGuard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/FHTW-AI25/CiteGuard/releases/tag/v0.1.0
