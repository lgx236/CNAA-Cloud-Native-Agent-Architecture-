# CNAA V0.1 接口规范文档

> Cloud Native Agentic Architecture - Interface Specification
>
> 版本：v0.1.0

---

## 1. 概述

CNAA（Cloud Native Agentic Architecture）是一个面向 AI Agent 的经验记忆运行时框架。本文档定义了 CNAA 的核心接口规范，包括：

- **数据模型**：记忆、状态、偏好、环境等核心数据结构
- **交互接口**：本地与云端之间的操作契约
- **MCP 工具**：通过 MCP 协议暴露的工具定义
- **生命周期**：记忆和状态的状态流转规则

### 1.1 架构模式

```
云端（单一）
┌──────────────────────────────────────┐
│           CNAA Server                │
│         (MCP Server)                 │
│                                      │
│  · 远期记忆持久化                     │
│  · State 管理（preference/知识沉淀）   │
│  · Environment 状态                  │
│  · MCP 工具暴露                       │
└──────────────┬───────────────────────┘
               │ MCP over HTTP
               │ (Streamable HTTP)
      ┌────────┼────────┐
      ▼        ▼        ▼
┌──────────┐┌──────────┐┌──────────┐
│ Agent 1  ││ Agent 2  ││ Agent N  │   本地（多实例）
│(MCP Cli) ││(MCP Cli) ││(MCP Cli) │
│          ││          ││          │
│·近期记忆  ││·近期记忆  ││·近期记忆  │
│·本地沉淀  ││·本地沉淀  ││·本地沉淀  │
└──────────┘└──────────┘└──────────┘

多地同智能体：多个本地实例共享同一云端状态
```

### 1.2 核心交互流

```
Agent 完成任务点 → 压缩完整记忆 → 通过 MCP tool 上传远期记忆至云端
                                    ↓
Agent 需要回溯  → 通过 MCP tool 请求远期记忆 / state
                                    ↓
Agent 初始化    → 通过 MCP tool 请求 preference / environment
                                    ↓
知识沉淀        → 重要记忆 → preference，短期知识 → state
```

---

## 2. 数据模型

### 2.1 Memory（记忆）

记忆是 CNAA 的核心经验单元。

```json
{
  "memory_id": "string",           // 记忆唯一标识
  "agent_id": "string",            // 所属 Agent 标识
  "type": "long_term | short_term", // 记忆类型：远期/近期
  "content": {},                    // 记忆内容（开放 JSON 结构）
  "tags": ["string"],               // 记忆标签（用于检索）
  "completion_score": 0.0,          // 任务完成度 [0.0, 1.0]
  "timestamp": "ISO-8601",          // 记忆时间戳
  "metadata": {}                    // 可选扩展元数据
}
```

**说明**：
- `content` 是开放的 JSON 结构，CNAA 不解释或推理其内容（哑服务原则）
- `type` 决定存储位置：`long_term` 存云端，`short_term` 存本地
- `tags` 用于记忆检索和分类

### 2.2 TaskCheckpoint（任务点）

任务点代表一个已完成的任务节点，包含压缩后的完整记忆。

```json
{
  "task_id": "string",              // 任务标识
  "checkpoint_id": "string",        // 任务点唯一标识
  "compressed_memory": {            // 压缩后的完整记忆（存云端）
    "memory_id": "string",
    "agent_id": "string",
    "type": "long_term",
    "content": {},
    "tags": [],
    "completion_score": 0.0,
    "timestamp": "ISO-8601"
  },
  "summary": "string",              // 轻量摘要（存本地即时记忆）
  "completion_score": 0.0,          // 任务完成度
  "timestamp": "ISO-8601"           // 任务点时间戳
}
```

**流程**：
```
Agent 完成任务点 → 压缩为 TaskCheckpoint →
  完整数据（compressed_memory）存云端 →
  轻量摘要（summary）存本地即时记忆
```

### 2.3 State（状态）

状态是 Agent 从经验中沉淀的知识。

```json
{
  "agent_id": "string",             // 所属 Agent 标识
  "state_id": "string",             // 状态唯一标识
  "category": "preference | knowledge | environment", // 状态分类
  "content": {},                    // 状态内容（JSON）
  "updated_at": "ISO-8601"          // 最后更新时间
}
```

**分类说明**：
- `preference`：重要记忆模式，塑造 Agent 行为
- `knowledge`：从经验中积累的知识
- `environment`：Agent 运行的环境上下文

### 2.4 Preference（偏好）

偏好是 Agent 的重要记忆模式，影响决策行为。

