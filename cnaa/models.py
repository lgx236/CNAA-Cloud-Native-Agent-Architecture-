"""CNAA Core Data Model Specification.

Defines all data structures used in the CNAA framework.
These models are the fundamental building blocks of the
interface contract layer — they define WHAT the framework manages.

Key concepts:
- Memory: Experience memory entity (long-term in cloud, short-term local)
- TaskCheckpoint: Compressed task point with full memory + summary
- State: Agent accumulated knowledge (condensed from experiences)
- Preference: Agent important memory patterns (shape behavior)
- Environment: Agent environment context
- InstantMemory: Local short-term memory with cloud reference pointer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MemoryType(str, Enum):
    """Memory storage location.

    LONG_TERM:  Persisted in CNAA cloud (remote).
    SHORT_TERM: Kept in agent local context (local).
    """

    LONG_TERM = "long_term"
    SHORT_TERM = "short_term"


class MemoryStatus(str, Enum):
    """Memory lifecycle status.

    ACTIVE:    Available for direct use by agent.
    CONDENSED: Condensed to index pointer, full data in cloud.
    EVICTED:   Removed from local context.
    """

    ACTIVE = "active"
    CONDENSED = "condensed"
    EVICTED = "evicted"


class StateCategory(str, Enum):
    """State classification.

    PREFERENCE:  Important memory patterns that shape agent behavior.
    KNOWLEDGE:   Accumulated knowledge from experiences.
    ENVIRONMENT: Environment context the agent operates in.
    """

    PREFERENCE = "preference"
    KNOWLEDGE = "knowledge"
    ENVIRONMENT = "environment"


# ---------------------------------------------------------------------------
# Core Data Models
# ---------------------------------------------------------------------------

@dataclass
class Memory:
    """Experience memory entity.

    The core unit of experience in CNAA. A memory can be:
    - Long-term: persisted in CNAA cloud for cross-device access
    - Short-term: kept in agent local context for immediate use

    The content field is an open JSON structure — CNAA does not
    interpret or reason about memory content (dumb service principle).
    """

    memory_id: str
    agent_id: str
    type: MemoryType
    content: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    completion_score: float = 0.0
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TaskCheckpoint:
    """Task checkpoint with compressed memory.

    Represents a completed task point. Contains:
    - compressed_memory: Full task data for cloud storage (long-term)
    - summary: Lightweight summary for local instant memory

    Flow: Agent completes task point → compresses into checkpoint →
    full data stored in cloud, summary kept as instant memory locally.
    """

    task_id: str
    checkpoint_id: str
    compressed_memory: Memory
    summary: str
    completion_score: float
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class State:
    """Agent state — accumulated knowledge.

    Represents knowledge that has been condensed from experience
    memories over time. States form the agent's persistent
    knowledge base in the cloud.

    Multiple local instances (same agent_id) share the same
    cloud state, enabling cross-device consistency.
    """

    agent_id: str
    state_id: str
    category: StateCategory
    content: dict[str, Any]
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Preference:
    """Agent preference — important memory patterns.

    Preferences are important memories that have been identified
    as shaping the agent's behavior and decision-making patterns.
    They are persisted in the cloud and shared across all local
    instances of the same agent.
    """

    agent_id: str
    preference_id: str
    key: str
    value: dict[str, Any]
    importance: float = 0.0
    source_memory_ids: list[str] = field(default_factory=list)


@dataclass
class Environment:
    """Agent environment context.

    Stores the current environment state that the agent operates in.
    Provides context-aware information for agent decision-making.
    Persisted in cloud, accessible from any local instance.
    """

    agent_id: str
    env_id: str
    context: dict[str, Any]
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class InstantMemory:
    """Instant memory — local short-term memory.

    Lightweight summary kept in agent's local context.
    Contains a reference pointer (cnaa_ref) to the full
    memory stored in CNAA cloud.

    Lifecycle: active → condensed → evicted
    - active:    Full summary available locally
    - condensed: Reduced to index pointer, pull full data via cnaa_ref
    - evicted:   Removed from local context
    """

    memory_id: str
    task_id: str
    checkpoint_id: str
    summary: str
    status: MemoryStatus = MemoryStatus.ACTIVE
    cnaa_ref: str = ""
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class MemorySummary:
    """Lightweight memory summary for list operations."""

    memory_id: str
    tags: list[str] = field(default_factory=list)
    completion_score: float = 0.0
    timestamp: datetime | None = None


@dataclass
class SearchResult:
    """Search result from memory retrieval."""

    memory_id: str
    agent_id: str
    summary: str
    completion_score: float
    relevance_score: float
