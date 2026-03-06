from io import BytesIO


def extract_text_from_upload(filename: str, payload: bytes) -> str:
    lowered = filename.lower()
    if lowered.endswith(".txt") or lowered.endswith(".md"):
        return payload.decode("utf-8", errors="ignore")

    if lowered.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF parsing requires pypdf. Install pypdf to parse PDF files.") from exc

        reader = PdfReader(BytesIO(payload))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if lowered.endswith(".docx"):
        try:
            import docx
        except ImportError as exc:
            raise RuntimeError("DOCX parsing requires python-docx. Install python-docx.") from exc

        document = docx.Document(BytesIO(payload))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise RuntimeError("Unsupported file type. Use TXT, PDF, or DOCX.")

