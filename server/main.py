#!/usr/bin/env python3
"""Server entry point - minimal code that sets up the application."""

import argparse
import logging
from pathlib import Path
from server.config import load_config, setup_logging
from server.handlers.mcp_handler import MCPServerHandler
from server.handlers.health_handler import HealthHandler

logger = logging.getLogger(__name__)


def create_handlers(config):
    """Create and configure all handlers."""
    from cloud.storage.unified import create_storage_backend
    
    # Create storage backend
    storage_type = config.get("storage_type", "sqlite")
    db_path = config.get("db_path", "./cnaa_data.db")
    
    backend = create_storage_backend(storage_type, db_path=db_path)
    
    # Initialize handler instances
    mcp_handler = MCPServerHandler(backend)
    health_handler = HealthHandler()
    
    return {
        'mcp': mcp_handler,
        'health': health_handler
    }


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="CNAA Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config)
    
    logger.info(f"Starting CNAA Server v1.0.0 on {args.host}:{args.port}")
    
    # Create handlers
    handlers = create_handlers(config)
    
    # Import and start server
    from http.server import HTTPServer
    from server.base_handler import BaseRequestHandler
    
    # Configure request handler with our handlers
    class CNAARequestHandler(BaseRequestHandler):
        handlers = handlers  # Class-level reference
    
    # Start server
    server = HTTPServer((args.host, args.port), CNAARequestHandler)
    
    try:
        logger.info("Server started successfully!")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        server.shutdown()


if __name__ == "__main__":
    main()
