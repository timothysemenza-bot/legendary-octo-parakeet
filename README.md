# Video Game Mod CI/CD Skeleton

This repository now includes a complete CI/CD skeleton for a private mod project.

## What this includes
- Hosted CI (`.github/workflows/ci.yml`) on `ubuntu-latest`:
  - Lua lint (`luacheck` via `luarocks`)
  - mod validation (`tools/validate_mod.py`)
  - Python unit tests (`python -m unittest discover tests`)
  - deterministic packaging (`tools/pack_mod.py`) to `dist/mod-dev.zip`
- Self-hosted integration CI (`.github/workflows/integration.yml`) on Windows runner labels:
  - `runs-on: [self-hosted, isaac-win]`
  - installs mod into game mods directory
  - runs seed scenarios via a generic harness (`tools/run_seeds.py`)
  - parses `BKTEST` contract logs (`tools/parse_log.py`)
  - compares report to baseline (`tools/compare_baseline.py`)
  - packages zip and uploads artifacts
- Release workflow (`.github/workflows/release.yml`):
  - triggers on tags `v*.*.*`
  - validates + packages with tag version
  - creates GitHub release with attached zip

## Important note
Hosted CI does **not** run the game and does not require proprietary binaries.

## Repo layout
- `mod/` sample mod scaffold
- `mod/main.lua` includes `TEST_MODE` switch and emits `BKTEST` + `BKTEST_DONE` JSON lines
- `tools/` Python 3.11 scripts
- `tests/` minimal unit tests
- `.artifacts/baselines/baseline.json` sample baseline
- `dist/` generated artifacts (gitignored)

## Local usage
### Validate mod
```bash
python tools/validate_mod.py
```

### Package mod (deterministic)
```bash
python tools/pack_mod.py --version dev
```

### Simulate integration test flow without game
```bash
python tools/run_seeds.py --seeds tools/seeds.txt --log dist/integration.log
python tools/parse_log.py --log dist/integration.log --out dist/test-report.json
python tools/compare_baseline.py --baseline .artifacts/baselines/baseline.json --report dist/test-report.json
```

## Self-hosted runner configuration
Set these env vars on your Windows self-hosted runner (or in workflow/job env):
- `ISAAC_MODS_DIR`: game mods directory to install into
- `ISAAC_EXE`: executable path for integration harness (leave empty to simulate)
- `LOG_PATH`: path to raw integration log output
- `ISAAC_ARGS_TEMPLATE` (optional): args template for executable, supports `{seed}`

Example defaults are already set in `integration.yml` and intended to be edited.

## Baseline behavior
Baseline file: `.artifacts/baselines/baseline.json`.

`tools/compare_baseline.py` checks:
- expected summary totals
- expected per-seed status
- expected per-seed metrics within configured tolerances

To intentionally update baseline after approved changes:
1. Run integration flow and inspect `dist/test-report.json`.
2. Copy expected values into `.artifacts/baselines/baseline.json`.
3. Commit baseline update with rationale in PR.
