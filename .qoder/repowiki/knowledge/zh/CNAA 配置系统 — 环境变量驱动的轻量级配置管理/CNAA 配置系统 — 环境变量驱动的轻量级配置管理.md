---
kind: configuration_system
name: CNAA 配置系统 — 环境变量驱动的轻量级配置管理
category: configuration_system
scope:
    - '**'
source_files:
    - cnaa/security.py
    - server.py
    - mcp_stdio_server.py
    - pyproject.toml
---

## 1. 使用的系统与方式

该仓库采用**纯环境变量 + Python dataclass**的轻量级配置方案，未引入第三方配置框架（如 Pydantic Settings、python-dotenv、configparser 等）。核心通过 `os.getenv` 读取环境变量，解析为 dataclass 实例后注入到各组件中。

- **认证配置**：`cnaa/security.py` 中的 `AuthConfig` dataclass，由 `load_auth_config_from_env()` 从环境变量加载。
- **生命周期配置**：`cnaa/lifecycle.py` 中的 `LifecycleConfig` dataclass，使用默认值，当前无外部加载器。
- **服务器启动参数**：通过 `argparse` 命令行参数（`--host`, `--port`）覆盖默认值。

## 2. 关键文件与包

| 文件 | 作用 |
|------|------|
| `cnaa/security.py` | 认证配置数据模型 (`AuthConfig`)、权限枚举、环境变量加载函数 |
| `server.py` | HTTP 服务入口，调用 `load_auth_config_from_env()` 并注入到请求处理器 |
| `mcp_stdio_server.py` | stdio MCP 服务器，不加载认证配置（直接传入空 `AuthConfig`） |
| `pyproject.toml` | 项目元数据与依赖声明（仅依赖 `mcp>=1.0.0`，无配置相关依赖） |
| `.gitignore` | 忽略 `.env` 文件，表明支持 .env 但未实现加载逻辑 |

## 3. 架构与约定

### 配置加载流程
```
环境变量 (os.getenv) → JSON 解析 → AuthConfig dataclass → 注入到 CNAARequestHandler / CNAA_MCPServer
```

### 设计原则（代码中明确声明）
- **认证默认关闭**：`AuthConfig.enabled = False`，保证向后兼容
- **纯标准库**：不使用任何第三方配置库
- **O(1) 查找**：API Key 验证使用字典查找
- **失败安全**：JSON 解析失败时回退为空字典

### 配置层级
1. **默认值**：dataclass 字段默认值（如 `enabled=False`, `allow_unauthenticated=True`）
2. **环境变量**：覆盖默认值的唯一来源
3. **运行时参数**：HTTP 服务器的 host/port 通过 argparse 覆盖

## 4. 约定与约束

### 环境变量命名约定
所有认证相关环境变量以 `CNAA_` 前缀开头：
- `CNAA_AUTH_ENABLED`: 启用/禁用认证（`"true"`/`"false"`，默认 `"false"`）
- `CNAA_ALLOW_UNAUTHENTICATED`: 允许未认证请求（`"true"`/`"false"`，默认 `"true"`）
- `CNAA_API_KEYS`: JSON 字符串，格式 `{"key": {"agent_id": "xxx", "permission": "read_write"}}`

### 强制规则（代码层面保证）
1. **认证开关**：`CNAA_AUTH_ENABLED` 必须为小写 `"true"` 才生效（`lower() == "true"`）
2. **API Keys 格式**：必须是 JSON 对象，否则记录错误日志并使用空字典
3. **权限级别**：非法权限值回退到 `read_write`，不会抛出异常
4. **未认证处理**：当 `enabled=True` 且 `allow_unauthenticated=False` 时，缺少 Bearer token 的请求返回 401

### 缺失的配置能力
- 无配置文件加载（`.yaml`、`.json`、`.toml` 均未实现）
- 无 `.env` 文件支持（虽然 `.gitignore` 包含 `.env`，但无 `load_dotenv` 调用）
- 无配置热重载机制
- 无配置验证（除 JSON 格式外）
- 无多环境配置支持（dev/staging/prod）

### 测试覆盖
`tests/test_security.py` 中对 `load_auth_config_from_env()` 进行了完整测试，包括：
- 空环境变量的默认行为
- 启用了认证后的 API Key 验证
- 未认证访问的控制
- JSON 解析错误的容错处理