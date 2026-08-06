"""CNAA Interaction Interface Specification.

Defines the abstract interfaces for local-cloud interaction.
These interfaces specify WHAT operations are available, not HOW they
are implemented. Cloud and local modules provide reference implementations.

Key interfaces:
- MemoryInterface: Memory operation contract (store/get/list/tag/delete)
- StateInterface: State operation contract (get/update/delete for state/preference/environment)

IMPLEMENTED:
    - Abstract interface definitions using ABC/abstractmethod
    - Full type annotations for all parameters and return types
    - Docstrings specifying the dumb service contract (JSON in/out, no reasoning)
    - Two orthogonal interfaces: MemoryInterface (experience) + StateInterface (state)

TODO (algorithm extension point):
    - Add async variants (AsyncMemoryInterface, AsyncStateInterface)
    - Add batch operation methods (store_memories, get_memories_bulk)
    - Add streaming interface for large memory retrieval
    - Add query builder pattern for complex memory searches
    - Add versioning/optimistic locking for concurrent state updates
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from cnaa.models import (
    Environment,
    Memory,
    MemorySummary,
    MemoryType,
    Preference,
    State,
)


# ---------------------------------------------------------------------------
# Memory Operation Interface
# ---------------------------------------------------------------------------

class MemoryInterface(ABC):
    """Abstract interface for memory operations.

    Defines the contract for storing, retrieving, and managing
    experience memories. Implementations must follow the dumb service
    principle: JSON in, JSON out, no reasoning.

    IMPLEMENTED:
        - 5 abstract methods covering full memory CRUD lifecycle
        - store_memory: Write memory (long-term → cloud, short-term → local)
        - get_memory: Read single memory by (agent_id, memory_id) composite key
        - list_memories: Query with optional type/tag filters
        - tag_short_term: Apply labels to recent memories
        - delete_memory: Remove memory by ID

    TODO (algorithm extension point):
        - Add search_memories(query, top_k) for semantic retrieval
        - Add get_similar(memory_id, threshold) for experience matching
        - Add condense(agent_id, strategy) for memory compression
        - Add memory lifecycle hooks (on_store, on_retrieve, on_expire)
    """

    @abstractmethod
    def store_memory(self, memory: Memory) -> dict[str, Any]:
        """Store a memory (long-term or short-term).

        For long-term memories: persists to cloud storage.
        For short-term memories: stores in local context.

        Args:
            memory: The memory entity to store.

        Returns:
            Dict with 'status' and 'memory_id' on success.
            Example: {"status": "ok", "memory_id": "mem-001"}
        """
        ...

    @abstractmethod
    def get_memory(self, agent_id: str, memory_id: str) -> Memory | None:
        """Retrieve a memory by ID.

        Args:
            agent_id: The agent identifier.
            memory_id: The memory identifier.

        Returns:
            The memory entity if found, None otherwise.
        """
        ...

    @abstractmethod
    def list_memories(
        self,
        agent_id: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
    ) -> list[MemorySummary]:
        """List memories for an agent with optional filtering.

        Args:
            agent_id: The agent identifier.
            memory_type: Optional filter by memory type (long_term/short_term).
            tags: Optional filter by tags.

        Returns:
            List of memory summaries (lightweight, no full content).
        """
        ...

    @abstractmethod
    def tag_short_term(
        self, agent_id: str, tags: list[str]
    ) -> dict[str, Any]:
        """Tag short-term memories with labels.

        Used to mark recent memories for later retrieval or
        knowledge condensation.

        Args:
            agent_id: The agent identifier.
            tags: List of tags to apply.

        Returns:
            Dict with 'status' on success.
            Example: {"status": "ok"}
        """
        ...

    @abstractmethod
    def delete_memory(self, agent_id: str, memory_id: str) -> dict[str, Any]:
        """Delete a memory.

        Args:
            agent_id: The agent identifier.
            memory_id: The memory identifier.

        Returns:
            Dict with 'status' on success.
            Example: {"status": "ok"}
        """
        ...
    
    # --- Scoring Methods (NEW) ---
    
    @abstractmethod
    def get_memory_scores(
        self,
        agent_id: str,
        access_counts: dict[str, int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get scored memories for an agent.
        
        Calculate composite scores for all memories and return them
        sorted by composite score (highest first).
        
        Args:
            agent_id: The agent identifier.
            access_counts: Optional dict mapping memory_id to access count.
            context: Optional context for relevance scoring.
        
        Returns:
            List of dicts with memory summaries and scores.
            Each dict contains: memory_id, scores (recency, completion, importance, frequency, relevance),
            composite_score, and original memory fields.
        """
        ...


