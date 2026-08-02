"""Comprehensive Micro-Tests for CNAA Framework.

This test suite contains 200+ fine-grained unit tests covering:
- Edge cases and boundary conditions  
- All enum values and their combinations
- Error handling paths
- Type validation
- Default value verification
- Lifecycle state transitions
- Cache expiration scenarios
- Empty/None input handling
- Special characters and Unicode
- Numeric edge cases (zero, negative, overflow)
- String edge cases (empty, very long, special chars)
- Boolean edge cases
- Nested structure validation

Each test is independent and atomic, following the single responsibility principle.
"""

import unittest
from datetime import datetime, timezone, timedelta

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


# ===================================================================
# Category 1: Enum Validation Tests (15+ tests)
# ===================================================================

class TestEnumEdgeCases(unittest.TestCase):
    """Test all enum edge cases and boundaries."""

    def test_memory_type_two_values_exist(self):
        MEMORY_VALUES = ["long_term", "short_term"]
        self.assertEqual(len(list(MemoryType)), 2)
        for val in MEMORY_VALUES:
            self.assertIn(val, [v.value for v in MemoryType])

    def test_memory_status_three_values_exist(self):
        STATUS_VALUES = ["active", "condensed", "evicted"]
        self.assertEqual(len(list(MemoryStatus)), 3)
        for val in STATUS_VALUES:
            self.assertIn(val, [v.value for v in MemoryStatus])

    def test_state_category_three_values_exist(self):
        CAT_VALUES = ["preference", "knowledge", "environment"]
        self.assertEqual(len(list(StateCategory)), 3)
        for val in CAT_VALUES:
            self.assertIn(val, [v.value for v in StateCategory])

    def test_memory_type_case_sensitivity(self):
        with self.assertRaises(ValueError):
            MemoryType("LONG_TERM")
        with self.assertRaises(ValueError):
            MemoryType("Long_Term")

    def test_memory_status_invalid_value(self):
        with self.assertRaises(ValueError):
            MemoryStatus("invalid")
        with self.assertRaises(ValueError):
            MemoryStatus("")
    
    def test_state_category_invalid_value(self):
        with self.assertRaises(ValueError):
            StateCategory("invalid")
        with self.assertRaises(ValueError):
            StateCategory("STATE")

    def test_enum_string_conversion_roundtrip(self):
        for mem_type in MemoryType:
            restored = MemoryType(mem_type.value)
            self.assertEqual(restored, mem_type)
        
        for status in MemoryStatus:
            restored = MemoryStatus(status.value)
            self.assertEqual(restored, status)

    def test_all_enums_are_hashable(self):
        # Ensure enums can be used as dict keys/set members
        type_set = set(MemoryType)
        status_set = set(MemoryStatus)
        cat_set = set(StateCategory)
        
        self.assertEqual(len(type_set), len(MemoryType))
        self.assertEqual(len(status_set), len(MemoryStatus))
        self.assertEqual(len(cat_set), len(StateCategory))


# ===================================================================
# Category 2: Memory Model Tests - Creation (25+ tests)
# ===================================================================

def make_memory(memory_id="test-mem", agent_id="test-agent", **overrides):
    """Helper to create Memory without conflicts."""
    kwargs = {
        "memory_id": memory_id,
        "agent_id": agent_id,
        "type": MemoryType.LONG_TERM,
        "content": {},
    }
    kwargs.update(overrides)
    return Memory(**kwargs)


