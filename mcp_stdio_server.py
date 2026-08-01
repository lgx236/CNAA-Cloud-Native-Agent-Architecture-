#!/usr/bin/env python3
"""CNAA MCP Stdio Server.

A stdio-based MCP server that wraps CNAA's tool implementations,
allowing agentic frameworks (like OpenClaw) to interact with CNAA
via the MCP protocol over stdin/stdout.

Protocol: JSON-RPC 2.0 over stdio (one message per line).

IMPLEMENTED:
    - MCP initialize handshake
    - tools/list: Returns all CNAA tool definitions
    - tools/call: Routes to CNAA tool handlers
    - notifications/initialized: Acknowledged (no-op)

TODO (algorithm):
    - Add request batching for multiple tool calls
    - Add streaming progress notifications for long operations
    - Add tool call result caching for read-only operations
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

# Add project root to path
sys.path.insert(0, "/root/CNAA-Cloud-Native-Agent-Architecture-")

from cloud.server.mcp_server import CNAA_MCPServer
from cnaa.tools import get_tool_definitions

# Configure logging to stderr (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


class CNAAStdioMCPServer:
    """Stdio-based MCP server wrapping CNAA tools.
    
    IMPLEMENTED:
        - JSON-RPC 2.0 message parsing and response formatting
        - MCP protocol initialize/initialized handshake
        - tools/list returning CNAA tool definitions
        - tools/call routing to CNAA_MCPServer.handle_tool_call
        - Error handling for malformed requests and unknown methods
    
    TODO (production):
        - Add JSON Schema validation for tool call arguments
        - Add request ID tracking for debugging
        - Add graceful shutdown on SIGTERM/SIGINT
    """
    
    def __init__(self) -> None:
        """Initialize the stdio MCP server."""
        self.cnaa_server = CNAA_MCPServer()
        self._initialized = False
    
    def run(self) -> None:
        """Main loop: read JSON-RPC messages from stdin, process, write to stdout.
        
        IMPLEMENTED:
            - Line-by-line JSON parsing from stdin
            - Method dispatch to handle_request()
            - JSON response writing to stdout
            - Graceful exit on EOF (stdin closed)
        
        TODO (production):
            - Add message framing for large payloads
            - Add connection health monitoring
        """
        logger.info("CNAA MCP stdio server starting")
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                
                # Only send response if there's an id (not a notification)
                if response is not None:
                    self._send_response(response)
                    
            except json.JSONDecodeError:
                self._send_response({
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                })
            except Exception as e:
                logger.exception("Error processing request")
                self._send_response({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": None,
                })
    
    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a JSON-RPC 2.0 request.
        
        IMPLEMENTED:
            - Dispatches based on 'method' field
            - Returns None for notifications (no 'id' field)
            - Returns proper JSON-RPC responses for requests
        
        TODO (algorithm):
            - Add method-level rate limiting
            - Add request prioritization (e.g., reads before writes)
        
        Args:
            request: JSON-RPC request dict
            
        Returns:
            JSON-RPC response dict, or None for notifications
        """
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Notifications (no id) don't get responses
        is_notification = request_id is None
        
        if method == "initialize":
            result = self._handle_initialize(params)
        elif method == "notifications/initialized":
            self._initialized = True
            logger.info("MCP client initialized")
            return None  # Notification, no response
        elif method == "tools/list":
            result = self._handle_tools_list()
        elif method == "tools/call":
            result = self._handle_tools_call(params)
        elif method == "ping":
            result = {}
        else:
            if is_notification:
                return None
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
                "id": request_id,
            }
        
        if is_notification:
            return None
            
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id,
        }
    
    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP initialize request.
        
        IMPLEMENTED:
            Returns server capabilities and info.
            Reports supported tools and protocol version.
        """
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "cnaa",
                "version": "0.1.0",
            },
        }
    
    def _handle_tools_list(self) -> dict[str, Any]:
        """Handle tools/list request.
        
        IMPLEMENTED:
            Returns all CNAA tool definitions from cnaa.tools.
            Each tool includes name, description, and inputSchema.
        """
        tools = get_tool_definitions()
        return {"tools": tools}
    
    def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call request.
        
        IMPLEMENTED:
            Extracts tool name and arguments from params.
            Delegates to CNAA_MCPServer.handle_tool_call().
            Wraps result in MCP content format.
        
        TODO (algorithm):
            - Add argument validation against tool's inputSchema
            - Add result caching for read-only tools (get_*)
        """
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        result = self.cnaa_server.handle_tool_call(tool_name, arguments)
        
        # Wrap result in MCP content format
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False),
                }
            ],
        }
    
    def _send_response(self, response: dict[str, Any]) -> None:
        """Send JSON-RPC response to stdout.
        
        IMPLEMENTED:
            Serializes response to JSON and writes to stdout.
            Flushes output to ensure immediate delivery.
        """
        output = json.dumps(response, ensure_ascii=False)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()


def main() -> None:
    """Entry point."""
    server = CNAAStdioMCPServer()
    server.run()


if __name__ == "__main__":
    main()