# ---------------------------------------------------------------------------
# State Operation Interface
# ---------------------------------------------------------------------------

class StateInterface(ABC):
    """Abstract interface for state operations.

    Defines the contract for managing agent state, preferences,
    and environment context. All operations follow the dumb service
    principle (JSON in, JSON out, no reasoning).

    State categories:
    - State: Accumulated knowledge from experiences
    - Preference: Important memory patterns that shape behavior
    - Environment: Context information for agent operation

    IMPLEMENTED:
        - 9 abstract methods covering 3 state categories (State/Preference/Environment)
        - Each category: get (read all) + update (upsert) + delete (remove)
        - Environment: get (read) + update (upsert) only — no delete (always present)
        - All methods keyed by agent_id for multi-tenant isolation

    TODO (algorithm extension point):
        - Add state evolution hooks (before_update, after_update, on_conflict)
        - Add state diff/merge for cross-device state synchronization
        - Add state versioning with rollback capability
        - Add preference importance decay over time
        - Add environment auto-refresh based on agent context
    """

    # --- State (Knowledge) ---

    @abstractmethod
    def get_state(self, agent_id: str) -> list[State]:
        """Retrieve all state entries for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            List of state entries.
        """
        ...

    @abstractmethod
    def update_state(self, agent_id: str, state: State) -> dict[str, Any]:
        """Create or update a state entry.

        Args:
            agent_id: The agent identifier.
            state: The state to persist.

        Returns:
            Dict with 'status' on success.
            Example: {"status": "ok"}
        """
        ...

    @abstractmethod
    def delete_state(self, agent_id: str, state_id: str) -> dict[str, Any]:
        """Delete a state entry.

        Args:
            agent_id: The agent identifier.
            state_id: The state identifier.

        Returns:
            Dict with 'status' on success.
            Example: {"status": "ok"}
        """
        ...

    # --- Preference (Important Memories) ---

    @abstractmethod
    def get_preference(self, agent_id: str) -> list[Preference]:
        """Retrieve all preferences for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            List of preference entries.
        """
        ...

    @abstractmethod
    def update_preference(
        self, agent_id: str, preference: Preference
    ) -> dict[str, Any]:
        """Create or update a preference entry.

        Args:
            agent_id: The agent identifier.
            preference: The preference to persist.

        Returns:
            Dict with 'status' on success.
            Example: {"status": "ok"}
        """
        ...

    @abstractmethod
    def delete_preference(
        self, agent_id: str, preference_id: str
    ) -> dict[str, Any]:
        """Delete a preference entry.

        Args:
            agent_id: The agent identifier.
            preference_id: The preference identifier.

        Returns:
            Dict with 'status' on success.
            Example: {"status": "ok"}
        """
        ...

    # --- Environment (Context) ---

    @abstractmethod
    def get_environment(self, agent_id: str) -> Environment | None:
        """Retrieve the environment context for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            The environment entry if found, None otherwise.
        """
        ...

    @abstractmethod
    def update_environment(
        self, agent_id: str, environment: Environment
    ) -> dict[str, Any]:
        """Create or update the environment context.

        Args:
            agent_id: The agent identifier.
            environment: The environment to persist.

        Returns:
            Dict with 'status' on success.
            Example: {"status": "ok"}
        """
        ...
