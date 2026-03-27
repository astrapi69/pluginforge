"""Security utilities for plugin name validation and path traversal prevention."""

import logging
import re

logger = logging.getLogger(__name__)

# Plugin names must be alphanumeric with underscores/hyphens, max 64 chars
_PLUGIN_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")


class InvalidPluginNameError(ValueError):
    """Raised when a plugin name contains invalid characters."""


def validate_plugin_name(name: str) -> None:
    """Validate a plugin name for safety.

    Plugin names are used to construct file paths (config/plugins/{name}.yaml),
    so they must not contain path separators or traversal sequences.

    Args:
        name: The plugin name to validate.

    Raises:
        InvalidPluginNameError: If the name is invalid.
    """
    if not _PLUGIN_NAME_RE.match(name):
        raise InvalidPluginNameError(
            f"Invalid plugin name '{name}'. "
            "Names must start with a letter, contain only letters, digits, "
            "underscores, or hyphens, and be at most 64 characters."
        )


def validate_safe_path(path: str, allowed_base: str) -> bool:
    """Check that a resolved path stays within the allowed base directory.

    Args:
        path: The path to validate.
        allowed_base: The base directory that the path must stay within.

    Returns:
        True if the path is safe, False otherwise.
    """
    from pathlib import Path

    resolved = Path(path).resolve()
    base = Path(allowed_base).resolve()
    try:
        resolved.relative_to(base)
        return True
    except ValueError:
        logger.warning("Path traversal detected: '%s' escapes base '%s'", path, allowed_base)
        return False
