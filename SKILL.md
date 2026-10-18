---
name: deno-to-bun
description: Migrate an existing Deno project to Bun while preserving application behavior, tests, dependencies, and operational safeguards. Use for Deno tasks, APIs, imports, tests, browser builds, and CI—not for maintaining this skill or monitoring Bun releases.
---

# Deno to Bun

Success means the application still works under Bun and the agreed Deno
dependencies are gone—not merely that a script starts or a bundle builds.

## 1. Establish scope and a baseline

- Read repository instructions and inspect the working tree. Preserve user work.
- Determine what the user wants migrated: runtime only, full toolchain, or
  temporary dual-runtime support. Do not silently retain Deno behind Bun scripts.
- Record installed runtime versions. Probe required commands outside the project
  so package scripts cannot impersonate native commands. Prefer a stable release
  that supports the requirements. Ask before requiring canary or changing global
  installations; do not turn the migration into a release-monitoring task.
- Inventory configuration, imports, Deno APIs, tests, scripts **including `.sh`**,
  worker entry points, hooks, CI, deployment, and active documentation.
- Run safe existing checks before editing. Record test counts, skipped tests,
  build outputs, and pre-existing failures. Do not run deployments or expensive,
  destructive experiments just because a task exists.

Give a short plan. Ask about actual blockers or material behavior/security
tradeoffs, not every routine equivalent edit. If a Deno-specific framework,
hosted service, or essential permission boundary has no agreed replacement,
identify that blocker rather than faking compatibility.

## 2. Migrate deliberately

- Merge into existing `package.json`/`tsconfig.json`; do not overwrite them with
  scaffolding. Preserve strictness, JSX, workspace layout, script arguments,
  working directories, and build targets.
- Move imports/dependencies using the existing resolved versions first. Review
  transitive drift separately. Generate `bun.lock` with Bun; do not hand-write it.
  Prefer supported JSR distributions over replacing assertion semantics.
- Preserve Web APIs where supported. Port Deno APIs to appropriate Web, Node, or
  Bun APIs, checking behavior rather than just renaming symbols. Read the relevant
  sections of `references/pitfalls.md` for the APIs/tooling present in the project.
- Make type-checking explicit. Bun execution alone does not check types. Use
  verified native checking when available; cover scripts, workers, and dynamically
  loaded entry points as well as the app. Never weaken types to make checks pass.
- Port test registration without losing assertions, discovery, skips, async
  completion, nested cases, timeouts, or isolation. Compare counts with baseline.
- Preserve production output paths, browser targets, assets, entry references,
  deployment protections, and install-script trust decisions. A static browser
  project does not need a new server or framework.
- Port or explicitly disclose remaining format/lint tools. First match exclusion
  scopes and inspect a read-only check. If style churn is approved, format
  automatically and replace the old gate; do not leave competing formatters.
- Update shell launchers, hooks, CI, and docs. If removing Deno completely, remove
  obsolete config/locks/proxies once no consumer needs them. Do not relabel old
  benchmark results as measurements of the new runtime.

**Security:** Bun does not automatically reproduce Deno's permission sandbox.
Explain lost restrictions and obtain agreement on essential replacements. Check
dotenv loading and subprocess environments. Never print secrets, broadly enable
permissions/lifecycle scripts, deploy, or change global tools to bypass a failure.

## 3. Prove the migration

Use checks independent of the edits wherever possible:

1. Install from the generated frozen lockfile, preferably in a fresh disposable
   copy without warm project dependencies.
2. Run whole-project type-checking, tests, the real build, and agreed lint/format
   gates. A successful run with zero discovered tests is not a pass.
3. Exercise observable behavior: CLI arguments and exit status, filesystem
   semantics, HTTP routes, browser behavior, or other relevant interfaces.
4. Add regression tests for nontrivial adapters. Check protected assets remain
   unchanged and formatting is idempotent when a reformat was approved.
5. Search executable/configuration consumers again. For full removal, run gates
   with Deno unavailable on PATH so hidden fallbacks cannot succeed.

Do not edit tests or remove checks merely to obtain green results. A bundle or
HTTP 200 does not prove browser gameplay, hosted services, or production saving.
Keep local, browser, hosted-CI, and deployment verification separate.

## 4. Handoff

Report the changed toolchain/version requirement, commands, checks actually run,
remaining dependencies/blockers, security changes, and what remains unverified.
Distinguish preserved behavior from intentional changes. Keep work on the requested
branch; respect the user's commit and deployment instructions. Never deploy as an
automatic consequence of migration.

Maintainer tasks and evaluation machinery are not part of this workflow.
