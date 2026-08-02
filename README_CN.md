# CNAA - Cloud Native Agentic Architecture

CNAA (Cloud Native Agentic Architecture) is a reference implementation for persistent experience memory in AI agents. It provides data models, interfaces, and MCP-based tools for storing and retrieving task memories across sessions.

## Overview

CNAA allows agents to save task completion records with scores and tags, then retrieve them later via simple API calls. The focus is on providing clean interfaces and reference implementations rather than novel algorithms.

Key features:
- In-memory storage for memories, states, preferences, and environments
- MCP protocol support (HTTP and stdio modes)
- Plugin interface for custom storage backends
- No LLM or reasoning in the server - pure JSON I/O

## What CNAA Is Not

- An agent framework (you build your agent around CNAA)
- A workflow engine (just stores results, doesn't orchestrate tasks)
- A RAG system (no semantic search in v0.1)
- A production database (in-memory only in this release)

## Quick Start

### Installation

```bash
git clone https://github.com/your-org/CNAA-Cloud-Native-Agent-Architecture-
cd CNAA-Cloud-Native-Agent-Architecture-
pip install -e .
```

### Running the Server

```bash
python server.py --port 8080
```

The server exposes three endpoints:
- `GET /health` - Health check
- `GET /schemas` - All JSON schemas
- `POST /mcp` - MCP tool calls

### Using via HTTP

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "cnaa_store_memory",
      "arguments": {
        "agent_id": "test-agent",
        "memory_id": "mem-001",
        "type": "long_term",
        "content": {"task": "example"}
      }
    }
  }'
```

### Using via MCP Stdio

For integrations with agent frameworks that support MCP:

```bash
# Start stdio server
python mcp_stdio_server.py

# Agent framework sends JSON-RPC over stdin/stdout
```

## Architecture

CNAA consists of four main components:

1. **cnaa/** - Core modules defining data models (Memory, State, Preference, Environment) and interaction interfaces
2. **cloud/** - Cloud-side reference implementation with MCP server
3. **local/** - Local client with instant memory manager and state cache
4. **mcp_stdio_server.py** - Standalone MCP stdio server entry point

All components share the same schema definitions from `cnaa/schemas.py`.

## MCP Tools

CNAA exposes 13 tools via MCP protocol:

**Memory operations:**
- `cnaa_store_memory` - Store a memory
- `cnaa_get_memory` - Retrieve a specific memory
- `cnaa_list_memories` - List memories with optional filters
- `cnaa_tag_short_term` - Tag recent memories
- `cnaa_delete_memory` - Delete a memory

**State operations:**
- `cnaa_get_state` - Get all state entries
- `cnaa_update_state` - Create or update a state
- `cnaa_delete_state` - Delete a state

**Preference operations:**
- `cnaa_get_preference` - Get all preferences
- `cnaa_update_preference` - Create or update a preference
- `cnaa_delete_preference` - Delete a preference

**Environment operations:**
- `cnaa_get_environment` - Get environment context
- `cnaa_update_environment` - Update environment context

## Testing

Run tests with Python 3.12+:

```bash
python3 -m pytest tests/ -v
```

Tests cover:
- Data model creation and validation
- In-memory storage CRUD operations
- MCP tool routing
- End-to-end cloud/local integration
- OpenClaw integration example

Current status: 126 tests passing.

## Configuration

Optional environment variables:

```bash
# Disable authentication (default: true, auth is disabled by default)
export CNAA_AUTH_ENABLED=false

# Enable API key authentication
export CNAA_AUTH_ENABLED=true
export CNAA_API_KEYS='{"sk-key": {"agent_id": "agent-001", "permission": "read_write"}}'
export CNAA_ALLOW_UNAUTHENTICATED=false
```

## Extending CNAA

To add a new storage backend:

1. Implement the `MemoryInterface` abstract class from `cnaa.interaction`
2. Replace `InMemoryMemoryStore` in `cloud/server/mcp_server.py`

Example:

```python
from cnaa.interaction import MemoryInterface
from cnaa.models import Memory

class PostgreSQLMemoryStore(MemoryInterface):
    def store_memory(self, memory: Memory) -> dict:
        # Save to PostgreSQL
        pass
    
    def get_memory(self, agent_id: str, memory_id: str) -> Memory | None:
        # Query PostgreSQL
        pass
    # ... implement other methods
```

Then instantiate it in `mcp_server.py`:

```python
self.memory_store = PostgreSQLMemoryStore()
```

## Documentation

See `docs/zh/technical-implementation.md` for detailed function-level documentation. Each module includes:
- IMPLEMENTED section: what is currently done
- TODO section: extension points for customization

## Project Status

This is version 0.1, released as a working reference implementation. The core specification (data models, interfaces, lifecycle rules) is stable. Future versions will add retrieval plugins, condensation strategies, and additional storage backends.

## License

MIT
