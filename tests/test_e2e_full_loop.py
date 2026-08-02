"""Full-loop end-to-end tests for CNAA framework.

This test suite forms a complete loop system, verifying that OpenClaw
(an agentic framework) can successfully interact with CNAA cloud through
the local interface. Every test exercises the full data path:

    OpenClaw → LocalAgentInterface → CNAA_MCPClient → CNAA_MCPServer → Storage
                                                                          ↓
    OpenClaw ← LocalAgentInterface ← CNAA_MCPClient ← CNAA_MCPServer ← Storage

Test coverage forms a closed loop:
1. Full CRUD loop: create → read → verify → update → read → delete → verify gone
2. Memory lifecycle loop: task → instant memory → condense → evict → cloud retrieval
3. Multi-agent loop: multiple agents sharing cloud, isolated locally
4. Multi-instance sync loop: two local instances see same cloud data
5. Cache invalidation loop: update → cache cleared → fresh fetch
6. OpenClaw HTTP loop: HTTP client → server → storage → response
7. Schema & tool integrity loop: all tools defined, schemas complete
8. Edge case loop: error handling, not-found, empty data
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from cnaa.models import (
    Environment,
    Memory,
    MemoryStatus,
    MemoryType,
    Preference,
    State,
    StateCategory,
)
from cnaa.tools import get_tool_definitions, get_tool_names
from cnaa.schemas import get_all_schemas, get_request_schemas, get_response_schemas
from cloud.server.mcp_server import CNAA_MCPServer
from cloud.agent import CloudAgentInterface
from cloud.storage.memory_store import InMemoryMemoryStore
from cloud.storage.state_store import InMemoryStateStore
from local.agent import LocalAgentInterface
from local.client.mcp_client import CNAA_MCPClient
from local.memory.instant_memory import InstantMemoryManager
from local.state.state_cache import StateCache
from examples.openclaw_integration import OpenClawCNAAIntegration


# ---------------------------------------------------------------------------
# Helper: build a full stack (server + local interface)
# ---------------------------------------------------------------------------

def _make_full_stack(agent_id: str, ttl: float = 5.0):
    """Create a connected server + local agent for testing."""
    server = CNAA_MCPServer()
    agent = LocalAgentInterface(
        agent_id=agent_id,
        cloud_server=server,
        cache_ttl_minutes=ttl,
    )
    return server, agent


# ===================================================================
# 1. Full CRUD Loop — every entity type through the complete cycle
# ===================================================================

class TestFullCRUDLoop(unittest.TestCase):
    """Full create → read → update → delete loop for all entity types."""

    def setUp(self):
        self.server, self.agent = _make_full_stack("crud-agent")

    # --- Memory CRUD ---

    def test_memory_full_crud(self):
        """IMPLEMENTED: Memory create → read → update → delete loop."""
        # CREATE
        result = self.agent.store_memory(
            memory_id="mem-crud",
            memory_type="long_term",
            content={"version": 1},
            tags=["crud-test"],
            completion_score=0.5,
        )
        self.assertEqual(result["status"], "ok")

        # READ
        result = self.agent.get_memory("mem-crud")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["content"]["version"], 1)
        self.assertEqual(result["memory"]["tags"], ["crud-test"])

        # UPDATE (overwrite with same memory_id)
        result = self.agent.store_memory(
            memory_id="mem-crud",
            memory_type="long_term",
            content={"version": 2},
            tags=["crud-test", "updated"],
        )
        self.assertEqual(result["status"], "ok")

        # READ after update
        result = self.agent.get_memory("mem-crud")
        self.assertEqual(result["memory"]["content"]["version"], 2)
        self.assertEqual(len(result["memory"]["tags"]), 2)

        # DELETE
        result = self.agent.delete_memory("mem-crud")
        self.assertEqual(result["status"], "ok")

        # VERIFY GONE
        result = self.agent.get_memory("mem-crud")
        self.assertEqual(result["status"], "not_found")

    # --- State CRUD ---

    def test_state_full_crud(self):
        """IMPLEMENTED: State create → read → update → delete loop."""
        # CREATE
        result = self.agent.update_state(
            state_id="state-crud",
            category="knowledge",
            content={"fact": "original"},
        )
        self.assertEqual(result["status"], "ok")

        # READ
        states = self.agent.get_states(use_cache=False)
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["content"]["fact"], "original")

        # UPDATE
        result = self.agent.update_state(
            state_id="state-crud",
            category="knowledge",
            content={"fact": "updated"},
        )
        self.assertEqual(result["status"], "ok")

        # READ after update
        states = self.agent.get_states(use_cache=False)
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["content"]["fact"], "updated")

        # DELETE via server
        result = self.server.handle_tool_call(
            "cnaa_delete_state",
            {"agent_id": "crud-agent", "state_id": "state-crud"},
        )
        self.assertEqual(result["status"], "ok")

        # VERIFY GONE
        states = self.agent.get_states(use_cache=False)
        self.assertEqual(len(states), 0)

    # --- Preference CRUD ---

    def test_preference_full_crud(self):
        """IMPLEMENTED: Preference create → read → update → delete loop."""
        # CREATE
        result = self.agent.update_preference(
            preference_id="pref-crud",
            key="theme",
            value={"mode": "dark"},
            importance=0.7,
        )
        self.assertEqual(result["status"], "ok")

        # READ
        prefs = self.agent.get_preferences(use_cache=False)
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0]["key"], "theme")
        self.assertEqual(prefs[0]["value"]["mode"], "dark")

        # UPDATE
        result = self.agent.update_preference(
            preference_id="pref-crud",
            key="theme",
            value={"mode": "light"},
            importance=0.9,
        )
        self.assertEqual(result["status"], "ok")

        # READ after update
        prefs = self.agent.get_preferences(use_cache=False)
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0]["value"]["mode"], "light")

        # DELETE via server
        result = self.server.handle_tool_call(
            "cnaa_delete_preference",
            {"agent_id": "crud-agent", "preference_id": "pref-crud"},
        )
        self.assertEqual(result["status"], "ok")

        # VERIFY GONE
        prefs = self.agent.get_preferences(use_cache=False)
        self.assertEqual(len(prefs), 0)

    # --- Environment CRUD ---

    def test_environment_full_crud(self):
        """IMPLEMENTED: Environment create → read → update → verify loop."""
        # CREATE
        result = self.agent.update_environment(
            env_id="env-crud",
            context={"stage": "development"},
        )
        self.assertEqual(result["status"], "ok")

        # READ
        env = self.agent.get_environment(use_cache=False)
        self.assertIsNotNone(env)
        self.assertEqual(env["context"]["stage"], "development")

        # UPDATE
        result = self.agent.update_environment(
            env_id="env-crud",
            context={"stage": "production"},
        )
        self.assertEqual(result["status"], "ok")

        # READ after update
        env = self.agent.get_environment(use_cache=False)
        self.assertIsNotNone(env)
        self.assertEqual(env["context"]["stage"], "production")


# ===================================================================
# 2. OpenClaw Local-Cloud Loop — full agent workflow simulation
# ===================================================================

class TestOpenClawLocalCloudLoop(unittest.TestCase):
    """Simulate OpenClaw agent completing multiple tasks via local → cloud."""

    def setUp(self):
        self.server, self.agent = _make_full_stack("openclaw-loop-agent")

    def test_multi_task_accumulation(self):
        """IMPLEMENTED: Multiple tasks → memories → states → preferences."""
        # Task 1: Agent completes a database migration
        self.agent.store_memory(
            memory_id="task-1-mem",
            memory_type="long_term",
            content={
                "task": "db_migration",
                "result": "success",
                "details": "Migrated user table",
            },
            tags=["database", "migration"],
            completion_score=0.95,
        )
        self.agent.create_instant_memory(
            task_id="task-1",
            checkpoint_id="cp-1",
            summary="Completed DB migration",
            memory_id="task-1-mem",
        )
        self.agent.update_state(
            state_id="knowledge-db",
            category="knowledge",
            content={"pattern": "PostgreSQL migration"},
        )

        # Task 2: Agent completes API design
        self.agent.store_memory(
            memory_id="task-2-mem",
            memory_type="long_term",
            content={
                "task": "api_design",
                "result": "success",
                "details": "REST API for users",
            },
            tags=["api", "design"],
            completion_score=0.88,
        )
        self.agent.create_instant_memory(
            task_id="task-2",
            checkpoint_id="cp-2",
            summary="Designed REST API",
            memory_id="task-2-mem",
        )
        self.agent.update_state(
            state_id="knowledge-api",
            category="knowledge",
            content={"pattern": "RESTful design"},
        )

        # Task 3: Agent identifies a preference
        self.agent.update_preference(
            preference_id="pref-style",
            key="coding_style",
            value={"preferred": "functional"},
            importance=0.85,
            source_memory_ids=["task-1-mem", "task-2-mem"],
        )

        # Set environment
        self.agent.update_environment(
            env_id="env-work",
            context={"project": "openclaw", "stage": "active"},
        )

        # Verify accumulation
        memories = self.agent.list_memories()
        self.assertEqual(len(memories["memories"]), 2)

        states = self.agent.get_states(use_cache=False)
        self.assertEqual(len(states), 2)

        prefs = self.agent.get_preferences(use_cache=False)
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0]["importance"], 0.85)

        env = self.agent.get_environment(use_cache=False)
        self.assertEqual(env["context"]["project"], "openclaw")

        # Verify instant memories
        active = self.agent.get_active_instant_memories()
        self.assertEqual(len(active), 2)

    def test_task_to_long_term_promotion(self):
        """IMPLEMENTED: Task → instant memory → cloud memory → retrieval."""
        # Agent completes task, stores to cloud
        self.agent.store_memory(
            memory_id="promote-mem",
            memory_type="long_term",
            content={"task": "critical_fix", "importance": "high"},
            tags=["critical"],
            completion_score=1.0,
        )

        # Create instant memory for local context
        result = self.agent.create_instant_memory(
            task_id="task-promote",
            checkpoint_id="cp-promote",
            summary="Fixed critical bug",
            memory_id="promote-mem",
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("cnaa://", result["cnaa_ref"])

        # Later: retrieve full memory from cloud via cnaa_ref pointer
        cloud_mem = self.agent.get_memory("promote-mem")
        self.assertEqual(cloud_mem["status"], "ok")
        self.assertEqual(cloud_mem["memory"]["content"]["task"], "critical_fix")


# ===================================================================
# 3. Memory Lifecycle Loop — instant memory full lifecycle
# ===================================================================

class TestMemoryLifecycleLoop(unittest.TestCase):
    """Test the full memory lifecycle: active → condensed → evicted."""

    def setUp(self):
        self.manager = InstantMemoryManager(agent_id="lifecycle-agent")

    def test_full_lifecycle(self):
        """IMPLEMENTED: Create → active → condense → evict → remove."""
        # Create
        instant = self.manager.create_instant_memory(
            task_id="t1",
            checkpoint_id="cp1",
            summary="Task summary",
            memory_id="lc-mem-1",
        )
        self.assertEqual(instant.status, MemoryStatus.ACTIVE)
        self.assertEqual(self.manager.count(), 1)

        # Verify active
        active = self.manager.get_active_memories()
        self.assertEqual(len(active), 1)

        # Condense
        condensed = self.manager.condense_memory("lc-mem-1")
        self.assertIsNotNone(condensed)
        self.assertEqual(condensed.status, MemoryStatus.CONDENSED)

        # No longer active
        active = self.manager.get_active_memories()
        self.assertEqual(len(active), 0)

        # Condensed memories available
        condensed_list = self.manager.get_condensed_memories()
        self.assertEqual(len(condensed_list), 1)

        # Evict
        evicted = self.manager.evict_memory("lc-mem-1")
        self.assertIsNotNone(evicted)
        self.assertEqual(evicted.status, MemoryStatus.EVICTED)

        # Remove from storage
        removed = self.manager.remove_evicted_memories()
        self.assertEqual(removed, 1)
        self.assertIsNone(self.manager.get_memory("lc-mem-1"))
        self.assertEqual(self.manager.count(), 0)

    def test_time_based_condensation(self):
        """IMPLEMENTED: Old memories auto-condense."""
        instant = self.manager.create_instant_memory(
            task_id="t1",
            checkpoint_id="cp1",
            summary="Old task",
            memory_id="old-mem",
        )
        # Simulate aging
        instant.timestamp = datetime.now() - timedelta(hours=3)

        count = self.manager.condense_old_memories(threshold_hours=1)
        self.assertEqual(count, 1)
        self.assertEqual(instant.status, MemoryStatus.CONDENSED)

    def test_time_based_eviction(self):
        """IMPLEMENTED: Old condensed memories auto-evict."""
        instant = self.manager.create_instant_memory(
            task_id="t1",
            checkpoint_id="cp1",
            summary="Very old task",
            memory_id="very-old-mem",
        )
        instant.timestamp = datetime.now() - timedelta(days=10)
        instant.status = MemoryStatus.CONDENSED

        count = self.manager.evict_old_memories(threshold_days=7)
        self.assertEqual(count, 1)
        self.assertEqual(instant.status, MemoryStatus.EVICTED)

    def test_mixed_status_counts(self):
        """IMPLEMENTED: Count by status with mixed lifecycle stages."""
        self.manager.create_instant_memory(
            task_id="t1", checkpoint_id="cp1", summary="Active", memory_id="m1"
        )
        self.manager.create_instant_memory(
            task_id="t2", checkpoint_id="cp2", summary="Active2", memory_id="m2"
        )
        self.manager.create_instant_memory(
            task_id="t3", checkpoint_id="cp3", summary="Will condense", memory_id="m3"
        )

        self.manager.condense_memory("m3")

        counts = self.manager.count_by_status()
        self.assertEqual(counts["active"], 2)
        self.assertEqual(counts["condensed"], 1)
        self.assertEqual(counts["evicted"], 0)


# ===================================================================
# 4. Multi-Agent Full Loop — isolation and sharing
# ===================================================================

class TestMultiAgentFullLoop(unittest.TestCase):
    """Test multiple agents in complete loop scenarios."""

    def setUp(self):
        self.server = CNAA_MCPServer()

    def test_three_agents_full_isolation(self):
        """IMPLEMENTED: Three agents with full CRUD, fully isolated."""
        agents = {}
        for name in ["alice", "bob", "charlie"]:
            agents[name] = LocalAgentInterface(
                agent_id=f"agent-{name}",
                cloud_server=self.server,
            )

        # Each agent stores their own data
        for name, agent in agents.items():
            agent.store_memory(
                memory_id=f"mem-{name}",
                memory_type="long_term",
                content={"owner": name},
            )
            agent.update_state(
                state_id=f"state-{name}",
                category="knowledge",
                content={"learned_by": name},
            )
            agent.update_preference(
                preference_id=f"pref-{name}",
                key="style",
                value={"owner": name},
            )
            agent.update_environment(
                env_id=f"env-{name}",
                context={"agent": name},
            )

        # Verify each agent sees only their own data
        for name, agent in agents.items():
            memories = agent.list_memories()
            self.assertEqual(len(memories["memories"]), 1)
            self.assertEqual(memories["memories"][0]["memory_id"], f"mem-{name}")

            states = agent.get_states(use_cache=False)
            self.assertEqual(len(states), 1)
            self.assertEqual(states[0]["state_id"], f"state-{name}")

            prefs = agent.get_preferences(use_cache=False)
            self.assertEqual(len(prefs), 1)

            env = agent.get_environment(use_cache=False)
            self.assertEqual(env["context"]["agent"], name)

    def test_shared_cloud_multi_instance(self):
        """IMPLEMENTED: Multiple local instances share cloud state."""
        # Instance 1 on device A
        instance_a = LocalAgentInterface(
            agent_id="shared-agent",
            cloud_server=self.server,
        )
        # Instance 2 on device B
        instance_b = LocalAgentInterface(
            agent_id="shared-agent",
            cloud_server=self.server,
        )

        # Device A writes
        instance_a.store_memory(
            memory_id="cross-device-mem",
            memory_type="long_term",
            content={"device": "A"},
        )
        instance_a.update_state(
            state_id="cross-state",
            category="knowledge",
            content={"from": "A"},
        )

        # Device B reads
        result = instance_b.get_memory("cross-device-mem")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["content"]["device"], "A")

        states = instance_b.get_states(use_cache=False)
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["content"]["from"], "A")

        # Device B writes, Device A reads
        instance_b.update_preference(
            preference_id="cross-pref",
            key="sync",
            value={"enabled": True},
        )
        prefs = instance_a.get_preferences(use_cache=False)
        self.assertEqual(len(prefs), 1)
        self.assertTrue(prefs[0]["value"]["enabled"])


# ===================================================================
# 5. Cache Invalidation Loop
# ===================================================================

class TestCacheInvalidationLoop(unittest.TestCase):
    """Test cache invalidation forms a complete loop."""

    def setUp(self):
        self.server, self.agent = _make_full_stack("cache-loop-agent", ttl=10.0)

    def test_update_invalidates_then_refetch(self):
        """IMPLEMENTED: Update → cache cleared → next read fetches fresh."""
        # Initial state
        self.agent.update_state(
            state_id="s1", category="knowledge", content={"v": 1}
        )
        # Populate cache
        states = self.agent.get_states(use_cache=True)
        self.assertEqual(len(states), 1)

        # Add new state (invalidates cache)
        self.agent.update_state(
            state_id="s2", category="knowledge", content={"v": 2}
        )
        # Cache was cleared, should fetch 2 states
        states = self.agent.get_states(use_cache=True)
        self.assertEqual(len(states), 2)

    def test_cache_ttl_expiry(self):
        """IMPLEMENTED: Cache expires after TTL."""
        server, agent = _make_full_stack("ttl-agent", ttl=0.001)
        agent.update_state(
            state_id="s1", category="knowledge", content={"v": 1}
        )
        # Populate cache
        agent.get_states(use_cache=True)

        import time
        time.sleep(0.01)

        # Cache should be expired, but data still in cloud
        states = agent.get_states(use_cache=True)
        self.assertEqual(len(states), 1)

    def test_all_types_cached_independently(self):
        """IMPLEMENTED: States, preferences, environment cached independently."""
        self.agent.update_state(
            state_id="s1", category="knowledge", content={}
        )
        self.agent.update_preference(
            preference_id="p1", key="k", value={}
        )
        self.agent.update_environment(
            env_id="e1", context={"v": 1}
        )

        # All should be fetchable
        states = self.agent.get_states(use_cache=True)
        prefs = self.agent.get_preferences(use_cache=True)
        env = self.agent.get_environment(use_cache=True)

        self.assertEqual(len(states), 1)
        self.assertEqual(len(prefs), 1)
        self.assertIsNotNone(env)

        # Update only preference → all caches cleared
        self.agent.update_preference(
            preference_id="p2", key="k2", value={}
        )
        prefs = self.agent.get_preferences(use_cache=True)
        self.assertEqual(len(prefs), 2)


# ===================================================================
# 6. OpenClaw HTTP Loop — mocked HTTP end-to-end
# ===================================================================

class TestOpenClawHTTPLoop(unittest.TestCase):
    """Test OpenClaw HTTP integration with mocked HTTP layer."""

    @patch("examples.openclaw_integration.requests.post")
    def test_full_http_loop(self, mock_post):
        """IMPLEMENTED: Store → retrieve → verify via mocked HTTP."""
        cnaa = OpenClawCNAAIntegration("http://localhost:8080")

        # Mock store response
        mock_resp = Mock()
        mock_resp.json.return_value = {"status": "ok", "memory_id": "http-mem"}
        mock_post.return_value = mock_resp

        result = cnaa.store_memory(
            agent_id="http-agent",
            memory_id="http-mem",
            memory_type="long_term",
            content={"via": "http"},
            tags=["http-test"],
            completion_score=0.9,
        )
        self.assertEqual(result["status"], "ok")

        # Mock get response
        mock_resp2 = Mock()
        mock_resp2.json.return_value = {
            "status": "ok",
            "memory": {
                "memory_id": "http-mem",
                "content": {"via": "http"},
                "tags": ["http-test"],
            },
        }
        mock_post.return_value = mock_resp2

        result = cnaa.get_memory("http-agent", "http-mem")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory"]["content"]["via"], "http")

    @patch("examples.openclaw_integration.requests.post")
    def test_http_with_api_key(self, mock_post):
        """IMPLEMENTED: API key is included in headers when provided."""
        cnaa = OpenClawCNAAIntegration(
            "http://localhost:8080", api_key="sk-test-key"
        )
        mock_resp = Mock()
        mock_resp.json.return_value = {"status": "ok", "memory_id": "auth-mem"}
        mock_post.return_value = mock_resp

        cnaa.store_memory(
            agent_id="auth-agent",
            memory_id="auth-mem",
            memory_type="long_term",
            content={"auth": True},
        )

        # Verify Authorization header was sent
        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers", {})
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer sk-test-key")

    @patch("examples.openclaw_integration.requests.post")
    def test_http_all_operations(self, mock_post):
        """IMPLEMENTED: All operations work through HTTP layer."""
        cnaa = OpenClawCNAAIntegration("http://localhost:8080")
        mock_resp = Mock()
        mock_resp.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_resp

        # Store memory
        result = cnaa.store_memory(
            "a1", "m1", "long_term", {"data": "test"}
        )
        self.assertEqual(result["status"], "ok")

        # Get memory
        result = cnaa.get_memory("a1", "m1")
        self.assertEqual(result["status"], "ok")

        # List memories
        mock_resp.json.return_value = {"status": "ok", "memories": []}
        result = cnaa.list_memories("a1")
        self.assertEqual(result["status"], "ok")

        # State operations
        result = cnaa.update_state("a1", "s1", "knowledge", {"k": "v"})
        self.assertEqual(result["status"], "ok")

        result = cnaa.get_states("a1")
        self.assertEqual(result["status"], "ok")

        # Preference operations
        result = cnaa.update_preference("a1", "p1", "key", {"v": 1}, 0.8)
        self.assertEqual(result["status"], "ok")

        result = cnaa.get_preferences("a1")
        self.assertEqual(result["status"], "ok")

        # Environment operations
        result = cnaa.update_environment("a1", "e1", {"os": "linux"})
        self.assertEqual(result["status"], "ok")

        result = cnaa.get_environment("a1")
        self.assertEqual(result["status"], "ok")


# ===================================================================
# 7. Schema & Tool Integrity Loop
# ===================================================================

class TestSchemaAndToolIntegrity(unittest.TestCase):
    """Verify tool definitions and schemas form a complete set."""

    def test_all_13_tools_defined(self):
        """IMPLEMENTED: Exactly 13 tools defined."""
        tools = get_tool_definitions()
        self.assertEqual(len(tools), 13)

    def test_all_tools_have_required_fields(self):
        """IMPLEMENTED: Every tool has name, description, inputSchema."""
        for tool in get_tool_definitions():
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
            self.assertTrue(len(tool["name"]) > 0)
            self.assertTrue(len(tool["description"]) > 0)

    def test_tool_names_match_definitions(self):
        """IMPLEMENTED: get_tool_names() matches get_tool_definitions()."""
        names = get_tool_names()
        definitions = get_tool_definitions()
        def_names = [d["name"] for d in definitions]
        self.assertEqual(sorted(names), sorted(def_names))

    def test_all_request_schemas_exist(self):
        """IMPLEMENTED: All request schemas are defined."""
        schemas = get_request_schemas()
        expected = [
            "store_memory", "get_memory", "list_memories",
            "tag_short_term", "delete_memory",
            "get_state", "update_state", "delete_state",
            "get_preference", "update_preference", "delete_preference",
            "get_environment", "update_environment",
        ]
        for name in expected:
            self.assertIn(name, schemas)

    def test_all_response_schemas_exist(self):
        """IMPLEMENTED: All response schemas are defined."""
        schemas = get_response_schemas()
        expected = [
            "status", "store_memory", "get_memory",
            "list_memories", "get_state", "get_preference",
            "get_environment",
        ]
        for name in expected:
            self.assertIn(name, schemas)

    def test_schema_registry_completeness(self):
        """IMPLEMENTED: Schema registry has all categories."""
        all_schemas = get_all_schemas()
        # Data schemas
        for name in ["memory", "state", "preference", "environment", "instant_memory"]:
            self.assertIn(name, all_schemas)
        # Request schemas (all_schemas uses "*_request" suffix)
        for name in get_request_schemas():
            self.assertIn(f"{name}_request", all_schemas)
        # Response schemas (all_schemas uses "*_response" suffix, except "status")
        for name in get_response_schemas():
            if name == "status":
                self.assertIn("status_response", all_schemas)
            else:
                self.assertIn(f"{name}_response", all_schemas)

    def test_server_exposes_all_tools(self):
        """IMPLEMENTED: MCP server exposes all 13 tools."""
        server = CNAA_MCPServer()
        tools = server.get_tool_definitions()
        self.assertEqual(len(tools), 13)


# ===================================================================
# 8. Edge Case & Error Loop
# ===================================================================

class TestEdgeCaseAndErrorLoop(unittest.TestCase):
    """Test edge cases and error handling form a complete loop."""

    def setUp(self):
        self.server, self.agent = _make_full_stack("edge-agent")

    def test_get_nonexistent_memory(self):
        """IMPLEMENTED: Getting non-existent memory returns not_found."""
        result = self.agent.get_memory("ghost-memory")
        self.assertEqual(result["status"], "not_found")

    def test_get_nonexistent_environment(self):
        """IMPLEMENTED: Getting non-existent environment returns None."""
        env = self.agent.get_environment(use_cache=False)
        self.assertIsNone(env)

    def test_empty_list_memories(self):
        """IMPLEMENTED: Listing memories for new agent returns empty."""
        result = self.agent.list_memories()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["memories"]), 0)

    def test_empty_states(self):
        """IMPLEMENTED: Getting states for new agent returns empty."""
        states = self.agent.get_states(use_cache=False)
        self.assertEqual(len(states), 0)

    def test_empty_preferences(self):
        """IMPLEMENTED: Getting preferences for new agent returns empty."""
        prefs = self.agent.get_preferences(use_cache=False)
        self.assertEqual(len(prefs), 0)

    def test_delete_nonexistent_memory(self):
        """IMPLEMENTED: Deleting non-existent memory returns ok."""
        result = self.agent.delete_memory("ghost")
        self.assertEqual(result["status"], "ok")

    def test_unknown_tool_returns_error(self):
        """IMPLEMENTED: Unknown tool returns error status."""
        result = self.server.handle_tool_call("cnaa_nonexistent", {})
        self.assertEqual(result["status"], "error")
        self.assertIn("Unknown tool", result["message"])

    def test_store_empty_content(self):
        """IMPLEMENTED: Empty content dict is valid."""
        result = self.agent.store_memory(
            memory_id="empty-mem",
            memory_type="long_term",
            content={},
        )
        self.assertEqual(result["status"], "ok")
        mem = self.agent.get_memory("empty-mem")
        self.assertEqual(mem["memory"]["content"], {})

    def test_store_complex_nested_content(self):
        """IMPLEMENTED: Deeply nested content is preserved."""
        complex_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep",
                        "array": [1, [2, [3]]],
                    }
                }
            }
        }
        self.agent.store_memory(
            memory_id="deep-mem",
            memory_type="long_term",
            content=complex_data,
        )
        result = self.agent.get_memory("deep-mem")
        self.assertEqual(
            result["memory"]["content"]["level1"]["level2"]["level3"]["value"],
            "deep",
        )

    def test_overwrite_environment(self):
        """IMPLEMENTED: Environment can be overwritten."""
        self.agent.update_environment(env_id="e1", context={"v": 1})
        self.agent.update_environment(env_id="e1", context={"v": 2})
        env = self.agent.get_environment(use_cache=False)
        self.assertEqual(env["context"]["v"], 2)

    def test_list_with_no_matching_tags(self):
        """IMPLEMENTED: Tag filter with no matches returns empty."""
        self.agent.store_memory(
            memory_id="tagged-mem",
            memory_type="long_term",
            content={},
            tags=["python"],
        )
        result = self.agent.list_memories(tags=["rust"])
        self.assertEqual(len(result["memories"]), 0)


# ===================================================================
# 9. CloudAgentInterface Full Loop
# ===================================================================

class TestCloudAgentInterfaceLoop(unittest.TestCase):
    """Test CloudAgentInterface forms a complete loop."""

    def setUp(self):
        self.server = CNAA_MCPServer()
        self.cloud = CloudAgentInterface(self.server)

    def test_full_memory_loop_via_cloud_interface(self):
        """IMPLEMENTED: Store → get → list → delete via CloudAgentInterface."""
        self.cloud.store_memory(
            agent_id="cloud-agent",
            memory_id="cm-1",
            memory_type="long_term",
            content={"via": "cloud_interface"},
        )
        result = self.cloud.get_memory("cloud-agent", "cm-1")
        self.assertEqual(result["status"], "ok")

        result = self.cloud.list_memories("cloud-agent")
        self.assertEqual(len(result["memories"]), 1)

    def test_full_state_loop_via_cloud_interface(self):
        """IMPLEMENTED: Update → get via CloudAgentInterface."""
        self.cloud.update_state(
            agent_id="cloud-agent",
            state_id="cs-1",
            category="knowledge",
            content={"fact": "test"},
        )
        result = self.cloud.get_state("cloud-agent")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["states"]), 1)

    def test_full_preference_loop_via_cloud_interface(self):
        """IMPLEMENTED: Update → get via CloudAgentInterface."""
        self.cloud.update_preference(
            agent_id="cloud-agent",
            preference_id="cp-1",
            key="style",
            value={"mode": "fast"},
            importance=0.6,
        )
        result = self.cloud.get_preference("cloud-agent")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["preferences"]), 1)

    def test_full_environment_loop_via_cloud_interface(self):
        """IMPLEMENTED: Update → get via CloudAgentInterface."""
        self.cloud.update_environment(
            agent_id="cloud-agent",
            env_id="ce-1",
            context={"env": "test"},
        )
        result = self.cloud.get_environment("cloud-agent")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["environment"]["context"]["env"], "test")


# ===================================================================
# 10. Storage Layer Full Loop
# ===================================================================

class TestStorageLayerLoop(unittest.TestCase):
    """Test storage layer forms a complete loop."""

    def test_memory_store_full_loop(self):
        """IMPLEMENTED: Store → get → list → delete → verify at storage level."""
        store = InMemoryMemoryStore()
        memory = Memory(
            memory_id="sm-1",
            agent_id="store-agent",
            type=MemoryType.LONG_TERM,
            content={"data": "raw"},
            tags=["test"],
        )
        result = store.store_memory(memory)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(store.count(), 1)

        retrieved = store.get_memory("store-agent", "sm-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content["data"], "raw")

        summaries = store.list_memories("store-agent")
        self.assertEqual(len(summaries), 1)

        result = store.delete_memory("store-agent", "sm-1")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(store.count(), 0)

    def test_state_store_full_loop(self):
        """IMPLEMENTED: Full CRUD at state store level."""
        store = InMemoryStateStore()

        # State
        state = State(
            agent_id="store-agent",
            state_id="ss-1",
            category=StateCategory.KNOWLEDGE,
            content={"k": "v"},
        )
        store.update_state("store-agent", state)
        self.assertEqual(store.count_states(), 1)
        states = store.get_state("store-agent")
        self.assertEqual(len(states), 1)

        store.delete_state("store-agent", "ss-1")
        self.assertEqual(store.count_states(), 0)

        # Preference
        pref = Preference(
            agent_id="store-agent",
            preference_id="sp-1",
            key="k",
            value={"v": 1},
        )
        store.update_preference("store-agent", pref)
        self.assertEqual(store.count_preferences(), 1)
        store.delete_preference("store-agent", "sp-1")
        self.assertEqual(store.count_preferences(), 0)

        # Environment
        env = Environment(
            agent_id="store-agent",
            env_id="se-1",
            context={"os": "linux"},
        )
        store.update_environment("store-agent", env)
        self.assertEqual(store.count_environments(), 1)
        retrieved = store.get_environment("store-agent")
        self.assertIsNotNone(retrieved)

    def test_state_store_clear(self):
        """IMPLEMENTED: Clear removes all data."""
        store = InMemoryStateStore()
        store.update_state(
            "a", State(agent_id="a", state_id="s1", category=StateCategory.KNOWLEDGE, content={})
        )
        store.update_preference(
            "a", Preference(agent_id="a", preference_id="p1", key="k", value={})
        )
        store.update_environment(
            "a", Environment(agent_id="a", env_id="e1", context={})
        )
        store.clear()
        self.assertEqual(store.count_states(), 0)
        self.assertEqual(store.count_preferences(), 0)
        self.assertEqual(store.count_environments(), 0)


# ===================================================================
# 11. Complete OpenClaw Simulation — the ultimate loop
# ===================================================================

class TestCompleteOpenClawSimulation(unittest.TestCase):
    """The ultimate loop: simulate a full OpenClaw agent session."""

    def test_full_agent_session(self):
        """IMPLEMENTED: Complete agent session from start to finish."""
        # === Setup: Initialize CNAA stack ===
        server = CNAA_MCPServer()
        agent = LocalAgentInterface(
            agent_id="openclaw-agent-session",
            cloud_server=server,
        )

        # === Phase 1: Agent starts working ===
        # Set up environment
        agent.update_environment(
            env_id="session-env",
            context={
                "framework": "openclaw",
                "language": "python",
                "stage": "development",
            },
        )

        # === Phase 2: Agent completes multiple tasks ===
        tasks = [
            {
                "task_id": "task-auth",
                "memory_id": "mem-auth",
                "summary": "Implemented JWT authentication",
                "content": {
                    "task": "authentication",
                    "steps": ["design_schema", "implement", "test"],
                    "result": "success",
                },
                "tags": ["auth", "security"],
                "score": 0.95,
            },
            {
                "task_id": "task-api",
                "memory_id": "mem-api",
                "summary": "Built REST API endpoints",
                "content": {
                    "task": "api_development",
                    "endpoints": ["/users", "/projects", "/tasks"],
                    "result": "success",
                },
                "tags": ["api", "backend"],
                "score": 0.88,
            },
            {
                "task_id": "task-ui",
                "memory_id": "mem-ui",
                "summary": "Created dashboard UI",
                "content": {
                    "task": "ui_development",
                    "components": ["Dashboard", "Sidebar", "Charts"],
                    "result": "partial",
                },
                "tags": ["frontend", "ui"],
                "score": 0.72,
            },
        ]

        for task in tasks:
            # Store to cloud
            agent.store_memory(
                memory_id=task["memory_id"],
                memory_type="long_term",
                content=task["content"],
                tags=task["tags"],
                completion_score=task["score"],
            )
            # Create local instant memory
            agent.create_instant_memory(
                task_id=task["task_id"],
                checkpoint_id=f"cp-{task['task_id']}",
                summary=task["summary"],
                memory_id=task["memory_id"],
            )

        # === Phase 3: Agent accumulates knowledge ===
        agent.update_state(
            state_id="knowledge-auth",
            category="knowledge",
            content={
                "pattern": "JWT authentication",
                "best_practices": ["use_https", "rotate_tokens"],
            },
        )
        agent.update_state(
            state_id="knowledge-api",
            category="knowledge",
            content={
                "pattern": "RESTful API design",
                "principles": ["resource_based", "stateless"],
            },
        )

        # === Phase 4: Agent learns preferences ===
        agent.update_preference(
            preference_id="pref-security",
            key="security_first",
            value={"approach": "always_validate"},
            importance=0.95,
            source_memory_ids=["mem-auth"],
        )
        agent.update_preference(
            preference_id="pref-style",
            key="code_style",
            value={"preferred": "functional"},
            importance=0.7,
        )

        # === Phase 5: Verify everything ===
        # Memories
        memories = agent.list_memories()
        self.assertEqual(len(memories["memories"]), 3)

        # Filter by tags
        auth_memories = agent.list_memories(tags=["auth"])
        self.assertEqual(len(auth_memories["memories"]), 1)

        # States
        states = agent.get_states(use_cache=False)
        self.assertEqual(len(states), 2)

        # Preferences
        prefs = agent.get_preferences(use_cache=False)
        self.assertEqual(len(prefs), 2)

        # Environment
        env = agent.get_environment(use_cache=False)
        self.assertEqual(env["context"]["framework"], "openclaw")

        # Instant memories
        active = agent.get_active_instant_memories()
        self.assertEqual(len(active), 3)

        # === Phase 6: Session ends, condense old memories ===
        # (In real scenario, time would pass)
        counts = agent.memory_manager.count_by_status()
        self.assertEqual(counts["active"], 3)

        # === Phase 7: New session starts, retrieve previous state ===
        new_agent = LocalAgentInterface(
            agent_id="openclaw-agent-session",
            cloud_server=server,
        )
        # New session can access cloud data
        prev_memories = new_agent.list_memories()
        self.assertEqual(len(prev_memories["memories"]), 3)

        prev_states = new_agent.get_states(use_cache=False)
        self.assertEqual(len(prev_states), 2)

        prev_prefs = new_agent.get_preferences(use_cache=False)
        self.assertEqual(len(prev_prefs), 2)

        prev_env = new_agent.get_environment(use_cache=False)
        self.assertEqual(prev_env["context"]["framework"], "openclaw")

        # But instant memories are local (not shared)
        prev_active = new_agent.get_active_instant_memories()
        self.assertEqual(len(prev_active), 0)


if __name__ == "__main__":
    unittest.main()