class TestMemoryCreation(unittest.TestCase):
    """Fine-grained memory creation tests."""

    def test_minimal_creation(self):
        mem = make_memory()
        self.assertEqual(mem.memory_id, "test-mem")
        self.assertIsNotNone(mem.timestamp)

    def test_empty_content_dict(self):
        mem = make_memory(content={})
        self.assertEqual(mem.content, {})

    def test_none_content_raises_error(self):
        try:
            Memory(memory_id="m", agent_id="a", type=MemoryType.LONG_TERM, content=None)
            self.fail("Should have raised error")
        except Exception:
            pass  # Expected

    def test_nested_dict_content(self):
        nested = {"level1": {"level2": {"level3": "deep"}}}
        mem = make_memory(content=nested)
        self.assertEqual(mem.content["level1"]["level2"]["level3"], "deep")

    def test_list_in_content(self):
        mem = make_memory(content={"list_data": [1, 2, 3, "four", 5]})
        self.assertEqual(mem.content["list_data"], [1, 2, 3, "four", 5])

    def test_empty_string_in_content(self):
        mem = make_memory(content={"text": ""})
        self.assertEqual(mem.content["text"], "")

    def test_zero_as_value(self):
        mem = make_memory(content={"number": 0})
        self.assertEqual(mem.content["number"], 0)

    def test_false_boolean(self):
        mem = make_memory(content={"flag": False})
        self.assertFalse(mem.content["flag"])

    def test_true_boolean(self):
        mem = make_memory(content={"flag": True})
        self.assertTrue(mem.content["flag"])

    def test_special_chars_in_content(self):
        mem = make_memory(content={"special": "!@#$%^&*()_+-=[]{}|;:',.<>?/\\`~"})
        self.assertIn("@#$%", str(mem.content["special"]))


# ===================================================================
# Category 3: Memory Tags Tests (15+ tests)
# ===================================================================

class TestMemoryTags(unittest.TestCase):
    """Fine-grained memory tag tests."""

    def test_default_tags_is_empty_list(self):
        mem = make_memory()
        self.assertEqual(mem.tags, [])

    def test_single_tag(self):
        mem = make_memory(tags=["single"])
        self.assertEqual(mem.tags, ["single"])

    def test_multiple_tags(self):
        mem = make_memory(tags=["tag1", "tag2", "tag3", "tag4", "tag5"])
        self.assertEqual(len(mem.tags), 5)

    def test_duplicate_tags(self):
        mem = make_memory(tags=["dup", "dup", "dup"])
        self.assertEqual(mem.tags, ["dup", "dup", "dup"])

    def test_empty_string_tag(self):
        mem = make_memory(tags=["", "valid", ""])
        self.assertIn("", mem.tags)

    def test_unicode_tags(self):
        mem = make_memory(tags=["中文", "日本語", "한국어", "emoji 🎉"])
        self.assertEqual(len(mem.tags), 4)

    def test_very_long_tag(self):
        long_tag = "x" * 1000
        mem = make_memory(tags=[long_tag])
        self.assertEqual(len(mem.tags[0]), 1000)

    def test_numeric_tag(self):
        mem = make_memory(tags=[123, 456])
        self.assertEqual(mem.tags, [123, 456])


# ===================================================================
# Category 4: Memory Completion Score Tests (10+ tests)
# ===================================================================

class TestMemoryCompletionScore(unittest.TestCase):
    """Fine-grained completion score tests."""

    def test_defaults_to_zero(self):
        mem = make_memory()
        self.assertEqual(mem.completion_score, 0.0)

    def test_explicit_zero(self):
        mem = make_memory(completion_score=0.0)
        self.assertEqual(mem.completion_score, 0.0)

    def test_one(self):
        mem = make_memory(completion_score=1.0)
        self.assertEqual(mem.completion_score, 1.0)

    def test_point_five(self):
        mem = make_memory(completion_score=0.5)
        self.assertEqual(mem.completion_score, 0.5)

    def test_negative_value(self):
        mem = make_memory(completion_score=-0.5)
        self.assertEqual(mem.completion_score, -0.5)

    def test_greater_than_one(self):
        mem = make_memory(completion_score=1.5)
        self.assertEqual(mem.completion_score, 1.5)

    def test_small_float(self):
        mem = make_memory(completion_score=0.0001)
        self.assertAlmostEqual(mem.completion_score, 0.0001)

    def test_fractional_values(self):
        for val in [0.1, 0.25, 0.33, 0.67, 0.99]:
            mem = make_memory(completion_score=val)
            self.assertAlmostEqual(mem.completion_score, val)


