# CNAA Architecture Document

> **CNAA — Cloud Native Agentic Architecture**
>
> An Experience Runtime Framework for AI Agents
>
> Version: v0.1-draft

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Design Principles](#2-design-principles)
- [3. System Architecture](#3-system-architecture)
- [4. Core Conceptual Model](#4-core-conceptual-model)
- [5. Interface Contract Specification](#5-interface-contract-specification)
- [6. Plugin System](#6-plugin-system)
- [7. Communication Protocol](#7-communication-protocol)
- [8. Architectural Constraints and Invariants](#8-architectural-constraints-and-invariants)
- [9. Deployment Topology](#9-deployment-topology)
- [10. Glossary](#10-glossary)

---

## 1. Overview

### 1.1 Project Positioning

CNAA is an **Experience Runtime Framework** — a runtime framework for persistent experience memory of AI Agents.

CNAA provides an architectural specification and reference implementations that enable any AI Agent to achieve persistent experience accumulation, cross-session retrieval, and pseudo-continuous memory — without modifying its internal reasoning process.

### 1.2 System Boundaries

| Within CNAA's Scope | Outside CNAA's Scope |
|--------------------|---------------------|
| Definition and implementation of experience data read/write interfaces | Agent reasoning, planning, and tool invocation |
| Persistence of task checkpoints | Task execution and evaluation logic |
| Lifecycle management rules for instant memory | Generation of instant memory summary content |
| Plugin interface definition for retrieval capabilities | Specific RAG / vector retrieval algorithm implementations |
| Implementation of the MCP communication protocol | Agent framework internal communication |

### 1.3 Core Deliverables

CNAA deliverables fall into two categories:

| Category | Content | Nature |
|----------|---------|--------|
| **Architectural Specification** | Interface contracts, data models, protocol formats, plugin interfaces | Irreplaceable, framework core |
| **Reference Implementations** | CNAA Server, Local SDK, default plugins | Replaceable, modifiable as needed |

---

## 2. Design Principles

### P1. Dumb Service Principle

The CNAA Server is "dumb" — it only receives structured JSON requests and returns structured JSON responses. It does not perform reasoning, run LLMs, generate content, or perform data transformation or aggregation.

```
Agent ──▶ JSON Request ──▶ CNAA Server ──▶ JSON Response ──▶ Agent
```

### P2. Interface First Principle

All capabilities are defined as interface contracts before implementations are provided. Interface contracts are the core deliverable of the framework; specific implementations are replaceable references.

### P3. Pluggable Principle

The storage layer, retrieval layer, and Agent adaptation layer are all connected through plugin interfaces. Replacing any layer does not affect the behavior of other layers.

### P4. Local First Principle

The Agent runs locally; the CNAA Server runs in the cloud. Instant memory is retained in the Agent's local context, while full experience data is stored in the cloud.

### P5. Highly Customizable

The framework is designed to be freely modified after cloning. The three-layer architecture is orthogonally separated — modifying any layer does not affect other layers.

---

## 3. System Architecture

### 3.1 Three-Layer Orthogonal Architecture

CNAA adopts a three-layer orthogonal architecture. Each layer answers a different dimensional question:

```
┌─────────────────────────────────────────────────────────┐
│                CNAA Experience Runtime Framework          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │       Layer 1: Interface Contract Layer            │  │
│  │                                                   │  │
│  │   Dimension: What — What can the framework do?    │  │
│  │   Responsibility: Data models, operation          │  │
│  │     contracts, protocol formats, plugin interfaces │  │
│  │   Constraint: No execution logic                  │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │            Layer 2: Runtime Layer                   │  │
│  │                                                   │  │
│  │   Dimension: How — How does the framework run?    │  │
│  │   Responsibility: Execution environment for       │  │
│  │     interface contracts                           │  │
│  │   Constraint: No state transition rules           │  │
│  │                                                   │  │
│  │   ┌──────────────────┐  ┌───────────────────────┐ │  │
│  │   │  Local Runtime    │  │  Remote Runtime       │ │  │
│  │   │  (Local SDK)      │  │  (CNAA Server)        │ │  │
│  │   │                   │  │                       │ │  │
│  │   │  · Instant Memory │  │  · Experience         │ │  │
│  │   │    Management     │  │    Persistence        │ │  │
│  │   │  · MCP Client     │  │  · MCP Server         │ │  │
│  │   │  · Context        │  │  · Plugin Dispatch    │ │  │
│  │   │    Injection      │  │                       │ │  │
│  │   └──────────────────┘  └───────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │          Layer 3: Lifecycle Layer                   │  │
│  │                                                   │  │
│  │   Dimension: When — How does experience evolve?   │  │
│  │   Responsibility: State transitions and           │  │
│  │     evolution rules                               │  │
│  │   Constraint: No concrete storage or              │  │
│  │     communication implementation                  │  │
│  │                                                   │  │
│  │   · Task checkpoint state machine                 │  │
│  │   · Instant memory lifecycle                      │  │
│  │   · Experience evolution rules                    │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────┬───────────────────────────────┘
                          │ Connected via plugin interfaces
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ Storage  │  │Retrieval │  │  Agent   │
      │ Plugin   │  │ Plugin   │  │ Adapter  │
      └──────────┘  └──────────┘  └──────────┘
```

### 3.2 Inter-Layer Dependency Rules

```
Interface Contract ◀──── Runtime Layer (depends on interface contracts)
Interface Contract ◀──── Lifecycle Layer (depends on interface contracts)
Runtime Layer      ◀──── Lifecycle Layer (executes lifecycle rules via runtime)

Plugins            ────▶ Interface Contract (implements plugin interfaces)
Plugins            ────▶ Runtime Layer (dispatched by runtime)

Agent              ────▶ Runtime Layer (invokes via MCP)
Agent              ────▶ Interface Contract (follows data models)
```

**Prohibited Dependency Directions**:

- The Interface Contract layer must not depend on the Runtime or Lifecycle layers
- The Lifecycle layer must not depend on concrete plugin implementations
- Plugins must not communicate directly with each other

### 3.3 Layer Responsibilities in Detail

#### 3.3.1 Interface Contract Layer

Defines the capability boundary of the framework. Composed of the following sub-interfaces:

```
Interface Contract Layer
│
├── Experience Interface
│   Defines CRUD operation contracts for experience data
│
├── Retrieval Interface
│   Defines operation contracts for experience retrieval
│
├── Plugin Interface
│   Defines integration contracts for storage and retrieval plugins
│
└── Protocol Contract
    Defines MCP tool names, parameter structures, and response formats
```

#### 3.3.2 Runtime Layer

The execution environment for interface contracts. Divided into two runtime instances:

**Local Runtime (Local SDK)**

| Module | Responsibility |
|--------|---------------|
| Instant Memory Manager | Generation, condensation, and eviction of instant memories |
| MCP Client | Establishes MCP connection with CNAA Server |
| Context Injector | Loads instant memories into Agent context at startup |

**Remote Runtime (CNAA Server)**

| Module | Responsibility |
|--------|---------------|
| Experience Persistence Engine | Receives and persists task checkpoint data |
| MCP Server | Exposes MCP tool interfaces |
| Plugin Dispatcher | Routes to storage and retrieval plugins based on configuration |

#### 3.3.3 Lifecycle Layer

Manages state transitions of experience entities. Independent of the runtime, configurable separately.

Contains three subsystems (see [4.4 Lifecycle](#44-lifecycle) for details):

- Task checkpoint state machine
- Instant memory lifecycle
- Experience evolution rules

---

## 4. Core Conceptual Model

### 4.1 Task Checkpoint

A task checkpoint is the fundamental experience unit in CNAA.

The Agent progresses through tasks in an evaluation environment. Upon reaching a checkpoint, it evaluates the completion score, uploads the full task data to CNAA, and generates a lightweight instant memory summary.

```
Task Execution Flow
│
├── Checkpoint A (completion 0.3) ──▶ Upload full data to CNAA ──▶ Generate Instant Memory A'
├── Checkpoint B (completion 0.6) ──▶ Upload full data to CNAA ──▶ Generate Instant Memory B'
└── Checkpoint C (completion 1.0) ──▶ Upload full data to CNAA ──▶ Generate Instant Memory C'
```

**Task checkpoint boundaries are defined by the Agent itself.** CNAA provides open integration interfaces and does not enforce checkpoint granularity rules. This affects effectiveness only, not architecture.

### 4.2 Instant Memory

Instant memory is a lightweight summary of a task checkpoint, retained in the Agent's context.

| Attribute | Storage Location | Characteristics |
|-----------|-----------------|-----------------|
| Full checkpoint data | CNAA Cloud | Heavyweight, contains complete task snapshot |
| Instant memory summary | Agent local context | Lightweight, contains key index only |

Three core functions of instant memory:

1. **Quick Localization**: After task interruption, the Agent quickly understands "where it left off" through summaries
2. **On-Demand Backtracking**: Through reference pointers, the Agent pulls full task details from CNAA via MCP protocol
3. **Pseudo-Continuity**: Multiple instant memories undergo condensation and eviction within the context, simulating memory continuity through a "small index → large storage" pattern

### 4.3 Pseudo-Continuous Memory

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
    └── No details needed ──▶ Continue execution based on summaries
```

Condensation mechanism:

- Multiple instant memories participate in condensation and eviction
- Old summaries can be condensed into index pointers, retaining only key information
- Full data is re-fetched from CNAA through pointers when needed

### 4.4 Lifecycle

#### 4.4.1 Task Checkpoint State Machine

```
         ┌──────────┐
         │ pending  │
         └────┬─────┘
              │ begin execution
              ▼
         ┌──────────┐
    ┌────│ active   │────┐
    │    └──────────┘    │
    │ success         failure
    ▼                    ▼
┌──────────┐      ┌──────────┐
│completed │      │  failed  │
└────┬─────┘      └──────────┘
     │ archive
     ▼
┌──────────┐
│ archived │
└──────────┘
```

#### 4.4.2 Instant Memory Lifecycle

```
created ──▶ active ──▶ condensed ──▶ evicted
```

| State | Meaning |
|-------|---------|
| created | Just generated from a task checkpoint |
| active | Readable and usable by the Agent |
| condensed | Condensed into an index pointer; full data must be fetched from CNAA |
| evicted | Removed from local context |

#### 4.4.3 Experience Evolution Rules

```
accumulated ──▶ associated ──▶ decayed
```

| Phase | Meaning |
|-------|---------|
| accumulated | Experience data is continuously written |
| associated | Cross-task experiences establish associations |
| decayed | Long-unreferenced experiences have lowered priority |

---

## 5. Interface Contract Specification

### 5.1 Experience Interface

#### `store` — Write a Task Checkpoint

**Request**:

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

**Response**:

```json
{
  "status": "ok",
  "checkpoint_id": "string"
}
```

#### `get` — Read a Task Checkpoint

**Request**:

```json
{
  "task_id": "string",
  "checkpoint_id": "string"
}
```

**Response**:

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

#### `list` — List Task Checkpoints

**Request**:

```json
{
  "task_id": "string"
}
```

**Response**:

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

### 5.2 Retrieval Interface

#### `search` — Search Experience by Query

**Request**:

```json
{
  "query": "string",
  "limit": 5
}
```

**Response**:

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

#### `recall` — Recall Relevant Experience Based on Context

**Request**:

```json
{
  "context": {},
  "limit": 5
}
```

**Response**:

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

### 5.3 Data Models

#### Task

```
Task
├── task_id        : string    — Unique task identifier
├── title          : string    — Task title
├── status         : enum      — pending | active | completed | failed | archived
├── created_at     : datetime  — Creation time
└── updated_at     : datetime  — Last update time
```

#### TaskCheckpoint

```
TaskCheckpoint
├── task_id          : string    — Parent task identifier
├── checkpoint_id    : string    — Unique checkpoint identifier
├── data             : object    — Full task snapshot (Agent-defined structure)
├── completion_score : float     — Completion score [0.0, 1.0]
├── timestamp        : datetime  — Checkpoint timestamp
└── metadata         : object    — Optional extension metadata
```

#### InstantMemory

```
InstantMemory
├── task_id          : string    — Associated task identifier
├── checkpoint_id    : string    — Associated checkpoint identifier
├── summary          : string    — Lightweight summary (Agent-generated)
├── completion_score : float     — Completion score [0.0, 1.0]
├── status           : enum      — created | active | condensed | evicted
├── timestamp        : datetime  — Generation time
└── cnaa_ref         : string    — CNAA reference pointer
```

---

## 6. Plugin System

### 6.1 Storage Plugin Interface (StoragePlugin)

```
StoragePlugin
│
├── save(checkpoint: TaskCheckpoint) → { status: string }
├── load(task_id: string, checkpoint_id: string) → TaskCheckpoint
├── list(task_id?: string) → [CheckpointSummary]
└── delete(task_id: string, checkpoint_id: string) → { status: string }
```

**Reference Implementations**:

| Implementation | Scenario | Priority |
|---------------|----------|----------|
| SQLite | Local development, single-node deployment | v0.1 |
| PostgreSQL | Production, multi-tenant | v0.2 |
| File System | Minimal scenarios, debugging | v0.2 |

### 6.2 Retrieval Plugin Interface (RetrievalPlugin)

```
RetrievalPlugin
│
├── index(checkpoint: TaskCheckpoint) → { status: string }
├── search(query: string, limit?: int) → [SearchResult]
└── recall(context: object, limit?: int) → [SearchResult]
```

**Reference Implementations**:

| Implementation | Scenario | Priority |
|---------------|----------|----------|
| Vector Retrieval (Embedding + ANN) | Semantic similarity | v0.2 |
| Full-Text Retrieval (BM25) | Keyword matching | v0.2 |
| Hybrid Retrieval | Semantic + keyword fusion | v0.3 |

### 6.3 Plugin Integration Rules

- Plugins are integrated through the Plugin Interface defined in the Interface Contract layer
- The Plugin Dispatcher in the Runtime layer is responsible for invoking plugins
- Plugins must not communicate directly with each other
- Plugin implementation details are transparent to the Interface Contract layer

---

## 7. Communication Protocol

### 7.1 Protocol Selection

CNAA uses **MCP (Model Context Protocol)** as its sole communication protocol.

### 7.2 Communication Model

```
Agent (MCP Client)
    │
    │  MCP Tool Call (JSON Request)
    ▼
CNAA Server (MCP Server)
    │
    │  JSON Response
    ▼
Agent (MCP Client)
```

All communication consists of JSON request-response pairs. No streaming, no bidirectional push.

### 7.3 MCP Tool Inventory

| Tool Name | Corresponding Interface | Input | Output |
|-----------|------------------------|-------|--------|
| `cnaa_store` | Experience.store | TaskCheckpoint JSON | `{ status }` |
| `cnaa_get` | Experience.get | `task_id`, `checkpoint_id` | TaskCheckpoint JSON |
| `cnaa_list` | Experience.list | `task_id?` | `{ checkpoints: [] }` |
| `cnaa_search` | Retrieval.search | `query`, `limit?` | `{ results: [] }` |
| `cnaa_recall` | Retrieval.recall | `context`, `limit?` | `{ results: [] }` |

---

## 8. Architectural Constraints and Invariants

### 8.1 Invariants

The following constraints are guaranteed by the framework and must not be replaced or violated:

| ID | Constraint | Rationale |
|----|-----------|-----------|
| I-1 | All interface inputs and outputs are structured JSON | Dumb Service Principle |
| I-2 | CNAA does not perform reasoning, run LLMs, or generate content | Dumb Service Principle |
| I-3 | Core data model fields cannot be omitted | `task_id`, `checkpoint_id`, `data`, `completion_score` |
| I-4 | MCP is the sole communication protocol | Protocol consistency |
| I-5 | Inter-layer dependency direction is strictly downward | Interface Contract ◀ Runtime ◀ Lifecycle |

### 8.2 Replaceable Components

| Replaceable Item | Replacement Method | Impact Scope |
|-----------------|-------------------|-------------|
| Storage backend | Implement StoragePlugin interface | Runtime layer only |
| Retrieval strategy | Implement RetrievalPlugin interface | Runtime layer only |
| Checkpoint granularity | Agent-defined boundaries | Does not affect CNAA |
| Instant memory condensation rules | Modify Lifecycle layer configuration | Lifecycle layer only |
| Agent framework | Implement Agent Adapter | Runtime layer only |

---

## 9. Deployment Topology

### 9.1 Standard Topology

```
┌─────────────────────┐          ┌─────────────────────────┐
│    Agent (Local)     │          │      CNAA (Cloud)        │
│                     │          │                         │
│  ┌───────────────┐  │   MCP    │  ┌───────────────────┐  │
│  │  Agent Process │  │◀──────▶│  │  CNAA Server      │  │
│  └───────┬───────┘  │          │  │  (MCP Server)     │  │
│          │          │          │  └────────┬──────────┘  │
│  ┌───────▼───────┐  │          │           │             │
│  │ Local Runtime  │  │          │  ┌────────▼──────────┐  │
│  │ · Instant      │  │          │  │ StoragePlugin     │  │
│  │   Memory       │  │          │  │ (SQLite / PG / …) │  │
│  │ · MCP Client   │  │          │  └───────────────────┘  │
│  └───────────────┘  │          │  ┌───────────────────┐  │
│                     │          │  │ RetrievalPlugin   │  │
│                     │          │  │ (Vector / BM25 / …) │  │
│                     │          │  └───────────────────┘  │
└─────────────────────┘          └─────────────────────────┘
```

### 9.2 Local Development Topology

```
┌──────────────────────────────────────┐
│        Local Development Environment  │
│                                      │
│  ┌──────────┐    MCP   ┌──────────┐ │
│  │  Agent   │◀────────▶│  CNAA    │ │
│  │          │          │  Server  │ │
│  └──────────┘          │ (SQLite) │ │
│                        └──────────┘ │
└──────────────────────────────────────┘
```

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| Experience Memory | Reusable knowledge generated by the Agent during task execution |
| Task Checkpoint | An evaluable node in the task execution flow, containing a full task snapshot |
| Instant Memory | A lightweight summary of a task checkpoint, retained in the Agent's local context |
| Pseudo-Continuous Memory | Memory continuity simulated through "instant memory index + cloud full data" |
| Interface Contract | An operational specification defining the framework's capability boundary |
| Plugin | An external component integrated through a standard interface (storage, retrieval, etc.) |
| Dumb Service | A service pattern that only performs JSON read/write without reasoning |
| Condense | The process by which an instant memory degrades from a full summary to an index pointer |
| Evict | The process by which an instant memory is removed from local context |
