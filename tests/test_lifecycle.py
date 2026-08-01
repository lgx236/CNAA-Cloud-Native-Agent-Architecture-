"""Tests for cnaa.lifecycle module.

Tests cover:
- LifecycleConfig defaults and customization
- TimeBasedLifecyclePlugin: condense/evict/promote logic
- DefaultStateEvolutionPlugin: rules and evolution
- LifecyclePlugins registry: registration and defaults
- LifecycleEvent enum values
- StateEvolutionPhase enum values
"""

import unittest
from datetime import datetime, timedelta

from cnaa.lifecycle import (
    DefaultStateEvolutionPlugin,
    LifecycleConfig,
    LifecycleEvent,
    LifecyclePlugins,
    MemoryLifecyclePlugin,
    RetrievalPlugin,
    StateEvolutionPhase,
    StateEvolutionPlugin,
    TimeBasedLifecyclePlugin,
)
from cnaa.models import (
    InstantMemory,
    Memory,
    MemoryStatus,
    MemoryType,
    SearchResult,
)


class TestLifecycleEvent(unittest.TestCase):
    """Test LifecycleEvent enum values."""

    def test_event_values(self):
        self.assertEqual(LifecycleEvent.TASK_COMPLETED, "task_completed")
        self.assertEqual(LifecycleEvent.MEMORY_CONDENSED, "memory_condensed")
        self.assertEqual(LifecycleEvent.MEMORY_EVICTED, "memory_evicted")
        self.assertEqual(LifecycleEvent.MEMORY_PROMOTED, "memory_promoted")
        self.assertEqual(LifecycleEvent.STATE_EVOLVED, "state_evolved")

    def test_event_count(self):
        self.assertEqual(len(LifecycleEvent), 5)


class TestStateEvolutionPhase(unittest.TestCase):
    """Test StateEvolutionPhase enum values."""

    def test_phase_values(self):
        self.assertEqual(StateEvolutionPhase.ACCUMULATED, "accumulated")
        self.assertEqual(StateEvolutionPhase.ASSOCIATED, "associated")
        self.assertEqual(StateEvolutionPhase.DECAYED, "decayed")

    def test_phase_count(self):
        self.assertEqual(len(StateEvolutionPhase), 3)


class TestLifecycleConfig(unittest.TestCase):
    """Test LifecycleConfig dataclass."""

    def test_default_values(self):
        config = LifecycleConfig()
        self.assertEqual(config.max_active_memories, 20)
        self.assertEqual(config.condensation_threshold, timedelta(hours=1))
        self.assertEqual(config.eviction_threshold, timedelta(days=7))
        self.assertEqual(config.promotion_score_threshold, 0.5)

    def test_custom_values(self):
        config = LifecycleConfig(
            max_active_memories=50,
            condensation_threshold=timedelta(minutes=30),
            eviction_threshold=timedelta(days=14),
            promotion_score_threshold=0.8,
        )
        self.assertEqual(config.max_active_memories, 50)
        self.assertEqual(config.condensation_threshold, timedelta(minutes=30))
        self.assertEqual(config.eviction_threshold, timedelta(days=14))
        self.assertEqual(config.promotion_score_threshold, 0.8)