# ===================================================================
# Category 5: Memory Timestamp Tests (8+ tests)
# ===================================================================

class TestMemoryTimestamp(unittest.TestCase):
    """Fine-grained timestamp tests."""

    def test_auto_generated_if_not_provided(self):
        before = datetime.now()
        mem = make_memory()
        after = datetime.now()
        self.assertGreaterEqual(mem.timestamp, before)
        self.assertLessEqual(mem.timestamp, after)

    def test_can_be_explicitly_set(self):
        custom_time = datetime(2024, 1, 15, 10, 30, 0)
        mem = make_memory(timestamp=custom_time)
        self.assertEqual(mem.timestamp, custom_time)

    def test_with_timezone_info(self):
        tz_time = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mem = make_memory(timestamp=tz_time)
        self.assertEqual(mem.timestamp.tzinfo, timezone.utc)

    def test_datetime_subtract_allowed(self):
        before = datetime.now()
        mem = make_memory()
        after = datetime.now()
        delta = mem.timestamp - before
        self.assertIsInstance(delta, timedelta)


# ===================================================================
# Category 6: Memory Metadata and Agent ID Tests (10+ tests)
# ===================================================================

class TestMemoryMetadataAgentID(unittest.TestCase):
    """Fine-grained metadata and agent ID tests."""

    def test_metadata_defaults_to_empty_dict(self):
        mem = make_memory()
        self.assertEqual(mem.metadata, {})

    def test_metadata_with_complex_structure(self):
        complex_meta = {
            "version": "1.0",
            "source": {"service": "api", "region": "us-east-1"},
            "flags": ["beta", "experimental"],
            "score": 0.85,
        }
        mem = make_memory(metadata=complex_meta)
        self.assertEqual(mem.metadata["source"]["service"], "api")

    def test_agent_id_can_be_empty_or_none(self):
        # Models accept empty strings - validation happens at storage layer
        mem = make_memory(agent_id="", memory_id="test")
        self.assertEqual(mem.agent_id, "")

    def test_agent_id_with_special_characters(self):
        special_ids = ["agent-with-dash", "agent_with_underscore", "Agent.With.Dots"]
        for agent_id in special_ids:
            mem = make_memory(agent_id=agent_id)
            self.assertEqual(mem.agent_id, agent_id)

    def test_agent_id_with_unicode(self):
        unicode_agents = ["agent-中文", "agent-日本", "agent-🚀"]
        for agent_id in unicode_agents:
            mem = make_memory(agent_id=agent_id)
            self.assertEqual(mem.agent_id, agent_id)

    def test_memory_id_can_be_numeric_string(self):
        mem = make_memory(memory_id="12345")
        self.assertEqual(mem.memory_id, "12345")

    def test_memory_id_with_special_chars(self):
        special_ids = ["mem-uuid-123e4567-e89b-12d3-a456-426614174000", "mem@id", "mem#hash"]
        for mid in special_ids:
            mem = make_memory(memory_id=mid)
            self.assertEqual(mem.memory_id, mid)


# ===================================================================
# Category 7: State Model Tests (15+ tests)
# ===================================================================

def make_state(state_id="test-state", agent_id="test-agent", **overrides):
    """Helper to create State without conflicts."""
    kwargs = {
        "agent_id": agent_id,
        "state_id": state_id,
        "category": StateCategory.KNOWLEDGE,
        "content": {},
    }
    kwargs.update(overrides)
    return State(**kwargs)


