"""Health check endpoint handler."""

from server.base_handler import BaseRequestHandler
from cnaa.config import get_config


class HealthHandler(BaseRequestHandler):
    """Handler for /health endpoint.
    
    Simple, synchronous health check for load balancers and monitoring.
    No async/await complexity.
    """
    
    def do_GET(self):
        """Handle GET requests to health endpoint."""
        if self.path == "/health":
            self._handle_health()
        else:
            self._send_error(404, "Not found")
    
    def _handle_health(self):
        """Return simple health status using config."""
        import sqlite3
        
        config = get_config()
        
        # Check database accessibility
        db_status = {config.database.db_path: "accessible"}
        
        try:
            if config.database.storage_type == "sqlite":
                conn = sqlite3.connect(config.database.db_path)
                conn.execute("SELECT COUNT(*) FROM sqlite_master")
                conn.close()
        except Exception as e:
            db_status[config.database.db_path] = f"error: {e}"
            status = "degraded"
        else:
            status = "healthy"
        
        response = {
            "status": status,
            "service": "CNAA Server v1.0.0",
            "uptime": "running",
            "database": db_status,
            "auth_enabled": config.auth.enabled
        }
        
        self._send_json_response(200, response)
