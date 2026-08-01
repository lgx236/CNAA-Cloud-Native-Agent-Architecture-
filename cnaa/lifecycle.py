"""CNAA Lifecycle Specification.

Defines lifecycle rules for memories and states.
This is part of the architecture specification — implementations
in cloud/ and local/ modules follow these rules.

Lifecycle concepts:
- Instant Memory Lifecycle: active → condensed → evicted
- Memory Condensation: Task completion → compress → store
- State Evolution: accumulated → associated → decayed
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from cnaa.models import (
    InstantMemory,
    Memory,
    MemoryStatus,
    MemoryType,
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
# Memory Lifecycle Manager
# ---------------------------------------------------------------------------

class MemoryLifecycleManager:
    """Manages memory lifecycle transitions.

    Handles the flow:
    1. Task completed → compress to instant memory + long-term memory
    2. Instant memory ages → condense to index pointer
    3. Condensed memory ages → evict from local context
    """

    def __init__(self, config: LifecycleConfig | None = None) -> None:
        self.config = config or LifecycleConfig()

    def compress_checkpoint(
        self,
        task_id: str,
        checkpoint_id: str,
        full_data: dict[str, Any],
        summary: str,
        completion_score: float,
        agent_id: str,
        memory_id: str,
    ) -> tuple[TaskCheckpoint, InstantMemory]:
        """Compress a task checkpoint into long-term + instant memory.

        This is the core compression flow:
        - Full task data → long-term memory (stored in cloud)
        - Lightweight summary → instant memory (kept locally)

        Args:
            task_id: Task identifier.
            checkpoint_id: Checkpoint identifier.
            full_data: Complete task data (for cloud storage).
            summary: Lightweight summary (for local context).
            completion_score: Task completion score.
            agent_id: Agent identifier.
            memory_id: Memory identifier for the long-term memory.

        Returns:
            Tuple of (TaskCheckpoint, InstantMemory).
        """
        # Create long-term memory with full data
        long_term_memory = Memory(
            memory_id=memory_id,
            agent_id=agent_id,
            type=MemoryType.LONG_TERM,
            content=full_data,
            tags=[task_id, checkpoint_id],
            completion_score=completion_score,
        )

        # Create task checkpoint
        checkpoint = TaskCheckpoint(
            task_id=task_id,
            checkpoint_id=checkpoint_id,
            compressed_memory=long_term_memory,
            summary=summary,
            completion_score=completion_score,
        )

        # Create instant memory (local reference)
        instant = InstantMemory(
            memory_id=memory_id,
            task_id=task_id,
            checkpoint_id=checkpoint_id,
            summary=summary,
            status=MemoryStatus.ACTIVE,
            cnaa_ref=f"cnaa://{agent_id}/{memory_id}",
        )

        return checkpoint, instant

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
        """Check if a condensed memory should be evicted.

        Args:
            memory: The instant memory to check.
            now: Current time (defaults to now).

        Returns:
            True if memory should be evicted.
        """
        if memory.status != MemoryStatus.CONDENSED:
            return False

        if now is None:
            now = datetime.now()

        if memory.timestamp is None:
            return False

        age = now - memory.timestamp
        return age >= self.config.eviction_threshold

    def condense_memory(self, memory: InstantMemory) -> InstantMemory:
        """Condense an instant memory to index pointer.

        Transitions memory from ACTIVE to CONDENSED status.
        The full data remains in cloud, accessible via cnaa_ref.

        Args:
            memory: The instant memory to condense.

        Returns:
            Updated instant memory with CONDENSED status.
        """
        memory.status = MemoryStatus.CONDENSED
        return memory

    def evict_memory(self, memory: InstantMemory) -> InstantMemory:
        """Evict a condensed memory from local context.

        Transitions memory from CONDENSED to EVICTED status.
        The memory is no longer available locally.

        Args:
            memory: The instant memory to evict.

        Returns:
            Updated instant memory with EVICTED status.
        """
        memory.status = MemoryStatus.EVICTED
        return memory

    def should_promote_to_long_term(self, memory: Memory) -> bool:
        """Check if a short-term memory should be promoted to long-term.

        Based on completion score threshold.

        Args:
            memory: The memory to check.

        Returns:
            True if memory should be promoted.
        """
        if memory.type != MemoryType.SHORT_TERM:
            return False

        return memory.completion_score >= self.config.promotion_score_threshold


# ---------------------------------------------------------------------------
# State Evolution
# ---------------------------------------------------------------------------

class StateEvolutionPhase(str, Enum):
    """Phases of state evolution."""

    ACCUMULATED = "accumulated"  # Experience data continuously written
    ASSOCIATED = "associated"  # Cross-task experiences establish associations
    DECAYED = "decayed"  # Long-unused experiences decrease in priority


@dataclass
class StateEvolutionRule:
    """Rule for state evolution transitions.

    Defines when and how states evolve through phases.
    """

    from_phase: StateEvolutionPhase
    to_phase: StateEvolutionPhase
    condition: str  # Human-readable condition description


# Default evolution rules
DEFAULT_EVOLUTION_RULES = [
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
