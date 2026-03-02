from src.sheets_client import _to_full_read_range


def test_to_full_read_range_from_append_anchor() -> None:
    assert _to_full_read_range("Ledger!A1") == "Ledger!A:J"


def test_to_full_read_range_keeps_sheet_name() -> None:
    assert _to_full_read_range("My Ledger!B2") == "My Ledger!A:J"
