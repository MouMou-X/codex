"""Command line interface for running the MPI pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path

from .config import ProcessingConfig, StorageConfig
from .mpi_app import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Docling MPI PDF processing")
    parser.add_argument("patterns", nargs="+", help="Glob patterns for PDF input files")
    parser.add_argument("--chunk-size", type=int, default=4, help="Number of pages per chunk")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--clean-output", action="store_true")
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--no-broadcast", dest="broadcast", action="store_false")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    storage = StorageConfig(output_dir=args.output_dir, ensure_clean=args.clean_output)
    config = ProcessingConfig.from_glob(
        args.patterns,
        chunk_size=args.chunk_size,
        broadcast_metadata=args.broadcast,
        max_retries=args.max_retries,
        storage=storage,
    )
    run(config)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
