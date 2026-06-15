from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    heading: str | None
    text: str
    start_line: int
    end_line: int


def chunk_markdown(text: str, *, target_lines: int = 45, overlap_lines: int = 5) -> list[Chunk]:
    lines = text.splitlines()
    sections = _split_heading_sections(lines)
    chunks: list[Chunk] = []

    for heading, start_index, end_index in sections:
        section_lines = lines[start_index:end_index]
        if not section_lines:
            continue

        offset = 0
        while offset < len(section_lines):
            window_end = min(offset + target_lines, len(section_lines))
            chunk_lines = section_lines[offset:window_end]
            chunk_text = "\n".join(chunk_lines).strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        ordinal=len(chunks),
                        heading=heading,
                        text=chunk_text,
                        start_line=start_index + offset + 1,
                        end_line=start_index + window_end,
                    )
                )
            if window_end == len(section_lines):
                break
            offset = max(window_end - overlap_lines, offset + 1)

    if chunks:
        return chunks

    stripped = text.strip()
    if not stripped:
        return []
    return [Chunk(ordinal=0, heading=None, text=stripped, start_line=1, end_line=len(lines))]


def chunks_from_boundaries(
    text: str,
    boundaries: list[tuple[str | None, int, int]],
) -> list[Chunk]:
    lines = text.splitlines()
    chunks: list[Chunk] = []

    for title, start_line, end_line in boundaries:
        if start_line < 1 or end_line < start_line or end_line > len(lines):
            raise ValueError(f"Invalid chunk boundary: {start_line}-{end_line}")
        chunk_text = "\n".join(lines[start_line - 1 : end_line]).strip()
        if not chunk_text:
            continue
        chunks.append(
            Chunk(
                ordinal=len(chunks),
                heading=title,
                text=chunk_text,
                start_line=start_line,
                end_line=end_line,
            )
        )

    if not chunks:
        raise ValueError("LLM chunk planner returned no usable chunks")
    return chunks


def _split_heading_sections(lines: list[str]) -> list[tuple[str | None, int, int]]:
    sections: list[tuple[str | None, int, int]] = []
    current_heading: str | None = None
    current_start = 0

    for index, line in enumerate(lines):
        if not line.startswith("#"):
            continue
        marker, _, title = line.partition(" ")
        if not marker or any(character != "#" for character in marker):
            continue
        if index > current_start:
            sections.append((current_heading, current_start, index))
        current_heading = title.strip() or line.strip()
        current_start = index

    if current_start < len(lines):
        sections.append((current_heading, current_start, len(lines)))

    return sections
