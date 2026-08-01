# CNAA Architecture Vision v0.1

> Cloud Native Agentic Architecture
>
> An Experience Runtime Framework for AI Agents

---

## 1. Project Positioning

CNAA is an **Experience Runtime Framework**.

It is not an Agent framework, not a Workflow engine, and not a RAG implementation.

CNAA provides an **architectural specification and reference implementations** that enable any AI Agent to achieve persistent experience accumulation, cross-session retrieval, and pseudo-continuous memory — **without modifying its internal reasoning process**.

### 1.1 Core Propositions

- **Decoupling Intelligence from Memory**: The Agent handles reasoning and decision-making; CNAA handles experience storage, retrieval, and lifecycle management
- **Architecture as Product**: CNAA's core deliverable is the architectural specification itself, not a fixed service
- **Highly Customizable**: After cloning, users can freely replace the storage layer, retrieval strategy, and lifecycle rules — everything is decoupled through interfaces

### 1.2 Boundary Statement

| CNAA Is Responsible For | CNAA Is Not Responsible For |
|------------------------|----------------------------|
| Read/write interfaces for experience data | Agent reasoning and planning |
| Persistent storage of task checkpoints | Task execution and evaluation |
| Condensation rules for instant memory | Content generation of instant memory |
| Plugin interfaces for retrieval capabilities | Specific RAG / vector retrieval implementations |
| MCP communication protocol | Agent internal communication |

---

## 2. Design Principles

### 2.1 Dumb Service Principle

The CNAA Server is "dumb" — it only receives structured JSON requests and returns structured JSON responses. It does not perform reasoning, run LLMs, generate content, or perform business transformations.

```
Agent ──JSON──▶ CNAA Server ──JSON──▶ Agent
        Request            Response
```

### 2.2 Interface First Principle

All capabilities are defined as interface contracts before implementations are provided. Interface contracts are the core deliverable of the framework; implementations are replaceable references.

### 2.3 Pluggable Principle

The storage layer, retrieval layer, and Agent adaptation layer are all connected through plugin interfaces. Replacing any layer does not affect other layers.

### 2.4 Local First Principle

The Agent runs locally; CNAA runs in the cloud. Instant memory is retained in the Agent's local context, while full experience data is stored in the cloud.

---

## 3. Core Concepts

### 3.1 Task Checkpoint

A task checkpoint is the fundamental experience unit in CNAA.

The Agent progresses through tasks in an evaluation environment. Upon reaching a checkpoint, it evaluates the completion score and uploads the full task data to CNAA.

```
Task Execution Flow
│
├── Checkpoint A (completion 0.3) ──▶ Upload full data to CNAA
├── Checkpoint B (completion 0.6) ──▶ Upload full data to CNAA
└── Checkpoint C (completion 1.0) ──▶ Upload full data to CNAA
```

**Task checkpoint boundaries are defined by the Agent itself.** CNAA provides open integration interfaces and does not enforce checkpoint granularity rules.

### 3.2 Instant Memory

Instant memory is a lightweight summary of a task checkpoint, retained in the Agent's context.

```
Full checkpoint data (heavyweight) ──▶ Stored in CNAA Cloud
Instant memory summary (lightweight) ──▶ Retained in Agent local context
```

Core functions of instant memory:
- **Quick Localization**: After task interruption, the Agent quickly understands "where it left off" through instant memory
- **On-Demand Backtracking**: Through reference pointers in instant memory, the Agent pulls full task details from CNAA via MCP protocol
- **Pseudo-Continuity**: Multiple instant memories undergo condensation and eviction within the Agent context, simulating memory continuity through a "small index → large storage" pattern

### 3.3 Pseudo-Continuous Memory

```
Agent Starts
    │
    ▼
Load instant memory list (lightweight summaries)
    │
    ▼
Agent assesses current state based on summaries
    │
    ├── Needs details ──▶ Pull full checkpoint from CNAA via MCP
    │
    └── No details needed ──▶ Continue execution
```

