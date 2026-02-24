# Briefs Directory

## Purpose

Human-readable outputs from automation scripts and daily operations.

## Structure

- `briefs/` (root): active daily summaries and stable reference briefs.
- `briefs/generated/public-capture/`: generated public-capture artifacts.
- `briefs/generated/go-no-go/`: generated go/no-go memo sets.

## Naming

- Daily: `YYYY-MM-DD.md`
- Dated generated output: `*-YYYY-MM-DD.md`
- Calendar exports: `*.ics`

## Cleanup

If a file is generated and not a long-term reference, place it under `generated/`.
