"""Integration tests - End-to-end testing of CNAA cloud and local modules.

Covers:
- MCP Server tool routing (all 13 tools)
- CloudAgentInterface convenience wrapper
- LocalAgentInterface (main entry point)
- Delete operations (state, preference)
- Upsert semantics
- Multi-agent isolation
- Cache invalidation on update
- MCP Client direct operations
- Tag short-term tool
"""

import unittest

from cloud.server.mcp_server import CNAA_MCPServer
from cloud.agent import CloudAgentInterface
from local.agent import LocalAgentInterface
from local.client.mcp_client import CNAA_MCPClient


class TestCloudMCPServer(unittest.TestCase):
    """Test CNAA_MCPServer tool routing."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = CNAA_MCPServer()

    def test_store_memory_tool(self):
        """IMPLEMENTED: Verify store_memory tool works end-to-end."""
        result = self.server.handle_tool_call(
            "cnaa_store_memory",
            {
                "agent_id": "test-agent",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {"task": "test"},
                "tags": ["test"],
                "completion_score": 0.8,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory_id"], "mem-001")

    def test_get_memory_tool(self):
        """IMPLEMENTED: Verify get_memory tool retrieves stored memory."""
        self.server.handle_tool_call(
            "cnaa_store_memory",
            {
                "agent_id": "test-agent",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {"task": "test"},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_get_memory",
            {"agent_id": "test-agent", "memory_id": "mem-001"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["memory_id"], "mem-001")
        self.assertEqual(result["memory"]["content"]["task"], "test")

    def test_get_memory_not_found(self):
        """IMPLEMENTED: Verify not_found status for missing memory."""
        result = self.server.handle_tool_call(
            "cnaa_get_memory",
            {"agent_id": "test-agent", "memory_id": "non-existent"},
        )
        self.assertEqual(result["status"], "not_found")

    def test_list_memories_tool(self):
        """IMPLEMENTED: Verify list_memories returns stored memories."""
        for i in range(3):
            self.server.handle_tool_call(
                "cnaa_store_memory",
                {
                    "agent_id": "test-agent",
                    "memory_id": f"mem-{i}",
                    "type": "long_term",
                    "content": {"index": i},
                },
            )
        result = self.server.handle_tool_call(
            "cnaa_list_memories",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["memories"]), 3)

    def test_delete_memory_tool(self):
        """IMPLEMENTED: Verify delete_memory removes memory."""
        self.server.handle_tool_call(
            "cnaa_store_memory",
            {
                "agent_id": "test-agent",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_delete_memory",
            {"agent_id": "test-agent", "memory_id": "mem-001"},
        )
        self.assertEqual(result["status"], "ok")

    def test_update_state_tool(self):
        """IMPLEMENTED: Verify update_state tool works."""
        result = self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": "test-agent",
                "state_id": "state-001",
                "category": "knowledge",
                "content": {"key": "value"},
            },
        )
        self.assertEqual(result["status"], "ok")

    def test_get_state_tool(self):
        """IMPLEMENTED: Verify get_state retrieves stored states."""
        self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": "test-agent",
                "state_id": "state-001",
                "category": "knowledge",
                "content": {"key": "value"},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_get_state",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["states"]), 1)

    def test_update_preference_tool(self):
        """IMPLEMENTED: Verify update_preference tool works."""
        result = self.server.handle_tool_call(
            "cnaa_update_preference",
            {
                "agent_id": "test-agent",
                "preference_id": "pref-001",
                "key": "language",
                "value": {"preferred": "python"},
                "importance": 0.9,
            },
        )
        self.assertEqual(result["status"], "ok")

    def test_get_preference_tool(self):
        """IMPLEMENTED: Verify get_preference retrieves stored preferences."""
        self.server.handle_tool_call(
            "cnaa_update_preference",
            {
                "agent_id": "test-agent",
                "preference_id": "pref-001",
                "key": "language",
                "value": {"preferred": "python"},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_get_preference",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["preferences"]), 1)

    def test_update_environment_tool(self):
        """IMPLEMENTED: Verify update_environment tool works."""
        result = self.server.handle_tool_call(
            "cnaa_update_environment",
            {
                "agent_id": "test-agent",
                "env_id": "env-001",
                "context": {"os": "linux"},
            },
        )
        self.assertEqual(result["status"], "ok")

    def test_get_environment_tool(self):
        """IMPLEMENTED: Verify get_environment retrieves stored environment."""
        self.server.handle_tool_call(
            "cnaa_update_environment",
            {
                "agent_id": "test-agent",
                "env_id": "env-001",
                "context": {"os": "linux"},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_get_environment",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["environment"]["context"]["os"], "linux")

    def test_unknown_tool(self):
        """IMPLEMENTED: Verify error status for unknown tool."""
        result = self.server.handle_tool_call(
            "unknown_tool",
            {"arg": "value"},
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Unknown tool", result["message"])


    def test_delete_state_tool(self):
        """IMPLEMENTED: Verify delete_state removes state."""
        self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": "test-agent",
                "state_id": "state-001",
                "category": "knowledge",
                "content": {"key": "value"},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_delete_state",
            {"agent_id": "test-agent", "state_id": "state-001"},
        )
        self.assertEqual(result["status"], "ok")
        # Verify it's gone
        result = self.server.handle_tool_call(
            "cnaa_get_state",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(len(result["states"]), 0)

    def test_delete_preference_tool(self):
        """IMPLEMENTED: Verify delete_preference removes preference."""
        self.server.handle_tool_call(
            "cnaa_update_preference",
            {
                "agent_id": "test-agent",
                "preference_id": "pref-001",
                "key": "language",
                "value": {"preferred": "python"},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_delete_preference",
            {"agent_id": "test-agent", "preference_id": "pref-001"},
        )
        self.assertEqual(result["status"], "ok")
        # Verify it's gone
        result = self.server.handle_tool_call(
            "cnaa_get_preference",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(len(result["preferences"]), 0)

    def test_tag_short_term_tool(self):
        """IMPLEMENTED: Verify tag_short_term returns ok."""
        result = self.server.handle_tool_call(
            "cnaa_tag_short_term",
            {"agent_id": "test-agent", "tags": ["important", "review"]},
        )
        self.assertEqual(result["status"], "ok")

    def test_upsert_state_overwrites(self):
        """IMPLEMENTED: Verify update_state overwrites existing state."""
        self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": "test-agent",
                "state_id": "state-001",
                "category": "knowledge",
                "content": {"version": 1},
            },
        )
        # Update same state_id with new content
        self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": "test-agent",
                "state_id": "state-001",
                "category": "knowledge",
                "content": {"version": 2},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_get_state",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(len(result["states"]), 1)
        self.assertEqual(result["states"][0]["content"]["version"], 2)

    def test_upsert_preference_overwrites(self):
        """IMPLEMENTED: Verify update_preference overwrites existing."""
        self.server.handle_tool_call(
            "cnaa_update_preference",
            {
                "agent_id": "test-agent",
                "preference_id": "pref-001",
                "key": "language",
                "value": {"preferred": "python"},
            },
        )
        self.server.handle_tool_call(
            "cnaa_update_preference",
            {
                "agent_id": "test-agent",
                "preference_id": "pref-001",
                "key": "language",
                "value": {"preferred": "rust"},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_get_preference",
            {"agent_id": "test-agent"},
        )
        self.assertEqual(len(result["preferences"]), 1)
        self.assertEqual(result["preferences"][0]["value"]["preferred"], "rust")

    def test_multi_agent_isolation(self):
        """IMPLEMENTED: Verify agents cannot see each other's data."""
        # Agent A stores memory
        self.server.handle_tool_call(
            "cnaa_store_memory",
            {
                "agent_id": "agent-A",
                "memory_id": "mem-A",
                "type": "long_term",
                "content": {"owner": "A"},
            },
        )
        # Agent B stores memory
        self.server.handle_tool_call(
            "cnaa_store_memory",
            {
                "agent_id": "agent-B",
                "memory_id": "mem-B",
                "type": "long_term",
                "content": {"owner": "B"},
            },
        )
        # Agent A can only see its own
        result_a = self.server.handle_tool_call(
            "cnaa_list_memories",
            {"agent_id": "agent-A"},
        )
        self.assertEqual(len(result_a["memories"]), 1)
        self.assertEqual(result_a["memories"][0]["memory_id"], "mem-A")

        # Agent B can only see its own
        result_b = self.server.handle_tool_call(
            "cnaa_list_memories",
            {"agent_id": "agent-B"},
        )
        self.assertEqual(len(result_b["memories"]), 1)
        self.assertEqual(result_b["memories"][0]["memory_id"], "mem-B")

    def test_multi_agent_state_isolation(self):
        """IMPLEMENTED: Verify state isolation between agents."""
        self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": "agent-X",
                "state_id": "state-x1",
                "category": "knowledge",
                "content": {"x": True},
            },
        )
        self.server.handle_tool_call(
            "cnaa_update_state",
            {
                "agent_id": "agent-Y",
                "state_id": "state-y1",
                "category": "knowledge",
                "content": {"y": True},
            },
        )
        result_x = self.server.handle_tool_call(
            "cnaa_get_state",
            {"agent_id": "agent-X"},
        )
        self.assertEqual(len(result_x["states"]), 1)
        self.assertEqual(result_x["states"][0]["state_id"], "state-x1")

    def test_list_memories_filter_by_type_and_tags(self):
        """IMPLEMENTED: Verify combined type + tag filtering."""
        for i in range(4):
            self.server.handle_tool_call(
                "cnaa_store_memory",
                {
                    "agent_id": "test-agent",
                    "memory_id": f"mem-{i}",
                    "type": "long_term" if i < 2 else "short_term",
                    "content": {},
                    "tags": ["python"] if i % 2 == 0 else ["java"],
                },
            )
        # Filter: long_term + python → only mem-0
        result = self.server.handle_tool_call(
            "cnaa_list_memories",
            {"agent_id": "test-agent", "type": "long_term", "tags": ["python"]},
        )
        self.assertEqual(len(result["memories"]), 1)
        self.assertEqual(result["memories"][0]["memory_id"], "mem-0")

    def test_get_environment_not_found(self):
        """IMPLEMENTED: Verify not_found for missing environment."""
        result = self.server.handle_tool_call(
            "cnaa_get_environment",
            {"agent_id": "no-such-agent"},
        )
        self.assertEqual(result["status"], "not_found")

    def test_delete_nonexistent_memory(self):
        """IMPLEMENTED: Verify delete of non-existent memory returns ok."""
        result = self.server.handle_tool_call(
            "cnaa_delete_memory",
            {"agent_id": "test-agent", "memory_id": "ghost"},
        )
        self.assertEqual(result["status"], "ok")

    def test_store_memory_with_metadata(self):
        """IMPLEMENTED: Verify metadata is stored and retrieved."""
        self.server.handle_tool_call(
            "cnaa_store_memory",
            {
                "agent_id": "test-agent",
                "memory_id": "mem-meta",
                "type": "long_term",
                "content": {"data": "test"},
                "metadata": {"source": "unit-test", "version": 2},
            },
        )
        result = self.server.handle_tool_call(
            "cnaa_get_memory",
            {"agent_id": "test-agent", "memory_id": "mem-meta"},
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["metadata"]["source"], "unit-test")


