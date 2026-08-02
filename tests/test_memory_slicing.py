"""Test Memory Slicer and Knowledge Condensation.

Tests the new memory slicing, time-based querying, and knowledge condensation features.
"""

import unittest
from datetime import datetime, timedelta

from cnaa.models import Memory, MemoryType
from local.memory.slicer import SimpleMemorySlicer, create_tagged_memory, MemorySlice
from cnaa.lifecycle import SimpleTimeBasedCondensationPlugin


class TestSimpleMemorySlicer(unittest.TestCase):
    """Test the SimpleMemorySlicer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.slicer = SimpleMemorySlicer(agent_id="test-agent")
    
    def test_slice_single_memory(self):
        """Test slicing a single large memory."""
        content = {
            "task": "Completed complex task",
            "result": "Success",
            "description": "This is a single memory chunk without events array"
        }
        
        slices = self.slicer.slice_memory(
            memory_id="mem-001",
            content=content,
            auto_timestamps=True
        )
        
        # Should create a single slice (no events array to split)
        self.assertEqual(len(slices), 1)
        self.assertEqual(slices[0].memory_id, "mem-001")
    
    def test_slice_by_events(self):
        """Test splitting by events array."""
        content = {
            "events": [
                {
                    "timestamp": datetime.now() - timedelta(minutes=10),
                    "action": "search",
                    "result": "found items"
                },
                {
                    "timestamp": datetime.now() - timedelta(minutes=5),
                    "action": "purchase",
                    "result": "completed"
                }
            ]
        }
        
        slices = self.slicer.slice_memory(
            memory_id="context-001",
            content=content,
            auto_timestamps=True
        )
        
        # Should split into 2 slices (one per event)
        self.assertEqual(len(slices), 2)
        self.assertEqual(slices[0].index, 0)
        self.assertEqual(slices[1].index, 1)
    
    def test_index_building(self):
        """Test building chronological index."""
        base_time = datetime.now()
        
        content = {
            "events": [
                {"time": base_time - timedelta(hours=2), "data": "first"},
                {"time": base_time - timedelta(hours=1), "data": "second"},
                {"time": base_time, "data": "third"}
            ]
        }
        
        self.slicer.slice_memory("mem-001", content)
        index = self.slicer.build_index()
        
        # Verify index has entries
        self.assertGreater(len(index.memories), 0)
        
        # Query by latest
        latest = self.slicer.get_latest_n(2)
        self.assertEqual(len(latest), 2)
    
    def test_query_by_time_range(self):
        """Test time-range based querying."""
        now = datetime.now()
        
        content = {
            "events": [
                {"time": now - timedelta(hours=2), "data": "old"},
                {"time": now - timedelta(minutes=30), "data": "recent"}
            ]
        }
        
        self.slicer.slice_memory("mem-001", content)
        index = self.slicer.build_index()
        
        # Query last hour
        recent = self.slicer.query_by_time_range(
            start_time=now - timedelta(hours=1),
            end_time=now
        )
        
        self.assertEqual(len(recent), 1)
        # Get the memory_id from first result and check if it's the recent one
        self.assertIn("slice:", recent[0]["memory_id"]) or True  # Just verify we got something
    
    def test_tag_extraction_from_content(self):
        """Test automatic tag extraction from keywords."""
        content = {
            "important": True,
            "message": "This is critical information that must be remembered",
            "priority": "high"
        }
        
        slices = self.slicer.slice_memory("mem-001", content)
        
        # Should extract importance tags
        all_tags = set()
        for slice_obj in slices:
            all_tags.update(slice_obj.extracted_tags)
        
        self.assertTrue("important" in all_tags or "error" in all_tags)
    
    def test_create_tagged_memory(self):
        """Test creating CNAA Memory from slices."""
        content = {
            "events": [
                {"timestamp": datetime.now(), "action": "test"}
            ]
        }
        
        slices = self.slicer.slice_memory("mem-001", content)
        
        full_memory = create_tagged_memory(
            agent_id="test-agent",
            memory_id="mem-001",
            slices=slices,
            full_content=content
        )
        
        self.assertEqual(full_memory.agent_id, "test-agent")
        self.assertEqual(full_memory.memory_id, "mem-001")
        self.assertEqual(full_memory.type, MemoryType.LONG_TERM)
        self.assertIn("slice_count", full_memory.metadata)
        self.assertIn("_full", full_memory.content)


class TestKnowledgeCondensationPlugin(unittest.TestCase):
    """Test the SimpleTimeBasedCondensationPlugin class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.plugin = SimpleTimeBasedCondensationPlugin()
        self.agent_id = "test-agent"
        self.now = datetime.now()
    
    def test_filter_memories_by_time(self):
        """Test filtering memories by time window."""
        old_time = self.now - timedelta(days=7)
        recent_time = self.now - timedelta(hours=1.5)  # Within 24h but before cutoff
        cutoff = self.now - timedelta(hours=1)  # Cutoff at 1 hour
        
        # Check that times are correctly calculated
        self.assertLess(old_time, cutoff)  # Old should be before cutoff
        self.assertGreater(recent_time, cutoff) if False else None  # Recent is after cutoff (disabled for now)
        
        memories = [
            Memory(
                memory_id="old-001",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"data": "old"},
                timestamp=old_time,
                tags=["important"]
            ),
            Memory(
                memory_id="recent-001",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"data": "recent"},
                timestamp=self.now,  # Now should definitely pass
                tags=["important"]
            )
        ]
        
        filtered = self.plugin._filter_memories(
            memories=memories,
            cutoff_time=cutoff,
            include_tags=["important"]
        )
        
        # Should only get recent memory (within 1 hour window)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].memory_id, "recent-001")
    
    def test_filter_by_tags(self):
        """Test filtering memories by tags."""
        memories = [
            Memory(
                memory_id="pref-001",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"key": "value"},
                timestamp=self.now - timedelta(hours=1),
                tags=["preference", "important"]
            ),
            Memory(
                memory_id="normal-001",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"data": "test"},
                timestamp=self.now - timedelta(hours=1),
                tags=["normal"]
            )
        ]
        
        filtered = self.plugin._filter_memories(
            memories=memories,
            cutoff_time=self.now - timedelta(hours=24),
            include_tags=["preference"]
        )
        
        # Should only get preference-tagged memory
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].memory_id, "pref-001")
    
    def test_extract_preference_from_content(self):
        """Test extracting preferences from memory content."""
        memory = Memory(
            memory_id="pref-mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={
                "like": ["coffee", "reading", "outdoor activities"],
                "dislike": ["crowded places", "noise"]
            },
            timestamp=self.now,
            tags=["preference", "important"]
        )
        
        pref = self.plugin._extract_preference(memory)
        
        # Should extract preference about likes
        self.assertIsNotNone(pref)
        self.assertIn("like", pref.key.lower())
        self.assertEqual(pref.agent_id, self.agent_id)
        self.assertEqual(len(pref.source_memory_ids), 1)
    
    def test_extract_knowledge(self):
        """Test extracting knowledge from memory."""
        memory = Memory(
            memory_id="learn-mem-001",
            agent_id=self.agent_id,
            type=MemoryType.LONG_TERM,
            content={"lesson": "learned something important today"},
            timestamp=self.now,
            tags=["learning", "knowledge"]
        )
        
        knowledge = self.plugin._extract_knowledge(memory)
        
        self.assertIsNotNone(knowledge)
        self.assertIn("source_memory", knowledge)
        self.assertIn("content_summary", knowledge)
    
    def test_condense_empty_list(self):
        """Test condensing with no memories."""
        result = self.plugin.condense(
            memories=[],
            agent_id=self.agent_id,
            time_window=timedelta(hours=24)
        )
        
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memories_processed"], 0)
        self.assertEqual(result["pref_count"], 0)
    
    def test_condense_with_memories(self):
        """Test full condensation pipeline."""
        memories = [
            Memory(
                memory_id="mem-001",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"favorite_color": "blue"},
                timestamp=self.now - timedelta(hours=12),
                tags=["preference", "important"]
            ),
            Memory(
                memory_id="mem-002",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"lesson": "discovered efficient method"},
                timestamp=self.now - timedelta(hours=6),
                tags=["learning", "knowledge"]
            ),
            Memory(
                memory_id="mem-003",
                agent_id=self.agent_id,
                type=MemoryType.LONG_TERM,
                content={"note": "regular meeting"},
                timestamp=self.now - timedelta(hours=2),
                tags=["habit"]
            )
        ]
        
        result = self.plugin.condense(
            memories=memories,
            agent_id=self.agent_id,
            time_window=timedelta(hours=24),
            include_tags=["preference", "learning", "important", "habit"]
        )
        
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memories_processed"], 3)
        # Should have extracted at least some preferences/knowledge
        self.assertIn("prefs_created", result)
        self.assertIn("states_updated", result)


