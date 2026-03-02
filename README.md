# Apple Receipt Reimbursement Automation

End-to-end Python automation for:
1. Pulling Apple-related receipt emails for a month window.
2. Parsing receipts into normalized line items.
3. Deduping against existing ledger keys and in-run duplicates.
4. Appending only new rows to Google Sheets `Ledger` via Sheets API `values.append`.
5. Emitting a monthly reimbursement report with total, itemized list, and Venmo memo text.

## Required Layout

- `src/config.py`
- `src/email_client_gmail_api.py`
- `src/email_client_imap.py`
- `src/receipt_extractors/apple_receipt_parser.py`
- `src/dedupe.py`
- `src/sheets_client.py`
- `src/monthly_report.py`
- `src/main.py`
- `config/merchants.json`
- `config/sheet_schema.json`
- `output/logs`, `output/reports`, `output/debug`
- `tests/` for parser, dedupe, and month-boundary logic

## Google Sheet Schema (documented)

Create a Google Sheet with tab `Ledger` and this header row:

`Date, Vendor, Description, Amount, Currency, InvoiceId, SourceMessageId, Source, MonthKey, ImportedAt`

Optional tab: `MonthlySummary`.

The script appends rows using Sheets API `spreadsheets.values.append` with:
- `valueInputOption=USER_ENTERED`
- `insertDataOption=INSERT_ROWS`

Reference:
- https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/append

## Setup

### 1. Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment config

Copy `.env.example` to `.env` and set values:

- `GMAIL_MODE=(api|imap)`
- `IMAP_HOST`, `IMAP_USER`, `IMAP_APP_PASSWORD` (IMAP fallback)
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_RANGE` (example: `Ledger!A1`)
- `GOOGLE_OAUTH_CLIENT_SECRET_JSON` (OAuth client secret JSON path)
- `GOOGLE_GMAIL_OAUTH_TOKEN_JSON` (Gmail OAuth token path)
- `GOOGLE_SHEETS_OAUTH_TOKEN_JSON` (Sheets OAuth token path)
- `TIMEZONE=America/New_York`
- `FRIEND_NAME=Matt`
- `EMAIL_FIXTURES_DIR` (optional local fixture mode)

### 3. Google Sheets API auth

Use the Google quickstart-style OAuth flow for installed apps. First run will open browser auth and save Gmail token JSON to `GOOGLE_GMAIL_OAUTH_TOKEN_JSON` and Sheets token JSON to `GOOGLE_SHEETS_OAUTH_TOKEN_JSON`.

Reference:
- https://developers.google.com/workspace/sheets/api/quickstart/python

### 4. Gmail auth mode

Recommended: Gmail API OAuth (`GMAIL_MODE=api`) using the same OAuth credentials flow.

Fallback: IMAP app password (`GMAIL_MODE=imap`). Gmail app passwords require 2-Step Verification.

Reference:
- https://support.google.com/accounts/answer/185833

## CLI Usage

### Dry run

```powershell
python -m src.main dry-run --month prior
```

- Parses and computes report totals without writing to Sheets.
- Works without external services when fixture mode is enabled (`EMAIL_FIXTURES_DIR`) or when `tests/fixtures/messages` exists.

### Monthly run

```powershell
python -m src.main run --month prior
```

- Pulls prior month in `America/New_York`.
- Dedupes against existing `Ledger` rows and within current run.
- Appends only new rows to `Ledger`.
- Writes report: `output/reports/YYYY-MM.txt`

### Backfill

```powershell
python -m src.main backfill --start 2025-01 --end 2025-12
```

## Report output

Each report file includes:
- `MonthKey`
- `Total`
- itemized list `(date, description, amount)`
- Venmo memo: `Apple expenses YYYY-MM`
- `Amount to pay Matt: $X.XX`

## Error handling and logs

- Structured JSON logs: `output/logs/automation.log`
- On parse failures, raw message is written to `output/debug` and processing continues.

## Windows Task Scheduler (monthly)

Create a task:
1. Trigger: Monthly, day 1, `08:00`.
2. Action: Start a program.
3. Program/script: `C:\Users\timot\Documents\Proposal-Microsite\.venv\Scripts\python.exe`
4. Arguments: `-m src.main run --month prior`
5. Start in: `C:\Users\timot\Documents\Proposal-Microsite`

This avoids Codex app automations dependency on the Codex app process.
Reference:
- https://developers.openai.com/codex/app/automations/
