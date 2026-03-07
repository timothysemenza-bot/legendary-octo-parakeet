import mimetypes
from dataclasses import dataclass
from io import BytesIO


SUPPORTED_UPLOAD_EXTENSIONS = (".txt", ".md", ".pdf", ".docx")


@dataclass
class BatchDocumentExtractionResult:
    combined_text: str
    parsed_files: list[str]
    skipped_files: list[str]
    warnings: list[str]
    source_filename: str
    documents: list["SourceDocumentExtractionRecord"]


@dataclass
class SourceDocumentExtractionRecord:
    source_filename: str
    content_type: str
    parse_status: str
    skip_reason: str | None
    upload_order: int
    source_size_bytes: int
    extracted_text_length: int
    content_text: str | None
    source_sha256: str | None
    storage_path: str | None
    source_payload: bytes | None


def _guess_content_type(filename: str) -> str:
    guessed, _encoding = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


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

    raise RuntimeError("Unsupported file type. Use TXT, MD, PDF, or DOCX.")


def extract_text_from_upload_batch(files: list[tuple[str, bytes]]) -> BatchDocumentExtractionResult:
    parsed_files: list[str] = []
    skipped_files: list[str] = []
    warnings: list[str] = []
    combined_parts: list[str] = []
    documents: list[SourceDocumentExtractionRecord] = []

    for upload_order, (filename, payload) in enumerate(files, start=1):
        content_type = _guess_content_type(filename)
        try:
            content = extract_text_from_upload(filename, payload)
        except RuntimeError as exc:
            skipped_files.append(filename)
            skip_reason = str(exc)
            warnings.append(f"{filename}: {skip_reason}")
            documents.append(
                SourceDocumentExtractionRecord(
                    source_filename=filename,
                    content_type=content_type,
                    parse_status="SKIPPED",
                    skip_reason=skip_reason,
                    upload_order=upload_order,
                    source_size_bytes=len(payload),
                    extracted_text_length=0,
                    content_text=None,
                    source_sha256=None,
                    storage_path=None,
                    source_payload=payload,
                )
            )
            continue

        normalized = content.strip()
        if len(normalized) < 20:
            skipped_files.append(filename)
            skip_reason = "extracted content is too short to parse."
            warnings.append(f"{filename}: {skip_reason}")
            documents.append(
                SourceDocumentExtractionRecord(
                    source_filename=filename,
                    content_type=content_type,
                    parse_status="SKIPPED",
                    skip_reason=skip_reason,
                    upload_order=upload_order,
                    source_size_bytes=len(payload),
                    extracted_text_length=len(normalized),
                    content_text=None,
                    source_sha256=None,
                    storage_path=None,
                    source_payload=payload,
                )
            )
            continue

        parsed_files.append(filename)
        combined_parts.append(f"Source file: {filename}\n{normalized}")
        documents.append(
            SourceDocumentExtractionRecord(
                source_filename=filename,
                content_type=content_type,
                parse_status="PARSED",
                skip_reason=None,
                upload_order=upload_order,
                source_size_bytes=len(payload),
                extracted_text_length=len(normalized),
                content_text=normalized,
                source_sha256=None,
                storage_path=None,
                source_payload=payload,
            )
        )

    parsed_count = len(parsed_files)
    return BatchDocumentExtractionResult(
        combined_text="\n\n".join(combined_parts),
        parsed_files=parsed_files,
        skipped_files=skipped_files,
        warnings=warnings,
        source_filename=f"intake-batch-{parsed_count}-files.txt",
        documents=documents,
    )
