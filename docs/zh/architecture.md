# CNAA 架构文档

> **CNAA — Cloud Native Agentic Architecture**
>
> 面向 AI Agent 的经验记忆运行时框架（Experience Runtime Framework）
>
> 版本：v0.1-draft

---

## 目录

- [1. 概述](#1-概述)
- [2. 设计原则](#2-设计原则)
- [3. 系统架构](#3-系统架构)
- [4. 核心概念模型](#4-核心概念模型)
- [5. 接口契约规范](#5-接口契约规范)
- [6. 插件体系](#6-插件体系)
- [7. 通信协议](#7-通信协议)
- [8. 架构约束与不变量](#8-架构约束与不变量)
- [9. 部署拓扑](#9-部署拓扑)
- [10. 术语表](#10-术语表)

---

## 1. 概述

### 1.1 项目定位

CNAA 是一个 **Experience Runtime Framework**——面向 AI Agent 的经验记忆运行时框架。

CNAA 提供一套架构规范与参考实现，使任何 AI Agent 在无需修改内部推理逻辑的前提下，实现经验的持久化沉淀、跨会话检索与伪连续记忆。

### 1.2 系统边界

| 属于 CNAA 职责 | 不属于 CNAA 职责 |
|---------------|-----------------|
| 经验数据的读写接口定义与实现 | Agent 的推理、规划与工具调用 |
| 任务点（Checkpoint）的持久化 | 任务执行过程与评测逻辑 |
| 即时记忆的生命周期管理规则 | 即时记忆摘要内容的生成 |
| 检索能力的插件接口定义 | 具体的 RAG / 向量检索算法实现 |
| MCP 通信协议的实现 | Agent 框架内部通信 |

### 1.3 核心交付物

CNAA 的交付物分为两类：

| 类别 | 内容 | 性质 |
|------|------|------|
| **架构规范** | 接口契约、数据模型、协议格式、插件接口 | 不可替换，框架核心 |
| **参考实现** | CNAA Server、Local SDK、默认插件 | 可替换，按需修改 |

---

## 2. 设计原则

### P1. 哑服务原则（Dumb Service）

CNAA Server 仅接收结构化 JSON 请求并返回结构化 JSON 响应。不执行推理，不运行 LLM，不生成内容，不做数据转换或聚合。

```
Agent ──▶ JSON 请求 ──▶ CNAA Server ──▶ JSON 响应 ──▶ Agent
```

### P2. 接口优先原则（Interface First）

所有能力先定义接口契约，再提供实现。接口契约是框架的核心交付物，具体实现是可替换的参考。

### P3. 可插拔原则（Pluggable）

存储层、检索层、Agent 适配层均通过插件接口接入。替换任何一层不影响其他层的行为。

### P4. 本地优先原则（Local First）

Agent 在本地运行，CNAA Server 在云端运行。即时记忆保留在 Agent 本地上下文中，完整经验数据存储在云端。

### P5. 极强可定制性（Highly Customizable）

框架设计目标是 clone 后可自由修改。三层架构正交分离，修改任一层不影响其他层。

---

## 3. 系统架构

### 3.1 三层正交架构

CNAA 采用三层正交架构，每层回答不同维度的问题：

```
┌─────────────────────────────────────────────────────────┐
│                CNAA Experience Runtime Framework          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │          Layer 1: 接口契约层 (Interface)           │  │
│  │                                                   │  │
│  │   维度：What — 框架能做什么                         │  │
│  │   职责：数据模型、操作契约、协议格式、插件接口         │  │
│  │   约束：不包含任何执行逻辑                           │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │            Layer 2: 运行时层 (Runtime)              │  │
│  │                                                   │  │
│  │   维度：How — 框架怎么跑                            │  │
│  │   职责：接口契约的执行环境                           │  │
│  │   约束：不包含状态流转规则                           │  │
│  │                                                   │  │
│  │   ┌──────────────────┐  ┌───────────────────────┐ │  │
│  │   │  Local Runtime    │  │  Remote Runtime       │ │  │
│  │   │  本地 SDK         │  │  CNAA Server          │ │  │
│  │   │                   │  │                       │ │  │
│  │   │  · 即时记忆管理   │  │  · 经验持久化         │ │  │
│  │   │  · MCP Client     │  │  · MCP Server         │ │  │
│  │   │  · 上下文注入     │  │  · 插件调度           │ │  │
│  │   └──────────────────┘  └───────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │          Layer 3: 生命周期层 (Lifecycle)            │  │
│  │                                                   │  │
│  │   维度：When — 经验怎么变                           │  │
│  │   职责：状态流转与演化规则                           │  │
│  │   约束：不包含具体存储或通信实现                      │  │
│  │                                                   │  │
│  │   · 任务点状态机                                    │  │
│  │   · 即时记忆生命周期                                │  │
│  │   · 经验演化规则                                    │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────┬───────────────────────────────┘
                          │ 通过插件接口接入
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ 存储插件  │  │ 检索插件  │  │  Agent   │
      │ Storage  │  │Retrieval │  │ Adapter  │
      └──────────┘  └──────────┘  └──────────┘
```

### 3.2 层间依赖规则

```
接口契约层 ◀──── 运行时层（依赖接口契约）
接口契约层 ◀──── 生命周期层（依赖接口契约）
运行时层   ◀──── 生命周期层（通过运行时执行生命周期规则）

插件       ────▶ 接口契约层（实现插件接口）
插件       ────▶ 运行时层（被运行时调度）

Agent      ────▶ 运行时层（通过 MCP 调用）
Agent      ────▶ 接口契约层（遵循数据模型）
```

**禁止的依赖方向**：

- 接口契约层不得依赖运行时层或生命周期层
- 生命周期层不得依赖具体插件实现
- 插件之间不得直接通信

### 3.3 各层职责详述

#### 3.3.1 接口契约层

定义框架的能力边界。由以下子接口组成：

```
接口契约层
│
├── 经验数据接口（Experience Interface）
│   定义经验数据的 CRUD 操作契约
│
├── 检索接口（Retrieval Interface）
│   定义经验检索的操作契约
│
├── 插件扩展接口（Plugin Interface）
│   定义存储插件和检索插件的接入契约
│
└── 通信契约（Protocol Contract）
    定义 MCP 工具的名称、参数结构与返回格式
```

#### 3.3.2 运行时层

接口契约的执行环境。分为两个运行时实例：

**Local Runtime（本地 SDK）**

| 模块 | 职责 |
|------|------|
| 即时记忆管理器 | 即时记忆的生成、沉淀、淘汰 |
| MCP Client | 建立与 CNAA Server 的 MCP 连接 |
| 上下文注入器 | Agent 启动时将即时记忆加载到 context |

**Remote Runtime（CNAA Server）**

| 模块 | 职责 |
|------|------|
| 经验持久化引擎 | 接收并持久化任务点数据 |
| MCP Server | 暴露 MCP 工具接口 |
| 插件调度器 | 根据配置路由到存储插件和检索插件 |

#### 3.3.3 生命周期层

管理经验实体的状态流转。独立于运行时，可单独配置。

包含三个子系统（详见 [4.4 生命周期](#44-生命周期)）：

- 任务点状态机
- 即时记忆生命周期
- 经验演化规则

---

## 4. 核心概念模型

### 4.1 任务点（Task Checkpoint）

任务点是 CNAA 的基本经验单元。

Agent 在评测环境中推进任务，每到达一个任务点即评测完成度，将完整任务数据上传至 CNAA，并生成轻量即时记忆摘要。

```
任务执行流
│
├── 任务点 A（完成度 0.3）──▶ 上传完整数据至 CNAA ──▶ 生成即时记忆 A'
├── 任务点 B（完成度 0.6）──▶ 上传完整数据至 CNAA ──▶ 生成即时记忆 B'
└── 任务点 C（完成度 1.0）──▶ 上传完整数据至 CNAA ──▶ 生成即时记忆 C'
```

**任务点边界由 Agent 自行定义。** CNAA 提供开放的接入接口，不强制任务点的粒度规则。此处仅影响效果，不影响架构。

### 4.2 即时记忆（Instant Memory）

即时记忆是任务点的轻量摘要，保留在 Agent 的上下文中。

| 属性 | 存储位置 | 特征 |
|------|---------|------|
| 任务点完整数据 | CNAA 云端 | 重量级，包含完整任务快照 |
| 即时记忆摘要 | Agent 本地 context | 轻量级，仅包含关键索引 |

即时记忆的三个核心作用：

1. **快速定位**：任务中断后，Agent 通过摘要快速了解"上次做到哪了"
2. **按需回溯**：通过引用指针，经 MCP 协议从 CNAA 拉取完整任务细节
3. **伪连续性**：多个即时记忆在 context 中沉淀与淘汰，以"小索引 → 大存储"模式模拟记忆连续性

### 4.3 伪连续记忆（Pseudo-Continuous Memory）

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
    └── 不需要细节 ──▶ 基于摘要继续执行
```

沉淀机制：

- 多个即时记忆参与沉淀与淘汰
- 旧摘要可沉淀为索引指针，仅保留关键信息
- 需要时通过指针从 CNAA 重新获取完整数据

### 4.4 生命周期

#### 4.4.1 任务点状态机

```
         ┌──────────┐
         │ pending  │
         └────┬─────┘
              │ 开始执行
              ▼
         ┌──────────┐
    ┌────│ active   │────┐
    │    └──────────┘    │
    │ 执行成功       执行失败
    ▼                    ▼
┌──────────┐      ┌──────────┐
│completed │      │  failed  │
└────┬─────┘      └──────────┘
     │ 归档
     ▼
┌──────────┐
│ archived │
└──────────┘
```

#### 4.4.2 即时记忆生命周期

```
created ──▶ active ──▶ condensed ──▶ evicted
（生成）    （可用）    （沉淀为索引）  （淘汰）
```

| 状态 | 含义 |
|------|------|
| created | 刚从任务点生成 |
| active | 可被 Agent 直接读取和使用 |
| condensed | 已沉淀为索引指针，完整数据需从 CNAA 拉取 |
| evicted | 已从本地 context 中移除 |

#### 4.4.3 经验演化规则

```
accumulated ──▶ associated ──▶ decayed
（积累）        （关联）        （衰减）
```

| 阶段 | 含义 |
|------|------|
| accumulated | 经验数据持续写入 |
| associated | 跨任务经验建立关联 |
| decayed | 长期未引用的经验降低优先级 |

---

## 5. 接口契约规范

### 5.1 经验数据接口（Experience Interface）

#### `store` — 写入任务点

**请求**：

```json
{
  "task_id": "string",
  "checkpoint_id": "string",
  "data": {},
  "completion_score": 0.0,
  "timestamp": "ISO-8601",
  "metadata": {}
}
```

**响应**：

```json
{
  "status": "ok",
  "checkpoint_id": "string"
}
```

#### `get` — 读取任务点

**请求**：

```json
{
  "task_id": "string",
  "checkpoint_id": "string"
}
```

**响应**：

```json
{
  "task_id": "string",
  "checkpoint_id": "string",
  "data": {},
  "completion_score": 0.0,
  "timestamp": "ISO-8601",
  "metadata": {}
}
```

#### `list` — 列出任务点

**请求**：

```json
{
  "task_id": "string"
}
```

**响应**：

```json
{
  "checkpoints": [
    {
      "checkpoint_id": "string",
      "completion_score": 0.0,
      "timestamp": "ISO-8601"
    }
  ]
}
```

### 5.2 检索接口（Retrieval Interface）

#### `search` — 按条件检索经验

**请求**：

```json
{
  "query": "string",
  "limit": 5
}
```

**响应**：

```json
{
  "results": [
    {
      "task_id": "string",
      "checkpoint_id": "string",
      "summary": "string",
      "completion_score": 0.0,
      "relevance_score": 0.0
    }
  ]
}
```

#### `recall` — 基于上下文回忆相关经验

**请求**：

```json
{
  "context": {},
  "limit": 5
}
```

**响应**：

```json
{
  "results": [
    {
      "task_id": "string",
      "checkpoint_id": "string",
      "summary": "string",
      "completion_score": 0.0,
      "relevance_score": 0.0
    }
  ]
}
```

### 5.3 数据模型

#### Task（任务）

```
Task
├── task_id        : string    — 任务唯一标识
├── title          : string    — 任务标题
├── status         : enum      — pending | active | completed | failed | archived
├── created_at     : datetime  — 创建时间
└── updated_at     : datetime  — 最后更新时间
```

#### TaskCheckpoint（任务点）

```
TaskCheckpoint
├── task_id          : string    — 所属任务标识
├── checkpoint_id    : string    — 任务点唯一标识
├── data             : object    — 完整任务快照（Agent 自定义结构）
├── completion_score : float     — 完成度评分 [0.0, 1.0]
├── timestamp        : datetime  — 任务点时间戳
└── metadata         : object    — 可选扩展元数据
```

#### InstantMemory（即时记忆）

```
InstantMemory
├── task_id          : string    — 关联任务标识
├── checkpoint_id    : string    — 关联任务点标识
├── summary          : string    — 轻量摘要（Agent 生成）
├── completion_score : float     — 完成度评分 [0.0, 1.0]
├── status           : enum      — created | active | condensed | evicted
├── timestamp        : datetime  — 生成时间
└── cnaa_ref         : string    — CNAA 引用指针
```

---

## 6. 插件体系

### 6.1 存储插件接口（StoragePlugin）

```
StoragePlugin
│
├── save(checkpoint: TaskCheckpoint) → { status: string }
├── load(task_id: string, checkpoint_id: string) → TaskCheckpoint
├── list(task_id?: string) → [CheckpointSummary]
└── delete(task_id: string, checkpoint_id: string) → { status: string }
```

**参考实现**：

| 实现 | 场景 | 优先级 |
|------|------|--------|
| SQLite | 本地开发、单机部署 | v0.1 |
| PostgreSQL | 生产环境、多租户 | v0.2 |
| 文件系统 | 极简场景、调试 | v0.2 |

### 6.2 检索插件接口（RetrievalPlugin）

```
RetrievalPlugin
│
├── index(checkpoint: TaskCheckpoint) → { status: string }
├── search(query: string, limit?: int) → [SearchResult]
└── recall(context: object, limit?: int) → [SearchResult]
```

**参考实现**：

| 实现 | 场景 | 优先级 |
|------|------|--------|
| 向量检索（Embedding + ANN） | 语义相似度 | v0.2 |
| 全文检索（BM25） | 关键词匹配 | v0.2 |
| 混合检索 | 语义 + 关键词融合 | v0.3 |

### 6.3 插件接入规则

- 插件通过接口契约层定义的 Plugin Interface 接入
- 运行时层的插件调度器负责调用插件
- 插件之间不得直接通信
- 插件的实现细节对接口契约层透明

---

## 7. 通信协议

### 7.1 协议选型

CNAA 采用 **MCP（Model Context Protocol）** 作为唯一通信协议。

### 7.2 通信模型

```
Agent（MCP Client）
    │
    │  MCP Tool Call（JSON 请求）
    ▼
CNAA Server（MCP Server）
    │
    │  JSON 响应
    ▼
Agent（MCP Client）
```

所有通信均为 JSON 请求-响应对。无 streaming，无双向推送。

### 7.3 MCP 工具清单

| 工具名 | 对应接口 | 输入 | 输出 |
|--------|---------|------|------|
| `cnaa_store` | Experience.store | TaskCheckpoint JSON | `{ status }` |
| `cnaa_get` | Experience.get | `task_id`, `checkpoint_id` | TaskCheckpoint JSON |
| `cnaa_list` | Experience.list | `task_id?` | `{ checkpoints: [] }` |
| `cnaa_search` | Retrieval.search | `query`, `limit?` | `{ results: [] }` |
| `cnaa_recall` | Retrieval.recall | `context`, `limit?` | `{ results: [] }` |

---

## 8. 架构约束与不变量

### 8.1 不变量（Invariants）

以下约束由框架保证，不可被替换或违反：

| 编号 | 约束 | 说明 |
|------|------|------|
| I-1 | 所有接口输入输出为结构化 JSON | 哑服务原则 |
| I-2 | CNAA 不执行推理、不运行 LLM、不生成内容 | 哑服务原则 |
| I-3 | 数据模型核心字段不可省略 | `task_id`、`checkpoint_id`、`data`、`completion_score` |
| I-4 | MCP 为唯一通信协议 | 协议一致性 |
| I-5 | 三层之间依赖方向单向向下 | 接口契约 ◀ 运行时 ◀ 生命周期 |

### 8.2 可替换清单

| 可替换项 | 替换方式 | 影响范围 |
|---------|---------|---------|
| 存储后端 | 实现 StoragePlugin 接口 | 仅运行时层 |
| 检索策略 | 实现 RetrievalPlugin 接口 | 仅运行时层 |
| 任务点粒度 | Agent 自行定义边界 | 不影响 CNAA |
| 即时记忆沉淀规则 | 修改生命周期层配置 | 仅生命周期层 |
| Agent 框架 | 实现 Agent Adapter | 仅运行时层 |

---

## 9. 部署拓扑

### 9.1 标准拓扑

```
┌─────────────────────┐          ┌─────────────────────────┐
│     Agent 本地       │          │       CNAA 云端          │
│                     │          │                         │
│  ┌───────────────┐  │   MCP    │  ┌───────────────────┐  │
│  │  Agent 进程    │  │◀──────▶│  │  CNAA Server      │  │
│  └───────┬───────┘  │          │  │  (MCP Server)     │  │
│          │          │          │  └────────┬──────────┘  │
│  ┌───────▼───────┐  │          │           │             │
│  │ Local Runtime  │  │          │  ┌────────▼──────────┐  │
│  │ · 即时记忆     │  │          │  │ StoragePlugin     │  │
│  │ · MCP Client   │  │          │  │ (SQLite / PG / …) │  │
│  └───────────────┘  │          │  └───────────────────┘  │
│                     │          │  ┌───────────────────┐  │
│                     │          │  │ RetrievalPlugin   │  │
│                     │          │  │ (向量 / BM25 / …) │  │
│                     │          │  └───────────────────┘  │
└─────────────────────┘          └─────────────────────────┘
```

### 9.2 本地开发拓扑

```
┌──────────────────────────────────────┐
│            本地开发环境               │
│                                      │
│  ┌──────────┐    MCP   ┌──────────┐ │
│  │  Agent   │◀────────▶│  CNAA    │ │
│  │          │          │  Server  │ │
│  └──────────┘          │ (SQLite) │ │
│                        └──────────┘ │
└──────────────────────────────────────┘
```

---

## 10. 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 经验记忆 | Experience Memory | Agent 在任务执行过程中产生的可复用知识 |
| 任务点 | Task Checkpoint | 任务执行流中的一个可评测节点，包含完整任务快照 |
| 即时记忆 | Instant Memory | 任务点的轻量摘要，保留在 Agent 本地 context 中 |
| 伪连续记忆 | Pseudo-Continuous Memory | 通过"即时记忆索引 + 云端完整数据"模拟的记忆连续性 |
| 接口契约 | Interface Contract | 定义框架能力边界的操作规范 |
| 插件 | Plugin | 通过标准接口接入的外部组件（存储、检索等） |
| 哑服务 | Dumb Service | 仅做 JSON 存取、不执行推理的服务模式 |
| 沉淀 | Condense | 即时记忆从完整摘要退化为索引指针的过程 |
| 淘汰 | Evict | 即时记忆从本地 context 中移除的过程 |
