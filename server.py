#!/usr/bin/env python3
"""CNAA Server Entry Point.

This is the main entry point for running the CNAA cloud server.
It provides agentic frameworks (e.g., openclow) with long-term memory
storage and state management capabilities.

The server exposes:
- GET /schemas: Interface schema definitions
- POST /mcp: MCP tool calls for memory/state operations
- GET /health: Health check endpoint

Usage:
    python server.py [--host HOST] [--port PORT]

Example:
    python server.py --host 0.0.0.0 --port 8080

IMPLEMENTED:
    - HTTP server using Python stdlib (http.server)
    - 3 endpoints: /schemas (GET), /mcp (POST), /health (GET)
    - JSON request/response handling
    - MCP tool call routing to CNAA_MCPServer
    - Graceful shutdown on KeyboardInterrupt
    - Configurable host/port via CLI arguments

TODO (production):
    - Add WSGI/ASGI server (gunicorn/uvicorn) for production deployment
    - Add request authentication (API key, JWT)
    - Add CORS headers for browser-based clients
    - Add request logging middleware
    - Add graceful timeout handling

TODO (algorithm extension point):
    - Add request batching for multiple MCP calls in one HTTP request
    - Add response compression (gzip) for large payloads
    - Add connection pooling for downstream storage backends
    - Add rate limiting per agent_id or IP
"""

from __future__ import annotations

import argparse
import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from cloud.server.mcp_server import CNAA_MCPServer
from cnaa.schemas import get_all_schemas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CNAARequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for CNAA server.
    
    Endpoints:
    - GET /schemas: Get all interface schemas
    - POST /mcp: Handle MCP tool calls
    - GET /health: Health check

    IMPLEMENTED:
        - Path-based routing via do_GET/do_POST dispatch
        - JSON request body parsing with Content-Length handling
        - MCP tool extraction: reads 'tool' and 'arguments' from request
        - Error responses with proper HTTP status codes
        - Logging override to use Python logging module

    TODO (algorithm extension point):
        - Add request validation (schema validation for MCP arguments)
        - Add request timing metrics
        - Add content negotiation (Accept header handling)
        - Add streaming responses for large result sets
    """
    
    # Class-level server reference
    cnaa_server: CNAA_MCPServer = None
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/schemas":
            self._handle_schemas()
        elif self.path == "/health":
            self._handle_health()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "Not found")
    
    def do_POST(self) -> None:
        """Handle POST requests."""
        if self.path == "/mcp":
            self._handle_mcp()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "Not found")
    
    def _handle_schemas(self) -> None:
        """Handle GET /schemas - return all interface schemas."""
        schemas = get_all_schemas()
        self._send_json(HTTPStatus.OK, schemas)
    
    def _handle_health(self) -> None:
        """Handle GET /health - health check."""
        self._send_json(HTTPStatus.OK, {"status": "healthy"})
    
    def _handle_mcp(self) -> None:
        """Handle POST /mcp - MCP tool calls.
        
        IMPLEMENTED:
            - Parse JSON request body
            - Extract 'tool' name and 'arguments' dict
            - Delegate to CNAA_MCPServer.handle_tool_call()
            - Return JSON response with proper status codes
            - Error handling for malformed JSON and missing fields
        
        TODO (algorithm extension point):
            - Add request schema validation before routing
            - Add agent_id-based authorization check
            - Add request/response size limits
            - Add timeout for long-running tool calls
        """
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            request = json.loads(body.decode("utf-8"))
            
            tool_name = request.get("tool")
            arguments = request.get("arguments", {})
            
            if not tool_name:
                self._send_error(HTTPStatus.BAD_REQUEST, "Missing 'tool' field")
                return
            
            # Handle tool call
            result = self.cnaa_server.handle_tool_call(tool_name, arguments)
            self._send_json(HTTPStatus.OK, result)
            
        except json.JSONDecodeError:
            self._send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
        except Exception as e:
            logger.exception("Error handling MCP request")
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
    
    def _send_json(self, status: HTTPStatus, data: dict[str, Any]) -> None:
        """Send JSON response.
        
        Args:
            status: HTTP status code
            data: Response data
        """
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response.encode("utf-8")))
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))
    
    def _send_error(self, status: HTTPStatus, message: str) -> None:
        """Send error response.
        
        Args:
            status: HTTP status code
            message: Error message
        """
        self._send_json(status, {"status": "error", "message": message})
    
    def log_message(self, format: str, *args: Any) -> None:
        """Override to use logging module."""
        logger.info("%s - %s", self.address_string(), format % args)


def create_server(
    host: str = "localhost",
    port: int = 8080,
) -> HTTPServer:
    """Create and configure the HTTP server.
    
    Args:
        host: Server host address
        port: Server port
        
    Returns:
        Configured HTTPServer instance
    """
    # Create CNAA server
    CNAARequestHandler.cnaa_server = CNAA_MCPServer()
    
    # Create HTTP server
    server = HTTPServer((host, port), CNAARequestHandler)
    return server


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CNAA Server")
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Server port (default: 8080)",
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting CNAA server on {args.host}:{args.port}")
    
    server = create_server(args.host, args.port)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.shutdown()


if __name__ == "__main__":
    main()
