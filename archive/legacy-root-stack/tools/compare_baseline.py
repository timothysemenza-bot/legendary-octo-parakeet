#!/usr/bin/env python3
"""Compare parsed test report against baseline expectations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_seed_map(report: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for result in report.get("results", []):
        seed = str(result.get("seed", ""))
        if seed:
            out[seed] = result
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default=".artifacts/baselines/baseline.json", help="Baseline JSON path")
    parser.add_argument("--report", default="dist/test-report.json", help="Current report JSON path")
    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    report_path = Path(args.report)

    if not baseline_path.exists():
        print(f"ERROR: baseline not found: {baseline_path}")
        return 1
    if not report_path.exists():
        print(f"ERROR: report not found: {report_path}")
        return 1

    baseline = load_json(baseline_path)
    report = load_json(report_path)

    tolerances = baseline.get("tolerances", {})
    expected = baseline.get("expected", {})
    expected_summary = expected.get("summary", {})
    expected_seeds = expected.get("seeds", {})

    report_summary = report.get("summary", {})
    report_seeds = as_seed_map(report)

    issues: list[str] = []

    for key, exp_val in expected_summary.items():
        got_val = report_summary.get(key)
        if got_val != exp_val:
            issues.append(f"summary mismatch {key}: expected {exp_val}, got {got_val}")

    for seed, exp in expected_seeds.items():
        got = report_seeds.get(seed)
        if not got:
            issues.append(f"missing seed result: {seed}")
            continue

        exp_status = exp.get("status")
        if exp_status is not None and got.get("status") != exp_status:
            issues.append(f"seed {seed} status mismatch: expected {exp_status}, got {got.get('status')}")

        exp_metrics = exp.get("metrics", {})
        got_metrics = got.get("metrics", {}) if isinstance(got.get("metrics"), dict) else {}
        for metric, exp_val in exp_metrics.items():
            got_val = got_metrics.get(metric)
            if got_val is None:
                issues.append(f"seed {seed} missing metric: {metric}")
                continue
            tol = tolerances.get(metric, 0)
            if isinstance(exp_val, (int, float)) and isinstance(got_val, (int, float)):
                if abs(got_val - exp_val) > tol:
                    issues.append(
                        f"seed {seed} metric {metric} out of tolerance: expected {exp_val} +/- {tol}, got {got_val}"
                    )
            elif got_val != exp_val:
                issues.append(f"seed {seed} metric {metric} mismatch: expected {exp_val}, got {got_val}")

    if issues:
        print("Baseline comparison failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Baseline comparison passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
