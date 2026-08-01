# CNAA 架构设想 v0.1

> Cloud Native Agentic Architecture
>
> 面向 AI Agent 的经验记忆运行时框架

---

## 1. 项目定位

CNAA 是一个 **Experience Runtime Framework（经验记忆运行时框架）**。

它不是 Agent 框架，不是 Workflow 引擎，不是 RAG 实现。

CNAA 提供一套**架构规范与参考实现**，让任何 AI Agent 在**无需修改推理逻辑**的前提下，实现经验的持久化沉淀、跨会话检索与伪连续记忆。

### 1.1 核心主张

- **智能与记忆解耦**：Agent 负责推理与决策，CNAA 负责经验的存储、检索与生命周期管理
- **架构即产品**：CNAA 的核心交付物是架构规范本身，而非某个固定服务
- **极强可定制性**：clone 后可自由替换存储层、检索策略、生命周期规则，一切通过接口解耦

### 1.2 边界声明

| CNAA 负责 | CNAA 不负责 |
|-----------|------------|
| 经验数据的读写接口 | Agent 的推理与规划 |
| 任务点的持久化存储 | 任务执行与评测 |
| 即时记忆的沉淀规则 | 即时记忆的内容生成 |
| 检索能力的插件接口 | 具体的 RAG / 向量检索实现 |
| MCP 通信协议 | Agent 内部通信 |

---

## 2. 设计原则

### 2.1 哑服务原则

CNAA Server 是"哑"的——仅接收结构化 JSON 请求，返回结构化 JSON 响应。不执行推理、不运行 LLM、不生成内容、不做业务转换。

```
Agent ──JSON──▶ CNAA Server ──JSON──▶ Agent
         请求              响应
```

### 2.2 接口优先原则

所有能力先定义接口契约，再提供实现。接口契约是框架的核心交付物，实现是可替换的参考。

### 2.3 可插拔原则

存储层、检索层、Agent 适配层均通过插件接口接入。替换任何一层不影响其他层。

### 2.4 本地优先原则

Agent 在本地运行，CNAA 在云端运行。即时记忆保留在 Agent 本地上下文中，完整经验数据存储在云端。

---

## 3. 核心概念

### 3.1 任务点（Task Checkpoint）

任务点是 CNAA 的基本经验单元。

Agent 在评测环境中推进任务，每到达一个任务点即评测完成度，并将完整任务数据上传至 CNAA。

```
任务执行流
│
├── 任务点 A（完成度 0.3）──▶ 上传完整数据至 CNAA
├── 任务点 B（完成度 0.6）──▶ 上传完整数据至 CNAA
└── 任务点 C（完成度 1.0）──▶ 上传完整数据至 CNAA
```

**任务点边界由 Agent 自行定义**，CNAA 提供开放的接入接口，不强制任务点的粒度规则。

### 3.2 即时记忆（Instant Memory）

即时记忆是任务点的轻量摘要，保留在 Agent 的上下文中。

```
任务点完整数据（重量）──▶ 存储于 CNAA 云端
即时记忆摘要（轻量）  ──▶ 保留在 Agent 本地 context
```

即时记忆的核心作用：
- **快速定位**：当任务中断后，Agent 通过即时记忆快速了解"上次做到哪了"
- **按需回溯**：通过即时记忆中的引用指针，经 MCP 协议从 CNAA 拉取完整任务细节
- **伪连续性**：多个即时记忆在 Agent 上下文中沉淀与淘汰，以"小索引 → 大存储"模式模拟记忆的连续性

### 3.3 伪连续记忆（Pseudo-Continuous Memory）

```
Agent 启动
    │
    ▼
加载即时记忆列表（轻量摘要，若干条）
    │
    ▼
Agent 根据摘要判断当前状态
    │
    ├── 需要细节 ──▶ 通过 MCP 从 CNAA 拉取完整任务点
    │
    └── 不需要细节 ──▶ 继续执行
```

即时记忆的沉淀机制：
- 多个即时记忆参与沉淀与淘汰
- 旧摘要可沉淀为索引指针，仅保留关键信息
- 需要时通过指针从 CNAA 重新获取完整数据

---

## 4. 三层架构

CNAA 采用三层正交架构。三层分别回答不同维度的问题，互不耦合。

