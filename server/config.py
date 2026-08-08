"""Server configuration management."""

import os
from pathlib import Path
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Returns:
        Dictionary of configuration values with defaults
        
    Environment Variables:
        HOST: Server host (default: 0.0.0.0)
        PORT: Server port (default: 8080)
        STORAGE_TYPE: 'in_memory' or 'sqlite' (default: sqlite)
        DB_PATH: Database file path (default: ./cnaa_data.db)
        LOG_LEVEL: Logging level (default: INFO)
    """
    config = {
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8080")),
        "storage_type": os.getenv("STORAGE_TYPE", "sqlite"),
        "db_path": os.getenv("DB_PATH", "./cnaa_data.db"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }
    
    return config


def setup_logging(config: Dict[str, Any]) -> None:
    """Setup Python logging based on config."""
    import logging
    
    # Create logger
    logger = logging.getLogger("cnas.server")
    logger.setLevel(getattr(logging, config["log_level"]))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(console_handler)
    
    return logger
