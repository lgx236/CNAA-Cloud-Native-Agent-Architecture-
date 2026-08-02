---
kind: build_system
name: 构建与打包系统（基于 setuptools 的 Python 包管理）
category: build_system
scope:
    - '**'
source_files:
    - pyproject.toml
    - server.py
---

该仓库采用极简的 Python 包构建体系，完全依赖 `pyproject.toml` + `setuptools.build_meta` 标准流程，未引入 Makefile、Dockerfile、CI 流水线或自定义构建脚本。

**构建系统与工具链**
- 构建后端：`setuptools.build_meta`（要求 setuptools>=68.0 与 wheel），通过 `python -m build` / `pip install .` 完成打包与安装。
- Python 版本约束：`requires-python = ">=3.11"`，mypy 与 ruff 均锁定 py311 目标。
- 运行时依赖：仅声明 `mcp>=1.0.0`；开发依赖（pytest、mypy、ruff）通过 `[project.optional-dependencies].dev` 提供。
- 包发现规则：`[tool.setuptools.packages.find] include = ["cnaa*"]`，仅打包 `cnaa*` 命名空间下的模块。

**入口与运行方式**
- 服务器入口：`server.py` 使用 `argparse` 暴露 `--host` / `--port` 参数，直接 `python server.py` 启动内置 HTTPServer。
- 无 `entry_points` / `console_scripts` 配置，因此不会生成可执行命令。

**测试与质量检查**
- 测试框架：`pytest`（在 dev 依赖中声明），测试文件位于 `tests/` 目录。
- 类型检查：`mypy` 以 `strict = true` 模式运行，Python 版本锁定 3.11。
- 代码风格：`ruff` 配置行宽 100、目标版本 py311。
- 测试缓存：`.gitignore` 忽略 `.pytest_cache/`。

**发布与制品**
- 版本号由 `pyproject.toml` 中的 `version = "0.1.0"` 统一管理。
- 未发现 Dockerfile、GitHub Actions、Makefile、release 脚本等 CI/CD 配置，打包产物为标准的 sdist/wheel。

**约定与约束**
- 所有构建、依赖、工具配置集中于单一 `pyproject.toml`，遵循 PEP 517/518 标准。
- 包结构以 `cnaa/` 为核心分发单元，`cloud/`、`local/`、`examples/`、`tests/` 未被纳入包发布范围。
- 项目未实现自动化测试、lint、类型检查的 CI 集成，这些工具仅在本地通过 pip 安装后手动调用。