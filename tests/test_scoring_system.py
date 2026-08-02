"""Tests for Memory Scoring System.

Validates scoring algorithms, composite calculations, and backend integration.
All tests use simple, deterministic scenarios for clarity and reliability.
"""

import unittest
from datetime import datetime, timedelta

from cnaa.models import Memory, MemoryType
from cnaa.scoring import MemoryScores, ScoreRanking, ScoreThresholds
from cnaa.scoring_algorithms import (
    RecencyScorer,
    CompletionScorer,
    ImportanceScorer,
    FrequencyScorer,
    RelevanceScorer,
    CompositeScorer,
)
from cloud.storage.scoring_backend import MemoryScoringBackend


class TestMemoryScores(unittest.TestCase):
    """Test MemoryScores data class."""
    
    def test_default_weights(self):
        """Test default weight distribution."""
        scores = MemoryScores(
            memory_id="test-001",
            agent_id="agent-001",
        )
        
        weights = scores.score_weights
        self.assertAlmostEqual(weights["recency"], 0.2)
        self.assertAlmostEqual(weights["completion"], 0.25)
        self.assertAlmostEqual(weights["importance"], 0.30)
        self.assertAlmostEqual(weights["frequency"], 0.15)
        self.assertAlmostEqual(weights["relevance"], 0.10)
    
    def test_composite_calculation(self):
        """Test weighted composite score calculation."""
        scores = MemoryScores(
            memory_id="test-001",
            agent_id="agent-001",
            recency_score=1.0,
            completion_score=0.8,
            importance_score=0.6,
            frequency_score=0.4,
            relevance_score=0.2,
        )
        
        # Expected: 1*0.2 + 0.8*0.25 + 0.6*0.3 + 0.4*0.15 + 0.2*0.1
        # = 0.2 + 0.2 + 0.18 + 0.06 + 0.02 = 0.66
        expected = 0.66
        
        self.assertAlmostEqual(scores.composite, expected, places=5)
        self.assertAlmostEqual(scores.composite_score, 0.0, places=5)  # Not updated yet
        
        scores.update_composite()
        self.assertAlmostEqual(scores.composite_score, expected, places=5)
    
    def test_to_dict_and_from_dict(self):
        """Test serialization/deserialization."""
        original = MemoryScores(
            memory_id="test-001",
            agent_id="agent-001",
            recency_score=0.8,
            completion_score=0.9,
            importance_score=0.7,
            frequency_score=0.5,
            relevance_score=0.3,
        )
        original.update_composite()
        
        data = original.to_dict()
        
        self.assertEqual(data["memory_id"], "test-001")
        self.assertEqual(data["scores"]["recency"], 0.8)
        self.assertAlmostEqual(data["composite"], original.composite_score, places=5)
        
        # Deserialize
        restored = MemoryScores.from_dict(data)
        self.assertEqual(restored.memory_id, "test-001")
        self.assertAlmostEqual(
            restored.recency_score, original.recency_score, places=5
        )


class TestRecencyScorer(unittest.TestCase):
    """Test recency scoring algorithm."""
    
    def test_brand_new_memory(self):
        """Brand new memories should have score 1.0."""
        scorer = RecencyScorer()
        timestamp = datetime.now()
        
        score = scorer.score(timestamp)
        self.assertAlmostEqual(score, 1.0, places=5)
    
    def test_half_life_decay(self):
        """At half-life, score should be ~0.5."""
        scorer = RecencyScorer(half_life_days=7.0)
        timestamp = datetime.now() - timedelta(days=7)
        
        score = scorer.score(timestamp)
        self.assertLess(score, 0.6)  # Should be close to 0.5
        self.assertGreater(score, 0.4)
    
    def test_old_memory(self):
        """Very old memories should approach 0."""
        scorer = RecencyScorer(half_life_days=7.0)
        timestamp = datetime.now() - timedelta(days=30)
        
        score = scorer.score(timestamp)
        self.assertLess(score, 0.1)  # Should be very small
    
    def test_none_timestamp(self):
        """None timestamp should return 0."""
        scorer = RecencyScorer()
        score = scorer.score(None)
        self.assertEqual(score, 0.0)
    
    def test_linear_score(self):
        """Test linear decay scoring."""
        scorer = RecencyScorer()
        
        # Brand new
        score = scorer.linear_score(datetime.now(), max_age_days=30)
        self.assertAlmostEqual(score, 1.0, places=5)
        
        # Half age
        score = scorer.linear_score(
            datetime.now() - timedelta(days=15), 
            max_age_days=30
        )
        self.assertAlmostEqual(score, 0.5, places=5)
        
        # Over threshold
        score = scorer.linear_score(
            datetime.now() - timedelta(days=35), 
            max_age_days=30
        )
        self.assertEqual(score, 0.0)


