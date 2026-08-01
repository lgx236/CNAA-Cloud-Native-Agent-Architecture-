# CNAA V0.1 API Reference

> Cloud Native Agentic Architecture - Interface Specification
>
> Version: v0.1.0

---

## 1. Overview

CNAA (Cloud Native Agentic Architecture) is an experience runtime framework for AI Agents. This document defines the core interface specifications, including:

- **Data Models**: Core data structures for memory, state, preference, and environment
- **Interaction Interfaces**: Operation contracts between local and cloud
- **MCP Tools**: Tool definitions exposed via MCP protocol
- **Lifecycle**: State transition rules for memory and state

### 1.1 Architecture Pattern

```
Cloud (Single Instance)
┌──────────────────────────────────────┐
│           CNAA Server                │
│         (MCP Server)                 │
│                                      │
│  · Long-term memory persistence      │
│  · State management                  │
│  · Environment state                 │
│  · MCP tool exposure                 │
└──────────────┬───────────────────────┘
               │ MCP over HTTP
               │ (Streamable HTTP)
      ┌────────┼────────┐
      ▼        ▼        ▼
┌──────────┐┌──────────┐┌──────────┐
│ Agent 1  ││ Agent 2  ││ Agent N  │   Local (Multiple Instances)
│(MCP Cli) ││(MCP Cli) ││(MCP Cli) │
│          ││          ││          │
│·Short-term│·Short-term│·Short-term│
│·Local     │·Local     │·Local     │
└──────────┘└──────────┘└──────────┘

Multi-location same agent: Multiple local instances share the same cloud state
```

### 1.2 Core Interaction Flow

```
Agent completes task → Compress memory → Upload long-term memory to cloud via MCP tool
                                              ↓
Agent needs recall → Request long-term memory / state via MCP tool
                                              ↓
Agent initializes → Request preference / environment via MCP tool
                                              ↓
Knowledge condensation → Important memory → preference, Short-term knowledge → state
```

---

## 2. Data Models

### 2.1 Memory

Memory is the core experience unit in CNAA.

```json
{
  "memory_id": "string",           // Unique memory identifier
  "agent_id": "string",            // Owner agent identifier
  "type": "long_term | short_term", // Memory type: long-term/short-term
  "content": {},                    // Memory content (open JSON structure)
  "tags": ["string"],               // Memory tags (for retrieval)
  "completion_score": 0.0,          // Task completion score [0.0, 1.0]
  "timestamp": "ISO-8601",          // Memory timestamp
  "metadata": {}                    // Optional extension metadata
}
```

**Notes**:
- `content` is an open JSON structure; CNAA does not interpret or reason about it (dumb service principle)
- `type` determines storage location: `long_term` stored in cloud, `short_term` stored locally
- `tags` used for memory retrieval and classification

### 2.2 TaskCheckpoint

A task checkpoint represents a completed task node with compressed full memory.

```json
{
  "task_id": "string",              // Task identifier
  "checkpoint_id": "string",        // Checkpoint unique identifier
  "compressed_memory": {            // Compressed full memory (stored in cloud)
    "memory_id": "string",
    "agent_id": "string",
    "type": "long_term",
    "content": {},
    "tags": [],
    "completion_score": 0.0,
    "timestamp": "ISO-8601"
  },
  "summary": "string",              // Lightweight summary (stored as instant memory locally)
  "completion_score": 0.0,          // Task completion score
  "timestamp": "ISO-8601"           // Checkpoint timestamp
}
```

**Flow**:
```
Agent completes task → Compress to TaskCheckpoint →
  Full data (compressed_memory) stored in cloud →
  Lightweight summary (summary) stored as instant memory locally
```

### 2.3 State

State represents knowledge condensed from agent experiences.

```json
{
  "agent_id": "string",             // Owner agent identifier
  "state_id": "string",             // State unique identifier
  "category": "preference | knowledge | environment", // State category
  "content": {},                    // State content (JSON)
  "updated_at": "ISO-8601"          // Last update time
}
```

