"""Pytest fixtures for CNAA tests."""

import pytest
import time
from datetime import datetime

def pytest_configure(config):
    """Register custom markers once per session."""
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "performance: Performance/benchmark tests")
    config.addinivalue_line("markers", "large: Large-scale operations (>1000 ops)")
    config.addinivalue_line("markers", "regression: Regression prevention tests")


@pytest.fixture
def random_agent_id():
    """Generate unique agent ID for each test."""
    return f"test-agent-{datetime.now().timestamp()}"


@pytest.fixture
def random_memory_id():
    """Generate unique memory ID for each test."""
    return f"mem-{int(time.time()*1000)}"


@pytest.fixture(scope="module")
def cleanup_on_module_finish(request):
    """Collect cleanup callbacks for module-level teardown."""
    cleanup_callbacks = []
    
    def add(callback):
        cleanup_callbacks.append(callback)
    
    yield add
    
    # Execute all cleanup callbacks after module tests complete
    for cb in cleanup_callbacks:
        try:
            cb()
        except Exception as e:
            pytest.warns(f"Cleanup callback failed: {e}")


@pytest.fixture
def isolated_storage():
    """Provide storage that's automatically cleaned between tests."""
    from cloud.storage.memory_store import InMemoryMemoryStore
    from cloud.storage.state_store import InMemoryStateStore
    
    store = InMemoryMemoryStore()
    state_store = InMemoryStateStore()
    
    yield store, state_store
    
    # Automatic cleanup
    store.clear()
    state_store.clear()
