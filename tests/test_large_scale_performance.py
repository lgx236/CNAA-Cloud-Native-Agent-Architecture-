"""Large-scale Performance and Load Tests for CNAA Framework.

This test suite focuses on:
- Large volume data operations (thousands of records)
- Long-running stress tests (simulated time, multiple cycles)
- Concurrency and parallel access patterns
- Memory efficiency with large datasets
- Performance benchmarks with metrics

All tests use realistic but scaled data to verify the system under
production-like loads while maintaining correctness.
"""

import unittest
import time
from datetime import datetime, timedelta

from cnaa.models import Memory, MemoryType, State, StateCategory, Preference, Environment, MemoryStatus
from cloud.server.mcp_server import CNAA_MCPServer
from cloud.storage.memory_store import InMemoryMemoryStore
from cloud.storage.state_store import InMemoryStateStore
from local.agent import LocalAgentInterface
from local.memory.instant_memory import InstantMemoryManager
from local.state.state_cache import StateCache


class TestLargeVolumeMemoryOperations(unittest.TestCase):
    """Test memory operations with large volumes."""

    def setUp(self):
        self.store = InMemoryMemoryStore()

    def test_store_1000_memories_batch(self):
        """PERFORMANCE: Store 1000 memories in batch."""
        start = time.time()
        
        for i in range(1000):
            memory = Memory(
                memory_id=f"mem-{i:04d}",
                agent_id="perf-agent",
                type=MemoryType.LONG_TERM,
                content={"index": i, "data": "x" * 100},
                tags=["perf", f"type-{i % 10}"],
                completion_score=i / 1000,
            )
            result = self.store.store_memory(memory)
            self.assertEqual(result["status"], "ok")
        
        elapsed = time.time() - start
        count = self.store.count()
        self.assertEqual(count, 1000)
        
        # Performance sanity check (should be reasonably fast)
        print(f"\nStored 1000 memories in {elapsed:.3f}s ({count/elapsed:.0f}/s)")
        self.assertLess(elapsed, 10.0)  # Should complete in < 10s

    def test_retrieve_1000_memories_random(self):
        """PERFORMANCE: Random retrieval of 1000 pre-stored memories."""
        # First populate store
        for i in range(1000):
            memory = Memory(
                memory_id=f"rand-mem-{i:04d}",
                agent_id="perf-agent",
                type=MemoryType.LONG_TERM,
                content={},
            )
            self.store.store_memory(memory)
        
        # Random retrievals
        import random
        indices = random.sample(range(1000), 200)
        start = time.time()
        
        retrieved_count = 0
        for idx in indices:
            mem = self.store.get_memory("perf-agent", f"rand-mem-{idx:04d}")
            if mem:
                retrieved_count += 1
        
        elapsed = time.time() - start
        self.assertEqual(retrieved_count, 200)
        
        # Average per retrieval
        avg_time = elapsed / 200 * 1000  # ms per retrieval
        print(f"\nAverage retrieval time: {avg_time:.3f}ms")
        self.assertLess(avg_time, 100)  # < 100ms per retrieval

    def test_list_all_1000_memories(self):
        """PERFORMANCE: List all 1000 memories."""
        # Populate
        for i in range(1000):
            memory = Memory(
                memory_id=f"list-mem-{i:04d}",
                agent_id="perf-agent",
                type=MemoryType.LONG_TERM,
                content={},
            )
            self.store.store_memory(memory)
        
        start = time.time()
        summaries = self.store.list_memories("perf-agent")
        elapsed = time.time() - start
        
        self.assertEqual(len(summaries), 1000)
        
        print(f"\nListed 1000 memories in {elapsed:.3f}s")
        self.assertLess(elapsed, 5.0)

    def test_filter_by_tags_1000_memories(self):
        """PERFORMANCE: Filter 1000 memories by tags."""
        # Create with various tags
        for i in range(1000):
            memory = Memory(
                memory_id=f"tag-mem-{i:04d}",
                agent_id="perf-agent",
                type=MemoryType.LONG_TERM,
                content={},
                tags=[f"category-{i % 5}"],
            )
            self.store.store_memory(memory)
        
        start = time.time()
        filtered = self.store.list_memories("perf-agent", tags=["category-2"])
        elapsed = time.time() - start
        
        self.assertEqual(len(filtered), 200)  # ~20% have this tag
        
        print(f"\nFiltered to {len(filtered)} memories in {elapsed:.3f}s")

    def test_delete_half_memories(self):
        """PERFORMANCE: Delete half of 1000 memories."""
        # Populate
        for i in range(1000):
            memory = Memory(
                memory_id=f"del-mem-{i:04d}",
                agent_id="perf-agent",
                type=MemoryType.LONG_TERM,
                content={},
            )
            self.store.store_memory(memory)
        
        # Delete every other
        start = time.time()
        deleted_count = 0
        for i in range(0, 1000, 2):
            result = self.store.delete_memory("perf-agent", f"del-mem-{i:04d}")
            if result["status"] == "ok":
                deleted_count += 1
        
        elapsed = time.time() - start
        remaining = self.store.count()
        
        self.assertEqual(deleted_count, 500)
        self.assertEqual(remaining, 500)
        
        print(f"\nDeleted {deleted_count} memories in {elapsed:.3f}s ({deleted_count/elapsed:.0f}/s)")