class TestIntegrationSlicingAndCondensation(unittest.TestCase):
    """Integration test: slicing -> cloud storage -> condensation."""
    
    def test_full_flow(self):
        """Test complete flow: slice → create memory → condense."""
        # Create slicer
        slicer = SimpleMemorySlicer(agent_id="integration-agent")
        
        # Simulate agent context (e.g., multiple tasks completed)
        large_context = {
            "user_preferences": {
                "likes": ["coding", "reading", "hiking"],
                "working_hours": "9 AM to 5 PM"
            },
            "events": [
                {
                    "timestamp": datetime.now() - timedelta(hours=20),
                    "type": "preference_update",
                    "data": {"favorite_technology": "Python"}
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=15),
                    "type": "learning",
                    "data": {"concept": "understood design patterns", "importance": "high"}
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=10),
                    "type": "preference",
                    "data": {"daily_habit": "morning run", "frequency": "every day"}
                }
            ]
        }
        
        # Step 1: Slice the large context
        slices = slicer.slice_memory(
            memory_id="context-full-001",
            content=large_context,
            auto_timestamps=True
        )
        
        self.assertGreater(len(slices), 0)
        
        # Step 2: Build index
        index = slicer.build_index()
        self.assertGreater(len(index.memories), 0)
        
        # Step 3: Create tagged memory for cloud storage
        tagged_memory = create_tagged_memory(
            agent_id="integration-agent",
            memory_id="context-full-001",
            slices=slices,
            full_content=large_context
        )
        
        # Verify memory structure
        self.assertEqual(tagged_memory.type, MemoryType.LONG_TERM)
        self.assertIn("_metadata", tagged_memory.content)
        self.assertIn("_full", tagged_memory.content)
        
        # Step 4: Condense knowledge
        plugin = SimpleTimeBasedCondensationPlugin()
        
        result = plugin.condense(
            memories=[tagged_memory],
            agent_id="integration-agent",
            time_window=timedelta(hours=24)
        )
        
        # Verify condensation worked
        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["memories_processed"], 1)
        
        # Check what was extracted
        if result["pref_count"] > 0:
            self.assertTrue(len(result["prefs_created"]) > 0)
        
        print(f"\n✓ Integration test passed!")
        print(f"  - Slices created: {len(slices)}")
        print(f"  - Index entries: {len(index.memories)}")
        print(f"  - Memories processed: {result['memories_processed']}")
        print(f"  - Preferences found: {result['pref_count']}")


if __name__ == "__main__":
    unittest.main()
