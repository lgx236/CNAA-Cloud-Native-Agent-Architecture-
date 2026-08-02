"""Memory Slicing and Knowledge Condensation Example.

This example demonstrates how to use the new memory slicing,
time-based querying, and knowledge condensation features.
"""

from datetime import datetime, timedelta
from cnaa.models import Memory, MemoryType
from local.memory.slicer import SimpleMemorySlicer, create_tagged_memory
from cnaa.lifecycle import SimpleTimeBasedCondensationPlugin


def example_1_basic_slicing():
    """Example 1: Basic memory slicing."""
    print("=" * 60)
    print("Example 1: Basic Memory Slicing")
    print("=" * 60)
    
    # Create a slicer for an agent
    slicer = SimpleMemorySlicer(agent_id="my-agent-001")
    
    # Simulate agent context (e.g., a conversation or task history)
    large_context = {
        "events": [
            {
                "timestamp": datetime.now() - timedelta(hours=3),
                "action": "search",
                "result": "found relevant information",
                "tags": ["important", "learning"]
            },
            {
                "timestamp": datetime.now() - timedelta(hours=2),
                "action": "decision",
                "result": "chose option A over B",
                "tags": ["decision", "preference"]
            },
            {
                "timestamp": datetime.now() - timedelta(hours=1),
                "action": "completion",
                "result": "task completed successfully",
                "tags": ["success"]
            }
        ]
    }
    
    # Slice the memory into chronological chunks
    slices = slicer.slice_memory(
        memory_id="conversation-001",
        content=large_context,
        auto_timestamps=True
    )
    
    print(f"✓ Created {len(slices)} slices from one memory")
    for i, slice_obj in enumerate(slices):
        print(f"  - Slice {i+1}: {slice_obj.summary}")
        print(f"    Tags: {slice_obj.extracted_tags}")
        print(f"    Time: {slice_obj.start_time}")
    
    # Build index for querying
    index = slicer.build_index()
    print(f"\n✓ Built index with {len(index.memories)} entries")


def example_2_time_based_querying():
    """Example 2: Time-based memory querying."""
    print("\n" + "=" * 60)
    print("Example 2: Time-Based Querying")
    print("=" * 60)
    
    slicer = SimpleMemorySlicer(agent_id="query-agent")
    
    # Add some memories with different timestamps
    base_time = datetime.now()
    
    content_old = {
        "events": [
            {"time": base_time - timedelta(days=1), "data": "old event"}
        ]
    }
    
    content_recent = {
        "events": [
            {"time": base_time - timedelta(minutes=30), "data": "recent event"}
        ]
    }
    
    slicer.slice_memory("old-mem", content_old)
    slicer.slice_memory("new-mem", content_recent)
    slicer.build_index()
    
    # Query by time range
    recent_memories = slicer.query_by_time_range(
        start_time=base_time - timedelta(hours=1),
        end_time=base_time
    )
    
    print(f"\nMemories from last hour: {len(recent_memories)}")
    for mem in recent_memories:
        print(f"  - {mem['memory_id']}")
    
    # Get most recent N memories
    latest = slicer.get_latest_n(5)
    print(f"\nLatest 5 memories: {len(latest)}")


def example_3_tag_extraction():
    """Example 3: Automatic tag extraction."""
    print("\n" + "=" * 60)
    print("Example 3: Automatic Tag Extraction")
    print("=" * 60)
    
    slicer = SimpleMemorySlicer(agent_id="tag-agent")
    
    # Content with important keywords
    important_content = {
        "message": "This is CRITICAL information that must be remembered",
        "priority": "high",
        "context": "urgent situation"
    }
    
    slices = slicer.slice_memory("important-001", important_content)
    
    all_tags = set()
    for slice_obj in slices:
        all_tags.update(slice_obj.extracted_tags)
    
    print(f"\nExtracted tags: {list(all_tags)}")
    print("Tags like 'important', 'critical' are automatically detected!")