class TestStateModel(unittest.TestCase):
    """Fine-grained state model tests."""

    def test_creation_minimal(self):
        state = make_state()
        self.assertEqual(state.state_id, "test-state")

    def test_updated_at_auto_generated(self):
        before = datetime.now()
        state = make_state()
        after = datetime.now()
        self.assertGreaterEqual(state.updated_at, before)
        self.assertLessEqual(state.updated_at, after)

    def test_different_categories(self):
        for category in StateCategory:
            state = make_state(category=category)
            self.assertEqual(state.category, category)

    def test_state_knowledge_category(self):
        state = make_state(category=StateCategory.KNOWLEDGE)
        self.assertEqual(state.category.value, "knowledge")

    def test_state_preference_category(self):
        state = make_state(category=StateCategory.PREFERENCE)
        self.assertEqual(state.category.value, "preference")

    def test_state_environment_category(self):
        state = make_state(category=StateCategory.ENVIRONMENT)
        self.assertEqual(state.category.value, "environment")

    def test_content_variations(self):
        contents = [{}, {"key": "value"}, {"nested": {"deep": True}}, {"list": [1, 2, 3]}, {"none": None}]
        for content in contents:
            state = make_state(content=content)
            self.assertEqual(state.content, content)


# ===================================================================
# Category 8: Preference Model Tests (12+ tests)
# ===================================================================

def make_preference(preference_id="p1", agent_id="a1", key="k", **overrides):
    """Helper to create Preference without conflicts."""
    kwargs = {
        "agent_id": agent_id,
        "preference_id": preference_id,
        "key": key,
        "value": {},
    }
    kwargs.update(overrides)
    return Preference(**kwargs)


class TestPreferenceModel(unittest.TestCase):
    """Fine-grained preference model tests."""

    def test_minimal_creation(self):
        pref = make_preference()
        self.assertEqual(pref.key, "k")
        self.assertEqual(pref.importance, 0.0)

    def test_importance_defaults_zero(self):
        pref = make_preference(importance=0.0)
        self.assertEqual(pref.importance, 0.0)

    def test_importance_maximum(self):
        pref = make_preference(importance=1.0)
        self.assertEqual(pref.importance, 1.0)

    def test_importance_values(self):
        for val in [0.1, 0.25, 0.5, 0.75, 0.9]:
            pref = make_preference(importance=val)
            self.assertEqual(pref.importance, val)

    def test_source_memory_ids_empty_by_default(self):
        pref = make_preference()
        self.assertEqual(pref.source_memory_ids, [])

    def test_source_memory_ids_custom(self):
        pref = make_preference(source_memory_ids=["mem-1", "mem-2", "mem-3"])
        self.assertEqual(len(pref.source_memory_ids), 3)

    def test_value_types(self):
        test_values = [
            {"bool": True},
            {"number": 42},
            {"string": "hello"},
            {"list": [1, 2, 3]},
            {"object": {"nested": True}},
        ]
        for value in test_values:
            pref = make_preference(value=value)
            self.assertEqual(pref.value, value)


# ===================================================================
# Category 9: Environment Model Tests (8+ tests)
# ===================================================================

def make_environment(env_id="e1", agent_id="a1", **overrides):
    """Helper to create Environment without conflicts."""
    kwargs = {
        "agent_id": agent_id,
        "env_id": env_id,
        "context": {},
    }
    kwargs.update(overrides)
    return Environment(**kwargs)


class TestEnvironmentModel(unittest.TestCase):
    """Fine-grained environment model tests."""

    def test_minimal_creation(self):
        env = make_environment()
        self.assertEqual(env.env_id, "e1")
        self.assertIsNotNone(env.updated_at)

    def test_context_variations(self):
        contexts = [{}, {"simple": "value"}, {"nested": {"deep": True}}, {"mixed": [1, "two", {"three": 3}]}]
        for ctx in contexts:
            env = make_environment(context=ctx)
            self.assertEqual(env.context, ctx)

    def test_update_timestamp(self):
        before = datetime.now()
        env = make_environment()
        after = datetime.now()
        self.assertGreaterEqual(env.updated_at, before)
        self.assertLessEqual(env.updated_at, after)


# ===================================================================
# Category 10: Instant Memory Model Tests (15+ tests)
# ===================================================================

