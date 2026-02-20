# Contributing

## Workflow goal

All production changes must flow through GitHub with pull requests into `main`.

## Process

1. Create a branch from `main`.
2. Push your branch to GitHub.
3. Open a PR and fill in the checklist.
4. Wait for `CI` to pass.
5. Merge only after approval.

## Branch rules

- Never push directly to `main`.
- Use descriptive branch names such as `feat/short-description` or `fix/short-description`.

## Local conventions

- Keep generated files out of version control (`.docx`, `.doc`, logs, `data/`).
- Update content library and branding files with valid JSON.

## Optional local safety

Install the repo hooks to catch accidental pushes to `main`:

```bash
git config core.hooksPath .githooks
```

Then run `npm start` and the smoke endpoint before opening a PR:

```bash
npm start
curl http://localhost:3000/api/proposals
```