class TestTimeBasedLifecyclePlugin(unittest.TestCase):
    """Test TimeBasedLifecyclePlugin implementation."""

    def setUp(self):
        self.plugin = TimeBasedLifecyclePlugin()

    def _make_instant_memory(self, status=MemoryStatus.ACTIVE, age_minutes=0):
        mem = InstantMemory(
            memory_id="im-001",
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test summary",
        )
        mem.status = status
        if age_minutes > 0:
            mem.timestamp = datetime.now() - timedelta(minutes=age_minutes)
        return mem

    def _make_memory(self, memory_type=MemoryType.SHORT_TERM, score=0.0):
        return Memory(
            memory_id="mem-001",
            agent_id="test-agent",
            type=memory_type,
            content={"test": "data"},
            completion_score=score,
        )

    # --- should_condense tests ---

    def test_should_condense_active_old_memory(self):
        mem = self._make_instant_memory(status=MemoryStatus.ACTIVE, age_minutes=120)
        self.assertTrue(self.plugin.should_condense(mem))

    def test_should_not_condence_active_young_memory(self):
        mem = self._make_instant_memory(status=MemoryStatus.ACTIVE, age_minutes=10)
        self.assertFalse(self.plugin.should_condense(mem))

    def test_should_not_condense_non_active_memory(self):
        mem = self._make_instant_memory(status=MemoryStatus.CONDENSED, age_minutes=120)
        self.assertFalse(self.plugin.should_condense(mem))

    def test_should_not_condense_evicted_memory(self):
        mem = self._make_instant_memory(status=MemoryStatus.EVICTED, age_minutes=120)
        self.assertFalse(self.plugin.should_condense(mem))

    def test_should_not_condense_without_timestamp(self):
        mem = self._make_instant_memory(status=MemoryStatus.ACTIVE)
        mem.timestamp = None
        self.assertFalse(self.plugin.should_condense(mem))

    # --- should_evict tests ---

    def test_should_evict_condensed_old_memory(self):
        mem = self._make_instant_memory(status=MemoryStatus.CONDENSED, age_minutes=7 * 24 * 60 + 1)
        self.assertTrue(self.plugin.should_evict(mem))

    def test_should_not_evict_condensed_young_memory(self):
        mem = self._make_instant_memory(status=MemoryStatus.CONDENSED, age_minutes=60)
        self.assertFalse(self.plugin.should_evict(mem))

    def test_should_not_evict_active_memory(self):
        mem = self._make_instant_memory(status=MemoryStatus.ACTIVE, age_minutes=7 * 24 * 60 + 1)
        self.assertFalse(self.plugin.should_evict(mem))

    # --- condense_memory tests ---

    def test_condense_memory_changes_status(self):
        mem = self._make_instant_memory(status=MemoryStatus.ACTIVE)
        result = self.plugin.condense_memory(mem)
        self.assertEqual(result.status, MemoryStatus.CONDENSED)

    def test_condense_memory_returns_same_object(self):
        mem = self._make_instant_memory(status=MemoryStatus.ACTIVE)
        result = self.plugin.condense_memory(mem)
        self.assertIs(result, mem)

    # --- evict_memory tests ---

    def test_evict_memory_changes_status(self):
        mem = self._make_instant_memory(status=MemoryStatus.CONDENSED)
        result = self.plugin.evict_memory(mem)
        self.assertEqual(result.status, MemoryStatus.EVICTED)

    # --- should_promote_to_long_term tests ---

    def test_promote_short_term_high_score(self):
        mem = self._make_memory(memory_type=MemoryType.SHORT_TERM, score=0.8)
        self.assertTrue(self.plugin.should_promote_to_long_term(mem))

    def test_not_promote_short_term_low_score(self):
        mem = self._make_memory(memory_type=MemoryType.SHORT_TERM, score=0.3)
        self.assertFalse(self.plugin.should_promote_to_long_term(mem))

    def test_not_promote_long_term(self):
        mem = self._make_memory(memory_type=MemoryType.LONG_TERM, score=0.8)
        self.assertFalse(self.plugin.should_promote_to_long_term(mem))

    def test_promote_at_exact_threshold(self):
        mem = self._make_memory(memory_type=MemoryType.SHORT_TERM, score=0.5)
        self.assertTrue(self.plugin.should_promote_to_long_term(mem))

    # --- custom config tests ---

    def test_custom_condensation_threshold(self):
        config = LifecycleConfig(condensation_threshold=timedelta(minutes=5))
        plugin = TimeBasedLifecyclePlugin(config=config)
        mem = self._make_instant_memory(status=MemoryStatus.ACTIVE, age_minutes=10)
        self.assertTrue(plugin.should_condense(mem))

    def test_custom_promotion_threshold(self):
        config = LifecycleConfig(promotion_score_threshold=0.9)
        plugin = TimeBasedLifecyclePlugin(config=config)
        mem = self._make_memory(memory_type=MemoryType.SHORT_TERM, score=0.8)
        self.assertFalse(plugin.should_promote_to_long_term(mem))


