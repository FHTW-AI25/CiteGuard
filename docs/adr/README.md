# Architecture Decision Records

An ADR records one decision between real alternatives: the situation, the options, what was chosen and what follows from it. The [TDD](../TDD.md) describes the design as it is; ADRs explain why it is that way.

## Index

| # | Decision | Status | Plan item |
| :--- | :--- | :--- | :--- |
| [0001](0001-llm-model-selection.md) | Which language and embedding models to use | Proposed | P-01 |
| [0002](0002-langfuse-deployment.md) | Self-hosted LangFuse or LangFuse Cloud | Proposed | P-02 |
| [0003](0003-pdf-parsing-libraries.md) | PDF parsing libraries and the PyMuPDF licence | Proposed | P-03 |

The other pre-week items in the [implementation plan](../IMPLEMENTATION_PLAN.md#before-week-1) are not architecture decisions and have no ADR: P-04 (obtaining keys), P-05 (track owners, recorded in the plan) and P-06 (the development chapter, recorded in the evaluation protocol when chosen).

## Status

| Status | Meaning |
| :--- | :--- |
| **Proposed** | Written with a recommendation. Not yet agreed, so nothing depends on it. |
| **Accepted** | Agreed by the group. The TDD and other documents are updated to match. |
| **Superseded** | Replaced by a later ADR, which is linked. The text is kept as history. |
| **Rejected** | Considered and not adopted. Kept so the question is not reopened without new information. |

## Process

1. Copy the template below to `NNNN-short-title.md`, using the next free number, with status **Proposed**.
2. Open a pull request. Decisions that affect more than one track need agreement from the owners of those tracks ([CONTRIBUTING.md](../../CONTRIBUTING.md)).
3. On agreement, set the status to **Accepted**, fill in the date and the deciders, and make the changes listed under "On acceptance" in the same pull request.
4. An accepted ADR is not edited afterwards, apart from its status. To change a decision, write a new ADR that supersedes it.

## Template

```markdown
# NNNN. Title

| | |
| :--- | :--- |
| **Status** | Proposed |
| **Date** | YYYY-MM-DD |
| **Deciders** | names |
| **Plan item** | task or decision ID, if any |

## Context

What situation forces a decision, and which constraints apply.

## Options

Each option with its advantages and drawbacks.

## Decision

What we do, stated as a rule someone could follow.

## Consequences

What becomes easier, what becomes harder, what we now have to maintain.

## Before accepting

Facts to check first, if any.

## On acceptance

Documents and code to update.
```
