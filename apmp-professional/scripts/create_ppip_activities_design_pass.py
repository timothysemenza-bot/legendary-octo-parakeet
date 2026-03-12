from __future__ import annotations

import shutil
from pathlib import Path

import pythoncom
import win32com.client as win32


ROOT = Path(r"C:\Users\timot\Documents\Proposal-Microsite")
SOURCE_PPT = ROOT / "apmp-professional" / "deliverables" / "Timothy Semenza APMP Professional PPIP Draft.pptx"
ARCHIVE_ROOT = ROOT / "apmp-professional" / "archive" / "deliverables"
DESIGN_PASS_DIR = ARCHIVE_ROOT / "design-pass"
DESIGN_PASS_PPT = DESIGN_PASS_DIR / "Timothy Semenza APMP Professional PPIP Draft.activities-results-visual-pass.pptx"
PREVIEW_DIR = DESIGN_PASS_DIR / "preview"


def rgb(red: int, green: int, blue: int) -> int:
    return red + (green * 256) + (blue * 65536)


def add_textbox(slide, left, top, width, height, text, font_size, bold=False, color=None):
    textbox = slide.Shapes.AddTextbox(1, left, top, width, height)
    text_range = textbox.TextFrame.TextRange
    text_range.Text = text
    text_range.Font.Size = font_size
    text_range.Font.Bold = -1 if bold else 0
    if color is not None:
        text_range.Font.Color.RGB = color
    textbox.TextFrame.WordWrap = -1
    textbox.TextFrame.MarginLeft = 6
    textbox.TextFrame.MarginRight = 6
    textbox.TextFrame.MarginTop = 4
    textbox.TextFrame.MarginBottom = 4
    return textbox


def add_card(slide, left, top, width, height, day_range, title, lines, fill_color, accent_color):
    unit = 72
    card = slide.Shapes.AddShape(5, left, top, width, height)
    card.Fill.ForeColor.RGB = fill_color
    card.Line.ForeColor.RGB = accent_color
    card.Line.Weight = 1.5

    chip = slide.Shapes.AddShape(5, left + 0.14 * unit, top - 0.34 * unit, width - 0.28 * unit, 0.28 * unit)
    chip.Fill.ForeColor.RGB = accent_color
    chip.Line.Visible = 0
    chip.TextFrame.TextRange.Text = f"{day_range}"
    chip.TextFrame.TextRange.Font.Size = 10
    chip.TextFrame.TextRange.Font.Bold = -1
    chip.TextFrame.TextRange.Font.Color.RGB = rgb(255, 255, 255)
    chip.TextFrame.MarginLeft = 8
    chip.TextFrame.MarginRight = 8
    chip.TextFrame.MarginTop = 2

    title_box = add_textbox(
        slide,
        left + 0.12 * unit,
        top + 0.42 * unit,
        width - 0.24 * unit,
        0.22 * unit,
        title,
        12,
        bold=True,
        color=rgb(35, 73, 126),
    )
    title_box.Line.Visible = 0
    title_box.Fill.Visible = 0

    body_text = "\r".join([f"- {line}" for line in lines])
    body_box = add_textbox(
        slide,
        left + 0.12 * unit,
        top + 0.96 * unit,
        width - 0.24 * unit,
        height - 1.06 * unit,
        body_text,
        10,
        bold=False,
        color=rgb(45, 45, 45),
    )
    body_box.Line.Visible = 0
    body_box.Fill.Visible = 0


