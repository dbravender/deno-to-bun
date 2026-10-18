# Initial evaluator validation

Date: 2026-10-18. Bun 1.4.3; Deno 2.9.7. No agent trials are represented here.

- **5/5 original fixtures** passed under Deno.
- **5/5 hand-authored reference migrations** passed under Bun, using clean
  dependency trees and frozen lockfiles.
- **10/10 deliberately broken migrations** were rejected: fake checking,
  weakened strictness, a shell fallback, implicit dotenv, overwritten exclusive
  output, a Dirent mistake, a symlink escape, empty tests, a missing nested
  assertion, and altered protected HTML.
- **9/9 harness unit tests** passed, including guards against comparing different
  runtimes/graders/models, unpaired attempts, and counting self-tests as agent work.

The raw self-test report is `results/selftest.json`. It identifies the grader and
fixture hash; changing either requires rerunning validation. Reproduce with the
commands in `README.md` using recorded runtime versions.

The first evaluator run caught defects in the fixtures/grader itself: test
callbacks returning assertion objects, case-sensitive HTTP header comparison,
and an assumed Node installation. Those were fixed rather than interpreted as
migration failures. Additional checks now exercise strictness, individual nested
assertions, large subprocess streams, and isolated installs.

**Conclusion:** the acceptance harness works for these known examples. No claim
is made yet that the revised skill improves an agent's migration success rate.
The next experiment is the fresh-session paired protocol, with independent diff
review and at least three repeats per fixture. Real-browser automation and hosted
service/CI validation remain outside this initial suite.