class TestLongRunningSessionSimulation(unittest.TestCase):
    """Test simulated long-running agent sessions."""

    def test_week_of_activity_simulation(self):
        """LONG-RUNNING: Simulate a week of agent activity."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="week-agent", cloud_server=server)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        tasks_per_day = 10
        total_activities = 0
        
        print("\n=== Week Simulation ===")
        
        # Day 1
        print(f"\n[{days[0]}] Task execution...")
        for i in range(tasks_per_day):
            agent.store_memory(
                memory_id=f"w1-t{i:02d}",
                memory_type="long_term",
                content={"day": 1, "task": i, "data": f"Day1-Task{i}"},
                completion_score=0.7 + (i % 10) * 0.05,
            )
            total_activities += 1
        
        # Days 2-7
        for day_idx in range(2, 8):
            print(f"[{days[day_idx-1]}] Tasks {total_activities+1}-{total_activities+tasks_per_day}...")
            for i in range(tasks_per_day):
                agent.store_memory(
                    memory_id=f"w{day_idx}-t{i:02d}",
                    memory_type="long_term",
                    content={"day": day_idx, "task": i},
                    completion_score=0.6 + (i % 10) * 0.06,
                )
                total_activities += 1
                
                # Occasionally create instant memory
                if i % 3 == 0:
                    agent.create_instant_memory(
                        task_id=f"task-w{day_idx}-{i}",
                        checkpoint_id=f"cp-w{day_idx}-{i}",
                        summary=f"Completed day{day_idx} task{i}",
                        memory_id=f"w{day_idx}-t{i:02d}",
                    )
        
        # Accumulate knowledge over the week
        for k in range(15):
            agent.update_state(
                state_id=f"knowledge-k{k:02d}",
                category="knowledge",
                content={
                    "topic": f"lesson_{k}",
                    "learned_from_days": list(range(1, min(k + 2, 8))),
                },
            )
        
        # Learn preferences
        for p in range(8):
            agent.update_preference(
                preference_id=f"pref-p{p:02d}",
                key=f"preference_{p}",
                value={"strength": 0.5 + p * 0.1},
                importance=0.6 + p * 0.05,
            )
        
        # Update environment daily
        for day_idx in range(1, 8):
            agent.update_environment(
                env_id="env-day",
                context={
                    "current_day": day_idx,
                    "total_activities": total_activities // 7 * day_idx,
                },
            )
        
        # Summary
        final_memories = len(agent.list_memories()["memories"])
        final_states = len(agent.get_states(use_cache=False))
        final_prefs = len(agent.get_preferences(use_cache=False))
        active_instants = len(agent.get_active_instant_memories())
        
        print(f"\n=== Week Summary ===")
        print(f"Total activities: {total_activities}")
        print(f"Final memories stored: {final_memories}")
        print(f"Knowledge accumulated: {final_states} states")
        print(f"Preferences learned: {final_prefs}")
        print(f"Active instant memories: {active_instants}")
        
        self.assertEqual(final_memories, 70)  # 7 days * 10 tasks/day
        self.assertEqual(final_states, 15)
        self.assertEqual(final_prefs, 8)
        self.assertEqual(active_instants, 24)  # Condensation happens during week

    def test_monthly_summary_generation(self):
        """LONG-RUNNING: Monthly activity with periodic summarization."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="month-agent", cloud_server=server)
        
        days_in_month = 30
        weekly_summaries = []
        
        print("\n=== Month Activity with Weekly Summaries ===")
        
        for week in range(4):
            week_tasks = 0
            
            # Week period
            for day in range(7):
                task_index = (week * 7 + day) * 5 + 1
                
                # Multiple tasks per day
                for i in range(5):
                    agent.store_memory(
                        memory_id=f"m{week}d{day}t{i:02d}",
                        memory_type="long_term",
                        content={"week": week, "day": day, "task_num": i},
                        completion_score=(task_index + i) / 35,
                    )
                    week_tasks += 1
            
            # End of week: accumulate knowledge from week
            week_summary = f"Completed {week_tasks} tasks in week {week}"
            weekly_summaries.append(week_summary)
            
            agent.update_state(
                state_id=f"weekly-summary-w{week}",
                category="knowledge",
                content={
                    "summary": week_summary,
                    "total_tasks": week_tasks,
                    "average_completion": (sum(list(range(task_index + 5))) / task_index) / 35,
                },
            )
        
        # Monthly review
        agent.update_state(
            state_id="monthly-review",
            category="knowledge",
            content={
                "total_weeks": 4,
                "total_tasks": sum(len(s) for s in weekly_summaries),
                "lessons_learned": 4,
            },
        )
        
        agent.update_preference(
            preference_id="monthly-pattern",
            key="work_pattern",
            value={"consistency": "high", "productivity_trend": "increasing"},
            importance=0.8,
        )
        
        # Final counts
        memories = len(agent.list_memories()["memories"])
        states = len(agent.get_states(use_cache=False))
        
        print(f"\nMemories stored: {memories}")
        print(f"States accumulated: {states}")
        
        self.assertEqual(memories, 140)  # 4 weeks * 7 days * 5 tasks
        self.assertEqual(states, 5)  # 4 weekly summaries + 1 monthly review

    def test_yearly_retention_simulation(self):
        """LONG-RUNNING: Yearly data retention pattern."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="year-agent", cloud_server=server)
        
        months = [
            "Q1", "Q2", "Q3", "Q4",
        ]
        
        print("\n=== Yearly Retention Pattern ===")
        
        # Quarterly milestones
        for quarter in range(4):
            month_name = months[quarter]
            tasks_this_quarter = 0
            
            # Each quarter has 3 months
            for month in range(3):
                for task in range(20):  # 20 tasks/month
                    agent.store_memory(
                        memory_id=f"y{quarter}m{month}t{task:02d}",
                        memory_type="long_term",
                        content={
                            "quarter": quarter,
                            "month": month,
                            "task": task,
                            "quarter_name": month_name,
                        },
                        completion_score=(task + month) / 40 + quarter * 0.1,
                    )
                    tasks_this_quarter += 1
            
            # Quarterly milestone state
            agent.update_state(
                state_id=f"milestone-q{quarter}",
                category="knowledge",
                content={
                    "quarter": month_name,
                    "completed_tasks": tasks_this_quarter,
                    "completion_avg": tasks_this_quarter / 60,
                },
            )
            
            print(f"{month_name}: {tasks_this_quarter} tasks completed")
        
        # Annual goals
        agent.update_state(
            state_id="annual-goals",
            category="knowledge",
            content={
                "total_quarters": 4,
                "goal": "Complete all quarterly objectives",
            },
        )
        
        # Annual achievements
        for achievement in range(12):
            agent.update_preference(
                preference_id=f"achievement-{achievement:02d}",
                key="skill",
                value={"level": 1 + achievement // 4},
                importance=0.5 + (achievement % 4) * 0.1,
            )
        
        # Verify yearly totals
        memories = len(agent.list_memories()["memories"])
        states = len(agent.get_states(use_cache=False))
        prefs = len(agent.get_preferences(use_cache=False))
        
        print(f"\nYearly Summary:")
        print(f"Total memories: {memories}")
        print(f"Milestone states: {states}")
        print(f"Achievements tracked: {prefs}")
        
        self.assertEqual(memories, 240)  # 4 quarters * 3 months * 20 tasks
        self.assertEqual(states, 5)  # 4 quarterly milestones + 1 annual goals
        self.assertEqual(prefs, 12)


class TestConcurrentAccessPatterns(unittest.TestCase):
    """Test concurrent access patterns to shared storage."""

    def test_multiple_agents_concurrent_stores(self):
        """CONCURRENT: 10 agents each storing 50 memories concurrently."""
        server = CNAA_MCPServer()
        
        start = time.time()
        
        # Simulate concurrent agents
        for agent_idx in range(10):
            agent = LocalAgentInterface(
                agent_id=f"concurrent-agent-{agent_idx}",
                cloud_server=server,
            )
            
            # Each agent stores 50 memories
            for mem_idx in range(50):
                agent.store_memory(
                    memory_id=f"ca{agent_idx}-m{mem_idx:02d}",
                    memory_type="long_term",
                    content={
                        "agent": agent_idx,
                        "memory": mem_idx,
                        "shared": True,
                    },
                )
        
        elapsed = time.time() - start
        
        # Verify isolation
        for agent_idx in range(10):
            agent = LocalAgentInterface(
                agent_id=f"concurrent-agent-{agent_idx}",
                cloud_server=server,
            )
            memories = agent.list_memories()["memories"]
            self.assertEqual(len(memories), 50)
        
        total = server.memory_store.count()
        self.assertEqual(total, 500)  # 10 agents * 50 memories
        
        print(f"\n10 agents × 50 memories in {elapsed:.3f}s")
        self.assertLess(elapsed, 15.0)  # Should complete quickly

    def test_same_agent_concurrent_updates(self):
        """CONCURRENT: Same agent updating many different entities rapidly."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="burst-agent", cloud_server=server)
        
        start = time.time()
        
        # Rapid burst updates
        for i in range(100):
            # Alternate between different entity types
            if i % 3 == 0:
                agent.update_state(
                    state_id=f"burst-s{i:03d}",
                    category="knowledge",
                    content={"burst": i},
                )
            elif i % 3 == 1:
                agent.update_preference(
                    preference_id=f"burst-p{i:03d}",
                    key=f"key_{i}",
                    value={"burst": i},
                )
            else:
                agent.update_environment(
                    env_id="burst-env",
                    context={"burst": i, "timestamp": datetime.now().isoformat()},
                )
        
        elapsed = time.time() - start
        
        states = len(agent.get_states(use_cache=False))
        prefs = len(agent.get_preferences(use_cache=False))
        env = agent.get_environment(use_cache=False)
        
        self.assertEqual(states, 34)  # ceil(100/3)
        self.assertEqual(prefs, 33)  # floor(100/3)
        self.assertIsNotNone(env)
        
        print(f"\n100 rapid updates in {elapsed:.3f}s ({elapsed*10:.1f}ms/update)")


