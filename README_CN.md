# CNAA

<p align="center">

[English](README.md) | **简体中文**

</p>

<p align="center">
<strong>Cloud Native Agentic Architecture</strong><br/>
<em>面向 AI Agent 的经验记忆运行时框架</em>
</p>

<p align="center">
<img src="https://img.shields.io/badge/status-designing-blue" alt="Status">
<img src="https://img.shields.io/badge/version-v0.1--draft-orange" alt="Version">
<img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

CNAA 是一个**经验记忆运行时框架（Experience Runtime Framework）**，让任何 AI Agent 在无需修改内部推理逻辑的前提下，实现经验的跨会话持久化、检索与复用。

CNAA **不是** Agent 框架，**不是** Workflow 引擎，**不是** RAG 实现。

CNAA 提供一套**架构规范与参考实现**，提出 **Persistent Experience Memory（持久化经验记忆）**，让经验成为独立的运行时资源，而非临时的 Prompt 上下文。

---

## 为什么需要 CNAA？

当前 AI Agent 已经具备完成任务的能力，但绝大多数 Agent **不会持续记住任务经验**。

现有 Memory 方案通常只是延长 Context Window。CNAA 提出了不同的路径：

> **任务点分块 + 即时记忆沉淀 + 云端持久化**

Agent 在任务推进过程中将经验沉淀为任务点，本地仅保留轻量摘要（即时记忆），完整数据存储在云端——通过"小索引 → 大存储"模式实现伪连续记忆。

---

## 核心概念

| 概念 | 说明 |
|------|------|
| **任务点（Task Checkpoint）** | 基本经验单元。Agent 在每个任务点评测完成度，将完整数据上传至 CNAA。 |
| **即时记忆（Instant Memory）** | 任务点的轻量摘要，保留在 Agent 本地 context 中，用于快速定位与按需回溯。 |
| **伪连续记忆（Pseudo-Continuous Memory）** | 多个即时记忆通过沉淀与淘汰机制，以引用指针指向云端完整数据，模拟记忆的连续性。 |

---

## 架构

CNAA 采用**三层正交架构**，每层回答不同维度的问题，可独立修改。

```
┌───────────────────────────────────────────────────────┐
│              CNAA Experience Runtime Framework         │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │     接口契约层（What）                            │  │
│  │     数据模型 · 操作契约 · 协议格式 · 插件接口      │  │
│  └──────────────────────┬──────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐  │
│  │     运行时层（How）                               │  │
│  │                                                  │  │
│  │   ┌─────────────────┐  ┌──────────────────────┐ │  │
│  │   │  Local Runtime   │  │  Remote Runtime      │ │  │
│  │   │  （本地 SDK）     │  │  （CNAA Server）     │ │  │
│  │   │                  │  │                      │ │  │
│  │   │ · 即时记忆管理   │  │ · 经验持久化         │ │  │
│  │   │ · MCP Client     │  │ · MCP Server         │ │  │
│  │   │ · 上下文注入     │  │ · 插件调度           │ │  │
│  │   └─────────────────┘  └──────────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐  │
│  │     生命周期层（When）                            │  │
│  │     任务点状态机 · 即时记忆生命周期 · 经验演化规则  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                       │
└───────────────────────────┬───────────────────────────┘
                            │ 插件接口
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ 存储插件  │  │ 检索插件  │  │  Agent   │
        │          │  │          │  │ Adapter  │
        └──────────┘  └──────────┘  └──────────┘
```

### 通信方式

Agent 通过 **MCP（Model Context Protocol）** 与 CNAA Server 通信，所有交互均为结构化 JSON 请求-响应对。

```
Agent（MCP Client）──JSON──▶ CNAA Server（MCP Server）──JSON──▶ Agent
```

### 安全性设计（可选）

CNAA 支持可选的 API 密钥认证和读写权限控制。认证默认关闭，保持向后兼容。

启用方式：
```bash
export CNAA_AUTH_ENABLED=true
export CNAA_API_KEYS='{"sk-your-key": {"agent_id": "your-agent", "permission": "read_write"}}'
```

客户端通过 `Authorization: Bearer <key>` 请求头认证。详见 [API 参考文档](docs/zh/api-reference-v0.1.md)。

---

## 设计原则

| 原则 | 说明 |
|------|------|
| **哑服务** | CNAA Server 仅做 JSON 存取，不执行推理、不运行 LLM、不生成内容。 |
| **接口优先** | 所有能力先定义接口契约，再提供可替换的实现。 |
| **可插拔** | 存储层、检索层、Agent 适配层均通过插件接口接入。 |
| **本地优先** | 即时记忆留在 Agent context 中，完整数据存储在云端。 |
| **极强可定制** | clone 后可自由修改任一层，不影响其他层。 |

---

## 文档

- 📚 [架构文档](docs/zh/architecture.md) — 完整架构规范
- 🗺️ [架构设想 v0.1](docs/zh/architecture-vision-v0.1.md) — 设计思路与 v0.1 范围
- 🔧 [技术实现文档](docs/zh/technical-implementation.md) — 详细实现指南，包含函数级文档、调用链路、算法详解与修改扩展指南

---

## 路线图

### v0.1（当前）

- [x] 架构规范设计
- [ ] 接口契约定义（经验数据接口 + 通信契约）
- [ ] CNAA Server 参考实现（MCP Server）
- [ ] 本地 SDK 参考实现（MCP Client + 即时记忆管理）
- [ ] 存储插件 — SQLite

### v0.2

- [ ] 检索插件接口与实现
- [ ] 即时记忆沉淀策略
- [ ] 多种检索策略（向量检索、BM25）
- [ ] 更多存储后端（PostgreSQL、文件系统）

### v0.3

- [ ] Multi-Agent 经验共享
- [ ] 经验关联与演化
- [ ] 云端部署方案

---

## 项目状态

> **V0.1 参考实现已完成。**
>
> 核心数据模型、交互接口、MCP 工具定义和生命周期规则均已实现。云端服务（HTTP + stdio MCP）和本地 SDK（MCP Client + 即时记忆 + 状态缓存）参考实现已可正常运行。详见 [技术实现文档](docs/zh/technical-implementation.md)。

---

## 参与贡献

本项目处于早期设计阶段，欢迎对架构设计的讨论、反馈与贡献。

---

## 许可证

MIT
