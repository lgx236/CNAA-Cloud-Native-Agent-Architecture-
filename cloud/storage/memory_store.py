"""In-Memory Memory Store.

Reference implementation of memory storage using in-memory dictionaries.
This is a simple implementation for testing and development.
Can be replaced with persistent storage backends.

Algorithm responsibilities:
- IMPLEMENTED: Dict-based CRUD, tag filtering, type filtering
- TODO (production): Replace with persistent storage (SQLite, PostgreSQL)
- TODO (algorithm): Implement indexing for efficient tag/type queries
"""

from typing import Any
from datetime import datetime
from cnaa.models import Memory, MemoryType, MemorySummary
from cnaa.interaction import MemoryInterface


class InMemoryMemoryStore(MemoryInterface):
    """In-memory implementation of MemoryInterface.
    
    Stores memories in a dictionary keyed by (agent_id, memory_id).
    Suitable for testing and development.

    IMPLEMENTED:
        - Dict-based CRUD: store/get/delete with O(1) lookup by composite key
        - list_memories: linear scan with optional type/tag filters — O(n)
        - tag_short_term: no-op for in-memory (all memories are local)
        - Auto-timestamp on store via Memory model __post_init__

    TODO (algorithm extension point):
        - Replace with persistent storage (SQLite, PostgreSQL)
        - Add indexing for efficient tag/type queries
        - Add content hashing for deduplication detection
        - Add pagination for large result sets
    """
    
    def __init__(self) -> None:
        """Initialize empty memory store."""
        self._memories: dict[tuple[str, str], Memory] = {}
    
    def store_memory(
        self, memory: Memory, auth_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Store a memory in the in-memory store.
        
        Args:
            memory: Memory object to store
            auth_context: Optional authentication context dict
            
        Returns:
            Dict with status and memory_id
        """
        if auth_context and memory.agent_id != auth_context.get("agent_id"):
            return {
                "status": "error",
                "message": "Agent ID mismatch with authentication",
            }
        key = (memory.agent_id, memory.memory_id)
        self._memories[key] = memory
        return {
            "status": "ok",
            "memory_id": memory.memory_id,
        }
    
    def get_memory(
        self,
        agent_id: str,
        memory_id: str,
        auth_context: dict[str, Any] | None = None,
    ) -> Memory | None:
        """Retrieve a memory by ID.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory identifier
            auth_context: Optional authentication context dict
            
        Returns:
            Memory object if found, None otherwise
        """
        if auth_context and auth_context.get("agent_id") != agent_id:
            return None
        key = (agent_id, memory_id)
        return self._memories.get(key)
    
    def list_memories(
        self,
        agent_id: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        auth_context: dict[str, Any] | None = None,
    ) -> list[MemorySummary]:
        """List memories for an agent with optional filtering.
        
        IMPLEMENTED:
            Linear scan of all memories for the agent.
            Applies type filter (exact match) and tag filter (any match).
            Returns MemorySummary (no full content).
            Time complexity: O(n) where n = memories for this agent.
        
        TODO (algorithm extension point):
            - Add index on (agent_id, type) for O(1) type filtering
            - Add inverted index on tags for efficient tag queries
            - Support pagination (limit, offset)
            - Support sorting (by timestamp, completion_score)
        
        Args:
            agent_id: Agent identifier
            memory_type: Optional filter by memory type
            tags: Optional filter by tags
            auth_context: Optional authentication context dict
            
        Returns:
            List of MemorySummary objects
        """
        if auth_context and auth_context.get("agent_id") != agent_id:
            return []
        results = []
        
        for (aid, mid), memory in self._memories.items():
            if aid != agent_id:
                continue
            
            # Filter by type
            if memory_type is not None and memory.type != memory_type:
                continue
            
            # Filter by tags
            if tags is not None:
                if not any(tag in memory.tags for tag in tags):
                    continue
            
            # Create summary
            summary = MemorySummary(
                memory_id=memory.memory_id,
                tags=memory.tags,
                completion_score=memory.completion_score,
                timestamp=memory.timestamp,
            )
            results.append(summary)
        
        return results
    
    def tag_short_term(self, agent_id: str, tags: list[str]) -> dict[str, Any]:
        """Tag short-term memories (no-op for in-memory store).
        
        This is a placeholder for implementations that need to track
        short-term memory tags separately.
        
        Args:
            agent_id: Agent identifier
            tags: Tags to apply
            
        Returns:
            Dict with status
        """
        # In-memory store doesn't distinguish short-term tags
        # This would be implemented in a more sophisticated backend
        return {"status": "ok"}
    
    def delete_memory(
        self,
        agent_id: str,
        memory_id: str,
        auth_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Delete a memory from the store.
        
        Args:
            agent_id: Agent identifier
            memory_id: Memory identifier
            auth_context: Optional authentication context dict
            
        Returns:
            Dict with status
        """
        if auth_context and auth_context.get("agent_id") != agent_id:
            return {
                "status": "error",
                "message": "Agent ID mismatch with authentication",
            }
        key = (agent_id, memory_id)
        if key in self._memories:
            del self._memories[key]
        return {"status": "ok"}
    
    def clear(self) -> None:
        """Clear all memories (for testing)."""
        self._memories.clear()
    
    def count(self) -> int:
        """Get total number of memories (for testing).
        
        Returns:
            Number of memories in store
        """
        return len(self._memories)
