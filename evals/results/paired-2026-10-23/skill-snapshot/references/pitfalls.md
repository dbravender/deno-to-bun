# Migration pitfalls: read only the sections relevant to the project

## Commands and configuration

- Inspect actual CLI help and distinguish stable, canary, live docs, and merged
  source. Verify capabilities rather than inferring them from a version number.
- Native-looking package scripts (`check`, `fmt`, `lint`) can shadow Bun commands.
  Prefer unambiguous script names such as `typecheck`, `format:check`, and
  `lint:check`. Never hide a retained Deno command behind a native-looking alias.
- Stable Bun 1.4.4 ships native `bun fmt`, including `--no-script` and `--check`.
  Verified against the official macOS ARM64 binary on 2026-10-23: a read-only check
  exits 1 for unformatted code, formatting then checking exits 0, and `--no-script`
  bypasses a project's `fmt` script. Native `bun lint` is absent in that release;
  do not require canary merely to replace a working lint gate.
- Preserve compiler strictness and environments. Bun CLI checking need not install
  a separate TypeScript compiler; runtime declarations may need `@types/bun` and
  explicit `types`. Declaration emission and editor language services are separate.
- Entry-point `--check` may miss workers, computed imports, and subprocess entry
  points. Whole-project checking must include all relevant source roots.
- Disable implicit dotenv loading when preserving explicit loading, for example
  verified `env = false` in `bunfig.toml`. An inner flag cannot undo environment
  variables already loaded by an outer script runner. Test with a harmless fixture.

## Imports and dependencies

- Import-map aliases/scopes are not automatically portable to every consumer.
  Verify execution, type-checking, bundling, and package exports where applicable.
- Do not collapse multiple versions into one silently. Compare actual resolved
  versions, not lockfile peer-context suffixes. Document any compatibility pins.
- Portable JSR packages can use the official npm compatibility registry. Example:
  `"@std/assert": "npm:@jsr/std__assert@<existing-version>"` and `.npmrc` containing
  `@jsr:registry=https://npm.jsr.io`. Verify current support and preserve unrelated
  registry settings without copying credentials.
- URL/JSR dependencies may themselves use Deno APIs. A new import spelling is not
  proof of portability. Do not substitute a similarly named npm package.
- Keep install-script trust explicit. A fresh install can reveal required generated
  files that a warm dependency tree hides.

## Files, processes, and servers

- Preserve UTF-8 decoding, truncation/append behavior, exclusive creation (`wx`),
  atomic rename, and awaited file-handle closure. `Bun.write` is not a universal
  substitute for option-bearing Deno writes.
- Node Dirent has `isFile()`; Deno directory entries have boolean properties.
  Recognize `ENOENT` without swallowing permission or other I/O errors.
- Preserve subprocess arguments, stdin, stdout/stderr, exit codes, cancellation,
  signals, and deadlines. Drain both output pipes concurrently. Use the intended
  executable and convert file URLs to paths where required by the target CLI.
- Keep shebangs first when inserting imports. Review codemod output around
  comments, template strings, object-form registrations, and option-bearing calls.
- Check static-file realpath containment with separator boundaries and symlink
  escape requests—not only successful requests.
- Custom Bun installers must provide required aliases such as `bunx`, not just the
  `bun` executable. Test the real CI/deployment consumer before claiming parity.

## Tests

- Deno object registrations need deliberate conversion. `ignore` can map to
  `test.skipIf(condition)(name, fn)`; passing the original object is not equivalent.
- Runner arguments differ. Prefer explicit opt-ins instead of translating
  `Deno.args`-based test skips to `process.argv` mechanically.
- Preserve nested-case assertions, resource/permission guarantees, mocks, teardown,
  and timeout behavior. Unsupported guarantees need disclosure or a replacement.
- Deno parallel files are not Bun concurrent tests. Global RNG or browser-global
  mutation and shared module state can make concurrency unsafe. Do not promise a
  speedup; compare pass/skip/fail counts and representative execution time.

## Format, lint, and operations

- Prefer stable Bun 1.4.4 or newer for native formatting. Use
  `bun fmt --no-script --check` for the initial read-only check and CI, and
  `bun fmt --no-script` to format after approval. Carry over Deno format options
  and exclusions into `[fmt]` in `bunfig.toml`; existing Prettier/oxfmt configs
  are also supported. Deno ignore comments need translation to `prettier-ignore`.
- Match exclusions before writing: generated assets, verbatim licensed material,
  hidden settings, and historical documents may need protection. Matching common
  style options does not make different formatter algorithms identical.
- Once approved, run the new formatter automatically, require an idempotent check,
  and replace the old gate. Hash protected files to prove they were untouched.
- Translate suppression directives and decide warning thresholds; a successful
  lint exit with warnings is not necessarily equivalent to the old gate.
- Preserve pinned CI dependencies, build output filenames/formats, assets, service
  workers, production-branch restrictions, and rollback paths. Hosted Deno services
  are separate migrations; do not silently replace them with Bun processes.

Official references: https://bun.com/docs, https://docs.deno.com/runtime/, and
https://jsr.io/docs/using-packages. Consult only relevant sections when needed.
Stable formatter release: https://bun.com/blog/bun-v1.4.4; configuration and CLI:
https://bun.com/docs/format.