```
┌───────────────────────────────────────────────────────┐
│              CNAA Experience Runtime Framework         │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │           接口契约层（Interface Contract）        │  │
│  │                                                 │  │
│  │   回答：框架能做什么？（What）                    │  │
│  │   职责：定义数据模型、操作契约、协议格式、插件接口  │  │
│  │   不包含：任何执行逻辑                            │  │
│  └──────────────────────┬──────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐  │
│  │              运行时层（Runtime）                   │  │
│  │                                                 │  │
│  │   回答：框架怎么跑？（How）                       │  │
│  │   职责：提供执行环境，实现接口契约                  │  │
│  │   不包含：状态流转规则                              │  │
│  │                                                 │  │
│  │   ┌─────────────────┐  ┌──────────────────────┐ │  │
│  │   │  Local Runtime   │  │  Remote Runtime      │ │  │
│  │   │  （本地 SDK）     │  │  （CNAA Server）     │ │  │
│  │   │                  │  │                      │ │  │
│  │   │ · 即时记忆管理   │  │ · 经验持久化         │ │  │
│  │   │ · MCP Client     │  │ · MCP Server         │ │  │
│  │   │ · 上下文注入     │  │ · 插件调度           │ │  │
│  │   └─────────────────┘  └──────────────────────┘ │  │
│  └─────────────────────────────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐  │
│  │            生命周期层（Lifecycle）                 │  │
│  │                                                 │  │
│  │   回答：经验怎么变？（When）                      │  │
│  │   职责：管理状态流转与演化规则                      │  │
│  │   不包含：具体存储或通信实现                        │  │
│  │                                                 │  │
│  │   · 任务点状态机                                  │  │
│  │   · 即时记忆生命周期（生成 → 沉淀 → 淘汰）        │  │
│  │   · 经验演化规则（积累 → 关联 → 衰减）            │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
└───────────────────────────┬───────────────────────────┘
                            │ 通过扩展接口接入
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ 存储插件  │  │ 检索插件  │  │  Agent   │
        │ SQLite   │  │ 向量RAG  │  │ 任意框架  │
        │ PG / FS  │  │ 全文检索  │  │          │
        └──────────┘  └──────────┘  └──────────┘
```

### 4.1 接口契约层（Interface Contract）

定义框架的能力边界，不包含任何执行逻辑。

```
接口契约层
│
├── 经验数据接口（Experience Interface）
│   · store(task_point)           ← 写入任务点
│   · get(task_id, checkpoint_id) ← 读取任务点
│   · list(task_id?)              ← 列出任务点
│
├── 检索接口（Retrieval Interface）
│   · search(query)               ← 按条件检索经验
│   · recall(context)             ← 基于上下文回忆相关经验
│
├── 插件扩展接口（Plugin Interface）
│   · StoragePlugin               ← 存储层抽象（可插拔）
│   └── RetrievalPlugin           ← 检索层抽象（可插拔）
│
└── 通信契约（Protocol Contract）
    └── MCP Tool Definitions      ← 工具名、参数、返回格式
```

**接口示例**：

```jsonc
// store —— 写入任务点
// 请求
{
  "task_id": "task-001",
  "checkpoint_id": "cp-003",
  "data": { /* 完整任务快照 */ },
  "completion_score": 0.65,
  "timestamp": "2026-08-01T10:30:00Z"
}
// 响应
{
  "status": "ok",
  "checkpoint_id": "cp-003"
}

// get —— 读取任务点
// 请求
{
  "task_id": "task-001",
  "checkpoint_id": "cp-003"
}
// 响应
{
  "task_id": "task-001",
  "checkpoint_id": "cp-003",
  "data": { /* 完整任务快照 */ },
  "completion_score": 0.65,
  "timestamp": "2026-08-01T10:30:00Z"
}

// search —— 检索经验
// 请求
{
  "query": "数据库迁移相关经验",
  "limit": 5
}
// 响应
{
  "results": [
    {
      "task_id": "task-001",
      "checkpoint_id": "cp-003",
      "summary": "已完成数据库迁移...",
      "completion_score": 0.65,
      "score": 0.92
    }
  ]
}
```

### 4.2 运行时层（Runtime）

接口契约的执行环境，分为本地运行时和远程运行时。

**Local Runtime（本地 SDK）**：

| 职责 | 说明 |
|------|------|
| 即时记忆管理 | 生成、沉淀、淘汰即时记忆 |
| MCP Client | 连接 CNAA Server，调用 MCP 工具 |
| 上下文注入 | Agent 启动时加载即时记忆到 context |

**Remote Runtime（CNAA Server）**：

| 职责 | 说明 |
|------|------|
| 经验持久化 | 接收并存储任务点完整数据 |
| MCP Server | 暴露 MCP 工具接口供 Agent 调用 |
| 插件调度 | 根据配置调用存储插件和检索插件 |

### 4.3 生命周期层（Lifecycle）

管理经验的状态流转，独立于运行时实现。

**任务点状态机**：

```
pending ──▶ active ──▶ completed ──▶ archived
                    ↘
                      failed
```

**即时记忆生命周期**：

```
created ──▶ active ──▶ condensed ──▶ evicted
（生成）    （可用）    （沉淀为索引）  （淘汰）
```

**经验演化规则**：

```
accumulated ──▶ associated ──▶ decayed
（积累）        （关联）        （衰减）
```

---

## 5. 数据模型

### 5.1 Task（任务）

