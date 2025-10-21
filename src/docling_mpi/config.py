"""Configuration dataclasses for the Docling MPI processing pipeline."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class StorageConfig:
    """Configuration for persistent artifact storage."""

    output_dir: Path
    ensure_clean: bool = False

    def prepare_output_dir(self) -> None:
        """Create the output directory, optionally cleaning it first."""
        if self.ensure_clean and self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class MonitoringConfig:
    """Configuration for metrics and health reporting."""

    enable_prometheus: bool = False
    prometheus_port: int = 8000


@dataclass(frozen=True)
class ProcessingConfig:
    """Configuration for the distributed PDF processing job."""

    pdf_paths: List[Path]
    chunk_size: int = 4
    broadcast_metadata: bool = True
    max_retries: int = 1
    storage: StorageConfig = field(default_factory=lambda: StorageConfig(Path("output")))
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    @classmethod
    def from_glob(cls, patterns: Iterable[str], **kwargs: object) -> "ProcessingConfig":
        """Create a configuration from one or more glob patterns."""
        paths: List[Path] = []
        for pattern in patterns:
            paths.extend(sorted(Path().glob(pattern)))
        unique_paths: List[Path] = sorted({path.resolve() for path in paths})
        if not unique_paths:
            raise ValueError("No PDF files matched the provided patterns")
        return cls(pdf_paths=unique_paths, **kwargs)

    def validate(self) -> None:
        """Validate configuration properties before running."""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        for pdf in self.pdf_paths:
            if not pdf.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf}")
        if self.monitoring.enable_prometheus and not (1024 <= self.monitoring.prometheus_port <= 65535):
            raise ValueError("prometheus_port must be within the range 1024-65535")