class TestCompletionScorer(unittest.TestCase):
    """Test completion scoring."""
    
    def test_full_completion(self):
        """Fully completed tasks should score high."""
        scorer = CompletionScorer()
        score = scorer.score(completion_score=1.0)
        self.assertAlmostEqual(score, 1.0, places=5)
    
    def test_partial_completion(self):
        """Partial completion should scale accordingly."""
        scorer = CompletionScorer()
        score = scorer.score(completion_score=0.5)
        self.assertAlmostEqual(score, 0.5, places=5)
    
    def test_with_success_keywords(self):
        """Success keywords should boost score slightly."""
        scorer = CompletionScorer()
        
        score1 = scorer.score(completion_score=0.8, tags=None)
        score2 = scorer.score(
            completion_score=0.8, 
            tags=["success", "completed"]
        )
        
        self.assertGreater(score2, score1)  # Should be boosted
        self.assertLess(score2, 1.0)  # But clamped


class TestImportanceScorer(unittest.TestCase):
    """Test importance scoring via keyword matching."""
    
    def test_high_importance_keywords(self):
        """High-priority keywords should score 1.0."""
        scorer = ImportanceScorer()
        
        score = scorer.score(tags=["critical"])
        self.assertAlmostEqual(score, 1.0, places=5)
        
        score = scorer.score(tags=["important", "urgent"])
        self.assertAlmostEqual(score, 1.0, places=5)
    
    def test_medium_importance_keywords(self):
        """Medium keywords should have intermediate scores."""
        scorer = ImportanceScorer()
        
        score = scorer.score(tags=["priority"])
        self.assertAlmostEqual(score, 0.6, places=5)
        
        score = scorer.score(tags=["note"])
        self.assertAlmostEqual(score, 0.4, places=5)
    
    def test_low_importance_keywords(self):
        """Info-level keywords should score low."""
        scorer = ImportanceScorer()
        
        score = scorer.score(tags=["info", "background"])
        self.assertAlmostEqual(score, 0.2, places=5)
    
    def test_no_keywords(self):
        """No keywords should return 0."""
        scorer = ImportanceScorer()
        score = scorer.score(tags=["normal", "regular"])
        self.assertEqual(score, 0.0)


class TestFrequencyScorer(unittest.TestCase):
    """Test access frequency scoring."""
    
    def test_no_accesses(self):
        """No accesses should return 0."""
        scorer = FrequencyScorer()
        score = scorer.score_from_count(0)
        self.assertEqual(score, 0.0)
    
    def test_few_accesses(self):
        """Few accesses should return low but non-zero score."""
        scorer = FrequencyScorer()
        score = scorer.score_from_count(5)
        self.assertGreater(score, 0.0)
        self.assertLess(score, 0.5)
    
    def test_many_accesses(self):
        """Many accesses should approach 1.0."""
        scorer = FrequencyScorer()
        score = scorer.score_from_count(100)
        self.assertGreater(score, 0.8)  # Close to max


class TestRelevanceScorer(unittest.TestCase):
    """Test context relevance scoring."""
    
    def test_exact_match(self):
        """Exact keyword matches should score high."""
        scorer = RelevanceScorer()
        
        score = scorer.score_from_keywords(
            query_terms=["python", "coding"],
            memory_content="This is about Python programming",
        )
        self.assertGreaterEqual(score, 0.5)  # Should be at least 0.5
    
    def test_no_match(self):
        """No overlapping terms should return 0."""
        scorer = RelevanceScorer()
        
        score = scorer.score_from_keywords(
            query_terms=["quantum physics"],
            memory_content="This is about cooking recipes",
        )
        self.assertEqual(score, 0.0)
    
    def test_partial_match(self):
        """Partial overlap should return intermediate score."""
        scorer = RelevanceScorer()
        
        score = scorer.score_from_keywords(
            query_terms=["python", "java", "rust"],
            memory_content="I love Python programming",
        )
        # 1/3 match
        self.assertAlmostEqual(score, 1/3, places=5)


class TestCompositeScorer(unittest.TestCase):
    """Test combined scoring with all components."""
    
    def test_simple_scenario(self):
        """Test with a simple known scenario."""
        scorer = CompositeScorer()
        
        # Create a recent, completed, important memory
        memory = Memory(
            memory_id="mem-001",
            agent_id="agent-001",
            type=MemoryType.LONG_TERM,
            content={"task": "Completed successfully"},
            tags=["important", "success"],
            completion_score=1.0,
            timestamp=datetime.now() - timedelta(hours=1),
        )
        
        scores = scorer.score_memory(memory)
        
        # Check individual scores are in range
        self.assertGreaterEqual(scores["recency"], 0.0)
        self.assertLessEqual(scores["recency"], 1.0)
        self.assertAlmostEqual(scores["completion"], 1.0, places=5)
        self.assertAlmostEqual(scores["importance"], 1.0, places=5)
        self.assertGreaterEqual(scores["frequency"], 0.0)
        self.assertLessEqual(scores["frequency"], 1.0)
        
        # Composite should reflect these values
        self.assertGreater(scores["composite"], 0.5)  # Should be high
    
    def test_weight_customization(self):
        """Test custom weight configuration."""
        custom_weights = {
            "recency": 0.1,
            "completion": 0.1,
            "importance": 0.6,  # Make importance more important
            "frequency": 0.1,
            "relevance": 0.1,
        }
        
        scorer = CompositeScorer(weights=custom_weights)
        
        # Verify weights are normalized
        total = sum(scorer.weights.values())
        self.assertAlmostEqual(total, 1.0, places=5)


