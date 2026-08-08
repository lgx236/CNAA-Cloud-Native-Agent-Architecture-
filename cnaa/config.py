"""CNAA configuration management - centralized, simple, intuitive.

This module provides a unified way to configure CNAA using environment variables
or explicit Python objects. Follows the principle of simplicity and intuition.

Quick Start:
    # Simple default configuration
    config = CNAAConfig()
    
    # Custom configuration
    config = CNAAConfig(
        host="0.0.0.0",
        port=8080,
        auth_enabled=True
    )
    
    # From environment variables
    config = CNAAConfig.from_env()
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    storage_type: str = "sqlite"  # 'sqlite' or 'in_memory'
    db_path: str = "./cnaa_data.db"
    
    def __post_init__(self):
        if self.storage_type not in ("sqlite", "in_memory"):
            raise ValueError(f"Invalid storage type: {self.storage_type}")
        
        # Ensure directory exists for SQLite
        if self.storage_type == "sqlite":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)


@dataclass  
class AuthConfig:
    """Authentication configuration."""
    
    enabled: bool = False
    allow_unauthenticated: bool = True
    
    # API keys mapping: key -> {agent_id, permission}
    api_keys: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Load from environment variables.
        
        Environment Variables:
            CNAA_AUTH_ENABLED: "true" or "false" (default: false)
            CNAA_ALLOW_UNAUTHENTICATED: "true" or "false" (default: true)
            CNAA_API_KEYS: JSON string mapping of keys (default: {})
        """
        return cls(
            enabled=os.getenv("CNAA_AUTH_ENABLED", "false").lower() == "true",
            allow_unauthenticated=os.getenv("CNAA_ALLOW_UNAUTHENTICATED", "true").lower() == "true",
            api_keys=_parse_api_keys_from_env(),
        )


def _parse_api_keys_from_env() -> Dict[str, Dict[str, Any]]:
    """Parse API keys from environment variable."""
    import json
    
    keys_str = os.getenv("CNAA_API_KEYS", "{}")
    
    try:
        return json.loads(keys_str)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid CNAA_API_KEYS format: {e}")
        return {}


@dataclass
class LoggingConfig:
    """Logging configuration."""
    
    level: str = "INFO"
    file_path: str = "./cnaa.log"
    
    def __post_init__(self):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}. Must be one of {valid_levels}")
        
        # Ensure directory exists
        Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)


@dataclass 
class ServerConfig:
    """Server configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 1
    debug: bool = False
    
    def __post_init__(self):
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port number: {self.port}")
        if not (1 <= self.workers <= 32):
            raise ValueError(f"Invalid worker count: {self.workers}")


@dataclass
class CNAAConfig:
    """Main CNAA configuration class.
    
    All configuration options are organized into logical groups:
    - server: HTTP server settings
    - database: Storage backend settings
    - auth: Authentication settings
    - logging: Logging settings
    
    This makes it intuitive to find and modify settings.
    """
    
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig.from_env)
    logging: LoggingConfig = field(default_factory=lambda: LoggingConfig())
    
    @classmethod
    def from_env(cls) -> "CNAAConfig":
        """Create configuration from all environment variables.
        
        This is the recommended way to create production configurations.
        """
        import os
        
        # Parse each section separately
        database = DatabaseConfig(
            storage_type=os.getenv("STORAGE_TYPE", "sqlite"),
            db_path=os.getenv("DB_PATH", "./cnaa_data.db")
        )
        
        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=os.getenv("LOG_PATH", "./cnaa.log")
        )
        
        server_config = ServerConfig(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8080")),
        )
        
        return cls(
            server=server_config,
            database=database,
            auth=AuthConfig.from_env(),
            logging=logging_config,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "workers": self.server.workers,
                "debug": self.server.debug
            },
            "database": {
                "storage_type": self.database.storage_type,
                "db_path": self.database.db_path
            },
            "auth": {
                "enabled": self.auth.enabled,
                "allow_unauthenticated": self.auth.allow_unauthenticated,
                "api_keys_count": len(self.auth.api_keys)
            },
            "logging": {
                "level": self.logging.level,
                "file_path": self.logging.file_path
            }
        }
    
    def __repr__(self):
        """Simple representation showing key settings."""
        return f"CNAAConfig(host={self.server.host}, port={self.server.port}, auth={'enabled' if self.auth.enabled else 'disabled'})"


# ============================================================================
# GLOBAL CONFIGURATION INSTANCE
# ============================================================================

_default_config: Optional[CNAAConfig] = None


def get_config() -> CNAAConfig:
    """Get the global configuration instance.
    
    Returns the same instance throughout the application lifecycle.
    Thread-safe for read operations.
    """
    global _default_config
    if _default_config is None:
        _default_config = CNAAConfig.from_env()
    return _default_config


def set_config(config: CNAAConfig) -> None:
    """Set the global configuration instance.
    
    Use this to override the default configuration programmatically.
    """
    global _default_config
    _default_config = config
