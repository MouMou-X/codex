"""MPI scheduler that coordinates master and worker nodes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from mpi4py import MPI  # type: ignore

from .chunker import Chunker, DocumentChunk
from .config import ProcessingConfig
from .docling_adapter import DoclingProcessor, DoclingResult
from .tasks import TaskStatus, WorkItem, WorkResult


@dataclass
class SchedulerContext:
    """Holds state shared between the master and worker nodes."""

    comm: MPI.Comm
    rank: int
    size: int


class MasterScheduler:
    """Master node responsible for distributing work and collecting results."""

    def __init__(
        self,
        config: ProcessingConfig,
        processor: DoclingProcessor,
        chunker: Chunker,
    ) -> None:
        self._config = config
        self._processor = processor
        self._chunker = chunker
        self._pending: List[WorkItem] = []
        self._in_flight: Dict[int, WorkItem] = {}
        self._completed: List[WorkResult] = []

    def _prepare_chunks(self) -> Iterator[DocumentChunk]:
        metadata: List[tuple[Path, int]] = []
        for pdf_path in self._config.pdf_paths:
            total_pages = self._processor.count_pages(pdf_path)
            metadata.append((pdf_path, total_pages))
        return self._chunker.chunk_multiple(metadata)

    def run(self, context: SchedulerContext) -> List[WorkResult]:
        chunks = list(self._prepare_chunks())
        for chunk in chunks:
            self._pending.append(WorkItem(chunk=chunk))

        status = MPI.Status()
        workers = range(1, context.size)
        completed_workers = 0

        # Prime workers with initial tasks
        for worker_rank in workers:
            if not self._pending:
                break
            item = self._pending.pop(0)
            context.comm.send(obj=item, dest=worker_rank, tag=TaskStatus.WORK.value)
            self._in_flight[worker_rank] = item

        while completed_workers < context.size - 1:
            result: WorkResult = context.comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            worker_rank = status.Get_source()
            tag = TaskStatus(status.Get_tag())

            if tag == TaskStatus.SUCCESS:
                self._completed.append(result)
                self._in_flight.pop(worker_rank, None)
            elif tag == TaskStatus.FAILURE:
                failed_item = self._in_flight.pop(worker_rank, None)
                if failed_item and failed_item.attempt < self._config.max_retries:
                    retry_item = WorkItem(chunk=failed_item.chunk, attempt=failed_item.attempt + 1)
                    self._pending.append(retry_item)
                else:
                    self._completed.append(result)
            elif tag == TaskStatus.NO_MORE_WORK:
                completed_workers += 1

            if self._pending:
                next_item = self._pending.pop(0)
                context.comm.send(obj=next_item, dest=worker_rank, tag=TaskStatus.WORK.value)
                self._in_flight[worker_rank] = next_item
            else:
                if worker_rank not in self._in_flight:
                    context.comm.send(None, dest=worker_rank, tag=TaskStatus.NO_MORE_WORK.value)

        return self._completed


class WorkerExecutor:
    """Worker node that receives work and executes Docling processing."""

    def __init__(
        self,
        processor: DoclingProcessor,
        output_dir: Path,
    ) -> None:
        self._processor = processor
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, context: SchedulerContext) -> None:
        status = MPI.Status()
        comm = context.comm
        while True:
            work_item: Optional[WorkItem] = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            tag = TaskStatus(status.Get_tag())
            if tag == TaskStatus.NO_MORE_WORK or work_item is None:
                comm.send(obj=WorkResult(chunk_id="", status=TaskStatus.NO_MORE_WORK), dest=0, tag=TaskStatus.NO_MORE_WORK.value)
                break

            try:
                result = self._processor.process_chunk(
                    work_item.chunk.pdf_path,
                    work_item.chunk.page_numbers,
                )
                output_path = self._persist_result(result)
                comm.send(
                    obj=WorkResult(
                        chunk_id=result.chunk_id,
                        status=TaskStatus.SUCCESS,
                        payload_path=output_path,
                        attempt=work_item.attempt,
                    ),
                    dest=0,
                    tag=TaskStatus.SUCCESS.value,
                )
            except Exception as exc:  # pragma: no cover - relies on MPI runtime
                comm.send(
                    obj=WorkResult(
                        chunk_id=work_item.chunk.id,
                        status=TaskStatus.FAILURE,
                        error_message=str(exc),
                        attempt=work_item.attempt,
                    ),
                    dest=0,
                    tag=TaskStatus.FAILURE.value,
                )

    def _persist_result(self, result: DoclingResult) -> Path:
        output_path = self._output_dir / f"{result.chunk_id}.json"
        output_path.write_text(result.to_json(), encoding="utf-8")
        return output_path
