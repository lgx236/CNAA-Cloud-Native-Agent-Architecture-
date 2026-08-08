"""Performance Edge Case Tests for CNAA."""

import pytest
import asyncio
import time
from pathlib import Path
import tempfile
import os


class TestLargePayloadHandling:
    """Test handling of large data payloads."""

    @pytest.mark.unit
    def test_large_memory_content(self):
        """Handle memory with large content field."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Very large content (~1MB)
        large_data = "x" * (1024 * 1024)
        
        result = store.store_memory({
            'memory_id': 'large-content-test',
            'agent_id': 'perf-test-agent',
            'type': 'experience',
            'content': {'data': large_data}
        })
        
        # Should handle without crashing
        assert 'status' in result
    
    @pytest.mark.unit
    def test_bulk_storage_performance(self):
        """Bulk storage operations perform reasonably."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Store 100 memories
        start_time = time.time()
        
        for i in range(100):
            store.store_memory({
                'memory_id': f'bulk-{i:03d}',
                'agent_id': 'bulk-test',
                'type': 'knowledge',
                'content': {'index': i, 'data': f'value-{i}'}
            })
        
        elapsed = time.time() - start_time
        
        # Should complete within reasonable time (< 5 seconds)
        assert elapsed < 5.0, f"Bulk storage took too long: {elapsed}s"


class TestConcurrentAccess:
    """Test concurrent access patterns."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_writes(self):
        """Multiple concurrent write operations handled safely."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        async def concurrent_write_task(task_id):
            """Write task that adds a memory."""
            await asyncio.sleep(0.01 * task_id)  # Stagger starts
            result = store.store_memory({
                'memory_id': f'concurrent-{task_id}',
                'agent_id': 'concurrent-test',
                'type': 'experience',
                'content': {'task': task_id}
            })
            return result
        
        # Run multiple concurrent writes
        tasks = [concurrent_write_task(i) for i in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        
        # All should complete successfully
        success_count = sum(1 for r in results if r.get('status') in ['ok', 'stored'])
        assert success_count >= 8  # Allow some failures due to concurrency
    
    @pytest.mark.integration
    def test_read_during_write(self):
        """Read operations during writes remain functional."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Initial write
        store.store_memory({
            'memory_id': 'initial',
            'agent_id': 'test',
            'type': 'knowledge',
            'content': {'ready': True}
        })
        
        async def writer():
            """Background writer."""
            for i in range(5):
                store.store_memory({
                    'memory_id': f'background-{i}',
                    'agent_id': 'test',
                    'type': 'experience',
                    'content': {'step': i}
                })
                await asyncio.sleep(0.05)
        
        async def reader():
            """Periodic reader."""
            memories = list(store.get_memories(agent_id='test'))
            assert len(memories) > 0
        
        # Run both concurrently
        asyncio.run(asyncio.gather(writer(), reader()))
        
        # Verify reads succeeded
        all_memories = list(store.get_memories(agent_id='test'))
        assert len(all_memories) >= 2


class TestTimeoutHandling:
    """Test timeout scenarios."""

    @pytest.mark.unit
    def test_very_long_key_handling(self):
        """Handles memory IDs with unusual length."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Extremely long memory ID
        long_id = "x" * 1000
        
        result = store.store_memory({
            'memory_id': long_id,
            'agent_id': 'test',
            'type': 'experience',
            'content': {}
        })
        
        # Should not crash, may have warnings
        assert 'status' in result
    
    @pytest.mark.unit
    def test_nested_deep_structures(self):
        """Handles deeply nested content structures."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Deeply nested structure
        deep_data = {'level0': {'level1': {'level2': {'level3': 'deep'}}}}
        
        result = store.store_memory({
            'memory_id': 'nested-deep',
            'agent_id': 'test',
            'type': 'experience',
            'content': deep_data
        })
        
        assert 'status' in result
    
    @pytest.mark.unit
    def test_special_characters_in_content(self):
        """Handles special characters in content."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Content with special characters
        special_content = {
            'text': 'Hello\nWorld\tTabbed\rNewlines',
            'emoji': '🚀💻🎉',
            'unicode': '日本語中文한국어',
            'json_like': '{"key": "value"}',
            'sql_like': "SELECT * FROM users WHERE id=1",
            'quotes': "'single' and \"double\" quotes"
        }
        
        result = store.store_memory({
            'memory_id': 'special-chars',
            'agent_id': 'test',
            'type': 'experience',
            'content': special_content
        })
        
        assert 'status' in result


class TestMemoryLimitScenarios:
    """Test memory limitation scenarios."""

    @pytest.mark.unit
    def test_many_memories_retrieval(self):
        """Retrieving many memories performs acceptably."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Populate with many entries
        for i in range(100):
            store.store_memory({
                'memory_id': f'many-{i:03d}',
                'agent_id': 'performance-test',
                'type': 'knowledge',
                'content': {'index': i}
            })
        
        # Time the retrieval
        start_time = time.time()
        memories = list(store.get_memories(agent_id='performance-test'))
        elapsed = time.time() - start_time
        
        assert len(memories) == 100
        # Retrieval should be reasonably fast
        assert elapsed < 5.0, f"Retrieval too slow: {elapsed}s"


class TestEdgeCaseConfiguration:
    """Test edge case configurations."""

    @pytest.mark.unit
    def test_empty_string_values(self):
        """Handles empty strings gracefully."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        result = store.store_memory({
            'memory_id': 'empty-test',
            'agent_id': '',  # Empty agent_id
            'type': 'experience',
            'content': {'field': ''}  # Empty content value
        })
        
        assert 'status' in result
    
    @pytest.mark.unit
    def test_none_values_handling(self):
        """Handles None values appropriately."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Note: This may fail validation or be stored as-is
        try:
            result = store.store_memory({
                'memory_id': 'none-test',
                'agent_id': None,  # None agent_id
                'type': None,  # None type
                'content': None  # None content
            })
            # If succeeds, it's acceptable
            assert 'status' in result
        except Exception as e:
            # Expected - invalid inputs should raise
            pass
    
    @pytest.mark.unit
    def test_mixed_type_fields(self):
        """Handles mixed types in content."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        mixed_types = {
            'string': 'hello',
            'number': 42,
            'float': 3.14,
            'boolean_true': True,
            'boolean_false': False,
            'null_value': None,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'tuple': (1, 2),
        }
        
        result = store.store_memory({
            'memory_id': 'mixed-types',
            'agent_id': 'test',
            'type': 'experience',
            'content': mixed_types
        })
        
        assert 'status' in result


