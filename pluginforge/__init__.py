"""PluginForge - Application-agnostic plugin framework built on pluggy."""

from pluginforge.base import BasePlugin
from pluginforge.discovery import CircularDependencyError
from pluginforge.manager import PluginManager

__version__ = "0.1.0"
__all__ = ["BasePlugin", "CircularDependencyError", "PluginManager"]