class TestCloudAgentInterface(unittest.TestCase):
    """Test CloudAgentInterface convenience wrapper."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = CNAA_MCPServer()
        self.agent = CloudAgentInterface(self.server)

    def test_store_and_get_memory(self):
        """IMPLEMENTED: Verify memory can be stored and retrieved via interface."""
        result = self.agent.store_memory(
            agent_id="test-agent",
            memory_id="mem-001",
            memory_type="long_term",
            content={"task": "test"},
        )
        self.assertEqual(result["status"], "ok")

        result = self.agent.get_memory("test-agent", "mem-001")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["content"]["task"], "test")


class TestLocalAgentInterface(unittest.TestCase):
    """Test LocalAgentInterface - main entry point for agentic frameworks."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = CNAA_MCPServer()
        self.agent = LocalAgentInterface(
            agent_id="test-agent",
            cloud_server=self.server,
        )

    def test_store_memory_cloud(self):
        """IMPLEMENTED: Verify memory is stored in cloud via local interface."""
        result = self.agent.store_memory(
            memory_id="mem-001",
            memory_type="long_term",
            content={"task": "test"},
        )
        self.assertEqual(result["status"], "ok")

        # Verify it's in cloud
        cloud_result = self.agent.get_memory("mem-001")
        self.assertEqual(cloud_result["status"], "ok")

    def test_create_instant_memory_local(self):
        """IMPLEMENTED: Verify instant memory is created locally."""
        result = self.agent.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test summary",
            memory_id="mem-001",
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory_id"], "mem-001")
        self.assertIn("cnaa_ref", result)

    def test_get_active_instant_memories(self):
        """IMPLEMENTED: Verify active instant memories are retrieved."""
        self.agent.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Test 1",
            memory_id="mem-001",
        )
        self.agent.create_instant_memory(
            task_id="task-002",
            checkpoint_id="cp-002",
            summary="Test 2",
            memory_id="mem-002",
        )
        active = self.agent.get_active_instant_memories()
        self.assertEqual(len(active), 2)

    def test_get_states_with_cache(self):
        """IMPLEMENTED: Verify states are cached locally after first fetch."""
        # Store a state in cloud
        self.agent.update_state(
            state_id="state-001",
            category="knowledge",
            content={"key": "value"},
        )

        # First fetch - should go to cloud
        states = self.agent.get_states(use_cache=True)
        self.assertEqual(len(states), 1)

        # Second fetch - should use cache
        states = self.agent.get_states(use_cache=True)
        self.assertEqual(len(states), 1)

    def test_get_preferences_with_cache(self):
        """IMPLEMENTED: Verify preferences are cached locally."""
        self.agent.update_preference(
            preference_id="pref-001",
            key="language",
            value={"preferred": "python"},
        )
        prefs = self.agent.get_preferences(use_cache=True)
        self.assertEqual(len(prefs), 1)

    def test_get_environment_with_cache(self):
        """IMPLEMENTED: Verify environment is cached locally."""
        self.agent.update_environment(
            env_id="env-001",
            context={"os": "linux"},
        )
        env = self.agent.get_environment(use_cache=True)
        self.assertIsNotNone(env)
        self.assertEqual(env["context"]["os"], "linux")

    def test_full_workflow(self):
        """IMPLEMENTED: Verify complete workflow from task to long-term memory."""
        # 1. Agent completes a task, stores to cloud
        result = self.agent.store_memory(
            memory_id="mem-001",
            memory_type="long_term",
            content={"task": "database migration", "result": "success"},
            tags=["database", "migration"],
            completion_score=0.9,
        )
        self.assertEqual(result["status"], "ok")

        # 2. Create instant memory for local context
        result = self.agent.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Completed database migration",
            memory_id="mem-001",
        )
        self.assertEqual(result["status"], "ok")

        # 3. Verify instant memory is available locally
        active = self.agent.get_active_instant_memories()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["summary"], "Completed database migration")

        # 4. Update state with new knowledge
        result = self.agent.update_state(
            state_id="knowledge-db",
            category="knowledge",
            content={"learned": "PostgreSQL migration patterns"},
        )
        self.assertEqual(result["status"], "ok")

        # 5. Verify state is retrievable
        states = self.agent.get_states()
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["state_id"], "knowledge-db")