```json
{
  "agent_id": "string",             // 所属 Agent 标识
  "preference_id": "string",        // 偏好唯一标识
  "key": "string",                  // 偏好键/标签
  "value": {},                      // 偏好内容（JSON）
  "importance": 0.0,                // 重要度 [0.0, 1.0]
  "source_memory_ids": ["string"]   // 来源记忆标识列表
}
```

### 2.5 Environment（环境）

环境是 Agent 运行的上下文信息。

```json
{
  "agent_id": "string",             // 所属 Agent 标识
  "env_id": "string",               // 环境唯一标识
  "context": {},                    // 环境上下文（JSON）
  "updated_at": "ISO-8601"          // 最后更新时间
}
```

### 2.6 InstantMemory（即时记忆）

即时记忆是本地短期记忆，包含指向云端远期记忆的引用。

```json
{
  "memory_id": "string",            // 记忆唯一标识
  "task_id": "string",              // 关联任务标识
  "checkpoint_id": "string",        // 关联任务点标识
  "summary": "string",              // 轻量摘要
  "status": "active | condensed | evicted", // 状态
  "cnaa_ref": "string",             // 指向云端远期记忆的引用
  "timestamp": "ISO-8601"           // 生成时间
}
```

**生命周期**：
```
active（活跃）→ condensed（沉淀为索引）→ evicted（淘汰）
```

- `active`：完整摘要可用
- `condensed`：缩减为索引指针，需通过 `cnaa_ref` 拉取完整数据
- `evicted`：从本地上下文移除

---

## 3. 交互接口

### 3.1 记忆操作接口

#### store_memory — 上传远期记忆

**功能**：将记忆持久化到 CNAA 云端

**请求**：
```json
{
  "agent_id": "string",
  "memory_id": "string",
  "content": {},
  "tags": ["string"],
  "completion_score": 0.0,
  "metadata": {}
}
```

**响应**：
```json
{
  "status": "ok",
  "memory_id": "string"
}
```

#### get_memory — 请求远期记忆

**功能**：从云端拉取完整记忆数据

**请求**：
```json
{
  "agent_id": "string",
  "memory_id": "string"
}
```

**响应**：
```json
{
  "memory_id": "string",
  "agent_id": "string",
  "content": {},
  "tags": ["string"],
  "completion_score": 0.0,
  "timestamp": "ISO-8601",
  "metadata": {}
}
```

#### list_memories — 列出记忆

**功能**：列出 Agent 的记忆（支持过滤）

**请求**：
```json
{
  "agent_id": "string",
  "type": "long_term | short_term",  // 可选
  "tags": ["string"]                 // 可选
}
```

**响应**：
```json
{
  "memories": [
    {
      "memory_id": "string",
      "tags": ["string"],
      "completion_score": 0.0,
      "timestamp": "ISO-8601"
    }
  ]
}
```

#### tag_short_term — 标记近期记忆标签

**功能**：为近期记忆添加标签，用于后续检索或知识沉淀

**请求**：
```json
{
  "agent_id": "string",
  "tags": ["string"]
}
```

**响应**：
```json
{
  "status": "ok"
}
```

#### delete_memory — 删除记忆

**功能**：从云端删除记忆

**请求**：
```json
{
  "agent_id": "string",
  "memory_id": "string"
}
```

**响应**：
```json
{
  "status": "ok"
}
```

### 3.2 状态操作接口

#### get_state — 请求 State

**功能**：获取 Agent 的所有状态（知识沉淀）

**请求**：
```json
{
  "agent_id": "string"
}
```

**响应**：
```json
{
  "states": [
    {
      "state_id": "string",
      "category": "preference | knowledge | environment",
      "content": {},
      "updated_at": "ISO-8601"
    }
  ]
}
```

#### update_state — 更新 State

**功能**：创建或更新状态条目

**请求**：
```json
{
  "agent_id": "string",
  "state_id": "string",
  "category": "preference | knowledge | environment",
  "content": {}
}
```

**响应**：
```json
{
  "status": "ok"
}
```

#### delete_state — 删除 State

**功能**：删除状态条目

**请求**：
```json
{
  "agent_id": "string",
  "state_id": "string"
}
```

**响应**：
```json
{
  "status": "ok"
}
```

#### get_preference — 请求 Preference

**功能**：获取 Agent 的所有偏好（重要记忆模式）

**请求**：
```json
{
  "agent_id": "string"
}
```

**响应**：
```json
{
  "preferences": [
    {
      "preference_id": "string",
      "key": "string",
      "value": {},
      "importance": 0.0,
      "source_memory_ids": ["string"]
    }
  ]
}
```

#### update_preference — 更新 Preference

**功能**：创建或更新偏好条目

**请求**：
```json
{
  "agent_id": "string",
  "preference_id": "string",
  "key": "string",
  "value": {},
  "importance": 0.0,
  "source_memory_ids": ["string"]
}
```

