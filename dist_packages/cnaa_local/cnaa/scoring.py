"""Memory Scoring Models.

Defines data structures for memory scoring and evaluation.
All scores are normalized to [0.0, 1.0] range.

Scoring dimensions:
- Recency: How recent the memory is (0-7 days decay)
- Completion: Task completion score from agent
- Importance: User-assigned importance level
- Frequency: Access/hit count over time
- Relevance: Contextual relevance to current situation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryScores:
    """Complete scoring profile for a single memory."""
    
    memory_id: str
    agent_id: str
    
    # Core scores (always calculated)
    recency_score: float = 0.0      # How recent: newer = higher
    completion_score: float = 0.0   # Task completion: completed = higher
    importance_score: float = 0.0   # User/importance keywords: important = higher
    
    # Dynamic scores (updated over time)
    frequency_score: float = 0.0    # Access frequency: frequently used = higher
    relevance_score: float = 0.0    # Context relevance: matching context = higher
    
    # Weighted combined score
    composite_score: float = 0.0
    
    # Metadata
    last_evaluated: datetime | None = None
    evaluation_version: str = "1.0"
    score_weights: dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        # Check if score_weights is empty (either None or empty dict)
        if not self.score_weights:
            self.score_weights = self._default_weights()
    
    def _default_weights(self) -> dict[str, float]:
        """Default weights for each score component."""
        return {
            "recency": 0.2,          # 20% weight
            "completion": 0.25,      # 25% weight
            "importance": 0.30,      # 30% weight (most important!)
            "frequency": 0.15,       # 15% weight
            "relevance": 0.10,       # 10% weight
        }
    
    @property
    def composite(self) -> float:
        """Calculate weighted composite score."""
        weights = self.score_weights
        
        return (
            self.recency_score * weights.get("recency", 0.2) +
            self.completion_score * weights.get("completion", 0.25) +
            self.importance_score * weights.get("importance", 0.30) +
            self.frequency_score * weights.get("frequency", 0.15) +
            self.relevance_score * weights.get("relevance", 0.10)
        )
    
    def update_composite(self) -> None:
        """Recalculate composite score from components."""
        self.composite_score = self.composite
        self.last_evaluated = datetime.now()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "scores": {
                "recency": self.recency_score,
                "completion": self.completion_score,
                "importance": self.importance_score,
                "frequency": self.frequency_score,
                "relevance": self.relevance_score,
            },
            "composite": self.composite_score,
            "weights": self.score_weights,
            "last_evaluated": self.last_evaluated.isoformat() if self.last_evaluated else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryScores":
        """Create from dictionary."""
        scores_data = data.get("scores", {})
        
        instance = cls(
            memory_id=data["memory_id"],
            agent_id=data["agent_id"],
            recency_score=scores_data.get("recency", 0.0),
            completion_score=scores_data.get("completion", 0.0),
            importance_score=scores_data.get("importance", 0.0),
            frequency_score=scores_data.get("frequency", 0.0),
            relevance_score=scores_data.get("relevance", 0.0),
            composite_score=data.get("composite", 0.0),
            last_evaluated=datetime.fromisoformat(data["last_evaluated"]) 
                if data.get("last_evaluated") else None,
            evaluation_version=data.get("evaluation_version", "1.0"),
            score_weights=data.get("weights", {}),
        )
        instance.update_composite()
        return instance


@dataclass
class ScoreRanking:
    """Ranked list of memories by composite score."""
    
    agent_id: str
    memories: list[tuple[str, float]]  # (memory_id, score)
    query_time: datetime = field(default_factory=datetime.now)
    total_count: int = 0
    filtered_count: int = 0
    
    @property
    def top_n(self, n: int) -> list[tuple[str, float]]:
        """Get top N scored memories."""
        return self.memories[:n]
    
    @property
    def avg_score(self) -> float:
        """Average score across all ranked memories."""
        if not self.memories:
            return 0.0
        return sum(score for _, score in self.memories) / len(self.memories)


@dataclass
class ScoreThresholds:
    """Configuration for score-based filtering thresholds."""
    
    # Minimum scores for inclusion
    min_recency: float = 0.0          # No minimum by default
    min_completion: float = 0.0       # No minimum by default  
    min_importance: float = 0.0       # No minimum by default
    min_frequency: float = 0.0        # No minimum by default
    min_relevance: float = 0.0        # No minimum by default
    
    # Composite score threshold
    min_composite: float = 0.0        # No minimum by default
    
    # Maximum age in seconds (filters out very old memories)
    max_age_seconds: float = 7 * 24 * 3600  # 7 days default
    
    def should_include(
        self, 
        scores: MemoryScores,
        memory_age_seconds: float
    ) -> bool:
        """Check if memory should be included based on thresholds."""
        # Check individual score thresholds
        if (scores.recency_score < self.min_recency or
            scores.completion_score < self.min_completion or
            scores.importance_score < self.min_importance or
            scores.frequency_score < self.min_frequency or
            scores.relevance_score < self.min_relevance):
            return False
        
        # Check composite score
        if scores.composite_score < self.min_composite:
            return False
        
        # Check age limit
        if memory_age_seconds > self.max_age_seconds:
            return False
        
        return True
