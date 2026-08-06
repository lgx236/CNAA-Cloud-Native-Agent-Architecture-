# CNAA Development Standards & Best Practices

> **Version**: 0.2.0 | **Date**: 2026-08-06  
> **Purpose**: Code quality, readability, and professional standards for CNAA development

---

## 📋 Table of Contents

1. [Code Structure](#code-structure)
2. [Naming Conventions](#naming-conventions)
3. [Documentation Requirements](#documentation-requirements)
4. [Testing Guidelines](#testing-guidelines)
5. [Error Handling](#error-handling)
6. [Performance Considerations](#performance-considerations)
7. [Security Practices](#security-practices)
8. [Git Workflow](#git-workflow)

---

## Code Structure

### Directory Organization

```
project_root/
├── cnaa/                    # Core library (reusable code)
│   ├── models.py           # Data definitions
│   ├── schemas.py          # JSON Schema definitions
│   ├── tools.py            # MCP tool definitions
│   ├── security.py         # Authentication & authorization
│   ├── adapters/           # Agent framework adapters
│   └── __init__.py         # Public API exports
│
├── cloud/                   # Cloud layer (server-side)
│   ├── server/             # HTTP Server implementation
│   └── storage/            # Database backends
│
├── local/                   # Local layer (client-side)
│   ├── client/             # HTTP clients
│   ├── memory/             # Instant memory (local only)
│   └── state/              # Local state cache
│
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
│
├── examples/                # Usage examples
│   ├── simple_demo.py      # Beginner-friendly
│   └── advanced_demo.py    # Production-ready
│
├── docs/                    # Documentation
│   ├── user_guide.md       # User documentation
│   ├── api_reference.md    # API documentation
│   └── development_guide.md # Developer documentation
│
├── scripts/                 # Automation scripts
└── .github/                 # GitHub configurations
```

### File Layout Rules

**Rule 1**: Max file size - **600 lines per file**
- If larger, split into logical modules
- Create sub-packages if needed

**Rule 2**: Import order
```python
# ✅ CORRECT ORDER
from datetime import datetime       # Standard library
from typing import Dict, List       # Standard library + generics

import requests                     # Third-party
import pydantic                     # Third-party

from cnaa.adapters import BaseCNAAAdapter  # Local package
from local.client import CNAA_MCPClient     # Local package
```

```python
# ❌ WRONG ORDER (mixed imports)
import os
from cnaa.models import Memory
from typing import List
import requests
```

**Rule 3**: Constants at top of module
```python
# ✅ Good practice
API_TIMEOUT = 30  # seconds
DEFAULT_PORT = 8080
MAX_MEMORY_SIZE = 1024 * 1024  # 1MB

def main():
    pass
```

---

## Naming Conventions

### Files

| Type | Format | Example |
|------|--------|---------|
| Module files | `snake_case.py` | `memory_store.py`, `api_handler.py` |
| Class files | `pascal_case.py` | `CNAA_MCPServer.py` |
| Test files | `test_<module>.py` | `test_models.py`, `test_security.py` |
| Config files | `.env.example`, `pyproject.toml` |

### Classes

**Rule**: PascalCase with descriptive prefixes

```python
# ✅ GOOD
class CNAA_MCPServer:           # Prefix indicates purpose
    pass

class BaseCNAAAdapter:          # ABC prefix for base class
    pass

class LangChainCNAAMixin:       # Framework + feature pattern
    pass
```

```python
# ❌ BAD
class Server:                   # Too generic
    pass

class Adapter:                  # Missing specificity
    pass
```

### Functions and Methods

**Rule**: snake_case, verb-based names for actions

```python
# ✅ Action verbs
def store_memory():             # Write operation
def get_memory():               # Read operation
def delete_memory():            # Delete operation
def update_state():             # Update operation
def validate_request():         # Validation
def process_task():             # Processing
```

```python
# ❌ Ambiguous names
def handle():                   # What does it handle?
def process():                  # Process what?
def check():                    # Check what?
```

### Variables

**Rule**: Descriptive, single-word when possible

```python
# ✅ Clear intent
agent_id: str
memory_config: dict
completion_score: float
response_data: list

# ✅ Short in loops
for item in items:
    yield item

for line in lines:
    print(line.strip())
```

```python
# ❌ Too short / ambiguous
a: str                          # What is 'a'?
x: dict                         # What is 'x'?
data: Any                       # Too vague
```

### Constants

**Rule**: UPPER_SNAKE_CASE, all caps for global constants

```python
# ✅ Global constants
API_KEY_ENABLED: bool = True
DEFAULT_TIMEOUT: int = 30
MAX_RETRIES: int = 3

# ✅ Module-level constants
HTTP_HEADER_AUTH = "Authorization"
CONTENT_TYPE_JSON = "application/json"
```

```python
# ❌ Using mixed case for constants
ApiKeyEnabled = True            # Looks like a variable
default_timeout = 30            # Should be uppercase
```

### Boolean Values

**Rule**: Use predicates for boolean variables/methods

```python
# ✅ Predicates
is_enabled: bool
has_permission: bool
should_retry: bool
user_authenticated: bool

def is_valid_request() -> bool:
    pass

def has_access_rights(user_id: str) -> bool:
    pass
```

```python
# ❌ Non-predicate booleans
enabled: bool
valid: bool
```

---

## Documentation Requirements

### All Public APIs Must Have

#### 1. Module Docstring

```python
"""
Module: Security Implementation

Provides API Key authentication and permission control for CNAA MCP Server.

Components:
- APIKeyAuthConfig: Authentication configuration dataclass
- validate_api_key(): Verify token authenticity
- check_permissions(): Enforce read/write access control

Usage Example:
    >>> auth_config = APIKeyAuthConfig(api_keys=["admin", "developer"])
    >>> handler.auth_config = auth_config
    >>> if auth_config.validate_api_key(request.headers.get("Authorization")):
    ...     return handle_mcp_request()
    ... else:
    ...     return deny_access()
"""
```

#### 2. Function/Method Docstrings

Use Google-style or NumPy-style format:

```python
def store_memory(
    self,
    agent_id: str,
    memory_id: str,
    memory_type: MemoryType | str,
    content: Dict[str, Any],
    tags: Optional[List[str]] = None,
    completion_score: float = 1.0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Store a memory in CNAA cloud.

    Stores task experiences, knowledge, or conversation history with optional
    scoring metadata for future retrieval prioritization.

    Args:
        agent_id: Unique identifier for the agent storing the memory
        memory_id: Custom memory identifier (must be unique within agent)
        memory_type: Type classification ('long_term' or 'short_term')
        content: Dictionary containing the actual memory content
        tags: Optional categorization tags for filtering
        completion_score: Success score [0.0, 1.0] for priority ranking
        metadata: Additional structured information about the memory

    Returns:
        Dictionary with confirmation details:
        {
            "status": "ok",
            "memory_id": str,
            "timestamp": str (ISO format),
            "message": str
        }

    Raises:
        RuntimeError: If CNAA client not initialized
        ValueError: If completion_score is outside [0.0, 1.0] range
        
    Example:
        >>> agent = MyAgent(server_url="http://localhost:8080")
        >>> result = agent.store_memory(
        ...     agent_id="langchain-demo",
        ...     memory_id="task-123",
        ...     memory_type="long_term",
        ...     content={"query": "Analyze sales", "result": {...}},
        ...     tags=["sales", "analysis"],
        ...     completion_score=0.95
        ... )
        >>> print(result["status"])
        ok
    """
```

#### 3. Class Docstrings

```python
class BaseCNAAAdapter(ABC):
    """
    Abstract base class defining the adapter contract for all CNAA integrations.

    Provides common functionality shared across all agent framework adapters:
    
    Core Responsibilities:
    - HTTP Client management (Layer 1)
    - Unified interface definition (Layer 2)
    - Template methods for customization (Layer 3)

    Architecture Pattern:
    - Uses Mix-in pattern to add memory capabilities without inheritance conflicts
    - Delegates to HTTP client for network communication
    - Defines abstract lifecycle hooks for framework-specific behavior

    Subclasses Must Implement:
    - on_agent_start(agent_id): Initialization hook
    - on_task_complete(agent_id, task_result): Success handling
    - on_error(agent_id, error): Error logging

    Example (LangChain Integration):
        >>> from cnaa.adapters.langchain import LangChainCNAAMixin
        >>> 
        >>> class MyAgent(LangChainCNAAMixin, AgentExecutor):
        ...     agent_id = "my-langchain-agent"
        ...     
        ...     def _call(self, inputs):
        ...         result = super()._call(inputs)
        ...         self.on_task_complete(self.agent_id, result)
        ...         return result
    
    See Also:
        - docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md
        - docs/AGENT_INTEGRATION_GUIDE.md
    """
```

### When Comments Are Required

**Required comments:**
1. Complex algorithms (>10 lines non-trivial logic)
2. Workarounds explaining why something is done
3. Performance optimizations
4. External system dependencies
5. Security-critical operations

**Example:**
```python
# NOTE: Using exponential backoff to prevent server overload
# First retry: 1s delay, Second: 2s, Third: 4s max
retry_delay = min(4, 2 ** attempt_count)
time.sleep(retry_delay)

# SECURITY: Always sanitize input before database operations
# Prevents SQL injection attacks on agent_id field
sanitized_agent_id = agent_id.replace("'", "")
```

### Never Include

❌ **Obvious explanations:**
```python
count += 1  # increment count by one (DON'T DO THIS)
```

❌ **Outdated TODOs:**
```python
# TODO: Fix this later (ALREADY FIXED IN V0.2)
```

❌ **Internal implementation details:**
```python
# This calls the third parameter which is the config object
result = self._process(config)
```

---

## Testing Guidelines

### Test Coverage Requirements

**Minimum coverage levels:**
- **Core modules** (cnaa/*): ≥95%
- **Storage layers**: ≥90%
- **Integration points**: 100%
- **Public API surface**: 100%

### Test Structure

```python
# ✅ ORGANIZED TESTS
class TestMemoryModel(TestCase):
    """Unit tests for Memory data model"""
    
    def test_valid_memory_creation(self):
        """Should create memory with valid data"""
        pass
    
    def test_empty_content_handling(self):
        """Should handle empty content gracefully"""
        pass
    
    def test_invalid_completion_score(self):
        """Should raise ValueError for out-of-range scores"""
        pass


class TestCNAAAdapterIntegration(TestCase):
    """Integration tests for adapter layer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = MagicMock(spec=CNAA_MCPClient)
        self.adapter = BaseCNAAAdapter.__new__(BaseCNAAAdapter)
        self.adapter._client = self.mock_client
    
    def test_store_memory_http_call(self):
        """Should make correct HTTP request to cloud server"""
        pass
    
    def test_cross_framework_memory_sharing(self):
        """Should allow different agents to share memories"""
        pass
```

### Test Naming Convention

Format: `test_<scenario>_<expected_behavior>()`

```python
# ✅ CLEAR NAMES
def test_memory_retrieval_with_valid_id():
    """Should return stored memory given valid ID"""
    pass

def test_authentication_with_invalid_api_key():
    """Should reject request with expired key"""
    pass

def test_concurrent_agent_access_no_conflicts():
    """Should handle simultaneous requests without race conditions"""
    pass
```

```python
# ❌ AMBIGUOUS NAMES
def test_something():           # What?
def test_case_1():              # Unclear
def basic_test():               # Not specific enough
```

### Running Tests

```bash
# Full test suite
pytest tests/ -v --cov=cnaa --cov-report=html

# Specific test category
pytest tests/test_models.py tests/test_scoring_system.py -v

# Distributed system tests
./scripts/run_distributed_tests.sh all

# Quick smoke tests
pytest tests/test_integration.py::TestIntegrationTests::test_basic_workflow -v
```

---

## Error Handling

### Exception Types

Define custom exceptions for domain-specific errors:

```python
# cnaa/security.py
class APIKeyValidationError(Exception):
    """Raised when API key validation fails"""
    pass

class PermissionDeniedError(Exception):
    """Raised when access control blocks operation"""
    pass

# cnaa/storage.py
class MemoryNotFoundError(Exception):
    """Raised when requested memory doesn't exist"""
    pass

class StorageError(Exception):
    """Base exception for storage backend errors"""
    pass
```

### Error Response Format

All error responses must follow this structure:

```python
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable description",
        "details": {                      # Optional, debug info
            "field": "problematic_field",
            "value": "invalid_value",
            "reason": "validation_failed"
        },
        "timestamp": "2026-08-06T20:30:00Z"
    }
}
```

### Logging Best Practices

```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD LOGGING
logger.info("User %s authenticated successfully", user_id)
logger.warning("Rate limit exceeded for agent %s", agent_id)
logger.error("Failed to store memory: %s", str(error), exc_info=True)

# ❌ BAD PRACTICES
print("Error occurred")                           # No log level
logger.error(f"Error: {exception}")               # f-string overhead
logger.critical("System failure!")                # Overly dramatic
```

### Try-Except Patterns

```python
# ✅ SPECIFIC EXCEPTION HANDLING
try:
    result = self._store_in_database(memory_config)
except sqlite3.IntegrityError as e:
    logger.warning("Duplicate memory detected: %s", str(e))
    return {"error": "MEMORY_EXISTS"}
except ConnectionError as e:
    logger.error("Database connection failed: %s", str(e), exc_info=True)
    return {"error": "SERVICE_UNAVAILABLE"}

# ❌ TOO BROAD
try:
    result = self._store_in_database(memory_config)
except Exception as e:
    logger.error("Something went wrong")
    return {"error": "UNKNOWN"}
```

---

## Performance Considerations

### Time Complexity Targets

| Operation | Target Complexity | Notes |
|-----------|-------------------|-------|
| Memory lookup by ID | O(1) | Hash-based index |
| List memories | O(n/k) | n total memories, k limit |
| Update state | O(1) | In-memory dictionary |
| Scoring algorithm | O(1) | Pre-computed values |

### Avoid Common Pitfalls

**PITFALL 1: N+1 Query Problem**

```python
# ❌ BAD: One query per loop iteration
memories = []
for agent_id in agent_ids:
    memos = db.query("SELECT * FROM memories WHERE agent_id = ?", agent_id)
    memories.extend(memos)

# ✅ GOOD: Single batch query
placeholders = ",".join(["?" for _ in agent_ids])
query = f"SELECT * FROM memories WHERE agent_id IN ({placeholders})"
memories = db.query(query, agent_ids)
```

**PITFALL 2: Unnecessary Object Creation**

```python
# ❌ BAD: Creating objects in hot path
def calculate_priority(memory):
    config = MemoryConfig(                      # New object each call
        agent_id=memory.agent_id,
        content=memory.content,
        tags=memory.tags,
        # ...
    )
    return compute_score(config)

# ✅ GOOD: Reuse pre-configured objects
_PRIORITY_CACHE = {}

def calculate_priority(memory):
    cache_key = f"{memory.agent_id}:{memory.memory_id}"
    if cache_key not in _PRIORITY_CACHE:
        _PRIORITY_CACHE[cache_key] = compute_score(memory)
    return _PRIORITY_CACHE[cache_key]
```

### Memory Limits

```python
# Maximum memory payload size (1MB)
MAX_PAYLOAD_SIZE = 1024 * 1024

def validate_payload_size(data: bytes) -> bool:
    """Ensure payload doesn't exceed limits"""
    if len(data) > MAX_PAYLOAD_SIZE:
        logger.warning("Payload too large: %d bytes", len(data))
        return False
    return True
```

---

## Security Practices

### API Key Management

```python
# ✅ CORRECT: Hash comparison
from hashlib import sha256

stored_hash = sha256(api_key.encode()).hexdigest()
provided_hash = sha256(input_key.encode()).hexdigest()

if stored_hash == provided_hash:
    grant_access()

# ❌ WRONG: Plain text comparison
if api_key == input_key:          # Security risk!
    grant_access()
```

### Input Validation

```python
# ✅ Validate ALL external inputs
def validate_agent_id(agent_id: str) -> bool:
    """Check agent ID format and length"""
    if not isinstance(agent_id, str):
        return False
    
    if len(agent_id) < 3 or len(agent_id) > 64:
        return False
    
    # Only alphanumeric and underscores
    if not re.match(r"^[a-zA-Z0-9_]+$", agent_id):
        return False
    
    return True

# ❌ Trusting user input
agent_id = request.json["agent_id"]   # UNSAFE!
```

### Sanitization Before DB Operations

```python
# ✅ Escape special characters
def sanitize_for_sql(value: str) -> str:
    """Prevent SQL injection"""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    return conn.execute("SELECT ?", (value,)).fetchone()[0]

# ❌ Manual string manipulation (EASILY BREACHABLE)
safe_input = user_input.replace("'", "").replace('"', '')
query = f"SELECT * FROM table WHERE id = '{safe_input}'"
```

---

## Git Workflow

### Branch Naming Convention

```bash
# Feature branches
git checkout -b feat/add-cnaa-adapters
git checkout -b feat/multi-language-clients

# Bug fixes
git checkout -b fix/http-client-timeout
git checkout -b fix/memory-storage-leak

# Documentation
git checkout -b docs/update-readme
git checkout -b docs/add-api-reference
```

### Commit Message Format

```bash
# Format: <type>(<scope>): <description>

types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation changes
  style:    Code style changes (formatting)
  refactor: Code restructuring (no behavior change)
  test:     Adding/updating tests
  chore:    Maintenance tasks

examples:
  feat(adapters): Add universal agent framework integration
  fix(storage): Resolve SQLite connection timeout issue
  docs(readme): Rewrite with integration examples
  refactor(adapter_base): Extract HTTP client initialization
```

### Pull Request Checklist

Before submitting PR:

- [ ] Code passes all tests (`pytest tests/ -v`)
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] CI builds pass
- [ ] Code coverage ≥ 90%
- [ ] Changelog updated (if applicable)

---

## 🎯 Quick Reference Card

### File Sizes
- Maximum: **600 lines**
- Typical modules: **150-300 lines**

### Lines of Code
- Functions: **< 30 lines**
- Classes: **< 500 lines**
- Modules: **< 600 lines**

### Test Coverage
- Core: **≥95%**
- Integration: **100%**

### Performance Targets
- Memory lookup: **O(1)**
- List operation: **O(n/k)**

### Security Checks
- ✅ Input validation
- ✅ SQL sanitization  
- ✅ API key hashing
- ✅ Rate limiting

---

**Last Updated**: 2026-08-06  
**Maintained By**: CNAA Development Team
