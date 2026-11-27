<!-- Title: task ID and a subject in commit style, for example "W2-04: add hybrid chunk search" -->

Closes #

## What changed

<!-- A few sentences. Explain why, if the diff does not make it obvious. -->

## How it was tested

<!-- Commands you ran, or what you checked by hand. -->

## For the reviewer

<!-- Anything to look at closely, known gaps, follow-up issues. Delete if empty. -->

## Checklist

- [ ] The task's "done when" condition is met.
- [ ] Tests cover the new behaviour and pass locally.
- [ ] Lint and format checks pass.
- [ ] `CHANGELOG.md` has a line under `Unreleased`, if the change is noticeable.
- [ ] The TDD is updated if the implementation deliberately differs from it.
- [ ] New environment variables are in `.env.example` and in the README table.

<!--
Changes to a shared contract, an existing database column, RabbitMQ names or the
frozen benchmark need agreement from all affected tracks before merging.
See CONTRIBUTING.md, "Changes that need more than one reviewer".
-->