**响应**：
```json
{
  "status": "ok"
}
```

#### delete_preference — 删除 Preference

**功能**：删除偏好条目

**请求**：
```json
{
  "agent_id": "string",
  "preference_id": "string"
}
```

**响应**：
```json
{
  "status": "ok"
}
```

#### get_environment — 请求 Environment

**功能**：获取 Agent 的环境上下文

**请求**：
```json
{
  "agent_id": "string"
}
```

**响应**：
```json
{
  "env_id": "string",
  "context": {},
  "updated_at": "ISO-8601"
}
```

#### update_environment — 更新 Environment

**功能**：创建或更新环境上下文

**请求**：
```json
{
  "agent_id": "string",
  "env_id": "string",
  "context": {}
}
```

**响应**：
```json
{
  "status": "ok"
}
```

---

## 4. MCP 工具定义

CNAA Server 通过 MCP 协议暴露以下工具：

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `cnaa_store_memory` | 上传远期记忆 | Memory JSON | `{status, memory_id}` |
| `cnaa_get_memory` | 请求远期记忆 | `agent_id`, `memory_id` | Memory JSON |
| `cnaa_list_memories` | 列出记忆 | `agent_id`, `type?`, `tags?` | `{memories: []}` |
| `cnaa_tag_short_term` | 标记近期记忆标签 | `agent_id`, `tags` | `{status}` |
| `cnaa_delete_memory` | 删除记忆 | `agent_id`, `memory_id` | `{status}` |
| `cnaa_get_state` | 请求 State | `agent_id` | `{states: []}` |
| `cnaa_update_state` | 更新 State | `agent_id`, State JSON | `{status}` |
| `cnaa_delete_state` | 删除 State | `agent_id`, `state_id` | `{status}` |
| `cnaa_get_preference` | 请求 Preference | `agent_id` | `{preferences: []}` |
| `cnaa_update_preference` | 更新 Preference | `agent_id`, Preference JSON | `{status}` |
| `cnaa_delete_preference` | 删除 Preference | `agent_id`, `preference_id` | `{status}` |
| `cnaa_get_environment` | 请求 Environment | `agent_id` | Environment JSON |
| `cnaa_update_environment` | 更新 Environment | `agent_id`, Environment JSON | `{status}` |

### 4.1 工具调用示例

**上传远期记忆**：
```json
// 请求
{
  "agent_id": "agent-001",
  "memory_id": "mem-20240101-001",
  "content": {
    "task_description": "数据库迁移任务",
    "steps_completed": ["备份数据", "创建新schema"],
    "issues_encountered": ["字段类型不兼容"]
  },
  "tags": ["database", "migration"],
  "completion_score": 0.65
}

// 响应
{
  "status": "ok",
  "memory_id": "mem-20240101-001"
}
```

**请求远期记忆**：
```json
// 请求
{
  "agent_id": "agent-001",
  "memory_id": "mem-20240101-001"
}

// 响应
{
  "memory_id": "mem-20240101-001",
  "agent_id": "agent-001",
  "content": {
    "task_description": "数据库迁移任务",
    "steps_completed": ["备份数据", "创建新schema"],
    "issues_encountered": ["字段类型不兼容"]
  },
  "tags": ["database", "migration"],
  "completion_score": 0.65,
  "timestamp": "2024-01-01T10:30:00Z"
}
```

**请求 Preference**：
```json
// 请求
{
  "agent_id": "agent-001"
}

// 响应
{
  "preferences": [
    {
      "preference_id": "pref-001",
      "key": "coding_style",
      "value": {
        "prefer_type_hints": true,
        "max_line_length": 100
      },
      "importance": 0.8,
      "source_memory_ids": ["mem-20240101-001", "mem-20240102-003"]
    }
  ]
}
```

---

## 5. 生命周期规则

### 5.1 即时记忆生命周期

```
created → active → condensed → evicted
（生成）   （可用）   （沉淀）      （淘汰）
```

| 状态 | 含义 | 触发条件 |
|------|------|----------|
| `active` | 完整摘要可用 | 刚从任务点生成 |
| `condensed` | 缩减为索引指针 | 超过沉淀阈值（如1小时） |
| `evicted` | 从本地移除 | 超过淘汰阈值（如7天） |

### 5.2 记忆沉淀流程

```
1. Agent 完成任务点
   ↓
2. 压缩完整数据 → 远期记忆（存云端）
   ↓
3. 生成轻量摘要 → 即时记忆（存本地）
   ↓
4. 即时记忆老化 → 沉淀为索引指针
   ↓
5. 需要时通过 cnaa_ref 拉取完整数据
```

### 5.3 状态演化

```
accumulated → associated → decayed
（积累）       （关联）       （衰减）
```

