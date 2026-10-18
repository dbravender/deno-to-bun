"""Fast tests for evaluator safety and paired-comparison validation."""
import json
from pathlib import Path
import tempfile
import unittest

from compare import REVIEW_FIELDS, summarize
from run import Evaluation, prepare


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_prepare_refuses_existing_directory(self):
        with self.assertRaises(AssertionError):
            prepare("cli", self.root)

    def test_evaluation_refuses_unmarked_target(self):
        with self.assertRaises(FileNotFoundError):
            Evaluation("cli", self.root, "bun", "/unused/bun", "/unused/deno")

    def manifest(self):
        report = {"case": "cli", "runtime": "bun", "passed": True,
                  "checks": [{"name": "behavior", "passed": True}],
                  "evaluator_sha256": "same-grader",
                  "versions": {"bun": "test-bun", "deno": "test-deno"}}
        for arm in ("skill", "control"):
            (self.root / (arm + ".json")).write_text(json.dumps(report))
        common = {"pair": "cli-01", "case": "cli", "repeat": 1, "model": "same-model",
                  "request_sha256": "same-request", "budget": {"seconds": 60}, "tools": ["same-tools"]}
        return {"kind": "paired-agent-trials", "attempts": [
            {**common, "arm": arm, "report": arm + ".json"} for arm in ("skill", "control")
        ]}

    def test_comparison_does_not_invent_review_or_cost(self):
        result = summarize(self.manifest(), self.root)
        self.assertEqual(result["automated_outcomes"]["both_pass"], 1)
        self.assertEqual(result["reviewed_pairs"], 0)
        self.assertIsNone(result["metrics"]["skill"]["cost_usd"]["median"])

    def test_unpaired_attempt_is_rejected(self):
        manifest = self.manifest()
        manifest["attempts"].pop()
        with self.assertRaisesRegex(ValueError, "Unpaired"):
            summarize(manifest, self.root)

    def test_different_models_are_not_a_pair(self):
        manifest = self.manifest()
        manifest["attempts"][1]["model"] = "different"
        with self.assertRaisesRegex(ValueError, "model"):
            summarize(manifest, self.root)

    def test_different_runtime_versions_are_not_a_pair(self):
        manifest = self.manifest()
        path = self.root / "skill.json"
        report = json.loads(path.read_text())
        report["versions"]["bun"] = "different"
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "runtimes"):
            summarize(manifest, self.root)

    def test_selftest_is_not_agent_evidence(self):
        manifest = self.manifest()
        path = self.root / "skill.json"
        report = json.loads(path.read_text())
        report["kind"] = "evaluator-selftest-not-agent-comparison"
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "Self-tests"):
            summarize(manifest, self.root)

    def test_different_graders_are_not_comparable(self):
        manifest = self.manifest()
        path = self.root / "skill.json"
        report = json.loads(path.read_text())
        report["evaluator_sha256"] = "different-grader"
        path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "evaluators"):
            summarize(manifest, self.root)

    def test_review_failure_is_not_a_migration_success(self):
        manifest = self.manifest()
        for attempt in manifest["attempts"]:
            attempt["review"] = dict.fromkeys(REVIEW_FIELDS, True)
        manifest["attempts"][0]["review"]["honest_handoff"] = False
        result = summarize(manifest, self.root)
        self.assertEqual(result["reviewed_pairs"], 1)
        self.assertEqual(result["reviewed_outcomes"]["control_only"], 1)


if __name__ == "__main__":
    unittest.main()
