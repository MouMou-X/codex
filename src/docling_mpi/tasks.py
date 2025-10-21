"""Task definitions for MPI-based document processing."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional

from .chunker import DocumentChunk


class TaskStatus(Enum):
    """Statuses used within MPI communication."""

    WORK = auto()
    NO_MORE_WORK = auto()
    RETRY = auto()
    FAILURE = auto()
    SUCCESS = auto()


@dataclass
class WorkItem:
    """Payload for worker execution."""

    chunk: DocumentChunk
    attempt: int = 0


@dataclass
class WorkResult:
    """Result payload returned by workers."""

    chunk_id: str
    status: TaskStatus
    payload_path: Optional[Path] = None
    error_message: Optional[str] = None
    attempt: int = 0
