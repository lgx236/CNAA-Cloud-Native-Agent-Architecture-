# CNAA

<p align="center">

**English** | [简体中文](README_CN.md)

</p>

<p align="center">
<strong>Cloud Native Agentic Architecture</strong><br/>
<em>An Experience Runtime Framework for AI Agents</em>
</p>

<p align="center">
<img src="https://img.shields.io/badge/status-designing-blue" alt="Status">
<img src="https://img.shields.io/badge/version-v0.1--draft-orange" alt="Version">
<img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

CNAA is an **Experience Runtime Framework** that enables any AI Agent to persist, retrieve, and reuse task experience across sessions — without modifying its internal reasoning.

CNAA is **not** an Agent framework. It is **not** a workflow engine. It is **not** another RAG implementation.

Instead, CNAA provides an architectural specification and reference implementations for **Persistent Experience Memory**, making experience an independent runtime resource rather than temporary prompt context.

---

## The Problem

Current AI Agents can solve tasks, but few of them **remember** tasks.

Most existing memory systems simply extend context windows. CNAA introduces a different approach:

> **Task Checkpoint + Instant Memory + Cloud Persistence**

Agents accumulate experience in checkpoints, retain lightweight summaries locally, and store full task data in the cloud — achieving pseudo-continuous memory through a "small index → large storage" pattern.

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Task Checkpoint** | The fundamental experience unit. Agents evaluate completion at each checkpoint and upload full task data to CNAA. |
| **Instant Memory** | A lightweight summary of a checkpoint, retained in the Agent's local context for quick reference. |
| **Pseudo-Continuous Memory** | Multiple instant memories undergo condensation and eviction, simulating memory continuity through reference pointers to cloud data. |

---

## Architecture

CNAA adopts a **three-layer orthogonal architecture**. Each layer answers a different dimensional question and is independently modifiable.

```
┌───────────────────────────────────────────────────────┐
│              CNAA Experience Runtime Framework         │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │     Interface Contract Layer (What)              │  │
│  │     Data models · Operation contracts            │  │
│  │     Protocol formats · Plugin interfaces         │  │
│  └──────────────────────┬──────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐  │
│  │     Runtime Layer (How)                          │  │
│  │                                                  │  │
│  │   ┌─────────────────┐  ┌──────────────────────┐ │  │
│  │   │  Local Runtime   │  │  Remote Runtime      │ │  │
│  │   │  (Local SDK)     │  │  (CNAA Server)       │ │  │
│  │   │                  │  │                      │ │  │
│  │   │ · Instant Memory │  │ · Experience         │ │  │
│  │   │   Management     │  │   Persistence        │ │  │
│  │   │ · MCP Client     │  │ · MCP Server         │ │  │
│  │   │ · Context        │  │ · Plugin Dispatch    │ │  │
│  │   │   Injection      │  │                      │ │  │
│  │   └─────────────────┘  └──────────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐  │
│  │     Lifecycle Layer (When)                       │  │
│  │     Checkpoint state machine                     │  │
│  │     Instant memory lifecycle                     │  │
│  │     Experience evolution rules                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                       │
└───────────────────────────┬───────────────────────────┘
                            │ Plugin interfaces
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Storage  │  │Retrieval │  │  Agent   │
        │ Plugin   │  │ Plugin   │  │ Adapter  │
        └──────────┘  └──────────┘  └──────────┘
```

### Communication

Agents communicate with CNAA Server exclusively via **MCP (Model Context Protocol)** using structured JSON request-response pairs.

```
Agent (MCP Client) ──JSON──▶ CNAA Server (MCP Server) ──JSON──▶ Agent
```

### Security (Optional)

CNAA supports optional API key authentication with read/write permission levels. Authentication is disabled by default for backward compatibility.

To enable:
```bash
export CNAA_AUTH_ENABLED=true
export CNAA_API_KEYS='{"sk-your-key": {"agent_id": "your-agent", "permission": "read_write"}}'
```

Clients authenticate via `Authorization: Bearer <key>` header. See [API Reference](docs/zh/api-reference-v0.1.md) for details.

---

## Design Principles

| Principle | Description |
|-----------|-------------|
| **Dumb Service** | CNAA Server only stores and retrieves JSON. No reasoning, no LLM, no content generation. |
| **Interface First** | All capabilities are defined as interface contracts before implementations. |
| **Pluggable** | Storage, retrieval, and Agent adapters are all connected through plugin interfaces. |
| **Local First** | Instant memory stays in Agent context; full data lives in the cloud. |
| **Highly Customizable** | Clone and freely modify any layer without affecting others. |

---

## Documentation

- 📚 [Architecture Document](docs/en/architecture.md) — Full architectural specification
- 🗺️ [Architecture Vision v0.1](docs/en/architecture-vision-v0.1.md) — Design rationale and v0.1 scope
- 🔌 [API Reference v0.1](docs/en/api-reference-v0.1.md) — Interface specification and MCP tool definitions
- 📖 [中文文档](docs/zh/) — Chinese documentation

---

## Roadmap

### v0.1 (Current)

- [x] Architecture specification
- [x] Interface contract definition (Memory/State/Preference/Environment)
- [x] MCP tool definitions (13 tools)
- [x] Lifecycle rules specification
- [x] API reference documentation (Chinese & English)
- [ ] CNAA Server reference implementation (MCP Server)
- [ ] Local SDK reference implementation (MCP Client + Instant Memory management)
- [ ] Storage plugin — SQLite

### v0.2

- [ ] Retrieval plugin interface and implementations
- [ ] Instant memory condensation strategy
- [ ] Multiple retrieval strategies (vector, BM25)
- [ ] Additional storage backends (PostgreSQL, file system)

### v0.3

- [ ] Multi-Agent experience sharing
- [ ] Experience association and evolution
- [ ] Cloud deployment solutions

---

## Project Status

> **V0.1 interface specification is complete.**
>
> Core data models, interaction interfaces, MCP tool definitions, and lifecycle rules have been implemented. Reference implementations (cloud server and local SDK) are under development.

---

## Contributing

This project is in early design. Contributions, discussions, and feedback on the architecture are welcome.

---

## License

MIT
