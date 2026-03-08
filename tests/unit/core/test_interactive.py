"""Unit tests for skills.core.interactive module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from skills.core.interactive import (
    format_non_interactive_response,
    is_interactive,
    prompt_choice,
    prompt_yes_no,
)


class TestIsInteractive:
    """Tests for is_interactive function."""

    def test_returns_true_for_tty(self) -> None:
        with patch("sys.stdin") as mock:
            mock.isatty.return_value = True
            assert is_interactive() is True

    def test_returns_false_for_non_tty(self) -> None:
        with patch("sys.stdin") as mock:
            mock.isatty.return_value = False
            assert is_interactive() is False


class TestPromptYesNo:
    """Tests for prompt_yes_no function."""

    def test_yes_response(self) -> None:
        with patch("builtins.input", return_value="y"):
            assert prompt_yes_no("Continue?") is True

    def test_yes_full_word(self) -> None:
        with patch("builtins.input", return_value="yes"):
            assert prompt_yes_no("Continue?") is True

    def test_ja_response(self) -> None:
        with patch("builtins.input", return_value="ja"):
            assert prompt_yes_no("Continue?") is True

    def test_j_response(self) -> None:
        with patch("builtins.input", return_value="j"):
            assert prompt_yes_no("Continue?") is True

    def test_no_response(self) -> None:
        with patch("builtins.input", return_value="n"):
            assert prompt_yes_no("Continue?") is False

    def test_empty_with_default_false(self) -> None:
        with patch("builtins.input", return_value=""):
            assert prompt_yes_no("Continue?", default=False) is False

    def test_empty_with_default_true(self) -> None:
        with patch("builtins.input", return_value=""):
            assert prompt_yes_no("Continue?", default=True) is True

    def test_prompt_suffix_default_false(self) -> None:
        with patch("builtins.input", return_value="y") as mock_input:
            prompt_yes_no("Continue?", default=False)
            mock_input.assert_called_with("Continue? [y/N] ")

    def test_prompt_suffix_default_true(self) -> None:
        with patch("builtins.input", return_value="y") as mock_input:
            prompt_yes_no("Continue?", default=True)
            mock_input.assert_called_with("Continue? [Y/n] ")


class TestPromptChoice:
    """Tests for prompt_choice function."""

    def test_select_by_number(self) -> None:
        with patch("builtins.input", return_value="2"):
            result = prompt_choice("Pick:", ["a", "b", "c"])
            assert result == "b"

    def test_select_by_name(self) -> None:
        with patch("builtins.input", return_value="b"):
            result = prompt_choice("Pick:", ["a", "b", "c"])
            assert result == "b"

    def test_default_on_empty(self) -> None:
        with patch("builtins.input", return_value=""):
            result = prompt_choice("Pick:", ["a", "b", "c"], default="b")
            assert result == "b"

    def test_invalid_then_valid(self) -> None:
        with patch("builtins.input", side_effect=["0", "5", "abc", "2"]):
            result = prompt_choice("Pick:", ["a", "b", "c"])
            assert result == "b"

    def test_no_default_shows_in_prompt(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        with patch("builtins.input", return_value="1"):
            prompt_choice("Pick:", ["a", "b"])
            captured = capsys.readouterr()
            assert " 1. a" in captured.out
            assert " 2. b" in captured.out

    def test_default_marked_with_asterisk(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        with patch("builtins.input", return_value="1"):
            prompt_choice("Pick:", ["a", "b"], default="b")
            captured = capsys.readouterr()
            assert "*2. b" in captured.out


class TestFormatNonInteractiveResponse:
    """Tests for format_non_interactive_response function."""

    def test_minimal_response(self) -> None:
        result = format_non_interactive_response(action="add")
        assert result == {"interactive_required": True, "action": "add"}

    def test_with_name(self) -> None:
        result = format_non_interactive_response(action="add", name="test")
        assert result["name"] == "test"

    def test_with_message(self) -> None:
        result = format_non_interactive_response(action="add", message="Hello")
        assert result["message"] == "Hello"

    def test_with_schema(self) -> None:
        schema = {"field": "string"}
        result = format_non_interactive_response(action="add", schema=schema)
        assert result["config_schema"] == schema

    def test_with_example(self) -> None:
        example = {"cmd": "test"}
        result = format_non_interactive_response(action="add", example=example)
        assert result["example"] == example

    def test_with_current_config(self) -> None:
        config = {"key": "value"}
        result = format_non_interactive_response(action="edit", current_config=config)
        assert result["current_config"] == config

    def test_with_confirm_command(self) -> None:
        result = format_non_interactive_response(action="remove", confirm_command="cmd --yes")
        assert result["confirm_command"] == "cmd --yes"

    def test_with_warning(self) -> None:
        result = format_non_interactive_response(action="remove", warning="Careful!")
        assert result["warning"] == "Careful!"

    def test_with_extra_fields(self) -> None:
        result = format_non_interactive_response(action="add", custom_field="custom_value")
        assert result["custom_field"] == "custom_value"

    def test_all_fields(self) -> None:
        result = format_non_interactive_response(
            action="edit",
            name="project",
            message="Edit this",
            schema={"f": "s"},
            example={"cmd": "x"},
            current_config={"k": "v"},
            confirm_command="cmd --yes",
            warning="Warning!",
        )
        assert result["interactive_required"] is True
        assert result["action"] == "edit"
        assert result["name"] == "project"
        assert result["message"] == "Edit this"
        assert result["config_schema"] == {"f": "s"}
        assert result["example"] == {"cmd": "x"}
        assert result["current_config"] == {"k": "v"}
        assert result["confirm_command"] == "cmd --yes"
        assert result["warning"] == "Warning!"

    def test_none_values_excluded(self) -> None:
        result = format_non_interactive_response(
            action="add", name=None, message=None
        )
        assert "name" not in result
        assert "message" not in result
