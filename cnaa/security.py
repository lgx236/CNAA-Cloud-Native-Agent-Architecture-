"""CNAA Security Configuration Module.

Provides lightweight authentication and authorization primitives
for CNAA Server. Supports API key-based authentication with
configurable permission levels (read_only, read_write, admin).

Design principles:
- Authentication is OFF by default (backward compatible)
- Pure data exchange: no business logic, only credential validation
- O(1) dict-based API key lookup
- Standard library only (no external dependencies)

Usage:
    config = load_auth_config_from_env()
    ctx = validate_api_key(request_key, config)
    if not check_permission(ctx, "write"):
        # reject request
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for CNAA agent authentication."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"


@dataclass
class AuthConfig:
    """Authentication configuration for CNAA Server.

    Attributes:
        enabled: Whether authentication is enabled. Default False for
            backward compatibility.
        api_keys: Mapping of API key strings to key metadata dicts.
            Each value dict should contain "agent_id" (str) and
            optionally "permission" (str, defaults to "read_write").
        allow_unauthenticated: Whether to allow requests without an
            API key when authentication is enabled.
    """

    enabled: bool = False
    api_keys: dict[str, dict] = field(default_factory=dict)
    allow_unauthenticated: bool = True


@dataclass
class AuthContext:
    """Authenticated request context.

    Attributes:
        agent_id: The authenticated agent identifier.
        permission: The permission level granted to the agent.
        authenticated: Whether the request was successfully authenticated.
    """

    agent_id: str
    permission: PermissionLevel
    authenticated: bool = True

    def to_dict(self) -> dict:
        """Serialize the auth context to a plain dict.

        Returns:
            Dict with agent_id, permission (as string value),
            and authenticated flag.
        """
        return {
            "agent_id": self.agent_id,
            "permission": self.permission.value,
            "authenticated": self.authenticated,
        }


def validate_api_key(
    api_key: str | None, config: AuthConfig
) -> AuthContext | None:
    """Validate an API key and return the corresponding auth context.

    Performs an O(1) dict lookup against the configured API keys.

    Args:
        api_key: The API key string from the request, or None if not
            provided.
        config: The authentication configuration to validate against.

    Returns:
        An AuthContext if the key is valid, or None when:
        - Authentication is disabled (config.enabled is False)
        - No key is provided but unauthenticated access is allowed
        - The key is not found in config.api_keys
    """
    if not config.enabled:
        return None  # Authentication disabled

    if not api_key:
        if config.allow_unauthenticated:
            return None  # Allow unauthenticated requests
        return None  # Key required but not provided

    key_info = config.api_keys.get(api_key)
    if key_info is None:
        logger.warning("Invalid API key attempted")
        return None  # Invalid key

    return AuthContext(
        agent_id=key_info["agent_id"],
        permission=_parse_permission(key_info.get("permission")),
    )


def _parse_permission(raw: str | None) -> PermissionLevel:
    """Safely parse permission string, falling back to READ_WRITE on invalid values."""
    try:
        return PermissionLevel(raw or "read_write")
    except ValueError:
        logger.error(
            "Invalid permission level %r, falling back to read_write",
            raw,
        )
        return PermissionLevel.READ_WRITE


def check_permission(
    auth_context: AuthContext | None, required_level: str
) -> bool:
    """Check if an auth context satisfies the required permission level.

    Args:
        auth_context: The auth context to check, or None when
            authentication is disabled (treated as full access).
        required_level: The required permission level string.
            "read" — allowed for READ_ONLY, READ_WRITE, and ADMIN.
            "write" — allowed for READ_WRITE and ADMIN only.

    Returns:
        True if the context has sufficient permission, False otherwise.
        Returns True when auth_context is None (auth disabled = allow all).
    """
    if auth_context is None:
        return True  # No auth context = auth disabled = allow all

    if auth_context.permission == PermissionLevel.ADMIN:
        return True

    if required_level == "read":
        return auth_context.permission in (
            PermissionLevel.READ_ONLY,
            PermissionLevel.READ_WRITE,
        )

    if required_level == "write":
        return auth_context.permission == PermissionLevel.READ_WRITE

    return False


def load_auth_config_from_env() -> AuthConfig:
    """Load authentication configuration from environment variables.

    Reads the following environment variables:
        CNAA_AUTH_ENABLED: "true" to enable authentication (default "false").
        CNAA_ALLOW_UNAUTHENTICATED: "true" to allow unauthenticated requests
            when auth is enabled (default "true").
        CNAA_API_KEYS: JSON string mapping API keys to metadata dicts
            (default "{}").

    Returns:
        An AuthConfig instance populated from environment variables.
    """
    enabled = os.getenv("CNAA_AUTH_ENABLED", "false").lower() == "true"
    allow_unauthenticated = (
        os.getenv("CNAA_ALLOW_UNAUTHENTICATED", "true").lower() == "true"
    )

    api_keys_str = os.getenv("CNAA_API_KEYS", "{}")
    try:
        raw = json.loads(api_keys_str)
    except json.JSONDecodeError:
        logger.error("Failed to parse CNAA_API_KEYS env var as JSON")
        api_keys = {}
    else:
        if isinstance(raw, dict):
            api_keys = raw
        else:
            logger.error(
                "CNAA_API_KEYS must be a JSON object, got %s",
                type(raw).__name__,
            )
            api_keys = {}

    return AuthConfig(
        enabled=enabled,
        api_keys=api_keys,
        allow_unauthenticated=allow_unauthenticated,
    )
