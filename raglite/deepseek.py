from __future__ import annotations

import json
import os
from typing import Any

import httpx


class DeepSeekChunkingError(RuntimeError):
    pass


def plan_chunks_with_deepseek(
    path: str,
    text: str,
    *,
    target_lines: int = 45,
    max_lines: int = 75,
) -> list[tuple[str | None, int, int]]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekChunkingError("DEEPSEEK_API_KEY is required for DeepSeek chunking")

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("RAGLITE_CHUNK_LLM_MODEL", "deepseek-chat")
    numbered_text = _line_numbered_text(text)

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You propose chunk boundaries for documentation retrieval. "
                    "Return valid JSON only. Do not rewrite source text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Source path: {path}\n"
                    f"Target chunk size: {target_lines} lines\n"
                    f"Maximum chunk size: {max_lines} lines\n\n"
                    "Return JSON with this schema:\n"
                    '{"chunks":[{"title":"short title","start_line":1,"end_line":20}]}\n\n'
                    "Line-numbered document:\n"
                    f"{numbered_text}"
                ),
            },
        ],
    }

    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise DeepSeekChunkingError(f"DeepSeek chunk planning failed for {path}") from error

    content = _extract_content(response.json())
    return _parse_boundaries(content, total_lines=len(text.splitlines()), max_lines=max_lines)


def _extract_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise DeepSeekChunkingError("DeepSeek response did not contain message content") from error
    if not isinstance(content, str):
        raise DeepSeekChunkingError("DeepSeek message content was not a string")
    return content


def _parse_boundaries(
    content: str,
    *,
    total_lines: int,
    max_lines: int,
) -> list[tuple[str | None, int, int]]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise DeepSeekChunkingError("DeepSeek returned invalid JSON") from error

    raw_chunks = data.get("chunks")
    if not isinstance(raw_chunks, list):
        raise DeepSeekChunkingError("DeepSeek JSON did not contain a chunks array")

    boundaries: list[tuple[str | None, int, int]] = []
    previous_end = 0
    for raw_chunk in raw_chunks:
        if not isinstance(raw_chunk, dict):
            raise DeepSeekChunkingError("DeepSeek chunk entry was not an object")
        title = raw_chunk.get("title")
        start_line = raw_chunk.get("start_line")
        end_line = raw_chunk.get("end_line")
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            raise DeepSeekChunkingError("DeepSeek chunk lines must be integers")
        if start_line < 1 or end_line < start_line or end_line > total_lines:
            raise DeepSeekChunkingError(f"DeepSeek returned invalid boundary {start_line}-{end_line}")
        if end_line - start_line + 1 > max_lines:
            raise DeepSeekChunkingError(f"DeepSeek returned oversized boundary {start_line}-{end_line}")
        if start_line <= previous_end:
            raise DeepSeekChunkingError("DeepSeek returned overlapping or unsorted boundaries")
        previous_end = end_line
        boundaries.append((title if isinstance(title, str) else None, start_line, end_line))

    if not boundaries:
        raise DeepSeekChunkingError("DeepSeek returned no chunk boundaries")
    return boundaries


def _line_numbered_text(text: str) -> str:
    return "\n".join(f"{line_number}: {line}" for line_number, line in enumerate(text.splitlines(), 1))
