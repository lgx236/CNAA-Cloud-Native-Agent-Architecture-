---
kind: logging_system
name: 基于 Python 标准库 logging 的轻量级日志系统
category: logging_system
scope:
    - '**'
source_files:
    - server.py
    - mcp_stdio_server.py
    - cloud/server/mcp_server.py
    - cnaa/security.py
    - local/client/mcp_client.py
---

本仓库采用 Python 标准库 `logging` 模块作为统一的日志系统，未引入第三方日志框架（如 loguru、structlog 等）。所有模块通过 `logging.getLogger(__name__)` 获取模块级 logger 实例，遵循“每个模块一个 logger”的约定。

**日志配置与输出**
- HTTP 服务器入口 `server.py` 通过 `logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")` 初始化根记录器，默认输出到 stdout。
- stdio MCP 服务器 `mcp_stdio_server.py` 将日志流重定向到 `sys.stderr`，以避免与 MCP 协议使用的 stdout 冲突，注释明确说明“stdout is reserved for MCP protocol”。
- 日志格式统一包含时间戳、模块名、级别和消息内容，便于在容器环境中收集和分析。

**日志级别使用模式**
- `logger.info()`：用于服务启动、关闭、认证状态、MCP 初始化等正常流程信息。
- `logger.warning()`：用于无效 API key 尝试、客户端未连接等可恢复异常。
- `logger.error()`：用于配置解析失败、权限级别非法等配置类错误。
- `logger.exception()`：用于捕获并记录异常堆栈，常见于请求处理、工具调用等 try/except 块中。

**架构约定**
- 日志配置分散在各入口文件（HTTP server、stdio server），而非集中管理，属于轻量级实践。
- 各模块仅通过 `getLogger(__name__)` 获取 logger，不直接操作 root logger 或 handler，由入口文件统一配置。
- 未实现结构化日志字段（如 request_id、agent_id 等上下文字段），也未使用过滤器或格式化器进行增强。
- 无日志轮转、异步写入、分级输出目标等高级特性，适合开发调试场景。

**约束与限制**
- 当前日志级别固定为 INFO，未提供运行时动态调整机制。
- 未集成外部日志收集服务（如 ELK、Loki、CloudWatch 等）。
- 未对敏感信息进行脱敏处理（如 API key、用户数据等），在生产环境需谨慎使用。