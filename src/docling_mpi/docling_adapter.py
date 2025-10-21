"""Adapter between the pipeline and the Docling processing library."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


try:  # pragma: no cover - optional dependency
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat, AnnotationSchema, Pipeline
except Exception:  # pragma: no cover - used when Docling is unavailable
    DocumentConverter = None  # type: ignore
    InputFormat = Any  # type: ignore
    AnnotationSchema = Any  # type: ignore
    Pipeline = Any  # type: ignore


@dataclass(frozen=True)
class DoclingResult:
    """Structured extraction output for a processed chunk."""

    chunk_id: str
    tables: List[Dict[str, Any]]
    text_blocks: List[str]
    images: List[bytes]

    def to_json(self) -> str:
        return json.dumps(
            {
                "chunk_id": self.chunk_id,
                "tables": self.tables,
                "text_blocks": self.text_blocks,
                "images": [image.hex() for image in self.images],
            }
        )


class DoclingProcessor:
    """Perform Docling-based extraction for a document chunk."""

    def __init__(
        self,
        annotations: str | None = None,
        pipeline: str | None = None,
    ) -> None:
        self._annotations = annotations
        self._pipeline = pipeline
        if DocumentConverter is not None:
            self._converter = DocumentConverter()
        else:  # pragma: no cover - only when Docling is absent
            self._converter = None

    def _ensure_available(self) -> None:
        if self._converter is None:
            raise RuntimeError(
                "Docling is not available. Install docling to enable processing."
            )

    def load(self, pdf_path: Path) -> Any:
        self._ensure_available()
        return self._converter.load_from(pdf_path)

    def count_pages(self, pdf_path: Path) -> int:
        self._ensure_available()
        document = self._converter.load_from(pdf_path)
        return len(document.pages)

    def process_chunk(self, pdf_path: Path, page_numbers: List[int]) -> DoclingResult:
        self._ensure_available()
        document = self._converter.load_from(pdf_path, page_indices=page_numbers)
        # The actual API shape depends on Docling internals. We keep this method
        # defensive and rely on duck typing to minimise breakage.
        tables: List[Dict[str, Any]] = []
        text_blocks: List[str] = []
        images: List[bytes] = []

        for page in getattr(document, "pages", []):
            tables.extend(getattr(page, "tables", []) or [])
            text_blocks.extend(getattr(page, "text_blocks", []) or [])
            images.extend(getattr(page, "images", []) or [])

        return DoclingResult(
            chunk_id=f"{pdf_path.stem}-p{'_'.join(map(str, page_numbers))}",
            tables=tables,
            text_blocks=text_blocks,
            images=images,
        )