Condensation mechanism for instant memory:
- Multiple instant memories participate in condensation and eviction
- Old summaries can be condensed into index pointers, retaining only key information
- Full data is re-fetched from CNAA through pointers when needed

---

## 4. Three-Layer Architecture

CNAA adopts a three-layer orthogonal architecture. Each layer answers a different dimensional question and is decoupled from the others.

```
┌───────────────────────────────────────────────────────┐
│              CNAA Experience Runtime Framework         │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │       Interface Contract Layer                   │  │
│  │                                                 │  │
│  │   Answers: What can the framework do? (What)    │  │
│  │   Responsibility: Data models, operation        │  │
│  │     contracts, protocol formats, plugin ifaces  │  │
│  │   Excludes: Any execution logic                 │  │
│  └──────────────────────┬─────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼─────────────────────────┐  │
│  │              Runtime Layer                       │  │
│  │                                                 │  │
│  │   Answers: How does the framework run? (How)    │  │
│  │   Responsibility: Execution environment for     │  │
│  │     interface contracts                         │  │
│  │   Excludes: State transition rules              │  │
│  │                                                 │  │
│  │   ┌─────────────────┐  ┌──────────────────────┐│  │
│  │   │  Local Runtime   │  │  Remote Runtime      ││  │
│  │   │  (Local SDK)     │  │  (CNAA Server)       ││  │
│  │   │                  │  │                      ││  │
│  │   │ · Instant Memory │  │ · Experience         ││  │
│  │   │   Management     │  │   Persistence        ││  │
│  │   │ · MCP Client     │  │ · MCP Server         ││  │
│  │   │ · Context        │  │ · Plugin Dispatch    ││  │
│  │   │   Injection      │  │                      ││  │
│  │   └─────────────────┘  └──────────────────────┘│  │
│  └─────────────────────────────────────────────────┘  │
│                         │                             │
│  ┌──────────────────────▼─────────────────────────┐  │
│  │            Lifecycle Layer                       │  │
│  │                                                 │  │
│  │   Answers: How does experience evolve? (When)   │  │
│  │   Responsibility: State transitions and         │  │
│  │     evolution rules                             │  │
│  │   Excludes: Concrete storage or communication   │  │
│  │                                                 │  │
│  │   · Task checkpoint state machine               │  │
│  │   · Instant memory lifecycle                    │  │
│  │     (create → condense → evict)                 │  │
│  │   · Experience evolution rules                  │  │
│  │     (accumulate → associate → decay)            │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
└───────────────────────────┬───────────────────────────┘
                            │ Connected via extension interfaces
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Storage  │  │Retrieval │  │  Agent   │
        │ Plugin   │  │ Plugin   │  │ Adapter  │
        │ SQLite   │  │ Vector   │  │ Any      │
        │ PG / FS  │  │ BM25     │  │ Framework│
        └──────────┘  └──────────┘  └──────────┘
```

### 4.1 Interface Contract Layer

Defines the capability boundary of the framework. Contains no execution logic.

```
Interface Contract Layer
│
├── Experience Interface
│   · store(task_point)           ← Write a task checkpoint
│   · get(task_id, checkpoint_id) ← Read a task checkpoint
│   · list(task_id?)              ← List task checkpoints
│
├── Retrieval Interface
│   · search(query)               ← Search experience by condition
│   · recall(context)             ← Recall relevant experience by context
│
├── Plugin Interface
│   · StoragePlugin               ← Storage layer abstraction (pluggable)
│   └── RetrievalPlugin           ← Retrieval layer abstraction (pluggable)
│
└── Protocol Contract
    └── MCP Tool Definitions      ← Tool names, parameters, response formats
```

**Interface Examples**:

