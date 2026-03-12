from __future__ import annotations

import re
import shutil
from pathlib import Path

import pythoncom
import win32com.client as win32


ROOT = Path(r"C:\Users\timot\Documents\Proposal-Microsite")
PPT_PATH = ROOT / "apmp-professional" / "deliverables" / "Timothy Semenza APMP Professional PPIP Draft.pptx"
TALK_TRACK_PATH = ROOT / "apmp-professional" / "working" / "ppip-talk-track.md"
BACKUP_DIR = ROOT / "apmp-professional" / "archive" / "deliverables" / "backups"


def parse_talk_track(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^## Slide (\d+) - (.+?)\nTarget time: (.+?)\n\n(.*?)(?=^## Slide |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    notes: list[dict[str, str]] = []
    for match in pattern.finditer(text):
        slide_number = int(match.group(1))
        slide_label = match.group(2).strip()
        target_time = match.group(3).strip()
        body = match.group(4).strip()
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        note_text = f"Target time: {target_time}\r\n\r\n" + "\r\n\r\n".join(paragraphs)
        notes.append(
            {
                "slide_number": slide_number,
                "slide_label": slide_label,
                "target_time": target_time,
                "note_text": note_text,
            }
        )
    return notes


def backup_presentation(path: Path) -> Path:
    stamp = path.stat().st_mtime_ns
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{path.stem}.backup-before-speaker-notes-{stamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def update_speaker_notes(ppt_path: Path, notes: list[dict[str, str]]) -> None:
    pythoncom.CoInitialize()
    app = win32.Dispatch("PowerPoint.Application")
    presentation = app.Presentations.Open(str(ppt_path), WithWindow=False)

    try:
        if presentation.Slides.Count != len(notes):
            raise ValueError(
                f"Talk track has {len(notes)} slides but presentation has {presentation.Slides.Count} slides."
            )

        for note in notes:
            slide = presentation.Slides(note["slide_number"])
            notes_page = slide.NotesPage
            notes_placeholder = None
            for shape in notes_page.Shapes:
                try:
                    if shape.PlaceholderFormat.Type == 2:
                        notes_placeholder = shape
                        break
                except Exception:
                    continue

            if notes_placeholder is None:
                raise RuntimeError(f"Could not find notes placeholder on slide {note['slide_number']}.")

            notes_placeholder.TextFrame.TextRange.Text = note["note_text"]

        presentation.Save()
    finally:
        presentation.Close()
        app.Quit()


def main() -> None:
    notes = parse_talk_track(TALK_TRACK_PATH)
    if not notes:
        raise ValueError(f"No talk track sections found in {TALK_TRACK_PATH}.")

    backup_path = backup_presentation(PPT_PATH)
    update_speaker_notes(PPT_PATH, notes)

    print(f"Backup created: {backup_path}")
    print(f"Speaker notes updated in: {PPT_PATH}")


if __name__ == "__main__":
    main()