```jsonc
{
  "task_id": "string",          // 任务唯一标识
  "title": "string",            // 任务标题
  "status": "string",           // pending | active | completed | failed | archived
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 5.2 TaskCheckpoint（任务点）

```jsonc
{
  "task_id": "string",          // 所属任务
  "checkpoint_id": "string",    // 任务点唯一标识
  "data": {},                   // 完整任务快照（Agent 自定义结构）
  "completion_score": 0.0~1.0,  // 完成度评分
  "timestamp": "datetime",
  "metadata": {}                // 可选扩展元数据
}
```

### 5.3 InstantMemory（即时记忆）

```jsonc
{
  "task_id": "string",
  "checkpoint_id": "string",    // 指向 CNAA 中的完整任务点
  "summary": "string",          // 轻量摘要（Agent 生成）
  "completion_score": 0.0~1.0,
  "status": "string",           // created | active | condensed | evicted
  "timestamp": "datetime",
  "cnaa_ref": "string"          // CNAA 引用指针
}
```

---

## 6. 插件系统

所有外部依赖通过插件接口接入，CNAA 不绑定任何具体实现。

### 6.1 存储插件（StoragePlugin）

```
StoragePlugin 接口
│
├── save(task_checkpoint) → status
├── load(task_id, checkpoint_id) → task_checkpoint
├── list(task_id?) → [task_checkpoint_summary]
└── delete(task_id, checkpoint_id) → status
```

**参考实现**：

| 实现 | 适用场景 |
|------|---------|
| SQLite | 本地开发、单机部署 |
| PostgreSQL | 生产环境、多租户 |
| 文件系统 | 极简场景、调试 |

### 6.2 检索插件（RetrievalPlugin）

```
RetrievalPlugin 接口
│
├── index(task_checkpoint) → status
├── search(query, limit?) → [result]
└── recall(context, limit?) → [result]
```

**参考实现**：

| 实现 | 适用场景 |
|------|---------|
| 向量检索（Embedding + ANN） | 语义相似度检索 |
| 全文检索（BM25） | 关键词精确匹配 |
| 混合检索 | 语义 + 关键词融合 |

---

## 7. 通信协议

CNAA 采用 **MCP（Model Context Protocol）** 作为唯一通信协议。

### 7.1 协议模型

```
Agent（MCP Client）
    │
    │  工具调用（Tool Call）
    │  JSON 请求 ──▶
    ▼
CNAA Server（MCP Server）
    │
    │  JSON 响应 ◀──
    ▼
Agent（MCP Client）
```

### 7.2 MCP 工具定义

| 工具名 | 功能 | 输入 | 输出 |
|--------|------|------|------|
| `cnaa_store` | 存储任务点 | TaskCheckpoint JSON | status |
| `cnaa_get` | 获取任务点 | task_id, checkpoint_id | TaskCheckpoint JSON |
| `cnaa_list` | 列出任务点 | task_id? | [summary] |
| `cnaa_search` | 检索经验 | query, limit? | [result] |
| `cnaa_recall` | 回忆相关经验 | context, limit? | [result] |

---

## 8. 可定制性原则

CNAA 的核心设计目标是**极强可更改性**。clone 后用户可以自由修改任何一层而不影响其他层。

### 8.1 可替换清单

| 可替换项 | 替换方式 | 影响范围 |
|---------|---------|---------|
| 存储后端 | 实现 StoragePlugin 接口 | 仅运行时层 |
| 检索策略 | 实现 RetrievalPlugin 接口 | 仅运行时层 |
| 任务点粒度 | Agent 自行定义 | 不影响 CNAA |
| 即时记忆沉淀规则 | 修改生命周期层配置 | 仅生命周期层 |
| Agent 框架 | 实现 Agent Adapter | 仅运行时层 |
| 通信协议 | 扩展 Protocol Contract | 仅接口契约层 |

### 8.2 不变量

以下由 CNAA 框架保证，不可被替换：

- 接口契约层的操作定义（store / get / list / search / recall）
- 数据模型的核心字段（task_id / checkpoint_id / data / completion_score）
- MCP 协议的工具调用模式
- 哑服务原则（JSON in, JSON out, 无推理）

---

## 9. v0.1 范围

### 9.1 目标

实现云端记忆性架构的最小可用版本：

- Agent 能够通过 MCP 工具访问 CNAA Server
- CNAA Server 能够持久化存储任务点数据
- 基本的即时记忆管理能力

### 9.2 v0.1 交付物

| 交付物 | 说明 |
|--------|------|
| 接口契约规范 | 经验数据接口 + 通信契约的正式定义 |
| CNAA Server 参考实现 | MCP Server，支持 cnaa_store / cnaa_get / cnaa_list |
| 本地 SDK 参考实现 | MCP Client + 即时记忆管理基础功能 |
| 存储插件（SQLite） | StoragePlugin 的默认实现 |

### 9.3 v0.1 不包含

- 检索插件（v0.2）
- 经验演化规则（v0.2）
- Multi-Agent 经验共享（v0.3）
- 多存储后端参考实现（v0.2）

---

## 10. 演进路线

```
v0.1                    v0.2                    v0.3
─────────────────────────────────────────────────────────
接口契约规范             检索插件接口             Multi-Agent 共享
CNAA Server（MCP）      检索插件实现             经验关联与演化
本地 SDK 基础            即时记忆沉淀策略          多存储后端实现
SQLite 存储插件          多检索策略               云端部署方案
```
