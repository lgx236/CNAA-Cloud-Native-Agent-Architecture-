"""Memory Scoring Algorithms.

Implements simple, reliable scoring algorithms for memory evaluation.
All algorithms are designed to be:
- Simple and interpretable
- Fast to compute (O(1) per memory)
- Configurable via parameters
- Based on established heuristics

Scoring Dimensions:
1. Recency Score: Decay-based score that favors recent memories
2. Completion Score: Task completion status from agent
3. Importance Score: Keyword-based importance detection
4. Frequency Score: Access frequency over time window
5. Relevance Score: Context match quality (placeholder for future)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

from cnaa.models import Memory, MemoryType


class RecencyScorer:
    """Compute recency-based scores with exponential decay."""
    
    def __init__(self, half_life_days: float = 7.0):
        """Initialize scorer.
        
        Args:
            half_life_days: Days after which score drops by half.
                           Smaller value = faster decay.
        """
        self.half_life = timedelta(days=half_life_days)
        # k for exponential decay: score(t) = 2^(-t/half_life)
        self._decay_factor = math.log(2) / self.half_life.total_seconds()
    
    def score(self, timestamp: datetime | None) -> float:
        """Calculate recency score for a memory timestamp.
        
        Algorithm: Exponential decay
        - score = 2^(-(age_seconds)/half_life_seconds)
        - At age = 0: score = 1.0 (brand new)
        - At age = half_life: score = 0.5 (halfway decayed)
        - At age → ∞: score → 0
        
        Args:
            timestamp: Memory creation timestamp
            
        Returns:
            Score in range [0.0, 1.0]
        """
        if timestamp is None:
            return 0.0
        
        now = datetime.now()
        age_seconds = (now - timestamp).total_seconds()
        
        if age_seconds < 0:
            # Future timestamp? Treat as brand new
            return 1.0
        
        # Exponential decay formula
        decay = math.exp(-self._decay_factor * age_seconds)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, decay))
    
    @staticmethod
    def linear_score(timestamp: datetime | None, max_age_days: float = 30.0) -> float:
        """Simple linear decay score.
        
        Alternative algorithm: Linear decay
        - score = max(0, 1 - age/max_age)
        - Clean and predictable behavior
        
        Args:
            timestamp: Memory creation timestamp
            max_age_days: Age after which score becomes 0
            
        Returns:
            Score in range [0.0, 1.0]
        """
        if timestamp is None:
            return 0.0
        
        now = datetime.now()
        age_days = (now - timestamp).total_seconds() / 86400
        
        if age_days >= max_age_days:
            return 0.0
        
        return 1.0 - (age_days / max_age_days)


class CompletionScorer:
    """Compute completion-based scores."""
    
    def score(
        self, 
        completion_score: float | None,
        tags: list[str] | None = None,
        content: dict[str, Any] | None = None
    ) -> float:
        """Calculate completion score.
        
        Algorithm: Use provided completion_score directly,
        with adjustments based on keywords.
        
        Args:
            completion_score: Agent-provided completion score [0,1]
            tags: Optional tags for keyword detection
            content: Optional content for keyword detection
            
        Returns:
            Adjusted score in range [0.0, 1.0]
        """
        # Start with provided score
        base_score = completion_score if completion_score is not None else 0.0
        
        # Boost if success-related keywords present
        boost = 0.0
        if tags:
            success_tags = ["success", "completed", "done", "finished"]
            if any(tag in success_tags for tag in tags):
                boost = 0.1
        
        if content:
            content_str = str(content).lower()
            success_words = ["success", "completed", "finished", "done"]
            if any(word in content_str for word in success_words):
                boost = max(boost, 0.1)
        
        # Clamp result
        return max(0.0, min(1.0, base_score + boost))


class ImportanceScorer:
    """Compute importance-based scores using keyword matching."""
    
    # Priority levels for different keywords
    KEYWORD_WEIGHTS = {
        # High importance (weight 1.0)
        "critical": 1.0,
        "important": 1.0,
        "essential": 1.0,
        "urgent": 1.0,
        
        # Medium-high importance (weight 0.8)
        "high priority": 0.8,
        "must": 0.8,
        "require": 0.8,
        
        # Medium importance (weight 0.6)
        "priority": 0.6,
        "key": 0.6,
        "major": 0.6,
        
        # Low-medium importance (weight 0.4)
        "note": 0.4,
        "reminder": 0.4,
        "reference": 0.4,
        
        # Informational (weight 0.2)
        "info": 0.2,
        "background": 0.2,
    }
    
    def score(
        self,
        tags: list[str] | None = None,
        content: dict[str, Any] | None = None,
        importance_field: float | None = None
    ) -> float:
        """Calculate importance score.
        
        Algorithm: Weighted keyword matching
        - Scan tags and content for importance keywords
        - Take maximum weight found (or average of multiple matches)
        - Blend with explicit importance field if provided
        
        Args:
            tags: Memory tags
            content: Memory content dictionary
            importance_field: Explicit importance field [0,1] if exists
            
        Returns:
            Calculated importance score in range [0.0, 1.0]
        """
        keywords_found = []
        
        # Check tags
        if tags:
            for tag in tags:
                tag_lower = tag.lower()
                for keyword, weight in self.KEYWORD_WEIGHTS.items():
                    if keyword.lower() in tag_lower:
                        keywords_found.append(weight)
        
        # Check content
        if content:
            content_text = self._flatten_to_text(content)
            content_lower = content_text.lower()
            
            for keyword, weight in self.KEYWORD_WEIGHTS.items():
                if keyword.lower() in content_lower:
                    keywords_found.append(weight)
        
        # Calculate score from keywords
        if keywords_found:
            keyword_score = max(keywords_found)  # Take highest weight
        else:
            keyword_score = 0.0
        
        # Blend with explicit importance field
        if importance_field is not None:
            # Weight explicit importance more heavily
            return 0.7 * importance_field + 0.3 * keyword_score
        
        return keyword_score
    
    def _flatten_to_text(self, content: dict[str, Any]) -> str:
        """Flatten content dict to searchable text."""
        parts = []
        for key, value in content.items():
            parts.append(str(key))
            if isinstance(value, dict):
                parts.append(self._flatten_to_text(value))
            elif isinstance(value, list):
                parts.extend(str(item) for item in value)
            else:
                parts.append(str(value))
        return " ".join(parts)


class FrequencyScorer:
    """Compute access frequency-based scores."""
    
    def __init__(self, lookback_days: float = 7.0, doubling_period_hours: float = 24.0):
        """Initialize scorer.
        
        Args:
            lookback_days: Time window to count accesses
            doubling_period_hours: Hours for access rate to double score
        """
        self.lookback = timedelta(days=lookback_days)
        # For each access, multiply score by 2^(1/doubling_period)
        self._access_multiplier = 2.0 ** (1.0 / (doubling_period_hours / 24.0))
    
    def score_from_count(self, access_count: int) -> float:
        """Calculate score from raw access count.
        
        Algorithm: Logarithmic scaling
        - score = log(1 + count) / log(1 + max_lookup)
        - Diminishing returns for very high counts
        
        Args:
            access_count: Number of times memory was accessed
            
        Returns:
            Score in range [0.0, 1.0]
        """
        if access_count <= 0:
            return 0.0
        
        # Use logarithmic scale to prevent runaway scores
        # Max expected count for normalization: 100 accesses in lookback period
        max_expected = 100.0
        max_log = math.log(1.0 + max_expected)
        
        actual_log = math.log(1.0 + access_count)
        
        return min(1.0, actual_log / max_log)
    
    def score_from_rate(
        self, 
        access_count: int,
        memory_age_days: float
    ) -> float:
        """Calculate score from access rate.
        
        Args:
            access_count: Number of accesses
            memory_age_days: Age of memory in days
            
        Returns:
            Score in range [0.0, 1.0]
        """
        if memory_age_days <= 0:
            return 0.0
        
        # Accesses per day
        daily_rate = access_count / memory_age_days
        
        # Map rate to score with saturation
        # 1+ accesses/day = 1.0, less = proportional
        return min(1.0, daily_rate)


class RelevanceScorer:
    """Compute context relevance scores.
    
    Placeholder implementation - simple keyword matching.
    Can be enhanced with vector embeddings later.
    """
    
    def __init__(self):
        pass
    
    def score_from_keywords(
        self,
        query_terms: list[str],
        memory_content: str,
        memory_tags: list[str] | None = None
    ) -> float:
        """Score relevance based on keyword overlap.
        
        Algorithm: Jaccard similarity with term weighting
        - Higher weight for exact matches
        - Lower weight for partial matches
        
        Args:
            query_terms: Terms from current context/query
            memory_content: Memory content as text
            memory_tags: Optional memory tags
            
        Returns:
            Relevance score in range [0.0, 1.0]
        """
        if not query_terms:
            return 0.0
        
        # Normalize terms
        query_set = set(term.lower().strip() for term in query_terms if term.strip())
        content_text = memory_content.lower()
        
        # Count exact matches
        exact_matches = sum(1 for term in query_set if term in content_text)
        
        # Add tag matches (bonus points)
        tag_matches = 0
        if memory_tags:
            for term in query_set:
                for tag in memory_tags:
                    if term in tag.lower() or tag.lower() in term:
                        tag_matches += 1
        
        # Calculate score
        total_terms = len(query_set)
        matched_terms = exact_matches + tag_matches * 0.5  # Tags worth 0.5x
        
        return matched_terms / total_terms if total_terms > 0 else 0.0
    
    def simple_context_match(self, context: dict[str, Any], memory: Memory) -> float:
        """Simple context-to-memory relevance.
        
        Look for common keywords between context and memory.
        
        Args:
            context: Current context dict
            memory: Memory to score
            
        Returns:
            Relevance score
        """
        context_text = self._flatten_context(context)
        memory_text = self._flatten_memory(memory)
        
        context_words = set(context_text.split())
        memory_words = set(memory_text.split())
        
        # Jaccard similarity
        intersection = len(context_words & memory_words)
        union = len(context_words | memory_words)
        
        return intersection / union if union > 0 else 0.0
    
    def _flatten_context(self, context: dict[str, Any]) -> str:
        """Flatten context dict to text."""
        parts = []
        for value in context.values():
            if isinstance(value, (dict, list)):
                parts.append(str(value))
            else:
                parts.append(str(value))
        return " ".join(parts)
    
    def _flatten_memory(self, memory: Memory) -> str:
        """Flatten memory to text."""
        text_parts = [str(memory.content)]
        if memory.tags:
            text_parts.extend(memory.tags)
        return " ".join(text_parts)


class CompositeScorer:
    """Combine all individual scorers into composite score."""
    
    def __init__(
        self,
        weights: dict[str, float] | None = None,
        normalize: bool = True
    ):
        """Initialize composite scorer.
        
        Args:
            weights: Dict of component weights
            normalize: Whether to normalize weights to sum to 1.0
        """
        self.weights = weights or {
            "recency": 0.2,
            "completion": 0.25,
            "importance": 0.30,
            "frequency": 0.15,
            "relevance": 0.10,
        }
        self.normalize_weights(normalize)
        
        # Initialize individual scorers
        self.recency_scorer = RecencyScorer()
        self.completion_scorer = CompletionScorer()
        self.importance_scorer = ImportanceScorer()
        self.frequency_scorer = FrequencyScorer()
        self.relevance_scorer = RelevanceScorer()
    
    def normalize_weights(self, normalize: bool) -> None:
        """Normalize weights to sum to 1.0 if requested."""
        if not normalize:
            return
        
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def score_memory(
        self,
        memory: Memory,
        access_count: int = 0,
        query_terms: list[str] | None = None,
        context: dict[str, Any] | None = None,
        timestamp_override: datetime | None = None
    ) -> dict[str, float]:
        """Calculate full scoring profile for a memory.
        
        Args:
            memory: Memory object to score
            access_count: Number of times accessed
            query_terms: Terms for relevance calculation
            context: Full context for relevance calculation
            timestamp_override: Override for recency calculation
            
        Returns:
            Dict with all individual and composite scores
        """
        # Calculate each component
        scores = {}
        
        # Recency
        ts = timestamp_override or memory.timestamp
        scores["recency"] = self.recency_scorer.score(ts)
        
        # Completion
        scores["completion"] = self.completion_scorer.score(
            memory.completion_score,
            memory.tags,
            memory.content
        )
        
        # Importance
        scores["importance"] = self.importance_scorer.score(
            memory.tags,
            memory.content,
            memory.metadata.get("importance") if hasattr(memory, 'metadata') else None
        )
        
        # Frequency
        ages_days = self._calculate_age_days(memory.timestamp)
        scores["frequency"] = self.frequency_scorer.score_from_rate(access_count, ages_days)
        
        # Relevance
        if context:
            scores["relevance"] = self.relevance_scorer.simple_context_match(context, memory)
        elif query_terms:
            scores["relevance"] = self.relevance_scorer.score_from_keywords(
                query_terms,
                str(memory.content),
                memory.tags
            )
        else:
            scores["relevance"] = 0.0  # No context means no relevance
        
        # Calculate composite
        composite = sum(
            scores[dim] * self.weights.get(dim, 0.0)
            for dim in scores
        )
        scores["composite"] = composite
        
        return scores
    
    def _calculate_age_days(self, timestamp: datetime | None) -> float:
        """Calculate age of memory in days."""
        if timestamp is None:
            return 0.0
        now = datetime.now()
        return (now - timestamp).total_seconds() / 86400
