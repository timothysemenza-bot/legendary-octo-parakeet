from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .config import AppConfig, load_config
from .date_utils import get_month_window, get_prior_month_window, iter_month_keys
from .dedupe import DedupeResult, filter_new_items
from .email_client_fixtures import FixturesEmailClient
from .email_client_gmail_api import GmailApiEmailClient
from .email_client_imap import ImapEmailClient
from .logging_utils import setup_logging
from .models import EmailMessage, ExistingLedgerKeys, NormalizedLineItem, ProcessResult
from .monthly_report import now_iso, write_report
from .receipt_extractors.apple_receipt_parser import parse_apple_receipt
from .sheets_client import GoogleSheetsClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apple receipts to Google Sheets automation")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Import prior or specific month and write to Sheets")
    run_p.add_argument("--month", default="prior", help="prior or YYYY-MM")

    dry_p = sub.add_parser("dry-run", help="Parse and summarize without writing")
    dry_p.add_argument("--month", default="prior", help="prior or YYYY-MM")

    backfill_p = sub.add_parser("backfill", help="Import a month range inclusive")
    backfill_p.add_argument("--start", required=True, help="YYYY-MM")
    backfill_p.add_argument("--end", required=True, help="YYYY-MM")

    return parser


def _resolve_month_keys(command: str, month_arg: str | None, cfg: AppConfig, start: str | None, end: str | None) -> list[str]:
    if command == "backfill":
        if not start or not end:
            raise ValueError("--start and --end are required for backfill")
        return iter_month_keys(start, end)

    if month_arg == "prior":
        return [get_prior_month_window(cfg.timezone).month_key]
    if month_arg is None:
        raise ValueError("--month must be set")
    return [month_arg]


def _message_matches_merchants(message: EmailMessage, merchants: dict) -> bool:
    sender = message.sender.lower()
    subject = message.subject.lower()

    for vendor in merchants.get("vendors", []):
        sender_terms = [s.lower() for s in vendor.get("sender_contains", [])]
        subject_terms = [s.lower() for s in vendor.get("subject_contains", [])]
        sender_ok = any(term in sender for term in sender_terms) if sender_terms else True
        subject_ok = any(term in subject for term in subject_terms) if subject_terms else True
        if sender_ok and subject_ok:
            return True
    return False


def _build_email_client(cfg: AppConfig, dry_run: bool):
    fixtures_dir = cfg.email_fixtures_dir
    if not fixtures_dir and dry_run:
        default_fixture_dir = Path("tests") / "fixtures" / "messages"
        if default_fixture_dir.exists():
            fixtures_dir = str(default_fixture_dir)
    if fixtures_dir and Path(fixtures_dir).exists():
        return FixturesEmailClient(fixtures_dir), "fixtures"

    if cfg.gmail_mode == "imap":
        if not (cfg.imap_host and cfg.imap_user and cfg.imap_app_password):
            raise ValueError("IMAP mode requires IMAP_HOST, IMAP_USER, IMAP_APP_PASSWORD")
        return ImapEmailClient(cfg.imap_host, cfg.imap_user, cfg.imap_app_password), "imap"

    if not cfg.oauth_client_secret_json:
        raise ValueError("API mode requires GOOGLE_OAUTH_CLIENT_SECRET_JSON")
    return GmailApiEmailClient(cfg.oauth_client_secret_json, cfg.gmail_oauth_token_json), "gmail_api"


def _build_sheets_client(cfg: AppConfig) -> GoogleSheetsClient:
    if not cfg.spreadsheet_id:
        raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is required")
    if not cfg.oauth_client_secret_json:
        raise ValueError("GOOGLE_OAUTH_CLIENT_SECRET_JSON is required")

    return GoogleSheetsClient(
        spreadsheet_id=cfg.spreadsheet_id,
        range_name=cfg.sheets_range,
        client_secret=cfg.oauth_client_secret_json,
        token_path=cfg.sheets_oauth_token_json,
    )


def _item_to_row(item: NormalizedLineItem) -> list[str]:
    return [
        item.purchase_date.date().isoformat(),
        item.vendor,
        item.description,
        f"{item.amount:.2f}",
        item.currency,
        item.invoice_id,
        item.raw_message_id,
        item.source,
        item.month_key,
        now_iso(),
    ]


def _empty_keys() -> ExistingLedgerKeys:
    return ExistingLedgerKeys(invoice_ids=set(), source_message_ids=set(), fingerprints=set())


def process_month(
    cfg: AppConfig,
    month_key: str,
    dry_run: bool,
    logger,
) -> ProcessResult:
    month_window = get_month_window(cfg.timezone, month_key)

    email_client, source_name = _build_email_client(cfg, dry_run=dry_run)
    messages = email_client.fetch_messages(month_window.start, month_window.end_exclusive, cfg.merchants)
    filtered_messages = [m for m in messages if _message_matches_merchants(m, cfg.merchants)]

    parsed_items: list[NormalizedLineItem] = []
    debug_dir = Path("output") / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    for message in filtered_messages:
        try:
            extracted = parse_apple_receipt(message, timezone=cfg.timezone)
            parsed_items.extend(replace(item, source=source_name) for item in extracted)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Parse failure for message {message.message_id}: {exc}")
            debug_file = debug_dir / f"{month_key}-{message.message_id}.txt"
            debug_file.write_text(message.raw_content, encoding="utf-8")

    existing = _empty_keys()
    sheets_client = None
    if cfg.spreadsheet_id and cfg.oauth_client_secret_json:
        try:
            sheets_client = _build_sheets_client(cfg)
            existing = sheets_client.read_existing_keys()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Could not read existing ledger keys: {exc}")
            if not dry_run:
                raise

    deduped: DedupeResult = filter_new_items(parsed_items, existing)
    new_items = deduped.unique_items

    appended_rows = 0
    if not dry_run:
        if not sheets_client:
            raise ValueError("Sheets credentials missing for run/backfill mode")
        appended_rows = sheets_client.append_ledger_rows(_item_to_row(item) for item in new_items)

    report_path = write_report(Path("output") / "reports", month_key, cfg.friend_name, parsed_items)

    logger.info(
        f"Month {month_key}: fetched={len(messages)} matched={len(filtered_messages)} parsed={len(parsed_items)} new={len(new_items)} appended={appended_rows} dropped={deduped.dropped_count}"
    )

    return ProcessResult(
        month_key=month_key,
        fetched_messages=len(filtered_messages),
        parsed_items=len(parsed_items),
        new_items=len(new_items),
        appended_rows=appended_rows,
        report_path=str(report_path),
    )


def _run_for_keys(cfg: AppConfig, month_keys: Iterable[str], dry_run: bool) -> list[ProcessResult]:
    logger = setup_logging(Path("output") / "logs")
    results: list[ProcessResult] = []
    for month_key in month_keys:
        results.append(process_month(cfg, month_key, dry_run=dry_run, logger=logger))
    return results


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cfg = load_config(Path.cwd())

    month_keys = _resolve_month_keys(
        command=args.command,
        month_arg=getattr(args, "month", None),
        cfg=cfg,
        start=getattr(args, "start", None),
        end=getattr(args, "end", None),
    )

    dry_run = args.command == "dry-run"
    results = _run_for_keys(cfg, month_keys, dry_run=dry_run)

    for result in results:
        print(
            f"{result.month_key}: fetched={result.fetched_messages} parsed={result.parsed_items} new={result.new_items} appended={result.appended_rows} report={result.report_path}"
        )


if __name__ == "__main__":
    main()
