"""CNAA Lifecycle Specification.

Defines pluggable lifecycle interfaces for memory and state evolution.
External packages can implement these interfaces to provide custom
lifecycle management (e.g., RAG, vector search, knowledge graphs).

Key interfaces:
- MemoryLifecyclePlugin: For custom memory condensation/eviction strategies
- StateEvolutionPlugin: For custom state evolution rules
- RetrievalPlugin: For custom retrieval strategies (vector, BM25, hybrid)

IMPLEMENTED:
    - LifecycleEvent enum: 5 lifecycle transition events
    - LifecycleConfig dataclass: configurable thresholds (time, score)
    - MemoryLifecyclePlugin ABC: 5 abstract methods (condense/evict/promote)
    - TimeBasedLifecyclePlugin: default time-based implementation
    - RetrievalPlugin ABC: 4 abstract methods (index/search/recall/delete)
    - StateEvolutionPlugin ABC: 3 abstract methods (rules/should_evolve/evolve)
    - DefaultStateEvolutionPlugin: default no-op implementation
    - LifecyclePlugins registry: plugin holder with registration methods

TODO (algorithm extension point):
    - Add plugin discovery mechanism (auto-register from entry points)
    - Add plugin chaining (compose multiple plugins in pipeline)
    - Add lifecycle event hooks and observers
    - Add plugin health monitoring and metrics
    - Add hot-reload support for plugin updates without restart
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from cnaa.models import (
    InstantMemory,
    Memory,
    MemoryStatus,
    MemoryType,
    SearchResult,
    TaskCheckpoint,
)


# ---------------------------------------------------------------------------
# Lifecycle Events
# ---------------------------------------------------------------------------

class LifecycleEvent(str, Enum):
    """Events that trigger lifecycle transitions."""

    TASK_COMPLETED = "task_completed"
    MEMORY_CONDENSED = "memory_condensed"
    MEMORY_EVICTED = "memory_evicted"
    MEMORY_PROMOTED = "memory_promoted"  # short-term → long-term
    STATE_EVOLVED = "state_evolved"


# ---------------------------------------------------------------------------
# Lifecycle Configuration
# ---------------------------------------------------------------------------

@dataclass
class LifecycleConfig:
    """Configuration for lifecycle rules.

    These thresholds control when memories transition between states.
    Implementations can customize these values based on use case.
    """

    # Max instant memories before condensation is triggered
    max_active_memories: int = 20

    # Time before active memory becomes candidate for condensation
    condensation_threshold: timedelta = timedelta(hours=1)

    # Time before condensed memory is evicted
    eviction_threshold: timedelta = timedelta(days=7)

    # Completion score threshold for promotion to long-term
    promotion_score_threshold: float = 0.5


# ---------------------------------------------------------------------------
# Memory Lifecycle Plugin Interface
# ---------------------------------------------------------------------------

class MemoryLifecyclePlugin(ABC):
    """Abstract interface for memory lifecycle management.

    Implement this interface to provide custom memory condensation,
    eviction, and promotion strategies.

    IMPLEMENTED:
        - 5 abstract methods defining the memory lifecycle contract
        - should_condense: check if instant memory should be compressed
        - should_evict: check if condensed memory should be removed
        - condense_memory: compress instant memory to index pointer
        - evict_memory: remove condensed memory from local context
        - should_promote_to_long_term: check if short-term → long-term

    TODO (algorithm extension point):
        - Add on_memory_stored hook for post-store processing
        - Add batch condensation/eviction methods
        - Add memory priority scoring
        - Add custom trigger conditions beyond time/score

    Example implementations:
    - TimeBasedLifecyclePlugin: Based on time thresholds
    - UsageBasedLifecyclePlugin: Based on access frequency
    - ImportanceBasedLifecyclePlugin: Based on importance scores
    """

    @abstractmethod
    def should_condense(
        self, memory: InstantMemory, now: datetime | None = None
    ) -> bool:
        """Check if an instant memory should be condensed.

        Args:
            memory: The instant memory to check.
            now: Current time (defaults to now).

        Returns:
            True if memory should be condensed.
        """
        ...

    @abstractmethod
    def should_evict(
        self, memory: InstantMemory, now: datetime | None = None
    ) -> bool:
        """Check if a condensed memory should be evicted.

        Args:
            memory: The instant memory to check.
            now: Current time (defaults to now).

        Returns:
            True if memory should be evicted.
        """
        ...

    @abstractmethod
    def condense_memory(self, memory: InstantMemory) -> InstantMemory:
        """Condense an instant memory to index pointer.

        Args:
            memory: The instant memory to condense.

        Returns:
            Updated instant memory with CONDENSED status.
        """
        ...

    @abstractmethod
    def evict_memory(self, memory: InstantMemory) -> InstantMemory:
        """Evict a condensed memory from local context.

        Args:
            memory: The instant memory to evict.

        Returns:
            Updated instant memory with EVICTED status.
        """
        ...

    @abstractmethod
    def should_promote_to_long_term(self, memory: Memory) -> bool:
        """Check if a short-term memory should be promoted to long-term.

        Args:
            memory: The memory to check.

        Returns:
            True if memory should be promoted.
        """
        ...


# ---------------------------------------------------------------------------
# Default Time-Based Lifecycle Plugin
# ---------------------------------------------------------------------------

class TimeBasedLifecyclePlugin(MemoryLifecyclePlugin):
    """Default time-based lifecycle implementation.

    Uses time thresholds for condensation and eviction.
    
    IMPLEMENTED:
        Time-based condensation: if age >= condensation_threshold, condense.
        Time-based eviction: if age >= eviction_threshold, evict.
        Score-based promotion: if completion_score >= threshold, promote.
        Time complexity: O(1) per check.
    
    TODO (algorithm extension point):
        - Support composite scoring (time + importance + access frequency)
        - Support adaptive thresholds (adjust based on memory volume)
        - Support custom condensation scoring functions
    """

    def __init__(self, config: LifecycleConfig | None = None) -> None:
        self.config = config or LifecycleConfig()

    def should_condense(
        self, memory: InstantMemory, now: datetime | None = None
    ) -> bool:
        """Check if memory age exceeds condensation threshold."""
        if memory.status != MemoryStatus.ACTIVE:
            return False

        if now is None:
            now = datetime.now()

        if memory.timestamp is None:
            return False

        age = now - memory.timestamp
        return age >= self.config.condensation_threshold

    def should_evict(
        self, memory: InstantMemory, now: datetime | None = None
    ) -> bool:
        """Check if condensed memory age exceeds eviction threshold."""
        if memory.status != MemoryStatus.CONDENSED:
            return False

        if now is None:
            now = datetime.now()

        if memory.timestamp is None:
            return False

        age = now - memory.timestamp
        return age >= self.config.eviction_threshold

    def condense_memory(self, memory: InstantMemory) -> InstantMemory:
        """Condense memory to index pointer."""
        memory.status = MemoryStatus.CONDENSED
        return memory

    def evict_memory(self, memory: InstantMemory) -> InstantMemory:
        """Evict memory from local context."""
        memory.status = MemoryStatus.EVICTED
        return memory

    def should_promote_to_long_term(self, memory: Memory) -> bool:
        """Check if memory completion score exceeds threshold."""
        if memory.type != MemoryType.SHORT_TERM:
            return False

        return memory.completion_score >= self.config.promotion_score_threshold


# ---------------------------------------------------------------------------
# Retrieval Plugin Interface (for external packages)
# ---------------------------------------------------------------------------

class RetrievalPlugin(ABC):
    """Abstract interface for memory retrieval strategies.

    Implement this interface to provide custom retrieval algorithms.
    External packages (RAG, vector DB, knowledge graphs) should implement
    this interface to integrate with CNAA.

    IMPLEMENTED:
        - 4 abstract methods defining the retrieval contract
        - index: index a memory for later retrieval
        - search: query-based memory search with filters
        - recall: context-based memory recall
        - delete: remove a memory from the index

    TODO (algorithm extension point):
        - Add reindex method for bulk index rebuild
        - Add similarity search with configurable distance metrics
        - Add hybrid search combining multiple retrieval strategies
        - Add retrieval result caching

    Example implementations:
    - VectorRetrievalPlugin: Using embeddings + ANN search
    - BM25RetrievalPlugin: Full-text search
    - HybridRetrievalPlugin: Combining vector + keyword search
    - GraphRetrievalPlugin: Knowledge graph-based retrieval
    """

    @abstractmethod
    def index(self, memory: Memory) -> dict[str, Any]:
        """Index a memory for retrieval.

        Args:
            memory: The memory to index.

        Returns:
            Dict with 'status' on success.
        """
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        agent_id: str,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search memories by query.

        Args:
            query: Search query string.
            agent_id: Agent identifier for scoping.
            limit: Maximum number of results.
            filters: Optional filters (tags, date range, etc.)

        Returns:
            List of search results sorted by relevance.
        """
        ...

    @abstractmethod
    def recall(
        self,
        context: dict[str, Any],
        agent_id: str,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Recall memories based on context.

        Args:
            context: Context information for recall.
            agent_id: Agent identifier for scoping.
            limit: Maximum number of results.

        Returns:
            List of search results sorted by relevance.
        """
        ...

    @abstractmethod
    def delete(self, memory_id: str) -> dict[str, Any]:
        """Remove a memory from the index.

        Args:
            memory_id: The memory identifier to remove.

        Returns:
            Dict with 'status' on success.
        """
        ...


# ---------------------------------------------------------------------------
# State Evolution Plugin Interface
# ---------------------------------------------------------------------------

class StateEvolutionPhase(str, Enum):
    """Phases of state evolution."""

    ACCUMULATED = "accumulated"  # Experience data continuously written
    ASSOCIATED = "associated"  # Cross-task experiences establish associations
    DECAYED = "decayed"  # Long-unused experiences decrease in priority


@dataclass
class StateEvolutionRule:
    """Rule for state evolution transitions."""

    from_phase: StateEvolutionPhase
    to_phase: StateEvolutionPhase
    condition: str  # Human-readable condition description
    trigger_fn: Optional[Any] = None  # Optional callable for programmatic trigger


class StateEvolutionPlugin(ABC):
    """Abstract interface for state evolution management.

    Implement this interface to provide custom state evolution rules.
    External packages can implement domain-specific evolution strategies.

    IMPLEMENTED:
        - 3 abstract methods defining the evolution contract
        - get_evolution_rules: return list of transition rules
        - should_evolve: check if state should transition to next phase
        - evolve: perform the state transition

    TODO (algorithm extension point):
        - Add rollback support for failed evolutions
        - Add evolution history tracking
        - Add conditional evolution based on state content analysis
        - Add batch evolution for related states

    Example implementations:
    - FrequencyBasedEvolutionPlugin: Based on access frequency
    - RelevanceBasedEvolutionPlugin: Based on usage relevance
    - GraphBasedEvolutionPlugin: Using knowledge graph relationships
    """

    @abstractmethod
    def get_evolution_rules(self) -> list[StateEvolutionRule]:
        """Get the list of evolution rules.

        Returns:
            List of state evolution rules.
        """
        ...

    @abstractmethod
    def should_evolve(
        self,
        state_id: str,
        current_phase: StateEvolutionPhase,
        context: dict[str, Any],
    ) -> bool:
        """Check if a state should evolve to the next phase.

        Args:
            state_id: The state identifier.
            current_phase: Current evolution phase.
            context: Additional context for decision.

        Returns:
            True if state should evolve.
        """
        ...

    @abstractmethod
    def evolve(
        self,
        state_id: str,
        from_phase: StateEvolutionPhase,
        to_phase: StateEvolutionPhase,
    ) -> dict[str, Any]:
        """Evolve a state to the next phase.

        Args:
            state_id: The state identifier.
            from_phase: Current phase.
            to_phase: Target phase.

        Returns:
            Dict with evolution result.
        """
        ...


# ---------------------------------------------------------------------------
# Default State Evolution Plugin
# ---------------------------------------------------------------------------

class DefaultStateEvolutionPlugin(StateEvolutionPlugin):
    """Default state evolution implementation.
    
    IMPLEMENTED:
        Provides two default rules: accumulated->associated, associated->decayed.
        should_evolve() returns False (no auto-evolution by default).
        evolve() returns status dict without side effects.
    
    TODO (algorithm extension point):
        - Implement automatic evolution based on access patterns
        - Support frequency-based evolution (frequently accessed = stay accumulated)
        - Support graph-based evolution (related states evolve together)
        - Add decay priority (unused states decay faster)
    """

    def __init__(self) -> None:
        self.rules = [
            StateEvolutionRule(
                from_phase=StateEvolutionPhase.ACCUMULATED,
                to_phase=StateEvolutionPhase.ASSOCIATED,
                condition="Multiple related experiences accumulated",
            ),
            StateEvolutionRule(
                from_phase=StateEvolutionPhase.ASSOCIATED,
                to_phase=StateEvolutionPhase.DECAYED,
                condition="No access for extended period",
            ),
        ]

    def get_evolution_rules(self) -> list[StateEvolutionRule]:
        """Get default evolution rules."""
        return self.rules

    def should_evolve(
        self,
        state_id: str,
        current_phase: StateEvolutionPhase,
        context: dict[str, Any],
    ) -> bool:
        """Default implementation: always return False (no auto-evolution)."""
        # In default implementation, evolution is manual
        # Custom plugins can implement automatic evolution
        return False

    def evolve(
        self,
        state_id: str,
        from_phase: StateEvolutionPhase,
        to_phase: StateEvolutionPhase,
    ) -> dict[str, Any]:
        """Default evolution implementation."""
        return {
            "status": "ok",
            "state_id": state_id,
            "from_phase": from_phase.value,
            "to_phase": to_phase.value,
        }


# ---------------------------------------------------------------------------
# Plugin Registry
# ---------------------------------------------------------------------------

@dataclass
class LifecyclePlugins:
    """Registry for lifecycle plugins.

    Holds references to all pluggable lifecycle components.

    IMPLEMENTED:
        - Holds memory_lifecycle, retrieval, state_evolution plugins
        - Default factories: TimeBasedLifecyclePlugin, DefaultStateEvolutionPlugin
        - 3 registration methods for each plugin type

    TODO (algorithm extension point):
        - Add plugin priority ordering
        - Add plugin health checks
        - Add dynamic plugin loading from configuration
        - Add plugin metrics and monitoring
    """

    memory_lifecycle: MemoryLifecyclePlugin = field(
        default_factory=TimeBasedLifecyclePlugin
    )
    retrieval: Optional[RetrievalPlugin] = None
    state_evolution: StateEvolutionPlugin = field(
        default_factory=DefaultStateEvolutionPlugin
    )

    def register_retrieval_plugin(self, plugin: RetrievalPlugin) -> None:
        """Register a retrieval plugin.

        Args:
            plugin: The retrieval plugin to register.
        """
        self.retrieval = plugin

    def register_memory_lifecycle_plugin(
        self, plugin: MemoryLifecyclePlugin
    ) -> None:
        """Register a memory lifecycle plugin.

        Args:
            plugin: The memory lifecycle plugin to register.
        """
        self.memory_lifecycle = plugin

    def register_state_evolution_plugin(
        self, plugin: StateEvolutionPlugin
    ) -> None:
        """Register a state evolution plugin.

        Args:
            plugin: The state evolution plugin to register.
        """
        self.state_evolution = plugin