class TestDefaultStateEvolutionPlugin(unittest.TestCase):
    """Test DefaultStateEvolutionPlugin implementation."""

    def setUp(self):
        self.plugin = DefaultStateEvolutionPlugin()

    def test_get_evolution_rules_returns_two_rules(self):
        rules = self.plugin.get_evolution_rules()
        self.assertEqual(len(rules), 2)

    def test_first_rule_accumulated_to_associated(self):
        rules = self.plugin.get_evolution_rules()
        self.assertEqual(rules[0].from_phase, StateEvolutionPhase.ACCUMULATED)
        self.assertEqual(rules[0].to_phase, StateEvolutionPhase.ASSOCIATED)

    def test_second_rule_associated_to_decayed(self):
        rules = self.plugin.get_evolution_rules()
        self.assertEqual(rules[1].from_phase, StateEvolutionPhase.ASSOCIATED)
        self.assertEqual(rules[1].to_phase, StateEvolutionPhase.DECAYED)

    def test_should_evolve_always_returns_false(self):
        self.assertFalse(self.plugin.should_evolve(
            "state-001", StateEvolutionPhase.ACCUMULATED, {}
        ))
        self.assertFalse(self.plugin.should_evolve(
            "state-002", StateEvolutionPhase.ASSOCIATED, {"key": "value"}
        ))

    def test_evolve_returns_status_dict(self):
        result = self.plugin.evolve(
            "state-001",
            StateEvolutionPhase.ACCUMULATED,
            StateEvolutionPhase.ASSOCIATED,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["state_id"], "state-001")
        self.assertEqual(result["from_phase"], "accumulated")
        self.assertEqual(result["to_phase"], "associated")


class TestLifecyclePlugins(unittest.TestCase):
    """Test LifecyclePlugins registry."""

    def test_default_memory_lifecycle_plugin(self):
        registry = LifecyclePlugins()
        self.assertIsInstance(registry.memory_lifecycle, TimeBasedLifecyclePlugin)

    def test_default_state_evolution_plugin(self):
        registry = LifecyclePlugins()
        self.assertIsInstance(registry.state_evolution, DefaultStateEvolutionPlugin)

    def test_default_retrieval_is_none(self):
        registry = LifecyclePlugins()
        self.assertIsNone(registry.retrieval)

    def test_register_retrieval_plugin(self):
        registry = LifecyclePlugins()

        class MockRetrieval(RetrievalPlugin):
            def index(self, memory): return {"status": "ok"}
            def search(self, query, agent_id, limit=5, filters=None): return []
            def recall(self, context, agent_id, limit=5): return []
            def delete(self, memory_id): return {"status": "ok"}

        mock = MockRetrieval()
        registry.register_retrieval_plugin(mock)
        self.assertIs(registry.retrieval, mock)

    def test_register_memory_lifecycle_plugin(self):
        registry = LifecyclePlugins()

        class MockLifecycle(MemoryLifecyclePlugin):
            def should_condense(self, memory, now=None): return False
            def should_evict(self, memory, now=None): return False
            def condense_memory(self, memory): return memory
            def evict_memory(self, memory): return memory
            def should_promote_to_long_term(self, memory): return False

        mock = MockLifecycle()
        registry.register_memory_lifecycle_plugin(mock)
        self.assertIs(registry.memory_lifecycle, mock)

    def test_register_state_evolution_plugin(self):
        registry = LifecyclePlugins()

        class MockEvolution(StateEvolutionPlugin):
            def get_evolution_rules(self): return []
            def should_evolve(self, state_id, current_phase, context): return False
            def evolve(self, state_id, from_phase, to_phase): return {"status": "ok"}

        mock = MockEvolution()
        registry.register_state_evolution_plugin(mock)
        self.assertIs(registry.state_evolution, mock)


if __name__ == "__main__":
    unittest.main()
