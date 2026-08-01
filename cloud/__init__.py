"""CNAA Cloud Server Reference Implementation.

This is a reference implementation of the CNAA cloud server.
It provides:
- In-memory storage (can be replaced with persistent storage)
- MCP server for agent communication
- Agent interface for integration

Structure:
- storage/: Storage layer implementations
- server/: MCP server implementation
- agent.py: Agent-facing interface
"""

from cloud.server.mcp_server import CNAA_MCPServer
from cloud.agent import CloudAgentInterface

__all__ = [
    "CNAA_MCPServer",
    "CloudAgentInterface",
]