def add_result_card(slide, left, top, width, height, metric, baseline, result, evidence, accent_color):
    unit = 72
    card = slide.Shapes.AddShape(5, left, top, width, height)
    card.Fill.ForeColor.RGB = rgb(248, 249, 252)
    card.Line.ForeColor.RGB = accent_color
    card.Line.Weight = 1.5

    chip = slide.Shapes.AddShape(5, left + 0.12 * unit, top + 0.08 * unit, width - 0.24 * unit, 0.26 * unit)
    chip.Fill.ForeColor.RGB = accent_color
    chip.Line.Visible = 0
    chip.TextFrame.TextRange.Text = metric
    chip.TextFrame.TextRange.Font.Size = 10
    chip.TextFrame.TextRange.Font.Bold = -1
    chip.TextFrame.TextRange.Font.Color.RGB = rgb(255, 255, 255)
    chip.TextFrame.MarginLeft = 8
    chip.TextFrame.MarginRight = 8
    chip.TextFrame.MarginTop = 2

    baseline_label = add_textbox(
        slide,
        left + 0.14 * unit,
        top + 0.46 * unit,
        0.90 * unit,
        0.18 * unit,
        "Baseline",
        8,
        bold=True,
        color=rgb(112, 112, 112),
    )
    baseline_label.Line.Visible = 0
    baseline_label.Fill.Visible = 0

    baseline_box = add_textbox(
        slide,
        left + 0.14 * unit,
        top + 0.62 * unit,
        width - 0.28 * unit,
        0.34 * unit,
        baseline,
        8.5,
        bold=False,
        color=rgb(60, 60, 60),
    )
    baseline_box.Line.Visible = 0
    baseline_box.Fill.Visible = 0

    result_label = add_textbox(
        slide,
        left + 0.14 * unit,
        top + 0.98 * unit,
        0.90 * unit,
        0.18 * unit,
        "Result",
        8,
        bold=True,
        color=accent_color,
    )
    result_label.Line.Visible = 0
    result_label.Fill.Visible = 0

    result_box = add_textbox(
        slide,
        left + 0.14 * unit,
        top + 1.14 * unit,
        width - 0.28 * unit,
        0.44 * unit,
        result,
        9.5,
        bold=True,
        color=rgb(35, 73, 126),
    )
    result_box.Line.Visible = 0
    result_box.Fill.Visible = 0

    evidence_line = slide.Shapes.AddLine(left + 0.14 * unit, top + 1.62 * unit, left + width - 0.14 * unit, top + 1.62 * unit)
    evidence_line.Line.ForeColor.RGB = rgb(215, 220, 230)
    evidence_line.Line.Weight = 1

    evidence_label = add_textbox(
        slide,
        left + 0.14 * unit,
        top + 1.68 * unit,
        1.10 * unit,
        0.18 * unit,
        "Measured by",
        8,
        bold=True,
        color=rgb(112, 112, 112),
    )
    evidence_label.Line.Visible = 0
    evidence_label.Fill.Visible = 0

    evidence_box = add_textbox(
        slide,
        left + 0.14 * unit,
        top + 1.84 * unit,
        width - 0.28 * unit,
        0.24 * unit,
        evidence,
        8,
        bold=False,
        color=rgb(70, 70, 70),
    )
    evidence_box.Line.Visible = 0
    evidence_box.Fill.Visible = 0


def redesign_activities_slide(ppt_path: Path) -> None:
    pythoncom.CoInitialize()
    app = win32.Dispatch("PowerPoint.Application")
    presentation = app.Presentations.Open(str(ppt_path), WithWindow=False)

    try:
        slide = presentation.Slides(6)

        # Remove the existing activity table but preserve the title, opener, and footer text.
        for shape_index in range(slide.Shapes.Count, 0, -1):
            shape = slide.Shapes(shape_index)
            if shape.Type == 19:
                shape.Delete()

        timeline_left = 0.82 * 72
        timeline_top = 2.20 * 72
        card_width = 2.18 * 72
        card_height = 2.70 * 72
        gap = 0.12 * 72

        guide = slide.Shapes.AddLine(timeline_left + 0.20 * 72, timeline_top + 0.24 * 72, timeline_left + (card_width * 5) + (gap * 4) - 0.20 * 72, timeline_top + 0.24 * 72)
        guide.Line.ForeColor.RGB = rgb(171, 186, 208)
        guide.Line.Weight = 1.25

        fill_color = rgb(248, 249, 252)
        accent_colors = [
            rgb(31, 78, 121),
            rgb(0, 112, 192),
            rgb(45, 140, 175),
            rgb(89, 89, 89),
            rgb(41, 128, 185),
        ]

        cards = [
            ("Day 1", "Plan", ["Auto-build schedule", "Issue project plan", "Set review cadence"]),
            ("Days 1-5", "Align", ["Kickoff around customer", "Research evaluators", "Build compliance matrix"]),
            ("Days 6-12", "Build", ["Draft sections", "Integrate consultant", "Run QA and reviews"]),
            ("Days 13-20", "Submit", ["Package final files", "Align executives", "Protect handoff and submit"]),
            ("Post-submission", "Present", ["Prepare slide story", "Draft Q&A and notes", "Support 2 finalist rounds"]),
        ]

        for index, (day_range, title, lines) in enumerate(cards, start=1):
            left = timeline_left + (index - 1) * (card_width + gap)
            add_card(
                slide,
                left,
                timeline_top + 0.42 * 72,
                card_width,
                card_height,
                day_range,
                title,
                lines,
                fill_color,
                accent_colors[index - 1],
            )

        headline = add_textbox(
            slide,
            0.86 * 72,
            5.55 * 72,
            11.2 * 72,
            0.42 * 72,
            "Five operating checkpoints replaced a dense activity table and show how governance moved from planning to finalist delivery.",
            12,
            bold=False,
            color=rgb(35, 73, 126),
        )
        headline.Line.Visible = 0
        headline.Fill.Visible = 0

        presentation.Save()
    finally:
        presentation.Close()
        app.Quit()


