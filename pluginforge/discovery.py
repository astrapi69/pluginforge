"""Plugin discovery via entry points and dependency resolution."""

import logging
from importlib.metadata import entry_points
from typing import Any

from pluginforge.base import BasePlugin

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected among plugins."""


def discover_entry_points(group: str) -> dict[str, type[BasePlugin]]:
    """Load plugin classes from entry points.

    Args:
        group: Entry point group name (e.g. "myapp.plugins").

    Returns:
        Dict mapping plugin name to plugin class.
    """
    plugins: dict[str, type[BasePlugin]] = {}
    eps = entry_points()
    group_eps = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
    for ep in group_eps:
        try:
            plugin_cls = ep.load()
            if hasattr(plugin_cls, "name"):
                plugins[plugin_cls.name] = plugin_cls
            else:
                logger.warning("Entry point %s has no 'name' attribute, skipping", ep.name)
        except Exception as e:
            logger.error("Failed to load entry point %s: %s", ep.name, e)
    return plugins


def filter_plugins(
    plugins: dict[str, type[BasePlugin]],
    enabled: list[str] | None,
    disabled: list[str] | None,
) -> dict[str, type[BasePlugin]]:
    """Filter plugins based on enabled/disabled lists.

    If enabled list is provided, only those plugins are kept.
    Disabled list always takes precedence (plugins in disabled are removed).

    Args:
        plugins: All discovered plugins.
        enabled: List of enabled plugin names, or None for all.
        disabled: List of disabled plugin names, or None.

    Returns:
        Filtered plugins dict.
    """
    if enabled is not None:
        plugins = {name: cls for name, cls in plugins.items() if name in enabled}
    if disabled:
        plugins = {name: cls for name, cls in plugins.items() if name not in disabled}
    return plugins


def resolve_dependencies(
    plugins: dict[str, Any],
) -> list[str]:
    """Topologically sort plugins by their dependencies.

    Args:
        plugins: Dict mapping plugin name to plugin class (must have depends_on attribute).

    Returns:
        List of plugin names in dependency order.

    Raises:
        CircularDependencyError: If circular dependencies are detected.
    """
    graph: dict[str, list[str]] = {}
    for name, cls in plugins.items():
        deps = getattr(cls, "depends_on", []) or []
        graph[name] = [d for d in deps if d in plugins]

    visited: set[str] = set()
    in_stack: set[str] = set()
    order: list[str] = []

    def visit(node: str) -> None:
        if node in in_stack:
            raise CircularDependencyError(
                f"Circular dependency detected involving plugin '{node}'"
            )
        if node in visited:
            return
        in_stack.add(node)
        for dep in graph.get(node, []):
            visit(dep)
        in_stack.remove(node)
        visited.add(node)
        order.append(node)

    for name in graph:
        visit(name)

    return order


def check_missing_dependencies(
    plugins: dict[str, Any],
) -> dict[str, list[str]]:
    """Check which plugins have unresolved dependencies.

    Args:
        plugins: Dict mapping plugin name to plugin class.

    Returns:
        Dict mapping plugin name to list of missing dependency names.
    """
    missing: dict[str, list[str]] = {}
    available = set(plugins.keys())
    for name, cls in plugins.items():
        deps = getattr(cls, "depends_on", []) or []
        unresolved = [d for d in deps if d not in available]
        if unresolved:
            missing[name] = unresolved
    return missing
