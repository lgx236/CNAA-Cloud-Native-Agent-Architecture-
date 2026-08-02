"""Tests for CNAA security module - authentication and authorization."""

import unittest
from unittest.mock import patch

from cnaa.security import (
    AuthConfig,
    AuthContext,
    PermissionLevel,
    check_permission,
    load_auth_config_from_env,
    validate_api_key,
)
from cnaa.tools import (
    DELETE_MEMORY,
    DELETE_PREFERENCE,
    DELETE_STATE,
    GET_ENVIRONMENT,
    GET_MEMORY,
    GET_PREFERENCE,
    GET_STATE,
    LIST_MEMORIES,
    STORE_MEMORY,
    TAG_SHORT_TERM,
    TOOL_PERMISSION_MAP,
    UPDATE_ENVIRONMENT,
    UPDATE_PREFERENCE,
    UPDATE_STATE,
    get_tool_names,
)
from cloud.server.mcp_server import CNAA_MCPServer
from cloud.storage.memory_store import InMemoryMemoryStore
from cnaa.models import Memory, MemoryType


# ---------------------------------------------------------------------------
# 1. Security module basics
# ---------------------------------------------------------------------------

class TestPermissionLevel(unittest.TestCase):
    """Test PermissionLevel enum."""

    def test_permission_levels_exist(self):
        """Verify all permission levels are defined."""
        self.assertIsNotNone(PermissionLevel.READ_ONLY)
        self.assertIsNotNone(PermissionLevel.READ_WRITE)
        self.assertIsNotNone(PermissionLevel.ADMIN)

    def test_permission_values(self):
        """Verify permission level string values."""
        self.assertEqual(PermissionLevel.READ_ONLY.value, "read_only")
        self.assertEqual(PermissionLevel.READ_WRITE.value, "read_write")
        self.assertEqual(PermissionLevel.ADMIN.value, "admin")


class TestAuthConfig(unittest.TestCase):
    """Test AuthConfig dataclass."""

    def test_default_config(self):
        """Default config should have auth disabled."""
        config = AuthConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.api_keys, {})
        self.assertTrue(config.allow_unauthenticated)

    def test_custom_config(self):
        """Verify custom config creation."""
        config = AuthConfig(
            enabled=True,
            api_keys={"sk-001": {"agent_id": "a1", "permission": "admin"}},
            allow_unauthenticated=False,
        )
        self.assertTrue(config.enabled)
        self.assertIn("sk-001", config.api_keys)
        self.assertFalse(config.allow_unauthenticated)


class TestAuthContext(unittest.TestCase):
    """Test AuthContext dataclass."""

    def test_context_creation(self):
        """Verify auth context creation with all fields."""
        ctx = AuthContext(
            agent_id="agent-001",
            permission=PermissionLevel.READ_WRITE,
            authenticated=True,
        )
        self.assertEqual(ctx.agent_id, "agent-001")
        self.assertEqual(ctx.permission, PermissionLevel.READ_WRITE)
        self.assertTrue(ctx.authenticated)

    def test_to_dict(self):
        """Verify to_dict serialization."""
        ctx = AuthContext(
            agent_id="agent-001",
            permission=PermissionLevel.ADMIN,
        )
        d = ctx.to_dict()
        self.assertEqual(d["agent_id"], "agent-001")
        self.assertEqual(d["permission"], "admin")
        self.assertTrue(d["authenticated"])


# ---------------------------------------------------------------------------
# 2. Validation functions
# ---------------------------------------------------------------------------