def redesign_results_slide(ppt_path: Path) -> None:
    pythoncom.CoInitialize()
    app = win32.Dispatch("PowerPoint.Application")
    presentation = app.Presentations.Open(str(ppt_path), WithWindow=False)

    try:
        slide = presentation.Slides(7)

        for shape_index in range(slide.Shapes.Count, 0, -1):
            shape = slide.Shapes(shape_index)
            delete_shape = shape.Type == 19
            if not delete_shape:
                try:
                    if shape.HasTextFrame and shape.TextFrame.HasText:
                        text = shape.TextFrame.TextRange.Text
                        if "Later school bids shifted toward" in text or "Final award result is unknown" in text:
                            delete_shape = True
                except Exception:
                    pass
            if delete_shape:
                shape.Delete()

        unit = 72
        left_margin = 0.82 * unit
        top_margin = 2.00 * unit
        card_width = 5.52 * unit
        card_height = 2.12 * unit
        gap_x = 0.20 * unit
        gap_y = 0.16 * unit

        cards = [
            (
                "Finalist progression",
                "No assured advancement from an unprepared start",
                "Reached 2 finalist presentations",
                "Invitations to 2 finalist rounds",
                rgb(31, 78, 121),
            ),
            (
                "Reusable bid base",
                "Each school bid rebuilt structure and messaging",
                "About 12 later RNA school bids reused Detroit assets, with about 6 active at once",
                "Observed live reuse across later school-bid production",
                rgb(0, 112, 192),
            ),
            (
                "First-draft speed",
                "About 4 hours to reach a first compliant draft",
                "An about 80% draft could be reached in roughly 5 minutes before tailoring",
                "Compared live prep effort on later similar bids",
                rgb(45, 140, 175),
            ),
            (
                "Executive review burden",
                "Repeated review of unfamiliar writing and structure",
                "Later bids usually needed 1 executive review focused on solution and pricing differences",
                "Observed post-Detroit review pattern with executives and pricing",
                rgb(89, 89, 89),
            ),
        ]

        positions = [
            (left_margin, top_margin),
            (left_margin + card_width + gap_x, top_margin),
            (left_margin, top_margin + card_height + gap_y),
            (left_margin + card_width + gap_x, top_margin + card_height + gap_y),
        ]

        for (metric, baseline, result, evidence, accent_color), (left, top) in zip(cards, positions):
            add_result_card(slide, left, top, card_width, card_height, metric, baseline, result, evidence, accent_color)

        presentation.Save()
    finally:
        presentation.Close()
        app.Quit()


def export_preview(ppt_path: Path) -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    pythoncom.CoInitialize()
    app = win32.Dispatch("PowerPoint.Application")
    presentation = app.Presentations.Open(str(ppt_path), WithWindow=False)
    try:
        for slide_number in range(1, presentation.Slides.Count + 1):
            target = PREVIEW_DIR / f"Slide{slide_number}.PNG"
            presentation.Slides(slide_number).Export(str(target), "PNG")
    finally:
        presentation.Close()
        app.Quit()


def main() -> None:
    DESIGN_PASS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_PPT, DESIGN_PASS_PPT)
    redesign_activities_slide(DESIGN_PASS_PPT)
    redesign_results_slide(DESIGN_PASS_PPT)
    export_preview(DESIGN_PASS_PPT)
    print(f"Created design-pass copy: {DESIGN_PASS_PPT}")
    print(f"Exported previews to: {PREVIEW_DIR}")


if __name__ == "__main__":
    main()
