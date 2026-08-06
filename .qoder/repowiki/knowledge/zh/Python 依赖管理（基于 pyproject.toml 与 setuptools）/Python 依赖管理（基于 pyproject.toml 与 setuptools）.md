---
kind: dependency_management
name: Python 依赖管理（基于 pyproject.toml 与 setuptools）
category: dependency_management
scope:
    - '**'
source_files:
    - pyproject.toml
---

本仓库采用 Python 标准依赖管理体系，通过 `pyproject.toml` 声明式管理项目依赖、构建系统与开发工具链，未使用虚拟环境锁定文件或私有包仓库。

**使用的系统/工具**
- 构建系统：`setuptools`（`setuptools.build_meta`），要求版本 `>=68.0`，配合 `wheel` 打包。
- 包管理器：PEP 517/518 兼容的 `pip` / `uv` / `poetry` 等均可直接解析 `pyproject.toml`。
- 运行时约束：`requires-python = ">=3.11"`，强制 Python 3.11+。

**核心依赖声明**
- 唯一生产依赖：`mcp>=1.0.0`（MCP 协议库）。
- 可选开发依赖（`[dev]`）：`pytest>=7.0`、`mypy>=1.0`、`ruff>=0.1.0`。
- 包发现规则：`tool.setuptools.packages.find.include = ["cnaa*"]`，仅打包 `cnaa*` 命名空间下的模块。

**约定与约束**
- 代码风格与类型检查由 `ruff`（行宽 100、目标 py311）和 `mypy`（strict=true、python_version=3.11）在开发阶段强制执行。
- 未引入 `requirements.txt`、`poetry.lock`、`uv.lock` 等锁定文件，也未配置 `vendor/` 目录或私有 PyPI 源，依赖版本以宽松下限（`>=`）声明，便于上游更新但可能带来可重现性风险。
- 所有内部模块通过相对导入组织（如 `cloud.server.mcp_server`、`cnaa.models`、`local.agent`），不依赖外部 vendoring。