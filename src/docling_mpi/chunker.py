"""Utilities for splitting PDF documents into processing chunks."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List


@dataclass(frozen=True)
class DocumentChunk:
    """A single chunk of a PDF document."""

    pdf_path: Path
    page_numbers: List[int]

    @property
    def id(self) -> str:
        joined = "_".join(str(page) for page in self.page_numbers)
        return f"{self.pdf_path.stem}-p{joined}"


class Chunker:
    """Split PDF documents into fixed-size page chunks."""

    def __init__(self, chunk_size: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self._chunk_size = chunk_size

    def chunk(self, pdf_path: Path, total_pages: int) -> Iterator[DocumentChunk]:
        pages = list(range(total_pages))
        for index in range(0, len(pages), self._chunk_size):
            yield DocumentChunk(pdf_path=pdf_path, page_numbers=pages[index:index + self._chunk_size])

    def chunk_multiple(self, documents: Iterable[tuple[Path, int]]) -> Iterator[DocumentChunk]:
        for path, pages in documents:
            yield from self.chunk(path, pages)
