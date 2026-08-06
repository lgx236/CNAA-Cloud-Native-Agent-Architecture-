"""Memory Selection Utility with Scoring.

Provides convenient methods for selecting memories based on scores.
Usage scenarios:
- Retrieve top-N scored memories for an agent
- Filter memories by score thresholds
- Find best matching memory for a given context
"""

from typing import Any, Optional
from datetime import datetime

from cnaa.interaction import MemoryInterface
from cnaa.models import Memory, MemorySummary
from cloud.storage.scoring_backend import MemoryScoringBackend


class ScoredMemorySelector:
    """Utility class for selecting memories using scoring."""
    
    def __init__(self, memory_store: MemoryInterface):
        """Initialize selector with memory store.
        
        Args:
            memory_store: The memory store to query (should support scoring).
        """
        self.store = memory_store
        self.backend = MemoryScoringBackend()
    
    def get_top_n(
        self,
        agent_id: str,
        n: int,
        access_counts: dict[str, int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[tuple[Memory, float]]:
        """Get top N highest-scored memories for an agent.
        
        Algorithm:
        1. Fetch all memories for the agent
        2. Calculate composite scores for each
        3. Sort by composite score descending
        4. Return top N with full memory objects
        
        Args:
            agent_id: The agent identifier.
            n: Number of memories to return.
            access_counts: Optional hit counts per memory.
            context: Optional context for relevance scoring.
        
        Returns:
            List of (memory, score) tuples sorted by score descending.
            Example: [(Memory(...), 0.85), (Memory(...), 0.72), ...]
        """
        # Get all memories for this agent
        all_memories = self._fetch_all_memories(agent_id)
        
        if not all_memories:
            return []
        
        # Score and sort
        scored = self.backend.batch_update_scores(
            all_memories,
            access_counts=access_counts,
            context=context,
        )
        
        # Create list of (memory, score) tuples
        scored_list = []
        for s in scored:
            mem = next(
                (m for m in all_memories if m.memory_id == s.memory_id),
                None
            )
            if mem is not None:
                scored_list.append((mem, s.composite_score))
        
        # Sort by score descending
        scored_list.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        return scored_list[:n]
    
    def find_best_match(
        self,
        agent_id: str,
        query_context: dict[str, Any],
        threshold: float = 0.3,
    ) -> Optional[tuple[Memory, float]]:
        """Find the best matching memory for a given context.
        
        Algorithm:
        1. Extract keywords from query context
        2. Score all memories with relevance to context
        3. Return best match if above threshold
        
        Args:
            agent_id: The agent identifier.
            query_context: Context dict with 'keywords' or 'content'.
            threshold: Minimum composite score required.
        
        Returns:
            Best matching (memory, score) or None if below threshold.
        """
        # Get top candidates (fetch more than needed)
        candidates = self.get_top_n(
            agent_id,
            n=10,
            context=query_context,
        )
        
        if not candidates:
            return None
        
        # Check if best match meets threshold
        best_mem, best_score = candidates[0]
        
        if best_score < threshold:
            print(f"⚠️ No memory above threshold {threshold:.2f}")
            return None
        
        return (best_mem, best_score)
    
    def filter_by_threshold(
        self,
        agent_id: str,
        min_composite: float = 0.5,
        access_counts: dict[str, int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[tuple[Memory, float]]:
        """Filter memories by minimum composite score.
        
        Args:
            agent_id: The agent identifier.
            min_composite: Minimum composite score required.
            access_counts: Optional access counts.
            context: Optional context for relevance scoring.
        
        Returns:
            List of (memory, score) tuples above threshold.
        """
        # Get all scored memories
        all_memories = self._fetch_all_memories(agent_id)
        
        if not all_memories:
            return []
        
        # Score them
        scored = self.backend.batch_update_scores(
            all_memories,
            access_counts=access_counts,
            context=context,
        )
        
        # Filter by threshold
        filtered = []
        for s in scored:
            if s.composite_score >= min_composite:
                mem = next(
                    (m for m in all_memories if m.memory_id == s.memory_id),
                    None
                )
                if mem is not None:
                    filtered.append((mem, s.composite_score))
        
        # Sort descending
        filtered.sort(key=lambda x: x[1], reverse=True)
        return filtered
    
    def get_important_memories(
        self,
        agent_id: str,
        min_importance: float = 0.6,
        top_n: int = 5,
    ) -> list[tuple[Memory, float]]:
        """Get high-importance memories (by importance score only).
        
        Useful when you want to prioritize critical information
        over recency or frequency.
        
        Args:
            agent_id: The agent identifier.
            min_importance: Minimum importance score.
            top_n: Maximum number to return.
        
        Returns:
            List of (memory, importance_score) tuples.
        """
        all_memories = self._fetch_all_memories(agent_id)
        
        if not all_memories:
            return []
        
        # Score without context (importance doesn't need context)
        scored = self.backend.batch_update_scores(all_memories)
        
        # Filter by importance
        important = [
            (next(m for m in all_memories if m.memory_id == s.memory_id),
             s.importance_score)
            for s in scored
            if s.importance_score >= min_importance
        ]
        
        # Sort by importance descending
        important.sort(key=lambda x: x[1], reverse=True)
        return important[:top_n]
    
    def _fetch_all_memories(self, agent_id: str) -> list[Memory]:
        """Fetch all memories for an agent (internal helper)."""
        # Use list_memories to get summaries, then fetch full details
        summaries = self.store.list_memories(agent_id=agent_id)
        
        memories = []
        for summary in summaries:
            mem = self.store.get_memory(agent_id, summary.memory_id)
            if mem is not None:
                # Ensure content is dict-typed for scoring compatibility
                if isinstance(mem.content, str):
                    # Convert string content to dict format
                    mem_dict = {
                        "text": mem.content,
                        "id": mem.memory_id,
                        "tags": mem.tags or [],
                        "completion": mem.completion_score or 0.0
                    }
                    mem = Memory(
                        memory_id=mem.memory_id,
                        agent_id=mem.agent_id,
                        type=mem.type,
                        content=mem_dict,
                        tags=mem.tags,
                        completion_score=mem.completion_score,
                        timestamp=mem.timestamp,
                        metadata=mem.metadata,
                    )
                memories.append(mem)
        
        return memories


def create_scored_selector(memory_store: MemoryInterface) -> ScoredMemorySelector:
    """Factory function to create a ScoredMemorySelector.
    
    Args:
        memory_store: The memory store implementation.
    
    Returns:
        A configured ScoredMemorySelector instance.
    """
    return ScoredMemorySelector(memory_store)


# ---------------------------------------------------------------------------
# Usage Examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from cloud.storage.memory_store import InMemoryMemoryStore
    from cnaa.models import Memory, MemoryType
    from datetime import datetime, timedelta
    
    # Setup test data
    store = InMemoryMemoryStore()
    selector = create_scored_selector(store)
    
    # Create some sample memories
    memories = [
        Memory(
            memory_id=f"test-{i}",
            agent_id="demo-agent",
            type=MemoryType.LONG_TERM,
            content={"task": f"Task {i}"},
            tags=["important"] if i % 3 == 0 else [],
            completion_score=0.5 + (i % 3) * 0.2,
            timestamp=datetime.now() - timedelta(days=i % 7),
        )
        for i in range(5)
    ]
    
    for mem in memories:
        store.store_memory(mem)
    
    # Example 1: Get top 2 scored memories
    print("\n📊 Top 2 Scored Memories:")
    top_results = selector.get_top_n("demo-agent", n=2)
    for mem, score in top_results:
        print(f"  - {mem.memory_id}: score={score:.3f}")
    
    # Example 2: Find best match for context
    print("\n🔍 Best Match for Context:")
    best = selector.find_best_match(
        "demo-agent",
        query_context={"keywords": ["important", "task"]},
        threshold=0.4
    )
    if best:
        mem, score = best
        print(f"  Found: {mem.memory_id} (score={score:.3f})")
    else:
        print("  No relevant memory found")
    
    # Example 3: Get important memories only
    print("\n⭐ High Importance Memories:")
    important = selector.get_important_memories("demo-agent", min_importance=0.8)
    for mem, imp_score in important:
        print(f"  - {mem.memory_id}: importance={imp_score:.3f}")
    
    print("\n✅ All examples completed!")