**Category descriptions**:
- `preference`: Important memory patterns that shape agent behavior
- `knowledge`: Knowledge accumulated from experiences
- `environment`: Environment context the agent operates in

### 2.4 Preference

Preference represents important memory patterns that influence decision-making behavior.

```json
{
  "agent_id": "string",             // Owner agent identifier
  "preference_id": "string",        // Preference unique identifier
  "key": "string",                  // Preference key/label
  "value": {},                      // Preference content (JSON)
  "importance": 0.0,                // Importance score [0.0, 1.0]
  "source_memory_ids": ["string"]   // Source memory identifier list
}
```

### 2.5 Environment

Environment represents the context information where the agent operates.

```json
{
  "agent_id": "string",             // Owner agent identifier
  "env_id": "string",               // Environment unique identifier
  "context": {},                    // Environment context (JSON)
  "updated_at": "ISO-8601"          // Last update time
}
```

### 2.6 InstantMemory

Instant memory is local short-term memory with a reference pointer to cloud long-term memory.

```json
{
  "memory_id": "string",            // Memory unique identifier
  "task_id": "string",              // Associated task identifier
  "checkpoint_id": "string",        // Associated checkpoint identifier
  "summary": "string",              // Lightweight summary
  "status": "active | condensed | evicted", // Status
  "cnaa_ref": "string",             // Reference to cloud long-term memory
  "timestamp": "ISO-8601"           // Generation time
}
```

**Lifecycle**:
```
active → condensed → evicted
```

- `active`: Full summary available
- `condensed`: Reduced to index pointer, pull full data via `cnaa_ref`
- `evicted`: Removed from local context

---

## 3. Interaction Interfaces

### 3.1 Memory Operation Interfaces

#### store_memory — Upload Long-term Memory

**Function**: Persist memory to CNAA cloud

**Request**:
```json
{
  "agent_id": "string",
  "memory_id": "string",
  "content": {},
  "tags": ["string"],
  "completion_score": 0.0,
  "metadata": {}
}
```

**Response**:
```json
{
  "status": "ok",
  "memory_id": "string"
}
```

#### get_memory — Request Long-term Memory

**Function**: Pull full memory data from cloud

**Request**:
```json
{
  "agent_id": "string",
  "memory_id": "string"
}
```

**Response**:
```json
{
  "memory_id": "string",
  "agent_id": "string",
  "content": {},
  "tags": ["string"],
  "completion_score": 0.0,
  "timestamp": "ISO-8601",
  "metadata": {}
}
```

#### list_memories — List Memories

**Function**: List agent's memories (with filtering support)

**Request**:
```json
{
  "agent_id": "string",
  "type": "long_term | short_term",  // Optional
  "tags": ["string"]                 // Optional
}
```

**Response**:
```json
{
  "memories": [
    {
      "memory_id": "string",
      "tags": ["string"],
      "completion_score": 0.0,
      "timestamp": "ISO-8601"
    }
  ]
}
```

#### tag_short_term — Tag Short-term Memory

**Function**: Add tags to short-term memories for later retrieval or knowledge condensation

**Request**:
```json
{
  "agent_id": "string",
  "tags": ["string"]
}
```

**Response**:
```json
{
  "status": "ok"
}
```

#### delete_memory — Delete Memory

**Function**: Delete memory from cloud

**Request**:
```json
{
  "agent_id": "string",
  "memory_id": "string"
}
```

**Response**:
```json
{
  "status": "ok"
}
```

### 3.2 State Operation Interfaces

#### get_state — Request State

**Function**: Get all states (knowledge condensation) for an agent

**Request**:
```json
{
  "agent_id": "string"
}
```

**Response**:
```json
{
  "states": [
    {
      "state_id": "string",
      "category": "preference | knowledge | environment",
      "content": {},
      "updated_at": "ISO-8601"
    }
  ]
}
```

#### update_state — Update State

