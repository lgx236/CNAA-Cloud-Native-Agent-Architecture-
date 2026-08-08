"""Health check endpoint handler."""

from server.base_handler import BaseRequestHandler


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
        """Return simple health status."""
        import sqlite3
        from pathlib import Path
        
        # Check databases exist and are accessible
        db_files = ["cnaa_data.db"]
        
        status = {
            "status": "healthy",
            "service": "CNAA Server v1.0.0",
            "uptime": "running"
        }
        
        # Verify database accessibility
        for db_file in db_files:
            if Path(db_file).exists():
                try:
                    conn = sqlite3.connect(db_file)
                    conn.execute("SELECT COUNT(*) FROM sqlite_master")
                    conn.close()
                    status["databases"] = {db_file: "accessible"}
                except Exception as e:
                    status["status"] = "degraded"
                    status["errors"] = [str(e)]
            else:
                status["databases"] = {db_file: "not_found"}
        
        self._send_json_response(200, status)
