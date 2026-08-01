# CNAA Examples

This directory contains integration examples showing how agentic frameworks can use CNAA.

## OpenClaw Integration (MCP Stdio)

The recommended integration method uses the **MCP stdio server** (`mcp_stdio_server.py`), which wraps CNAA as a standard MCP server that OpenClaw can directly connect to.

### Architecture

```
OpenClaw Agent  ←stdio JSON-RPC→  mcp_stdio_server.py  ←→  CNAA Core  ←→  Storage
     MCP Protocol                     (MCP Wrapper)         (Tool Routing)
```

### Configuration

Add to `~/.openclaw/openclaw.json`:

```json5
{
  mcp: {
    servers: {
      cnaa: {
        command: "python3",
        args: ["/path/to/CNAA/mcp_stdio_server.py"],
      },
    },
  },
}
```

### Available Tools (13 total)

| Category | Tools |
|----------|-------|
| Memory | `cnaa_store_memory`, `cnaa_get_memory`, `cnaa_list_memories`, `cnaa_tag_short_term`, `cnaa_delete_memory` |
| State | `cnaa_get_state`, `cnaa_update_state`, `cnaa_delete_state` |
| Preference | `cnaa_get_preference`, `cnaa_update_preference`, `cnaa_delete_preference` |
| Environment | `cnaa_get_environment`, `cnaa_update_environment` |

### Verification

```bash
# Verify OpenClaw can see CNAA tools
openclaw mcp probe
# Expected: cnaa: 13 tools
```

## HTTP Integration (Alternative)

[`openclaw_integration.py`](openclaw_integration.py) demonstrates HTTP-based integration for frameworks that prefer REST APIs.

### Running the HTTP Example

1. Start the CNAA server:
   ```bash
   python3 server.py --host localhost --port 8080
   ```

2. Run the integration example:
   ```bash
   cd examples
   python3 openclaw_integration.py
   ```

## Design Principles

- **Dumb Service**: CNAA handles storage, agents handle reasoning
- **JSON in/out**: All communication via JSON (stdio or HTTP)
- **Agent-agnostic**: Works with any agentic framework
- **Algorithm extensible**: Each function documents IMPLEMENTED/TODO

## What's Next (Algorithm Extension Points)

- Connection pooling and retry logic
- Authentication and authorization
- Automatic memory condensation based on agent lifecycle
- Semantic search over memories (via RetrievalPlugin)
- Request batching for multiple tool calls
- Result caching for read-only operations
