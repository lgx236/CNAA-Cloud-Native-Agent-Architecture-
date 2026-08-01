# CNAA

> Cloud-Native Agent Architecture

<div align="right">
  <a href="#english">English</a> | <a href="#中文">简体中文</a>
</div>


**Persistent state infrastructure for AI Agents.**

CNAA provides a lightweight cloud backend that allows AI agents to maintain persistent state across devices through MCP.

Unlike traditional memory systems, CNAA does not perform reasoning or prompt engineering.

It simply stores and serves structured agent state.

---

## Motivation

Today's AI agents are session-based.

Every new device, IDE, or client starts from scratch.

CNAA separates **agent intelligence** from **agent state**.

```
            Local Machine

        ┌──────────────────┐
        │      Agent       │
        │                  │
        │  Reasoning       │
        │  Planning        │
        │  Tool Calling    │
        └────────┬─────────┘
                 │
               MCP
                 │
─────────────────┼─────────────────
                 │
        ┌────────▼────────┐
        │   CNAA Server   │
        │                 │
        │ Identity        │
        │ Memory          │
        │ Workspace       │
        │ History         │
        └─────────────────┘
```

The agent stays local.

The state lives in the cloud.

---

## Design Principles

- Local-first reasoning
- Cloud-native state
- MCP-native communication
- Structured JSON only
- Model agnostic

CNAA never runs an LLM.

The server only receives structured requests and returns structured responses.

---

## Example

Agent:

```json
{
  "tool": "memory.search",
  "query": "papers about MCP"
}
```

Server:

```json
{
  "results": [
    {
      "title": "Model Context Protocol",
      "time": "2026-08-01"
    }
  ]
}
```

The server never generates responses.

The agent decides how to use the returned data.

---

## Components

- Identity
- Memory
- Workspace
- History

More modules will be added in future releases.

---

## Roadmap

### v0.1

- [ ] MCP Server
- [ ] Memory API
- [ ] Identity API
- [ ] Workspace API

### v0.2

- [ ] History
- [ ] Authentication
- [ ] SDK

### v1.0

- [ ] Multi-agent support
- [ ] State synchronization
- [ ] Plugin ecosystem

---

## License

MIT



---

<a id="中文"></a>
# CNAA

> Cloud-Native Agent Architecture
>
> **Agents should persist, not sessions.**
>
> **Agent 应该长期存在，而不是会话。**

CNAA 是一个面向 AI Agent 的云端状态基础设施。

它通过 MCP 为 Agent 提供统一的状态服务，使 Agent 能够在不同设备、不同客户端之间共享自身状态。

CNAA **不负责推理，不负责生成，不运行任何 LLM**。

它只负责存储和提供结构化状态。

---

## 为什么需要 CNAA？

目前绝大多数 Agent 都是**会话式（Session-based）**的。

当你切换设备、IDE 或客户端时，Agent 往往需要重新开始。

即使支持 Memory，本质上也只是将历史内容重新拼接到 Prompt 中。

CNAA 希望将：

- Agent 的智能（Reasoning）
- Agent 的状态（State）

彻底解耦。

Agent 负责思考。

CNAA 负责保存。

---

## 架构

```text
                本地设备

        ┌────────────────────┐
        │       Agent        │
        │                    │
        │  Reasoning         │
        │  Planning          │
        │  Tool Calling      │
        └─────────┬──────────┘
                  │
                 MCP
                  │
──────────────────┼──────────────────
                  │
        ┌─────────▼──────────┐
        │    CNAA Server     │
        │                    │
        │ Identity           │
        │ Memory             │
        │ Workspace          │
        │ History            │
        └────────────────────┘
```

Agent 始终运行在本地。

状态始终保存在云端。

---

## 设计原则

- 本地推理（Local-first）
- 云端状态（Cloud State）
- MCP 原生（MCP Native）
- JSON 通信（Structured JSON）
- 模型无关（Model Agnostic）

CNAA 不参与任何推理过程。

Server 仅接收请求，并返回结构化数据。

---

## 一个简单示例

Agent 调用 MCP：

```json
{
    "tool": "memory.search",
    "query": "MCP 相关论文"
}
```

Server 返回：

```json
{
    "results": [
        {
            "title": "Model Context Protocol",
            "time": "2026-08-01"
        }
    ]
}
```

如何使用这些数据，由 Agent 自行决定。

---

## 当前模块

- Identity（身份）
- Memory（记忆）
- Workspace（工作空间）
- History（历史）

后续会逐步扩展更多状态模块。

---

## Roadmap

### v0.1

- [ ] MCP Server
- [ ] Memory API
- [ ] Identity API
- [ ] Workspace API

### v0.2

- [ ] History
- [ ] 用户认证
- [ ] SDK

### v1.0

- [ ] 多 Agent 支持
- [ ] 状态同步
- [ ] 插件生态

---

## License

MIT