class TestValidateApiKey(unittest.TestCase):
    """Test validate_api_key function."""

    def _make_config(self, **overrides):
        defaults = dict(
            enabled=True,
            api_keys={
                "sk-valid": {"agent_id": "agent-001", "permission": "read_write"},
            },
            allow_unauthenticated=False,
        )
        defaults.update(overrides)
        return AuthConfig(**defaults)

    def test_auth_disabled_returns_none(self):
        """When auth is disabled, should return None (skip validation)."""
        config = AuthConfig(enabled=False)
        result = validate_api_key("any-key", config)
        self.assertIsNone(result)

    def test_valid_key_returns_context(self):
        """Valid key should return AuthContext with correct agent_id and permission."""
        config = self._make_config()
        ctx = validate_api_key("sk-valid", config)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.agent_id, "agent-001")
        self.assertEqual(ctx.permission, PermissionLevel.READ_WRITE)

    def test_invalid_key_returns_none(self):
        """Invalid key should return None."""
        config = self._make_config()
        result = validate_api_key("sk-bogus", config)
        self.assertIsNone(result)

    def test_missing_key_with_allow_unauthenticated(self):
        """No key + allow_unauthenticated=True should return None."""
        config = self._make_config(allow_unauthenticated=True)
        result = validate_api_key("", config)
        self.assertIsNone(result)

    def test_none_key_returns_none(self):
        """None key should return None."""
        config = self._make_config(allow_unauthenticated=True)
        result = validate_api_key(None, config)
        self.assertIsNone(result)


class TestCheckPermission(unittest.TestCase):
    """Test check_permission function."""

    def test_no_auth_context_allows_all(self):
        """No auth context (auth disabled) should allow everything."""
        self.assertTrue(check_permission(None, "read"))
        self.assertTrue(check_permission(None, "write"))

    def test_read_only_can_read(self):
        """READ_ONLY permission should allow read operations."""
        ctx = AuthContext(agent_id="a", permission=PermissionLevel.READ_ONLY)
        self.assertTrue(check_permission(ctx, "read"))

    def test_read_only_cannot_write(self):
        """READ_ONLY permission should deny write operations."""
        ctx = AuthContext(agent_id="a", permission=PermissionLevel.READ_ONLY)
        self.assertFalse(check_permission(ctx, "write"))

    def test_read_write_can_read(self):
        """READ_WRITE permission should allow read operations."""
        ctx = AuthContext(agent_id="a", permission=PermissionLevel.READ_WRITE)
        self.assertTrue(check_permission(ctx, "read"))

    def test_read_write_can_write(self):
        """READ_WRITE permission should allow write operations."""
        ctx = AuthContext(agent_id="a", permission=PermissionLevel.READ_WRITE)
        self.assertTrue(check_permission(ctx, "write"))

    def test_admin_can_do_everything(self):
        """ADMIN permission should allow all operations."""
        ctx = AuthContext(agent_id="a", permission=PermissionLevel.ADMIN)
        self.assertTrue(check_permission(ctx, "read"))
        self.assertTrue(check_permission(ctx, "write"))


# ---------------------------------------------------------------------------
# 3. Configuration loading
# ---------------------------------------------------------------------------

class TestLoadAuthConfig(unittest.TestCase):
    """Test load_auth_config_from_env function."""

    def test_default_env(self):
        """With no env vars, should return disabled config."""
        with patch.dict("os.environ", {}, clear=True):
            config = load_auth_config_from_env()
        self.assertFalse(config.enabled)
        self.assertEqual(config.api_keys, {})
        self.assertTrue(config.allow_unauthenticated)

    def test_auth_enabled(self):
        """CNAA_AUTH_ENABLED=true should enable auth."""
        with patch.dict("os.environ", {"CNAA_AUTH_ENABLED": "true"}, clear=True):
            config = load_auth_config_from_env()
        self.assertTrue(config.enabled)

    def test_api_keys_parsing(self):
        """CNAA_API_KEYS JSON should be parsed correctly."""
        import json
        keys = {"sk-001": {"agent_id": "a1", "permission": "read_only"}}
        with patch.dict(
            "os.environ",
            {"CNAA_API_KEYS": json.dumps(keys)},
            clear=True,
        ):
            config = load_auth_config_from_env()
        self.assertEqual(config.api_keys, keys)

    def test_invalid_json_falls_back(self):
        """Invalid JSON in CNAA_API_KEYS should fall back to empty dict."""
        with patch.dict(
            "os.environ",
            {"CNAA_API_KEYS": "not-valid-json"},
            clear=True,
        ):
            config = load_auth_config_from_env()
        self.assertEqual(config.api_keys, {})


