# Codex


本仓库包含基于 Docling 的多节点智能分片并行处理系统设计与实现。

## 目录结构

- `docs/docling_mpi_design.md`：系统设计文档
- `src/docling_mpi/`：MPI 分布式处理框架核心代码
- `pyproject.toml`：项目依赖与打包配置

## 快速开始

1. 安装依赖（需要 MPI 运行环境，例如 OpenMPI）：

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. 使用 `mpiexec` 启动处理任务：

   ```bash
   mpiexec -n 4 docling-mpi "data/*.pdf" --chunk-size 4 --output-dir output
   ```

   - `-n` 指定总的 MPI 进程数量（1 个主节点 + 若干工作节点）。
   - `--chunk-size` 控制每个任务包含的页数。
   - `--output-dir` 结果输出目录，默认 `output/`。

处理完成后，每个工作节点会在 `output/rank_<id>/` 目录中写出 JSON 结果，文件名对应 `PDF` 的页块标识。
=======
本仓库包含基于 Docling 的多节点智能分片并行处理系统设计文档。

- [基于 Docling 的多节点智能分片并行处理系统设计](docs/docling_mpi_design.md)

