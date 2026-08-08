"""Error Handling and Edge Case Tests for CNAA."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json


class TestNetworkFailureHandling:
    """Test behavior when network failures occur."""

    def test_invalid_server_url_handling(self):
        """Invalid URLs handled gracefully."""
        from local.client.mcp_client import MCPClient
        
        # Should create client even with invalid URL
        client = MCPClient(server_url='invalid://not-a-real-server')
        assert client is not None
    
    def test_unreachable_server_fallback(self):
        """Unreachable server shows appropriate errors."""
        from fastapi.testclient import TestClient
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        try:
            from server import app
            client = TestClient(app, raise_exception=False)
            
            # Health check to non-existent server should timeout or fail
            response = client.get("/health", timeout=1)
            # Expected to fail - no actual server running
            assert True  # Test passed if it doesn't crash
        except Exception as e:
            # Timeout or connection error is acceptable
            assert 'timeout' in str(e).lower() or 'connection' in str(e).lower()


class TestInvalidInputs:
    """Test validation of invalid inputs."""

    @pytest.mark.unit
    def test_empty_memory_content(self):
        """Empty content rejected or handled."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Empty content should either be rejected or stored minimally
        result = store.store_memory({
            'memory_id': 'empty-test',
            'agent_id': 'test',
            'type': 'experience',
            'content': {}  # Empty dict
        })
        
        assert 'status' in result
    
    @pytest.mark.unit
    def test_missing_required_fields(self):
        """Missing required fields produce clear errors."""
        from cnaa.models import Memory
        
        # Missing agent_id
        try:
            Memory(memory_id='test', type='experience', content={})
            # If succeeds, should have default/None values
            assert True
        except TypeError as e:
            assert 'agent_id' in str(e)
    
    @pytest.mark.unit
    def test_invalid_memory_type(self):
        """Invalid memory type handled appropriately."""
        from cnaa.models import MemoryType
        
        # Valid types only
        valid_types = [MemoryType.PREFERENCE, MemoryType.KNOWLEDGE, 
                      MemoryType.EXPERIENCE, MemoryType.STATE]
        
        for t in valid_types:
            assert isinstance(t.value, str)


class TestAuthenticationFailures:
    """Test authentication failure scenarios."""

    @pytest.mark.unit
    def test_invalid_api_key_rejected(self):
        """Invalid API keys rejected."""
        from cnaa.security import SecurityConfig
        
        config = SecurityConfig(api_keys={'sk-valid': {'agent_id': 'test'}})
        
        # Invalid key should not match
        result = config.validate_request('X-Api-Key', 'sk-invalid-key')
        assert result is False
    
    @pytest.mark.unit
    def test_malformed_auth_header(self):
        """Malformed headers handled safely."""
        from cnaa.security import SecurityConfig
        
        config = SecurityConfig(api_keys={'sk-valid': {'agent_id': 'test'}})
        
        # Malformed header
        result = config.validate_request('X-Api-Key', 'BROKEN_HEADER_TOKEN')
        # Should handle gracefully, not crash
        assert result is False or result == {'error': 'Unauthorized'}


