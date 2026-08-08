"""CNAA deprecation management and backward compatibility utilities."""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


# Global registry of deprecated items
_DEPRECATED_REGISTRY: Dict[str, Dict[str, Any]] = {}


def mark_deprecated(
    item_name: str,
    reason: str,
    removed_in: str = None,
    replacement: str = None,
) -> None:
    """Mark an API item as deprecated.
    
    Args:
        item_name: Name of the deprecated item (e.g., function, class, parameter)
        reason: Why it's being deprecated
        removed_in: Version when it will be removed (e.g., "v1.2")
        replacement: Alternative to use instead
    
    Example:
        >>> mark_deprecated('old_memory_api', 'Use new_memory_api instead', 'v1.2')
    """
    deprecated_info = {
        'name': item_name,
        'reason': reason,
        'removed_in': removed_in or "future version",
        'replacement': replacement,
        'marked_at': datetime.utcnow(),
    }
    
    _DEPRECATED_REGISTRY[item_name] = deprecated_info
    
    # Log deprecation notice
    warning_msg = f"⚠️ DEPRECATION: '{item_name}' is deprecated."
    if reason:
        warning_msg += f" {reason}"
    if removed_in:
        warning_msg += f" Will be removed in {removed_in}."
    if replacement:
        warning_msg += f" Use '{replacement}' instead."
    
    logger.warning(warning_msg)


class DeprecationWarningManager:
    """Manage deprecation warnings for CNAA components."""
    
    def __init__(self):
        self._warnings_enabled = True
        self._suppressed_items: set = set()
    
    def enable_warnings(self) -> None:
        """Enable all deprecation warnings."""
        self._warnings_enabled = True
        self._suppressed_items.clear()
    
    def disable_warnings(self) -> None:
        """Disable all deprecation warnings."""
        self._warnings_enabled = False
    
    def suppress_warning(self, item_name: str) -> None:
        """Suppress warning for specific item."""
        self._suppressed_items.add(item_name)
    
    def is_suppressed(self, item_name: str) -> bool:
        """Check if warning for item is suppressed."""
        return item_name in self._suppressed_items
    
    def emit_warning(self, item_name: str) -> None:
        """Emit deprecation warning if enabled and not suppressed."""
        if not self._warnings_enabled:
            return
        
        if self.is_suppressed(item_name):
            return
        
        info = _DEPRECATED_REGISTRY.get(item_name)
        if not info:
            return
        
        warning_text = f"'{item_name}' is deprecated and will be removed in {info['removed_in']}."
        
        if info['reason']:
            warning_text += f" {info['reason']}"
        
        if info['replacement']:
            warning_text += f"\n\n💡 REPLACEMENT: Use '{info['replacement']}' instead."
        
        logger.warning(warning_text)


# Global instance
_deprecation_manager = DeprecationWarningManager()


def get_deprecation_manager() -> DeprecationWarningManager:
    """Get global deprecation manager instance."""
    return _deprecation_manager


def warn_deprecated(
    field_name: str,
    replacement: Optional[str] = None,
    removed_in: str = "v1.2",
) -> None:
    """Issue a deprecation warning for a field/parameter.
    
    Args:
        field_name: Name of the deprecated field or parameter
        replacement: Suggested replacement (optional)
        removed_in: Version when this will be removed
    
    Example:
        >>> warn_deprecated('legacy_mode', replacement='new_api_mode', removed_in='v1.2')
    """
    _deprecation_manager.emit_warning(field_name)


def require_not_deprecated(item_name: str, current_version: str) -> None:
    """Raise error if using deprecated functionality.
    
    This should be called at runtime to enforce deprecation removal.
    
    Args:
        item_name: Name of deprecated item
        current_version: Current version string (e.g., "1.0.0")
    
    Raises:
        RuntimeError: If item has been removed due to deprecation
    """
    import re
    
    info = _DEPRECATED_REGISTRY.get(item_name)
    if not info:
        return
    
    removed_in = info['removed_in']
    
    # Parse version number
    match = re.search(r'v?(\d+)\.(\d+)', removed_in)
    if not match:
        return  # Can't parse version
    
    target_major, target_minor = int(match.group(1)), int(match.group(2))
    
    # Compare versions
    current_match = re.search(r'(\d+)\.(\d+)', current_version)
    if not current_match:
        return
    
    curr_major, curr_minor = int(current_match.group(1)), int(current_match.group(2))
    
    if (curr_major, curr_minor) >= (target_major, target_minor):
        message = f"❌ REMOVED: '{item_name}' was removed in {removed_in}."
        
        if info['replacement']:
            message += f"\n   Use '{info['replacement']}' instead."
        
        raise RuntimeError(message)


# Decorator for marking functions/methods as deprecated
def deprecated(replacement: str = None, reason: str = None, removed_in: str = "v1.2"):
    """Decorator to mark a function or method as deprecated.
    
    Usage:
        @deprecated(replacement='new_function')
        def old_function():
            pass
    
    Args:
        replacement: Name of the replacement function/method
        reason: Explanation why deprecated
        removed_in: Version when deprecated item will be removed
    """
    def decorator(func: Callable) -> Callable:
        # Mark the function as deprecated
        func_name = func.__name__
        mark_deprecated(
            item_name=func_name,
            reason=reason or f"Function '{func_name}' is deprecated",
            removed_in=removed_in,
            replacement=replacement
        )
        
        # Wrap function with warning
        def wrapper(*args, **kwargs):
            _deprecation_manager.emit_warning(func_name)
            return func(*args, **kwargs)
        
        wrapper.__name__ = func_name
        wrapper.__doc__ = func.__doc__
        
        return wrapper
    
    return decorator


# Context manager for temporarily disabling deprecation warnings
class SuppressDeprecationWarnings:
    """Context manager to suppress deprecation warnings within a scope."""
    
    def __enter__(self):
        self._original_state = _deprecation_manager._warnings_enabled
        _deprecation_manager.disable_warnings()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _deprecation_manager._warnings_enabled = self._original_state


# Utility function to list all deprecated items
def list_deprecated_items() -> list:
    """List all currently deprecated items.
    
    Returns:
        List of dictionaries with deprecation information
    """
    return list(_DEPRECATED_REGISTRY.values())


# Check if item is deprecated
def is_deprecated(item_name: str) -> bool:
    """Check if an item is marked as deprecated."""
    return item_name in _DEPRECATED_REGISTRY


# Get deprecation details
def get_deprecation_info(item_name: str) -> Optional[Dict[str, Any]]:
    """Get deprecation information for an item."""
    return _DEPRECATEDRegistry.get(item_name)


if __name__ == "__main__":
    # Demo usage
    print("📝 CNAA Deprecation Management System Demo\n")
    
    # Register some deprecated items
    mark_deprecated(
        'legacy_store_memory',
        'Use store_memory_v2 instead',
        removed_in='v1.2',
        replacement='store_memory_v2'
    )
    
    mark_deprecated(
        'get_all_memories',
        'Use paginated retrieval methods',
        removed_in='v1.3',
        replacement='get_memories_with_pagination'
    )
    
    print("Registered deprecated items:")
    for item in list_deprecated_items():
        print(f"\n  • {item['name']}")
        print(f"    Reason: {item['reason']}")
        print(f"    Removed in: {item['removed_in']}")
        print(f"    Replacement: {item['replacement']}")
