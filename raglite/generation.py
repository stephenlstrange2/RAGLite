from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class RetrievedChunk:
    path: str
    heading: str | None
    text: str
    start_line: int
    end_line: int


class OllamaGenerationError(RuntimeError):
    pass


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    provider = os.getenv("RAGLITE_GENERATION_PROVIDER", "ollama")
    if provider != "ollama":
        raise OllamaGenerationError(f"Unsupported generation provider: {provider}")

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("RAGLITE_GENERATION_MODEL", "llama3.1:8b")
    prompt = _build_prompt(question, chunks)

    try:
        response = httpx.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise OllamaGenerationError(
            f"Ollama generation failed for model {model}. "
            f"Run `task doctor` and `task ollama:pull` before asking questions."
        ) from error

    data = response.json()
    answer = data.get("response")
    if not isinstance(answer, str) or not answer.strip():
        raise OllamaGenerationError("Ollama returned an empty generation response")
    return answer.strip()


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        heading = f" heading={chunk.heading}" if chunk.heading else ""
        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] source={chunk.path}:{chunk.start_line}-{chunk.end_line}{heading}",
                    chunk.text,
                ]
            )
        )

    context = "\n\n---\n\n".join(context_blocks)
    return f"""You answer questions about a software project using only the provided context.

Rules:
- Be concise and technical.
- Cite sources inline using [number].
- If the context does not contain the answer, say what is missing.
- Distinguish documented facts from inference.

Question:
{question}

Context:
{context}

Answer:
"""
