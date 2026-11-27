# Contributing to CiteGuard

This guide is for the four members of the project group. It describes how we change the repository so that work from four parallel tracks fits together.

Related documents:

- [docs/TDD.md](docs/TDD.md): what we are building.
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md): the tasks, their order and their owners.
- [docs/EVALUATION.md](docs/EVALUATION.md): how results are measured.
- [docs/VERSIONING.md](docs/VERSIONING.md): version numbers, changelog and releases.

## The short version

1. Pick a task from the implementation plan and assign its GitHub issue to yourself.
2. Create a branch from `main` named after the task.
3. Make the change with tests, and add a changelog line if a user or deployer would notice it.
4. Open a pull request, get one approval, squash-merge.

## Tasks and issues

- Every task in the implementation plan has an ID such as `W2-04`. Each gets one GitHub issue titled `W2-04: corpus-rag-mcp chunk search`, in the milestone for its week.
- Work that is not in the plan (a bug, an idea) gets an issue first. If it is more than a small fix, it is added to the plan before anyone starts on it.
- Before starting a task, check its **Depends on** column. If a dependency is not merged, build against the shared contracts with a fake rather than waiting.
- A task is finished when its **Done when** condition is met and the [definition of done](docs/IMPLEMENTATION_PLAN.md#definition-of-done) holds.

## Branches

- `main` is always in a working state. Nobody pushes to it directly; every change arrives through a pull request.
- Branch names start with the task ID in lower case, followed by a few words: `w2-04-chunk-search`. For work without a task ID use `fix/…` or `docs/…`.
- Keep branches short-lived. Rebase on `main` at least daily. A branch open for more than three days is a sign the task should be split.

Until the scaffold task W1-01 is merged, the repository holds documentation only and direct commits to `main` have been the practice. From W1-01 onward the rule above applies, and `main` is protected on GitHub (one approval and green CI required).

## Commits

Commit messages follow the style already in the history:

- Lower case, imperative mood, no trailing full stop: `add implementation plan`, `fix quote normalisation for ligatures`.
- At most 72 characters in the subject line.
- Use the body to explain *why* when it is not obvious from the diff.

Commits inside a branch can be as rough as you like, because pull requests are squash-merged.

## Pull requests

- **Title:** the task ID and a subject in commit style, for example `W2-04: add hybrid chunk search`. With squash merge this becomes the commit on `main`.
- **Description:** what changed, how you tested it, and anything the reviewer should look at closely. Link the issue with `Closes #12`.
- **Size:** aim for under 400 changed lines, not counting lock files and generated code. Split larger tasks into several pull requests behind the same issue.
- **Draft early.** Open a draft pull request as soon as there is something to look at, especially for anything that touches a shared contract.

Checklist before asking for review:

- [ ] The task's "done when" condition is met.
- [ ] Tests cover the new behaviour and pass locally.
- [ ] Lint and format checks pass.
- [ ] `CHANGELOG.md` has a line under `Unreleased`, if the change is noticeable.
- [ ] The TDD is updated if the implementation deliberately differs from it.
- [ ] New environment variables are in `.env.example` and in the README table.

### Review

- One approval from another group member is required.
- Default reviewers follow the points where tracks meet: **A and C** review each other, **B and D** review each other. Ask a specific person if someone else knows the area better.
- Review within one working day. If you cannot, say so, so the author can ask someone else.
- Reviewers check that the change is correct, tested and matches the TDD. Style is the linter's job.
- The author merges, after approval and green CI, using **squash and merge**. Delete the branch afterwards.

### Changes that need more than one reviewer

Some changes affect everyone. Announce them in the group channel and get agreement from the owners of all affected tracks before merging:

- The shared contracts package: verdict and claim schemas, MCP tool signatures, progress events.
- Database migrations that change existing columns.
- RabbitMQ exchange, queue or routing key names.
- Anything in `docs/EVALUATION.md` or `benchmarks/data/` after the benchmark is frozen. This needs all four members.

## Changelog and versions

- Add a line under `## [Unreleased]` in `CHANGELOG.md` in the same pull request as any change a user or deployer would notice. Internal refactoring and tests do not need one.
- Mark breaking changes with a leading `**Breaking:**`. What counts as breaking is listed in [docs/VERSIONING.md](docs/VERSIONING.md).
- Do not edit `VERSION` or released changelog sections by hand. Releases are cut by track A at the end of each milestone with `scripts/bump-version.sh`.

## Design changes and decisions

- **The TDD stays true.** If you implement something differently from the TDD on purpose, change the TDD in the same pull request. If you find the TDD is wrong, fix it.
- **Record decisions as ADRs.** A choice between real alternatives (a library, a storage layout, a protocol) gets a short record in `docs/adr/NNNN-title.md` with the context, the decision and the consequences. One page is enough. The template, the status meanings and the index are in [docs/adr/README.md](docs/adr/README.md).

## AI coding assistants

- `AGENTS.md` is the one shared instruction file for AI coding tools. `CLAUDE.md` only imports it. If your tool reads a different file name, add a file that points to `AGENTS.md` rather than copying its content.
- Change `AGENTS.md` through a pull request. It holds project facts and rules, not personal preferences or tricks for one model.
- Personal instructions and settings stay out of the repository: `CLAUDE.local.md` and `.claude/settings.local.json` are git-ignored.
- You are responsible for what you commit, whoever or whatever wrote it. Generated code gets the same tests and review as any other.

## Development setup

> The tooling below is created by task W1-01. Until that is merged these commands do not exist. Whoever completes W1-01 replaces this note with the verified commands.

Planned prerequisites: Docker with Compose, Python 3.12, [`uv`](https://docs.astral.sh/uv/), Node 22 and `pnpm`.

Planned commands:

| Purpose | Command |
| :--- | :--- |
| Start the whole stack | `cp .env.example .env`, then `docker compose up --build` |
| Install backend dependencies | `uv sync` in `backend/` or an MCP server directory |
| Run backend tests | `uv run pytest` |
| Run one test | `uv run pytest path/to/test_file.py::test_name` |
| Lint and format Python | `uv run ruff check` and `uv run ruff format` |
| Apply migrations | `uv run alembic upgrade head` in `backend/` |
| Install frontend dependencies | `pnpm install` in `frontend/` |
| Run frontend tests | `pnpm test` |

## Code rules specific to this project

General good practice is assumed. These are the rules that are particular to CiteGuard.

### Tests

- Database tests run against a real PostgreSQL 18 with `pgvector`, not SQLite, because the schema relies on `uuidv7()`, `vector` and `tsvector`.
- Tests must not call a live model or an external scholarly API in CI. Use recorded responses. Tests that need a live call are marked so that CI skips them and are run by hand.
- Every route of the workflow graph has a test, including the retry and `UNGROUNDED` paths.
- Security properties are asserted in tests rather than assumed: the judge has no MCP tool, path traversal is rejected, a second user cannot read a project.

### Migrations

- One migration per pull request. Never edit a migration that is already on `main`; add a new one.
- Every migration has a working downgrade.
- If two branches add migrations at the same time, the second to merge rebases and re-points its `down_revision`.

### Agents and tools

- An agent's tool list is exactly the one in TDD §3.2. Adding a tool to an agent is a design change and needs a TDD update.
- Text from papers or external APIs is untrusted. It reaches the judge only through `evidence_sanitizer`.
- Prompts live in files under version control, not inline in code, so that changes are visible in review and can be hashed for evaluation runs.
- A component that an ablation switches off gets its switch when it is written.

### Evaluation

- Do not tune a prompt, threshold or normalisation rule against the frozen benchmark. Use the development set.
- The quote normalisation is one shared function, used by both `quote_verifier` and the evaluator.
- Benchmark PDFs are not committed; only the manifest with hashes is.
- Results files in `benchmarks/results/` are committed as produced and never edited.

### Secrets and data

- Never commit `.env`, API keys or OAuth client secrets. If one is committed by mistake, tell the group and rotate it immediately; removing it from history is not enough.
- Development default passwords in `docker-compose.yml` are for local use only.
- Do not commit thesis drafts or papers that we do not have the right to redistribute.

## When something is unclear

Ask in the group channel before guessing, especially about a shared contract. A five-minute question is cheaper than two tracks building against different assumptions.
