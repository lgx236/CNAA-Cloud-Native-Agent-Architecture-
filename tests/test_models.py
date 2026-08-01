"""Tests for cnaa.models - Core data model specification."""

import unittest
from datetime import datetime

from cnaa.models import (
    Environment,
    InstantMemory,
    Memory,
    MemoryStatus,
    MemorySummary,
    MemoryType,
    Preference,
    SearchResult,
    State,
    StateCategory,
    TaskCheckpoint,
)


class TestMemoryType(unittest.TestCase):
    """Test MemoryType enumeration."""

    def test_values(self):
        """IMPLEMENTED: Verify enum values match expected strings."""
        self.assertEqual(MemoryType.LONG_TERM.value, "long_term")
        self.assertEqual(MemoryType.SHORT_TERM.value, "short_term")

    def test_from_string(self):
        """IMPLEMENTED: Verify enum can be created from string."""
        self.assertEqual(MemoryType("long_term"), MemoryType.LONG_TERM)
        self.assertEqual(MemoryType("short_term"), MemoryType.SHORT_TERM)


class TestMemoryStatus(unittest.TestCase):
    """Test MemoryStatus enumeration."""

    def test_values(self):
        """IMPLEMENTED: Verify enum values match expected strings."""
        self.assertEqual(MemoryStatus.ACTIVE.value, "active")
        self.assertEqual(MemoryStatus.CONDENSED.value, "condensed")
        self.assertEqual(MemoryStatus.EVICTED.value, "evicted")


class TestStateCategory(unittest.TestCase):
    """Test StateCategory enumeration."""

    def test_values(self):
        """IMPLEMENTED: Verify enum values match expected strings."""
        self.assertEqual(StateCategory.PREFERENCE.value, "preference")
        self.assertEqual(StateCategory.KNOWLEDGE.value, "knowledge")
        self.assertEqual(StateCategory.ENVIRONMENT.value, "environment")


class TestMemory(unittest.TestCase):
    """Test Memory dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify Memory can be created with required fields."""
        memory = Memory(
            memory_id="mem-001",
            agent_id="agent-001",
            type=MemoryType.LONG_TERM,
            content={"task": "test"},
        )
        self.assertEqual(memory.memory_id, "mem-001")
        self.assertEqual(memory.agent_id, "agent-001")
        self.assertEqual(memory.type, MemoryType.LONG_TERM)
        self.assertEqual(memory.content, {"task": "test"})

    def test_defaults(self):
        """IMPLEMENTED: Verify default values are set correctly."""
        memory = Memory(
            memory_id="mem-001",
            agent_id="agent-001",
            type=MemoryType.LONG_TERM,
            content={},
        )
        self.assertEqual(memory.tags, [])
        self.assertEqual(memory.completion_score, 0.0)
        self.assertEqual(memory.metadata, {})
        self.assertIsNotNone(memory.timestamp)

    def test_auto_timestamp(self):
        """IMPLEMENTED: Verify timestamp is auto-set if not provided."""
        before = datetime.now()
        memory = Memory(
            memory_id="mem-001",
            agent_id="agent-001",
            type=MemoryType.LONG_TERM,
            content={},
        )
        after = datetime.now()
        self.assertGreaterEqual(memory.timestamp, before)
        self.assertLessEqual(memory.timestamp, after)


class TestTaskCheckpoint(unittest.TestCase):
    """Test TaskCheckpoint dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify TaskCheckpoint can be created."""
        memory = Memory(
            memory_id="mem-001",
            agent_id="agent-001",
            type=MemoryType.LONG_TERM,
            content={"task": "test"},
        )
        checkpoint = TaskCheckpoint(
            task_id="task-001",
            checkpoint_id="cp-001",
            compressed_memory=memory,
            summary="Test summary",
            completion_score=0.8,
        )
        self.assertEqual(checkpoint.task_id, "task-001")
        self.assertEqual(checkpoint.checkpoint_id, "cp-001")
        self.assertEqual(checkpoint.summary, "Test summary")
        self.assertEqual(checkpoint.completion_score, 0.8)


class TestState(unittest.TestCase):
    """Test State dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify State can be created."""
        state = State(
            agent_id="agent-001",
            state_id="state-001",
            category=StateCategory.KNOWLEDGE,
            content={"key": "value"},
        )
        self.assertEqual(state.agent_id, "agent-001")
        self.assertEqual(state.category, StateCategory.KNOWLEDGE)
        self.assertIsNotNone(state.updated_at)


class TestPreference(unittest.TestCase):
    """Test Preference dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify Preference can be created."""
        pref = Preference(
            agent_id="agent-001",
            preference_id="pref-001",
            key="language",
            value={"preferred": "python"},
            importance=0.9,
        )
        self.assertEqual(pref.key, "language")
        self.assertEqual(pref.importance, 0.9)
        self.assertEqual(pref.source_memory_ids, [])


class TestEnvironment(unittest.TestCase):
    """Test Environment dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify Environment can be created."""
        env = Environment(
            agent_id="agent-001",
            env_id="env-001",
            context={"os": "linux", "version": "24.04"},
        )
        self.assertEqual(env.env_id, "env-001")
        self.assertEqual(env.context["os"], "linux")


class TestInstantMemory(unittest.TestCase):
    """Test InstantMemory dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify InstantMemory can be created."""
        instant = InstantMemory(
            memory_id="mem-001",
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test summary",
        )
        self.assertEqual(instant.status, MemoryStatus.ACTIVE)
        self.assertEqual(instant.cnaa_ref, "")
        self.assertIsNotNone(instant.timestamp)


class TestMemorySummary(unittest.TestCase):
    """Test MemorySummary dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify MemorySummary can be created."""
        summary = MemorySummary(
            memory_id="mem-001",
            tags=["test", "demo"],
            completion_score=0.5,
        )
        self.assertEqual(summary.memory_id, "mem-001")
        self.assertEqual(len(summary.tags), 2)


class TestSearchResult(unittest.TestCase):
    """Test SearchResult dataclass."""

    def test_creation(self):
        """IMPLEMENTED: Verify SearchResult can be created."""
        result = SearchResult(
            memory_id="mem-001",
            agent_id="agent-001",
            summary="Test result",
            completion_score=0.8,
            relevance_score=0.95,
        )
        self.assertEqual(result.relevance_score, 0.95)


if __name__ == "__main__":
    unittest.main()
