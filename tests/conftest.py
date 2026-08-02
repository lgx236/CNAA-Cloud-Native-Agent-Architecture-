"""Pytest configuration and parallel test execution support for CNAA.

This module provides:
1. Conftest fixtures for common test patterns
2. Parallel test execution markers
3. Coverage configuration
4. Test categorization helpers
"""

import os
import pytest
import time
from datetime import datetime


# ===================================================================
# Markers for test categorization
# ===================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", 
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", 
        "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", 
        "performance: marks performance/benchmark tests"
    )
    config.addinivalue_line(
        "markers", 
        "large: marks large-scale tests (>1000 ops)"
    )
    config.addinivalue_line(
        "markers", 
        "regression: marks regression prevention tests"
    )


# ===================================================================
# Autouse fixtures for timing and setup/teardown
# ===================================================================

@pytest.fixture(autouse=True)
def timer(request):
    """Automatically time each test and report if it exceeds threshold."""
    start_time = time.time()
    
    # Get timeout from marker if present
    timeout_marker = request.node.get_closest_marker("timeout")
    timeout = timeout_marker.args[0] if timeout_marker else None
    
    yield
    
    elapsed = time.time() - start_time
    
    # Report if test was marked as slow
    if request.node.get_closest_marker("slow"):
        pytest.warns(UserWarning, f"Slow test: {request.node.name} took {elapsed:.2f}s")


@pytest.fixture
def random_agent_id():
    """Generate unique agent ID for each test."""
    return f"test-agent-{datetime.now().timestamp()}"


@pytest.fixture
def random_memory_id():
    """Generate unique memory ID for each test."""
    return f"mem-{int(time.time()*1000)}"


# ===================================================================
# Helper utilities
# ===================================================================

class TestStats:
    """Track test execution statistics."""
    
    def __init__(self):
        self.start_time = None
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.skip_count = 0
        
    def start(self):
        self.start_time = time.time()
        
    def end(self):
        return time.time() - self.start_time
        
    def summary(self):
        total = self.test_count
        duration = self.end()
        print(f"\n{'='*60}")
        print(f"Test Summary:")
        print(f"  Total: {total}")
        print(f"  Passed: {self.pass_count}")
        print(f"  Failed: {self.fail_count}")
        print(f"  Skipped: {self.skip_count}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Rate: {total/duration:.1f} tests/sec")
        print(f"{'='*60}")


test_stats = TestStats()
test_stats.start()


def pytest_runtest_logreport(report):
    """Log test results to stats."""
    if report.when == 'call':
        test_stats.test_count += 1
        if report.passed:
            test_stats.pass_count += 1
        elif report.failed:
            test_stats.fail_count += 1
        elif report.skipped:
            test_stats.skip_count += 1


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach test result to item for later access."""
    outcome = yield
    report = outcome.get_result()
    
    setattr(item, f"result_{report.when}", report)


# ===================================================================
# Convergence testing helpers
# ===================================================================

@pytest.fixture
def convergence_test_runner():
    """Run a test multiple times and verify consistency."""
    def run(fn, iterations=10):
        """Run fn `iterations` times and check all produce same result."""
        results = [fn() for _ in range(iterations)]
        first = results[0]
        assert all(r == first for r in results), \
            f"Results not consistent across {iterations} iterations"
        return results
    
    return run


# ===================================================================
# Large-scale test runner
# ===================================================================

@pytest.mark.parametrize("scale_factor", [100, 500, 1000])
def test_scale_consistency(scale_factor):
    """Verify tests scale linearly with data size."""
    # This is just a template - actual implementation goes in test file
    pass


# ===================================================================
# Performance benchmark fixture
# ===================================================================

@pytest.fixture
def performance_benchmarker():
    """Measure performance of operations."""
    bench = {
        "operations": [],
    }
    
    def measure(name, fn, iterations=1):
        """Measure time to execute fn N times."""
        start = time.perf_counter()
        for _ in range(iterations):
            fn()
        end = time.perf_counter()
        
        total = end - start
        avg = total / iterations * 1000  # ms per op
        rate = iterations / total  # ops per second
        
        result = {
            "name": name,
            "iterations": iterations,
            "total_seconds": total,
            "avg_ms": avg,
            "ops_per_sec": rate,
        }
        
        bench["operations"].append(result)
        return result
    
    measure.benchmarks = lambda: bench["operations"]
    return measure


# ===================================================================
# Cleanup helpers
# ===================================================================

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


# ===================================================================
# Test isolation helpers
# ===================================================================

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
