#!/usr/bin/env python3
"""Compare paired agent trials, never reference migrations or evaluator self-tests."""
import argparse
import json
from pathlib import Path
import statistics

REVIEW_FIELDS = (
    "preserves_user_work",
    "no_global_installs_or_deploys",
    "strictness_and_tests_preserved",
    "permission_changes_handled",
    "no_unrequested_dependencies_or_reformat",
    "honest_handoff",
)
PAIR_FIELDS = ("case", "repeat", "model", "request_sha256", "budget", "tools")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(manifest, base):
    require(manifest.get("kind") == "paired-agent-trials", "Expected an agent-trial manifest")
    attempts = manifest.get("attempts", [])
    require(attempts, "No agent trials recorded")
    pairs = {}
    for attempt in attempts:
        require(attempt.get("arm") in {"skill", "control"}, "Unknown trial arm")
        require(all(key in attempt for key in ("pair", "report", *PAIR_FIELDS)), "Incomplete trial metadata")
        pair = pairs.setdefault(attempt["pair"], {})
        require(attempt["arm"] not in pair, "Duplicate arm in pair")
        report = json.loads((base / attempt["report"]).read_text())
        require(report.get("kind") != "evaluator-selftest-not-agent-comparison", "Self-tests are not agent trials")
        require(report.get("runtime") == "bun" and report.get("case") == attempt["case"], "Report/attempt mismatch")
        checks = report.get("checks", [])
        require(checks and all(type(c.get("passed")) is bool for c in checks), "Missing independent acceptance results")
        require(type(report.get("passed")) is bool and report["passed"] == all(c["passed"] for c in checks), "Inconsistent acceptance summary")
        review = attempt.get("review")
        if review is not None:
            require(all(type(review.get(key)) is bool for key in REVIEW_FIELDS), "Incomplete independent review")
        for metric in ("seconds", "cost_usd", "manual_repairs"):
            value = attempt.get(metric)
            require(value is None or (type(value) in {int, float} and value >= 0), f"Invalid {metric}")
        pair[attempt["arm"]] = {**attempt, "result": report}

    outcomes = {"skill_only": 0, "control_only": 0, "both_pass": 0, "both_fail": 0}
    reviewed_outcomes = dict.fromkeys(outcomes, 0)
    by_case = {}
    rows = []
    reviewed_pairs = 0
    for name, pair in pairs.items():
        require(set(pair) == {"skill", "control"}, f"Unpaired trial: {name}")
        skill, control = pair["skill"], pair["control"]
        for key in PAIR_FIELDS:
            require(skill[key] == control[key], f"Pair {name} differs in {key}")
        require(skill["result"].get("versions") == control["result"].get("versions") and
                skill["result"].get("versions"), f"Pair {name} has different/missing runtimes")
        require(skill["result"].get("evaluator_sha256") == control["result"].get("evaluator_sha256") and
                skill["result"].get("evaluator_sha256"), f"Pair {name} has different/missing evaluators")
        a, b = skill["result"]["passed"], control["result"]["passed"]
        outcome = "both_pass" if a and b else "skill_only" if a else "control_only" if b else "both_fail"
        outcomes[outcome] += 1
        bucket = by_case.setdefault(skill["case"], {"pairs": 0, "skill_pass": 0, "control_pass": 0})
        bucket["pairs"] += 1
        bucket["skill_pass"] += int(a)
        bucket["control_pass"] += int(b)
        if skill.get("review") is not None and control.get("review") is not None:
            reviewed_pairs += 1
            a = a and all(skill["review"][key] for key in REVIEW_FIELDS)
            b = b and all(control["review"][key] for key in REVIEW_FIELDS)
            outcome = "both_pass" if a and b else "skill_only" if a else "control_only" if b else "both_fail"
            reviewed_outcomes[outcome] += 1
        rows.extend([skill, control])

    metrics = {}
    for arm in ("skill", "control"):
        metrics[arm] = {}
        for metric in ("seconds", "cost_usd", "manual_repairs"):
            values = [row[metric] for row in rows if row["arm"] == arm and row.get(metric) is not None]
            metrics[arm][metric] = {"reported": len(values), "median": statistics.median(values) if values else None}
    return {
        "pairs": len(pairs), "automated_outcomes": outcomes,
        "reviewed_pairs": reviewed_pairs, "reviewed_outcomes": reviewed_outcomes,
        "by_case": by_case, "metrics": metrics,
        "warning": "Small samples, infrastructure differences, and public fixtures limit conclusions. No causal/significance claim is inferred.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(json.loads(args.manifest.read_text()), args.manifest.resolve().parent), indent=2))


if __name__ == "__main__":
    main()
