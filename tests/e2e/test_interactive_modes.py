"""
E2E tests for interactive mode support across all commands.

Tests both Terminal mode (isatty=True) and Claude Code mode (isatty=False).
Each command with add/edit/remove/create/delete actions must:
- In terminal mode: Show interactive prompts
- In Claude Code mode: Return JSON with interactive_required=True
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


# Test vault setup
@pytest.fixture
def test_vault(tmp_path: Path) -> Path:
    """Create a test vault with settings."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    claude_dir = vault / ".claude"
    claude_dir.mkdir()

    settings = {
        "version": 1,
        "methodology": "lyt-ace",
        "core_properties": ["type", "up", "created", "daily", "tags"],
        "note_types": {
            "map": {
                "description": "Map of Content",
                "folder_hints": ["Atlas/Maps"],
                "icon": "map",
                "properties": {"additional_required": [], "optional": ["related"]},
            },
            "project": {
                "description": "Project tracking",
                "folder_hints": ["Efforts"],
                "icon": "target",
                "properties": {"additional_required": ["status"], "optional": ["deadline"]},
            },
        },
    }

    import yaml

    (claude_dir / "settings.yaml").write_text(yaml.dump(settings))

    # Create templates directory (Obsidian standard location)
    templates_dir = vault / ".obsidian" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "test_template.md").write_text("# Test Template\n")

    return vault


def run_command(cmd: list[str], vault: Path) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr.

    Args:
        cmd: Full command list to execute
        vault: Path to test vault (used for cwd context)

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    import os

    project_root = Path(__file__).parent.parent.parent

    # Use the project root as cwd so uv can find pyproject.toml
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(project_root)},
        stdin=subprocess.DEVNULL,  # Non-interactive (simulates Claude Code)
    )
    return result.returncode, result.stdout, result.stderr


# =============================================================================
# TYPES COMMAND TESTS (Reference - already implemented)
# =============================================================================


