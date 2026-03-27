"""Tests for pluginforge.security module."""

import pytest

from pluginforge.security import InvalidPluginNameError, validate_plugin_name, validate_safe_path


class TestValidatePluginName:
    def test_valid_simple_name(self) -> None:
        validate_plugin_name("hello")

    def test_valid_with_underscore(self) -> None:
        validate_plugin_name("my_plugin")

    def test_valid_with_hyphen(self) -> None:
        validate_plugin_name("my-plugin")

    def test_valid_with_digits(self) -> None:
        validate_plugin_name("plugin2")

    def test_valid_mixed(self) -> None:
        validate_plugin_name("My-Plugin_v2")

    def test_rejects_path_traversal(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("../../etc/passwd")

    def test_rejects_slash(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("my/plugin")

    def test_rejects_backslash(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("my\\plugin")

    def test_rejects_dot_dot(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("..")

    def test_rejects_empty(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("")

    def test_rejects_starting_with_digit(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("2plugin")

    def test_rejects_starting_with_underscore(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("_hidden")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("a" * 65)

    def test_accepts_max_length(self) -> None:
        validate_plugin_name("a" * 64)

    def test_rejects_spaces(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("my plugin")

    def test_rejects_null_byte(self) -> None:
        with pytest.raises(InvalidPluginNameError):
            validate_plugin_name("plugin\x00evil")


class TestValidateSafePath:
    def test_safe_path(self, tmp_path) -> None:
        child = tmp_path / "subdir" / "file.txt"
        child.parent.mkdir(parents=True)
        child.touch()
        assert validate_safe_path(str(child), str(tmp_path)) is True

    def test_traversal_detected(self, tmp_path) -> None:
        escaped = str(tmp_path / ".." / ".." / "etc" / "passwd")
        assert validate_safe_path(escaped, str(tmp_path)) is False

    def test_same_dir_is_safe(self, tmp_path) -> None:
        assert validate_safe_path(str(tmp_path), str(tmp_path)) is True
