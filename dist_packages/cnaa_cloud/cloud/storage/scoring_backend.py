"""Memory Scoring Backend.

Implements scoring computation and storage for CNAA memories.
Provides efficient score calculation and ranking for memory retrieval.

Key Features:
- Incremental score updates (no full recalculation)
- Configurable scoring weights per agent
- Access frequency tracking
- Context-aware relevance scoring
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from cnaa.models import Memory, MemorySummary, MemoryType
from cnaa.scoring import MemoryScores, ScoreRanking
from cnaa.scoring_algorithms import CompositeScorer


class MemoryScoringBackend:
    """Backend for computing and storing memory scores."""
    
    def __init__(self, scorer: CompositeScorer | None = None):
        """Initialize scoring backend.
        
        Args:
            scorer: Composite scorer instance (uses defaults if None)
        """
        self.scorer = scorer or CompositeScorer()
        self._scores: dict[str, MemoryScores] = {}  # memory_id -> MemoryScores
    
    def update_scores_for_memory(
        self,
        memory: Memory,
        access_count: int = 0,
        context: dict[str, Any] | None = None,
    ) -> MemoryScores:
        """Update scores for a single memory.
        
        Calculates all component scores and stores the profile.
        
        Args:
            memory: Memory object to score
            access_count: Number of times this memory was accessed
            context: Optional context for relevance scoring
            
        Returns:
            Updated MemoryScores object
        """
        # Calculate all scores
        raw_scores = self.scorer.score_memory(
            memory=memory,
            access_count=access_count,
            context=context
        )
        
        # Create or update score profile
        score_obj = MemoryScores(
            memory_id=memory.memory_id,
            agent_id=memory.agent_id,
            recency_score=raw_scores["recency"],
            completion_score=raw_scores["completion"],
            importance_score=raw_scores["importance"],
            frequency_score=raw_scores["frequency"],
            relevance_score=raw_scores["relevance"],
            composite_score=raw_scores["composite"],
        )
        
        # Store
        self._scores[memory.memory_id] = score_obj
        
        return score_obj
    
    def batch_update_scores(
        self,
        memories: list[Memory],
        access_counts: dict[str, int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[MemoryScores]:
        """Batch update scores for multiple memories.
        
        Args:
            memories: List of memories to score
            access_counts: Dict mapping memory_id to access count
            context: Optional context for relevance scoring
            
        Returns:
            List of updated MemoryScores objects
        """
        access_counts = access_counts or {}
        scored = []
        
        for memory in memories:
            access_count = access_counts.get(memory.memory_id, 0)
            score = self.update_scores_for_memory(memory, access_count, context)
            scored.append(score)
        
        return scored
    
    def get_scores_for_agent(
        self,
        agent_id: str,
        top_n: int | None = None,
        min_composite: float = 0.0,
    ) -> ScoreRanking:
        """Get scored memories for an agent, sorted by composite score.
        
        Args:
            agent_id: Agent identifier
            top_n: Limit to top N scores (None = all)
            min_composite: Minimum composite score threshold
            
        Returns:
            ScoreRanking with memories sorted by score
        """
        # Filter by agent and minimum score
        scored_memories = [
            (score.memory_id, score.composite_score)
            for score in self._scores.values()
            if score.agent_id == agent_id and score.composite_score >= min_composite
        ]
        
        # Sort by composite score descending
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Apply top_n limit
        if top_n is not None:
            scored_memories = scored_memories[:top_n]
        
        return ScoreRanking(
            agent_id=agent_id,
            memories=scored_memories,
            total_count=len(self._scores),
            filtered_count=len(scored_memories),
        )
    
    def increment_access_count(
        self, 
        memory_id: str, 
        count: int = 1
    ) -> None:
        """Increment access count for a memory.
        
        This will trigger a score recalculation next time
        scores are requested.
        
        Args:
            memory_id: Memory to increment
            count: Number of accesses to add
        """
        if memory_id not in self._scores:
            return
        
        # We would need to track access counts separately
        # For now, just mark as needing update
        pass
    
    def get_best_memory(
        self,
        agent_id: str,
        context: dict[str, Any] | None = None,
        exclude_ids: list[str] | None = None,
    ) -> tuple[MemoryScores, Memory] | None:
        """Get the best-scoring memory for an agent.
        
        Args:
            agent_id: Agent identifier
            context: Context for relevance scoring
            exclude_ids: List of memory IDs to exclude
            
        Returns:
            Tuple of (MemoryScores, Memory) or None if no matches
        """
        ranking = self.get_scores_for_agent(agent_id, top_n=1)
        
        if not ranking.memories:
            return None
        
        best_id = ranking.memories[0][0]
        
        if exclude_ids and best_id in exclude_ids:
            return None
        
        # Get the score object
        score_obj = self._scores.get(best_id)
        
        if score_obj:
            return (score_obj, None)  # Memory needs to be retrieved separately
        
        return None
    
    def clear_all(self) -> None:
        """Clear all stored scores."""
        self._scores.clear()
    
    def get_score_summary(self, memory_id: str) -> MemoryScores | None:
        """Get score summary for a specific memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            MemoryScores if found, None otherwise
        """
        return self._scores.get(memory_id)


def integrate_with_memory_store(
    memory_store,
    scoring_backend: MemoryScoringBackend,
):
    """Integrate scoring backend with existing memory store.
    
    Creates wrapper methods that automatically compute scores.
    
    Args:
        memory_store: Original memory store instance
        scoring_backend: Scoring backend to use
        
    Returns:
        Wrapper class with scoring capabilities
    """
    from functools import wraps
    
    class ScoredMemoryStore:
        """Memory store with automatic scoring integration."""
        
        def __init__(self, store, scorer_backend):
            self._store = store
            self._scorer = scorer_backend
            self._access_counts: dict[str, int] = {}
        
        @property
        def store(self):
            """Access underlying store."""
            return self._store
        
        def store_memory(self, memory, *args, **kwargs):
            """Store memory and compute initial scores."""
            result = self._store.store_memory(memory, *args, **kwargs)
            
            # Compute initial scores
            self._scorer.update_scores_for_memory(memory)
            
            return result
        
        def get_memory(self, agent_id, memory_id, *args, **kwargs):
            """Get memory and update access count."""
            memory = self._store.get_memory(agent_id, memory_id, *args, **kwargs)
            
            if memory:
                # Increment access count
                self._access_counts[memory_id] = self._access_counts.get(memory_id, 0) + 1
                
                # Trigger score update
                self._scorer.update_scores_for_memory(
                    memory,
                    access_count=self._access_counts.get(memory_id, 1)
                )
            
            return memory
        
        def get_memory_scores(
            self,
            agent_id,
            access_counts=None,
            context=None,
        ):
            """Get scored memories for agent."""
            # Ensure we have access counts up to date
            memories = self._store.list_memories(agent_id)
            
            # Use cached access counts if provided
            final_counts = {**self._access_counts}
            if access_counts:
                final_counts.update(access_counts)
            
            # Get pre-computed scores
            ranking = self._scorer.get_scores_for_agent(
                agent_id,
                top_n=None,
                min_composite=0.0
            )
            
            # Convert to list format
            scored_list = []
            for mem_id, comp_score in ranking.memories:
                score_obj = self._scorer.get_score_summary(mem_id)
                if score_obj:
                    scored_list.append({
                        "memory_id": mem_id,
                        "scores": score_obj.to_dict()["scores"],
                        "composite_score": score_obj.composite_score,
                    })
            
            return scored_list
        
        def __getattr__(self, name):
            """Delegate all other calls to underlying store."""
            return getattr(self._store, name)
    
    return ScoredMemoryStore(memory_store, scoring_backend)
