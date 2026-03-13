from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "Rev-IQ_Mutual_NDA_Light_Redline_2026-03-13.html"
PDF_PATH = ROOT / "Rev-IQ_Mutual_NDA_Light_Redline_2026-03-13.pdf"


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    html = html_path.read_text(encoding="utf-8")
    story = fitz.Story(html=html)
    mediabox = fitz.paper_rect("letter")
    margin = 48
    where = fitz.Rect(margin, margin, mediabox.width - margin, mediabox.height - margin)
    writer = fitz.DocumentWriter(str(pdf_path))
    more = True
    while more:
        device = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()


if __name__ == "__main__":
    render_pdf(HTML_PATH, PDF_PATH)
    print(PDF_PATH)
