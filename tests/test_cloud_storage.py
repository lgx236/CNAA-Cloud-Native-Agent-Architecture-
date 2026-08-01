"""Tests for cloud storage - InMemoryMemoryStore and InMemoryStateStore."""

import unittest

from cnaa.models import (
    Environment,
    Memory,
    MemoryType,
    Preference,
    State,
    StateCategory,
)
from cloud.storage.memory_store import InMemoryMemoryStore
from cloud.storage.state_store import InMemoryStateStore


class TestInMemoryMemoryStore(unittest.TestCase):
    """Test InMemoryMemoryStore implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.store = InMemoryMemoryStore()
        self.agent_id = "test-agent"

    def test_store_memory(self):
        """IMPLEMENTED: Verify memory can be stored and retrieved."""
        memory = Memory(
            memory_id="mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={"task": "test"},
        )
        result = self.store.store_memory(memory)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory_id"], "mem-001")

    def test_get_memory(self):
        """IMPLEMENTED: Verify stored memory can be retrieved."""
        memory = Memory(
            memory_id="mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={"task": "test"},
        )
        self.store.store_memory(memory)
        retrieved = self.store.get_memory(self.agent_id, "mem-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.memory_id, "mem-001")
        self.assertEqual(retrieved.content, {"task": "test"})

    def test_get_memory_not_found(self):
        """IMPLEMENTED: Verify None returned for non-existent memory."""
        result = self.store.get_memory(self.agent_id, "non-existent")
        self.assertIsNone(result)

    def test_list_memories(self):
        """IMPLEMENTED: Verify memories can be listed for an agent."""
        for i in range(3):
            memory = Memory(
                memory_id=f"mem-{i}",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"index": i},
            )
            self.store.store_memory(memory)

        summaries = self.store.list_memories(self.agent_id)
        self.assertEqual(len(summaries), 3)

    def test_list_memories_filter_by_type(self):
        """IMPLEMENTED: Verify memories can be filtered by type."""
        long_term = Memory(
            memory_id="mem-long",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={},
        )
        short_term = Memory(
            memory_id="mem-short",
            agent_id=self.agent_id,
            type=MemoryType.SHORT_TERM,
            content={},
        )
        self.store.store_memory(long_term)
        self.store.store_memory(short_term)

        long_only = self.store.list_memories(
            self.agent_id, memory_type=MemoryType.LONG_TERM
        )
        self.assertEqual(len(long_only), 1)
        self.assertEqual(long_only[0].memory_id, "mem-long")

    def test_list_memories_filter_by_tags(self):
        """IMPLEMENTED: Verify memories can be filtered by tags."""
        mem1 = Memory(
            memory_id="mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={},
            tags=["python", "test"],
        )
        mem2 = Memory(
            memory_id="mem-002",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={},
            tags=["java", "test"],
        )
        self.store.store_memory(mem1)
        self.store.store_memory(mem2)

        python_only = self.store.list_memories(self.agent_id, tags=["python"])
        self.assertEqual(len(python_only), 1)
        self.assertEqual(python_only[0].memory_id, "mem-001")

    def test_delete_memory(self):
        """IMPLEMENTED: Verify memory can be deleted."""
        memory = Memory(
            memory_id="mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={},
        )
        self.store.store_memory(memory)
        result = self.store.delete_memory(self.agent_id, "mem-001")
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(self.store.get_memory(self.agent_id, "mem-001"))

    def test_count(self):
        """IMPLEMENTED: Verify count returns correct number."""
        self.assertEqual(self.store.count(), 0)
        memory = Memory(
            memory_id="mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={},
        )
        self.store.store_memory(memory)
        self.assertEqual(self.store.count(), 1)

    def test_clear(self):
        """IMPLEMENTED: Verify clear removes all memories."""
        memory = Memory(
            memory_id="mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={},
        )
        self.store.store_memory(memory)
        self.store.clear()
        self.assertEqual(self.store.count(), 0)


class TestInMemoryStateStore(unittest.TestCase):
    """Test InMemoryStateStore implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.store = InMemoryStateStore()
        self.agent_id = "test-agent"

    def test_update_and_get_state(self):
        """IMPLEMENTED: Verify state can be stored and retrieved."""
        state = State(
            agent_id=self.agent_id,
            state_id="state-001",
            category=StateCategory.KNOWLEDGE,
            content={"key": "value"},
        )
        result = self.store.update_state(self.agent_id, state)
        self.assertEqual(result["status"], "ok")

        states = self.store.get_state(self.agent_id)
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0].state_id, "state-001")

    def test_delete_state(self):
        """IMPLEMENTED: Verify state can be deleted."""
        state = State(
            agent_id=self.agent_id,
            state_id="state-001",
            category=StateCategory.KNOWLEDGE,
            content={},
        )
        self.store.update_state(self.agent_id, state)
        result = self.store.delete_state(self.agent_id, "state-001")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(self.store.get_state(self.agent_id)), 0)

    def test_update_and_get_preference(self):
        """IMPLEMENTED: Verify preference can be stored and retrieved."""
        pref = Preference(
            agent_id=self.agent_id,
            preference_id="pref-001",
            key="language",
            value={"preferred": "python"},
            importance=0.9,
        )
        result = self.store.update_preference(self.agent_id, pref)
        self.assertEqual(result["status"], "ok")

        prefs = self.store.get_preference(self.agent_id)
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0].key, "language")

    def test_delete_preference(self):
        """IMPLEMENTED: Verify preference can be deleted."""
        pref = Preference(
            agent_id=self.agent_id,
            preference_id="pref-001",
            key="language",
            value={},
        )
        self.store.update_preference(self.agent_id, pref)
        result = self.store.delete_preference(self.agent_id, "pref-001")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(self.store.get_preference(self.agent_id)), 0)

    def test_update_and_get_environment(self):
        """IMPLEMENTED: Verify environment can be stored and retrieved."""
        env = Environment(
            agent_id=self.agent_id,
            env_id="env-001",
            context={"os": "linux"},
        )
        result = self.store.update_environment(self.agent_id, env)
        self.assertEqual(result["status"], "ok")

        retrieved = self.store.get_environment(self.agent_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.context["os"], "linux")

    def test_get_environment_not_found(self):
        """IMPLEMENTED: Verify None returned for non-existent environment."""
        result = self.store.get_environment("non-existent")
        self.assertIsNone(result)

    def test_count_methods(self):
        """IMPLEMENTED: Verify count methods return correct numbers."""
        self.assertEqual(self.store.count_states(), 0)
        self.assertEqual(self.store.count_preferences(), 0)
        self.assertEqual(self.store.count_environments(), 0)

        state = State(
            agent_id=self.agent_id,
            state_id="state-001",
            category=StateCategory.KNOWLEDGE,
            content={},
        )
        self.store.update_state(self.agent_id, state)
        self.assertEqual(self.store.count_states(), 1)


if __name__ == "__main__":
    unittest.main()
