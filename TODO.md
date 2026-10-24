# Maintainer backlog

This file is for skill maintainers, **not an instruction to run during migration**.
The skill does not monitor releases or modify itself when a user loads it.

- [x] Add generic fixtures, independent acceptance tests, known-good controls,
      negative controls, and paired-comparison safeguards. These test the evaluator;
      paired agent trials remain outstanding below.

- [x] Verify stable native `bun fmt` and refresh capability guidance. Verified
      2026-10-23 with the official Bun 1.4.4 macOS ARM64 binary: read-only failure,
      formatting, idempotent success, and `--no-script` bypass of a `fmt` script.
- [ ] Verify a stable release with native `bun lint`; it is absent in the official
      Bun 1.4.4 binary. Keep lint capability checks separate from formatter support.
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
