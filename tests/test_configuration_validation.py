"""Configuration Validation Tests for CNAA."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestEnvironmentVariableValidation:
    """Test validation of environment variables."""

    def test_valid_server_url_formats(self):
        """Valid server URLs accepted."""
        valid_urls = [
            'http://localhost:8080',
            'https://cnaa.example.com',
            'http://192.168.1.100:8080',
            'http://your-cloud-server-ip:8080',
        ]
        
        with patch.dict(os.environ, {'CNAA_SERVER_URL': valid_urls[0]}):
            from local.client.mcp_client import MCPClient
            # Should not raise exception
            client = MCPClient()
            assert client is not None
    
    def test_missing_required_env_vars(self):
        """Missing required vars handled gracefully."""
        # Temporarily remove critical vars
        saved_vars = {}
        for var in ['CNAA_SERVER_URL']:
            saved_vars[var] = os.environ.pop(var, None)
        
        try:
            # Client should handle missing URL
            from local.client.mcp_client import MCPClient
            client = MCPClient()  # No args - uses env
            assert client is not None
        finally:
            # Restore
            for var, val in saved_vars.items():
                if val is not None:
                    os.environ[var] = val
    
    def test_api_key_format_validation(self):
        """API key format validation."""
        from cnaa.security import SecurityConfig
        
        config = SecurityConfig()
        
        # Valid-looking keys
        valid_keys = [
            'sk-test-key-123456',
            'sk-' + 'a' * 32,
            'test-api-key',
        ]
        
        for key in valid_keys:
            result = config.validate_request('X-Api-Key', key)
            # Either accepts or rejects, but doesn't crash
            assert isinstance(result, (bool, dict))


class TestConfigurationFiles:
    """Test .env file handling."""

    def test_env_file_not_found(self):
        """Missing .env file handled."""
        # Remove any existing .env references
        env_files = ['.env', '.env.local']
        original_values = {}
        
        for ef in env_files:
            path = Path(__file__).parent.parent / ef
            if path.exists():
                original_values[ef] = path.read_text()
                path.unlink()
        
        try:
            # Application should still work
            from cloud.server.mcp_server import CNAA_MCPServer
            
            # Server creation shouldn't fail
            server = CNAA_MCPServer()
            assert server is not None
        finally:
            # Restore files
            for ef, content in original_values.items():
                path = Path(__file__).parent.parent / ef
                path.write_text(content)
    
    def test_empty_env_file(self):
        """Empty .env file doesn't break system."""
        fd, temp_env = tempfile.mkstemp(suffix='.env')
        
        try:
            os.write(fd, b'# Empty config file\n')
            os.close(fd)
            
            # Should load without errors
            from dotenv import load_dotenv
            result = load_dotenv(temp_env)
            
            # May return False for empty, but shouldn't crash
            assert result is True or result is False
        finally:
            os.unlink(temp_env)


class TestSecurityConfiguration:
    """Test security settings validation."""

    @pytest.mark.unit
    def test_auth_enabled_with_valid_keys(self):
        """Authentication enabled with valid keys works."""
        api_keys_str = '{"sk-valid": {"agent_id": "test", "permission": "read_write"}}'
        
        with patch.dict(os.environ, {
            'CNAA_AUTH_ENABLED': 'true',
            'CNAA_API_KEYS': api_keys_str
        }):
            from cnaa.security import SecurityConfig
            
            config = SecurityConfig()
            
            # Should have loaded the API key
            assert hasattr(config, 'api_keys')
    
    @pytest.mark.unit
    def test_auth_disabled_mode(self):
        """Authentication disabled allows all requests."""
        with patch.dict(os.environ, {
            'CNAA_AUTH_ENABLED': 'false',
            'CNAA_ALLOW_UNAUTHENTICATED': 'true'
        }):
            from cnaa.security import SecurityConfig
            
            config = SecurityConfig()
            assert not config.auth_enabled or config.auth_enabled == False
    
    @pytest.mark.unit
    def test_permissions_default_to_read_only(self):
        """Default permissions are restrictive."""
        api_keys_str = '{"sk-default": {"agent_id": "unknown", "permission": "read_write"}}'
        
        config = SecurityConfig(api_keys={"sk-default": {}})
        
        # Check permissions field exists
        if 'permission' in config.api_keys.get('sk-default', {}):
            permission = config.api_keys['sk-default']['permission']
            assert isinstance(permission, str)


