# APMP Helpjuice Export

Use this workflow when you want to capture your own licensed APMP Helpjuice study-guide pages into this repo so Codex can align agents to the exact BOK wording.

## What this does

- opens a real Chromium window with a persistent local profile
- lets you log in yourself
- recursively crawls pages under `https://apmp.helpjuice.com/` by default
- saves the exported HTML and lightweight metadata into `outputs/generated/`

## Why this is the safest path

- you keep control of the login in your own browser window
- credentials never need to be shared in chat
- the exported files stay local in your workspace

## Run it

From the repo root:

```bash
node .\scripts\export-apmp-helpjuice-bok.mjs
```

Optional flags:

```bash
node .\scripts\export-apmp-helpjuice-bok.mjs ^
  --url "https://apmp.helpjuice.com/study-guide-v4/foundation-study-guide-version4" ^
  --scope-prefix "https://apmp.helpjuice.com/" ^
  --max-pages 500 ^
  --output-dir ".\outputs\generated\apmp-helpjuice-export" ^
  --profile-dir ".\.tmp\apmp-helpjuice-profile"
```

## How to use it

1. Run the script.
2. Log in in the opened browser window.
3. Open the broadest APMP Helpjuice page you want to start from, such as a browse-everything or table-of-contents view.
4. Expand collapsed navigation and scroll far enough to trigger lazy-loaded links.
5. Return to the terminal and press Enter.
6. Let the crawler recursively discover and save subordinate pages within the chosen scope.

## Output

The script writes:

- `outputs/generated/apmp-helpjuice-export-YYYY-MM-DD/manifest.json`
- `outputs/generated/apmp-helpjuice-export-YYYY-MM-DD/pages/*.html`
- `outputs/generated/apmp-helpjuice-export-YYYY-MM-DD/pages/*.json`

Each JSON file contains the page URL, title, headings, and extracted body text alongside the full HTML snapshot.

The manifest also records:

- the actual page where the crawl started
- which page each URL was discovered from
- how many links were discovered on each exported page
- whether the crawl stopped because it hit the max page limit

## After export

Once the export exists locally, Codex can:

- build a canonical APMP reference pack
- align the APMP competency agents to the exact BOK wording
- tighten the skill and handoff definitions using the real source text

## Notes

- Keep the export local and private.
- Do not distribute member-only APMP material.
- The crawler only follows normal page links that appear in the DOM. It will not discover content hidden behind forms, search requests, or JavaScript-only API calls unless those links are rendered on a page first.
- Use `--scope-prefix "https://apmp.helpjuice.com/"` for a whole-site crawl, or narrow it if you only want a subsection.
- Increase `--max-pages` if the crawl stops before it reaches the whole section you want.
