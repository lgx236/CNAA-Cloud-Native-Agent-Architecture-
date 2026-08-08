"""Base request handler with common functionality."""

from http.server import BaseHTTPRequestHandler, HTTPServer


class BaseRequestHandler(BaseHTTPRequestHandler):
    """Base class for all request handlers.
    
    Provides common functionality:
    - JSON response formatting
    - Error handling
    - Request logging
    
    Subclasses should implement specific handler methods.
    """
    
    # Class-level handlers dictionary (set by main.py)
    handlers = {}
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response with proper headers."""
        import json
        
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode("utf-8"))
    
    def _send_error(self, status_code: int, message: str):
        """Send error response."""
        self._send_json_response(status_code, {
            "status": "error",
            "message": message
        })
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("%s - %s", self.address_string(), format % args)
