"""Tests for pluginforge.alembic_ext module."""

from pathlib import Path

from pluginforge.alembic_ext import collect_migrations_dirs
from pluginforge.base import BasePlugin


class MigratingPlugin(BasePlugin):
    name = "migrating"
    _migrations_dir: str | None = None

    def get_migrations_dir(self) -> str | None:
        return self._migrations_dir


class TestAlembicExt:
    def test_collect_with_valid_dir(self, tmp_path: Path) -> None:
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        plugin = MigratingPlugin()
        plugin._migrations_dir = str(migrations_dir)
        plugin.init({}, {})

        result = collect_migrations_dirs([plugin])
        assert "migrating" in result
        assert result["migrating"] == str(migrations_dir)

    def test_collect_with_missing_dir(self) -> None:
        plugin = MigratingPlugin()
        plugin._migrations_dir = "/nonexistent/path"
        plugin.init({}, {})

        result = collect_migrations_dirs([plugin])
        assert "migrating" not in result

    def test_collect_with_no_migrations(self) -> None:
        plugin = MigratingPlugin()
        plugin.init({}, {})

        result = collect_migrations_dirs([plugin])
        assert result == {}

    def test_collect_mixed_plugins(self, tmp_path: Path) -> None:
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        plugin1 = MigratingPlugin()
        plugin1.name = "with_migrations"  # type: ignore[assignment]
        plugin1._migrations_dir = str(migrations_dir)
        plugin1.init({}, {})

        plugin2 = MigratingPlugin()
        plugin2.name = "without_migrations"  # type: ignore[assignment]
        plugin2.init({}, {})

        result = collect_migrations_dirs([plugin1, plugin2])
        assert "with_migrations" in result
        assert "without_migrations" not in result
