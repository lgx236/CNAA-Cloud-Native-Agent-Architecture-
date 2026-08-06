"""CNAA Local Client Reference Implementation.

This is a reference implementation of the CNAA local client.
It provides agentic frameworks (e.g., openclow) with:
- Long-term memory: persistent experience stored in cloud
- Instant memory: lightweight task summaries in local context
- State cache: fast access to knowledge and preferences
- MCP client: communication with cloud server

Structure:
- memory/: Instant memory management (short-term)
- state/: Local state cache
- client/: MCP client implementation
- agent.py: Agentic framework interface (main entry point)
"""

from local.agent import LocalAgentInterface
from local.client.mcp_client import CNAA_MCPClient

__all__ = [
    "LocalAgentInterface",
    "CNAA_MCPClient",
]
