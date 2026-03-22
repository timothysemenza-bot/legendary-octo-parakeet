# Legacy Root Stack

This folder preserves the older root-level systems that used to define this repository before the ProposalOps refocus.

## What is here

- `mod/`: the old Lua mod scaffold
- `src/`, `tests/`, `tools/`, `config/`: the older Python reporting and helper stack
- `.artifacts/`: baseline data used by that stack
- `.github/workflows/`: the old mod-oriented CI, integration, and release workflows
- `requirements.txt` and `.luacheckrc`: legacy root-level support files for that system

## Why it was moved

These files were real work, but they no longer support the active product story of this repository:

- `proposal-ops/` as the flagship
- `boss-key-website/` as the market-facing wrapper
- `marketing-agents/` as the operating automation layer

Keeping the legacy stack here preserves it without letting it compete with the current direction.

## If you ever revisit it

Treat this folder as its own historical subproject.
If any part of it becomes relevant again, bring back only the pieces that clearly support the current product lane.