def example_4_knowledge_condensation():
    """Example 4: Knowledge condensation plugin."""
    print("\n" + "=" * 60)
    print("Example 4: Knowledge Condensation")
    print("=" * 60)
    
    plugin = SimpleTimeBasedCondensationPlugin()
    
    # Create some memories that might trigger preference/knowledge extraction
    now = datetime.now()
    memories = [
        Memory(
            memory_id="pref-001",
            agent_id="condense-agent",
            type=MemoryType.LONG_TERM,
            content={"favorite_language": "Python", "reason": "versatile"},
            timestamp=now - timedelta(hours=12),
            tags=["preference", "important"]
        ),
        Memory(
            memory_id="learn-001",
            agent_id="condense-agent",
            type=MemoryType.LONG_TERM,
            content={"lesson": "understood design patterns", "importance": "high"},
            timestamp=now - timedelta(hours=6),
            tags=["learning", "knowledge"]
        ),
        Memory(
            memory_id="habit-001",
            agent_id="condense-agent",
            type=MemoryType.LONG_TERM,
            content={"daily_routine": "morning coding session"},
            timestamp=now - timedelta(hours=2),
            tags=["habit", "preference"]
        )
    ]
    
    # Run condensation
    result = plugin.condense(
        memories=memories,
        agent_id="condense-agent",
        time_window=timedelta(hours=24),
        include_tags=["preference", "learning", "important", "habit"]
    )
    
    print(f"\nCondensation results:")
    print(f"  - Memories processed: {result['memories_processed']}")
    print(f"  - Preferences extracted: {result['pref_count']}")
    print(f"  - States updated: {len(result['states_updated'])}")
    
    if result["prefs_created"]:
        print(f"  - Preference IDs: {result['prefs_created']}")


def example_5_full_integration():
    """Example 5: Full workflow integration."""
    print("\n" + "=" * 60)
    print("Example 5: Complete Agent Workflow")
    print("=" * 60)
    
    # Step 1: Agent completes multiple tasks
    print("\n1️⃣ Agent completing tasks...")
    slicer = SimpleMemorySlicer(agent_id="workflow-agent")
    
    agent_context = {
        "user_preferences": {
            "likes": ["coding", "reading", "hiking"],
            "working_hours": "9 AM to 5 PM"
        },
        "events": [
            {
                "timestamp": datetime.now() - timedelta(hours=20),
                "type": "preference_update",
                "data": {"favorite_technology": "Python", "importance": "high"}
            },
            {
                "timestamp": datetime.now() - timedelta(hours=15),
                "type": "learning",
                "data": {"concept": "design patterns", "mastery": "intermediate"}
            },
            {
                "timestamp": datetime.now() - timedelta(hours=10),
                "type": "preference",
                "data": {"daily_habit": "morning run", "frequency": "every day"}
            }
        ]
    }
    
    # Step 2: Slice large context
    print("\n2️⃣ Slicing large context into chunks...")
    slices = slicer.slice_memory(
        memory_id="day-completion-001",
        content=agent_context,
        auto_timestamps=True
    )
    print(f"   ✓ Created {len(slices)} memory slices")
    
    # Step 3: Build index
    print("\n3️⃣ Building chronological index...")
    index = slicer.build_index()
    print(f"   ✓ Index contains {len(index.memories)} entries")
    
    # Step 4: Create CNAA Memory for cloud storage
    print("\n4️⃣ Creating CNAA Memory for cloud storage...")
    full_memory = create_tagged_memory(
        agent_id="workflow-agent",
        memory_id="day-completion-001",
        slices=slices,
        full_content=agent_context
    )
    
    print(f"   ✓ Memory ID: {full_memory.memory_id}")
    print(f"   ✓ Type: {full_memory.type.value}")
    print(f"   ✓ Tags: {full_memory.tags}")
    print(f"   ✓ Metadata: {full_memory.metadata}")
    
    # Step 5: Condense knowledge
    print("\n5️⃣ Condensing knowledge from memories...")
    plugin = SimpleTimeBasedCondensationPlugin()
    
    result = plugin.condense(
        memories=[full_memory],
        agent_id="workflow-agent",
        time_window=timedelta(hours=24)
    )
    
    print(f"   ✓ Processed {result['memories_processed']} memories")
    print(f"   ✓ Extracted {result['pref_count']} preferences")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ COMPLETE WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"• Agent sliced their experience into {len(slices)} parts")
    print(f"• Each slice was tagged automatically")
    print(f"• Chronological index built for fast querying")
    print(f"• Full content stored as CNAA Memory in cloud")
    print(f"• Knowledge condensed to extract preferences")
    print("\nThe agent can now:")
    print("  • Query memories by time range")
    print("  • Search by tags")
    print("  • Access cloud-stored memories via cnaa_ref")
    print("  • Have preferences/知识沉淀 to cloud state layer")


if __name__ == "__main__":
    print("\n🎯 CNAA Memory Slicing & Knowledge Condensation Demo\n")
    
    try:
        example_1_basic_slicing()
        example_2_time_based_querying()
        example_3_tag_extraction()
        example_4_knowledge_condensation()
        example_5_full_integration()
        
        print("\n" + "=" * 60)
        print("🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Integrate slicer into your agent framework")
        print("2. Use MCP tools to store memories in cloud")
        print("3. Query memories when needed for context retrieval")
        print("4. Run condensation periodically to extract preferences")
        
    except Exception as e:
        print(f"\n❌ Error during examples: {e}")
        import traceback
        traceback.print_exc()
