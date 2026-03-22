from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import BASE_DIR


CONTENT_LIBRARY_JSON = BASE_DIR.parent / "content-library.json"
SAMPLE_CONTENT_DIR = BASE_DIR.parent / "sample-content"
SUPPORTED_BLOCK_EXTENSIONS = {".md", ".txt"}


@dataclass(frozen=True)
class ContentBlock:
    id: str
    title: str
    category: str
    tags: tuple[str, ...]
    body: str
    source_path: str


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", value.lower())
        if token not in {"with", "from", "into", "that", "this", "their", "they", "have"}
    }


def _clean_title(value: str) -> str:
    return re.sub(r"[_-]+", " ", value).strip().title()


def _add_block(blocks: list[ContentBlock], block_id: str, title: str, category: str, tags: list[str], body: str, source_path: str) -> None:
    normalized_body = body.strip()
    if not normalized_body:
        return
    blocks.append(
        ContentBlock(
            id=block_id,
            title=title,
            category=category,
            tags=tuple(tag for tag in tags if tag),
            body=normalized_body,
            source_path=source_path,
        )
    )


def _flatten_json_blocks(prefix: list[str], value: object, blocks: list[ContentBlock]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            _flatten_json_blocks(prefix + [str(key)], nested, blocks)
        return

    if isinstance(value, list):
        for index, nested in enumerate(value):
            _flatten_json_blocks(prefix + [str(index + 1)], nested, blocks)
        return

    if not isinstance(value, str):
        return

    path_tokens = [token for token in prefix if token.isidentifier() or token.replace("-", "").replace("_", "").isalnum()]
    if len(value.strip()) < 40 and "\n" not in value:
        return
    category = _clean_title(path_tokens[0]) if path_tokens else "Library"
    title = _clean_title(" ".join(path_tokens[-2:] or path_tokens or ["Content Block"]))
    block_id = "json-" + "-".join(token.lower().replace("_", "-") for token in path_tokens[-4:])
    _add_block(blocks, block_id, title, category, [token.lower() for token in path_tokens], value, CONTENT_LIBRARY_JSON.as_posix())


def _load_json_library() -> list[ContentBlock]:
    if not CONTENT_LIBRARY_JSON.exists():
        return []
    try:
        payload = json.loads(CONTENT_LIBRARY_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    blocks: list[ContentBlock] = []
    _flatten_json_blocks([], payload, blocks)
    return blocks


def _load_sample_content() -> list[ContentBlock]:
    if not SAMPLE_CONTENT_DIR.exists():
        return []

    blocks: list[ContentBlock] = []
    for file_path in SAMPLE_CONTENT_DIR.rglob("*"):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_BLOCK_EXTENSIONS:
            continue
        relative_parts = list(file_path.relative_to(SAMPLE_CONTENT_DIR).parts)
        if not relative_parts:
            continue
        stem = file_path.stem
        tags = [part.lower().replace("_", "-") for part in relative_parts[:-1]]
        category = _clean_title(relative_parts[0])
        title = _clean_title(" ".join(relative_parts[-2:-1] + [stem]))
        block_id = "sample-" + "-".join(part.lower().replace("_", "-") for part in relative_parts).replace(".", "-")
        _add_block(
            blocks,
            block_id,
            title,
            category,
            tags + [stem.lower().replace("_", "-")],
            file_path.read_text(encoding="utf-8", errors="ignore"),
            file_path.as_posix(),
        )
    return blocks


@lru_cache(maxsize=1)
def load_content_blocks() -> tuple[ContentBlock, ...]:
    blocks = _load_sample_content() + _load_json_library()
    deduped: dict[str, ContentBlock] = {}
    for block in blocks:
        deduped[block.id] = block
    return tuple(deduped.values())


def content_block_inventory() -> list[dict[str, object]]:
    return [
        {
            "block_id": block.id,
            "title": block.title,
            "category": block.category,
            "tags": list(block.tags),
            "source_path": block.source_path,
        }
        for block in load_content_blocks()
    ]


def select_candidate_blocks(*, section_name: str, requirement_texts: list[str], limit: int = 5) -> list[ContentBlock]:
    query_tokens = _tokenize(section_name)
    for text in requirement_texts:
        query_tokens.update(_tokenize(text))

    scored: list[tuple[int, int, ContentBlock]] = []
    for block in load_content_blocks():
        haystack = " ".join([block.title, block.category, " ".join(block.tags), block.body[:600]])
        block_tokens = _tokenize(haystack)
        overlap = len(query_tokens & block_tokens)
        if overlap == 0:
            continue
        section_boost = 2 if any(token in block_tokens for token in _tokenize(section_name)) else 0
        scored.append((overlap, section_boost, block))

    ranked = sorted(scored, key=lambda item: (-item[0], -item[1], item[2].title))
    return [block for _overlap, _boost, block in ranked[:limit]]

