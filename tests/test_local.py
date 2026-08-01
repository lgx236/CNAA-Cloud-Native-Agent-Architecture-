"""Tests for local modules - InstantMemoryManager and StateCache."""

import unittest
from datetime import datetime, timedelta

from cnaa.models import (
    Environment,
    MemoryStatus,
    Preference,
    State,
    StateCategory,
)
from local.memory.instant_memory import InstantMemoryManager
from local.state.state_cache import StateCache


class TestInstantMemoryManager(unittest.TestCase):
    """Test InstantMemoryManager implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = InstantMemoryManager(agent_id="test-agent")

    def test_create_instant_memory(self):
        """IMPLEMENTED: Verify instant memory can be created."""
        instant = self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test summary",
            memory_id="mem-001",
        )
        self.assertEqual(instant.memory_id, "mem-001")
        self.assertEqual(instant.status, MemoryStatus.ACTIVE)
        self.assertEqual(instant.cnaa_ref, "cnaa://test-agent/mem-001")

    def test_get_memory(self):
        """IMPLEMENTED: Verify instant memory can be retrieved."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        retrieved = self.manager.get_memory("mem-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.memory_id, "mem-001")

    def test_get_memory_not_found(self):
        """IMPLEMENTED: Verify None returned for non-existent memory."""
        result = self.manager.get_memory("non-existent")
        self.assertIsNone(result)

    def test_get_active_memories(self):
        """IMPLEMENTED: Verify only ACTIVE memories are returned."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test 1",
            memory_id="mem-001",
        )
        self.manager.create_instant_memory(
            task_id="task-002",
            checkpoint_id="cp-002",
            summary="Test 2",
            memory_id="mem-002",
        )
        # Condense one
        self.manager.condense_memory("mem-001")

        active = self.manager.get_active_memories()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].memory_id, "mem-002")

    def test_condense_memory(self):
        """IMPLEMENTED: Verify memory status transitions to CONDENSED."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        result = self.manager.condense_memory("mem-001")
        self.assertIsNotNone(result)
        self.assertEqual(result.status, MemoryStatus.CONDENSED)

    def test_condense_already_condensed(self):
        """IMPLEMENTED: Verify condensing non-ACTIVE memory returns None."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        self.manager.condense_memory("mem-001")
        result = self.manager.condense_memory("mem-001")
        self.assertIsNone(result)

    def test_evict_memory(self):
        """IMPLEMENTED: Verify memory status transitions to EVICTED."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        self.manager.condense_memory("mem-001")
        result = self.manager.evict_memory("mem-001")
        self.assertIsNotNone(result)
        self.assertEqual(result.status, MemoryStatus.EVICTED)

    def test_evict_non_condensed(self):
        """IMPLEMENTED: Verify evicting non-CONDENSED memory returns None."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        result = self.manager.evict_memory("mem-001")
        self.assertIsNone(result)

    def test_condense_old_memories(self):
        """IMPLEMENTED: Verify old memories are condensed."""
        # Create memory with old timestamp
        instant = self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        # Manually set old timestamp
        instant.timestamp = datetime.now() - timedelta(hours=2)

        condensed = self.manager.condense_old_memories(threshold_hours=1)
        self.assertEqual(condensed, 1)
        self.assertEqual(instant.status, MemoryStatus.CONDENSED)

    def test_evict_old_memories(self):
        """IMPLEMENTED: Verify old condensed memories are evicted."""
        instant = self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        # Manually set old timestamp and condense
        instant.timestamp = datetime.now() - timedelta(days=8)
        instant.status = MemoryStatus.CONDENSED

        evicted = self.manager.evict_old_memories(threshold_days=7)
        self.assertEqual(evicted, 1)
        self.assertEqual(instant.status, MemoryStatus.EVICTED)

    def test_remove_evicted_memories(self):
        """IMPLEMENTED: Verify evicted memories are removed from storage."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        self.manager.condense_memory("mem-001")
        self.manager.evict_memory("mem-001")

        removed = self.manager.remove_evicted_memories()
        self.assertEqual(removed, 1)
        self.assertIsNone(self.manager.get_memory("mem-001"))

    def test_count(self):
        """IMPLEMENTED: Verify count returns correct number."""
        self.assertEqual(self.manager.count(), 0)
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        self.assertEqual(self.manager.count(), 1)

    def test_count_by_status(self):
        """IMPLEMENTED: Verify count_by_status returns correct counts."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test 1",
            memory_id="mem-001",
        )
        self.manager.create_instant_memory(
            task_id="task-002",
            checkpoint_id="cp-002",
            summary="Test 2",
            memory_id="mem-002",
        )
        self.manager.condense_memory("mem-001")

        counts = self.manager.count_by_status()
        self.assertEqual(counts["active"], 1)
        self.assertEqual(counts["condensed"], 1)
        self.assertEqual(counts["evicted"], 0)

    def test_clear(self):
        """IMPLEMENTED: Verify clear removes all memories."""
        self.manager.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test",
            memory_id="mem-001",
        )
        self.manager.clear()
        self.assertEqual(self.manager.count(), 0)


class TestStateCache(unittest.TestCase):
    """Test StateCache implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = StateCache(agent_id="test-agent", ttl_minutes=5)

    def test_update_and_get_states(self):
        """IMPLEMENTED: Verify states can be cached and retrieved."""
        states = [
            State(
                agent_id="test-agent",
                state_id="state-001",
                category=StateCategory.KNOWLEDGE,
                content={"key": "value"},
            )
        ]
        self.cache.update_states(states)
        retrieved = self.cache.get_states()
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].state_id, "state-001")

    def test_update_and_get_preferences(self):
        """IMPLEMENTED: Verify preferences can be cached and retrieved."""
        prefs = [
            Preference(
                agent_id="test-agent",
                preference_id="pref-001",
                key="language",
                value={"preferred": "python"},
            )
        ]
        self.cache.update_preferences(prefs)
        retrieved = self.cache.get_preferences()
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].key, "language")

    def test_update_and_get_environment(self):
        """IMPLEMENTED: Verify environment can be cached and retrieved."""
        env = Environment(
            agent_id="test-agent",
            env_id="env-001",
            context={"os": "linux"},
        )
        self.cache.update_environment(env)
        retrieved = self.cache.get_environment()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.context["os"], "linux")

    def test_is_expired_initial(self):
        """IMPLEMENTED: Verify cache is expired when never updated."""
        self.assertTrue(self.cache.is_expired())

    def test_is_expired_after_update(self):
        """IMPLEMENTED: Verify cache is not expired after update."""
        states = [
            State(
                agent_id="test-agent",
                state_id="state-001",
                category=StateCategory.KNOWLEDGE,
                content={},
            )
        ]
        self.cache.update_states(states)
        self.assertFalse(self.cache.is_expired())

    def test_is_expired_after_ttl(self):
        """IMPLEMENTED: Verify cache expires after TTL."""
        # Create cache with very short TTL
        cache = StateCache(agent_id="test-agent", ttl_minutes=0.001)
        states = [
            State(
                agent_id="test-agent",
                state_id="state-001",
                category=StateCategory.KNOWLEDGE,
                content={},
            )
        ]
        cache.update_states(states)
        # Wait for expiration
        import time
        time.sleep(0.1)
        self.assertTrue(cache.is_expired())

    def test_get_state_by_id(self):
        """IMPLEMENTED: Verify specific state can be retrieved by ID."""
        states = [
            State(
                agent_id="test-agent",
                state_id="state-001",
                category=StateCategory.KNOWLEDGE,
                content={"key": "value1"},
            ),
            State(
                agent_id="test-agent",
                state_id="state-002",
                category=StateCategory.KNOWLEDGE,
                content={"key": "value2"},
            ),
        ]
        self.cache.update_states(states)
        retrieved = self.cache.get_state_by_id("state-002")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content["key"], "value2")

    def test_get_states_by_category(self):
        """IMPLEMENTED: Verify states can be filtered by category."""
        states = [
            State(
                agent_id="test-agent",
                state_id="state-001",
                category=StateCategory.KNOWLEDGE,
                content={},
            ),
            State(
                agent_id="test-agent",
                state_id="state-002",
                category=StateCategory.PREFERENCE,
                content={},
            ),
        ]
        self.cache.update_states(states)
        knowledge = self.cache.get_states_by_category("knowledge")
        self.assertEqual(len(knowledge), 1)
        self.assertEqual(knowledge[0].state_id, "state-001")

    def test_clear(self):
        """IMPLEMENTED: Verify clear removes all cached data."""
        states = [
            State(
                agent_id="test-agent",
                state_id="state-001",
                category=StateCategory.KNOWLEDGE,
                content={},
            )
        ]
        self.cache.update_states(states)
        self.cache.clear()
        self.assertEqual(len(self.cache.get_states()), 0)
        self.assertTrue(self.cache.is_expired())

    def test_count(self):
        """IMPLEMENTED: Verify count returns correct numbers."""
        states = [
            State(
                agent_id="test-agent",
                state_id="state-001",
                category=StateCategory.KNOWLEDGE,
                content={},
            )
        ]
        prefs = [
            Preference(
                agent_id="test-agent",
                preference_id="pref-001",
                key="language",
                value={},
            )
        ]
        self.cache.update_states(states)
        self.cache.update_preferences(prefs)
        
        counts = self.cache.count()
        self.assertEqual(counts["states"], 1)
        self.assertEqual(counts["preferences"], 1)
        self.assertEqual(counts["environment"], 0)


if __name__ == "__main__":
    unittest.main()
