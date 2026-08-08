"""MCP protocol handler - processes tool calls from agents."""

from server.base_handler import BaseRequestHandler


class MCPServerHandler(BaseRequestHandler):
    """Handle POST /mcp requests from agents.
    
    Receives JSON: {
        "tool": "memory_name",
        "arguments": {...}
    }
    
    Returns: Result of tool execution
    """
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
    
    def do_POST(self):
        """Handle POST requests to /mcp endpoint."""
        if self.path == "/mcp":
            self._handle_mcp()
        else:
            self._send_error(404, "Not found")
    
    def _handle_mcp(self):
        """Process MCP tool call."""
        import json
        
        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            request = json.loads(body.decode("utf-8"))
            
            tool_name = request.get("tool")
            arguments = request.get("arguments", {})
            
            if not tool_name:
                self._send_error(400, "Missing 'tool' field")
                return
            
            # Route to appropriate handler based on tool name
            if tool_name == "store_memory":
                result = self._handle_store_memory(arguments)
            elif tool_name == "get_memories":
                result = self._handle_get_memories(arguments)
            else:
                self._send_error(400, f"Unknown tool: {tool_name}")
                return
            
            self._send_json_response(200, result)
            
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_store_memory(self, args):
        """Store a new memory."""
        memory = {
            "memory_id": args.get("memory_id"),
            "agent_id": args.get("agent_id"),
            "type": args.get("type"),
            "content": args.get("content"),
            "tags": args.get("tags", []),
            "completion_score": args.get("completion_score")
        }
        
        result = self.storage.save(memory)
        return {"status": "ok", **result}
    
    def _handle_get_memories(self, args):
        """Get memories for an agent."""
        agent_id = args.get("agent_id")
        
        # Return all memories for now (simplified)
        memories = list(self.storage.find_all(agent_id=agent_id))
        
        return {
            "status": "ok",
            "memories": [dict(m) for m in memories],
            "count": len(memories)
        }
