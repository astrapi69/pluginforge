"""PluginForge - Application-agnostic plugin framework built on pluggy."""

from pluginforge.base import BasePlugin
from pluginforge.discovery import CircularDependencyError
from pluginforge.manager import PluginManager
from pluginforge.security import InvalidPluginNameError

__version__ = "0.3.0"
__all__ = [
    "BasePlugin",
    "CircularDependencyError",
    "InvalidPluginNameError",
    "PluginManager",
]