class TestMemoryEfficiencyWithLargeData(unittest.TestCase):
    """Test memory usage patterns with large datasets."""

    def test_5000_memories_memory_footprint(self):
        """MEMORY: Store 5000 memories and measure approximate footprint."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="large-agent", cloud_server=server)
        
        # Store large memories
        print("\nStoring 5000 large memories...")
        for i in range(5000):
            agent.store_memory(
                memory_id=f"bigmem-{i:05d}",
                memory_type="long_term",
                content={
                    "data": "x" * 1000,  # 1KB per memory content
                    "metadata": {"size_kb": 1},
                },
            )
        
        count = len(agent.list_memories()["memories"])
        self.assertEqual(count, 5000)
        
        import gc
        gc.collect()
        
        # Get rough memory estimate
        try:
            import resource
            mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # MB
            print(f"Max RSS during test: {mem_usage:.1f}MB")
        except ImportError:
            print("Memory stats not available on this platform")
    
    def test_cache_with_large_state_lists(self):
        """MEMORY: Test cache with many cached items."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(
            agent_id="cache-large-agent",
            cloud_server=server,
            cache_ttl_minutes=30.0,
        )
        
        # Cache a lot of states
        for i in range(200):
            agent.update_state(
                state_id=f"state-{i:03d}",
                category="knowledge",
                content={"value": i, "data": "test"},
            )
        
        # Verify caching works
        for _ in range(3):  # Fetch multiple times
            states = agent.get_states(use_cache=True)
            self.assertEqual(len(states), 200)
        
        print(f"\nCached 200 states, fetched 3 times")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks with timing metrics."""

    def test_store_operations_per_second(self):
        """BENCHMARK: Measure store operations/sec rate."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="bench-agent", cloud_server=server)
        
        iterations = 1000
        start = time.perf_counter()
        
        for i in range(iterations):
            agent.store_memory(
                memory_id=f"bench-{i}",
                memory_type="long_term",
                content={},
            )
        
        elapsed = time.perf_counter() - start
        ops_per_sec = iterations / elapsed
        
        print(f"\nSTORE BENCHMARK:")
        print(f"  Iterations: {iterations}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Rate: {ops_per_sec:.1f} ops/sec")
        
        # Sanity check - should be at least 50 ops/sec
        self.assertGreater(ops_per_sec, 50)

    def test_get_operations_per_second(self):
        """BENCHMARK: Measure get operations/sec rate."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="bench-get-agent", cloud_server=server)
        
        # Pre-populate
        iterations = 100
        for i in range(iterations):
            agent.store_memory(
                memory_id=f"bench-get-{i:03d}",
                memory_type="long_term",
                content={},
            )
        
        start = time.perf_counter()
        
        for i in range(iterations):
            agent.get_memory(f"bench-get-{i:03d}")
        
        elapsed = time.perf_counter() - start
        ops_per_sec = iterations / elapsed
        
        print(f"\nGET BENCHMARK:")
        print(f"  Iterations: {iterations}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Rate: {ops_per_sec:.1f} ops/sec")

    def test_list_operations_with_filtering(self):
        """BENCHMARK: List with filtering performance."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="bench-list-agent", cloud_server=server)
        
        # Create varied data
        categories = ["cat-a", "cat-b", "cat-c", "cat-d"]
        for i in range(500):
            agent.store_memory(
                memory_id=f"list-bench-{i:03d}",
                memory_type="long_term",
                content={},
                tags=[categories[i % 4], f"idx-{i % 10}"],
            )
        
        # Filter test
        start = time.perf_counter()
        result = agent.list_memories(tags=["cat-a"])
        elapsed = time.perf_counter() - start
        
        count = len(result["memories"])
        ops_per_sec = count / elapsed if elapsed > 0 else 0
        
        print(f"\nLIST+BENCHMARK:")
        print(f"  Total: 500 memories")
        print(f"  Filtered: {count} items")
        print(f"  Time: {elapsed:.4f}s")
        print(f"  Rate: {ops_per_sec:.0f} items/sec")

    def test_bulk_lifecycle_transitions(self):
        """BENCHMARK: Bulk lifecycle transitions."""
        manager = InstantMemoryManager(agent_id="lifecycle-bench")
        
        # Create 200 active memories
        num_memories = 200
        for i in range(num_memories):
            manager.create_instant_memory(
                task_id=f"bench-t{i:03d}",
                checkpoint_id=f"bench-cp{i:03d}",
                summary=f"Benchmark {i}",
                memory_id=f"bench-lc{i:03d}",
            )
        
        # Manually condense all (bypass time threshold)
        condensed_count = 0
        for mid in list(manager._memories.keys()):
            if manager.condense_memory(mid) is not None:
                condensed_count += 1
        
        # Evict all condensed
        evicted_count = 0
        for mid in list(manager._memories.keys()):
            instant = manager._memories.get(mid)
            if instant and instant.status == MemoryStatus.CONDENSED:
                if manager.evict_memory(mid) is not None:
                    evicted_count += 1
        
        # Remove all evicted
        removed_count = manager.remove_evicted_memories()
        
        print(f"\nLIFECYCLE BENCHMARK (n={num_memories}):")
        print(f"  Created: {num_memories} active")
        print(f"  Condensed: {condensed_count}")
        print(f"  Evicted: {evicted_count}")
        print(f"  Removed: {removed_count}")
        
        self.assertEqual(condensed_count, num_memories)
        self.assertEqual(evicted_count, num_memories)
        self.assertEqual(removed_count, num_memories)


