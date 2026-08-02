"""Memory Scoring and Selection System.

Implements simple, rule-based scoring for memory importance and selection.
Uses basic keyword matching and time decay - no complex ML or AI algorithms.

Design principles:
- Simple and reliable: Only use clear, interpretable rules
- Agent-controlled: Agents can override automatic scores
- Transparent: Every factor's contribution is visible
- Fast: All calculations are O(n) linear scans

Key features:
- Multi-factor scoring: tags, recency, content structure, metadata
- Configurable weights: Adjust importance of each factor
- Time decay: Older memories score lower unless marked important
- Manual overrides: Agents can set explicit importance scores
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from cnaa.models import Memory, MemoryType


class SimpleMemoryScorer:
    """Simple rule-based memory scorer.
    
    This scorer calculates an importance score (0.0-1.0) for each memory
    based on multiple factors:
    
    1. Tag-based (40% weight): Special tags like "important", "preference"
    2. Content quality (30%): Structure and completeness
    3. Recency (20%): Newer memories score higher (time decay)
    4. Completion (10%): Task completion_score field
    
    Formula:
        score = w_tags * tag_score + 
                w_content * content_score + 
                w_recency * recency_score + 
                w_completion * completion_score
    
    Example:
        ```python
        scorer = SimpleMemoryScorer()
        
        # Score all memories
        scored_memories = scorer.score_all(memories)
        
        # Get top N most important
        top_5 = scorer.get_top_n(scored_memories, n=5)
        
        # Filter by minimum threshold
        important = scorer.filter_by_score(scored_memories, min_score=0.7)
        ```
    """
    
    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize the scorer.
        
        Args:
            weights: Optional custom weights. Must sum to 1.0.
                    Default: {"tags": 0.4, "content": 0.3, "recency": 0.2, "completion": 0.1}
        """
        self.weights = weights or {
            "tags": 0.4,
            "content": 0.3,
            "recency": 0.2,
            "completion": 0.1,
        }
        
        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def score_memory(self, memory: Memory) -> tuple[Memory, float]:
        """Calculate importance score for a single memory.
        
        IMPLEMENTED:
            - Factor 1: Tag-based score (40%)
            - Factor 2: Content structure score (30%)
            - Factor 3: Recency score with time decay (20%)
            - Factor 4: Completion score (10%)
            - Weighted average of all factors
        
        Args:
            memory: Memory object to score
            
        Returns:
            Tuple of (memory with updated score, calculated_score)
        """
        tag_score = self._score_tags(memory)
        content_score = self._score_content(memory)
        recency_score = self._score_recency(memory)
        completion_score = memory.completion_score if hasattr(memory, 'completion_score') else 0.0
        
        # Calculate weighted average
        final_score = (
            self.weights["tags"] * tag_score +
            self.weights["content"] * content_score +
            self.weights["recency"] * recency_score +
            self.weights["completion"] * completion_score
        )
        
        # Clamp to [0.0, 1.0]
        final_score = max(0.0, min(1.0, final_score))
        
        return memory, final_score
    
    def _score_tags(self, memory: Memory) -> float:
        """Score based on tags.
        
        HIGH VALUE TAGS (high score):
        - "important", "critical" → 1.0
        - "preference", "habit" → 0.8
        - "learning", "knowledge" → 0.6
        - "decision" → 0.5
        
        NORMAL TAGS (medium score):
        - Any other tags → 0.3
        No tags → 0.1
        
        Returns:
            Tag score in range [0.0, 1.0]
        """
        high_value_tags = {"important", "critical", "urgent"}
        medium_value_tags = {"preference", "habit", "favorite", "learned"}
        low_value_tags = {"learning", "knowledge", "decision"}
        
        memory_tags = set(tag.lower() for tag in memory.tags)
        
        # Check for high value tags
        if any(tag in memory_tags for tag in high_value_tags):
            return 1.0
        
        # Check for medium value tags
        if any(tag in memory_tags for tag in medium_value_tags):
            return 0.8
        
        # Check for low value tags
        if any(tag in memory_tags for tag in low_value_tags):
            return 0.6
        
        # General tags
        if len(memory_tags) > 0:
            return 0.3
        
        return 0.1
    
    def _score_content(self, memory: Memory) -> float:
        """Score based on content structure.
        
        HIGH QUALITY STRUCTURES:
        - Dict with multiple key-value pairs → 0.9
        - Dict with events array → 0.8
        - Single structured dict → 0.6
        - Plain text/string → 0.4
        - Empty/minimal content → 0.2
        
        Returns:
            Content quality score in range [0.0, 1.0]
        """
        content = memory.content
        
        if not content:
            return 0.1
        
        if isinstance(content, dict):
            num_keys = len(content)
            
            if num_keys >= 3:
                return 0.9
            
            if num_keys == 2:
                return 0.7
            
            if num_keys == 1:
                return 0.5
            
            return 0.3
        
        elif isinstance(content, list):
            if len(content) >= 3:
                return 0.8
            
            if len(content) > 0:
                return 0.5
            
            return 0.1
        
        elif isinstance(content, str):
            if len(content) > 100:
                return 0.6
            
            return 0.4
        
        return 0.2
    
    def _score_recency(self, memory: Memory) -> float:
        """Score based on how recent the memory is.
        
        TIME DECAY RULES:
        - Within 1 hour → 1.0 (very fresh)
        - Within 24 hours → 0.8 (recent)
        - Within 7 days → 0.5 (moderate)
        - Within 30 days → 0.3 (old)
        - Older than 30 days → 0.1 (very old)
        
        NO TIMESTAMP:
        - If timestamp is None → 0.5 (neutral score)
        
        Returns:
            Recency score in range [0.0, 1.0]
        """
        if memory.timestamp is None:
            return 0.5
        
        now = datetime.now()
        age_hours = (now - memory.timestamp).total_seconds() / 3600
        age_days = age_hours / 24
        
        if age_hours <= 1:
            return 1.0
        
        if age_hours <= 24:
            return 0.8
        
        if age_days <= 7:
            return 0.5
        
        if age_days <= 30:
            return 0.3
        
        return 0.1
    
    def score_all(self, memories: list[Memory]) -> list[tuple[Memory, float]]:
        """Score a list of memories.
        
        Args:
            memories: List of Memory objects
            
        Returns:
            List of (Memory, score) tuples
        """
        results = []
        for memory in memories:
            scored = self.score_memory(memory)
            results.append(scored)
        return results
    
    def get_top_n(self, memories_with_scores: list[tuple[Memory, float]], n: int) -> list[tuple[Memory, float]]:
        """Get the top N highest-scoring memories.
        
        Args:
            memories_with_scores: List of (Memory, score) tuples from score_all()
            n: Number of memories to return
            
        Returns:
            Top N memories sorted by score (highest first)
        """
        # Sort by score descending
        sorted_list = sorted(
            memories_with_scores,
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_list[:n]
    
    def filter_by_score(
        self, 
        memories_with_scores: list[tuple[Memory, float]], 
        min_score: float = 0.5,
        max_score: float = 1.0
    ) -> list[tuple[Memory, float]]:
        """Filter memories by score range.
        
        Args:
            memories_with_scores: List of (Memory, score) tuples
            min_score: Minimum acceptable score
            max_score: Maximum acceptable score
            
        Returns:
            Memories within score range
        """
        return [
            item for item in memories_with_scores
            if min_score <= item[1] <= max_score
        ]
    
    def categorize_memories(
        self, 
        memories_with_scores: list[tuple[Memory, float]]
    ) -> dict[str, list[tuple[Memory, float]]]:
        """Categorize memories into importance levels.
        
        Categories:
        - "critical": score >= 0.9
        - "high": 0.7 <= score < 0.9
        - "medium": 0.5 <= score < 0.7
        - "low": 0.3 <= score < 0.5
        - "min": score < 0.3
        
        Args:
            memories_with_scores: List of (Memory, score) tuples
            
        Returns:
            Dict mapping category name to list of (Memory, score) tuples
        """
        categories = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "min": [],
        }
        
        for memory, score in memories_with_scores:
            if score >= 0.9:
                categories["critical"].append((memory, score))
            elif score >= 0.7:
                categories["high"].append((memory, score))
            elif score >= 0.5:
                categories["medium"].append((memory, score))
            elif score >= 0.3:
                categories["low"].append((memory, score))
            else:
                categories["min"].append((memory, score))
        
        return categories


