---
kind: error_handling
name: CNAA 错误处理体系：基于 JSON Schema 的响应状态与 HTTP 层统一错误封装
category: error_handling
scope:
    - '**'
source_files:
    - server.py
    - cloud/server/mcp_server.py
    - cnaa/schemas.py
    - local/client/mcp_client.py
---

## 1. 系统/方法概述
该仓库采用「HTTP 层统一错误封装 + MCP 工具调用返回统一 status 字段」的两层错误处理模式，没有定义独立的异常类型或全局错误码枚举。错误通过标准 Python 异常（Exception、json.JSONDecodeError）捕获后，统一转换为包含 `status` 字段的 JSON 响应，由 HTTP 层 `_send_error` 方法包装为 `{"status": "error", "message": ...}` 结构。

- 协议层：所有 MCP 工具调用返回的 dict 都遵循 `cnaa/schemas.py` 中定义的 `STATUS_RESPONSE` 等 schema，其中 `status` 字段取值为 `ok` / `error` / `not_found`。
- HTTP 层：`server.py` 中的 `CNAARequestHandler._send_error` 是唯一的 HTTP 错误出口，将业务错误映射到对应 HTTPStatus（NOT_FOUND、BAD_REQUEST、INTERNAL_SERVER_ERROR）。
- 日志：使用 Python 标准 `logging` 模块，在关键路径（MCP 请求处理、工具调用异常）记录 `logger.exception`。

## 2. 关键文件与位置
- `server.py`：HTTP 入口，集中处理请求路由、JSON 解析异常、通用 `_send_error` 封装。
- `cloud/server/mcp_server.py`：MCP Server，`handle_tool_call` 统一 try/except 捕获工具处理器异常并返回 `{"status": "error", "message": str(e)}`；未知 tool 直接返回 error 状态。
- `cnaa/schemas.py`：接口契约的唯一来源，定义所有响应 schema 中的 `status` 枚举值（`ok` / `error` / `not_found`）及可选 `message` 字段。
- `local/client/mcp_client.py`：客户端侧对未连接服务器场景返回 `{"status": "error", "message": "MCP client not connected to server"}`，保持与服务端一致的响应结构。

## 3. 架构与约定
- **统一响应结构**：所有 API 响应必须包含 `status` 字段，成功为 `ok`，失败为 `error` 或 `not_found`；可选 `message` 提供人类可读描述。该约定由 `cnaa/schemas.py` 中的 `STATUS_RESPONSE`、`STORE_MEMORY_RESPONSE`、`GET_MEMORY_RESPONSE` 等 schema 强制。
- **HTTP 错误出口单一化**：`CNAARequestHandler._send_error(status, message)` 是唯一发送错误响应的入口，确保所有 HTTP 错误格式一致。
- **异常捕获分层**：
  - HTTP 层：`_handle_mcp` 中分别捕获 `json.JSONDecodeError`（返回 BAD_REQUEST）和通用 `Exception`（记录日志后返回 INTERNAL_SERVER_ERROR）。
  - MCP 层：`handle_tool_call` 对所有工具处理器包裹 try/except Exception，记录堆栈后返回 `status: error`。
- **存储层不抛异常**：内存存储后端（`cloud/storage/memory_store.py`、`state_store.py`）直接返回 dict 结果（如 `{"status": "ok", ...}`），不在底层抛出异常，由上层统一兜底。
- **无自定义异常类**：代码中未发现 `class *Error(Exception)` 的定义，错误传播依赖标准 Exception 与返回值中的 `status` 字段。

## 4. 约定与约束
- **响应 status 枚举约束**：根据 `cnaa/schemas.py` 中各 response schema 的 `status` 字段定义，合法取值仅限 `ok`、`error`、`not_found`（部分响应仅允许 `ok`/`error`）。
- **HTTP 错误必须经 `_send_error`**：所有非 200 响应均通过 `_send_error(HTTPStatus, message)` 发出，保证 `{"status": "error", "message": ...}` 格式。
- **工具调用异常必须被捕获**：`handle_tool_call` 要求每个工具处理器内部逻辑不得向外抛出未捕获异常，否则会被外层 try/except 捕获并转为 `status: error`。
- **日志记录规范**：异常路径使用 `logger.exception(...)` 输出完整堆栈，正常路径使用 `logger.info` 记录关键事件（如服务启动、关闭）。
- **客户端一致性**：本地客户端在未连接服务端时返回与服务端相同的 `{"status": "error", "message": ...}` 结构，便于上层统一处理。

## 5. 缺失与改进空间
- 缺少统一的自定义异常类型（如 `CNAAError`、`NotFoundError`），导致错误语义仅靠字符串消息传递。
- 未实现重试、超时、熔断等网络错误处理策略（客户端注释已注明当前为参考实现）。
- 错误码未结构化（目前仅用字符串 message），不利于自动化错误分类与监控告警。
