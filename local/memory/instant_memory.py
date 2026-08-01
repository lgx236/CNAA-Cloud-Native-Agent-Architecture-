"""Instant Memory Manager.

Manages instant memories (short-term memories) on the local side.
Instant memories are lightweight summaries kept in agent's local context,
with references to full data stored in CNAA cloud.

Algorithm responsibilities:
- IMPLEMENTED: CRUD operations, status transitions, time-based filtering
- TODO (plugin): Custom condensation strategies (importance-based, usage-based)
- TODO (plugin): Custom eviction strategies (LRU, LFU, priority-based)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from cnaa.models import InstantMemory, MemoryStatus


class InstantMemoryManager:
    """Manager for instant memories on the local side.
    
    Instant memories are lightweight summaries of task checkpoints.
    They are kept in the agent's local context for quick access,
    with references (cnaa_ref) to full data in cloud.
    
    Lifecycle:
    - created: Just generated from task checkpoint
    - active: Available for use
    - condensed: Reduced to index pointer, full data in cloud
    - evicted: Removed from local context
    
    Example:
        ```python
        manager = InstantMemoryManager(agent_id="agent-001")
        
        # Create instant memory from task checkpoint
        instant = manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Completed database migration",
            memory_id="mem-001",
        )
        
        # Get active memories
        active = manager.get_active_memories()
        
        # Condense old memories
        manager.condense_old_memories(threshold_hours=1)
        ```
    """
    
    def __init__(self, agent_id: str) -> None:
        """Initialize the instant memory manager.
        
        Args:
            agent_id: Agent identifier
        """
        self.agent_id = agent_id
        self._memories: dict[str, InstantMemory] = {}
    
    def create_instant_memory(
        self,
        task_id: str,
        checkpoint_id: str,
        summary: str,
        memory_id: str,
        cnaa_ref: str = "",
    ) -> InstantMemory:
        """Create a new instant memory from a task checkpoint.
        
        IMPLEMENTED:
            Creates InstantMemory with ACTIVE status, stores in local dict.
            Auto-generates cnaa_ref if not provided.
        
        TODO (when integrating agent framework):
            - Validate memory_id uniqueness against cloud
            - Link to TaskCheckpoint for automatic compression
        
        Args:
            task_id: Task identifier
            checkpoint_id: Checkpoint identifier
            summary: Lightweight summary of the checkpoint
            memory_id: Memory identifier (should match cloud memory_id)
            cnaa_ref: Reference to cloud memory (e.g., "cnaa://agent-001/mem-001")
            
        Returns:
            Created InstantMemory object
        """
        instant = InstantMemory(
            memory_id=memory_id,
            task_id=task_id,
            checkpoint_id=checkpoint_id,
            summary=summary,
            status=MemoryStatus.ACTIVE,
            cnaa_ref=cnaa_ref or f"cnaa://{self.agent_id}/{memory_id}",
            timestamp=datetime.now(),
        )
        
        self._memories[memory_id] = instant
        return instant
    
    def get_memory(self, memory_id: str) -> InstantMemory | None:
        """Get an instant memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            InstantMemory if found, None otherwise
        """
        return self._memories.get(memory_id)
    
    def get_active_memories(self) -> list[InstantMemory]:
        """Get all active (non-condensed, non-evicted) memories.
        
        Returns:
            List of active InstantMemory objects
        """
        return [
            mem for mem in self._memories.values()
            if mem.status == MemoryStatus.ACTIVE
        ]
    
    def get_condensed_memories(self) -> list[InstantMemory]:
        """Get all condensed memories.
        
        Returns:
            List of condensed InstantMemory objects
        """
        return [
            mem for mem in self._memories.values()
            if mem.status == MemoryStatus.CONDENSED
        ]
    
    def condense_memory(self, memory_id: str) -> InstantMemory | None:
        """Condense an instant memory to index pointer.
        
        Transitions memory from ACTIVE to CONDENSED status.
        The full data remains in cloud, accessible via cnaa_ref.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Updated InstantMemory if found, None otherwise
        """
        memory = self._memories.get(memory_id)
        if memory and memory.status == MemoryStatus.ACTIVE:
            memory.status = MemoryStatus.CONDENSED
            return memory
        return None
    
    def condense_old_memories(self, threshold_hours: float = 1.0) -> int:
        """Condense memories older than threshold.
        
        IMPLEMENTED:
            Linear scan of all ACTIVE memories.
            If (now - timestamp) >= threshold_hours, transition to CONDENSED.
            Time complexity: O(n) where n = total memories.
        
        TODO (algorithm extension point):
            - Replace time-based threshold with custom scoring function
            - Support importance-weighted condensation (high importance = keep longer)
            - Support usage-frequency-based condensation (frequently accessed = keep)
            - Integrate with MemoryLifecyclePlugin for custom strategies
        
        Args:
            threshold_hours: Age threshold in hours
            
        Returns:
            Number of memories condensed
        """
        now = datetime.now()
        condensed_count = 0
        
        for memory in self._memories.values():
            if memory.status != MemoryStatus.ACTIVE:
                continue
            
            if memory.timestamp is None:
                continue
            
            age_hours = (now - memory.timestamp).total_seconds() / 3600
            if age_hours >= threshold_hours:
                memory.status = MemoryStatus.CONDENSED
                condensed_count += 1
        
        return condensed_count
    
    def evict_memory(self, memory_id: str) -> InstantMemory | None:
        """Evict a memory from local context.
        
        Transitions memory from CONDENSED to EVICTED status.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Updated InstantMemory if found, None otherwise
        """
        memory = self._memories.get(memory_id)
        if memory and memory.status == MemoryStatus.CONDENSED:
            memory.status = MemoryStatus.EVICTED
            return memory
        return None
    
    def evict_old_memories(self, threshold_days: float = 7.0) -> int:
        """Evict condensed memories older than threshold.
        
        IMPLEMENTED:
            Linear scan of all CONDENSED memories.
            If (now - timestamp) >= threshold_days, transition to EVICTED.
            Time complexity: O(n) where n = total memories.
        
        TODO (algorithm extension point):
            - Replace time-based threshold with custom eviction policy
            - Support LRU/LFU eviction strategies
            - Support priority-based eviction (low importance first)
            - Integrate with MemoryLifecyclePlugin for custom strategies
        
        Args:
            threshold_days: Age threshold in days
            
        Returns:
            Number of memories evicted
        """
        now = datetime.now()
        evicted_count = 0
        
        for memory in self._memories.values():
            if memory.status != MemoryStatus.CONDENSED:
                continue
            
            if memory.timestamp is None:
                continue
            
            age_days = (now - memory.timestamp).total_seconds() / 86400
            if age_days >= threshold_days:
                memory.status = MemoryStatus.EVICTED
                evicted_count += 1
        
        return evicted_count
    
    def remove_evicted_memories(self) -> int:
        """Remove evicted memories from local storage.
        
        Returns:
            Number of memories removed
        """
        evicted_ids = [
            mid for mid, mem in self._memories.items()
            if mem.status == MemoryStatus.EVICTED
        ]
        
        for mid in evicted_ids:
            del self._memories[mid]
        
        return len(evicted_ids)
    
    def get_all_memories(self) -> list[InstantMemory]:
        """Get all memories regardless of status.
        
        Returns:
            List of all InstantMemory objects
        """
        return list(self._memories.values())
    
    def count(self) -> int:
        """Get total number of memories.
        
        Returns:
            Number of memories
        """
        return len(self._memories)
    
    def count_by_status(self) -> dict[str, int]:
        """Get count of memories by status.
        
        Returns:
            Dict mapping status to count
        """
        counts = {
            "active": 0,
            "condensed": 0,
            "evicted": 0,
        }
        
        for memory in self._memories.values():
            counts[memory.status.value] += 1
        
        return counts
    
    def clear(self) -> None:
        """Clear all memories (for testing)."""
        self._memories.clear()
