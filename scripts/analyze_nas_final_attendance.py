from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import csv
import math

from openpyxl import load_workbook


WORKBOOK_PATH = Path(
    r"C:\Users\timot\Downloads\NAS_Spring_Dance_2026-2026-03-14-165602-collection_summary_reworked.xlsx"
)
OUTPUT_DIR = Path(r"C:\Users\timot\Documents\Proposal-Microsite\output")
SUMMARY_PATH = OUTPUT_DIR / "nas_spring_dance_2026_attendance_summary.md"
SEGMENTS_PATH = OUTPUT_DIR / "nas_spring_dance_2026_contact_segments.csv"
CAMPAIGN_PATH = OUTPUT_DIR / "nas_spring_dance_2026_marketing_campaign.md"


ATTENDANCE_SHEETS = ["12PM Attendees", "2PM Attendees"]
DATA_COLS = 9


@dataclass
class StudentRecord:
    source_sheet: str
    source_row: int
    student_last: str
    student_first: str
    session: str
    grade: str
    teacher: str
    payer_name: str
    payer_email: str
    payment_status: str
    note: str
    attended: bool
    fill_signature: str


def normalize(value) -> str:
    return str(value).strip() if value is not None else ""


def row_attended(ws, row_index: int) -> tuple[bool, str]:
    fills = []
    for col in range(1, DATA_COLS + 1):
        cell = ws.cell(row_index, col)
        fill = cell.fill
        color = fill.fgColor.rgb or fill.fgColor.indexed or fill.fgColor.type
        fills.append((fill.patternType, color))
    signature = Counter(fills).most_common(1)[0][0]
    attended = any(pattern == "solid" and color != "00000000" for pattern, color in fills)
    return attended, f"{signature[0]}:{signature[1]}"


def load_records(path: Path) -> list[StudentRecord]:
    wb = load_workbook(path)
    records: list[StudentRecord] = []
    for sheet_name in ATTENDANCE_SHEETS:
        ws = wb[sheet_name]
        for row_idx in range(2, ws.max_row + 1):
            values = [ws.cell(row_idx, col).value for col in range(1, DATA_COLS + 1)]
            if not any(value is not None for value in values):
                continue
            attended, fill_signature = row_attended(ws, row_idx)
            records.append(
                StudentRecord(
                    source_sheet=sheet_name,
                    source_row=row_idx,
                    student_last=normalize(values[0]),
                    student_first=normalize(values[1]),
                    session=normalize(values[2]),
                    grade=normalize(values[3]),
                    teacher=normalize(values[4]),
                    payer_name=normalize(values[5]),
                    payer_email=normalize(values[6]).lower(),
                    payment_status=normalize(values[7]),
                    note=normalize(values[8]),
                    attended=attended,
                    fill_signature=fill_signature,
                )
            )
    return records


def pct(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 1) if denominator else 0.0


def group_stats(records: list[StudentRecord], key_fn):
    grouped: dict[str, list[StudentRecord]] = defaultdict(list)
    for record in records:
        grouped[key_fn(record)].append(record)
    rows = []
    for key, group in grouped.items():
        total = len(group)
        attended = sum(1 for row in group if row.attended)
        rows.append((key, total, attended, pct(attended, total)))
    rows.sort(key=lambda item: (-item[2], item[0]))
    return rows


def build_contact_segments(records: list[StudentRecord]) -> list[dict[str, str]]:
    contacts: dict[str, dict] = {}
    for record in records:
        key = record.payer_email or f"name:{record.payer_name}"
        if key not in contacts:
            contacts[key] = {
                "payer_name": record.payer_name,
                "payer_email": record.payer_email,
                "students": [],
                "sessions": Counter(),
                "grades": Counter(),
                "payment_statuses": Counter(),
                "notes": [],
                "attended_students": 0,
                "noshow_students": 0,
            }
        contact = contacts[key]
        contact["students"].append(f"{record.student_first} {record.student_last}")
        contact["sessions"][record.session] += 1
        contact["grades"][record.grade] += 1
        contact["payment_statuses"][record.payment_status] += 1
        if record.note:
            contact["notes"].append(record.note)
        if record.attended:
            contact["attended_students"] += 1
        else:
            contact["noshow_students"] += 1

    rows = []
    for key, contact in sorted(
        contacts.items(), key=lambda item: (item[1]["payer_name"], item[1]["payer_email"])
    ):
        attended = contact["attended_students"]
        noshow = contact["noshow_students"]
        total = attended + noshow
        if attended and not noshow:
            segment = "Attended - Multi Student" if total > 1 else "Attended - Single Student"
            recommended_message = (
                "Thank-you + photos + stay-connected invite + early access to next event"
            )
        elif noshow and not attended:
            segment = "No Show"
            recommended_message = "Sorry we missed you + recap + invitation to future events"
        else:
            segment = "Mixed Household"
            recommended_message = "Thanks for attending + mention flexible options for next event"

        rows.append(
            {
                "segment": segment,
                "payer_name": contact["payer_name"],
                "payer_email": contact["payer_email"],
                "student_names": "; ".join(sorted(contact["students"])),
                "student_count": str(total),
                "attended_students": str(attended),
                "noshow_students": str(noshow),
                "sessions": "; ".join(
                    f"{session} ({count})" for session, count in sorted(contact["sessions"].items())
                ),
                "grades": "; ".join(
                    f"{grade} ({count})" for grade, count in sorted(contact["grades"].items())
                ),
                "payment_statuses": "; ".join(
                    f"{status} ({count})"
                    for status, count in sorted(contact["payment_statuses"].items())
                    if status
                ),
                "notes": " | ".join(contact["notes"]),
                "recommended_message": recommended_message,
            }
        )
    return rows