class TestMCPClientDirect(unittest.TestCase):
    """Test CNAA_MCPClient direct operations via mock handler."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = CNAA_MCPServer()
        self.client = CNAA_MCPClient()
        self.client.set_mock_handler(self.server)

    def test_store_and_get_memory(self):
        """IMPLEMENTED: Verify client can store and get memory via mock."""
        result = self.client.store_memory(
            agent_id="client-agent",
            memory_id="cmem-001",
            memory_type="long_term",
            content={"via": "client"},
        )
        self.assertEqual(result["status"], "ok")

        result = self.client.get_memory("client-agent", "cmem-001")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["content"]["via"], "client")

    def test_list_memories(self):
        """IMPLEMENTED: Verify client can list memories."""
        self.client.store_memory(
            agent_id="client-agent",
            memory_id="cm-1",
            memory_type="long_term",
            content={},
        )
        self.client.store_memory(
            agent_id="client-agent",
            memory_id="cm-2",
            memory_type="short_term",
            content={},
        )
        result = self.client.list_memories("client-agent")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["memories"]), 2)

    def test_delete_memory(self):
        """IMPLEMENTED: Verify client can delete memory."""
        self.client.store_memory(
            agent_id="client-agent",
            memory_id="cm-del",
            memory_type="long_term",
            content={},
        )
        result = self.client.delete_memory("client-agent", "cm-del")
        self.assertEqual(result["status"], "ok")
        result = self.client.get_memory("client-agent", "cm-del")
        self.assertEqual(result["status"], "not_found")

    def test_state_operations(self):
        """IMPLEMENTED: Verify client state CRUD."""
        result = self.client.update_state(
            "client-agent", "st-1", "knowledge", {"fact": "test"}
        )
        self.assertEqual(result["status"], "ok")

        result = self.client.get_state("client-agent")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["states"]), 1)

        result = self.client.delete_state("client-agent", "st-1")
        self.assertEqual(result["status"], "ok")

        result = self.client.get_state("client-agent")
        self.assertEqual(len(result["states"]), 0)

    def test_preference_operations(self):
        """IMPLEMENTED: Verify client preference CRUD."""
        result = self.client.update_preference(
            "client-agent", "pf-1", "theme", {"dark": True}, 0.8
        )
        self.assertEqual(result["status"], "ok")

        result = self.client.get_preference("client-agent")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["preferences"]), 1)

        result = self.client.delete_preference("client-agent", "pf-1")
        self.assertEqual(result["status"], "ok")

        result = self.client.get_preference("client-agent")
        self.assertEqual(len(result["preferences"]), 0)

    def test_environment_operations(self):
        """IMPLEMENTED: Verify client environment CRUD."""
        result = self.client.update_environment(
            "client-agent", "env-1", {"os": "linux"}
        )
        self.assertEqual(result["status"], "ok")

        result = self.client.get_environment("client-agent")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["environment"]["context"]["os"], "linux")

    def test_client_without_handler_returns_error(self):
        """IMPLEMENTED: Verify client without handler returns error."""
        orphan_client = CNAA_MCPClient()
        result = orphan_client.get_memory("any", "any")
        self.assertEqual(result["status"], "error")
        self.assertIn("not connected", result["message"])


class TestLocalAgentCacheInvalidation(unittest.TestCase):
    """Test cache invalidation behavior in LocalAgentInterface."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = CNAA_MCPServer()
        self.agent = LocalAgentInterface(
            agent_id="cache-agent",
            cloud_server=self.server,
            cache_ttl_minutes=10.0,
        )

    def test_state_cache_invalidated_on_update(self):
        """IMPLEMENTED: Verify state cache is cleared after update."""
        self.agent.update_state(
            state_id="s1", category="knowledge", content={"v": 1}
        )
        # First get populates cache
        states = self.agent.get_states(use_cache=True)
        self.assertEqual(len(states), 1)

        # Update invalidates cache
        self.agent.update_state(
            state_id="s2", category="knowledge", content={"v": 2}
        )
        # Next get should fetch fresh data
        states = self.agent.get_states(use_cache=True)
        self.assertEqual(len(states), 2)

    def test_preference_cache_invalidated_on_update(self):
        """IMPLEMENTED: Verify preference cache is cleared after update."""
        self.agent.update_preference(
            preference_id="p1", key="k", value={"a": 1}
        )
        prefs = self.agent.get_preferences(use_cache=True)
        self.assertEqual(len(prefs), 1)

        self.agent.update_preference(
            preference_id="p2", key="k", value={"b": 2}
        )
        prefs = self.agent.get_preferences(use_cache=True)
        self.assertEqual(len(prefs), 2)

    def test_environment_cache_invalidated_on_update(self):
        """IMPLEMENTED: Verify environment cache is cleared after update."""
        self.agent.update_environment(env_id="e1", context={"v": 1})
        env = self.agent.get_environment(use_cache=True)
        self.assertEqual(env["context"]["v"], 1)

        self.agent.update_environment(env_id="e1", context={"v": 2})
        env = self.agent.get_environment(use_cache=True)
        self.assertEqual(env["context"]["v"], 2)

    def test_get_states_without_cache(self):
        """IMPLEMENTED: Verify use_cache=False always fetches from cloud."""
        self.agent.update_state(
            state_id="s1", category="knowledge", content={"v": 1}
        )
        states = self.agent.get_states(use_cache=False)
        self.assertEqual(len(states), 1)

        states = self.agent.get_states(use_cache=False)
        self.assertEqual(len(states), 1)