# ===================================================================
# Super Big Tests (10+) - These are the "mega" tests
# ===================================================================

@unittest.skip("Skip large tests by default - run with --large-tests flag")
class TestSuperLargeScalePerformance(unittest.TestCase):
    """Super large-scale performance tests for production readiness."""
    
    @classmethod
    def setUpClass(cls):
        """Run once for entire test class."""
        print("\n" + "="*80)
        print("SUPER LARGE SCALE TESTS - PRODUCTION READINESS BENCHMARKING")
        print("="*80 + "\n")
    
    def test_10000_memories_full_operations(self):
        """MEGA: 10K memories through full CRUD operations."""
        print("\n[TEST] MEGA: 10,000 Memories Full Lifecycle")
        start_total = time.time()
        
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="mega-10k", cloud_server=server)
        
        # Phase 1: Massive bulk store
        print("  → Storing 10,000 memories...")
        start = time.time()
        for i in range(10000):
            agent.store_memory(
                memory_id=f"mega-{i:05d}",
                memory_type="long_term",
                content={
                    "batch": i // 1000,
                    "index": i,
                    "payload": "data" * 100,  # Medium payload
                },
                tags=[f"batch-{i//1000}"],
                completion_score=i / 10000,
            )
        store_time = time.time() - start
        print(f"      ✓ Stored 10,000 in {store_time:.2f}s ({10000/store_time:.1f}/s)")
        
        # Phase 2: Massive query verification
        print("  → Querying 10,000 memories...")
        start = time.time()
        for i in range(0, 10000, 100):  # Every 100th
            result = agent.get_memory(f"mega-{i:05d}")
            self.assertEqual(result["status"], "ok")
        query_time = time.time() - start
        sampled_rate = 100 / query_time
        print(f"      ✓ Sampled queries at {sampled_rate:.0f} ops/sec average")
        
        # Phase 3: Bulk list
        print("  → Listing all memories...")
        start = time.time()
        all_memories = agent.list_memories()
        list_time = time.time() - start
        print(f"      ✓ Listed {len(all_memories['memories'])} in {list_time:.2f}s")
        
        # Phase 4: Deletion of half
        print("  → Deleting 5,000 memories...")
        start = time.time()
        for i in range(0, 10000, 2):
            agent.delete_memory(f"mega-{i:05d}")
        delete_time = time.time() - start
        print(f"      ✓ Deleted 5,000 in {delete_time:.2f}s ({5000/delete_time:.0f}/s)")
        
        total_time = time.time() - start_total
        print(f"\n  🏆 TOTAL TIME: {total_time:.2f}s for 10K memory operations")
        self.assertLess(total_time, 120)  # Should complete in < 2 minutes
    
    def test_100_agents_heavy_load(self):
        """MEGA: 100 agents each doing heavy operations simultaneously."""
        print("\n[TEST] MEGA: 100 Agents × Heavy Operations")
        start_total = time.time()
        
        server = CNAA_MCPServer()
        agents = []
        
        # Create 100 agents
        print("  → Creating 100 agents...")
        for i in range(100):
            agents.append(LocalAgentInterface(
                agent_id=f"mega-agent-{i:03d}",
                cloud_server=server,
            ))
        
        # Each agent performs heavy workload
        print("  → Running heavy load on each agent...")
        start = time.time()
        for agent_idx, agent in enumerate(agents):
            # Memories
            for j in range(50):
                agent.store_memory(
                    memory_id=f"a{agent_idx}-m{j:02d}",
                    memory_type="long_term",
                    content={"agent": agent_idx, "mem": j},
                )
            # States
            for j in range(20):
                agent.update_state(
                    state_id=f"a{agent_idx}-s{j:02d}",
                    category="knowledge",
                    content={"val": j},
                )
            # Preferences
            for j in range(10):
                agent.update_preference(
                    preference_id=f"a{agent_idx}-p{j:02d}",
                    key=f"pref_{j}",
                    value={"important": True},
                )
        mixed_time = time.time() - start
        
        # Verify everything persisted correctly
        print("  → Verifying persistence...")
        for agent_idx in range(100):
            agent = LocalAgentInterface(
                agent_id=f"mega-agent-{agent_idx:03d}",
                cloud_server=server,
            )
            
            memories = len(agent.list_memories()["memories"])
            self.assertEqual(memories, 50)
            
            states = len(agent.get_states(use_cache=False))
            self.assertEqual(states, 20)
            
            prefs = len(agent.get_preferences(use_cache=False))
            self.assertEqual(prefs, 10)
        
        total_time = time.time() - start_total
        
        print(f"\n  🏆 100 agents × 80 ops = 8,000 operations in {mixed_time:.2f}s")
        print(f"  🏆 Throughput: {8000/mixed_time:.0f} ops/sec")
        self.assertLess(mixed_time, 180)  # < 3 minutes

    def test_extremely_large_single_memory(self):
        """MEGA: Test with extremely large single memory payloads."""
        print("\n[TEST] MEGA: Extremely Large Single Memories")
        
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="huge-memory", cloud_server=server)
        
        sizes = [
            ("10KB", 10 * 1024),
            ("50KB", 50 * 1024),
            ("100KB", 100 * 1024),
        ]
        
        results = {}
        
        for name, size in sizes:
            print(f"\n  Testing {name} memory...")
            
            # Generate large payload
            large_data = "x" * size
            
            start = time.time()
            result = agent.store_memory(
                memory_id=f"huge-{name}",
                memory_type="long_term",
                content={"data": large_data},
            )
            store_time = time.time() - start
            
            self.assertEqual(result["status"], "ok")
            
            # Retrieve it back
            start = time.time()
            retrieved = agent.get_memory(f"huge-{name}")
            retrieve_time = time.time() - start
            
            self.assertEqual(retrieved["memory"]["content"]["data"], large_data)
            results[name] = {"store": store_time, "retrieve": retrieve_time}
            
            print(f"    Store: {store_time:.3f}s, Retrieve: {retrieve_time:.3f}s")
        
        print(f"\n  🏆 Large memory handling verified")
        # All should complete successfully
        self.assertTrue(all(r["store"] < 10 for r in results.values()))
    
    def test_continuous_operation_for_one_hour(self):
        """MEGA: Continuous operations simulating one hour session."""
        print("\n[TEST] MEGA: One-Hour Continuous Operations (Simulated)")
        print("  Note: Compressing time to make test manageable")
        
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(agent_id="hour-long", cloud_server=server)
        
        # Simulate 1 hour compressed into 6 cycles of 10 minutes each
        print("  → Starting 6-hour cycle simulation...")
        start_total = time.time()
        
        for cycle in range(6):
            print(f"    Cycle {cycle+1}/6: Processing...")
            
            # Each cycle: 20 tasks + knowledge accumulation
            for task in range(20):
                agent.store_memory(
                    memory_id=f"cycle{cycle}-task{task}",
                    memory_type="long_term",
                    content={
                        "cycle": cycle,
                        "task": task,
                        "duration_minutes": 10,
                    },
                    completion_score=(task + cycle) / 20,
                )
            
            # End of cycle knowledge
            agent.update_state(
                state_id=f"cycle{cycle}-summary",
                category="knowledge",
                content={
                    "completed_tasks": 20,
                    "average_completion": cycle / 6,
                },
            )
            
            # Progress bar
            progress = ((cycle + 1) / 6) * 100
            print(f"      Progress: {progress:.0f}% of simulated hour")
        
        # Final hour summary
        agent.update_state(
            state_id="hour-final-summary",
            category="knowledge",
            content={
                "total_cycles": 6,
                "total_tasks": 120,
                "final_productivity": 1.0,
            },
        )
        
        total_time = time.time() - start_total
        
        # Verify
        memories = len(agent.list_memories()["memories"])
        states = len(agent.get_states(use_cache=False))
        
        print(f"\n  🏆 Completed 120 tasks in {total_time:.2f}s")
        print(f"  🏆 Equivalent to hourly throughput: {120/(total_time/60):.1f} tasks/hr")
        
        self.assertEqual(memories, 120)
        self.assertEqual(states, 7)  # 6 cycle summaries + 1 final
    
    def test_massive_parallel_agent_creation(self):
        """MEGA: Create 1000 agents and verify complete isolation."""
        print("\n[TEST] MEGA: 1000 Agent Isolation Test")
        
        server = CNAA_MCPServer()
        
        # Create 1000 unique agents
        print("  → Creating 1,000 agents...")
        start = time.time()
        
        for i in range(1000):
            agent = LocalAgentInterface(
                agent_id=f"parallel-agent-{i:04d}",
                cloud_server=server,
            )
            # Each agent does minimal work
            agent.store_memory(
                memory_id=f"a{i:04d}-mem",
                memory_type="long_term",
                content={"unique_to": i},
            )
        
        creation_time = time.time() - start
        print(f"    Created 1000 agents in {creation_time:.2f}s")
        
        # Verify isolation: each agent sees only their own memory
        print("  → Verifying isolation for all 1000 agents...")
        verify_start = time.time()
        
        for i in range(1000):
            agent = LocalAgentInterface(
                agent_id=f"parallel-agent-{i:04d}",
                cloud_server=server,
            )
            result = agent.list_memories()
            self.assertEqual(len(result["memories"]), 1,
                           f"Agent {i} should see only 1 memory")
        
        verify_time = time.time() - verify_start
        print(f"    Verified isolation in {verify_time:.2f}s")
        print(f"    Verification rate: {1000/verify_time:.0f} agents/sec")
        
        total_agents = server.memory_store.count()
        print(f"\n  🏆 Successfully created and verified 1,000 isolated agents")
        print(f"  🏆 Total storage entries: {total_agents}")
        
        self.assertEqual(total_agents, 1000)


if __name__ == "__main__":
    # Run with -v for verbose output
    unittest.main()
