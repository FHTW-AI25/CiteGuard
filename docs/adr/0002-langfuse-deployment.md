# 0002. LangFuse deployment

| | |
| :--- | :--- |
| **Status** | Proposed |
| **Date** | 2026-11-27 |
| **Deciders** | _the four group members, on acceptance_ |
| **Plan item** | P-02 |

## Context

Tracing to LangFuse is one of the four mandatory course requirements (TDD §1), and the evaluation protocol reads latency, token counts and scores from the traces. LangFuse can be self-hosted or used as a hosted service.

Facts checked on 2026-11-27:

- **Server and SDK versions are coupled.** LangFuse Python SDK v5, the current release, requires a self-hosted server of 4.59.0 or later. A v3 server works only with SDK v4. A v2 server has no OpenTelemetry endpoint at all (it was added in 3.22.0).
- **Self-hosting needs five containers** besides PostgreSQL: the web application, a worker, ClickHouse, Redis and S3-compatible storage (MinIO).
- **LangFuse Cloud's free Hobby plan** includes 50,000 units per month, 30 days of data access and **2 users**. The Core plan costs 29 USD per month, with 100,000 units, 90 days of data access and no user limit.

Estimated usage: one audited claim produces roughly 20 observations (model calls, tool calls, workflow nodes) and 4 scores, so one 180-claim benchmark run is about 4,000 to 5,000 units. The evaluation protocol calls for up to 18 benchmark runs plus 120 injection runs, on top of four weeks of development traffic. That is well above 50,000 units in a month. This is an estimate made before any code exists and should be re-checked after the first real trace.

Other considerations:

- Thesis drafts are unpublished work. With self-hosting, their text never leaves the machine in a trace.
- The group has four members, so a two-user limit locks half of the group out of the traces.
- The final report links to representative traces. Links into a self-hosted instance only work on the machine that runs it.

## Options

### A. Self-host LangFuse v4

- No quota and no user limit; everything starts with `docker compose up`.
- Trace content stays local.
- Five extra containers. ClickHouse in particular needs memory, which may be a problem on a laptop that also runs PostgreSQL, Neo4j and RabbitMQ.
- Task W1-04 is real work, and the configuration must track LangFuse's own compose file.

### B. LangFuse Cloud, Hobby plan

- Nothing to run or maintain.
- Two users for a group of four.
- The estimated usage exceeds the monthly quota, and the plan has no paid overage.
- Trace content, including thesis text, is sent to a third party.

### C. LangFuse Cloud, Core plan

- Nothing to run; no user limit; shareable trace links.
- 29 USD for the month. Usage above 100,000 units is billed, and the estimate is close to that figure.
- Trace content is sent to a third party.

### D. Self-host LangFuse v3 with the SDK pinned to v4

- Works, and v3 is what most existing tutorials describe.
- Pins the project to a superseded SDK and server line from the first day.

## Decision

Proposed:

1. **Self-host LangFuse v4 (option A)** as the default for development and for all benchmark runs.
2. **Pin the server image and the Python SDK together**, to exact versions, with the server at 4.59.0 or later. They are upgraded only as a pair.
3. **Provision the LangFuse project and API keys from environment variables** at first start, so that every developer's stack has the same keys in `.env` and no one has to click through the UI. LangFuse supports this through its headless initialisation variables.
4. **Keep the cloud as a fallback, not a parallel path.** The application only knows `LANGFUSE_HOST` and two keys. If a member's machine cannot run the stack, that member points those variables at a shared Core-plan project (option C). The benchmark is still run on a self-hosted instance so all reported numbers come from one setup.
5. **Options B and D are rejected**: B for the user and quota limits, D for starting on a superseded version line.
6. **Traces shown in the report are exported**, as screenshots or JSON, since links into a local instance do not work for readers.

## Consequences

- The compose stack grows by five services. The TDD §11.3 file already contains them.
- Whoever runs the benchmark needs a machine that can hold the full stack. This should be identified in week 1.
- A LangFuse upgrade is a deliberate, paired change of image tag and SDK version, not something a routine dependency update may do.
- Switching a single developer to the cloud is a three-variable change, so the decision is cheap to revisit.

## Before accepting

- [ ] Compare the service list and environment variables in TDD §11.3 with LangFuse's current official self-hosting compose file for v4. The TDD block was written from the v3 layout and has not been run.
- [ ] Start the stack on the least powerful laptop in the group and note memory use with all services up.
- [ ] Confirm the headless initialisation variable names in the current self-hosting documentation.
- [ ] Re-check the Hobby and Core limits on the pricing page.

## On acceptance

- Set the status to Accepted and record the pinned server and SDK versions here.
- Update TDD §11.3 with any differences found in the compose check, and add the initialisation variables.
- Add the fallback instructions to the development setup in `CONTRIBUTING.md`.
- Add a changelog entry.

## Sources

- [LangFuse versions and compatibility](https://langfuse.com/self-hosting/upgrade/versioning)
- [LangFuse SDK overview](https://langfuse.com/docs/observability/sdk/overview)
- [LangFuse OpenTelemetry integration](https://langfuse.com/integrations/native/opentelemetry)
- [LangFuse docs change stating the 4.59.0 minimum for Python SDK v5](https://github.com/langfuse/langfuse-docs/pull/4068)
- [LangFuse pricing](https://langfuse.com/pricing)
