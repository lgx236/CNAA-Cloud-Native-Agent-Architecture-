---
kind: dependency_management
name: Python 依赖管理（基于 pyproject.toml 与 setuptools）
category: dependency_management
scope:
    - '**'
source_files:
    - pyproject.toml
---

本仓库使用 Python 标准的 `pyproject.toml` 作为唯一的依赖声明入口，采用 `setuptools.build_meta` 作为构建后端，未引入 Poetry、Pipenv、uv 等第三方包管理器，也未使用 vendoring 或私有 PyPI 源。具体约定如下：

1. **运行时依赖**：仅声明一个核心依赖 `mcp>=1.0.0`，位于 `[project].dependencies`。
2. **可选开发依赖**：通过 `[project.optional-dependencies]` 的 `dev` 分组提供 `pytest`、`mypy`、`ruff`，安装时需显式指定 `pip install -e ".[dev]`。
3. **构建系统**：`requires-python = ">=3.11` 强制最低 Python 版本；`build-system.requires` 锁定 `setuptools>=68.0` 和 `wheel`。
4. **包发现**：`tool.setuptools.packages.find.include = ["cnaa*"]` 仅打包以 `cnaa` 开头的包。
5. **代码质量工具配置**：`tool.ruff` 与 `tool.mypy` 在 `pyproject.toml` 中直接声明规则（行宽 100、strict 模式、target-version py311），无需额外配置文件。
6. **无锁文件**：仓库未包含 `requirements.txt`、`poetry.lock`、`uv.lock` 等锁定文件，依赖版本以宽松下限（`>=`）形式声明，由 pip 在安装时解析。
7. **无 vendoring / 私有源**：未发现 `vendor/` 目录、`.pypirc`、`pip.conf` 或环境变量中的私有索引配置，所有依赖均从官方 PyPI 获取。

约束与约束来源：
- Python 版本不低于 3.11（由 `requires-python` 字段强制执行）。
- 开发环境需单独启用 `dev` 可选依赖组（由 setuptools 的可选依赖机制保证）。
- 类型检查与 lint 严格模式由 mypy 的 `strict = true` 与 ruff 的 `line-length = 100` 配置生效。