# ---------------------------------------------------------------------------
# 4. MCP server auth integration
# ---------------------------------------------------------------------------

class TestMCPServerAuth(unittest.TestCase):
    """Test MCP server authentication integration."""

    def setUp(self):
        """Set up server with auth enabled."""
        self.auth_config = AuthConfig(
            enabled=True,
            api_keys={
                "sk-test-001": {"agent_id": "agent-001", "permission": "read_write"},
                "sk-test-readonly": {"agent_id": "agent-001", "permission": "read_only"},
            },
            allow_unauthenticated=False,
        )
        self.server = CNAA_MCPServer(auth_config=self.auth_config)

    def test_no_auth_context_still_works(self):
        """Without _auth_context in arguments, tool call should proceed (backward compat)."""
        result = self.server.handle_tool_call(
            STORE_MEMORY,
            {
                "agent_id": "agent-001",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {"task": "test"},
            },
        )
        self.assertEqual(result["status"], "ok")

    def test_read_only_cannot_store_memory(self):
        """Read-only auth context should reject store_memory."""
        result = self.server.handle_tool_call(
            STORE_MEMORY,
            {
                "agent_id": "agent-001",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {"task": "test"},
                "_auth_context": {
                    "agent_id": "agent-001",
                    "permission": "read_only",
                },
            },
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Permission denied", result["message"])

    def test_read_write_can_store_memory(self):
        """Read-write auth context should allow store_memory."""
        result = self.server.handle_tool_call(
            STORE_MEMORY,
            {
                "agent_id": "agent-001",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {"task": "test"},
                "_auth_context": {
                    "agent_id": "agent-001",
                    "permission": "read_write",
                },
            },
        )
        self.assertEqual(result["status"], "ok")

    def test_agent_id_mismatch_rejected(self):
        """Auth context agent_id not matching request agent_id should be rejected."""
        result = self.server.handle_tool_call(
            STORE_MEMORY,
            {
                "agent_id": "agent-002",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {"task": "test"},
                "_auth_context": {
                    "agent_id": "agent-001",
                    "permission": "read_write",
                },
            },
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Agent ID mismatch", result["message"])

    def test_read_only_can_get_memory(self):
        """Read-only auth context should allow get_memory."""
        # First store a memory (without auth context for simplicity)
        self.server.handle_tool_call(
            STORE_MEMORY,
            {
                "agent_id": "agent-001",
                "memory_id": "mem-001",
                "type": "long_term",
                "content": {"task": "test"},
            },
        )
        result = self.server.handle_tool_call(
            GET_MEMORY,
            {
                "agent_id": "agent-001",
                "memory_id": "mem-001",
                "_auth_context": {
                    "agent_id": "agent-001",
                    "permission": "read_only",
                },
            },
        )
        self.assertEqual(result["status"], "ok")


# ---------------------------------------------------------------------------
# 5. Storage layer auth
# ---------------------------------------------------------------------------

class TestStorageAuth(unittest.TestCase):
    """Test storage layer auth_context validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.store = InMemoryMemoryStore()
        self.memory = Memory(
            memory_id="mem-001",
            agent_id="agent-001",
            type=MemoryType.LONG_TERM,
            content={"task": "test"},
        )

    def test_store_memory_with_matching_auth(self):
        """Store should succeed when auth_context agent_id matches."""
        result = self.store.store_memory(
            self.memory,
            auth_context={"agent_id": "agent-001", "permission": "read_write"},
        )
        self.assertEqual(result["status"], "ok")

    def test_store_memory_with_mismatched_auth(self):
        """Store should return error when auth_context agent_id doesn't match."""
        result = self.store.store_memory(
            self.memory,
            auth_context={"agent_id": "agent-999", "permission": "read_write"},
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("mismatch", result["message"].lower())

    def test_store_memory_without_auth(self):
        """Store should succeed without auth_context (backward compat)."""
        result = self.store.store_memory(self.memory)
        self.assertEqual(result["status"], "ok")

    def test_get_memory_with_matching_auth(self):
        """Get should return memory when auth_context agent_id matches."""
        self.store.store_memory(self.memory)
        result = self.store.get_memory(
            "agent-001",
            "mem-001",
            auth_context={"agent_id": "agent-001"},
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.memory_id, "mem-001")

    def test_get_memory_with_mismatched_auth(self):
        """Get should return None when auth_context agent_id doesn't match (stealth)."""
        self.store.store_memory(self.memory)
        result = self.store.get_memory(
            "agent-001",
            "mem-001",
            auth_context={"agent_id": "agent-999"},
        )
        self.assertIsNone(result)

    def test_get_memory_without_auth(self):
        """Get should work normally without auth_context."""
        self.store.store_memory(self.memory)
        result = self.store.get_memory("agent-001", "mem-001")
        self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# 6. Tool permission map
# ---------------------------------------------------------------------------

class TestToolPermissionMap(unittest.TestCase):
    """Test TOOL_PERMISSION_MAP completeness."""

    def test_all_tools_have_permissions(self):
        """Every tool in tool definitions should have a permission mapping."""
        for name in get_tool_names():
            self.assertIn(
                name,
                TOOL_PERMISSION_MAP,
                f"Tool {name} is missing from TOOL_PERMISSION_MAP",
            )

    def test_read_tools_mapped_to_read(self):
        """GET/LIST/SEARCH tools should map to 'read'."""
        read_tools = [GET_MEMORY, LIST_MEMORIES, GET_STATE, GET_PREFERENCE, GET_ENVIRONMENT]
        for tool in read_tools:
            self.assertEqual(
                TOOL_PERMISSION_MAP[tool],
                "read",
                f"{tool} should be mapped to 'read'",
            )

    def test_write_tools_mapped_to_write(self):
        """STORE/UPDATE/DELETE tools should map to 'write'."""
        write_tools = [
            STORE_MEMORY,
            DELETE_MEMORY,
            TAG_SHORT_TERM,
            UPDATE_STATE,
            DELETE_STATE,
            UPDATE_PREFERENCE,
            DELETE_PREFERENCE,
            UPDATE_ENVIRONMENT,
        ]
        for tool in write_tools:
            self.assertEqual(
                TOOL_PERMISSION_MAP[tool],
                "write",
                f"{tool} should be mapped to 'write'",
            )


# ---------------------------------------------------------------------------
# 7. Auth bypass & config robustness fixes
# ---------------------------------------------------------------------------

class TestAuthBypassFix(unittest.TestCase):
    """Tests for authentication bypass fix."""

    def test_no_auth_header_rejected_when_required(self):
        """When auth enabled and unauthenticated not allowed, no key should return None."""
        config = AuthConfig(
            enabled=True,
            allow_unauthenticated=False,
            api_keys={"sk-001": {"agent_id": "a1", "permission": "read_write"}},
        )
        result = validate_api_key(None, config)
        self.assertIsNone(result)


class TestConfigRobustness(unittest.TestCase):
    """Tests for configuration parsing robustness."""

    def test_non_dict_api_keys_falls_back(self):
        """CNAA_API_KEYS as JSON list should fall back to empty dict."""
        with patch.dict(
            "os.environ",
            {"CNAA_API_KEYS": '["a", "b"]', "CNAA_AUTH_ENABLED": "true"},
        ):
            config = load_auth_config_from_env()
            self.assertEqual(config.api_keys, {})

    def test_invalid_permission_falls_back(self):
        """Invalid permission string should fall back to READ_WRITE."""
        config = AuthConfig(
            enabled=True,
            api_keys={"sk-bad": {"agent_id": "a1", "permission": "rw"}},
        )
        ctx = validate_api_key("sk-bad", config)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.permission, PermissionLevel.READ_WRITE)


if __name__ == "__main__":
    unittest.main()
