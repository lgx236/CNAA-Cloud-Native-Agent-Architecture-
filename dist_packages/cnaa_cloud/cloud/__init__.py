"""CNAA Cloud Server Reference Implementation.

This is a reference implementation of the CNAA cloud server.
It provides agentic frameworks (e.g., openclow) with:
- Long-term memory storage: persistent experience across sessions
- State management: knowledge accumulation and preference learning
- MCP server for agent communication
- Python interface for direct integration

Structure:
- storage/: Storage layer implementations
- server/: MCP server implementation
- agent.py: Agentic framework interface
"""

from cloud.server.mcp_server import CNAA_MCPServer
from cloud.agent import CloudAgentInterface

__all__ = [
    "CNAA_MCPServer",
    "CloudAgentInterface",
]
