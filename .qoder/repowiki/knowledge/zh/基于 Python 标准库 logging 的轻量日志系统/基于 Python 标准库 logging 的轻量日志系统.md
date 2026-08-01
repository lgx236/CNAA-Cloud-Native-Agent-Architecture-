---
kind: logging_system
name: 基于 Python 标准库 logging 的轻量日志系统
category: logging_system
scope:
    - '**'
source_files:
    - server.py
    - cloud/server/mcp_server.py
    - local/client/mcp_client.py
---

本仓库采用 Python 标准库 `logging` 模块作为唯一的日志系统，未引入第三方日志框架（如 loguru、structlog 等）。所有日志输出遵循统一的命名空间 logger 模式，通过 `logging.getLogger(__name__)` 在每个模块中获取独立的 logger 实例。

**日志配置与初始化**：在入口文件 `server.py` 中通过 `logging.basicConfig()` 集中配置根 logger，设置默认级别为 `INFO`，格式为 `%(asctime)s - %(name)s - %(levelname)s - %(message)s`。该配置同时被 `cloud/server/mcp_server.py`、`local/client/mcp_client.py` 等模块继承使用。

**日志级别使用约定**：
- `logger.info()`：用于常规业务流程记录，如服务器启动/关闭、HTTP 请求处理等
- `logger.warning()`：用于非致命异常或配置缺失场景，如客户端未连接服务端时的警告
- `logger.exception()`：用于捕获并记录完整异常堆栈，通常在 try-except 块中使用

**结构化字段策略**：当前实现未采用结构化日志格式（JSON），所有日志均为纯文本格式。错误响应通过 HTTP 层的 `_send_error()` 方法以 JSON 形式返回，但日志本身保持简单文本格式。

**HTTP 请求日志**：通过重写 `BaseHTTPRequestHandler.log_message()` 方法，将 HTTP 请求日志统一路由到自定义 logger，包含客户端地址和请求信息。

**约束与限制**：无统一的日志级别管理策略，各模块独立决定使用何种级别；无日志轮转、异步写入、多目标输出等高级特性；无敏感信息过滤机制。