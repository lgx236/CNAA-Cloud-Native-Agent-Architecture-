# CNAA

<p align="center">

**English** | [简体中文](README_CN.md)

</p>

> **CNAA (Cloud Native Agentic Architecture)**
>
> A runtime framework for persistent Agent memory.

CNAA is **not** an Agent framework.

CNAA is **not** a workflow engine.

CNAA is **not** another RAG implementation.

CNAA provides a lightweight **Experience Runtime** that enables any AI Agent to continuously accumulate, synchronize and reuse task experience without modifying its internal reasoning process.

---

## Why CNAA?

Current AI Agents can solve tasks.

Few of them can **remember** tasks.

Most existing memory systems simply extend context windows.

CNAA introduces **Persistent Experience Memory**, allowing experience to become an independent runtime resource rather than temporary prompt context.

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

## Features

- 🧠 Persistent Experience Memory
- 🔄 Runtime State Synchronization
- 🔌 Unified State Interface
- 🤖 Agent-Agnostic Design
- ☁️ Cloud / Local Deployment

---

## Architecture

```
                AI Agent
                    │
                    ▼
        Experience Runtime SDK
        │
        ├── State Interface
        ├── Memory Manager
        ├── Task Lifecycle
        └── Agent Adapter
                    │
              MCP / HTTP
                    │
                    ▼
          CNAA State Service
```

---

## Documentation

- 📖 [Getting Started](docs/en/getting-started.md)
- 🧠 [Persistent Memory](docs/en/memory.md)
- 🔄 [State Interface](docs/en/state-interface.md)
- 📦 [Experience Runtime SDK](docs/en/runtime.md)
- ☁️ [CNAA State Service](docs/en/state-service.md)
- 🔌 [MCP Integration](docs/en/mcp.md)
- 🤖 [Agent Integration](docs/en/integration.md)
- 📚 [Architecture](docs/en/architecture.md)

---

## Roadmap

- [ ] Experience Runtime SDK
- [ ] State Interface Specification
- [ ] Persistent Memory
- [ ] CNAA State Service
- [ ] MCP Support
- [ ] Multi-Agent Experience Sharing

---

## License

MIT