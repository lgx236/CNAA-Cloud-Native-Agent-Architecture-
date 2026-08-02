# CNAA 技术实现文档

> 本文档面向所有开发者，详细描述了 CNAA 框架的每一个模块、每一个函数的功能与调用关系。
> 即使你是第一次接触本项目，也可以按照本文档快速理解代码结构并进行修改。

---

## 目录

- [1. 快速上手](#1-快速上手)
- [2. 项目目录结构总览](#2-项目目录结构总览)
- [3. 核心契约层 `cnaa/`](#3-核心契约层-cnaa)
  - [3.1 `cnaa/models.py` — 核心数据模型](#31-cnaamodelspy--核心数据模型)
  - [3.2 `cnaa/schemas.py` — JSON 接口 Schema 定义](#32-cnaaschemasspy--json-接口-schema-定义)
  - [3.3 `cnaa/interaction.py` — 抽象交互接口](#33-cnaainteractionspy--抽象交互接口)
  - [3.4 `cnaa/lifecycle.py` — 可插拔生命周期插件](#34-cnaalifecyclespy--可插拔生命周期插件)
  - [3.5 `cnaa/security.py` — 安全认证模块](#35-cnaasecurityspy--安全认证模块)
  - [3.6 `cnaa/tools.py` — MCP 工具定义](#36-cnaatoolspy--mcp-工具定义)
- [4. 云端实现层 `cloud/`](#4-云端实现层-cloud)
  - [4.1 `cloud/server/mcp_server.py` — MCP 服务端](#41-cloudservermcp_serverpy--mcp-服务端)
  - [4.2 `cloud/storage/memory_store.py` — 记忆存储后端](#42-cloudstoragememory_storepy--记忆存储后端)
  - [4.3 `cloud/storage/state_store.py` — 状态存储后端](#43-cloudstoragestate_storepy--状态存储后端)
  - [4.4 `cloud/agent.py` — 云端 Agent 接口](#44-cloudagentpy--云端-agent-接口)
- [5. 本地实现层 `local/`](#5-本地实现层-local)
  - [5.1 `local/client/mcp_client.py` — MCP 客户端](#51-localclientmcp_clientpy--mcp-客户端)
  - [5.2 `local/memory/instant_memory.py` — 即时记忆管理器](#52-localmemoryinstant_memorypy--即时记忆管理器)
  - [5.3 `local/state/state_cache.py` — 状态缓存](#53-localstatestate_cachepy--状态缓存)
  - [5.4 `local/agent.py` — 本地 Agent 接口（主入口）](#54-localagentpy--本地-agent-接口主入口)
- [6. 服务入口](#6-服务入口)
  - [6.1 `server.py` — HTTP 服务入口](#61-serverpy--http-服务入口)
  - [6.2 `mcp_stdio_server.py` — Stdio MCP 服务入口](#62-mcp_stdio_serverpy--stdio-mcp-服务入口)
- [7. 完整调用链路图](#7-完整调用链路图)
- [8. 核心算法详解](#8-核心算法详解)
- [9. 如何修改与扩展](#9-如何修改与扩展)

---

## 1. 快速上手

### 1.1 环境要求

- Python >= 3.11
- 无外部依赖（仅使用 Python 标准库 + 项目内模块）

### 1.2 安装与运行

```bash
# 克隆项目
git clone <repo-url>
cd CNAA-Cloud-Native-Agent-Architecture-

# 直接启动 HTTP 服务（默认 localhost:8080）
python server.py

# 或指定端口
python server.py --host 0.0.0.0 --port 9090

# 启动 stdio 模式 MCP 服务
python mcp_stdio_server.py
```

### 1.3 运行测试

```bash
python -m pytest tests/ -v
```

### 1.4 最简使用示例

```python
from cloud.server.mcp_server import CNAA_MCPServer

# 1. 创建服务端
server = CNAA_MCPServer()

# 2. 存储一条记忆
result = server.handle_tool_call("cnaa_store_memory", {
    "agent_id": "my-agent",
    "memory_id": "mem-001",
    "type": "long_term",
    "content": {"task": "示例任务", "result": "成功"},
})
# result = {"status": "ok", "memory_id": "mem-001"}

# 3. 读取记忆
result = server.handle_tool_call("cnaa_get_memory", {
    "agent_id": "my-agent",
    "memory_id": "mem-001",
})
# result = {"status": "ok", "memory": {...}}
```

---

## 2. 项目目录结构总览

```
CNAA-Cloud-Native-Agent-Architecture-/
│
├── cnaa/                          # 【核心契约层】定义数据模型、接口、Schema、工具、生命周期
│   ├── __init__.py                # 包入口，统一导出所有公共 API
│   ├── models.py                  # 核心数据模型（Memory, State, Preference 等）
│   ├── schemas.py                 # JSON Schema 定义（单一事实来源）
│   ├── interaction.py             # 抽象交互接口（MemoryInterface, StateInterface）
│   ├── lifecycle.py               # 可插拔生命周期插件接口与默认实现
│   ├── security.py                # API Key 认证与权限校验
│   └── tools.py                   # 13 个 MCP 工具定义与注册
│
├── cloud/                         # 【云端实现层】CNAA 服务端参考实现
│   ├── __init__.py
│   ├── agent.py                   # CloudAgentInterface — 云端 Python API 封装
│   ├── server/
│   │   ├── __init__.py
│   │   └── mcp_server.py          # CNAA_MCPServer — MCP 工具路由与调度核心
│   └── storage/
│       ├── __init__.py
│       ├── memory_store.py        # InMemoryMemoryStore — 记忆内存存储
│       └── state_store.py         # InMemoryStateStore — 状态/偏好/环境内存存储
│
├── local/                         # 【本地实现层】Agent 本地 SDK 参考实现
│   ├── __init__.py
│   ├── agent.py                   # LocalAgentInterface — 本地主入口
│   ├── client/
│   │   ├── __init__.py
│   │   └── mcp_client.py          # CNAA_MCPClient — MCP 协议客户端
│   ├── memory/
│   │   ├── __init__.py
│   │   └── instant_memory.py      # InstantMemoryManager — 即时记忆管理
│   └── state/
│       ├── __init__.py
│       └── state_cache.py         # StateCache — TTL 状态缓存
│
├── server.py                      # HTTP 服务入口（python server.py 启动）
├── mcp_stdio_server.py            # Stdio MCP 服务入口
├── examples/
│   └── openclaw_integration.py    # OpenClaw 集成示例
├── tests/                         # 单元测试与集成测试
├── docs/                          # 文档目录
├── pyproject.toml                 # 项目配置与依赖
└── README.md / README_CN.md       # 项目说明
```

**三层架构对应关系：**

| 层次 | 目录 | 职责 | 核心类/函数 |
|------|------|------|------------|
| 接口契约层 (What) | `cnaa/` | 定义数据模型、接口规范、工具定义 | `Memory`, `State`, `MemoryInterface`, `get_tool_definitions()` |
| 运行时层 (How) | `cloud/` + `local/` | 服务端实现 + 客户端实现 | `CNAA_MCPServer`, `LocalAgentInterface` |
| 生命周期层 (When) | `cnaa/lifecycle.py` | 记忆沉淀/淘汰/状态演化规则 | `TimeBasedLifecyclePlugin`, `StateEvolutionPlugin` |

---

## 3. 核心契约层 `cnaa/`

### 3.1 `cnaa/models.py` — 核心数据模型

**文件职责：** 定义框架中所有数据结构，是整个系统的"数据字典"。

**依赖关系：** 无外部依赖，仅使用 Python 标准库（`dataclasses`, `datetime`, `enum`）。

#### 枚举类型

| 枚举 | 值 | 含义 |
|------|------|------|
| `MemoryType.LONG_TERM` | `"long_term"` | 云端长期记忆 |
| `MemoryType.SHORT_TERM` | `"short_term"` | 本地短期记忆 |
| `MemoryStatus.ACTIVE` | `"active"` | 活跃状态，可用 |
| `MemoryStatus.CONDENSED` | `"condensed"` | 已压缩，仅保留索引指针 |
| `MemoryStatus.EVICTED` | `"evicted"` | 已从本地上下文移除 |
| `StateCategory.PREFERENCE` | `"preference"` | 偏好——影响 Agent 行为的重要记忆模式 |
| `StateCategory.KNOWLEDGE` | `"knowledge"` | 知识——从经验中积累的知识 |
| `StateCategory.ENVIRONMENT` | `"environment"` | 环境——Agent 运行的上下文信息 |

#### 数据模型详解

**`Memory`** — 经验记忆实体

```
字段：
  memory_id: str           — 记忆唯一标识
  agent_id: str            — 所属 Agent 标识
  type: MemoryType         — 存储位置（长期/短期）
  content: dict[str, Any]  — 记忆内容（开放 JSON，哑服务原则）
  tags: list[str]          — 标签列表，用于分类和过滤
  completion_score: float  — 任务完成度 [0.0, 1.0]
  timestamp: datetime      — 创建时间（未提供时自动设为当前时间）
  metadata: dict[str, Any] — 可选元数据

内部方法：
  __post_init__() → None
    作用：如果 timestamp 为 None，自动设为 datetime.now()
    调用者：Python dataclass 构造函数自动调用
```

**`TaskCheckpoint`** — 任务检查点

```
字段：
  task_id: str                  — 任务标识
  checkpoint_id: str            — 检查点标识
  compressed_memory: Memory     — 完整记忆数据（存云端）
  summary: str                  — 轻量摘要（存本地即时记忆）
  completion_score: float       — 完成度
  timestamp: datetime           — 创建时间

内部方法：
  __post_init__() → None
    作用：自动设置 timestamp
```

**`State`** — Agent 状态（积累的知识）

```
字段：
  agent_id: str            — Agent 标识
  state_id: str            — 状态唯一标识
  category: StateCategory  — 分类（preference/knowledge/environment）
  content: dict[str, Any]  — 状态内容
  updated_at: datetime     — 更新时间（自动设置）

内部方法：
  __post_init__() → None
    作用：自动设置 updated_at
```

**`Preference`** — Agent 偏好

```
字段：
  agent_id: str               — Agent 标识
  preference_id: str          — 偏好唯一标识
  key: str                    — 偏好键名
  value: dict[str, Any]       — 偏好内容
  importance: float           — 重要度 [0.0, 1.0]
  source_memory_ids: list[str]— 来源记忆 ID 列表
```

**`Environment`** — Agent 环境上下文

```
字段：
  agent_id: str            — Agent 标识
  env_id: str              — 环境标识
  context: dict[str, Any]  — 环境上下文内容
  updated_at: datetime     — 更新时间（自动设置）

内部方法：
  __post_init__() → None
    作用：自动设置 updated_at
```

**`InstantMemory`** — 即时记忆（本地短期）

```
字段：
  memory_id: str         — 记忆标识
  task_id: str           — 关联任务标识
  checkpoint_id: str     — 关联检查点标识
  summary: str           — 轻量摘要文本
  status: MemoryStatus   — 生命周期状态（默认 ACTIVE）
  cnaa_ref: str          — 云端记忆引用指针（如 "cnaa://agent-001/mem-001"）
  timestamp: datetime    — 创建时间（自动设置）

内部方法：
  __post_init__() → None
    作用：自动设置 timestamp

生命周期流转：
  ACTIVE → CONDENSED → EVICTED
  （活跃 → 压缩 → 淘汰）
```

**`MemorySummary`** — 记忆摘要（用于列表查询返回）

```
字段：
  memory_id: str          — 记忆标识
  tags: list[str]         — 标签
  completion_score: float — 完成度
  timestamp: datetime     — 时间戳
```

**`SearchResult`** — 搜索结果

```
字段：
  memory_id: str         — 记忆标识
  agent_id: str          — Agent 标识
  summary: str           — 摘要
  completion_score: float— 完成度
  relevance_score: float — 相关度评分
```

---

### 3.2 `cnaa/schemas.py` — JSON 接口 Schema 定义

**文件职责：** 所有 JSON 接口格式的**单一事实来源**。修改此文件即可改变所有接口格式。

**依赖关系：** 无外部依赖。

#### Schema 常量一览

| 常量名 | 类型 | 用途 |
|--------|------|------|
| `MEMORY_SCHEMA` | 数据 Schema | Memory 数据结构定义 |
| `STATE_SCHEMA` | 数据 Schema | State 数据结构定义 |
| `PREFERENCE_SCHEMA` | 数据 Schema | Preference 数据结构定义 |
| `ENVIRONMENT_SCHEMA` | 数据 Schema | Environment 数据结构定义 |
| `INSTANT_MEMORY_SCHEMA` | 数据 Schema | InstantMemory 数据结构定义 |
| `STORE_MEMORY_REQUEST` | 请求 Schema | 存储记忆的请求格式 |
| `GET_MEMORY_REQUEST` | 请求 Schema | 获取记忆的请求格式 |
| `LIST_MEMORIES_REQUEST` | 请求 Schema | 列出记忆的请求格式 |
| `TAG_SHORT_TERM_REQUEST` | 请求 Schema | 标记短期记忆的请求格式 |
| `DELETE_MEMORY_REQUEST` | 请求 Schema | 删除记忆的请求格式 |
| `GET_STATE_REQUEST` | 请求 Schema | 获取状态的请求格式 |
| `UPDATE_STATE_REQUEST` | 请求 Schema | 更新状态的请求格式 |
| `DELETE_STATE_REQUEST` | 请求 Schema | 删除状态的请求格式 |
| `GET_PREFERENCE_REQUEST` | 请求 Schema | 获取偏好的请求格式 |
| `UPDATE_PREFERENCE_REQUEST` | 请求 Schema | 更新偏好的请求格式 |
| `DELETE_PREFERENCE_REQUEST` | 请求 Schema | 删除偏好的请求格式 |
| `GET_ENVIRONMENT_REQUEST` | 请求 Schema | 获取环境的请求格式 |
| `UPDATE_ENVIRONMENT_REQUEST` | 请求 Schema | 更新环境的请求格式 |
| `STATUS_RESPONSE` | 响应 Schema | 通用状态响应 |
| `STORE_MEMORY_RESPONSE` | 响应 Schema | 存储记忆响应 |
| `GET_MEMORY_RESPONSE` | 响应 Schema | 获取记忆响应 |
| `LIST_MEMORIES_RESPONSE` | 响应 Schema | 列出记忆响应 |
| `GET_STATE_RESPONSE` | 响应 Schema | 获取状态响应 |
| `GET_PREFERENCE_RESPONSE` | 响应 Schema | 获取偏好响应 |
| `GET_ENVIRONMENT_RESPONSE` | 响应 Schema | 获取环境响应 |

#### 函数详解

**`get_all_schemas() -> dict[str, Any]`**

```
功能：返回所有 Schema 定义的字典
输入：无
输出：dict，键为 Schema 名称（如 "memory"），值为 Schema dict
调用者：server.py 的 _handle_schemas() 调用此函数返回 /schemas 端点数据
内部逻辑：构建一个包含所有 Schema 常量的 dict 并返回
```

**`get_schema(name: str) -> dict[str, Any] | None`**

```
功能：按名称获取单个 Schema
输入：name — Schema 名称字符串（如 "memory", "store_memory_request"）
输出：Schema dict 或 None（未找到时）
内部逻辑：调用 get_all_schemas() 获取全部，然后用 dict.get(name) 查找
```

**`get_request_schemas() -> dict[str, Any]`**

```
功能：返回所有请求 Schema
输出：dict，键为操作名，值为请求 Schema dict
```

**`get_response_schemas() -> dict[str, Any]`**

```
功能：返回所有响应 Schema
输出：dict，键为操作名，值为响应 Schema dict
```

---

### 3.3 `cnaa/interaction.py` — 抽象交互接口

**文件职责：** 定义本地与云端之间的抽象交互契约。只规定"做什么"，不规定"怎么做"。

**依赖关系：** 导入 `cnaa.models` 中的 `Memory`, `State`, `Preference`, `Environment`, `MemorySummary`, `MemoryType`。

#### `MemoryInterface` (ABC)

抽象基类，定义了 5 个抽象方法：

| 方法签名 | 功能 | 被谁实现 |
|----------|------|----------|
| `store_memory(memory: Memory) -> dict` | 存储一条记忆 | `InMemoryMemoryStore` |
| `get_memory(agent_id, memory_id) -> Memory \| None` | 按 ID 获取记忆 | `InMemoryMemoryStore` |
| `list_memories(agent_id, memory_type?, tags?) -> list[MemorySummary]` | 列出记忆（可过滤） | `InMemoryMemoryStore` |
| `tag_short_term(agent_id, tags) -> dict` | 给短期记忆打标签 | `InMemoryMemoryStore` |
| `delete_memory(agent_id, memory_id) -> dict` | 删除一条记忆 | `InMemoryMemoryStore` |

#### `StateInterface` (ABC)

抽象基类，定义了 8 个抽象方法，覆盖 3 个状态类别：

| 方法签名 | 功能 | 被谁实现 |
|----------|------|----------|
| `get_state(agent_id) -> list[State]` | 获取所有状态 | `InMemoryStateStore` |
| `update_state(agent_id, state) -> dict` | 创建/更新状态 | `InMemoryStateStore` |
| `delete_state(agent_id, state_id) -> dict` | 删除状态 | `InMemoryStateStore` |
| `get_preference(agent_id) -> list[Preference]` | 获取所有偏好 | `InMemoryStateStore` |
| `update_preference(agent_id, preference) -> dict` | 创建/更新偏好 | `InMemoryStateStore` |
| `delete_preference(agent_id, preference_id) -> dict` | 删除偏好 | `InMemoryStateStore` |
| `get_environment(agent_id) -> Environment \| None` | 获取环境上下文 | `InMemoryStateStore` |
| `update_environment(agent_id, environment) -> dict` | 创建/更新环境 | `InMemoryStateStore` |

---

### 3.4 `cnaa/lifecycle.py` — 可插拔生命周期插件

**文件职责：** 定义记忆和状态演化的可插拔接口。外部包可实现这些接口来提供自定义的生命周期管理。

**依赖关系：** 导入 `cnaa.models` 中的 `InstantMemory`, `Memory`, `MemoryStatus`, `MemoryType`, `SearchResult`, `TaskCheckpoint`。

#### 核心组件

**`LifecycleEvent` (Enum)** — 生命周期事件枚举

| 事件 | 含义 |
|------|------|
| `TASK_COMPLETED` | 任务完成 |
| `MEMORY_CONDENSED` | 记忆被压缩 |
| `MEMORY_EVICTED` | 记忆被淘汰 |
| `MEMORY_PROMOTED` | 短期记忆提升为长期 |
| `STATE_EVOLVED` | 状态发生演化 |

**`LifecycleConfig` (dataclass)** — 生命周期配置

```
字段：
  max_active_memories: int = 20               — 最大活跃即时记忆数
  condensation_threshold: timedelta = 1h      — 压缩时间阈值
  eviction_threshold: timedelta = 7d          — 淘汰时间阈值
  promotion_score_threshold: float = 0.5      — 提升为长期记忆的完成度阈值
```

**`MemoryLifecyclePlugin` (ABC)** — 记忆生命周期插件接口

| 抽象方法 | 功能 |
|----------|------|
| `should_condense(memory, now?) -> bool` | 判断即时记忆是否应被压缩 |
| `should_evict(memory, now?) -> bool` | 判断压缩记忆是否应被淘汰 |
| `condense_memory(memory) -> InstantMemory` | 执行压缩操作 |
| `evict_memory(memory) -> InstantMemory` | 执行淘汰操作 |
| `should_promote_to_long_term(memory) -> bool` | 判断短期记忆是否应提升为长期 |

**`TimeBasedLifecyclePlugin`** — 默认基于时间的实现

```
继承自：MemoryLifecyclePlugin

构造函数：
  __init__(config: LifecycleConfig | None = None)
    功能：使用给定配置或默认配置初始化
    内部逻辑：self.config = config or LifecycleConfig()

方法实现：
  should_condense(memory, now?) -> bool
    算法：
      1. 如果 memory.status != ACTIVE → 返回 False
      2. 如果 memory.timestamp is None → 返回 False
      3. 计算 age = now - memory.timestamp
      4. 返回 age >= config.condensation_threshold（默认 1 小时）
    时间复杂度：O(1)

  should_evict(memory, now?) -> bool
    算法：
      1. 如果 memory.status != CONDENSED → 返回 False
      2. 如果 memory.timestamp is None → 返回 False
      3. 计算 age = now - memory.timestamp
      4. 返回 age >= config.eviction_threshold（默认 7 天）
    时间复杂度：O(1)

  condense_memory(memory) -> InstantMemory
    算法：将 memory.status 设为 CONDENSED，返回修改后的 memory

  evict_memory(memory) -> InstantMemory
    算法：将 memory.status 设为 EVICTED，返回修改后的 memory

  should_promote_to_long_term(memory) -> bool
    算法：
      1. 如果 memory.type != SHORT_TERM → 返回 False
      2. 返回 memory.completion_score >= config.promotion_score_threshold
    时间复杂度：O(1)
```

**`RetrievalPlugin` (ABC)** — 检索插件接口

| 抽象方法 | 功能 |
|----------|------|
| `index(memory) -> dict` | 为记忆建立索引 |
| `search(query, agent_id, limit?, filters?) -> list[SearchResult]` | 按查询搜索记忆 |
| `recall(context, agent_id, limit?) -> list[SearchResult]` | 基于上下文回忆记忆 |
| `delete(memory_id) -> dict` | 从索引中删除记忆 |

**`StateEvolutionPlugin` (ABC)** — 状态演化插件接口

| 抽象方法 | 功能 |
|----------|------|
| `get_evolution_rules() -> list[StateEvolutionRule]` | 获取演化规则列表 |
| `should_evolve(state_id, current_phase, context) -> bool` | 判断状态是否应演化 |
| `evolve(state_id, from_phase, to_phase) -> dict` | 执行状态演化 |

**`DefaultStateEvolutionPlugin`** — 默认空操作实现

```
构造函数：
  __init__()
    内部逻辑：创建两条默认规则：
      规则 1：ACCUMULATED → ASSOCIATED（条件："多条相关经验积累"）
      规则 2：ASSOCIATED → DECAYED（条件："长期未访问"）

方法实现：
  get_evolution_rules() → 返回 self.rules
  should_evolve(...) → 始终返回 False（默认不自动演化）
  evolve(...) → 返回 {"status": "ok", ...} 状态字典
```

**`LifecyclePlugins` (dataclass)** — 插件注册中心

```
字段：
  memory_lifecycle: MemoryLifecyclePlugin  — 默认 TimeBasedLifecyclePlugin
  retrieval: RetrievalPlugin | None        — 默认 None
  state_evolution: StateEvolutionPlugin    — 默认 DefaultStateEvolutionPlugin

方法：
  register_retrieval_plugin(plugin) → None
    功能：注册检索插件
  register_memory_lifecycle_plugin(plugin) → None
    功能：注册记忆生命周期插件
  register_state_evolution_plugin(plugin) → None
    功能：注册状态演化插件
```

---

### 3.5 `cnaa/security.py` — 安全认证模块

**文件职责：** 提供轻量级 API Key 认证和权限校验。

**依赖关系：** 仅使用标准库（`json`, `logging`, `os`）。

#### 核心组件

**`PermissionLevel` (Enum)** — 权限级别

| 级别 | 值 | 能力 |
|------|------|------|
| `READ_ONLY` | `"read_only"` | 只能执行读操作 |
| `READ_WRITE` | `"read_write"` | 可执行读写操作 |
| `ADMIN` | `"admin"` | 可执行所有操作 |

**`AuthConfig` (dataclass)** — 认证配置

```
字段：
  enabled: bool = False                    — 是否启用认证（默认关闭）
  api_keys: dict[str, dict] = {}           — API Key → 元数据映射
  allow_unauthenticated: bool = True       — 是否允许未认证请求
```

**`AuthContext` (dataclass)** — 认证上下文

```
字段：
  agent_id: str               — 认证后的 Agent 标识
  permission: PermissionLevel — 授予的权限级别
  authenticated: bool = True  — 是否认证成功

方法：
  to_dict() -> dict
    功能：序列化为普通字典
    输出：{"agent_id": ..., "permission": "read_write", "authenticated": True}
    调用者：server.py 的 _handle_mcp() 调用此方法注入请求参数
```

#### 函数详解

**`validate_api_key(api_key, config) -> AuthContext | None`**

```
功能：验证 API Key 并返回认证上下文
输入：
  api_key — 请求中的 API Key 字符串或 None
  config  — AuthConfig 认证配置
输出：AuthContext 或 None
算法：
  1. 如果 config.enabled == False → 返回 None（认证未启用）
  2. 如果 api_key 为空：
     a. 如果 config.allow_unauthenticated → 返回 None（允许匿名访问）
     b. 否则 → 返回 None（需要 Key 但未提供）
  3. 用 O(1) 字典查找：key_info = config.api_keys.get(api_key)
  4. 如果 key_info is None → 记录警告日志，返回 None（无效 Key）
  5. 构建并返回 AuthContext(agent_id, permission)
调用者：server.py 的 _handle_mcp()
```

**`_parse_permission(raw: str | None) -> PermissionLevel`**

```
功能：安全解析权限字符串，无效值回退到 READ_WRITE
输入：raw — 权限字符串（"read_only"/"read_write"/"admin"）或 None
输出：PermissionLevel 枚举值
算法：
  1. 尝试 PermissionLevel(raw or "read_write")
  2. 如果 ValueError → 记录错误日志，返回 PermissionLevel.READ_WRITE
调用者：validate_api_key()
```

**`check_permission(auth_context, required_level) -> bool`**

```
功能：检查认证上下文是否满足所需权限级别
输入：
  auth_context  — AuthContext 或 None
  required_level — "read" 或 "write"
输出：bool
算法：
  1. 如果 auth_context is None → 返回 True（认证未启用 = 全部允许）
  2. 如果 permission == ADMIN → 返回 True（管理员拥有所有权限）
  3. 如果 required_level == "read"：
     返回 permission in (READ_ONLY, READ_WRITE)
  4. 如果 required_level == "write"：
     返回 permission == READ_WRITE
  5. 其他 → 返回 False
调用者：CNAA_MCPServer.handle_tool_call()
```

**`load_auth_config_from_env() -> AuthConfig`**

```
功能：从环境变量加载认证配置
输入：无（读取环境变量）
环境变量：
  CNAA_AUTH_ENABLED          — "true" 启用认证（默认 "false"）
  CNAA_ALLOW_UNAUTHENTICATED — "true" 允许匿名（默认 "true"）
  CNAA_API_KEYS              — JSON 字符串，映射 API Key → 元数据
输出：AuthConfig 实例
算法：
  1. 读取并解析三个环境变量
  2. 尝试 json.loads(CNAA_API_KEYS)
  3. 如果 JSON 解析失败 → 记录错误，使用空 dict
  4. 如果解析结果不是 dict → 记录错误，使用空 dict
  5. 返回 AuthConfig(enabled, api_keys, allow_unauthenticated)
调用者：server.py 的 create_server()
```

---

### 3.6 `cnaa/tools.py` — MCP 工具定义

**文件职责：** 定义 CNAA 暴露给 Agent 的全部 13 个 MCP 工具。

**依赖关系：** 导入 `cnaa.schemas` 中的请求 Schema 常量。

#### 工具名称常量

| 常量 | 值 | 类别 |
|------|------|------|
| `STORE_MEMORY` | `"cnaa_store_memory"` | 记忆 |
| `GET_MEMORY` | `"cnaa_get_memory"` | 记忆 |
| `LIST_MEMORIES` | `"cnaa_list_memories"` | 记忆 |
| `TAG_SHORT_TERM` | `"cnaa_tag_short_term"` | 记忆 |
| `DELETE_MEMORY` | `"cnaa_delete_memory"` | 记忆 |
| `GET_STATE` | `"cnaa_get_state"` | 状态 |
| `UPDATE_STATE` | `"cnaa_update_state"` | 状态 |
| `DELETE_STATE` | `"cnaa_delete_state"` | 状态 |
| `GET_PREFERENCE` | `"cnaa_get_preference"` | 偏好 |
| `UPDATE_PREFERENCE` | `"cnaa_update_preference"` | 偏好 |
| `DELETE_PREFERENCE` | `"cnaa_delete_preference"` | 偏好 |
| `GET_ENVIRONMENT` | `"cnaa_get_environment"` | 环境 |
| `UPDATE_ENVIRONMENT` | `"cnaa_update_environment"` | 环境 |

#### 函数详解

**`get_tool_definitions() -> list[dict[str, Any]]`**

```
功能：返回所有 13 个 MCP 工具的完整定义
输出：列表，每个元素包含 {"name": ..., "description": ..., "inputSchema": ...}
调用者：
  - CNAA_MCPServer.get_tool_definitions()
  - CNAAStdioMCPServer._handle_tools_list()
内部逻辑：构建包含 13 个工具定义的 list 并返回
```

**`get_tool_names() -> list[str]`**

```
功能：返回所有工具名称列表
输出：13 个工具名称字符串的列表
```

**`get_tool_by_name(name: str) -> dict[str, Any] | None`**

```
功能：按名称查找工具定义
输入：name — 工具名称字符串
输出：工具定义 dict 或 None
内部逻辑：遍历 get_tool_definitions()，匹配 name 字段
```

**`TOOL_PERMISSION_MAP`** — 工具权限映射

```
将每个工具映射到 "read" 或 "write" 权限需求：
  读操作（"read"）：GET_MEMORY, LIST_MEMORIES, GET_STATE, GET_PREFERENCE, GET_ENVIRONMENT
  写操作（"write"）：STORE_MEMORY, DELETE_MEMORY, TAG_SHORT_TERM, UPDATE_STATE,
                     DELETE_STATE, UPDATE_PREFERENCE, DELETE_PREFERENCE, UPDATE_ENVIRONMENT
调用者：CNAA_MCPServer.handle_tool_call() 用于权限检查
```

---

## 4. 云端实现层 `cloud/`

### 4.1 `cloud/server/mcp_server.py` — MCP 服务端

**文件职责：** CNAA 的核心调度引擎。接收工具调用请求，路由到对应的处理函数，操作存储后端。

**依赖关系：**
- 导入 `cnaa.models`（Memory, State, Preference, Environment, MemoryType, StateCategory）
- 导入 `cnaa.security`（AuthConfig, AuthContext, PermissionLevel, check_permission）
- 导入 `cnaa.tools`（13 个工具常量 + TOOL_PERMISSION_MAP + get_tool_definitions）
- 导入 `cloud.storage.memory_store.InMemoryMemoryStore`
- 导入 `cloud.storage.state_store.InMemoryStateStore`

#### `CNAA_MCPServer` 类

```
构造函数：
  __init__(memory_store?, state_store?, auth_config?)
    功能：初始化服务端
    内部逻辑：
      1. self.memory_store = memory_store or InMemoryMemoryStore()
      2. self.state_store = state_store or InMemoryStateStore()
      3. self.auth_config = auth_config or AuthConfig()
      4. self._tool_handlers = self._register_tool_handlers()
    被谁调用：
      - server.py 的 create_server()
      - mcp_stdio_server.py 的 CNAAStdioMCPServer.__init__()
      - cloud/agent.py 的 CloudAgentInterface.__init__()
```

**`_register_tool_handlers() -> dict[str, Any]`**

```
功能：建立工具名称到处理函数的映射表
输出：dict，13 个键值对，如 {"cnaa_store_memory": self._handle_store_memory, ...}
算法：直接构建 dict 字面量
调用者：__init__()
```

**`handle_tool_call(tool_name, arguments) -> dict[str, Any]`**

```
功能：处理一个 MCP 工具调用（核心入口函数）
输入：
  tool_name — 工具名称字符串
  arguments — 工具参数字典
输出：JSON 响应 dict
算法：
  1. 从 _tool_handlers 中 O(1) 查找 handler
  2. 如果未找到 → 返回 {"status": "error", "message": "Unknown tool: ..."}
  3. 提取并移除 arguments["_auth_context"]（认证上下文）
  4. 如果存在认证上下文：
     a. 重建 AuthContext 对象
     b. 从 TOOL_PERMISSION_MAP 获取所需权限级别
     c. 调用 check_permission() 校验权限
     d. 如果权限不足 → 返回错误
     e. 校验 agent_id 一致性
  5. 调用 handler(arguments)
  6. 如果 handler 抛异常 → 捕获并返回 {"status": "error", "message": str(e)}
调用者：
  - server.py 的 _handle_mcp()（HTTP 入口）
  - mcp_stdio_server.py 的 _handle_tools_call()（stdio 入口）
  - local/client/mcp_client.py 的 _call_tool()（客户端 mock 模式）
  - cloud/agent.py 的所有方法（Python API 模式）
```

**13 个工具处理函数（_handle_*）：**

**记忆类处理函数：**

```
_handle_store_memory(args) -> dict
  功能：处理 cnaa_store_memory 工具调用
  算法：
    1. 从 args 提取字段，构建 Memory 对象
    2. 调用 self.memory_store.store_memory(memory)
    3. 返回存储结果
  调用：memory_store.store_memory()

_handle_get_memory(args) -> dict
  功能：处理 cnaa_get_memory 工具调用
  算法：
    1. 调用 self.memory_store.get_memory(agent_id, memory_id)
    2. 如果返回 None → {"status": "not_found", ...}
    3. 否则 → 序列化为 JSON dict 返回
  调用：memory_store.get_memory()

_handle_list_memories(args) -> dict
  功能：处理 cnaa_list_memories 工具调用
  算法：
    1. 解析可选的 type 和 tags 过滤条件
    2. 调用 self.memory_store.list_memories(agent_id, memory_type, tags)
    3. 将 MemorySummary 列表序列化为 JSON 数组
  调用：memory_store.list_memories()

_handle_tag_short_term(args) -> dict
  功能：处理 cnaa_tag_short_term 工具调用
  算法：直接委托给 memory_store.tag_short_term()
  调用：memory_store.tag_short_term()

_handle_delete_memory(args) -> dict
  功能：处理 cnaa_delete_memory 工具调用
  算法：直接委托给 memory_store.delete_memory()
  调用：memory_store.delete_memory()
```

**状态类处理函数：**

```
_handle_get_state(args) -> dict
  功能：获取 Agent 的所有状态
  算法：
    1. 调用 self.state_store.get_state(agent_id)
    2. 将 State 列表序列化（注意 category 是枚举，需 .value）
  调用：state_store.get_state()

_handle_update_state(args) -> dict
  功能：创建或更新状态
  算法：
    1. 从 args 构建 State 对象（category 需转为 StateCategory 枚举）
    2. 调用 self.state_store.update_state(agent_id, state)
  调用：state_store.update_state()

_handle_delete_state(args) -> dict
  功能：删除状态
  调用：state_store.delete_state()
```

**偏好类处理函数：**

```
_handle_get_preference(args) -> dict
  功能：获取 Agent 的所有偏好
  调用：state_store.get_preference()

_handle_update_preference(args) -> dict
  功能：创建或更新偏好
  算法：从 args 构建 Preference 对象 → 调用 state_store.update_preference()
  调用：state_store.update_preference()

_handle_delete_preference(args) -> dict
  调用：state_store.delete_preference()
```

**环境类处理函数：**

```
_handle_get_environment(args) -> dict
  功能：获取 Agent 的环境上下文
  算法：
    1. 调用 self.state_store.get_environment(agent_id)
    2. 如果返回 None → {"status": "not_found", ...}
    3. 否则 → 序列化为 JSON dict
  调用：state_store.get_environment()

_handle_update_environment(args) -> dict
  功能：创建或更新环境
  算法：从 args 构建 Environment 对象 → 调用 state_store.update_environment()
  调用：state_store.update_environment()
```

---

### 4.2 `cloud/storage/memory_store.py` — 记忆存储后端

**文件职责：** 记忆存储的参考实现，使用内存字典。实现了 `MemoryInterface` 抽象接口。

**依赖关系：** 导入 `cnaa.models`（Memory, MemoryType, MemorySummary）和 `cnaa.interaction.MemoryInterface`。

#### `InMemoryMemoryStore` 类

```
内部数据结构：
  _memories: dict[tuple[str, str], Memory]
  键为 (agent_id, memory_id) 复合键，值为 Memory 对象

构造函数：
  __init__()
    功能：初始化空的记忆字典
```

| 方法 | 功能 | 时间复杂度 | 调用的底层操作 |
|------|------|-----------|--------------|
| `store_memory(memory, auth_context?) -> dict` | 存储记忆 | O(1) | dict 赋值 |
| `get_memory(agent_id, memory_id, auth_context?) -> Memory \| None` | 获取记忆 | O(1) | dict.get() |
| `list_memories(agent_id, type?, tags?, auth_context?) -> list[MemorySummary]` | 列出记忆 | O(n) | 线性扫描 + 过滤 |
| `tag_short_term(agent_id, tags) -> dict` | 标记短期记忆 | O(1) | 空操作（no-op） |
| `delete_memory(agent_id, memory_id, auth_context?) -> dict` | 删除记忆 | O(1) | dict del |
| `clear() -> None` | 清空所有记忆 | O(1) | dict.clear() |
| `count() -> int` | 获取记忆数量 | O(1) | len(dict) |

**`list_memories` 算法详解（线性扫描过滤）：**

```
输入：agent_id, 可选 memory_type, 可选 tags
算法：
  1. 如果 auth_context 存在且 agent_id 不匹配 → 返回空列表
  2. 遍历 _memories 的所有 (key, memory) 对
  3. 跳过 aid != agent_id 的条目
  4. 如果指定了 memory_type 且不匹配 → 跳过
  5. 如果指定了 tags：
     检查 memory.tags 中是否包含任意一个请求的 tag
     如果不包含任何一个 → 跳过
  6. 为通过的条目创建 MemorySummary 对象
  7. 返回所有 MemorySummary 的列表
```

---

### 4.3 `cloud/storage/state_store.py` — 状态存储后端

**文件职责：** 状态/偏好/环境存储的参考实现。实现了 `StateInterface` 抽象接口。

**依赖关系：** 导入 `cnaa.models`（State, Preference, Environment）和 `cnaa.interaction.StateInterface`。

#### `InMemoryStateStore` 类

```
内部数据结构：
  _states: dict[tuple[str, str], State]         — 键为 (agent_id, state_id)
  _preferences: dict[tuple[str, str], Preference] — 键为 (agent_id, preference_id)
  _environments: dict[str, Environment]           — 键为 agent_id（每个 Agent 一个）

构造函数：
  __init__()
    功能：初始化三个空字典
```

| 方法 | 功能 | 时间复杂度 |
|------|------|-----------|
| `get_state(agent_id, auth_context?) -> list[State]` | 获取 Agent 所有状态 | O(n) |
| `update_state(agent_id, state, auth_context?) -> dict` | 创建/更新状态 | O(1) |
| `delete_state(agent_id, state_id, auth_context?) -> dict` | 删除状态 | O(1) |
| `get_preference(agent_id, auth_context?) -> list[Preference]` | 获取所有偏好 | O(n) |
| `update_preference(agent_id, pref, auth_context?) -> dict` | 创建/更新偏好 | O(1) |
| `delete_preference(agent_id, pref_id, auth_context?) -> dict` | 删除偏好 | O(1) |
| `get_environment(agent_id, auth_context?) -> Environment \| None` | 获取环境 | O(1) |
| `update_environment(agent_id, env, auth_context?) -> dict` | 创建/更新环境 | O(1) |
| `clear() -> None` | 清空所有数据 | O(1) |
| `count_states() -> int` | 状态数量 | O(1) |
| `count_preferences() -> int` | 偏好数量 | O(1) |
| `count_environments() -> int` | 环境数量 | O(1) |

---

### 4.4 `cloud/agent.py` — 云端 Agent 接口

**文件职责：** 为外部 Agent 框架提供 Python API 封装，免去直接构造 JSON 的麻烦。

**依赖关系：** 导入 `cloud.server.mcp_server.CNAA_MCPServer`。

#### `CloudAgentInterface` 类

```
构造函数：
  __init__(server: CNAA_MCPServer | None = None)
    功能：初始化云端接口
    内部逻辑：self.server = server or CNAA_MCPServer()
```

| 方法 | 功能 | 调用的底层函数 |
|------|------|--------------|
| `store_memory(agent_id, memory_id, memory_type, content, ...)` | 存储记忆 | `server.handle_tool_call("cnaa_store_memory", {...})` |
| `get_memory(agent_id, memory_id)` | 获取记忆 | `server.handle_tool_call("cnaa_get_memory", {...})` |
| `list_memories(agent_id, type?, tags?)` | 列出记忆 | `server.handle_tool_call("cnaa_list_memories", {...})` |
| `get_state(agent_id)` | 获取状态 | `server.handle_tool_call("cnaa_get_state", {...})` |
| `update_state(agent_id, state_id, category, content)` | 更新状态 | `server.handle_tool_call("cnaa_update_state", {...})` |
| `get_preference(agent_id)` | 获取偏好 | `server.handle_tool_call("cnaa_get_preference", {...})` |
| `update_preference(agent_id, preference_id, key, value, ...)` | 更新偏好 | `server.handle_tool_call("cnaa_update_preference", {...})` |
| `get_environment(agent_id)` | 获取环境 | `server.handle_tool_call("cnaa_get_environment", {...})` |
| `update_environment(agent_id, env_id, context)` | 更新环境 | `server.handle_tool_call("cnaa_update_environment", {...})` |

**每个方法的内部逻辑相同：** 将参数组装为 dict → 调用 `self.server.handle_tool_call(tool_name, args)` → 返回结果 dict。

---

## 5. 本地实现层 `local/`

### 5.1 `local/client/mcp_client.py` — MCP 客户端

**文件职责：** MCP 协议客户端参考实现，负责将工具调用发送到云端。

**依赖关系：** 仅使用标准库（`json`, `logging`）。

#### `CNAA_MCPClient` 类

```
构造函数：
  __init__(server_url?, timeout?, api_key?)
    功能：初始化客户端
    内部逻辑：
      1. 保存 server_url, timeout, api_key
      2. self._mock_handler = None（测试用 mock 处理器）

方法：
  set_mock_handler(handler) -> None
    功能：设置 mock 处理器（用于测试，模拟云端服务器）
    输入：handler — 拥有 handle_tool_call 方法的对象

  _call_tool(tool_name, arguments) -> dict
    功能：调用一个 MCP 工具
    算法：
      1. 如果 self._mock_handler 存在 → 调用 handler.handle_tool_call(tool_name, arguments)
      2. 否则 → 构建 HTTP headers（含 Authorization），记录警告，返回错误
    调用者：本类的所有 13 个工具方法
```

13 个工具方法（与云端工具一一对应）：

| 方法 | 内部调用 |
|------|---------|
| `store_memory(agent_id, memory_id, ...)` | `_call_tool("cnaa_store_memory", {...})` |
| `get_memory(agent_id, memory_id)` | `_call_tool("cnaa_get_memory", {...})` |
| `list_memories(agent_id, type?, tags?)` | `_call_tool("cnaa_list_memories", {...})` |
| `delete_memory(agent_id, memory_id)` | `_call_tool("cnaa_delete_memory", {...})` |
| `get_state(agent_id)` | `_call_tool("cnaa_get_state", {...})` |
| `update_state(agent_id, state_id, category, content)` | `_call_tool("cnaa_update_state", {...})` |
| `delete_state(agent_id, state_id)` | `_call_tool("cnaa_delete_state", {...})` |
| `get_preference(agent_id)` | `_call_tool("cnaa_get_preference", {...})` |
| `update_preference(agent_id, preference_id, key, value, ...)` | `_call_tool("cnaa_update_preference", {...})` |
| `delete_preference(agent_id, preference_id)` | `_call_tool("cnaa_delete_preference", {...})` |
| `get_environment(agent_id)` | `_call_tool("cnaa_get_environment", {...})` |
| `update_environment(agent_id, env_id, context)` | `_call_tool("cnaa_update_environment", {...})` |

---

### 5.2 `local/memory/instant_memory.py` — 即时记忆管理器

**文件职责：** 管理本地即时记忆的生命周期（创建 → 压缩 → 淘汰 → 清除）。

**依赖关系：** 导入 `cnaa.models`（InstantMemory, MemoryStatus）。

#### `InstantMemoryManager` 类

```
内部数据结构：
  _memories: dict[str, InstantMemory]
  键为 memory_id，值为 InstantMemory 对象

构造函数：
  __init__(agent_id: str)
    功能：初始化管理器
    内部逻辑：保存 agent_id，初始化空字典
```

| 方法 | 功能 | 时间复杂度 |
|------|------|-----------|
| `create_instant_memory(task_id, checkpoint_id, summary, memory_id, cnaa_ref?) -> InstantMemory` | 创建即时记忆 | O(1) |
| `get_memory(memory_id) -> InstantMemory \| None` | 按 ID 获取 | O(1) |
| `get_active_memories() -> list[InstantMemory]` | 获取所有活跃记忆 | O(n) |
| `get_condensed_memories() -> list[InstantMemory]` | 获取所有已压缩记忆 | O(n) |
| `condense_memory(memory_id) -> InstantMemory \| None` | 压缩单条记忆 | O(1) |
| `condense_old_memories(threshold_hours?) -> int` | 批量压缩旧记忆 | O(n) |
| `evict_memory(memory_id) -> InstantMemory \| None` | 淘汰单条记忆 | O(1) |
| `evict_old_memories(threshold_days?) -> int` | 批量淘汰旧记忆 | O(n) |
| `remove_evicted_memories() -> int` | 从存储中移除已淘汰记忆 | O(k) |
| `get_all_memories() -> list[InstantMemory]` | 获取所有记忆 | O(1) |
| `count() -> int` | 总数量 | O(1) |
| `count_by_status() -> dict[str, int]` | 按状态统计数量 | O(n) |
| `clear() -> None` | 清空所有记忆 | O(1) |

**`create_instant_memory` 算法详解：**

```
输入：task_id, checkpoint_id, summary, memory_id, cnaa_ref（可选）
算法：
  1. 构建 InstantMemory 对象：
     - status = MemoryStatus.ACTIVE
     - cnaa_ref = cnaa_ref 或自动生成 "cnaa://{agent_id}/{memory_id}"
     - timestamp = datetime.now()
  2. 存入 self._memories[memory_id] = instant
  3. 返回 instant 对象
```

**`condense_old_memories` 算法详解（基于时间的批量压缩）：**

```
输入：threshold_hours（默认 1.0 小时）
算法：
  1. now = datetime.now()
  2. condensed_count = 0
  3. 遍历 self._memories 中的所有 memory：
     a. 如果 memory.status != ACTIVE → 跳过（只压缩活跃记忆）
     b. 如果 memory.timestamp is None → 跳过
     c. 计算 age_hours = (now - memory.timestamp).total_seconds() / 3600
     d. 如果 age_hours >= threshold_hours：
        - memory.status = MemoryStatus.CONDENSED
        - condensed_count += 1
  4. 返回 condensed_count
```

**`evict_old_memories` 算法详解（基于时间的批量淘汰）：**

```
输入：threshold_days（默认 7.0 天）
算法：
  1. now = datetime.now()
  2. evicted_count = 0
  3. 遍历所有 memory：
     a. 如果 memory.status != CONDENSED → 跳过（只淘汰已压缩记忆）
     b. 如果 memory.timestamp is None → 跳过
     c. 计算 age_days = (now - memory.timestamp).total_seconds() / 86400
     d. 如果 age_days >= threshold_days：
        - memory.status = MemoryStatus.EVICTED
        - evicted_count += 1
  4. 返回 evicted_count
```

---

### 5.3 `local/state/state_cache.py` — 状态缓存

**文件职责：** 缓存从云端获取的 State/Preference/Environment 数据，减少网络调用。

**依赖关系：** 导入 `cnaa.models`（Environment, Preference, State）。

#### `StateCache` 类

```
内部数据结构：
  _states: list[State]              — 缓存的状态列表
  _preferences: list[Preference]    — 缓存的偏好列表
  _environment: Environment | None  — 缓存的环境
  _states_loaded: bool              — 状态是否已加载
  _preferences_loaded: bool         — 偏好是否已加载
  _environment_loaded: bool         — 环境是否已加载
  _last_updated: datetime | None    — 最后更新时间

构造函数：
  __init__(agent_id: str, ttl_minutes: float = 5.0)
    功能：初始化缓存
    内部逻辑：
      1. self.ttl = timedelta(minutes=ttl_minutes)
      2. 初始化所有数据为空/None
      3. 所有 loaded 标志为 False
```

| 方法 | 功能 | 时间复杂度 |
|------|------|-----------|
| `update_states(states) -> None` | 更新缓存的状态 | O(1) |
| `update_preferences(preferences) -> None` | 更新缓存的偏好 | O(1) |
| `update_environment(environment) -> None` | 更新缓存的环境 | O(1) |
| `get_states() -> list[State]` | 获取缓存的状态 | O(1) |
| `get_preferences() -> list[Preference]` | 获取缓存的偏好 | O(1) |
| `get_environment() -> Environment \| None` | 获取缓存的环境 | O(1) |
| `is_expired() -> bool` | 检查缓存是否过期 | O(1) |
| `is_states_expired() -> bool` | 检查状态缓存是否过期 | O(1) |
| `is_preferences_expired() -> bool` | 检查偏好缓存是否过期 | O(1) |
| `is_environment_expired() -> bool` | 检查环境缓存是否过期 | O(1) |
| `clear() -> None` | 清空所有缓存 | O(1) |
| `get_state_by_id(state_id) -> State \| None` | 按 ID 查找状态 | O(n) |
| `get_preference_by_id(pref_id) -> Preference \| None` | 按 ID 查找偏好 | O(n) |
| `get_states_by_category(category) -> list[State]` | 按类别过滤状态 | O(n) |
| `count() -> dict[str, int]` | 获取各项缓存数量 | O(1) |

**TTL 过期检查算法：**

```
is_expired() 算法：
  1. 如果 _last_updated is None → 返回 True（从未更新 = 已过期）
  2. 返回 (datetime.now() - _last_updated) > self.ttl

is_states_expired() 算法：
  1. 如果 not _states_loaded → 返回 True（从未加载 = 已过期）
  2. 返回 self.is_expired()  （委托给通用 TTL 检查）
```

---

### 5.4 `local/agent.py` — 本地 Agent 接口（主入口）

**文件职责：** **这是外部 Agent 框架集成 CNAA 的主入口。** 组合了三个本地组件：MCP 客户端、即时记忆管理器、状态缓存。

**依赖关系：**
- 导入 `cnaa.models`（Environment, Preference, State, StateCategory）
- 导入 `local.client.mcp_client.CNAA_MCPClient`
- 导入 `local.memory.instant_memory.InstantMemoryManager`
- 导入 `local.state.state_cache.StateCache`

#### `LocalAgentInterface` 类

```
构造函数：
  __init__(agent_id, server_url?, cloud_server?, cache_ttl_minutes?)
    功能：初始化本地 Agent 接口
    内部逻辑：
      1. self.agent_id = agent_id
      2. self.memory_manager = InstantMemoryManager(agent_id)
      3. self.state_cache = StateCache(agent_id, ttl_minutes=cache_ttl_minutes)
      4. self.mcp_client = CNAA_MCPClient(server_url=server_url)
      5. 如果 cloud_server 不为 None → self.mcp_client.set_mock_handler(cloud_server)
    被谁调用：外部 Agent 框架（如 OpenClaw）的集成代码
```

**记忆操作（通过 MCP 客户端 → 云端）：**

| 方法 | 功能 | 调用链 |
|------|------|--------|
| `store_memory(memory_id, type, content, ...)` | 存储记忆 | → `mcp_client.store_memory(agent_id, ...)` → `_call_tool("cnaa_store_memory", ...)` |
| `get_memory(memory_id)` | 获取记忆 | → `mcp_client.get_memory(agent_id, memory_id)` → `_call_tool("cnaa_get_memory", ...)` |
| `list_memories(type?, tags?)` | 列出记忆 | → `mcp_client.list_memories(agent_id, ...)` → `_call_tool("cnaa_list_memories", ...)` |
| `delete_memory(memory_id)` | 删除记忆 | → `mcp_client.delete_memory(agent_id, memory_id)` → `_call_tool("cnaa_delete_memory", ...)` |

**即时记忆操作（纯本地）：**

| 方法 | 功能 | 调用链 |
|------|------|--------|
| `create_instant_memory(task_id, checkpoint_id, summary, memory_id)` | 创建即时记忆 | → `memory_manager.create_instant_memory(...)` |
| `get_active_instant_memories()` | 获取活跃即时记忆 | → `memory_manager.get_active_memories()` |
| `condense_old_instant_memories(threshold_hours?)` | 压缩旧即时记忆 | → `memory_manager.condense_old_memories(...)` |

**状态操作（云端 + 本地缓存）：**

| 方法 | 功能 | 调用链 |
|------|------|--------|
| `get_states(use_cache?)` | 获取状态（带缓存） | 检查缓存 → `state_cache.get_states()` 或 → `mcp_client.get_state(agent_id)` → 更新缓存 |
| `update_state(state_id, category, content)` | 更新状态 | → `mcp_client.update_state(...)` → `state_cache.clear()` |
| `get_preferences(use_cache?)` | 获取偏好（带缓存） | 检查缓存 → `state_cache.get_preferences()` 或 → `mcp_client.get_preference(agent_id)` → 更新缓存 |
| `update_preference(preference_id, key, value, ...)` | 更新偏好 | → `mcp_client.update_preference(...)` → `state_cache.clear()` |
| `get_environment(use_cache?)` | 获取环境（带缓存） | 检查缓存 → `state_cache.get_environment()` 或 → `mcp_client.get_environment(agent_id)` → 更新缓存 |
| `update_environment(env_id, context)` | 更新环境 | → `mcp_client.update_environment(...)` → `state_cache.clear()` |

**`get_states` 带缓存读取算法详解：**

```
输入：use_cache（默认 True）
算法：
  1. 如果 use_cache 为 True 且 state_cache.is_states_expired() 为 False：
     → 直接从 state_cache.get_states() 获取
  2. 否则：
     a. 调用 mcp_client.get_state(agent_id) 从云端获取
     b. 如果 response["status"] == "ok"：
        - 调用 _update_state_cache(response["states"]) 更新缓存
        - 从 state_cache.get_states() 获取
     c. 否则返回空列表
  3. 将 State 对象序列化为 dict 列表返回
```

**`_update_state_cache` 辅助方法：**

```
输入：states_data — 从云端返回的状态 dict 列表
算法：
  1. 将每个 dict 转换为 State 对象：
     State(agent_id, state_id, category=StateCategory(category), content)
  2. 调用 state_cache.update_states(states)
```

---

## 6. 服务入口

### 6.1 `server.py` — HTTP 服务入口

**文件职责：** 提供 HTTP 服务，暴露 CNAA 的 MCP 工具能力。

**依赖关系：**
- 导入 `cloud.server.mcp_server.CNAA_MCPServer`
- 导入 `cnaa.schemas.get_all_schemas`
- 导入 `cnaa.security`（load_auth_config_from_env, validate_api_key, AuthConfig, AuthContext）

#### 端点一览

| 端点 | 方法 | 功能 |
|------|------|------|
| `GET /schemas` | GET | 返回所有 JSON Schema 定义 |
| `GET /health` | GET | 健康检查 |
| `POST /mcp` | POST | MCP 工具调用 |

#### `CNAARequestHandler` 类

```
类属性：
  cnaa_server: CNAA_MCPServer  — 服务端实例
  auth_config: AuthConfig      — 认证配置

do_GET() → 路由到 _handle_schemas() 或 _handle_health()
do_POST() → 路由到 _handle_mcp()
```

**`_handle_mcp()` 算法详解（核心 HTTP 处理函数）：**

```
算法：
  1. 读取请求体：
     - 获取 Content-Length
     - 读取 body 并 json.loads() 解析
  2. 提取 tool 和 arguments 字段
  3. 如果缺少 tool → 返回 400 错误
  4. 认证处理：
     a. 从 Authorization 头提取 Bearer token
     b. 如果认证启用且不允许匿名且无 token → 返回 401
     c. 如果有 token → 调用 validate_api_key() 验证
     d. 如果验证失败 → 返回 401
     e. 将 auth_context 注入 arguments
  5. 调用 cnaa_server.handle_tool_call(tool_name, arguments)
  6. 返回 JSON 响应
  7. 异常处理：
     - JSONDecodeError → 400
     - 其他异常 → 500
```

#### 启动函数

**`create_server(host, port) -> HTTPServer`**

```
算法：
  1. 调用 load_auth_config_from_env() 加载认证配置
  2. 设置 CNAARequestHandler.auth_config
  3. 创建 CNAA_MCPServer(auth_config=auth_config)
  4. 创建 HTTPServer((host, port), CNAARequestHandler)
  5. 返回 HTTPServer
```

**`main()`**

```
算法：
  1. 解析命令行参数（--host, --port）
  2. 调用 create_server(host, port)
  3. server.serve_forever()
  4. KeyboardInterrupt → server.shutdown()
```

---

### 6.2 `mcp_stdio_server.py` — Stdio MCP 服务入口

**文件职责：** 提供基于标准输入/输出的 MCP 服务，使用 JSON-RPC 2.0 协议。

**依赖关系：**
- 导入 `cloud.server.mcp_server.CNAA_MCPServer`
- 导入 `cnaa.tools.get_tool_definitions`

#### `CNAAStdioMCPServer` 类

```
构造函数：
  __init__()
    内部逻辑：
      1. self.cnaa_server = CNAA_MCPServer()
      2. self._initialized = False

run() — 主循环
  算法：
    1. 逐行读取 stdin
    2. json.loads() 解析每行
    3. 调用 handle_request(request)
    4. 如果 response 不为 None → _send_response(response)
    5. 异常处理：JSON 解析错误 → -32700，其他 → -32603

handle_request(request) -> dict | None
  算法：
    1. 提取 method, params, id
    2. 判断是否为通知（id is None）
    3. 方法路由：
       - "initialize" → _handle_initialize()
       - "notifications/initialized" → 设置 _initialized = True，返回 None
       - "tools/list" → _handle_tools_list()
       - "tools/call" → _handle_tools_call()
       - "ping" → 返回 {}
       - 其他 → 返回 -32601 错误
    4. 如果是通知 → 返回 None
    5. 否则返回 {"jsonrpc": "2.0", "result": result, "id": request_id}

_handle_tools_call(params) -> dict
  算法：
    1. 从 params 提取 tool_name 和 arguments
    2. 调用 cnaa_server.handle_tool_call(tool_name, arguments)
    3. 将结果包装为 MCP content 格式：
       {"content": [{"type": "text", "text": json.dumps(result)}]}
```

---

## 7. 完整调用链路图

### 7.1 记忆存储链路（从外部 Agent 到持久化）

```
外部 Agent 框架
    │
    ├─ [Python API 模式]
    │   │
    │   ├─ CloudAgentInterface.store_memory()
    │   │   └─ CNAA_MCPServer.handle_tool_call("cnaa_store_memory", args)
    │   │       ├─ 权限检查：check_permission(auth_context, "write")
    │   │       ├─ agent_id 一致性校验
    │   │       └─ _handle_store_memory(args)
    │   │           ├─ 构建 Memory 对象（from cnaa.models）
    │   │           └─ InMemoryMemoryStore.store_memory(memory)
    │   │               └─ self._memories[(agent_id, memory_id)] = memory
    │   │
    │   └─ LocalAgentInterface.store_memory()
    │       └─ CNAA_MCPClient.store_memory(agent_id, ...)
    │           └─ _call_tool("cnaa_store_memory", {...})
    │               └─ mock_handler.handle_tool_call(...)
    │                   └─ [同上 CNAA_MCPServer.handle_tool_call 流程]
    │
    └─ [HTTP 模式]
        │
        └─ POST /mcp {"tool": "cnaa_store_memory", "arguments": {...}}
            └─ CNAARequestHandler._handle_mcp()
                ├─ 解析 JSON 请求体
                ├─ validate_api_key() — 认证
                └─ CNAA_MCPServer.handle_tool_call(...)
                    └─ [同上流程]
```

### 7.2 带缓存的状态读取链路

```
LocalAgentInterface.get_states(use_cache=True)
    │
    ├─ [缓存命中]
    │   └─ state_cache.is_states_expired() == False
    │       └─ state_cache.get_states() → 返回缓存的 State 列表
    │
    └─ [缓存未命中/过期]
        └─ mcp_client.get_state(agent_id)
            └─ _call_tool("cnaa_get_state", {"agent_id": ...})
                └─ CNAA_MCPServer.handle_tool_call("cnaa_get_state", ...)
                    └─ _handle_get_state(args)
                        └─ InMemoryStateStore.get_state(agent_id)
                            └─ 线性扫描 _states 字典
        └─ _update_state_cache(response["states"])
            ├─ 将 dict 列表转换为 State 对象列表
            └─ state_cache.update_states(states)
                ├─ self._states = states
                ├─ self._states_loaded = True
                └─ self._last_updated = datetime.now()
```

### 7.3 即时记忆生命周期链路

```
LocalAgentInterface
    │
    ├─ create_instant_memory(task_id, checkpoint_id, summary, memory_id)
    │   └─ InstantMemoryManager.create_instant_memory(...)
    │       ├─ 构建 InstantMemory(status=ACTIVE, cnaa_ref="cnaa://...")
    │       └─ _memories[memory_id] = instant
    │
    ├─ get_active_instant_memories()
    │   └─ InstantMemoryManager.get_active_memories()
    │       └─ 列表推导：[mem for mem in _memories.values() if mem.status == ACTIVE]
    │
    └─ condense_old_instant_memories(threshold_hours=1.0)
        └─ InstantMemoryManager.condense_old_memories(threshold_hours)
            ├─ 遍历所有 memory
            ├─ 如果 status == ACTIVE 且 age >= threshold → status = CONDENSED
            └─ 返回压缩数量
```

---

## 8. 核心算法详解

### 8.1 记忆生命周期状态机

```
                    ┌──────────────┐
                    │   CREATED    │
                    │  (刚创建)     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
            ┌──────│    ACTIVE     │
            │      │  (活跃可用)   │
            │      └──────┬───────┘
            │             │  超过 condensation_threshold (默认 1h)
            │             │  或调用 condense_memory()
            │             ▼
            │      ┌──────────────┐
            │      │  CONDENSED   │
            │      │  (已压缩)     │
            │      └──────┬───────┘
            │             │  超过 eviction_threshold (默认 7d)
            │             │  或调用 evict_memory()
            │             ▼
            │      ┌──────────────┐
            └─────▶│   EVICTED    │
                   │  (已淘汰)     │
                   └──────────────┘
```

**时间判定算法（TimeBasedLifecyclePlugin）：**

```
判断是否压缩：
  条件：memory.status == ACTIVE
  条件：memory.timestamp 不为 None
  条件：(当前时间 - memory.timestamp) >= condensation_threshold
  三个条件全满足 → 应压缩

判断是否淘汰：
  条件：memory.status == CONDENSED
  条件：memory.timestamp 不为 None
  条件：(当前时间 - memory.timestamp) >= eviction_threshold
  三个条件全满足 → 应淘汰

判断是否提升为长期记忆：
  条件：memory.type == SHORT_TERM
  条件：memory.completion_score >= promotion_score_threshold (默认 0.5)
  两个条件全满足 → 应提升
```

### 8.2 状态演化三阶段模型

```
┌─────────────────┐     多条相关经验积累     ┌─────────────────┐
│  ACCUMULATED    │ ──────────────────────▶ │   ASSOCIATED    │
│  (持续写入)     │                         │  (建立关联)      │
└─────────────────┘                         └────────┬────────┘
                                                     │
                                          长期未访问   │
                                                     ▼
                                            ┌─────────────────┐
                                            │     DECAYED     │
                                            │   (优先级衰减)   │
                                            └─────────────────┘
```

默认实现中 `should_evolve()` 始终返回 `False`（不自动演化），需要外部包实现自定义演化策略。

### 8.3 TTL 缓存失效算法

```
StateCache 使用写时记录时间戳 + 读时检查过期 的策略：

写入时：
  update_states() / update_preferences() / update_environment()
    → 记录 _last_updated = datetime.now()
    → 设置对应 _loaded = True

读取时：
  is_states_expired() / is_preferences_expired() / is_environment_expired()
    → 先检查 _loaded 标志（未加载 = 过期）
    → 再检查 (now - _last_updated) > ttl

特点：
  - 三种数据类型共享同一个 _last_updated 时间戳
  - 任一种类型的写入都会更新全局时间戳
  - TTL 默认 5 分钟
  - 更新操作（update_state 等）会调用 state_cache.clear() 使缓存失效
```

### 8.4 O(1) 权限检查算法

```
TOOL_PERMISSION_MAP 将 13 个工具分为两类：
  "read"  — GET_MEMORY, LIST_MEMORIES, GET_STATE, GET_PREFERENCE, GET_ENVIRONMENT
  "write" — STORE_MEMORY, DELETE_MEMORY, TAG_SHORT_TERM, UPDATE_*, DELETE_*

check_permission() 的判定逻辑：
  1. auth_context is None → True（认证未启用，全部放行）
  2. permission == ADMIN → True（管理员通吃）
  3. required == "read" → READ_ONLY 和 READ_WRITE 都放行
  4. required == "write" → 仅 READ_WRITE 放行
  5. 其他 → False

时间复杂度：O(1)，纯条件判断，无循环
```

---

## 9. 如何修改与扩展

### 9.1 修改接口格式

如果你想改变某个工具的输入/输出格式：

1. 打开 `cnaa/schemas.py`
2. 找到对应的 Schema 常量（如 `STORE_MEMORY_REQUEST`）
3. 修改 `properties` 和 `required` 字段
4. 在 `cnaa/models.py` 中修改对应的 dataclass
5. 在 `cloud/server/mcp_server.py` 的 `_handle_*` 方法中更新字段提取逻辑

### 9.2 替换存储后端

当前使用内存字典存储。要替换为 SQLite/PostgreSQL：

1. 创建新文件如 `cloud/storage/sqlite_memory_store.py`
2. 实现 `MemoryInterface` 的所有抽象方法
3. 在 `CNAA_MCPServer.__init__()` 中传入你的实现：
   ```python
   server = CNAA_MCPServer(
       memory_store=SQLiteMemoryStore("data.db"),
       state_store=SQLiteStateStore("data.db"),
   )
   ```

### 9.3 添加新的 MCP 工具

1. 在 `cnaa/schemas.py` 中添加请求/响应 Schema
2. 在 `cnaa/tools.py` 中添加工具名称常量和定义
3. 在 `cloud/server/mcp_server.py` 中：
   - 添加 `_handle_xxx()` 处理函数
   - 在 `_register_tool_handlers()` 中注册映射
4. 在 `cnaa/tools.py` 的 `TOOL_PERMISSION_MAP` 中添加权限映射
5. 在 `local/client/mcp_client.py` 中添加对应的客户端方法

### 9.4 实现自定义生命周期策略

```python
from cnaa.lifecycle import MemoryLifecyclePlugin

class MyCustomLifecyclePlugin(MemoryLifecyclePlugin):
    def should_condense(self, memory, now=None):
        # 你的压缩逻辑（如基于重要度、访问频率等）
        ...

    def should_evict(self, memory, now=None):
        # 你的淘汰逻辑
        ...

    def condense_memory(self, memory):
        memory.status = MemoryStatus.CONDENSED
        return memory

    def evict_memory(self, memory):
        memory.status = MemoryStatus.EVICTED
        return memory

    def should_promote_to_long_term(self, memory):
        # 你的提升逻辑
        ...

# 注册插件
plugins = LifecyclePlugins()
plugins.register_memory_lifecycle_plugin(MyCustomLifecyclePlugin())
```

### 9.5 实现自定义检索插件

```python
from cnaa.lifecycle import RetrievalPlugin

class VectorRetrievalPlugin(RetrievalPlugin):
    def index(self, memory):
        # 使用 embedding 模型生成向量并存入向量数据库
        ...

    def search(self, query, agent_id, limit=5, filters=None):
        # 向量相似度搜索
        ...

    def recall(self, context, agent_id, limit=5):
        # 基于上下文的记忆召回
        ...

    def delete(self, memory_id):
        # 从向量数据库中删除
        ...
```

### 9.6 集成到你的 Agent 框架

```python
from local.agent import LocalAgentInterface

# 为你的 Agent 创建接口
agent_interface = LocalAgentInterface(
    agent_id="your-agent-id",
    server_url="http://localhost:8080",  # CNAA 服务地址
    cache_ttl_minutes=5.0,               # 缓存 TTL
)

# 存储经验
agent_interface.store_memory(
    memory_id="mem-001",
    memory_type="long_term",
    content={"task": "完成的任务", "result": "成功"},
    tags=["task-complete"],
    completion_score=0.95,
)

# 创建本地即时记忆
agent_interface.create_instant_memory(
    task_id="task-001",
    checkpoint_id="cp-001",
    summary="完成了某某任务",
    memory_id="mem-001",
)

# 获取积累的知识
states = agent_interface.get_states()
preferences = agent_interface.get_preferences()
```

---

## 附录：文件依赖关系总览

```
server.py
  ├── cloud/server/mcp_server.py (CNAA_MCPServer)
  │     ├── cnaa/models.py (Memory, State, Preference, Environment, ...)
  │     ├── cnaa/security.py (AuthConfig, check_permission, ...)
  │     ├── cnaa/tools.py (工具常量, get_tool_definitions, TOOL_PERMISSION_MAP)
  │     │     └── cnaa/schemas.py (请求 Schema 常量)
  │     ├── cloud/storage/memory_store.py (InMemoryMemoryStore)
  │     │     ├── cnaa/models.py
  │     │     └── cnaa/interaction.py (MemoryInterface)
  │     └── cloud/storage/state_store.py (InMemoryStateStore)
  │           ├── cnaa/models.py
  │           └── cnaa/interaction.py (StateInterface)
  ├── cnaa/schemas.py (get_all_schemas)
  └── cnaa/security.py (load_auth_config_from_env, validate_api_key)

mcp_stdio_server.py
  ├── cloud/server/mcp_server.py (CNAA_MCPServer)
  └── cnaa/tools.py (get_tool_definitions)

local/agent.py (LocalAgentInterface)
  ├── local/client/mcp_client.py (CNAA_MCPClient)
  ├── local/memory/instant_memory.py (InstantMemoryManager)
  │     └── cnaa/models.py (InstantMemory, MemoryStatus)
  └── local/state/state_cache.py (StateCache)
        └── cnaa/models.py (State, Preference, Environment)

cloud/agent.py (CloudAgentInterface)
  └── cloud/server/mcp_server.py (CNAA_MCPServer)

cnaa/lifecycle.py
  └── cnaa/models.py (InstantMemory, Memory, MemoryStatus, MemoryType, SearchResult, TaskCheckpoint)
```

---

> **提示：** 如果你发现文档与代码不一致，欢迎提交 Issue 或 PR 进行修正。