```jsonc
// store — Write a task checkpoint
// Request
{
  "task_id": "task-001",
  "checkpoint_id": "cp-003",
  "data": { /* full task snapshot */ },
  "completion_score": 0.65,
  "timestamp": "2026-08-01T10:30:00Z"
}
// Response
{
  "status": "ok",
  "checkpoint_id": "cp-003"
}

// get — Read a task checkpoint
// Request
{
  "task_id": "task-001",
  "checkpoint_id": "cp-003"
}
// Response
{
  "task_id": "task-001",
  "checkpoint_id": "cp-003",
  "data": { /* full task snapshot */ },
  "completion_score": 0.65,
  "timestamp": "2026-08-01T10:30:00Z"
}

// search — Search experience
// Request
{
  "query": "database migration experience",
  "limit": 5
}
// Response
{
  "results": [
    {
      "task_id": "task-001",
      "checkpoint_id": "cp-003",
      "summary": "Database migration completed...",
      "completion_score": 0.65,
      "score": 0.92
    }
  ]
}
```

### 4.2 Runtime Layer

The execution environment for interface contracts, divided into local runtime and remote runtime.

**Local Runtime (Local SDK)**:

| Responsibility | Description |
|---------------|-------------|
| Instant Memory Management | Generate, condense, and evict instant memories |
| MCP Client | Connect to CNAA Server, invoke MCP tools |
| Context Injection | Load instant memories into context at Agent startup |

**Remote Runtime (CNAA Server)**:

| Responsibility | Description |
|---------------|-------------|
| Experience Persistence | Receive and store full task checkpoint data |
| MCP Server | Expose MCP tool interfaces for Agent invocation |
| Plugin Dispatch | Route to storage and retrieval plugins based on configuration |

### 4.3 Lifecycle Layer

Manages state transitions of experience entities. Independent of the runtime implementation.

**Task Checkpoint State Machine**:

```
pending ──▶ active ──▶ completed ──▶ archived
                    ↘
                      failed
```

**Instant Memory Lifecycle**:

```
created ──▶ active ──▶ condensed ──▶ evicted
```

**Experience Evolution Rules**:

```
accumulated ──▶ associated ──▶ decayed
```

---

## 5. Data Models

### 5.1 Task

```jsonc
{
  "task_id": "string",          // Unique task identifier
  "title": "string",            // Task title
  "status": "string",           // pending | active | completed | failed | archived
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 5.2 TaskCheckpoint

```jsonc
{
  "task_id": "string",          // Parent task identifier
  "checkpoint_id": "string",    // Unique checkpoint identifier
  "data": {},                   // Full task snapshot (Agent-defined structure)
  "completion_score": 0.0~1.0,  // Completion score
  "timestamp": "datetime",
  "metadata": {}                // Optional extension metadata
}
```

### 5.3 InstantMemory

```jsonc
{
  "task_id": "string",
  "checkpoint_id": "string",    // Points to full checkpoint in CNAA
  "summary": "string",          // Lightweight summary (Agent-generated)
  "completion_score": 0.0~1.0,
  "status": "string",           // created | active | condensed | evicted
  "timestamp": "datetime",
  "cnaa_ref": "string"          // CNAA reference pointer
}
```

---

## 6. Plugin System

All external dependencies are connected through plugin interfaces. CNAA does not bind to any specific implementation.

### 6.1 Storage Plugin (StoragePlugin)

```
StoragePlugin Interface
│
├── save(task_checkpoint) → status
├── load(task_id, checkpoint_id) → task_checkpoint
├── list(task_id?) → [task_checkpoint_summary]
└── delete(task_id, checkpoint_id) → status
```

**Reference Implementations**:

| Implementation | Applicable Scenario |
|---------------|---------------------|
| SQLite | Local development, single-node deployment |
| PostgreSQL | Production, multi-tenant |
| File System | Minimal scenarios, debugging |

### 6.2 Retrieval Plugin (RetrievalPlugin)

```
RetrievalPlugin Interface
│
├── index(task_checkpoint) → status
├── search(query, limit?) → [result]
└── recall(context, limit?) → [result]
```

**Reference Implementations**:

| Implementation | Applicable Scenario |
|---------------|---------------------|
| Vector Retrieval (Embedding + ANN) | Semantic similarity search |
| Full-Text Retrieval (BM25) | Keyword exact matching |
| Hybrid Retrieval | Semantic + keyword fusion |

---

## 7. Communication Protocol

CNAA uses **MCP (Model Context Protocol)** as its sole communication protocol.

### 7.1 Protocol Model

```
Agent (MCP Client)
    │
    │  Tool Call
    │  JSON Request ──▶
    ▼
