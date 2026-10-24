# Deno to Bun migration skill

In his October 9, 2026 post, [Deno is joining Cloudflare](https://deno.com/blog/cloudflare),
Ryan Dahl announced one more year of runtime bug fixes and security updates before
the team's development of Deno ends. That prompted me to migrate my projects to
Bun and create this skill.

Reusable instructions for migrating an existing project while preserving behavior.
The entry point is [`SKILL.md`](skills/deno-to-bun/SKILL.md); conditional API details are in
[`references/pitfalls.md`](skills/deno-to-bun/references/pitfalls.md). Maintenance is separate in
[`TODO.md`](TODO.md)—users do not need to run a release-maintenance workflow.

## Install and use

Install directly from GitHub with the [Skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add dbravender/deno-to-bun --skill deno-to-bun
```

Or use Bun:

```sh
bunx --bun skills add dbravender/deno-to-bun --skill deno-to-bun
```

The installer lets you choose agents and installation scope. For an explicit
global installation, choose your agent:

```sh
npx skills add dbravender/deno-to-bun --skill deno-to-bun --agent codex --global
npx skills add dbravender/deno-to-bun --skill deno-to-bun --agent claude-code --global
npx skills add dbravender/deno-to-bun --skill deno-to-bun --agent opencode --global
```

In Codex, you can also ask its built-in installer:

> Use $skill-installer to install https://github.com/dbravender/deno-to-bun/tree/main/skills/deno-to-bun.

Then ask your agent (in Codex, invoke `$deno-to-bun`):

> Use the deno-to-bun skill to migrate this project to Bun. Preserve behavior, remove the
> agreed Deno dependencies, and flag security or deployment blockers first.

For manual installation, copy only `skills/deno-to-bun/` into your agent's skill
directory. The installable folder contains the skill and its reference; `evals/`,
historical skill snapshots, and `TODO.md` remain outside it.

## Evaluate it

[`evals/README.md`](evals/README.md) describes generic projects, independent
acceptance tests, negative controls, and the paired comparison protocol.

An evaluator self-test demonstrates that fixtures work and broken migrations are
rejected. It does **not** establish that an agent performs better with this skill.
That requires fresh-session, with/without-skill trials and repeated measurements.