def write_segments_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "segment",
        "payer_name",
        "payer_email",
        "student_names",
        "student_count",
        "attended_students",
        "noshow_students",
        "sessions",
        "grades",
        "payment_statuses",
        "notes",
        "recommended_message",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, records: list[StudentRecord], segment_rows: list[dict[str, str]]) -> None:
    raw_total = len(records)
    raw_attended = sum(1 for record in records if record.attended)
    raw_noshow = raw_total - raw_attended

    duplicate_rows = defaultdict(list)
    for record in records:
        key = (record.student_last, record.student_first, record.session)
        duplicate_rows[key].append(record)
    duplicate_rows = {key: rows for key, rows in duplicate_rows.items() if len(rows) > 1}

    session_rows = group_stats(records, lambda row: row.session)
    grade_rows = group_stats(records, lambda row: row.grade)
    teacher_rows = group_stats(records, lambda row: row.teacher)[:12]

    no_show_rows = [row for row in records if not row.attended]
    no_show_by_session = group_stats(no_show_rows, lambda row: row.session)
    no_show_by_grade = group_stats(no_show_rows, lambda row: row.grade)

    all_attended_contacts = sum(1 for row in segment_rows if row["segment"].startswith("Attended"))
    no_show_contacts = sum(1 for row in segment_rows if row["segment"] == "No Show")
    multi_student_attended_contacts = sum(
        1 for row in segment_rows if row["segment"] == "Attended - Multi Student"
    )

    lines = [
        "# NAS Spring Dance 2026 Final Attendance Summary",
        "",
        "## Attendance Snapshot",
        f"- Student rows on attendance tabs: {raw_total}",
        f"- Marked attended (non-white highlight): {raw_attended}",
        f"- Marked no-show (white rows): {raw_noshow}",
        f"- Row-level attendance rate: {pct(raw_attended, raw_total)}%",
        "",
        "## Session Performance",
    ]
    for session, total, attended, rate in session_rows:
        lines.append(f"- {session}: {attended}/{total} attended ({rate}%)")

    lines += [
        "",
        "## Grade Performance",
    ]
    for grade, total, attended, rate in grade_rows:
        lines.append(f"- {grade}: {attended}/{total} attended ({rate}%)")

    lines += [
        "",
        "## Highest-Attendance Teacher Groups",
    ]
    for teacher, total, attended, rate in teacher_rows:
        lines.append(f"- {teacher}: {attended}/{total} attended ({rate}%)")

    lines += [
        "",
        "## Contact Segments",
        f"- Household contacts with at least one attendee: {all_attended_contacts}",
        f"- Household contacts with no attendees: {no_show_contacts}",
        f"- Multi-student attendee households: {multi_student_attended_contacts}",
        "",
        "## No-Show Breakdown",
    ]
    for session, total, attended, rate in no_show_by_session:
        lines.append(f"- {session}: {total} no-show rows")
    for grade, total, attended, rate in no_show_by_grade:
        lines.append(f"- {grade}: {total} no-show rows")

    lines += [
        "",
        "## Data Notes",
        "- Attendance appears to be tracked on the `12PM Attendees` and `2PM Attendees` sheets via row fill color.",
        "- This summary treats any non-white fill on the first 9 columns as attended.",
        "- Three duplicate student names were already present in the source export: Carla Lopez Santana, Vivian Lynn, and Teresa Ridgway.",
        "- One additional manual row was added for Jasania Roane with a note about an onsite payment and an unregistered niece.",
        "",
        "## Duplicate Rows Found",
    ]
    for key, rows in sorted(duplicate_rows.items()):
        lines.append(f"- {key[1]} {key[0]} ({key[2]}): {len(rows)} rows")
        for row in rows:
            note_text = f" | note: {row.note}" if row.note else ""
            lines.append(
                f"  - {row.source_sheet} row {row.source_row} | payer: {row.payer_name} | email: {row.payer_email or 'n/a'}{note_text}"
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_campaign_brief(path: Path, records: list[StudentRecord], segment_rows: list[dict[str, str]]) -> None:
    raw_total = len(records)
    raw_attended = sum(1 for record in records if record.attended)
    raw_noshow = raw_total - raw_attended

    by_grade = group_stats(records, lambda row: row.grade)
    by_session = group_stats(records, lambda row: row.session)

    attended_single = sum(1 for row in segment_rows if row["segment"] == "Attended - Single Student")
    attended_multi = sum(1 for row in segment_rows if row["segment"] == "Attended - Multi Student")
    no_show = sum(1 for row in segment_rows if row["segment"] == "No Show")

    best_grade = by_grade[0][0] if by_grade else "Kindergarten"

    lines = [
        "# NAS Spring Dance 2026 Marketing Campaign",
        "",
        "## Goals",
        "- Keep families warm between events.",
        "- Turn dance attendees into repeat PTO/event participants.",
        "- Recover goodwill and future attendance from the small no-show group.",
        "- Convert event buyers into an opt-in family-events list you can reuse later.",
        "",
        "## What The Attendance Data Suggests",
        f"- Overall turnout was strong: {raw_attended}/{raw_total} rows attended ({pct(raw_attended, raw_total)}%).",
        f"- The best turnout came from {best_grade}, so that is your strongest engagement pool for future family events.",
    ]
    for session, total, attended, rate in by_session:
        lines.append(f"- {session} performed at {rate}% attendance, so neither session needs a major messaging overhaul.")
    lines += [
        f"- You have {attended_multi} multi-student attendee households; these are strong candidates for ambassador-style messaging because they already engage at a family level.",
        f"- The no-show pool is small ({no_show} households), which makes personalized recovery outreach realistic.",
        "",
        "## Audience Segments",
        f"- Attended - Single Student: {attended_single} contacts",
        f"- Attended - Multi Student: {attended_multi} contacts",
        f"- No Show: {no_show} contacts",
        "",
        "## Recommended Campaign",
        "### 1. Attendee Thank-You Campaign",
        "Timing: 2 to 4 days after the event",
        "Audience: Attended - Single Student + Attended - Multi Student",
        "Message angle: gratitude, community, and light momentum into the next family event.",
        "Suggested subject lines:",
        '- "Thanks for coming to the Spring Dance"',
        '- "We loved seeing your family at the dance"',
        '- "Thanks for being part of the Spring Dance"',
        "Suggested CTA: invite them to join or stay on a family-events / PTO updates list.",
        "",
        "### 2. Attendee Recap + Stay-Connected Campaign",
        "Timing: 7 to 10 days after the event",
        "Audience: Attended households",
        "Message angle: photo recap, highlights, and a low-friction stay-in-touch ask.",
        "Suggested subject lines:",
        '- "Spring Dance highlights + what\'s next"',
        '- "A few favorite moments from the dance"',
        '- "Stay in the loop for the next family event"',
        "Suggested CTA: sign up for future event emails, follow the PTO page, or volunteer interest form.",
        "",
        "### 3. No-Show Recovery Campaign",
        "Timing: 3 to 7 days after the event",
        "Audience: No Show",
        "Message angle: warm, not guilty. Emphasize that you missed them, share a quick recap, and give them a reason to stay connected for the next event.",
        "Suggested subject lines:",
        '- "Sorry we missed you at the Spring Dance"',
        '- "We missed your family at the dance"',
        '- "Want to hear about the next family event?"',
        "Suggested CTA: join the future events list so they catch the next one early.",
        "",
        "### 4. Next-Event Early Access Campaign",
        "Timing: 3 to 6 weeks before your next family event",
        "Audience: everyone, with an optional first send to attendees",
        "Message angle: attendees get early access because they already showed up; no-shows get a friendly fresh start.",
        "Suggested subject lines:",
        '- "Early access for our family event list"',
        '- "Be the first to hear about the next school event"',
        '- "Next event coming soon"',
        "",
        "## Suggested Cadence",
        "- Email 1: Thank-you or no-show recovery",
        "- Email 2: Recap + stay-connected invite",
        "- Email 3: Early notice for the next event",
        "",
        "## Messaging Notes By Segment",
        "- Attended - Single Student: keep it simple and warm; the main goal is repeat participation.",
        "- Attended - Multi Student: mention family participation and invite them to volunteer, sponsor, or spread the word next time.",
        "- No Show: do not lean on pressure; use a recap plus future value.",
        "",
        "## Best Next Step",
        "- Export the `nas_spring_dance_2026_contact_segments.csv` file into your email platform and send one thank-you campaign to the two attendee segments, then a separate no-show recovery email to the 17 no-show households.",
        "",
        "## Compliance Note",
        "- Since these contacts came from an event purchase workflow, keep the outreach clearly tied to school/PTO events and include a simple opt-in or unsubscribe path before expanding into broader ongoing marketing.",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    records = load_records(WORKBOOK_PATH)
    segments = build_contact_segments(records)
    write_segments_csv(SEGMENTS_PATH, segments)
    write_summary(SUMMARY_PATH, records, segments)
    write_campaign_brief(CAMPAIGN_PATH, records, segments)
    print(SUMMARY_PATH)
    print(SEGMENTS_PATH)
    print(CAMPAIGN_PATH)


if __name__ == "__main__":
    main()
