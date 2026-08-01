# CNAA Examples

This directory contains integration examples showing how agentic frameworks can use CNAA.

## OpenClaw Integration

[`openclaw_integration.py`](openclaw_integration.py) demonstrates how [OpenClaw](https://github.com/openclaw/openclaw) (a TypeScript-based personal AI assistant) can integrate with CNAA to provide long-term memory capabilities.

### Architecture

```
OpenClaw (TypeScript)  ←→  CNAA Cloud (Python)  ←→  Storage
     HTTP/MCP                  HTTP API
```

### Key Concepts

1. **Long-term Memory**: OpenClaw agents store task experiences in CNAA cloud
2. **State Management**: Agents accumulate knowledge and preferences over time
3. **Cross-session Persistence**: Memories persist across agent restarts
4. **Multi-device Sync**: All OpenClaw instances share the same memory via CNAA cloud

### Running the Example

1. Start the CNAA server:
   ```bash
   python server.py --host localhost --port 8080
   ```

2. Run the integration example:
   ```bash
   cd examples
   python openclaw_integration.py
   ```

### Integration Pattern

The integration follows CNAA's design principles:
- **Dumb Service**: CNAA handles storage, OpenClaw handles reasoning
- **JSON in/out**: All communication via JSON over HTTP
- **Agent-agnostic**: Works with any agentic framework, not just OpenClaw

### What's Implemented

- HTTP client for CNAA cloud server
- All CNAA operations (store/get/list/delete memories, states, preferences, environments)
- Complete usage examples

### What's Next (Algorithm Extension Points)

- Connection pooling and retry logic
- Authentication and authorization
- Automatic memory condensation based on agent lifecycle
- Semantic search over memories (via RetrievalPlugin)
- Background sync between OpenClaw and CNAA
