"""Simplified Scoring Algorithms for CNAA v0.2.

Core principles:
1. Simple and interpretable (explainable AI)
2. O(1) time complexity per memory
3. Zero external dependencies
4. Configurable via parameters

Available algorithms:
- simple_recency: Linear decay over 30 days
- composite_v1: Weighted combination of simple factors
- chroma_rerank: Placeholder for vector-based re-ranking

Usage:
    from algorithms.simple_algorithms import load_algorithm
    
    scorer = load_algorithm("simple_recency")
    score = scorer.score(memory)
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


# ============================================================================
# Base Algorithm Interface
# ============================================================================

class BaseScorer(ABC):
    """Base interface for all scoring algorithms."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize scorer with optional configuration.
        
        Args:
            config: Algorithm-specific configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    def score(self, memory: Any) -> float:
        """Calculate score for a memory.
        
        Args:
            memory: Memory object to score
            
        Returns:
            Score in range [0.0, 1.0]
        """
        pass
    
    def batch_score(self, memories: list[Any]) -> list[float]:
        """Calculate scores for multiple memories.
        
        Args:
            memories: List of memory objects
            
        Returns:
            List of scores in same order as input
        """
        return [self.score(mem) for mem in memories]


# ============================================================================
# Simple Recency Scorer (v0.2 Default)
# ============================================================================

