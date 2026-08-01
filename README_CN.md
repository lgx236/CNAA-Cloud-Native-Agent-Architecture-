# CNAA

<p align="center">

[English](README.md) | **简体中文**

</p>

> **CNAA（Cloud Native Agentic Architecture）**
>
> 面向 AI Agent 的持久化记忆运行时框架。

CNAA **不是 Agent 框架**。

CNAA **不是 Workflow 引擎**。

CNAA **不是 RAG**。

CNAA 提供一套轻量级 **Experience Runtime（经验运行时）**，让任何 Agent 在**无需修改推理逻辑**的情况下，实现经验沉淀、状态同步与持续记忆。

---

## 为什么需要 CNAA？

当前 Agent 已经具备完成任务的能力。

但绝大多数 Agent **不会持续记住任务经验**。

目前主流 Memory 方案通常只是：

> 延长 Prompt。

CNAA 提出：

> **Persistent Experience Memory（持久化经验记忆）**

经验不再属于 Prompt，

而成为 Agent 生命周期之外的一种独立资源。

```
AI Agent
        │
        ▼
Experience Runtime
        │
        ▼
Persistent Memory
```

---

## 核心能力

- 🧠 持久化经验记忆（Persistent Experience Memory）
- 🔄 状态同步（State Synchronization）
- 🔌 统一状态接口（State Interface）
- 🤖 Agent 无关设计（Agent-Agnostic）
- ☁️ 云端 / 本地部署

---

## 架构

```
                AI Agent
                    │
                    ▼
        Experience Runtime SDK
        │
        ├── State Interface（状态接口）
        ├── Memory Manager（记忆管理）
        ├── Task Lifecycle（任务生命周期）
        └── Agent Adapter（Agent 适配）
                    │
              MCP / HTTP
                    │
                    ▼
          CNAA State Service
```

---

## 文档

- 📖 [快速开始](docs/zh/getting-started.md)
- 🧠 [持久化记忆](docs/zh/memory.md)
- 🔄 [State Interface](docs/zh/state-interface.md)
- 📦 [Experience Runtime SDK](docs/zh/runtime.md)
- ☁️ [CNAA State Service](docs/zh/state-service.md)
- 🔌 [MCP 接入](docs/zh/mcp.md)
- 🤖 [Agent 接入](docs/zh/integration.md)
- 📚 [整体架构](docs/zh/architecture.md)

---

## Roadmap

- [ ] Experience Runtime SDK
- [ ] State Interface 标准
- [ ] Persistent Memory
- [ ] CNAA State Service
- [ ] MCP 接入
- [ ] Multi-Agent Experience Sharing

---

## License

MIT