| 阶段 | 含义 |
|------|------|
| `accumulated` | 经验数据持续写入 |
| `associated` | 跨任务经验建立关联 |
| `decayed` | 长期未引用的经验降低优先级 |

---

## 6. 设计原则

### 6.1 哑服务原则（Dumb Service）

CNAA Server 仅接收结构化 JSON 请求并返回结构化 JSON 响应。不执行推理，不运行 LLM，不生成内容。

```
Agent ──▶ JSON 请求 ──▶ CNAA Server ──▶ JSON 响应 ──▶ Agent
```

### 6.2 接口优先原则（Interface First）

所有能力先定义接口契约，再提供实现。接口契约是框架的核心交付物，具体实现是可替换的参考。

### 6.3 可插拔原则（Pluggable）

存储层、检索层均通过插件接口接入。替换任何一层不影响其他层的行为。

### 6.4 本地优先原则（Local First）

Agent 在本地运行，CNAA Server 在云端运行。即时记忆保留在 Agent 本地上下文中，完整经验数据存储在云端。

---

## 7. 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 经验记忆 | Experience Memory | Agent 在任务执行过程中产生的可复用知识 |
| 任务点 | Task Checkpoint | 任务执行流中的一个可评测节点，包含完整任务快照 |
| 即时记忆 | Instant Memory | 任务点的轻量摘要，保留在 Agent 本地 context 中 |
| 远期记忆 | Long-term Memory | 持久化在云端的完整记忆数据 |
| 近期记忆 | Short-term Memory | 保留在 Agent 本地上下文的记忆 |
| 状态 | State | 从经验中沉淀的知识 |
| 偏好 | Preference | 重要记忆模式，影响 Agent 行为 |
| 环境 | Environment | Agent 运行的上下文信息 |
| 伪连续记忆 | Pseudo-Continuous Memory | 通过"即时记忆索引 + 云端完整数据"模拟的记忆连续性 |
| 哑服务 | Dumb Service | 仅做 JSON 存取、不执行推理的服务模式 |
| 沉淀 | Condense | 即时记忆从完整摘要退化为索引指针的过程 |
| 淘汰 | Evict | 即时记忆从本地 context 中移除的过程 |

---

## 8. 安全与认证

### 概述

CNAA v0.1 支持可选的 API 密钥认证和读写权限控制。认证机制默认关闭，可通过环境变量启用，确保向后兼容。

### 启用认证

通过环境变量配置：

```bash
CNAA_AUTH_ENABLED=true
CNAA_API_KEYS={"sk-cnaa-001": {"agent_id": "agent-001", "permission": "read_write"}}
CNAA_ALLOW_UNAUTHENTICATED=false
```

### 请求认证

在 HTTP 请求中添加 `Authorization` 头：

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-cnaa-001" \
  -d '{"tool": "cnaa_store_memory", "arguments": {...}}'
```

### 权限级别

| 权限级别 | 值 | 读操作 | 写操作 | 说明 |
|---------|---|-------|-------|------|
| READ_ONLY | `read_only` | ✓ | ✗ | 仅读取记忆和状态 |
| READ_WRITE | `read_write` | ✓ | ✓ | 读写权限（默认） |
| ADMIN | `admin` | ✓ | ✓ | 管理员，可跨租户操作 |

### 工具权限分类

**读操作**（需要 `read_only` 及以上权限）：
- `cnaa_get_memory`、`cnaa_list_memories`、`cnaa_search_memories`、`cnaa_recall_memories`
- `cnaa_get_state`、`cnaa_get_preference`、`cnaa_get_environment`

**写操作**（需要 `read_write` 及以上权限）：
- `cnaa_store_memory`、`cnaa_delete_memory`
- `cnaa_update_state`、`cnaa_delete_state`
- `cnaa_update_preference`、`cnaa_update_environment`

### Agent ID 隔离

启用认证后：
- API 密钥绑定特定的 `agent_id`
- 请求中的 `agent_id` 必须与密钥关联的 `agent_id` 匹配
- 读操作不匹配时返回 `null`（隐形拒绝）
- 写操作不匹配时返回错误响应

### 错误响应

| HTTP 状态码 | 场景 | 响应示例 |
|-----------|------|--------|
| 401 | 无效或缺失的 API 密钥 | `{"status": "error", "message": "Invalid or missing API key"}` |
| 200 | 权限不足 | `{"status": "error", "message": "Permission denied: read_only cannot perform write"}` |
| 200 | Agent ID 不匹配 | `{"status": "error", "message": "Agent ID mismatch..."}` |

---

## 9. 版本历史

- **v0.1.0**（2024-01）：初始版本，定义核心数据模型、交互接口、MCP 工具、生命周期规则
