---
kind: logging_system
name: 基于 Python 标准库 logging 的轻量级日志系统
category: logging_system
scope:
    - '**'
source_files:
    - server.py
    - cloud/server/mcp_server.py
    - local/client/mcp_client.py
---

本仓库采用 Python 标准库 logging 模块实现统一的日志记录，未引入第三方日志框架（如 loguru、structlog 等）。日志系统围绕单一入口 server.py 集中配置，各模块通过 logging.getLogger(__name__) 获取独立 logger 实例。

架构与约定：
- 框架与工具：Python 标准库 logging，无外部依赖
- 配置位置：仅在 server.py 中通过 logging.basicConfig() 统一初始化
- Logger 命名：每个模块使用 logger = logging.getLogger(__name__) 获取以模块全限定名为名的 logger
- 日志格式：固定格式 "%(asctime)s - %(name)s - %(levelname)s - %(message)s"，包含时间戳、模块名、级别和消息
- 默认级别：INFO 级别作为默认输出阈值
- 错误处理：异常捕获后统一使用 logger.exception(...) 输出堆栈信息
- HTTP 请求日志：CNAARequestHandler.log_message 重写基类方法，将 HTTP 访问日志重定向到 logger.info
- 客户端警告：mcp_client.py 在未连接服务器时使用 logger.warning 提示当前为 mock 模式

约束：
- 所有模块必须通过 logging.getLogger(__name__) 获取 logger，禁止直接调用 logging.info() 等根 logger 方法
- 异常日志统一使用 logger.exception() 而非 logger.error()，确保堆栈信息完整输出
- 未在代码中发现结构化日志字段或自定义 Formatter/Handler，日志输出为纯文本平面格式
- 日志级别策略简单：仅 INFO 及以上级别输出，无 DEBUG/WARNING/ERROR 分级开关配置