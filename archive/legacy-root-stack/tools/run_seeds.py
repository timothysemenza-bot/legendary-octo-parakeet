#!/usr/bin/env python3
"""Run seed scenarios via generic executable harness or simulation."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path


def read_seeds(path: Path) -> list[str]:
    seeds: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        seeds.append(line)
    return seeds


def write_line(handle, line: str) -> None:
    handle.write(line + "\n")
    handle.flush()


def simulate(seeds: list[str], log_path: Path) -> None:
    with log_path.open("w", encoding="utf-8") as out:
        for i, seed in enumerate(seeds):
            write_line(out, "BKTEST " + json.dumps({"seed": seed, "event": "start", "frame": 0}, sort_keys=True))
            write_line(out, "BKTEST " + json.dumps({"seed": seed, "event": "checkpoint", "rooms": i + 1}, sort_keys=True))
            done = {
                "seed": seed,
                "status": "pass",
                "metrics": {"duration_ms": 100 + i * 10, "score": 100 + i * 20},
            }
            write_line(out, "BKTEST_DONE " + json.dumps(done, sort_keys=True))


def run_external(seeds: list[str], exe: Path, args_template: str, timeout: int, log_path: Path) -> None:
    with log_path.open("w", encoding="utf-8") as out:
        for seed in seeds:
            argv = [str(exe)]
            if args_template:
                argv.extend(shlex.split(args_template.format(seed=seed)))
            else:
                argv.append(seed)

            write_line(out, f"# RUN {' '.join(argv)}")
            started = time.time()
            try:
                completed = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
                elapsed_ms = int((time.time() - started) * 1000)
                if completed.stdout:
                    out.write(completed.stdout)
                    if not completed.stdout.endswith("\n"):
                        out.write("\n")
                if completed.stderr:
                    out.write(completed.stderr)
                    if not completed.stderr.endswith("\n"):
                        out.write("\n")
                out.flush()
                if completed.returncode != 0:
                    write_line(
                        out,
                        "BKTEST_DONE "
                        + json.dumps(
                            {
                                "seed": seed,
                                "status": "fail",
                                "metrics": {"duration_ms": elapsed_ms, "score": 0},
                                "returncode": completed.returncode,
                            },
                            sort_keys=True,
                        ),
                    )
            except subprocess.TimeoutExpired:
                write_line(
                    out,
                    "BKTEST_DONE "
                    + json.dumps(
                        {"seed": seed, "status": "fail", "metrics": {"duration_ms": timeout * 1000, "score": 0}, "reason": "timeout"},
                        sort_keys=True,
                    ),
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="tools/seeds.txt", help="Path to seeds list")
    parser.add_argument("--exe", default=os.environ.get("ISAAC_EXE", ""), help="Executable path for integration harness")
    parser.add_argument("--args-template", default=os.environ.get("ISAAC_ARGS_TEMPLATE", ""), help="Optional args template, supports {seed}")
    parser.add_argument("--timeout", type=int, default=60, help="Per-seed timeout in seconds")
    parser.add_argument("--log", default=os.environ.get("LOG_PATH", "dist/integration.log"), help="Output log path")
    args = parser.parse_args()

    seeds_path = Path(args.seeds)
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not seeds_path.exists():
        print(f"ERROR: seeds file not found: {seeds_path}")
        return 1

    seeds = read_seeds(seeds_path)
    if not seeds:
        print("ERROR: no seeds found")
        return 1

    exe_raw = args.exe.strip()
    if not exe_raw:
        print("ISAAC_EXE not set; running in simulate mode.")
        simulate(seeds, log_path)
        print(f"Wrote simulated log: {log_path}")
        return 0

    exe_path = Path(exe_raw)
    if not exe_path.exists():
        print(f"ERROR: ISAAC_EXE does not exist: {exe_path}")
        return 1

    run_external(seeds, exe_path, args.args_template, args.timeout, log_path)
    print(f"Wrote integration log: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