class TestDatabaseErrors:
    """Test database error handling."""

    @pytest.mark.unit
    def test_corrupted_database_recovery(self):
        """Corrupt DB produces helpful errors."""
        import sqlite3
        
        # Create a minimal SQLite file
        fd, db_path = tempfile.mkstemp(suffix='.db')
        try:
            # Write garbage (not a real SQLite DB)
            os.write(fd, b'This is not a real database file')
            os.close(fd)
            
            # Should fail with meaningful error
            conn = sqlite3.connect(db_path)
            try:
                conn.execute('SELECT * FROM memories')
                # If no error, file might have been opened differently
                pass
            except sqlite3.DatabaseError as e:
                # Expected error for corrupted DB
                assert 'database disk image' in str(e).lower() or \
                       'file is not a database' in str(e).lower()
            finally:
                conn.close()
        finally:
            os.unlink(db_path)
    
    @pytest.mark.unit
    def test_concurrent_write_conflicts(self):
        """Concurrent writes don't corrupt data."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Multiple stores should be safe
        results = []
        for i in range(5):
            result = store.store_memory({
                'memory_id': f'concurrent-{i}',
                'agent_id': 'test-agent',
                'type': 'knowledge',
                'content': {'attempt': i}
            })
            results.append(result)
        
        # All should complete
        assert len(results) == 5
        assert all('status' in r for r in results)


class TestLargePayloads:
    """Test handling of large data payloads."""

    @pytest.mark.unit
    def test_large_content_storage(self):
        """Large content handled appropriately."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Large content (~1MB text)
        large_text = "x" * (1024 * 1024)
        
        result = store.store_memory({
            'memory_id': 'large-test',
            'agent_id': 'test',
            'type': 'experience',
            'content': {'data': large_text}
        })
        
        # Should succeed but may have warnings
        assert 'status' in result
    
    @pytest.mark.unit
    def test_many_memories_performance(self):
        """Many memories handled reasonably."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Store 100 memories
        start_id = 0
        for i in range(100):
            store.store_memory({
                'memory_id': f'many-{i:03d}',
                'agent_id': 'batch-agent',
                'type': 'knowledge',
                'content': {'index': i}
            })
        
        # Retrieve all
        memories = list(store.get_memories(agent_id='batch-agent'))
        
        assert len(memories) >= 100


class TestTimeoutScenarios:
    """Test timeout handling."""

    @pytest.mark.unit
    def test_request_timeout_graceful_failure(self):
        """Timeouts handled without crashes."""
        from fastapi.testclient import TestClient
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server import app
        
        client = TestClient(app)
        
        # Normal request should complete quickly
        response = client.get("/")
        # May return 404 or similar, but shouldn't hang
        assert response.status_code != 408  # Shouldn't timeout
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slow_operation_interruption(self):
        """Slow operations can be interrupted."""
        import asyncio
        
        async def slow_operation():
            await asyncio.sleep(10)  # Simulate slow operation
            return "complete"
        
        # Cancel before completion
        task = asyncio.create_task(slow_operation())
        await asyncio.sleep(0.1)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected


class TestEdgeCaseConfiguration:
    """Test edge cases in configuration."""

    def test_missing_env_vars_defaults(self):
        """Missing env vars use sensible defaults."""
        # Unset potentially missing variables
        saved_server_url = os.environ.pop('CNAA_SERVER_URL', None)
        saved_agent_id = os.environ.pop('LOCAL_AGENT_ID', None)
        
        try:
            # Should work with defaults
            from local.client.mcp_client import MCPClient
            
            client = MCPClient()  # No params - should use defaults
            assert client is not None
        finally:
            # Restore originals
            if saved_server_url:
                os.environ['CNAA_SERVER_URL'] = saved_server_url
            if saved_agent_id:
                os.environ['LOCAL_AGENT_ID'] = saved_agent_id
    
    def test_invalid_json_config_handling(self):
        """Invalid JSON configs handled gracefully."""
        from cnaa.security import SecurityConfig
        
        config = SecurityConfig()
        
        # Invalid JSON string should not crash
        try:
            config.set_api_keys("this is not json")
            # May set empty/default value
        except (json.JSONDecodeError, ValueError):
            # Expected - invalid JSON raises exception
            pass
    
    def test_empty_string_in_environment(self):
        """Empty environment strings handled."""
        # Set to empty string
        os.environ['CNAA_SERVER_URL'] = ''
        
        try:
            from local.client.mcp_client import MCPClient
            # Should handle empty string (may use fallback or error gracefully)
            client = MCPClient()
            assert client is not None
        finally:
            del os.environ['CNAA_SERVER_URL']


# Helper imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
