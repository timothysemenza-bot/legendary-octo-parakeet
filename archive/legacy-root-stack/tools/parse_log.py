#!/usr/bin/env python3
"""Parse BKTEST log contract into a structured report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_line(prefix: str, line: str):
    payload = line[len(prefix):].strip()
    return json.loads(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="dist/integration.log", help="Input log file")
    parser.add_argument("--out", default="dist/test-report.json", help="Output JSON report")
    args = parser.parse_args()

    log_path = Path(args.log)
    out_path = Path(args.out)

    if not log_path.exists():
        print(f"ERROR: log file not found: {log_path}")
        return 1

    events: dict[str, list[dict]] = {}
    done: dict[str, dict] = {}

    for raw in log_path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("BKTEST_DONE "):
            try:
                obj = parse_line("BKTEST_DONE ", line)
                seed = str(obj.get("seed", "unknown"))
                done[seed] = obj
            except Exception:
                continue
        elif line.startswith("BKTEST "):
            try:
                obj = parse_line("BKTEST ", line)
                seed = str(obj.get("seed", "unknown"))
                events.setdefault(seed, []).append(obj)
            except Exception:
                continue

    all_seeds = sorted(set(events.keys()) | set(done.keys()))
    results: list[dict] = []

    for seed in all_seeds:
        done_obj = done.get(seed, {})
        status = str(done_obj.get("status", "unknown"))
        metrics = done_obj.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}
        results.append(
            {
                "seed": seed,
                "status": status,
                "events": len(events.get(seed, [])),
                "metrics": metrics,
            }
        )

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = total - passed

    report = {
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
        },
        "meta": {
            "source": str(log_path),
            "bktest_events": sum(len(v) for v in events.values()),
            "bktest_done": len(done),
        },
    }

    if total == 0:
        print("ERROR: no BKTEST/BKTEST_DONE entries parsed")
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote report: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
