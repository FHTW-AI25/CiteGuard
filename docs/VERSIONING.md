# Versioning

CiteGuard follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). Versions have the form `MAJOR.MINOR.PATCH`, with an optional pre-release suffix such as `1.0.0-rc.1`.

## Single source of truth

The current version is the single line in the [`VERSION`](../VERSION) file at the repository root. The whole repository (backend, MCP servers, frontend, benchmarks) is released together under that one version.

When package manifests are added (`backend/pyproject.toml`, `frontend/package.json`, the MCP servers' `pyproject.toml` files), they must either read the version from `VERSION` or be updated by `scripts/bump-version.sh`. Extend the script when you add a manifest.

Git tags are the version prefixed with `v`, for example `v0.2.0`.

The "Architecture Baseline v1.0" label inside `docs/TDD.md` is the revision of that document. It is separate from the project version.

## What counts as the public interface

A change is breaking when it forces someone who uses or deploys CiteGuard to change something. The public interface is:

- REST and SSE endpoints under `/api/v1`, including request and response shapes and progress event names.
- MCP tool names, parameters and return types on the three MCP servers.
- The `ClaimVerificationVerdict` schema and the `EntailmentStatus` values.
- The database schema, when a migration cannot be applied automatically or loses data.
- RabbitMQ exchange, queue and routing key names, and message payloads.
- Environment variables and Docker Compose service names.
- The `claim_fingerprint` definition, since changing it invalidates every cached verdict.

## When to bump which number

| Bump | When | Examples |
| :--- | :--- | :--- |
| **MAJOR** | A breaking change to the public interface. | Removing or renaming an API route, changing a verdict field's type, renaming an environment variable. |
| **MINOR** | New functionality that is backwards compatible. | A new endpoint, a new MCP tool, a new optional verdict field, a new agent or node, an additive migration. |
| **PATCH** | Backwards compatible fixes and internal changes. | Bug fixes, prompt tuning, performance work, dependency updates, documentation. |

### Before 1.0.0

While the version is `0.y.z` the interface is not stable:

- Breaking changes bump **MINOR** (`0.2.0` → `0.3.0`).
- Everything else bumps **PATCH**.

`1.0.0` is released when the full pipeline in the TDD runs end to end and the benchmark results are published.

## Changelog

Every change that a user or deployer would notice gets a line in [`CHANGELOG.md`](../CHANGELOG.md) under `## [Unreleased]`, in the same pull request as the change. Use the Keep a Changelog headings:

- `Added` for new features.
- `Changed` for changes to existing behaviour.
- `Deprecated` for features that will be removed.
- `Removed` for removed features.
- `Fixed` for bug fixes.
- `Security` for vulnerability fixes.

Mark breaking changes with a leading `**Breaking:**`. Write entries for the reader of the release, not as commit messages.

## Cutting a release

1. Make sure `main` is green and `## [Unreleased]` in the changelog describes everything in the release.
2. Run the helper with the bump type or an explicit version:

   ```bash
   scripts/bump-version.sh minor      # or: major | patch | 1.0.0-rc.1
   ```

   It updates `VERSION`, moves the `Unreleased` entries under a new dated heading, and updates the comparison links. It refuses to run if `Unreleased` is empty. It does not commit, tag or push.
3. Review the diff, then commit and tag using the commands the script prints:

   ```bash
   git commit -am "Release v0.2.0"
   git tag -a v0.2.0 -m "v0.2.0"
   git push origin main --follow-tags
   ```