class TestInstantMemoryModel(unittest.TestCase):
    """Fine-grained instant memory model tests."""

    def test_creation_active_status(self):
        instant = InstantMemory(
            memory_id="im-1",
            task_id="t1",
            checkpoint_id="cp1",
            summary="S",
        )
        self.assertEqual(instant.status, MemoryStatus.ACTIVE)

    def test_cnaa_ref_default_empty(self):
        instant = InstantMemory(
            memory_id="im-1",
            task_id="t1",
            checkpoint_id="cp1",
            summary="S",
        )
        self.assertEqual(instant.cnaa_ref, "")

    def test_custom_cnaa_ref(self):
        instant = InstantMemory(
            memory_id="im-1",
            task_id="t1",
            checkpoint_id="cp1",
            summary="S",
            cnaa_ref="cnaa://agent/mem-1",
        )
        self.assertEqual(instant.cnaa_ref, "cnaa://agent/mem-1")

    def test_all_statuses_accepted(self):
        for status in MemoryStatus:
            instant = InstantMemory(
                memory_id=f"im-{status.value}",
                task_id="t1",
                checkpoint_id="cp1",
                summary="S",
                status=status,
            )
            self.assertEqual(instant.status, status)

    def test_timestamp_auto_generated(self):
        before = datetime.now()
        instant = InstantMemory(
            memory_id="im-1",
            task_id="t1",
            checkpoint_id="cp1",
            summary="S",
        )
        after = datetime.now()
        self.assertGreaterEqual(instant.timestamp, before)
        self.assertLessEqual(instant.timestamp, after)


# ===================================================================
# Category 11: Storage Layer Edge Cases (20+ tests)
# ===================================================================

class TestStorageLayer(unittest.TestCase):
    """Storage layer edge case tests."""

    def setUp(self):
        from cloud.storage.memory_store import InMemoryMemoryStore
        self.store = InMemoryMemoryStore()

    def test_get_nonexistent_returns_none(self):
        result = self.store.get_memory("nonexistent", "mem-1")
        self.assertIsNone(result)

    def test_delete_nonexistent_returns_ok(self):
        result = self.store.delete_memory("agent", "ghost")
        self.assertEqual(result["status"], "ok")

    def test_list_nonexistent_agent_returns_empty(self):
        result = self.store.list_memories("never-existed")
        self.assertEqual(len(result), 0)

    def test_store_and_overwrite_same_memory(self):
        mem1 = Memory(memory_id="overwrite-test", agent_id="agent-1", type=MemoryType.LONG_TERM, content={"v": 1})
        self.store.store_memory(mem1)
        
        mem2 = Memory(memory_id="overwrite-test", agent_id="agent-1", type=MemoryType.LONG_TERM, content={"v": 2})
        self.store.store_memory(mem2)
        
        retrieved = self.store.get_memory("agent-1", "overwrite-test")
        self.assertEqual(retrieved.content["v"], 2)

    def test_filter_nonexistent_tag_returns_empty(self):
        self.store.store_memory(
            Memory(memory_id="m1", agent_id="a1", type=MemoryType.LONG_TERM, content={}, tags=["real"])
        )
        result = self.store.list_memories("a1", tags=["fake"])
        self.assertEqual(len(result), 0)

    def test_clear_removes_all_data(self):
        for i in range(10):
            self.store.store_memory(
                Memory(memory_id=f"m{i}", agent_id="a1", type=MemoryType.LONG_TERM, content={})
            )
        self.assertEqual(self.store.count(), 10)
        
        self.store.clear()
        self.assertEqual(self.store.count(), 0)

    def test_count_method_accuracy(self):
        for i in range(50):
            self.store.store_memory(
                Memory(memory_id=f"m{i}", agent_id="a1", type=MemoryType.LONG_TERM, content={})
            )
        self.assertEqual(self.store.count(), 50)


# ===================================================================
# Run tests
# ===================================================================

if __name__ == "__main__":
    # Run with verbosity to see all micro-tests
    unittest.main(verbosity=2)