class TestTypesInteractiveMode:
    """Tests for obsidian:types interactive mode."""

    def test_types_add_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'types add' without --config returns JSON."""
        cmd = [
            "uv",
            "run",
            "skills/note-types/scripts/types_command.py",
            "--vault",
            str(test_vault),
            "add",
            "meeting",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "add"
        assert "config_schema" in data
        assert "example" in data

    def test_types_edit_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'types edit' without --config returns JSON."""
        cmd = [
            "uv",
            "run",
            "skills/note-types/scripts/types_command.py",
            "--vault",
            str(test_vault),
            "edit",
            "map",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "edit"
        assert "current_config" in data

    def test_types_remove_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'types remove' without --yes returns JSON."""
        cmd = [
            "uv",
            "run",
            "skills/note-types/scripts/types_command.py",
            "--vault",
            str(test_vault),
            "remove",
            "project",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "remove"
        assert "confirm_command" in data

    def test_types_config_flag_bypasses_interactive(self, test_vault: Path):
        """The --config flag should bypass interactive mode."""
        config = json.dumps(
            {"description": "Daily standup meetings", "folder": "Meetings/", "icon": "users"}
        )
        cmd = [
            "uv",
            "run",
            "skills/note-types/scripts/types_command.py",
            "--vault",
            str(test_vault),
            "add",
            "standup",
            "--config",
            config,
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should succeed without returning interactive_required
        assert exit_code == 0, f"Command failed: {stderr}"
        # Should not be JSON with interactive_required
        if stdout.strip():
            try:
                data = json.loads(stdout)
                assert data.get("interactive_required") is not True
            except json.JSONDecodeError:
                pass  # Text output is fine

    def test_types_yes_flag_bypasses_confirmation(self, test_vault: Path):
        """The --yes flag should bypass confirmation for remove."""
        cmd = [
            "uv",
            "run",
            "skills/note-types/scripts/types_command.py",
            "--vault",
            str(test_vault),
            "remove",
            "project",
            "--yes",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should succeed without returning interactive_required
        assert exit_code == 0, f"Command failed: {stderr}"
        if stdout.strip():
            try:
                data = json.loads(stdout)
                assert data.get("interactive_required") is not True
            except json.JSONDecodeError:
                pass  # Text output is fine


# =============================================================================
# CONFIG COMMAND TESTS (Need implementation)
# =============================================================================


class TestConfigInteractiveMode:
    """Tests for obsidian:config interactive mode."""

    def test_config_edit_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'config edit' should return JSON guidance."""
        cmd = [
            "uv",
            "run",
            "skills/config/scripts/config_command.py",
            "--vault",
            str(test_vault),
            "edit",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # This test should FAIL initially - config_command.py doesn't support this yet
        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "edit"
        assert "message" in data


# =============================================================================
# PROPS COMMAND TESTS (Need implementation)
# =============================================================================


class TestPropsInteractiveMode:
    """Tests for obsidian:props interactive mode."""

    def test_props_core_add_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'props core add' without name should return JSON."""
        # Note: This tests that when called non-interactively, it provides guidance
        cmd = [
            "uv",
            "run",
            "skills/frontmatter/scripts/props_command.py",
            "--vault",
            str(test_vault),
            "core",
            "add",
            "priority",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Currently this just adds directly - should return JSON in Claude Code mode
        # This test should FAIL initially
        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "add"

    def test_props_core_remove_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'props core remove' without --yes returns JSON."""
        cmd = [
            "uv",
            "run",
            "skills/frontmatter/scripts/props_command.py",
            "--vault",
            str(test_vault),
            "core",
            "remove",
            "tags",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should return JSON asking for confirmation
        # This test should FAIL initially
        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "remove"
        assert "confirm_command" in data

    def test_props_yes_flag_bypasses_confirmation(self, test_vault: Path):
        """The --yes flag should bypass confirmation for core remove."""
        # 'daily' is in core_properties and is not essential (type, created)
        cmd = [
            "uv",
            "run",
            "skills/frontmatter/scripts/props_command.py",
            "--vault",
            str(test_vault),
            "core",
            "remove",
            "daily",
            "--yes",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should succeed without returning interactive_required
        assert exit_code == 0, f"Command failed: {stderr}"


# =============================================================================
# TEMPLATES COMMAND TESTS (Need implementation)
# =============================================================================


class TestTemplatesInteractiveMode:
    """Tests for obsidian:templates interactive mode."""

    def test_templates_create_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'templates create' without --content returns JSON."""
        cmd = [
            "uv",
            "run",
            "skills/templates/scripts/templates_command.py",
            "--vault",
            str(test_vault),
            "create",
            "new_template",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should return JSON with interactive_required
        # This test should FAIL initially
        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "create"
        assert "example" in data

    def test_templates_edit_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'templates edit' should return JSON guidance."""
        cmd = [
            "uv",
            "run",
            "skills/templates/scripts/templates_command.py",
            "--vault",
            str(test_vault),
            "edit",
            "test_template",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should return JSON with interactive_required
        # This test should FAIL initially
        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "edit"

    def test_templates_delete_claude_code_mode_returns_json(self, test_vault: Path):
        """In Claude Code mode, 'templates delete' without --yes returns JSON."""
        cmd = [
            "uv",
            "run",
            "skills/templates/scripts/templates_command.py",
            "--vault",
            str(test_vault),
            "delete",
            "test_template",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should return JSON asking for confirmation
        # This test should FAIL initially
        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data.get("interactive_required") is True
        assert data.get("action") == "delete"
        assert "confirm_command" in data

    def test_templates_content_flag_bypasses_interactive(self, test_vault: Path):
        """The --content flag should bypass interactive mode for create."""
        cmd = [
            "uv",
            "run",
            "skills/templates/scripts/templates_command.py",
            "--vault",
            str(test_vault),
            "create",
            "quick_note",
            "--content",
            "# Quick Note\n\nContent here.",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should succeed without returning interactive_required
        assert exit_code == 0, f"Command failed: {stderr}"
        if stdout.strip():
            try:
                data = json.loads(stdout)
                assert data.get("interactive_required") is not True
            except json.JSONDecodeError:
                pass  # Text output is fine

    def test_templates_yes_flag_bypasses_confirmation(self, test_vault: Path):
        """The --yes flag should bypass confirmation for delete."""
        # First create a template to delete
        create_cmd = [
            "uv",
            "run",
            "skills/templates/scripts/templates_command.py",
            "--vault",
            str(test_vault),
            "create",
            "to_delete",
            "--content",
            "# To Delete",
        ]
        run_command(create_cmd, test_vault)

        # Now try to delete with --yes
        cmd = [
            "uv",
            "run",
            "skills/templates/scripts/templates_command.py",
            "--vault",
            str(test_vault),
            "delete",
            "to_delete",
            "--yes",
        ]
        exit_code, stdout, stderr = run_command(cmd, test_vault)

        # Should succeed without returning interactive_required
        # This test should FAIL initially - --yes flag doesn't exist yet
        assert exit_code == 0, f"Command failed: {stderr}"


# =============================================================================
# SHARED INTERACTIVE MODULE TESTS
# =============================================================================


class TestInteractiveModule:
    """Tests for the shared skills/core/interactive module."""

    def test_is_interactive_returns_false_when_no_tty(self):
        """is_interactive() should return False when stdin is not a TTY."""
        from skills.core.interactive import is_interactive

        # When running in pytest/subprocess, stdin is not a TTY
        # This should return False
        with patch("sys.stdin.isatty", return_value=False):
            assert is_interactive() is False

    def test_is_interactive_returns_true_when_tty(self):
        """is_interactive() should return True when stdin is a TTY."""
        from skills.core.interactive import is_interactive

        with patch("sys.stdin.isatty", return_value=True):
            assert is_interactive() is True

    def test_format_non_interactive_response_structure(self):
        """format_non_interactive_response() should return proper structure."""
        from skills.core.interactive import format_non_interactive_response

        result = format_non_interactive_response(
            action="add",
            name="test",
            message="Test message",
            schema={"field": "description"},
            example={"command": "test --config '{}'"},
        )

        assert result["interactive_required"] is True
        assert result["action"] == "add"
        assert result["name"] == "test"
        assert result["message"] == "Test message"
        assert "config_schema" in result
        assert "example" in result
