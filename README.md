# Deno to Bun migration skill

Reusable instructions for migrating an existing project while preserving behavior.
The entry point is [`SKILL.md`](SKILL.md); conditional API details are in
[`references/pitfalls.md`](references/pitfalls.md). Maintenance is separate in
[`TODO.md`](TODO.md)—users do not need to run a release-maintenance workflow.

## Install and use

Copy `SKILL.md` and `references/` to your agent's supported skill location, for
example `.opencode/skills/deno-to-bun/`, then ask:

> Use @deno-to-bun to migrate this project to Bun. Preserve behavior, remove the
> agreed Deno dependencies, and flag security or deployment blockers first.

Do not install `evals/` or `TODO.md` as skill instructions. Evaluations,
reference solutions, and the backlog are maintainer tooling, not content to give
a migration agent.

## Evaluate it

[`evals/README.md`](evals/README.md) describes generic projects, independent
acceptance tests, negative controls, and the paired comparison protocol.

An evaluator self-test demonstrates that fixtures work and broken migrations are
rejected. It does **not** establish that an agent performs better with this skill.
That requires fresh-session, with/without-skill trials and repeated measurements.
