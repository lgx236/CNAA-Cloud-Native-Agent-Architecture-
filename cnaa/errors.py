"""Unified error hierarchy for CNAA.

Provides consistent, intuitive error handling across all modules.

Usage:
    from cnaa.errors import StorageError, NotFoundError
    
    try:
        memory = store.find(memory_id)
    except NotFoundError as e:
        return {"status": "not_found", "message": str(e)}

Principles:
- All errors inherit from a common base
- Clear error messages help users fix problems
- Type-safe exception handling
"""


class CNAAError(Exception):
    """Base class for all CNAA exceptions.
    
    All CNAA errors inherit from this class for unified handling.
    """
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            **self.details
        }


# ============================================================================
# Storage Errors
# ============================================================================

class StorageError(CNAAError):
    """Base class for all storage-related errors."""
    pass


class NotFoundError(StorageError):
    """Resource not found error."""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type.title()} '{resource_id}' not found"
        super().__init__(message, {"resource_type": resource_type, "resource_id": resource_id})


class DuplicateError(StorageError):
    """Duplicate resource error."""
    
    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type.title()} '{identifier}' already exists"
        super().__init__(message, {"resource_type": resource_type, "identifier": identifier})


class ValidationError(StorageError):
    """Invalid data error."""
    
    def __init__(self, field: str, issue: str):
        message = f"Invalid {field}: {issue}"
        super().__init__(message, {"field": field, "issue": issue})


# ============================================================================
# Authentication Errors
# ============================================================================

class AuthError(CNAAError):
    """Base class for authentication errors."""
    pass


class UnauthorizedError(AuthError):
    """Authentication failed error."""
    
    def __init__(self, reason: str = "Invalid credentials"):
        super().__init__(f"Unauthorized: {reason}")


class PermissionDeniedError(AuthError):
    """Access denied error."""
    
    def __init__(self, action: str, resource: str):
        super().__init__(f"Permission denied: cannot {action} on {resource}")


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigError(CNAAError):
    """Configuration error."""
    pass


class MissingConfigError(ConfigError):
    """Required configuration missing."""
    
    def __init__(self, key: str):
        super().__init__(f"Missing required config: {key}", {"missing_key": key})


# ============================================================================
# Helper Functions
# ============================================================================

def handle_error(error: Exception) -> dict[str, Any]:
    """Convert any exception to standardized error response.
    
    Args:
        error: The exception to convert
        
    Returns:
        Dictionary with error information
    """
    if isinstance(error, CNAAError):
        return error.to_dict()
    
    # Generic fallback for unexpected errors
    return {
        "error_type": "InternalError",
        "message": str(error),
        "details": {"handled": False}
    }