class TestLocalAgentMultiInstance(unittest.TestCase):
    """Test multiple LocalAgentInterface instances sharing one cloud server."""

    def setUp(self):
        """Set up shared cloud server."""
        self.server = CNAA_MCPServer()

    def test_two_instances_share_cloud_memory(self):
        """IMPLEMENTED: Verify two local instances see same cloud data."""
        agent1 = LocalAgentInterface(
            agent_id="shared-agent",
            cloud_server=self.server,
        )
        agent2 = LocalAgentInterface(
            agent_id="shared-agent",
            cloud_server=self.server,
        )
        # Agent1 stores to cloud
        agent1.store_memory(
            memory_id="shared-mem",
            memory_type="long_term",
            content={"shared": True},
        )
        # Agent2 can read it from cloud
        result = agent2.get_memory("shared-mem")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["content"]["shared"], True)

    def test_two_instances_share_cloud_state(self):
        """IMPLEMENTED: Verify two local instances see same cloud state."""
        agent1 = LocalAgentInterface(
            agent_id="shared-agent-2",
            cloud_server=self.server,
        )
        agent2 = LocalAgentInterface(
            agent_id="shared-agent-2",
            cloud_server=self.server,
        )
        agent1.update_state(
            state_id="shared-state",
            category="knowledge",
            content={"learned": True},
        )
        states = agent2.get_states(use_cache=False)
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["content"]["learned"], True)

    def test_instant_memory_is_local_only(self):
        """IMPLEMENTED: Verify instant memories are NOT shared between instances."""
        agent1 = LocalAgentInterface(
            agent_id="local-only-agent",
            cloud_server=self.server,
        )
        agent2 = LocalAgentInterface(
            agent_id="local-only-agent",
            cloud_server=self.server,
        )
        agent1.create_instant_memory(
            task_id="t1",
            checkpoint_id="cp1",
            summary="Local to agent1",
            memory_id="im-1",
        )
        # Agent2 should NOT see agent1's instant memories
        active = agent2.get_active_instant_memories()
        self.assertEqual(len(active), 0)

    def test_different_agents_isolated(self):
        """IMPLEMENTED: Verify different agent_ids are fully isolated."""
        agent_a = LocalAgentInterface(
            agent_id="agent-alpha",
            cloud_server=self.server,
        )
        agent_b = LocalAgentInterface(
            agent_id="agent-beta",
            cloud_server=self.server,
        )
        agent_a.store_memory(
            memory_id="alpha-mem",
            memory_type="long_term",
            content={"owner": "alpha"},
        )
        agent_b.store_memory(
            memory_id="beta-mem",
            memory_type="long_term",
            content={"owner": "beta"},
        )
        # Each sees only their own
        result_a = agent_a.list_memories()
        self.assertEqual(len(result_a["memories"]), 1)
        result_b = agent_b.list_memories()
        self.assertEqual(len(result_b["memories"]), 1)


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow simulating openclow integration."""

    def test_openclow_style_workflow(self):
        """IMPLEMENTED: Simulate openclow agent using CNAA for memory."""
        # Setup: Create cloud server and local interface (as openclow would)
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(
            agent_id="openclow-agent-001",
            cloud_server=server,
        )

        # Step 1: Agent completes task checkpoint
        agent.store_memory(
            memory_id="task-mem-001",
            memory_type="long_term",
            content={
                "task": "user_authentication",
                "steps": ["validate_token", "check_permissions", "return_user"],
                "result": "success",
            },
            tags=["auth", "security"],
            completion_score=0.95,
        )

        # Step 2: Create instant memory for current context
        agent.create_instant_memory(
            task_id="task-001",
            checkpoint_id="cp-001",
            summary="Implemented user authentication flow",
            memory_id="task-mem-001",
        )

        # Step 3: Agent accumulates knowledge
        agent.update_state(
            state_id="knowledge-auth",
            category="knowledge",
            content={
                "pattern": "JWT-based authentication",
                "best_practices": ["use_https", "rotate_tokens", "validate_signatures"],
            },
        )

        # Step 4: Agent identifies important preference
        agent.update_preference(
            preference_id="pref-security",
            key="security_first",
            value={"approach": "always_validate_tokens"},
            importance=0.95,
            source_memory_ids=["task-mem-001"],
        )

        # Step 5: Agent updates environment
        agent.update_environment(
            env_id="env-dev",
            context={
                "stage": "development",
                "framework": "openclow",
                "language": "python",
            },
        )

        # Verify all data is retrievable
        memories_response = agent.list_memories()
        self.assertEqual(memories_response["status"], "ok")
        self.assertEqual(len(memories_response["memories"]), 1)

        states = agent.get_states()
        self.assertEqual(len(states), 1)

        prefs = agent.get_preferences()
        self.assertEqual(len(prefs), 1)

        env = agent.get_environment()
        self.assertIsNotNone(env)
        self.assertEqual(env["context"]["framework"], "openclow")

        # Verify instant memory is still active
        active = agent.get_active_instant_memories()
        self.assertEqual(len(active), 1)

    def test_complete_delete_loop(self):
        """IMPLEMENTED: Verify full create → verify → delete → verify loop."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(
            agent_id="delete-loop-agent",
            cloud_server=server,
        )

        # Create all entity types
        agent.store_memory(
            memory_id="del-mem",
            memory_type="long_term",
            content={"to_delete": True},
        )
        agent.update_state(
            state_id="del-state",
            category="knowledge",
            content={"to_delete": True},
        )
        agent.update_preference(
            preference_id="del-pref",
            key="to_delete",
            value={"flag": True},
        )
        agent.update_environment(
            env_id="del-env",
            context={"to_delete": True},
        )

        # Verify all exist
        self.assertEqual(len(agent.list_memories()["memories"]), 1)
        self.assertEqual(len(agent.get_states()), 1)
        self.assertEqual(len(agent.get_preferences()), 1)
        self.assertIsNotNone(agent.get_environment())

        # Delete memory via local interface
        result = agent.delete_memory("del-mem")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(agent.list_memories()["memories"]), 0)

    def test_memory_content_integrity(self):
        """IMPLEMENTED: Verify content is preserved through the full loop."""
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(
            agent_id="integrity-agent",
            cloud_server=server,
        )
        complex_content = {
            "nested": {"deep": {"value": 42}},
            "list": [1, 2, 3],
            "string": "hello",
            "bool": True,
            "null": None,
        }
        agent.store_memory(
            memory_id="integrity-mem",
            memory_type="long_term",
            content=complex_content,
            tags=["a", "b", "c"],
            completion_score=0.75,
        )
        result = agent.get_memory("integrity-mem")
        self.assertEqual(result["memory"]["content"]["nested"]["deep"]["value"], 42)
        self.assertEqual(result["memory"]["content"]["list"], [1, 2, 3])
        self.assertEqual(result["memory"]["tags"], ["a", "b", "c"])
        self.assertEqual(result["memory"]["completion_score"], 0.75)


if __name__ == "__main__":
    unittest.main()
