# CNAA

> Cloud-Native Agent Architecture

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
