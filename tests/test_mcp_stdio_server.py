"""Tests for CNAA MCP Stdio Server.

Tests the stdio-based MCP server wrapper that enables
agentic frameworks to interact with CNAA via MCP protocol.

Test coverage:
- JSON-RPC message parsing and response formatting
- MCP initialize handshake
- tools/list returns all CNAA tool definitions
- tools/call routes to correct CNAA handlers
- Error handling for malformed requests and unknown methods
- Notification handling (no response expected)
"""

from __future__ import annotations

import json
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, "/root/CNAA-Cloud-Native-Agent-Architecture-")

from mcp_stdio_server import CNAAStdioMCPServer


class TestCNAAStdioMCPServer(unittest.TestCase):
    """Test the stdio MCP server."""
    
    def setUp(self):
        """Create server instance for each test."""
        self.server = CNAAStdioMCPServer()
    
    def test_initialize(self):
        """Test MCP initialize handshake."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        }
        
        response = self.server.handle_request(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        
        result = response["result"]
        self.assertEqual(result["protocolVersion"], "2024-11-05")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "cnaa")
        self.assertEqual(result["serverInfo"]["version"], "0.1.0")
    
    def test_initialized_notification(self):
        """Test notifications/initialized (no response expected)."""
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        
        response = self.server.handle_request(request)
        self.assertIsNone(response)
    
    def test_tools_list(self):
        """Test tools/list returns all CNAA tools."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        
        response = self.server.handle_request(request)
        
        self.assertIsNotNone(response)
        result = response["result"]
        tools = result["tools"]
        
        # Should have 13 tools
        self.assertEqual(len(tools), 13)
        
        # Check tool names
        tool_names = [t["name"] for t in tools]
        self.assertIn("cnaa_store_memory", tool_names)
        self.assertIn("cnaa_get_memory", tool_names)
        self.assertIn("cnaa_list_memories", tool_names)
        self.assertIn("cnaa_get_state", tool_names)
        self.assertIn("cnaa_get_preference", tool_names)
        self.assertIn("cnaa_get_environment", tool_names)
        
        # Check each tool has required fields
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
    
    def test_tools_call_store_memory(self):
        """Test tools/call with cnaa_store_memory."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "cnaa_store_memory",
                "arguments": {
                    "agent_id": "test-agent",
                    "memory_id": "test-mem-1",
                    "type": "long_term",
                    "content": {"text": "Test memory"},
                    "tags": ["test"],
                },
            },
        }
        
        response = self.server.handle_request(request)
        
        self.assertIsNotNone(response)
        result = response["result"]
        self.assertIn("content", result)
        
        # Parse the inner result
        inner = json.loads(result["content"][0]["text"])
        self.assertEqual(inner["status"], "ok")
        self.assertEqual(inner["memory_id"], "test-mem-1")
    
    def test_tools_call_get_memory(self):
        """Test tools/call with cnaa_get_memory after storing."""
        # First store a memory
        store_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "cnaa_store_memory",
                "arguments": {
                    "agent_id": "test-agent-2",
                    "memory_id": "mem-get-test",
                    "type": "long_term",
                    "content": {"data": "important"},
                },
            },
        }
        self.server.handle_request(store_request)
        
        # Then get it
        get_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "cnaa_get_memory",
                "arguments": {
                    "agent_id": "test-agent-2",
                    "memory_id": "mem-get-test",
                },
            },
        }
        
        response = self.server.handle_request(get_request)
        result = response["result"]
        inner = json.loads(result["content"][0]["text"])
        
        self.assertEqual(inner["status"], "ok")
        self.assertEqual(inner["memory"]["memory_id"], "mem-get-test")
        self.assertEqual(inner["memory"]["content"], {"data": "important"})
    
    def test_tools_call_unknown_tool(self):
        """Test tools/call with unknown tool name."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "cnaa_nonexistent_tool",
                "arguments": {},
            },
        }
        
        response = self.server.handle_request(request)
        result = response["result"]
        inner = json.loads(result["content"][0]["text"])
        
        self.assertEqual(inner["status"], "error")
        self.assertIn("Unknown tool", inner["message"])
    
    def test_unknown_method(self):
        """Test handling of unknown JSON-RPC method."""
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "unknown/method",
            "params": {},
        }
        
        response = self.server.handle_request(request)
        
        self.assertIsNotNone(response)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)
    
    def test_notification_no_response(self):
        """Test that notifications (no id) don't get responses."""
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/some_notification",
            "params": {"data": "test"},
        }
        
        response = self.server.handle_request(request)
        self.assertIsNone(response)
    
    def test_ping(self):
        """Test ping method."""
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "ping",
            "params": {},
        }
        
        response = self.server.handle_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response["result"], {})
    
    def test_tools_call_state_operations(self):
        """Test state update and retrieval via MCP."""
        # Update state
        update_request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "cnaa_update_state",
                "arguments": {
                    "agent_id": "state-test-agent",
                    "state_id": "state-1",
                    "category": "knowledge",
                    "content": {"fact": "Python is great"},
                },
            },
        }
        
        response = self.server.handle_request(update_request)
        inner = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(inner["status"], "ok")
        
        # Get state
        get_request = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "cnaa_get_state",
                "arguments": {"agent_id": "state-test-agent"},
            },
        }
        
        response = self.server.handle_request(get_request)
        inner = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(inner["status"], "ok")
        self.assertTrue(len(inner["states"]) > 0)


class TestStdioOutput(unittest.TestCase):
    """Test stdio output formatting."""
    
    def test_send_response_format(self):
        """Test that responses are properly formatted JSON lines."""
        server = CNAAStdioMCPServer()
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            server._send_response({
                "jsonrpc": "2.0",
                "result": {"test": True},
                "id": 42,
            })
        
        output = captured_output.getvalue().strip()
        parsed = json.loads(output)
        
        self.assertEqual(parsed["jsonrpc"], "2.0")
        self.assertEqual(parsed["id"], 42)
        self.assertTrue(parsed["result"]["test"])


if __name__ == "__main__":
    unittest.main()
