"""Unit tests for the help command.

Tests the central help system that provides:
- obsidian:help              # Overview of all commands
- obsidian:help init         # Details for init command
- obsidian:help types add    # Details for subcommand
- obsidian:help --json       # Machine-readable output

Following TDD: These tests are written FIRST before implementation.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestHelpListsAllCommands:
    """Test that help command lists all available commands."""

    def test_help_shows_all_commands_via_subprocess(self) -> None:
        """Test obsidian:help lists all registered commands."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should list all main commands
        assert "obsidian:init" in output or "init" in output
        assert "obsidian:config" in output or "config" in output
        assert "obsidian:types" in output or "types" in output
        assert "obsidian:props" in output or "props" in output
        assert "obsidian:templates" in output or "templates" in output
        assert "obsidian:validate" in output or "validate" in output

    def test_help_shows_command_descriptions(self) -> None:
        """Test that help shows descriptions for each command."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should include descriptions
        assert "initialize" in output or "vault" in output
        assert "configuration" in output or "config" in output


class TestHelpShowsCommandDetails:
    """Test obsidian:help <command> shows detailed help for a command."""

    def test_help_init_shows_details(self) -> None:
        """Test obsidian:help init shows init command details."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "init"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should show init-specific details
        assert "init" in output
        assert "vault" in output or "methodology" in output

    def test_help_config_shows_subcommands(self) -> None:
        """Test obsidian:help config shows available subcommands."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "config"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should list config subcommands
        assert "show" in output
        assert "edit" in output or "validate" in output

    def test_help_types_shows_subcommands(self) -> None:
        """Test obsidian:help types shows available subcommands."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "types"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should list types subcommands
        assert "list" in output
        assert "show" in output
        assert "add" in output

    def test_help_unknown_command_returns_error(self) -> None:
        """Test obsidian:help unknowncommand returns helpful error."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "unknowncommand"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        # Should exit with error code
        assert result.returncode == 1

        output = result.stdout.lower() + result.stderr.lower()
        # Should indicate command not found
        assert "unknown" in output or "not found" in output


class TestHelpShowsSubcommandDetails:
    """Test obsidian:help <command> <subcommand> shows subcommand details."""

    def test_help_types_add_shows_details(self) -> None:
        """Test obsidian:help types add shows add subcommand details."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "types", "add"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should show add-specific details
        assert "add" in output
        # Should mention config or parameters
        assert "config" in output or "name" in output

    def test_help_config_show_shows_details(self) -> None:
        """Test obsidian:help config show shows show subcommand details."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "config", "show"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should show show-specific details
        assert "show" in output

    def test_help_types_unknown_subcommand_returns_error(self) -> None:
        """Test obsidian:help types unknownsub returns error."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "types", "unknownsub"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        # Should exit with error code
        assert result.returncode == 1


class TestHelpJsonOutput:
    """Test obsidian:help --json returns structured JSON output."""

    def test_help_json_returns_valid_json(self) -> None:
        """Test --json flag returns valid JSON."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        # Should be valid JSON
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_help_json_contains_all_commands(self) -> None:
        """Test JSON output contains all commands with metadata."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        data = json.loads(result.stdout)
        # Should have commands key
        assert "commands" in data

        commands = data["commands"]
        # Should include all main commands
        command_names = [cmd.get("name", "") for cmd in commands]
        assert any("init" in name for name in command_names)
        assert any("config" in name for name in command_names)
        assert any("types" in name for name in command_names)

    def test_help_json_command_has_description(self) -> None:
        """Test JSON output includes descriptions for commands."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        data = json.loads(result.stdout)
        commands = data["commands"]
        # Each command should have a description
        for cmd in commands:
            assert "description" in cmd, f"Command {cmd.get('name')} missing description"

    def test_help_json_command_has_subcommands(self) -> None:
        """Test JSON output includes subcommands for commands that have them."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        data = json.loads(result.stdout)
        commands = data["commands"]

        # Find types command - should have subcommands
        types_cmd = next((c for c in commands if "types" in c.get("name", "")), None)
        assert types_cmd is not None, "types command not found"
        assert "subcommands" in types_cmd
        assert len(types_cmd["subcommands"]) > 0

    def test_help_command_json_shows_single_command(self) -> None:
        """Test obsidian:help types --json shows types command as JSON."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "types", "--json"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        data = json.loads(result.stdout)
        # Should be a single command object, not a list
        assert "name" in data
        assert "types" in data["name"]
        assert "subcommands" in data


class TestEachCommandHasExamplesInHelp:
    """Test that each command's --help includes usage examples."""

    @pytest.mark.parametrize(
        "script_path",
        [
            "skills/config/scripts/config_command.py",
            "skills/note-types/scripts/types_command.py",
            "skills/validate/scripts/validate_command.py",
            "skills/templates/scripts/templates_command.py",
            "skills/frontmatter/scripts/props_command.py",
        ],
    )
    def test_command_help_has_examples(self, script_path: str) -> None:
        """Test that command --help includes examples section."""
        script = PROJECT_ROOT / script_path
        if not script.exists():
            pytest.skip(f"Script not found: {script}")

        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        # Should have examples section
        assert "example" in output, f"No examples in {script_path} --help"

    def test_help_command_itself_has_examples(self) -> None:
        """Test that help_command.py --help includes examples."""
        script = PROJECT_ROOT / "skills" / "obsidian_commands" / "help_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

        output = result.stdout.lower()
        assert "example" in output, "No examples in help_command.py --help"


class TestHelpCommandIntegration:
    """Integration tests for the help command via module import."""

    def test_help_command_registered_in_router(self) -> None:
        """Test help command is registered in the router."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from skills.obsidian_commands.router import get_router

        router = get_router()
        commands = router.list_commands()
        command_names = [cmd.name for cmd in commands]

        assert "obsidian:help" in command_names

    def test_help_handler_exists_in_router(self) -> None:
        """Test help handler can be retrieved from router."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from skills.obsidian_commands.router import get_router

        router = get_router()
        handler = router.get_handler("obsidian:help")

        assert handler is not None
