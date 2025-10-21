"""Entry-point for running the MPI Docling processing application."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from mpi4py import MPI  # type: ignore

from .chunker import Chunker
from .config import ProcessingConfig
from .docling_adapter import DoclingProcessor
from .scheduler import MasterScheduler, SchedulerContext, WorkerExecutor


def run(config: ProcessingConfig) -> None:
    """Execute the distributed processing job with the provided config."""
    config.validate()
    config.storage.prepare_output_dir()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    context = SchedulerContext(comm=comm, rank=rank, size=comm.Get_size())

    processor = DoclingProcessor()
    chunker = Chunker(chunk_size=config.chunk_size)

    if rank == 0:
        scheduler = MasterScheduler(config=config, processor=processor, chunker=chunker)
        scheduler.run(context)
    else:
        worker_output = config.storage.output_dir / f"rank_{rank}"
        executor = WorkerExecutor(processor=processor, output_dir=worker_output)
        executor.run(context)


def run_from_patterns(patterns: Iterable[str], **kwargs: object) -> None:
    """Helper to run the pipeline from glob patterns."""
    config = ProcessingConfig.from_glob(patterns, **kwargs)
    run(config)
