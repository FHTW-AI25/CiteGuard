# 0001. Language and embedding model selection

| | |
| :--- | :--- |
| **Status** | Proposed |
| **Date** | 2026-11-27 |
| **Deciders** | _the four group members, on acceptance_ |
| **Plan item** | P-01 |

## Context

TDD §3.2 assigns `gemini-2.5-flash` to `claim_extractor` and `evidence_retriever`, and `gemini-2.5-pro` to `faithfulness_judge` and `revision_patcher`. TDD §6.3 names `gemini-embedding-001` at 768 dimensions for all vectors.

Whether the two Gemini 2.5 models can be relied on for this project is unclear. A check on 2026-11-27 found contradictory information:

- Some copies of Google's deprecations page list both models with a shutdown date of 16 October 2026, which is already past, and name `gemini-3.5-flash` and `gemini-3.1-pro-preview` as replacements.
- Other copies of the same page show "no shutdown date announced" for both.
- Developer forum posts report "no longer available" errors for these models on newly created projects.

This cannot be settled from documentation. It depends on what the group's own API key can call.

Constraints from the rest of the design:

- **Reproducibility.** The evaluation protocol compares runs across profiles and repetitions. A model that changes behind an alias during week 4 invalidates the comparison.
- **Features.** The judge needs constrained decoding with a JSON schema. The extractor, retriever and patcher need function calling for MCP tools. Google ADK must support the model.
- **Two cost tiers.** High-volume extraction and retrieval run on a cheap model; the judge and patcher run on a stronger one.
- **Embeddings are expensive to change.** All `vector(768)` columns and the LightRAG index depend on one embedding model. Changing it means re-embedding the corpus.

## Options

### A. Keep Gemini 2.5 as written in the TDD

- No document changes.
- May not be callable from a new key, and may be retired during the project.
- Results would be reported on a model generation that readers can no longer run.

### B. Use the current Gemini generation

- Available and supported for the project period.
- The strong-tier replacement may only exist as a preview model. Preview models can change or be withdrawn without the notice period that stable models get.
- Prices and rate limits differ from the TDD's assumptions and need a fresh cost estimate.

### C. Make the provider pluggable (for example through ADK's LiteLLM adapter)

- Removes the dependency on one vendor.
- Constrained decoding and tool calling behave differently across providers, which would add an uncontrolled variable to every ablation.
- More work than a four-week project can absorb.

## Decision

Proposed:

1. **Code refers to tiers, not model names.** Model identifiers are configuration: `MODEL_FAST`, `MODEL_STRONG` and `MODEL_EMBEDDING`. No model name appears in agent code.
2. **Identifiers are pinned to exact versions.** No `latest` aliases and no unversioned names.
3. **Use the current generation (option B)**, choosing for each tier the newest model that is generally available to the group's key and passes the checks below. Gemini 2.5 is used only if those checks show it is callable and it has no announced shutdown date within the project period plus four weeks.
4. **Prefer a stable model for the judge.** If the only strong-tier model that passes is a preview, use it, and record that as a threat to validity in the evaluation report.
5. **Embeddings stay on `gemini-embedding-001` with `output_dimensionality=768`**, as in the TDD. It is confirmed to support 768 dimensions.
6. **Models are frozen when the benchmark is frozen** (task W2-14). The identifiers are written into every results file. Changing a model after that point means re-running every reported number.
7. **Option C is rejected** for this project.

## Consequences

- Swapping a model is a configuration change, which also makes the fallback cheap if a model is withdrawn mid-project.
- The TDD's agent table, the README and `AGENTS.md` name specific models and must be updated when the identifiers are chosen.
- Cost estimates in the implementation plan's risk table must be redone with current prices.
- If a model is retired between the benchmark runs and the report, the results stand but cannot be reproduced by readers. The report states the run dates.

## Before accepting

Run these with the group's API key and attach the output to the pull request:

- [ ] List the models the key can call and note which are stable and which are preview.
- [ ] Read the live deprecations page and record any shutdown date for each candidate.
- [ ] For the fast-tier candidate: one function-calling round trip through ADK with an MCP tool.
- [ ] For the strong-tier candidate: one response constrained to `ClaimVerificationVerdict`, checking that field limits such as `max_length` and the enum are honoured.
- [ ] One embedding call for `gemini-embedding-001` returning 768 dimensions.
- [ ] Estimate the cost of one 180-claim benchmark run at current prices, and check the key's rate limits against the planned concurrency.

## On acceptance

- Fill in the chosen identifiers here and set the status to Accepted.
- Update TDD §3.2 (model tier column) and §6.3, the agent table in the README, and the Models section of `AGENTS.md`.
- Add `MODEL_FAST`, `MODEL_STRONG` and `MODEL_EMBEDDING` to `.env.example` and the README variable table.
- Add a changelog entry.

## Sources

- [Gemini API deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
- [Forum: deprecation date for gemini-2.5-pro, conflicting information](https://discuss.ai.google.dev/t/deprecation-shutdown-date-for-gemini-2-5-pro-conflicting-information/183251)
- [Forum: gemini-2.5-pro "no longer available to new users"](https://discuss.ai.google.dev/t/gemini-2-5-pro-returns-no-longer-available-to-new-users-contradicts-official-deprecation-date-oct-16-2026/176380)
- [Vertex AI: get text embeddings](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings)
