# St. Moritz Security Services - Proposal Microsite

A lightweight Node.js app for collecting intake details and generating proposal drafts, including `.docx` export.

## Why it is portable

- No hardcoded filesystem paths remain for data, content library, or branding.
- Runtime behavior is driven by environment variables so another client can deploy with their own settings.
- Includes both direct Node.js and Docker-based deployment paths.

## Local quick start

- Install Node.js 18+.
- Run `npm start`.
- Open `http://localhost:3000`.

## Environment variables

Create `.env` from `.env.example` and adjust values.

- `PORT` - server port (default `3000`)
- `PUBLIC_DIR` - directory for static files (default repo root)
- `PROPOSAL_DATA_DIR` - proposal store location (default `<repo>/data`)
- `LIBRARY_FILE` - path to content library JSON (default `<repo>/content-library.json`)
- `BRAND_NAME` - company name used in generated docs (default `St. Moritz Security Services`)
- `BRAND_TAGLINE` - optional startup log text (default `Proposal Builder`)
- `CLIENT_NAME_FALLBACK` - fallback client name in generated files
- `CORS_ORIGINS` - comma-separated allowed origins (default `*`)
- `WORD_IMAGES_ENABLED` - set `0` to temporarily disable images in DOCX export for recovery/debugging

## API endpoints

- `GET /api/library`
- `PUT /api/library`
- `POST /api/export/docx`
- `GET /api/proposals`
- `POST /api/proposals`
- `GET /api/proposals/:id`
- `PUT /api/proposals/:id`

## Docker

Run locally from this repo:

```bash
docker compose up --build
```

Compose mounts a volume for runtime data:

- proposals -> `PROPOSAL_DATA_DIR` (default `/app/data`)
- content library -> `LIBRARY_FILE`

You can replace `.env` values to target a different output location or brand.

## Persistence

- Proposals are stored in `proposals.json` inside `PROPOSAL_DATA_DIR`.
- Proposal library is stored at `LIBRARY_FILE`.

If you need isolated environments per client, mount host directories per deployment and set the env paths accordingly.

## GitHub deployment

### 1) Install Git and initialize

From this project folder:

- Install Git (if needed) and initialize:

```bash
git init
git branch -M main
```

- Add `.gitignore` entries (already in this repo) and check status:

```bash
git status
```

### 2) Create the first commit

```bash
git add .
git commit -m "Initial proposal microsite implementation"
```

Or run:

```powershell
./scripts/bootstrap-github.ps1 -GitHubOwnerRepo "<OWNER>/<REPO>"
```

### 3) Create a GitHub repository and connect it

- On GitHub, create a new repository (blank, no README/license if adding existing files).
- Add remote and push:

```bash
git remote add origin https://github.com/<OWNER>/<REPO>.git
git push -u origin main
```

### 4) Clone and run elsewhere

```bash
git clone https://github.com/<OWNER>/<REPO>.git
cd <REPO>
npm install
cp .env.example .env  # then update values for the target client
npm start
```

## Optional: protect client runtime data

- `data/` is ignored by `.gitignore` so proposal records stay local per deployment.
- Keep client branding and image libraries in versioned files (e.g., `content-library.json`) and mount client-specific runtime directories via env vars.

## Enforcing GitHub-only changes

To make sure all production changes come only from GitHub:

- Set `main` as the default branch.
- Enable branch protection on `main`:
  - Require pull requests before merging.
  - Require status checks from `CI` to pass.
  - Disable force pushes.
  - Do not allow deletion.

### Required workflow

- Never push to `main` directly.
- Open a feature branch for every change:
  - `git checkout -b feat/new-change`
- Push the branch and open a PR to `main`.
- Merge only after CI is green and reviews are complete.
- Deployments are generated only from `main` merges.

### Repository settings checklist

In GitHub -> Settings -> Branches -> Branch protection rules, configure:

- Branch name pattern: `main`
- Require a pull request before merging.
- Require status checks to pass before merging (`CI`).
- Disable force pushes.
- Prevent branch deletion.

Because CI runs in GitHub Actions and deployment artifacts are produced only from `push` events on `main`, local-only edits stay local until merged and pushed.


