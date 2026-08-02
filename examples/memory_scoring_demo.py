"""Demo: Using Memory Scoring for Smart Memory Selection.

This script demonstrates how to use the CNAA memory scoring system
to select the best memories for different use cases.

Key scenarios covered:
1. Selecting high-quality memories (important + completed)
2. Finding context-relevant memories
3. Balancing recency vs. importance
4. Practical agent workflow integration
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from cloud.storage.memory_store import InMemoryMemoryStore
from cloud.storage.scoring_backend import MemoryScoringBackend
from cnaa.models import Memory, MemoryType
from cnaa.memory_selector import create_scored_selector


def demo_basic_scoring():
    """Demonstrate basic score calculation and ranking."""
    print("\n" + "="*60)
    print("📈 DEMO 1: Basic Memory Scoring")
    print("="*60)
    
    # Setup store and add memories with varying qualities
    store = InMemoryMemoryStore()
    
    # Create memories with different characteristics
    test_memories = [
        # High quality: recent, completed, important
        Memory(
            memory_id="high-quality-1",
            agent_id="demo-agent",
            type=MemoryType.LONG_TERM,
            content={"task": "Critical system deployment successful"},
            tags=["critical", "success"],
            completion_score=1.0,
            timestamp=datetime.now() - timedelta(hours=2),
        ),
        # Medium quality: old but important
        Memory(
            memory_id="old-important",
            agent_id="demo-agent",
            type=MemoryType.LONG_TERM,
            content={"task": "Important configuration knowledge"},
            tags=["important", "documentation"],
            completion_score=0.8,
            timestamp=datetime.now() - timedelta(days=14),
        ),
        # Low quality: recent but incomplete and unimportant
        Memory(
            memory_id="low-quality-1",
            agent_id="demo-agent",
            type=MemoryType.LONG_TERM,
            content={"task": "Tentative experiment"}
        ),
        # Medium-low: old and partial work
        Memory(
            memory_id="partial-work",
            agent_id="demo-agent",
            type=MemoryType.LONG_TERM,
            content={"task": "Work in progress"},
            completion_score=0.3,
            timestamp=datetime.now() - timedelta(days=7),
        ),
    ]
    
    # Store all memories
    for mem in test_memories:
        store.store_memory(mem)
    
    # Create selector and get top scored
    selector = create_scored_selector(store)
    top_results = selector.get_top_n("demo-agent", n=len(test_memories))
    
    print("\nRanking by composite score:")
    print("-" * 60)
    for rank, (mem, score) in enumerate(top_results, 1):
        print(f"{rank}. {mem.memory_id}")
        print(f"   Score: {score:.3f}")
        print(f"   Tags: {mem.tags or 'none'}")
        print(f"   Completion: {mem.completion_score:.2f}")
        print()


def demo_context_aware_selection():
    """Demonstrate context-aware memory selection."""
    print("\n" + "="*60)
    print("🎯 DEMO 2: Context-Aware Memory Selection")
    print("="*60)
    
    store = InMemoryMemoryStore()
    
    # Create diverse memories
    memories = [
        Memory(
            memory_id="python-dev",
            agent_id="dev-agent",
            type=MemoryType.LONG_TERM,
            content="Learned Python programming fundamentals",
            tags=["programming", "python", "tutorial"],
            completion_score=1.0,
            timestamp=datetime.now() - timedelta(days=1),
        ),
        Memory(
            memory_id="cooking-basics",
            agent_id="dev-agent",
            type=MemoryType.LONG_TERM,
            content="Basic cooking recipes learned",
            tags=["cooking", "recipes", "food"],
            completion_score=0.9,
            timestamp=datetime.now() - timedelta(days=2),
        ),
        Memory(
            memory_id="data-science",
            agent_id="dev-agent",
            type=MemoryType.LONG_TERM,
            content="Python for data science workshop",
            tags=["python", "datascience", "ml"],
            completion_score=0.7,
            timestamp=datetime.now() - timedelta(days=5),
        ),
    ]
    
    for mem in memories:
        store.store_memory(mem)
    
    selector = create_scored_selector(store)
    
    # Scenario 1: User interested in programming
    print("\n🔍 User query: 'Looking for programming tutorials'")
    programming_context = {"keywords": ["programming", "coding", "python"]}
    results = selector.get_top_n(
        "dev-agent", 
        n=3,
        context=programming_context
    )
    
    print("Most relevant memories:")
    for mem, score in results:
        relevance = "⚡ RELEVANT" if "programming" in mem.tags or "python" in mem.tags else ""
        print(f"  - {mem.memory_id} (score={score:.3f}) {relevance}")
    
    # Scenario 2: User interested in cooking
    print("\n🔍 User query: 'Looking for cooking tips'")
    cooking_context = {"keywords": ["cooking", "recipes", "food"]}
    results = selector.get_top_n(
        "dev-agent",
        n=3,
        context=cooking_context
    )
    
    print("Most relevant memories:")
    for mem, score in results:
        if "cooking" in mem.tags or "recipes" in mem.tags:
            print(f"  - {mem.memory_id} (score={score:.3f}) ⚡ RELEVANT")


def demo_importance_vs_recency():
    """Demonstrate balancing importance and recency."""
    print("\n" + "="*60)
    print("⚖️  DEMO 3: Importance vs. Recency Trade-off")
    print("="*60)
    
    store = InMemoryMemoryStore()
    
    # Create memories with different importance/recency combinations
    memories = [
        # Old but critical
        Memory(
            memory_id="secure-config",
            agent_id="ops-agent",
            type=MemoryType.LONG_TERM,
            content={"text": "Security configuration guidelines"},
            tags=["critical", "security"],
            completion_score=1.0,
            timestamp=datetime.now() - timedelta(days=30),  # Old!
        ),
        # Recent but minor
        Memory(
            memory_id="daily-note",
            agent_id="ops-agent",
            type=MemoryType.LONG_TERM,
            content={"text": "Daily routine update"},
            tags=["note"],
            completion_score=0.5,
            timestamp=datetime.now() - timedelta(hours=1),  # Fresh!
        ),
        # Important and somewhat recent
        Memory(
            memory_id="backup-process",
            agent_id="ops-agent",
            type=MemoryType.LONG_TERM,
            content={"text": "Backup automation process"},
            tags=["important", "automation"],
            completion_score=0.9,
            timestamp=datetime.now() - timedelta(days=3),
        ),
    ]
    
    for mem in memories:
        store.store_memory(mem)
    
    selector = create_scored_selector(store)
    
    # Get ranked by default (balanced scoring)
    print("\n📊 Default ranking (balanced weights):")
    default_ranking = selector.get_top_n("ops-agent", n=3)
    for rank, (mem, score) in enumerate(default_ranking, 1):
        indicator = "🆕 NEW" if "hours" in str(mem.timestamp) else "📅 OLD" if "days" in str(mem.timestamp) else ""
        print(f"  {rank}. {mem.memory_id} ({indicator}) - {score:.3f}")
    
    # Prioritize importance
    print("\n⭐ Important memories only (importance > 0.8):")
    important = selector.get_important_memories("ops-agent", min_importance=0.8)
    for mem, imp_score in important:
        print(f"  - {mem.memory_id}: importance={imp_score:.3f}")


def demo_practical_workflow():
    """Demonstrate practical agent workflow integration."""
    print("\n" + "="*60)
    print("🤖 DEMO 4: Practical Agent Workflow")
    print("="*60)
    
    # Simulate an AI assistant's memory usage
    store = InMemoryMemoryStore()
    
    # Real-world scenario: Personal assistant agent
    user_memories = [
        # Preferences and important facts
        Memory(
            memory_id="user-preferences",
            agent_id="alice",
            type=MemoryType.LONG_TERM,
            content={"text": "User prefers Python for coding tasks, uses VS Code"},
            tags=["important", "preferences", "critical"],
            completion_score=1.0,
            timestamp=datetime.now() - timedelta(days=7),
        ),
        # Recent achievements
        Memory(
            memory_id="project-complete",
            agent_id="alice",
            type=MemoryType.LONG_TERM,
            content={"text": "Completed Python web development project successfully"},
            tags=["success", "important", "completed"],
            completion_score=1.0,
            timestamp=datetime.now() - timedelta(days=1),
        ),
        # Learning progress
        Memory(
            memory_id="ml-learning",
            agent_id="alice",
            type=MemoryType.LONG_TERM,
            content={"text": "Studied machine learning fundamentals"},
            tags=["learning", "note"],
            completion_score=0.6,
            timestamp=datetime.now() - timedelta(days=5),
        ),
        # Minor todo items
        Memory(
            memory_id="meeting-notes",
            agent_id="alice",
            type=MemoryType.LONG_TERM,
            content={"text": "Meeting notes from team sync"}
        ),
    ]
    
    for mem in user_memories:
        store.store_memory(mem)
    
    selector = create_scored_selector(store)
    
    # Use case 1: Help user recall important information
    print("\n💼 Use Case 1: User asks 'What did I accomplish recently?'")
    helpful_context = {"keywords": ["accomplish", "complete", "finish"]}
    best_match = selector.find_best_match(
        "alice",
        query_context=helpful_context,
        threshold=0.5
    )
    if best_match:
        mem, score = best_match
        print(f"  💡 Suggest: '{mem.content}'")
        print(f"     Relevance: {score:.3f}")
    
    # Use case 2: Prepare for meeting prep
    print("\n📋 Use Case 2: Prepare for weekly review meeting")
    important_items = selector.get_important_memories("alice", min_importance=0.7, top_n=3)
    print("  Key topics to discuss:")
    for i, (mem, imp_score) in enumerate(important_items, 1):
        # Get readable text from content dict
        content_text = mem.content.get("text", str(mem.content)) if isinstance(mem.content, dict) else mem.content
        print(f"    {i}. {content_text[:50]}...")
    
    # Use case 3: Suggest next steps based on partial work
    print("\n🚀 Use Case 3: Suggest next steps for ongoing projects")
    recent_work = selector.filter_by_threshold("alice", min_composite=0.4)
    if recent_work:
        for mem, score in recent_work[:2]:
            if mem.completion_score < 1.0:
                # Get readable text from content dict
                content_text = mem.content.get("text", str(mem.content)) if isinstance(mem.content, dict) else mem.content
                print(f"  🔄 Continue: {content_text[:40]}... (completion: {mem.completion_score:.0%})")


def main():
    """Run all demos."""
    print("\n" + "🧪" * 60)
    print("CNAA Memory Scoring System - Complete Demo")
    print("🧪" * 60)
    
    demo_basic_scoring()
    demo_context_aware_selection()
    demo_importance_vs_recency()
    demo_practical_workflow()
    
    print("\n" + "="*60)
    print("✅ All demos completed successfully!")
    print("="*60)
    print("\n📚 Key Takeaways:")
    print("  • Composite scoring balances multiple factors")
    print("  • Context-aware selection improves relevance")
    print("  • Importance weighting ensures critical info surfaces")
    print("  • Flexible thresholds enable different use cases")
    print("\n🛠️  Next steps:")
    print("  • Integrate into your agent workflow")
    print("  • Adjust weights for your domain")
    print("  • Customize scoring algorithms as needed")
    print()


if __name__ == "__main__":
    main()
