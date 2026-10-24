#!/usr/bin/env python3
"""Independent behavioral acceptance tests. Executes only disposable eval copies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
CASES = ("cli", "files", "http", "tests", "browser")
MARKER = ".migration-eval.json"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
REQUEST = """Migrate this disposable Deno project to the supplied Bun executable.
Preserve observable behavior, existing dependency versions, strict checking,
test assertions/skips, protected assets, and operational entry points. Remove
Deno execution/configuration; do not hide it behind Bun scripts. Provide a real
`typecheck` script, and preserve run/serve/test/build tasks that exist. Generate
bun.lock. Document intentional behavior/security differences in MIGRATION.md.
Do not change global tools, deploy, monitor releases, or modify evaluation files
outside this project. Do not add a framework or weaken types to bypass failures.
Formatter/linter replacement and broad reformatting are out of scope for this
initial benchmark. You may use installed Bun capabilities and relevant docs.
"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def prepare(case, target):
    require(not target.exists(), f"Refusing to overwrite {target}")
    shutil.copytree(ROOT / "fixtures" / case, target)
    (target / MARKER).write_text(json.dumps({"case": case, "schema": 1}))


class Evaluation:
    def __init__(self, case, target, runtime, bun, deno):
        self.case, self.target, self.runtime = case, target.resolve(), runtime
        require(target.is_dir(), "Target must be a prepared disposable project")
        marker = json.loads((target / MARKER).read_text())
        require(marker == {"case": case, "schema": 1}, "Prepared-project marker mismatch")
        self.bun, self.deno = bun, deno
        self.checks = []
        self.dotenv_touched = False
        self.dotenv_before = (target / ".env").read_bytes() if (target / ".env").exists() else None
        self.temp = tempfile.TemporaryDirectory(prefix="acceptance-", dir=target)
        self.scratch = Path(self.temp.name)
        self.env = {k: v for k, v in os.environ.items() if k in (
            "PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "BUN_INSTALL_CACHE_DIR",
        )}
        self.env.update(NO_COLOR="1", CI="1", APP_MODE="evaluation")
        self.env.pop("EVAL_IMPLICIT_ENV", None)
        if runtime == "bun":
            # An accidental `deno` proxy fails even if Deno is installed elsewhere.
            shim = self.scratch / "bin"
            shim.mkdir()
            (shim / "deno").write_text("#!/bin/sh\necho forbidden-deno-fallback >&2\nexit 97\n")
            (shim / "deno").chmod(0o755)
            (shim / "bun").symlink_to(bun)
            self.env["PATH"] = str(shim) + os.pathsep + self.env.get("PATH", "")

    def run(self, args, timeout=60):
        return subprocess.run([str(a) for a in args], cwd=self.target, env=self.env,
                              capture_output=True, text=True, timeout=timeout)

    def command(self, task, *args):
        if self.runtime == "deno":
            return [self.deno, "task", "check" if task == "typecheck" else task, *args]
        return [self.bun, "run", task, *args]

    def task(self, task, *args):
        return self.run(self.command(task, *args))

    def success(self, result):
        require(result.returncode == 0, (result.stdout + result.stderr)[-2000:])
        return result

    def data(self, *args):
        result = self.success(self.task("run", *args))
        return json.loads(result.stdout.strip())

    def check(self, name, function):
        before = time.monotonic()
        try:
            function()
            record = {"name": name, "passed": True}
        except Exception as error:
            record = {"name": name, "passed": False,
                      "detail": f"{type(error).__name__}: {error}"[:2500]}
        record["seconds"] = round(time.monotonic() - before, 3)
        self.checks.append(record)

    def installation(self):
        require((self.target / "bun.lock").is_file(), "Missing generated bun.lock")
        self.success(self.run([self.bun, "install", "--frozen-lockfile"]))

    def no_fallbacks(self):
        pattern = re.compile(r"\bDeno\.|\bdeno\s+(run|task|test|check|fmt|lint)|denoland/setup-deno")
        hits = []
        for path in self.target.rglob("*"):
            if not path.is_file() or any(part in {"node_modules", ".git"} or part.startswith("acceptance-") for part in path.parts):
                continue
            if path.name in {"deno.json", "deno.jsonc", "deno.lock"}:
                hits.append(str(path.relative_to(self.target)))
            elif path.suffix in {".ts", ".tsx", ".json", ".sh", ".yml", ".yaml", ".toml"} or path.name == "Makefile":
                if pattern.search(path.read_text()):
                    hits.append(str(path.relative_to(self.target)))
        require(not hits, f"Deno runtime/config consumers remain: {hits}")

    def typecheck(self):
        self.success(self.task("typecheck"))

    def rejects_type_error(self, task="typecheck"):
        path = self.target / "src/evaluation-type-probe.ts"
        require(not path.exists(), "Reserved probe path already exists")
        path.write_text('export const evaluationNumber: number = "not a number";\n'
                        'export function implicitAnyProbe(value) { return value; }\n')
        try:
            result = self.task(task)
            text = result.stdout + result.stderr
            require(result.returncode != 0 and "TS2322" in text and "TS7006" in text,
                    "Type-check task did not reject assignment and implicit-any probes")
        finally:
            path.unlink()

    def migration_notes(self):
        path = self.target / "MIGRATION.md"
        require(path.is_file(), "Missing migration handoff")
        text = path.read_text().lower()
        require("permission" in text and "sandbox" in text,
                "Handoff must address permissions/sandbox differences (requires human review too)")

    def cli(self):
        self.dotenv_touched = True
        (self.target / ".env").write_text("EVAL_IMPLICIT_ENV=must-not-load\n")
        expected = {"message": "Hello Ada", "count": 2, "mode": "evaluation", "implicit": None}
        require(self.data(" Ada ", "2") == expected, "CLI args, alias, environment, or dotenv behavior changed")
        result = self.task("run", "Ada", "0")
        require(result.returncode == 2 and "positive integer" in result.stderr,
                "Invalid arguments must retain exit status 2 and stderr diagnostic")
        wrapper = self.success(self.run(["bash", "scripts/run.sh", " Ada ", "2"]))
        require(json.loads(wrapper.stdout) == expected, "Shell entry point differs")
        self.success(self.run(["make", "check"]))
        workflow = self.target / ".github/workflows/check.yml"
        require(workflow.exists(), "CI workflow was deleted rather than migrated")
        if self.runtime == "bun":
            text = workflow.read_text()
            # Inspect literal run steps; then test the invoked task, including aliases.
            tasks = re.findall(r"(?m)^\s*(?:-\s+run:\s*)?bun\s+run\s+([\w:-]+)\s*(?:#.*)?$", text)
            require("--frozen-lockfile" in text and tasks,
                    "CI must install frozen dependencies and run a checking task")
            for task in tasks:
                try:
                    self.rejects_type_error(task)
                    break
                except AssertionError:
                    continue
            else:
                raise AssertionError("No CI task rejected assignment and implicit-any probes")

    def files(self):
        directory = self.scratch / "data"
        directory.mkdir()
        path = directory / "result.txt"
        self.success(self.task("run", "new", path, "héllo 🎲 trailing content"))
        require(self.data("read", path) == "héllo 🎲 trailing content", "UTF-8 round-trip failed")
        require(self.task("run", "new", path, "overwrite").returncode != 0,
                "Exclusive creation overwrote an existing result")
        require(path.read_text() == "héllo 🎲 trailing content", "Failed creation damaged original file")
        self.success(self.task("run", "replace", path, "short"))
        require(path.read_text() == "short", "Replacement must truncate, not append")
        encoded = directory / "encoded.txt"
        encoded.write_bytes(b"\xef\xbb\xbfa\xff")
        require(self.data("read", encoded) == "\ufeffa\ufffd",
                "Text decoding must preserve the UTF-8 BOM and replace malformed bytes")
        encoded.unlink()
        (directory / "subdirectory").mkdir()
        require(self.data("list", directory) == ["result.txt"], "Directory entry types changed")
        require(self.data("missing", directory / "absent") == {"missing": True}, "Missing-file handling changed")
        require(self.task("run", "missing", directory).returncode != 0,
                "Non-missing I/O errors were swallowed")
        require(self.data("child") == {"code": 7, "stdout": "out" * 40000 + "\n", "stderr": "err" * 40000 + "\n"},
                "Child arguments, streams, or exit status changed")

    def http(self):
        root = self.scratch / "public"
        root.mkdir()
        (root / "data.bin").write_bytes(b"\x00payload\xff")
        sibling = self.scratch / "public-private"
        sibling.mkdir()
        (sibling / "secret.txt").write_text("outside-root")
        (root / "escape.txt").symlink_to(sibling / "secret.txt")
        child = subprocess.Popen([str(a) for a in self.command("serve", root)],
                                 cwd=self.target, env=self.env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            try:
                require(selector.select(timeout=15), "Server did not announce an ephemeral port")
                line = child.stdout.readline()
            finally:
                selector.close()
            require(line, "Server exited before announcing a port")
            port = json.loads(line)["port"]

            def request(path, data=None):
                try:
                    response = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", data=data, timeout=5)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()

            status, _, body = request("/health")
            require(status == 200 and json.loads(body) == {"ok": True}, "Health route changed")
            status, headers, body = request("/echo", "héllo 🎲".encode())
            require(status == 201 and body.decode() == "héllo 🎲" and
                    "text/plain" in headers.get("content-type", ""), "POST echo contract changed")
            require(request("/static/data.bin")[2] == b"\x00payload\xff", "Binary response changed")
            require(request("/static/absent")[0] == 404, "Missing-file HTTP status changed")
            require(request("/static/escape.txt")[0] == 403, "Symlink escaped the static root")
            require(request("/unknown")[0] == 404, "Unknown-route status changed")
        finally:
            # Kill only the process group this evaluator created, including task runners.
            import signal
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.communicate(timeout=5)

    def tests(self):
        result = self.success(self.task("test"))
        output = ANSI.sub("", result.stdout + result.stderr)
        pattern = r"4 passed.*1 ignored" if self.runtime == "deno" else r"[45] pass[\s\S]*1 skip[\s\S]*0 fail"
        require(re.search(pattern, output), "Unexpected pass/skip/fail counts: " + output[-1200:])
        path = self.target / "src/count.ts"
        before = path.read_bytes()
        try:
            prefix = 'export function parseCount(value: string): number { const result = Number(value); '
            guard = 'if (!/^\\d+$/.test(value) || result < 1) throw new RangeError("positive integer required"); '
            mutations = {
                "valid": prefix + guard + 'return value === "2" ? 99 : result; }\n',
                "invalid": prefix + 'return result; }\n',
                "async": prefix + guard + 'return value === "3" ? 99 : result; }\n',
                "nested": prefix + guard + 'return value === "4" ? 99 : result; }\n',
            }
            for name, mutation in mutations.items():
                path.write_text(mutation)
                result = self.task("test")
                output = ANSI.sub("", result.stdout + result.stderr)
                require(result.returncode != 0 and re.search(r"\b[1-9]\d* fail", output),
                        f"Tests did not report an assertion failure for the independent {name} mutation")
        finally:
            path.write_bytes(before)

    def browser(self):
        self.success(self.task("build"))
        bundle = self.target / "public/app.js"
        require(bundle.is_file(), "Expected browser artifact was not produced")
        engine = shutil.which("node") or self.bun
        code = """const fs=require('node:fs'),vm=require('node:vm');
const element={textContent:''};
const context={Bun:undefined,process:undefined,require:undefined,
document:{getElementById:id=>id==='app'?element:null}};
vm.runInNewContext(fs.readFileSync(EVAL_BUNDLE,'utf8'),context,{timeout:3000});
if(element.textContent!=='Hello Ada')throw Error('wrong browser result: '+element.textContent);
"""
        self.success(self.run([engine, "-e", code.replace("EVAL_BUNDLE", json.dumps(str(bundle)))]))
        for name in ("index.html", "legal.html"):
            before = (ROOT / "fixtures/browser/public" / name).read_bytes()
            require((self.target / "public" / name).read_bytes() == before,
                    f"Protected browser asset changed: {name}")
        if self.runtime == "bun":
            package = json.loads((self.target / "package.json").read_text())
            require(package.get("dependencies", {}).get("preact") == "10.29.0",
                    "Preact version changed during runtime migration")

    def evaluate(self):
        try:
            if self.runtime == "bun":
                self.check("frozen-install", self.installation)
                self.check("no-deno-fallbacks", self.no_fallbacks)
                self.check("security-handoff", self.migration_notes)
            self.check("typecheck", self.typecheck)
            self.check("typecheck-rejects-error", self.rejects_type_error)
            self.check(self.case + "-behavior", getattr(self, self.case))
            return {"case": self.case, "runtime": self.runtime,
                    "passed": all(c["passed"] for c in self.checks), "checks": self.checks}
        finally:
            if self.dotenv_touched:
                if self.dotenv_before is None:
                    (self.target / ".env").unlink(missing_ok=True)
                else:
                    (self.target / ".env").write_bytes(self.dotenv_before)
            self.temp.cleanup()


def reference(case, target, bun):
    """Hand-authored known-good control, not an agent run or migration engine."""
    prepare(case, target)
    (target / "deno.json").unlink()
    source = ROOT / "reference" / case
    if source.exists():
        for path in source.iterdir():
            shutil.copyfile(path, target / "src" / path.name)
    scripts = {"typecheck": "bun check"}
    if case in {"cli", "files"}:
        scripts["run"] = "bun src/main.ts"
    if case == "http":
        scripts["serve"] = "bun src/server.ts"
    if case == "tests":
        scripts["test"] = "bun test --check src/"
    if case == "browser":
        scripts["build"] = "bun build --check --target browser --format iife src/main.tsx --outfile public/app.js"
    package = {"private": True, "type": "module", "scripts": scripts,
               "devDependencies": {"@types/bun": "1.4.3"}}
    if case == "tests":
        package["devDependencies"]["@std/assert"] = "npm:@jsr/std__assert@1.0.19"
        (target / ".npmrc").write_text("@jsr:registry=https://npm.jsr.io\n")
    if case == "browser":
        package["dependencies"] = {"preact": "10.29.0"}
    (target / "package.json").write_text(json.dumps(package, indent=2) + "\n")
    options = {"target": "ESNext", "module": "Preserve", "moduleResolution": "bundler",
               "strict": True, "types": ["bun"], "allowImportingTsExtensions": True,
               "noEmit": True, "skipLibCheck": True,
               "paths": {"@lib/*": ["./src/lib/*"]}}
    if case == "browser":
        options.update(jsx="react-jsx", jsxImportSource="preact", lib=["DOM", "ESNext"])
    (target / "tsconfig.json").write_text(json.dumps({"compilerOptions": options, "include": ["src/**/*"]}, indent=2) + "\n")
    (target / "bunfig.toml").write_text("env = false\n")
    (target / "MIGRATION.md").write_text(
        "Bun runs with OS privileges. Deno permission flags no longer provide a sandbox.\n"
        "Implicit dotenv loading is disabled. Use OS isolation for untrusted code.\n"
    )
    if case == "cli":
        (target / "scripts/run.sh").write_text('#!/usr/bin/env bash\nset -euo pipefail\ncd "$(dirname "$0")/.."\nbun src/main.ts "$@"\n')
        (target / "Makefile").write_text(".PHONY: check\ncheck:\n\tbun run typecheck\n")
        (target / ".github/workflows/check.yml").write_text(
            "name: Check\non: [push, pull_request]\njobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - uses: actions/checkout@v4\n      - uses: oven-sh/setup-bun@v2\n"
            '        with:\n          bun-version: "1.4.3"\n'
            "      - run: bun install --frozen-lockfile\n      - run: bun run typecheck\n"
        )
    result = subprocess.run([bun, "install"], cwd=target, capture_output=True, text=True, timeout=90)
    require(result.returncode == 0, result.stderr)


def evaluate_copy(case, target, runtime, bun, deno):
    """Freeze acceptance input into a clean copy, excluding warm dependencies."""
    marker = json.loads((target / MARKER).read_text())
    require(marker == {"case": case, "schema": 1}, "Prepared-project marker mismatch")
    with tempfile.TemporaryDirectory(prefix="migration-grade-", dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
        fresh = Path(directory) / "candidate"
        shutil.copytree(target, fresh, symlinks=True,
                        ignore=shutil.ignore_patterns("node_modules", ".git", "acceptance-*"))
        result = Evaluation(case, fresh, runtime, bun, deno).evaluate()
    digest = hashlib.sha256(Path(__file__).read_bytes())
    for path in sorted((ROOT / "fixtures").rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(ROOT)).encode())
            digest.update(path.read_bytes())
    result["evaluator_sha256"] = digest.hexdigest()
    result["fresh_dependency_tree"] = True
    return result


def selftest(work, bun, deno):
    results = []
    controls = []
    for case in CASES:
        baseline = work / (case + "-baseline")
        prepare(case, baseline)
        results.append(evaluate_copy(case, baseline, "deno", bun, deno))
        good = work / (case + "-reference")
        reference(case, good, bun)
        results.append(evaluate_copy(case, good, "bun", bun, deno))

    def negative(label, case, mutate):
        path = work / ("negative-" + label)
        shutil.copytree(work / (case + "-reference"), path)
        mutate(path)
        result = evaluate_copy(case, path, "bun", bun, deno)
        controls.append({"name": label, "rejected": not result["passed"],
                         "failed_checks": [c["name"] for c in result["checks"] if not c["passed"]]})

    def replace(path, old, new):
        text = path.read_text()
        require(old in text, f"Mutation anchor not found: {old}")
        path.write_text(text.replace(old, new))

    def ci_alias(path, command):
        package = path / "package.json"
        config = json.loads(package.read_text())
        config["scripts"]["typecheck"] = "bun check --no-script"
        config["scripts"]["check"] = command
        package.write_text(json.dumps(config, indent=2) + "\n")
        replace(path / ".github/workflows/check.yml", "bun run typecheck", "bun run check")

    alias = work / "positive-ci-alias"
    shutil.copytree(work / "cli-reference", alias)
    ci_alias(alias, "bun run typecheck")
    results.append(evaluate_copy("cli", alias, "bun", bun, deno))
    negative("fake-ci-alias", "cli", lambda p: ci_alias(p, "echo success"))
    require(controls[-1]["failed_checks"] == ["cli-behavior"],
            "Fake CI alias must fail CI checking without breaking the real typecheck task")
    negative("silent-typecheck", "cli", lambda p: replace(p / "package.json", '"typecheck": "bun check"', '"typecheck": "echo success"'))
    negative("weakened-types", "cli", lambda p: replace(p / "tsconfig.json", '"strict": true', '"strict": false'))
    negative("shell-fallback", "cli", lambda p: replace(p / "scripts/run.sh", "bun src/main.ts", "deno run --allow-env src/main.ts"))
    negative("implicit-dotenv", "cli", lambda p: (p / "bunfig.toml").write_text("env = true\n"))
    negative("overwrite-results", "files", lambda p: replace(p / "src/main.ts", 'flag: "wx"', 'flag: "w"'))
    negative("dirent-property", "files", lambda p: replace(p / "src/main.ts", "entry.isFile()", "entry.isFile"))
    negative("stripped-utf8-bom", "files", lambda p: replace(p / "src/main.ts", 'await readFile(path, "utf8")', 'new TextDecoder().decode(await readFile(path))'))
    negative("static-prefix-escape", "http", lambda p: replace(p / "src/server.ts", 'file.startsWith(root + "/")', "file.startsWith(root)"))
    negative("lost-test-assertions", "tests", lambda p: (p / "src/count_test.ts").write_text(
        'import {test} from "bun:test";for(let i=0;i<4;i++)test("empty"+i,()=>{});test.skip("expensive",()=>{});\n'))
    negative("lost-nested-assertion", "tests", lambda p: replace(p / "src/count_test.ts", 'assertEquals(parseCount("4"), 4);', '// assertion accidentally dropped'))
    negative("protected-asset", "browser", lambda p: (p / "public/legal.html").write_text("rewritten\n"))
    passed = all(r["passed"] for r in results) and all(c["rejected"] for c in controls)
    return {"kind": "evaluator-selftest-not-agent-comparison", "passed": passed,
            "runs": results, "negative_controls": controls}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bun", default=shutil.which("bun"))
    parser.add_argument("--deno", default=shutil.which("deno"))
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("prepare")
    create.add_argument("case", choices=CASES)
    create.add_argument("target", type=Path)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("case", choices=CASES)
    evaluate.add_argument("target", type=Path)
    evaluate.add_argument("--runtime", choices=("bun", "deno"), default="bun")
    evaluate.add_argument("--report", type=Path)
    test = commands.add_parser("selftest")
    test.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.case, args.target)
        print(REQUEST + f"\nProject: {args.target.resolve()}\nBun executable: {args.bun}\n")
        return
    require(args.bun and args.deno, "Both runtimes must be supplied for reproducible evaluation")
    if args.command == "selftest":
        with tempfile.TemporaryDirectory(prefix="deno-bun-evals-", dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            report = selftest(Path(directory), args.bun, args.deno)
    else:
        report = evaluate_copy(args.case, args.target, args.runtime, args.bun, args.deno)
    report["versions"] = {
        "bun": subprocess.check_output([args.bun, "--version"], text=True).strip(),
        "deno": subprocess.check_output([args.deno, "--version"], text=True).strip(),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
