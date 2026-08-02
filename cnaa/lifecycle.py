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
    Preference,
    SearchResult,
    State,
    StateCategory,
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

    # Time window for knowledge condensation (hours)
    knowledge_condensation_window: timedelta = timedelta(hours=24)
    
    # Minimum number of memories to trigger knowledge extraction
    min_memories_for_extraction: int = 3


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


# ---------------------------------------------------------------------------
# Knowledge Condensation Plugin
# ---------------------------------------------------------------------------

class SimpleTimeBasedCondensationPlugin:
    """Simple time-based knowledge condensation plugin.
    
    This plugin implements basic time-based knowledge accumulation:
    - Collects memories within a time window
    - Extracts preferences and knowledge from tagged memories
    - Returns summary of extracted content
    
    IMPLEMENTED:
        - Time-windowed collection: gather memories within N hours
        - Tag-based filtering: only process important tags
        - Automatic preference extraction: convert memories → Preference objects
        - Knowledge accumulation: prepare state entries for update
        - Pure rule-based: keyword matching, no ML or complex algorithms
    
    Algorithm choices:
        - Simple timestamp comparison
        - Keyword list matching
        - Agent-controlled triggering
    
    Example:
        ```python
        plugin = SimpleTimeBasedCondensationPlugin()
        
        # Condense knowledge from last 24 hours
        result = plugin.condense(
            memories=all_memories,
            agent_id="agent-001",
            time_window=timedelta(hours=24),
        )
        
        # Preferences extracted will be stored in cloud
        # States will be updated with new knowledge
        ```
    """
    
    def __init__(self) -> None:
        """Initialize the condensation plugin."""
        self._extracted_refs: dict[str, list[str]] = {}  # type → [memory_ids]
    
    def condense(
        self,
        memories: list[Memory],
        agent_id: str,
        time_window: timedelta | None = None,
        include_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Condense knowledge from a set of memories.
        
        Implementation:
            1. Filter by time window (default: 24h)
            2. Filter by relevant tags
            3. Extract preference/knowledge structures
        
        Args:
            memories: List of memories to process
            agent_id: Agent identifier
            time_window: Time window (default: 24 hours)
            include_tags: Required tags (default: preference, learning, important)
        
        Returns:
            {"status": ok, "memories_processed": n, "prefs_created": [...]}
        """
        now = datetime.now()
        cutoff_time = now - time_window if time_window else now - timedelta(hours=24)
        
        # Filter memories by time and tags
        filtered = self._filter_memories(
            memories=memories,
            cutoff_time=cutoff_time,
            include_tags=include_tags or ["preference", "learning", "important"],
        )
        
        prefs_to_create = []
        states_to_update = {}
        
        for memory in filtered:
            if self._has_high_importance(memory):
                pref = self._extract_preference(memory)
                if pref:
                    prefs_to_create.append(pref)
            
            knowledge = self._extract_knowledge(memory)
            if knowledge:
                category = StateCategory.KNOWLEDGE.value
                if category not in states_to_update:
                    states_to_update[category] = []
                states_to_update[category].append(knowledge)
        
        return {
            "status": "ok",
            "memories_processed": len(filtered),
            "prefs_created": [p.preference_id for p in prefs_to_create],
            "states_updated": list(states_to_update.keys()),
            "pref_count": len(prefs_to_create),
            "state_count": len(states_to_update),
        }
    
    def _filter_memories(
        self,
        memories: list[Memory],
        cutoff_time: datetime,
        include_tags: list[str],
    ) -> list[Memory]:
        """Filter memories by time range and tags."""
        filtered = []
        
        for memory in memories:
            # Check timestamp
            if memory.timestamp is None:
                continue
            if memory.timestamp < cutoff_time:
                continue
            
            # Check tags
            if not any(tag in memory.tags for tag in include_tags):
                continue
            
            filtered.append(memory)
        
        return filtered
    
    def _has_high_importance(self, memory: Memory) -> bool:
        """Check if memory has high importance indicators."""
        content_str = str(memory.content).lower()
        importance_keywords = [
            "important", "critical", "essential", "key point", "must remember",
            "high priority", "priority", "preference", "like", "dislike",
            "prefer", "favorite", "habit", "custom"
        ]
        
        return any(keyword in content_str for keyword in importance_keywords)
    
    def _extract_preference(self, memory: Memory) -> Preference | None:
        """Extract a preference from a memory."""
        if "preference" not in memory.tags:
            return None
        
        content = memory.content
        if isinstance(content, dict):
            # Check for explicit preference structure
            pref_keys = ["preference", "pref"]
            for key in pref_keys:
                if key in content and isinstance(content[key], dict):
                    value = content[key]
                    return Preference(
                        agent_id=memory.agent_id,
                        preference_id=f"pref-{memory.memory_id}",
                        key=str(list(value.keys())[0])[:50] if value else "unknown",
                        value=value,
                        importance=0.8,
                        source_memory_ids=[memory.memory_id],
                    )
            
            # Check for like/prefer keywords
            for key, value in content.items():
                key_lower = str(key).lower()
                if any(term in key_lower for term in ["like", "prefer", "favorite", "habit"]):
                    return Preference(
                        agent_id=memory.agent_id,
                        preference_id=f"pref-{memory.memory_id}",
                        key=key[:50],
                        value=value if isinstance(value, dict) else {"value": value},
                        importance=0.9,
                        source_memory_ids=[memory.memory_id],
                    )
        
        return None
    
    def _extract_knowledge(self, memory: Memory) -> dict[str, Any] | None:
        """Extract knowledge from a memory."""
        if "learning" not in memory.tags and "knowledge" not in memory.tags:
            return None
        
        content = memory.content
        if not content or (isinstance(content, dict) and len(content) == 0):
            return None
        
        return {
            "source_memory": memory.memory_id,
            "timestamp": memory.timestamp.isoformat() if memory.timestamp else None,
            "content_summary": str(content)[:500] if content else "",
            "tags": memory.tags,
        }
    
    def get_condensed_type(self, condensation_type: str) -> list[str]:
        """Get references of what has been condensed by type.
        
        Args:
            condensation_type: One of "preference", "knowledge", "all"
        
        Returns:
            List of memory IDs that have been processed
        """
        if condensation_type == "all":
            return list(self._extracted_refs.keys())
        
        # For now, return all as they may contain this type
        return list(self._extracted_refs.keys())
