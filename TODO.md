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
- [x] Run initial paired, fresh-session trials with and without the skill. Stopped
      at the user's request after 14 attempts (7 pairs) on 2026-10-23. Reviewed
      outcomes were 6/7 per arm; no demonstrated correctness advantage. Results
      and frozen submissions are in `evals/results/paired-2026-10-23/`.
- [ ] Complete broader repeated trials only when requested. The initial run is
      small and incomplete; rerating frozen submissions does not test an updated
      skill or establish a causal benefit.
- [ ] Expand coverage beyond the initial fixtures: workspaces, worker entry points,
      permissions that require a blocked migration, native addons, declaration output,
      native formatter/linter migration, real browser automation, and hosted-service
      migration.
- [x] Apply initial findings: test CI task aliases behaviorally, check BOM decoding,
      and add the observed decoding pitfall to the conditional reference. Existing
      lockfile-cleanup guidance already covers the control's leftover Deno lock.

Release-maintenance procedure: check the official stable release and notes,
verify relevant CLI commands and a tiny fixture outside a project, update only
applicable guidance, rerun evaluations, and synchronize reviewed changes to the
installed copy. Project/global-runtime upgrades and deployments are separate tasks.