**Function**: Create or update a state entry

**Request**:
```json
{
  "agent_id": "string",
  "state_id": "string",
  "category": "preference | knowledge | environment",
  "content": {}
}
```

**Response**:
```json
{
  "status": "ok"
}
```

#### delete_state — Delete State

**Function**: Delete a state entry

**Request**:
```json
{
  "agent_id": "string",
  "state_id": "string"
}
```

**Response**:
```json
{
  "status": "ok"
}
```

#### get_preference — Request Preference

**Function**: Get all preferences (important memory patterns) for an agent

**Request**:
```json
{
  "agent_id": "string"
}
```

**Response**:
```json
{
  "preferences": [
    {
      "preference_id": "string",
      "key": "string",
      "value": {},
      "importance": 0.0,
      "source_memory_ids": ["string"]
    }
  ]
}
```

#### update_preference — Update Preference

**Function**: Create or update a preference entry

**Request**:
```json
{
  "agent_id": "string",
  "preference_id": "string",
  "key": "string",
  "value": {},
  "importance": 0.0,
  "source_memory_ids": ["string"]
}
```

**Response**:
```json
{
  "status": "ok"
}
```

#### delete_preference — Delete Preference

**Function**: Delete a preference entry

**Request**:
```json
{
  "agent_id": "string",
  "preference_id": "string"
}
```

**Response**:
```json
{
  "status": "ok"
}
```

#### get_environment — Request Environment

**Function**: Get agent's environment context

**Request**:
```json
{
  "agent_id": "string"
}
```

**Response**:
```json
{
  "env_id": "string",
  "context": {},
  "updated_at": "ISO-8601"
}
```

#### update_environment — Update Environment

**Function**: Create or update environment context

**Request**:
```json
{
  "agent_id": "string",
  "env_id": "string",
  "context": {}
}
```

**Response**:
```json
{
  "status": "ok"
}
```

---

## 4. MCP Tool Definitions

CNAA Server exposes the following tools via MCP protocol:

| Tool Name | Function | Input | Output |
|-----------|----------|-------|--------|
| `cnaa_store_memory` | Upload long-term memory | Memory JSON | `{status, memory_id}` |
| `cnaa_get_memory` | Request long-term memory | `agent_id`, `memory_id` | Memory JSON |
| `cnaa_list_memories` | List memories | `agent_id`, `type?`, `tags?` | `{memories: []}` |
| `cnaa_tag_short_term` | Tag short-term memory | `agent_id`, `tags` | `{status}` |
| `cnaa_delete_memory` | Delete memory | `agent_id`, `memory_id` | `{status}` |
| `cnaa_get_state` | Request State | `agent_id` | `{states: []}` |
| `cnaa_update_state` | Update State | `agent_id`, State JSON | `{status}` |
| `cnaa_delete_state` | Delete State | `agent_id`, `state_id` | `{status}` |
| `cnaa_get_preference` | Request Preference | `agent_id` | `{preferences: []}` |
| `cnaa_update_preference` | Update Preference | `agent_id`, Preference JSON | `{status}` |
| `cnaa_delete_preference` | Delete Preference | `agent_id`, `preference_id` | `{status}` |
| `cnaa_get_environment` | Request Environment | `agent_id` | Environment JSON |
| `cnaa_update_environment` | Update Environment | `agent_id`, Environment JSON | `{status}` |

### 4.1 Tool Call Examples

**Upload long-term memory**:
```json
// Request
{
  "agent_id": "agent-001",
  "memory_id": "mem-20240101-001",
  "content": {
    "task_description": "Database migration task",
    "steps_completed": ["Backup data", "Create new schema"],
    "issues_encountered": ["Field type incompatibility"]
  },
  "tags": ["database", "migration"],
  "completion_score": 0.65
}

// Response
{
  "status": "ok",
  "memory_id": "mem-20240101-001"
}
```

