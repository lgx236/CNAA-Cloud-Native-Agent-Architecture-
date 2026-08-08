# CNAA API Compatibility Matrix

## Overview

This document defines the backward compatibility policy and versioning strategy for CNAA APIs. All changes follow [Semantic Versioning (SemVer)](https://semver.org/).

**Current Stable Version**: v1.0.0 (Production)

---

## API Version Matrix

| API Version | Release Date | Status          | End of Support | Breaking Changes |
|-------------|--------------|-----------------|----------------|------------------|
| v0.x        | N/A          | ❌ Deprecated   | v0.3           | Yes              |
| v0.2        | 2026-08      | ⚠️ Maintained   | v1.2           | No               |
| **v1.0**    | **2026-08**  | **✅ Stable**   | **v1.3+**      | **No**           |
| v1.1        | TBD          | 🔄 In Development | N/A           | May              |
| v2.0        | TBD          | 🔮 Planned      | N/A            | Yes (major)      |

---

## v1.0 API Specification

### Core Endpoints

#### `GET /health`
**Public endpoint - no authentication required**

**Response Schema:**
```json
{
  "status": "healthy",  // healthy, degraded, or unhealthy
  "timestamp": "2026-08-08T10:30:00Z",
  "component_count": 3,
  "errors_count": 0,
  "warnings_count": 0,
  "components": {
    "memory_storage": "ok: 5 memories",
    "state_storage": "ok: 2 states"
  }
}
```

**Status Codes:**
- 200: Health check succeeded
- 500: Internal server error

**Backward Compatible**: ✅ Yes

---

#### `GET /metrics`
**Public endpoint - no authentication required**

**Response Format**: Prometheus text format

**Example Response:**
```
# HELP cnaa_memory_count Total number of memories stored
# TYPE cnaa_memory_count gauge
cnaa_memory_count{agent_id="test-agent"} 5.0
# HELP cnaa_uptime_seconds Uptime in seconds
# TYPE cnaa_uptime_seconds gauge
cnaa_uptime_seconds 3600.5
```

**Backward Compatible**: ✅ New endpoint in v1.0

---

#### `GET /version`
**Public endpoint - no authentication required**

**Response Schema:**
```json
{
  "version": "1.0.0",
  "api_version": "v1",
  "status": "production-ready"
}
```

**Backward Compatible**: ✅ New endpoint in v1.0

---

#### `POST /mcp`
**Authenticated endpoint - API key required if auth enabled**

**Request Body:**
```json
{
  "tool": "store_memory",
  "arguments": {
    "memory_id": "mem-001",
    "agent_id": "agent-001",
    "type": "experience",
    "content": {"task": "example", "result": "success"}
  }
}
```

**Response Schema:**
```json
{
  "status": "ok",
  "memory_id": "mem-001"
}
```

**Backward Compatible**: ✅ Yes

---

#### `GET /schemas`
**Public endpoint - returns interface definitions**

**Response Schema:**
Returns all MCP tool schemas in JSON format

**Backward Compatible**: ✅ Yes

---

## Tool Definitions Backward Compatibility

### Memory Management Tools

| Tool Name          | Added in | v1.0 Status | Required Fields         | Optional Fields             |
|--------------------|----------|-------------|-------------------------|-----------------------------|
| `store_memory`     | v0.1     | ✅ Supported | memory_id, agent_id, type, content | completion_score, tags      |
| `get_memories`     | v0.1     | ✅ Supported | agent_id                | type_filter, limit, offset  |
| `delete_memory`    | v0.1     | ✅ Supported | memory_id               | soft_delete                 |
| `search_memories`  | v0.2     | ✅ Supported | query                   | agent_id, limit             |

### State Management Tools

| Tool Name          | Added in | v1.0 Status | Required Fields | Optional Fields             |
|--------------------|----------|-------------|-----------------|-----------------------------|
| `update_state`     | v0.1     | ✅ Supported | state_key       | category, value             |
| `get_states`       | v0.1     | ✅ Supported | agent_id        | category_filter             |
| `delete_state`     | v0.1     | ✅ Supported | state_key       |                             |

### Preference Management Tools

| Tool Name          | Added in | v1.0 Status | Required Fields | Optional Fields             |
|--------------------|----------|-------------|-----------------|-----------------------------|
| `update_preference`| v0.1     | ✅ Supported | category        | config                      |
| `get_preferences`  | v0.1     | ✅ Supported | agent_id        | category_filter             |

---

## Breaking Changes Policy

### What Constitutes a Breaking Change?

In Semantic Versioning, a breaking change is defined as any change that would cause existing clients to break or malfunction. This includes:

1. **Removing an endpoint** (e.g., `/health`)
2. **Changing response schema structure** (removing fields, changing types)
3. **Adding required fields** to request parameters
4. **Changing authentication requirements** (enabling auth when previously disabled)
5. **Altering error response formats**

### What Does NOT Break Compatibility?

The following changes are considered non-breaking:

1. Adding new endpoints (`/metrics`, `/version`)
2. Adding optional parameters to existing requests
3. Adding new fields to responses
4. Improving performance without changing behavior
5. Bug fixes that restore expected behavior
6. Adding new tools to the MCP interface

### Deprecation Process

When we plan to remove or significantly change an endpoint/tool:

1. **Deprecation Notice** (v1.0 → v1.1): Add deprecation warning to docs and logs
2. **Sunset Period** (v1.1 → v1.2): Feature still works but emits warnings
3. **Removal** (v1.2+): Endpoint completely removed with migration guide

**Example Migration Path:**
```yaml
v0.2 -> v1.0: Safe upgrade (no breaking changes)
v1.0 -> v1.1: Safe upgrade (new optional features)
v1.1 -> v1.2: Plan migration for deprecated features
v1.2 -> v2.0: Major upgrade with breaking changes
```

---

## Authentication Backward Compatibility

### v1.0 Authentication Model

**Default Configuration:**
- `CNAA_AUTH_ENABLED=false` → No authentication required
- `CNAA_AUTH_ENABLED=true` → API Key authentication enforced

**API Key Format:**
```
sk-cnaa-{random-string-here}
```

**Authorization Header:**
```
Authorization: Bearer sk-cnaa-xxx
```

### Migration from v0.x

If you were using custom auth mechanisms in v0.x, migrate to the standard API Key system:

**Step 1**: Generate API keys
```bash
python3 -c "import secrets; print('sk-' + secrets.token_hex(16))"
```

**Step 2**: Update `.env`:
```ini
CNAA_AUTH_ENABLED=true
CNAA_API_KEYS='{"sk-key-001": {"agent_id": "agent-*", "permission": "read_write"}}'
```

**Step 3**: Update client code:
```python
headers = {
    "Authorization": f"Bearer sk-key-001",
    "Content-Type": "application/json"
}
```

---

## Error Response Compatibility

### Standard Error Format (v1.0)

```json
{
  "status": "error",
  "message": "Detailed error message",
  "code": "ERROR_CODE"  // Optional machine-readable error code
}
```

### HTTP Status Codes

| Code | Meaning                    | Usage                          |
|------|----------------------------|--------------------------------|
| 200  | OK                         | Successful request             |
| 201  | Created                    | Resource successfully created  |
| 400  | Bad Request                | Invalid input/validation error |
| 401  | Unauthorized               | Missing or invalid auth token  |
| 403  | Forbidden                  | Insufficient permissions       |
| 404  | Not Found                  | Resource not found             |
| 408  | Request Timeout            | Request took too long          |
| 429  | Too Many Requests          | Rate limit exceeded            |
| 500  | Internal Server Error      | Server-side failure            |
| 503  | Service Unavailable        | Temporarily down/maintenance   |

### Error Code Reference

| Error Code | Description                           | Fix                                      |
|------------|---------------------------------------|------------------------------------------|
| INVALID_INPUT | Request body malformed or missing required fields | Validate against schema before sending |
| AUTH_FAILED | Invalid or expired API key            | Check API key validity                   |
| PERMISSION_DENIED | User lacks required permissions | Verify agent_id and permission level     |
| STORAGE_ERROR | Database operation failed           | Check database connectivity              |
| RATE_LIMITED | Too many requests                   | Implement exponential backoff            |

---

## Client Library Compatibility

### Official CNAA Clients

All official CNAA client libraries guarantee backward compatibility:

- **Python SDK** (`cnaa-client-python`): Supports v0.2 and v1.0 APIs
- **TypeScript SDK** (`cnaa-client-typescript`): Supports v1.0 only

### Third-Party Clients

Third-party integrations should handle both v0.x and v1.0 gracefully until v0.x reaches end-of-life.

---

## Testing Backward Compatibility

### Automated Compatibility Tests

All releases include automated tests for:
- ✅ Existing endpoints work correctly
- ✅ Response schemas match documented formats
- ✅ Authentication behaves consistently
- ✅ Error messages remain human-readable

### Running Compatibility Tests

```bash
# Run full test suite including backward compatibility checks
python3 -m pytest tests/ -m integration --tb=short

# Run specific version compatibility tests
python3 -m pytest tests/ -k "backward_compat" -v
```

---

## Migration Guide: v0.2 → v1.0

### Summary of Changes

| Category | Change | Impact | Action Required |
|----------|--------|--------|-----------------|
| **New** | `/metrics` endpoint added | None | Optional to use |
| **New** | `/version` endpoint added | None | Optional to use |
| **Enhanced** | `/health` returns detailed status | Enhanced functionality | No action needed |
| **Version** | Package version bumped to 1.0.0 | N/A | Update dependencies |

### Steps to Upgrade

1. **Update Dependencies:**
   ```bash
   pip install --upgrade cnaa==1.0.0
   ```

2. **Restart Services:**
   ```bash
   # Cloud server
   python server.py --port 8080
   
   # Local clients will auto-detect v1.0 endpoints
   ```

3. **Verify Health Check:**
   ```bash
   curl http://localhost:8080/health
   # Should return comprehensive health status
   ```

4. **Test Integration:**
   ```bash
   ./scripts/test_cloud_connection.sh
   ```

### Rollback Plan

If issues arise after upgrading to v1.0:

1. **Downgrade Package:**
   ```bash
   pip install cnaa==0.2.0
   ```

2. **Verify Functionality:**
   ```bash
   curl http://localhost:8080/version
   # Should show version 0.2.0
   ```

---

## Future Roadmap

### v1.1 Planned Features
- WebSocket support for real-time updates
- Batch operations endpoint (`/mcp/batch`)
- GraphQL API alternative
- Improved rate limiting options

### v2.0 Planned Features (Long-term)
- Event streaming architecture
- Multi-cloud sync capabilities
- Advanced caching strategies
- Machine learning-powered memory compression

---

## Contact & Support

For API compatibility questions or migration assistance:

- **GitHub Issues**: Report backward compatibility bugs
- **Discussions**: Discuss proposed API changes
- **Email**: api-compatibility@cnaa.org (hypothetical)

---

*Last Updated: 2026-08-08*  
*v1.0 API Stability Commitment: We guarantee no breaking changes between v1.0.x versions.*
