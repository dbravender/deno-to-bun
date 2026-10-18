# Maintainer backlog

This file is for skill maintainers, **not an instruction to run during migration**.
The skill does not monitor releases or modify itself when a user loads it.

- [x] Add generic fixtures, independent acceptance tests, known-good controls,
      negative controls, and paired-comparison safeguards. These test the evaluator;
      paired agent trials remain outstanding below.

- [ ] Verify a stable Bun release with native `bun fmt` and `bun lint`, then
      refresh historical capability notes. Last checked 2026-10-18: stable 1.4.3;
      native fmt/lint verified separately in 1.4.4-canary.1. Do not assume a future
      version number or release date. Verify an isolated official binary, not just
      live documentation, before changing guidance.
- [ ] Run paired, fresh-session migration trials with and without the skill,
      using the same model, request, tools, runtime versions, and budget. Record
      repeated outcomes; evaluator self-tests are not evidence that the skill helps.
- [ ] Expand coverage beyond the initial fixtures: workspaces, worker entry points,
      permissions that require a blocked migration, native addons, declaration output,
      native formatter/linter migration, real browser automation, and hosted-service
      migration.
- [ ] Use actual evaluation failures to decide which instructions to add/remove.
      Keep the core short; put conditional API detail in references.

Release-maintenance procedure: check the official stable release and notes,
verify relevant CLI commands and a tiny fixture outside a project, update only
applicable guidance, rerun evaluations, and synchronize reviewed changes to the
installed copy. Project/global-runtime upgrades and deployments are separate tasks.