**Request long-term memory**:
```json
// Request
{
  "agent_id": "agent-001",
  "memory_id": "mem-20240101-001"
}

// Response
{
  "memory_id": "mem-20240101-001",
  "agent_id": "agent-001",
  "content": {
    "task_description": "Database migration task",
    "steps_completed": ["Backup data", "Create new schema"],
    "issues_encountered": ["Field type incompatibility"]
  },
  "tags": ["database", "migration"],
  "completion_score": 0.65,
  "timestamp": "2024-01-01T10:30:00Z"
}
```

**Request Preference**:
```json
// Request
{
  "agent_id": "agent-001"
}

// Response
{
  "preferences": [
    {
      "preference_id": "pref-001",
      "key": "coding_style",
      "value": {
        "prefer_type_hints": true,
        "max_line_length": 100
      },
      "importance": 0.8,
      "source_memory_ids": ["mem-20240101-001", "mem-20240102-003"]
    }
  ]
}
```

---

## 5. Lifecycle Rules

### 5.1 Instant Memory Lifecycle

```
created → active → condensed → evicted
```

| Status | Meaning | Trigger Condition |
|--------|---------|-------------------|
| `active` | Full summary available | Just generated from task checkpoint |
| `condensed` | Reduced to index pointer | Exceeds condensation threshold (e.g., 1 hour) |
| `evicted` | Removed from local | Exceeds eviction threshold (e.g., 7 days) |

### 5.2 Memory Condensation Flow

```
1. Agent completes task checkpoint
   ↓
2. Compress full data → Long-term memory (stored in cloud)
   ↓
3. Generate lightweight summary → Instant memory (stored locally)
   ↓
4. Instant memory ages → Condenses to index pointer
   ↓
5. Pull full data via cnaa_ref when needed
```

### 5.3 State Evolution

```
accumulated → associated → decayed
```

| Phase | Meaning |
|-------|---------|
| `accumulated` | Experience data continuously written |
| `associated` | Cross-task experiences establish associations |
| `decayed` | Long-unused experiences decrease in priority |

---

## 6. Design Principles

### 6.1 Dumb Service Principle

CNAA Server only receives structured JSON requests and returns structured JSON responses. It does not perform reasoning, run LLMs, or generate content.

```
Agent ──▶ JSON Request ──▶ CNAA Server ──▶ JSON Response ──▶ Agent
```

### 6.2 Interface First Principle

All capabilities define interface contracts first, then provide implementations. Interface contracts are the core deliverable of the framework; specific implementations are replaceable references.

### 6.3 Pluggable Principle

Storage layer and retrieval layer are accessed through plugin interfaces. Replacing any layer does not affect other layers.

### 6.4 Local First Principle

Agents run locally, CNAA Server runs in the cloud. Instant memories remain in the agent's local context; full experience data is stored in the cloud.

---

## 7. Glossary

| Term | English | Definition |
|------|---------|------------|
| Experience Memory | Experience Memory | Reusable knowledge generated by agents during task execution |
| Task Checkpoint | Task Checkpoint | An evaluable node in the task execution flow, containing complete task snapshots |
| Instant Memory | Instant Memory | Lightweight summary of task checkpoints, kept in agent's local context |
| Long-term Memory | Long-term Memory | Full memory data persisted in the cloud |
| Short-term Memory | Short-term Memory | Memories kept in agent's local context |
| State | State | Knowledge condensed from experiences |
| Preference | Preference | Important memory patterns that influence agent behavior |
| Environment | Environment | Context information where the agent operates |
| Pseudo-Continuous Memory | Pseudo-Continuous Memory | Memory continuity simulated by "instant memory index + cloud full data" |
| Dumb Service | Dumb Service | Service mode that only does JSON storage/retrieval without reasoning |
| Condense | Condense | Process of instant memory degrading from full summary to index pointer |
| Evict | Evict | Process of instant memory being removed from local context |

---

## 8. Version History

- **v0.1.0** (2024-01): Initial version, defining core data models, interaction interfaces, MCP tools, and lifecycle rules
