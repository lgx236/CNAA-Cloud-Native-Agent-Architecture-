"""Integration tests - End-to-end testing of CNAA cloud and local modules."""

import unittest

from cloud.server.mcp_server import CNAA_MCPServer
from cloud.agent import CloudAgentInterface
from local.agent import LocalAgentInterface


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


if __name__ == "__main__":
    unittest.main()