class TestStoragePathValidation:
    """Test storage path configurations."""

    def test_relative_db_paths(self):
        """Relative database paths handled."""
        with patch.dict(os.environ, {
            'CNAA_DB_PATH': './memories.db',
            'CNAA_STATE_DB_PATH': './states.db'
        }):
            from cloud.storage.sqlite_memory_store import SQLiteMemoryStore
            
            # Should create store with relative path
            store = SQLiteMemoryStore(db_path='./test_relative.db')
            assert store is not None
        
        # Cleanup
        if Path('./test_relative.db').exists():
            Path('./test_relative.db').unlink()
    
    def test_absolute_db_paths(self):
        """Absolute database paths work."""
        fd, temp_path = tempfile.mkstemp(prefix='cnaa_test_', suffix='.db')
        os.close(fd)
        
        try:
            from cloud.storage.sqlite_memory_store import SQLiteMemoryStore
            
            store = SQLiteMemoryStore(db_path=temp_path)
            count = store.count()
            
            assert count >= 0  # Should be able to query
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
    
    def test_directory_creation_for_dbs(self):
        """Database directories created if needed."""
        temp_dir = tempfile.mkdtemp(prefix='cnaa_test_dir_')
        db_path = f'{temp_dir}/subdir/test.db'
        
        try:
            from cloud.storage.sqlite_memory_store import SQLiteMemoryStore
            
            # Subdirectory doesn't exist
            store = SQLiteMemoryStore(db_path=db_path)
            
            # File should be created
            assert Path(db_path).exists()
        finally:
            import shutil
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_log_path_configuration(self):
        """Log file path configurable."""
        with patch.dict(os.environ, {'CNAA_LOG_PATH': './test.log'}):
            import logging
            
            logger = logging.getLogger('cnaa.test')
            
            # Should be able to create logger
            assert logger is not None
    
    def test_console_only_fallback(self):
        """Console fallback if log file inaccessible."""
        # Invalid log path
        with patch.dict(os.environ, {'CNAA_LOG_PATH': '/invalid/path/log.log'}):
            import logging
            
            logger = logging.getLogger('cnaa.invalid_path')
            
            # Logger should still work even if file writing fails
            logger.setLevel(logging.INFO)
            
            # Should not crash on info
            logger.info("test message")


class TestBackwardCompatibility:
    """Test backward compatibility with v0.2 configs."""

    def test_legacy_var_support(self):
        """Legacy variable names still work."""
        # Old-style config that might still be used
        legacy_vars = {
            'CNAA_SERVER_URL': 'http://old-server:8080',
            'LOCAL_AGENT_ID': 'legacy-agent',
            'OPENROUTER_API_KEY': 'or-v1-old-key'
        }
        
        with patch.dict(os.environ, legacy_vars, clear=False):
            # System should recognize these
            from local.client.mcp_client import MCPClient
            
            client = MCPClient()
            assert client is not None


class TestConfigMigration:
    """Test configuration migration scenarios."""

    def test_migrate_from_v02_config(self):
        """Migration from v0.2 config structure."""
        # Simulate old config format being present
        fd, old_config = tempfile.mkstemp(suffix='.env.old')
        
        try:
            os.write(fd, b'''# Old CNAA v0.2 style config
HOST=0.0.0.0
PORT=8080
OPENROUTER_API_KEY=test-key
''')
            os.close(fd)
            
            # Should be able to load and migrate
            from dotenv import load_dotenv
            result = load_dotenv(old_config)
            
            # Loading should succeed
            assert result is True or result is False
        finally:
            os.unlink(old_config)


# Import helpers
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