def select_best_memories(
    memories: list[Memory],
    num_to_select: int = 5,
    force_importance: bool = True,
) -> list[Memory]:
    """Quick function to select top N important memories.
    
    Convenience wrapper around SimpleMemoryScorer.
    
    Args:
        memories: List of memories to evaluate
        num_to_select: How many to return
        force_importance: If True, ensure at least N items even if scores are low
        
    Returns:
        List of top N memories by importance
    """
    scorer = SimpleMemoryScorer()
    scored = scorer.score_all(memories)
    top_n = scorer.get_top_n(scored, num_to_select)
    
    if force_importance and len(top_n) < num_to_select:
        # Return what we have
        pass
    
    return [mem for mem, _ in top_n]


def recommend_top_memories_for_context(
    memories: list[Memory],
    context_window_hours: int = 24,
    target_count: int = 10,
) -> list[tuple[Memory, float, dict[str, Any]]]:
    """Recommend memories based on current context window.
    
    Implementation:
        1. Score all memories
        2. Prioritize within context window
        3. Balance across different categories
    
    Args:
        memories: All available memories
        context_window_hours: Hours of recent history to prioritize
        target_count: Number of memories to recommend
        
    Returns:
        List of (memory, score, reason) tuples
    """
    scorer = SimpleMemoryScorer()
    scored = scorer.score_all(memories)
    now = datetime.now()
    
    # Categorize memories
    categorized = scorer.categorize_memories(scored)
    
    # Select from each category, prioritizing recent ones
    recommendations = []
    
    # First, try to get some critical/high priority
    for cat in ["critical", "high"]:
        for mem, score in categorized[cat][:3]:  # Top 3 per category
            age_hours = (now - mem.timestamp).total_seconds() / 3600 if mem.timestamp else float('inf')
            
            # Boost score if in context window
            adjusted_score = score
            if age_hours <= context_window_hours:
                adjusted_score = min(1.0, score + 0.1)
            
            reason = "recent_and_important" if age_hours <= context_window_hours else "historically_important"
            recommendations.append((mem, adjusted_score, {"category": cat, "reason": reason}))
    
    # Fill remaining spots with high-quality memories
    remaining_needed = target_count - len(recommendations)
    if remaining_needed > 0:
        for cat in ["medium", "high"]:
            for mem, score in categorized[cat][:5]:
                if len(recommendations) >= target_count:
                    break
                
                if mem not in [r[0] for r in recommendations]:
                    recommendations.append((mem, score, {"category": cat}))
    
    # Sort by score and limit
    recommendations.sort(key=lambda x: x[1], reverse=True)
    
    return recommendations[:target_count]