class SimpleRecencyScorer(BaseScorer):
    """Simple linear decay recency scoring.
    
    Algorithm: Linear decay over max_age_days
    
    - At day 0: score = 1.0 (brand new)
    - At day max_age: score = 0.0
    - Linear interpolation between
    
    Configuration:
        max_age_days (float): Age after which score becomes 0
                              Default: 30.0
    
    Time Complexity: O(1)
    Space Complexity: O(1)
    """
    
    DEFAULT_MAX_AGE_DAYS = 30.0
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize simple recency scorer.
        
        Args:
            config: Configuration dict with 'max_age_days' key
        """
        super().__init__(config)
        self.max_age_days = self.config.get(
            "max_age_days", 
            self.DEFAULT_MAX_AGE_DAYS
        )
    
    def score(self, memory: Any) -> float:
        """Calculate simple recency score.
        
        Algorithm: Linear decay
        
            age_days = days_since_creation(memory)
            score = max(0, 1 - age_days / max_age_days)
        
        Args:
            memory: Memory object with timestamp field
            
        Returns:
            Score in range [0.0, 1.0]
        """
        if not hasattr(memory, 'timestamp') or memory.timestamp is None:
            return 0.0
        
        now = datetime.now()
        age_seconds = (now - memory.timestamp).total_seconds()
        age_days = age_seconds / 86400
        
        # Linear decay formula
        if age_days >= self.max_age_days:
            return 0.0
        
        return max(0.0, min(1.0, 1.0 - (age_days / self.max_age_days)))


# ============================================================================
# Composite V1 Algorithm
# ============================================================================

class CompositeV1Scorer(BaseScorer):
    """Weighted composite scorer using simple components.
    
    Components (all O(1)):
    1. Recency: Linear decay (default weight: 0.2)
    2. Completion: Use completion_score directly (weight: 0.25)
    3. Importance: Keyword matching in tags (weight: 0.3)
    4. Frequency: Access count approximation (weight: 0.15)
    5. Relevance: Simple keyword match (weight: 0.1)
    
    Configuration:
        weights (dict): Component weights (sum should be 1.0)
                        Default auto-normalizes
        
        max_age_days (float): For recency component
                              Default: 30.0
        
        importance_keywords (list): Keywords for importance
                                     Default: predefined list
    
    Example:
        config = {
            "weights": {"recency": 0.3, "completion": 0.3, ...},
            "max_age_days": 60.0,
            "importance_keywords": ["critical", "urgent"]
        }
        scorer = CompositeV1Scorer(config)
    """
    
    DEFAULT_WEIGHTS = {
        "recency": 0.2,
        "completion": 0.25,
        "importance": 0.30,
        "frequency": 0.15,
        "relevance": 0.10,
    }
    
    DEFAULT_IMPORTANCE_KEYWORDS = [
        "critical", "important", "essential", "urgent",
        "high priority", "must", "require"
    ]
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize composite scorer.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        
        # Load weights
        self.weights = config.get("weights", self.DEFAULT_WEIGHTS.copy())
        self._normalize_weights()
        
        # Load other configs
        self.max_age_days = config.get("max_age_days", 30.0)
        self.importance_keywords = config.get(
            "importance_keywords",
            self.DEFAULT_IMPORTANCE_KEYWORDS.copy()
        )
    
    def _normalize_weights(self):
        """Normalize weights to sum to 1.0."""
        total = sum(self.weights.values())
        if total > 0 and total != 1.0:
            self.weights = {k: v/total for k, v in self.weights.items()}
    
    def score(self, memory: Any) -> float:
        """Calculate composite score.
        
        Composite = Σ(component_score × weight)
        
        Args:
            memory: Memory object with relevant fields
            
        Returns:
            Composite score in range [0.0, 1.0]
        """
        scores = {}
        
        # 1. Recency score
        scores["recency"] = self._score_recency(memory)
        
        # 2. Completion score
        scores["completion"] = self._score_completion(memory)
        
        # 3. Importance score
        scores["importance"] = self._score_importance(memory)
        
        # 4. Frequency score (simplified)
        scores["frequency"] = self._score_frequency(memory)
        
        # 5. Relevance score (simplified)
        scores["relevance"] = self._score_relevance(memory)
        
        # Calculate weighted composite
        composite = sum(
            scores[dim] * self.weights.get(dim, 0.0)
            for dim in scores
        )
        
        return max(0.0, min(1.0, composite))
    
    def _score_recency(self, memory: Any) -> float:
        """Simple recency scoring."""
        scorer = SimpleRecencyScencer({
            "max_age_days": self.max_age_days
        })
        return scorer.score(memory)
    
    def _score_completion(self, memory: Any) -> float:
        """Use completion_score field directly."""
        if not hasattr(memory, 'completion_score'):
            return 0.0
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, memory.completion_score or 0.0))
    
    def _score_importance(self, memory: Any) -> float:
        """Keyword-based importance scoring."""
        if not hasattr(memory, 'tags') or not memory.tags:
            return 0.0
        
        tag_lower = [t.lower() for t in memory.tags]
        
        # Check for high-importance keywords
        for kw in self.importance_keywords:
            if any(kw.lower() in tag for tag in tag_lower):
                return 1.0  # Found important keyword
        
        # Check for medium-importance
        if any(t in tag_lower for t in ["note", "reminder", "reference"]):
            return 0.5
        
        return 0.0
    
    def _score_frequency(self, memory: Any) -> float:
        """Approximate frequency from metadata."""
        if not hasattr(memory, 'metadata'):
            return 0.0
        
        metadata = memory.metadata or {}
        access_count = metadata.get('access_count', 0)
        
        # Logarithmic scaling (diminishing returns)
        max_expected = 100.0
        if access_count <= 0:
            return 0.0
        
        return min(1.0, math.log(1 + access_count) / math.log(1 + max_expected))
    
    def _score_relevance(self, memory: Any) -> float:
        """Simple context relevance."""
        # Placeholder: always return 0
        # Can be enhanced with query context later
        return 0.0


# ============================================================================
# ChromaDB Rerank Scorer (Placeholder)
# ============================================================================

class ChromaRerankScorer(BaseScorer):
    """ChromaDB-based reranking scorer.
    
    This is a placeholder for future integration with ChromaDB.
    Will use vector similarity for re-ranking initial results.
    
    Current implementation: Falls back to simple recency scoring.
    
    To implement:
    1. Install ChromaDB: pip install chromadb
    2. Store memory embeddings in Chroma collection
    3. Query by embedding similarity
    4. Return reranked scores
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Chroma scorer.
        
        Note: Requires ChromaDB to be installed.
        Falls back to simple recency if not available.
        """
        super().__init__(config)
        
        try:
            import chromadb
            self.chroma_available = True
            self.client = chromadb.Client()
        except ImportError:
            self.chroma_available = False
            # Fall back to simple recency
            self._fallback_scorer = SimpleRecencyScorer(config)
    
    def score(self, memory: Any) -> float:
        """Score memory using Chroma or fallback.
        
        Currently uses fallback (simple recency).
        
        Args:
            memory: Memory object
            
        Returns:
            Score in range [0.0, 1.0]
        """
        if not self.chroma_available:
            return self._fallback_scorer.score(memory)
        
        # TODO: Implement ChromaDB vector search
        # This requires storing embeddings separately
        return 0.5  # Neutral score when Chroma enabled but no data
    
    def set_query_context(self, query_text: str):
        """Set query context for relevance calculation.
        
        Args:
            query_text: User query text
        """
        # TODO: Convert query to embedding and store
        pass


# ============================================================================
# Algorithm Factory
# ============================================================================

def load_algorithm(name: str, config: dict[str, Any] | None = None) -> BaseScorer:
    """Load scoring algorithm by name.
    
    Available algorithms:
    - simple_recency: Linear decay recency scoring (DEFAULT)
    - composite_v1: Weighted composite scoring
    - chroma_rerank: ChromaDB reranking (requires chromadb)
    
    Args:
        name: Algorithm name
        config: Optional configuration dictionary
        
    Returns:
        Initialized BaseScorer instance
        
    Raises:
        ValueError: If algorithm name is unknown
        
    Example:
        scorer = load_algorithm("composite_v1", {
            "weights": {"recency": 0.4, "completion": 0.6}
        })
    """
    config = config or {}
    
    if name == "simple_recency" or name == "recency":
        return SimpleRecencyScorer(config)
    
    elif name == "composite_v1" or name == "composite":
        return CompositeV1Scorer(config)
    
    elif name == "chroma_rerank" or name == "chroma":
        return ChromaRerankScorer(config)
    
    else:
        raise ValueError(
            f"Unknown algorithm: '{name}'. "
            f"Available: simple_recency, composite_v1, chroma_rerank"
        )


def list_available_algorithms() -> list[str]:
    """List all available algorithms.
    
    Returns:
        List of algorithm names
    """
    return ["simple_recency", "composite_v1", "chroma_rerank"]


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Demo usage
    print("Available algorithms:")
    for algo in list_available_algorithms():
        print(f"  - {algo}")
    
    print("\nCreating simple_recency scorer...")
    scorer = load_algorithm("simple_recency")
    print(f"✓ Created: {scorer.__class__.__name__}")
    
    print("\nCreating composite_v1 scorer...")
    scorer = load_algorithm("composite_v1")
    print(f"✓ Created: {scorer.__class__.__name__}")
