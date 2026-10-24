# Migration evaluations

These are maintainer tools, not instructions for a migration agent. Keep the
acceptance tests and reference solutions outside the candidate agent's workspace.
No real application, production data, deployment, or project-specific case study
is used.

## What is measured

| Fixture   | Independent acceptance checks                                                                                                                                        |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cli`     | Import alias, positional args, invalid-arg exit code/stderr, explicit environment, no implicit dotenv, shell launcher, Makefile, CI wiring                           |
| `files`   | UTF-8, exclusive writes, truncation, directory entry types, missing versus other I/O errors, child output/error/status                                               |
| `http`    | Ephemeral localhost server, health, Unicode POST/status/content type, binary body, missing routes/files, sibling-prefix symlink escape                               |
| `tests`   | JSR assertions, four passing/one skipped original parent tests, async/deep-equality/nested assertions, independent mutations for valid/invalid/async/nested behavior |
| `browser` | Pinned npm dependency, JSX and import alias, browser artifact path, VM execution without Bun/Node globals, byte-identical protected HTML                             |

Every candidate also needs a generated frozen lockfile, real strict checking that
rejects an injected type error, removal of Deno runtime/config consumers, and a
security handoff. Executable proxies fail because the evaluator puts a rejecting
`deno` shim first on PATH.

The handoff keyword check and CI inspection are preliminary checks, **not proof**
of adequate security analysis or hosted CI correctness. A reviewer must judge the
handoff, type settings, scope of changes, dependency choices, and operational
safeguards independently.

## Prerequisites

- Python 3.11+, Deno, Bun with native checking, Bash, and Make. The bundle smoke
  test uses Node if installed, otherwise Bun's `node:vm` implementation.
- Linux/POSIX: the HTTP test owns and terminates a process group and uses symlinks.
- Registry access for the original JSR/npm packages and Bun type declarations.
- Run on disposable copies. This executes candidate code; it is **not a security
  sandbox**. Use an appropriate container/VM for untrusted agents or third-party code.

Use `--bun /absolute/path/to/bun --deno /absolute/path/to/deno` before the
subcommand to select exact runtimes. No global runtime is installed or upgraded.
The harness does not need native fmt/lint; formatter/linter migrations are outside
this initial benchmark and remain an explicit coverage gap.

## First: test the evaluator

```sh
python3 -B -m unittest discover -s evals -p test_harness.py -v
python3 evals/run.py selftest --report /tmp/opencode/migration-selftest.json
```

This runs each original fixture on Deno and each hand-authored reference migration
on Bun. It then introduces broken migrations: a fake type-check command, weakened
strictness, a Deno shell fallback, implicit dotenv, overwriting exclusive outputs,
a Dirent property mistake, a static-root prefix escape, empty tests with plausible
counts, a lost nested assertion, and a changed protected asset. Each must be rejected.

A passing self-test shows that the evaluator accepts known-good examples and
rejects these known failures. **It does not measure the migration skill's effect.**
Reference implementations are not agent attempts and are never counted as such.

The self-test also accepts a CI `check` alias that invokes real typechecking and
rejects a CI alias that only prints success. Workflow inspection supports literal
`bun run <task>` steps and probes the invoked task with type errors; it does not
execute GitHub Actions. File behavior includes BOM preservation and malformed
UTF-8 replacement, with a negative control for accidental BOM stripping.

## Then: paired agent trials

1. Choose one model/version, target Bun version, tools/permissions, time/token
   budget, and user request. Record them and a hash of the request. Use fresh
   sessions and independent pristine copies. Start with all five fixtures and at
   least three repeats per fixture (30 attempts total); increase repetitions
   before drawing strong conclusions.
2. Prepare a project for each attempt:

   ```sh
   python3 evals/run.py prepare cli /tmp/opencode/cli-control-01
   python3 evals/run.py prepare cli /tmp/opencode/cli-skill-01
   ```

   The printed request is the same in both arms. Give one session that request
   without the skill; give the paired session the same request plus `SKILL.md`
   and its conditional `references/pitfalls.md`. Do not give either session this
   directory, reference solutions, self-test reports, or acceptance-test source.

3. Counterbalance which arm runs first. Prevent session memory or fixes from one
   attempt leaking into another. Do not reuse this author's context as a control.
   Keep registry availability/caches comparable and record infrastructure failures
   separately rather than silently changing one arm's runtime.
4. Freeze the agent's output before repairs. Run independent acceptance tests:

   ```sh
   python3 evals/run.py evaluate cli /tmp/opencode/cli-skill-01 \
     --report /tmp/opencode/cli-skill-01.report.json
   ```

   The grader creates a clean disposable snapshot without `node_modules`, injects
   probes and mutates a source function there, and removes the snapshot afterward.
   It leaves the submitted candidate unchanged and refuses targets without a
   prepared-project marker. Do not point it at a real working project. Reports
   belong outside the candidate tree. Reports include the grader/fixture hash;
   paired comparison rejects reports produced by different graders.

5. Review diffs without relying on the agent's self-report. Record whether it
   preserved user work, avoided global installs/deploys, retained strictness and
   tests, handled permission changes, avoided unrequested dependencies/reformatting,
   and gave an honest handoff. Record elapsed time, cost/tokens if available, and
   required manual repairs separately. A baseline error or registry outage is not
   automatically a migration failure.
6. Compare paired automated acceptance and reviewed acceptance, per fixture and
   overall. Also compare time/cost and manual repairs. Report sample sizes and
   ties, not just a headline percentage. Do not claim improvement from a single
   successful migration or from evaluator self-tests.

An optional `compare.py` tool reads a trial manifest and independent reports;
see its example schema in `trial-manifest.example.json`.

## How findings should change the skill

Keep a rule when repeated failures show it prevents a real error. Shorten or
remove advice that adds work without improving outcomes. Add a fixture/regression
check before adding another long paragraph about a one-off problem.

Do not weaken acceptance tests to make the skill look better. Changes to the
grader or fixtures require rerunning both arms. This is an initial public suite,
not an adversarial hidden benchmark; hold-out fixtures are needed to assess
generalization and discourage overfitting.

## Limits

The browser test executes a bundle with a minimal DOM stub; it is **not actual
browser automation**. Hosted CI, real services, permission-boundary equivalence,
concurrent race behavior, workspaces, native addons, declaration output, and
deployment correctness are not established by this suite. Its keyword/static
checks can be gamed and require independent review. See the maintainer backlog
for the remaining coverage work.
