---
kind: build_system
name: 构建与打包系统（基于 setuptools + pyproject.toml）
category: build_system
scope:
    - '**'
source_files:
    - pyproject.toml
---

该仓库采用 Python 标准构建体系，未使用 Makefile、Dockerfile、CI 流水线或自定义构建脚本，仅通过 `pyproject.toml` 声明式配置完成包定义、依赖管理与开发工具链集成。

1. **构建系统与后端**
- 使用 `setuptools.build_meta` 作为 build-backend，要求 `setuptools>=68.0` 与 `wheel`，遵循 PEP 517/518 现代 Python 打包规范。
- 包名 `cnaa`，版本 `0.1.0`，Python 最低版本要求 `>=3.11`，许可证 MIT。
- 运行时依赖仅声明 `mcp>=1.0.0`；开发依赖通过 `[project.optional-dependencies]` 的 `dev` 组提供 `pytest>=7.0`、`mypy>=1.0`、`ruff>=0.1.0`。
- 包发现规则为 `include = ["cnaa*"]`，即只打包 `cnaa` 命名空间下的子包。

2. **代码质量与类型检查**
- Ruff：行宽 100，目标 Python 版本 3.11。
- MyPy：严格模式（`strict = true`），Python 版本 3.11。
- 这些配置表明项目在构建时可通过 `ruff check` 和 `mypy .` 进行静态检查，但仓库中未提供对应的 CI 任务或 Makefile 来自动执行。

3. **测试组织**
- 测试文件集中在 `tests/` 目录，使用 pytest 框架（由 `pyproject.toml` 中的 dev 依赖引入）。
- 未见 `pytest.ini`、`conftest.py` 或 tox 等额外测试编排配置。

4. **发布与部署**
- 未发现 Dockerfile、docker-compose、GitHub Actions / GitLab CI 等自动化发布或容器化配置。
- `.gitignore` 中包含 `build/` 目录，说明构建产物会被忽略。
- README 中列出待办事项包含「Cloud deployment solutions」，表明云部署方案尚未实现。

5. **约束与约定**
- 所有 Python 代码需满足 mypy 严格模式与 ruff 规则。
- 包结构以 `cnaa*` 命名空间为打包边界，其他顶层模块（如 `cloud/`、`local/`、`examples/`、`server.py`、`mcp_stdio_server.py`）未被纳入包分发范围。
- 依赖管理完全集中於 `pyproject.toml`，无 `requirements.txt`、`poetry.lock` 或 `pipenv` 等其他锁定文件。