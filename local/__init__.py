"""CNAA Local Client Reference Implementation.

This is a reference implementation of the CNAA local client.
It provides:
- Instant memory management (short-term memory)
- State caching for local access
- MCP client for cloud communication
- Agent interface for integration

Structure:
- memory/: Instant memory management
- state/: Local state cache
- client/: MCP client implementation
- agent.py: Agent-facing interface
"""

from local.agent import LocalAgentInterface
from local.client.mcp_client import CNAA_MCPClient

__all__ = [
    "LocalAgentInterface",
    "CNAA_MCPClient",
]