class TestMemoryScoringBackend(unittest.TestCase):
    """Test the scoring backend integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = MemoryScoringBackend()
    
    def test_update_single_memory(self):
        """Test updating scores for one memory."""
        memory = Memory(
            memory_id="test-001",
            agent_id="agent-001",
            type=MemoryType.LONG_TERM,
            content={"data": "test"},
            tags=["important"],
            completion_score=0.8,
            timestamp=datetime.now() - timedelta(hours=1),
        )
        
        score = self.backend.update_scores_for_memory(memory)
        
        self.assertEqual(score.memory_id, "test-001")
        self.assertEqual(score.agent_id, "agent-001")
        self.assertGreater(score.importance_score, 0.5)
        self.assertGreater(score.composite_score, 0.0)
    
    def test_batch_update(self):
        """Test batch score updates."""
        memories = [
            Memory(
                memory_id=f"mem-{i}",
                agent_id="agent-001",
                type=MemoryType.LONG_TERM,
                content={"idx": i},
                tags=["important"] if i % 2 == 0 else [],
                completion_score=0.5 + i * 0.1,
                timestamp=datetime.now() - timedelta(hours=i),
            )
            for i in range(5)
        ]
        
        scores = self.backend.batch_update_scores(memories)
        
        self.assertEqual(len(scores), 5)
        self.assertTrue(all(s.composite_score > 0 for s in scores))
    
    def test_agent_ranking(self):
        """Test getting ranked scores for an agent."""
        # Create memories with different qualities
        for i in range(10):
            memory = Memory(
                memory_id=f"rank-test-{i}",
                agent_id="ranking-agent",
                type=MemoryType.LONG_TERM,
                content={"order": i},
                tags=["critical"] if i >= 7 else ["normal"],
                completion_score=0.3 + i * 0.1,
                timestamp=datetime.now() - timedelta(days=i % 7),
            )
            self.backend.update_scores_for_memory(memory)
        
        # Get top ranked
        ranking = self.backend.get_scores_for_agent("ranking-agent", top_n=3)
        
        self.assertEqual(len(ranking.memories), 3)
        
        # Highest scored should be first
        top_id, top_score = ranking.memories[0]
        self.assertGreater(top_score, 0.5)  # Should have good score


class TestScoringIntegration(unittest.TestCase):
    """Integration tests for complete scoring workflow."""
    
    def test_full_workflow(self):
        """Test end-to-end scoring workflow."""
        from cloud.storage.scoring_backend import integrate_with_memory_store
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        # Create store with scoring
        base_store = InMemoryMemoryStore()
        scoring_backend = MemoryScoringBackend()
        scored_store = integrate_with_memory_store(base_store, scoring_backend)
        
        # Store some memories
        memory1 = Memory(
            memory_id="good-mem",
            agent_id="workflow-agent",
            type=MemoryType.LONG_TERM,
            content={"task": "Completed perfectly"},
            tags=["critical", "success"],
            completion_score=1.0,
            timestamp=datetime.now() - timedelta(hours=2),
        )
        
        memory2 = Memory(
            memory_id="old-mem",
            agent_id="workflow-agent",
            type=MemoryType.LONG_TERM,
            content={"task": "Old and partial"},
            tags=["note"],
            completion_score=0.3,
            timestamp=datetime.now() - timedelta(days=7),
        )
        
        scored_store.store_memory(memory1)
        scored_store.store_memory(memory2)
        
        # Get scored list
        scored_list = scored_store.get_memory_scores("workflow-agent")
        
        self.assertGreaterEqual(len(scored_list), 2)
        
        # First should be the better memory
        top_mem = scored_list[0]
        self.assertIn("composite_score", top_mem)
        self.assertIn("scores", top_mem)
        
        print(f"\n✓ Top memory: {top_mem['memory_id']}")
        print(f"  Composite score: {top_mem['composite_score']:.3f}")
        print(f"  Individual scores: {top_mem['scores']}")


if __name__ == "__main__":
    print("\n🧪 Running Memory Scoring Tests...\n")
    unittest.main(verbosity=2)