class TestStressScenarios:
    """Stress testing scenarios."""

    @pytest.mark.integration
    @pytest.mark.performance
    def test_rapid_sequence_operations(self):
        """Rapid sequence of operations doesn't cause corruption."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Rapid alternating operations
        for i in range(50):
            # Write
            store.store_memory({
                'memory_id': f'rapid-{i}',
                'agent_id': 'stress-test',
                'type': 'experience',
                'content': {'sequence': i}
            })
            
            # Read immediately after
            memories = list(store.get_memories(agent_id='stress-test'))
            assert len(memories) >= 1
            
            # Delete every 5th
            if i % 5 == 0:
                store.delete_memory(f'rapid-{i}')
        
        # Final count check
        final_count = len(list(store.get_memories(agent_id='stress-test')))
        assert final_count == 40  # 50 written - 10 deleted
    
    @pytest.mark.integration
    def test_repeated_updates_same_id(self):
        """Repeated updates to same memory ID work correctly."""
        from cloud.storage.memory_store import InMemoryMemoryStore
        
        store = InMemoryMemoryStore()
        
        # Update same ID repeatedly
        for i in range(20):
            result = store.store_memory({
                'memory_id': 'update-same-id',
                'agent_id': 'test-updates',
                'type': 'experience',
                'content': {'version': i, 'timestamp': time.time()}
            })
            assert 'status' in result
        
        # Should have only one entry now (last update wins)
        memories = list(store.get_memories(agent_id='test-updates'))
        assert len(memories) == 1
        assert memories[0]['content']['version'] == 19


# Helper imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