CNAA Server (MCP Server)
    │
    │  JSON Response ◀──
    ▼
Agent (MCP Client)
```

### 7.2 MCP Tool Definitions

| Tool Name | Function | Input | Output |
|-----------|----------|-------|--------|
| `cnaa_store` | Store a task checkpoint | TaskCheckpoint JSON | status |
| `cnaa_get` | Get a task checkpoint | task_id, checkpoint_id | TaskCheckpoint JSON |
| `cnaa_list` | List task checkpoints | task_id? | [summary] |
| `cnaa_search` | Search experience | query, limit? | [result] |
| `cnaa_recall` | Recall relevant experience | context, limit? | [result] |

---

## 8. Customizability Principle

A core design goal of CNAA is **extreme customizability**. After cloning, users can freely modify any layer without affecting other layers.

### 8.1 Replaceable Components

| Replaceable Item | Replacement Method | Impact Scope |
|-----------------|-------------------|-------------|
| Storage backend | Implement StoragePlugin interface | Runtime layer only |
| Retrieval strategy | Implement RetrievalPlugin interface | Runtime layer only |
| Checkpoint granularity | Agent-defined | Does not affect CNAA |
| Instant memory condensation rules | Modify Lifecycle layer configuration | Lifecycle layer only |
| Agent framework | Implement Agent Adapter | Runtime layer only |
| Communication protocol | Extend Protocol Contract | Interface Contract layer only |

### 8.2 Invariants

The following are guaranteed by the CNAA framework and cannot be replaced:

- Operation definitions in the Interface Contract layer (store / get / list / search / recall)
- Core fields of the data model (task_id / checkpoint_id / data / completion_score)
- MCP protocol tool call pattern
- Dumb Service principle (JSON in, JSON out, no reasoning)

---

## 9. v0.1 Scope

### 9.1 Goals

Implement the minimum viable version of the cloud memory architecture:

- Agent can access CNAA Server through MCP tools
- CNAA Server can persistently store task checkpoint data
- Basic instant memory management capabilities

### 9.2 v0.1 Deliverables

| Deliverable | Description |
|-------------|-------------|
| Interface Contract Specification | Formal definition of Experience Interface + Protocol Contract |
| CNAA Server Reference Implementation | MCP Server supporting cnaa_store / cnaa_get / cnaa_list |
| Local SDK Reference Implementation | MCP Client + basic instant memory management |
| Storage Plugin (SQLite) | Default StoragePlugin implementation |

### 9.3 Not Included in v0.1

- Retrieval plugins (v0.2)
- Experience evolution rules (v0.2)
- Multi-Agent experience sharing (v0.3)
- Multiple storage backend reference implementations (v0.2)

---

## 10. Evolution Roadmap

```
v0.1                    v0.2                    v0.3
─────────────────────────────────────────────────────────
Interface Contract      Retrieval Plugin         Multi-Agent Sharing
CNAA Server (MCP)       Retrieval Plugin Impl    Experience Association
Local SDK Basics        Instant Memory           & Evolution
SQLite Storage Plugin   Condensation Strategy    Multiple Storage
                        Retrieval Strategies     Backends
                                                Cloud Deployment
```
