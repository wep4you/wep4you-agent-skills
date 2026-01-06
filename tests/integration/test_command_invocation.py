"""Integration tests for command invocation via subprocess.

These tests verify that commands work the way Claude Code invokes them:
- uv run commands/init.py <args>
- uv run python commands/init.py <args>

This catches issues like missing dependencies in PEP 723 script metadata
that unit tests (which import directly) would miss.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

# Project root directory (where pyproject.toml is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestInitCommandInvocation:
    """Test init command can be invoked via subprocess."""

    def test_init_help_via_uv_run(self) -> None:
        """Test uv run commands/init.py --help works."""
        result = subprocess.run(
            ["uv", "run", "commands/init.py", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "vault" in result.stdout.lower()
        assert "methodology" in result.stdout.lower()

    def test_init_help_via_uv_run_python(self) -> None:
        """Test uv run python commands/init.py --help works."""
        result = subprocess.run(
            ["uv", "run", "python", "commands/init.py", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "vault" in result.stdout.lower()

    def test_init_list_methodologies(self) -> None:
        """Test uv run commands/init.py --list works."""
        result = subprocess.run(
            ["uv", "run", "commands/init.py", "--list"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        # Should list available methodologies
        output = result.stdout.lower()
        assert "lyt-ace" in output or "para" in output

    def test_init_check_vault_status_empty_vault(self, tmp_path: Path) -> None:
        """Test uv run commands/init.py <path> --check works on empty vault."""
        vault = tmp_path / "test-vault"
        vault.mkdir()

        result = subprocess.run(
            ["uv", "run", "commands/init.py", str(vault), "--check"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        # Should output JSON status
        output = json.loads(result.stdout)
        assert "status" in output or "is_initialized" in output

    def test_init_check_vault_status_nonexistent_vault(self, tmp_path: Path) -> None:
        """Test --check on nonexistent vault path."""
        vault = tmp_path / "nonexistent-vault"

        result = subprocess.run(
            ["uv", "run", "commands/init.py", str(vault), "--check"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        # Should output JSON even for nonexistent path
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        output = json.loads(result.stdout)
        assert output is not None

    def test_init_full_workflow_with_defaults(self, tmp_path: Path) -> None:
        """Test full initialization with --defaults flag."""
        vault = tmp_path / "test-vault"
        vault.mkdir()

        result = subprocess.run(
            [
                "uv",
                "run",
                "commands/init.py",
                str(vault),
                "--action=continue",
                "-m",
                "para",
                "--defaults",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        # Should succeed or output JSON prompt
        # (full init may take longer, so we accept either success or prompt)
        output = result.stdout
        assert result.returncode == 0 or "prompt_type" in output, (
            f"Failed with stderr: {result.stderr}"
        )


class TestInitCommandInvocationFromAbsolutePath:
    """Test command invocation using absolute paths (like Claude Code does)."""

    def test_init_help_with_absolute_path(self) -> None:
        """Test uv run /absolute/path/to/commands/init.py --help works."""
        init_script = PROJECT_ROOT / "commands" / "init.py"

        result = subprocess.run(
            ["uv", "run", str(init_script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "vault" in result.stdout.lower()

    def test_init_list_with_absolute_path(self) -> None:
        """Test uv run /absolute/path/to/commands/init.py --list works."""
        init_script = PROJECT_ROOT / "commands" / "init.py"

        result = subprocess.run(
            ["uv", "run", str(init_script), "--list"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        output = result.stdout.lower()
        assert "lyt-ace" in output or "para" in output


class TestInitCommandFromDifferentWorkingDir:
    """Test command invocation from different working directories."""

    def test_init_help_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test invoking init from a different directory using absolute path."""
        init_script = PROJECT_ROOT / "commands" / "init.py"

        result = subprocess.run(
            ["uv", "run", str(init_script), "--help"],
            cwd=tmp_path,  # Run from temp directory
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "vault" in result.stdout.lower()

    def test_init_list_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test --list from a different directory using absolute path."""
        init_script = PROJECT_ROOT / "commands" / "init.py"

        result = subprocess.run(
            ["uv", "run", str(init_script), "--list"],
            cwd=tmp_path,  # Run from temp directory
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        output = result.stdout.lower()
        assert "lyt-ace" in output or "para" in output

    def test_init_check_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test --check from a different directory."""
        init_script = PROJECT_ROOT / "commands" / "init.py"
        vault = tmp_path / "test-vault"
        vault.mkdir()

        result = subprocess.run(
            ["uv", "run", str(init_script), str(vault), "--check"],
            cwd=tmp_path,  # Run from temp directory
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        # Should output JSON
        output = json.loads(result.stdout)
        assert output is not None


class TestValidateCommandInvocation:
    """Test validate command can be invoked via subprocess.

    These tests catch ModuleNotFoundError for skills.* imports
    that occur when sys.path is not properly configured.
    """

    def test_validate_help_via_uv_run(self) -> None:
        """Test uv run validate_command.py --help works."""
        script = PROJECT_ROOT / "skills" / "validate" / "scripts" / "validate_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "vault" in result.stdout.lower()
        assert "fix" in result.stdout.lower()

    def test_validate_help_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test validate --help from different directory (catches sys.path issues)."""
        script = PROJECT_ROOT / "skills" / "validate" / "scripts" / "validate_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=tmp_path,  # Different working directory
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "vault" in result.stdout.lower()

    def test_validate_imports_skills_modules(self) -> None:
        """Test that validator.py can import skills.* modules.

        This is the key regression test - previously failed with:
        ModuleNotFoundError: No module named 'skills'
        """
        script = PROJECT_ROOT / "skills" / "validate" / "scripts" / "validator.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        # Should not fail with ModuleNotFoundError
        assert "ModuleNotFoundError" not in result.stderr, f"Import failed: {result.stderr}"
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"


class TestNoteTypesCommandInvocation:
    """Test note-types command can be invoked via subprocess.

    Catches sys.path configuration issues for skills.* imports.
    """

    def test_types_command_help_via_uv_run(self) -> None:
        """Test uv run types_command.py --help works."""
        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "vault" in result.stdout.lower() or "list" in result.stdout.lower()

    def test_types_command_help_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test types_command --help from different directory."""
        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

    def test_note_types_script_imports_work(self) -> None:
        """Test that note_types.py can be imported without ModuleNotFoundError.

        Regression test for: ModuleNotFoundError: No module named 'skills'
        """
        # Test by running Python with an import statement
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-c",
                "from skills.note_types.scripts import note_types; print('OK')",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        # The import path with hyphen won't work, but the script itself should
        # So we test via the command instead
        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert "ModuleNotFoundError" not in result.stderr, f"Import failed: {result.stderr}"

    def test_types_list_on_initialized_vault(self, tmp_path: Path) -> None:
        """Test types list subcommand on an initialized vault.

        Regression test: types_command.py called manager.list_types() which
        returned a dict but didn't print anything. Should use display_type_list().
        """
        # Create a minimal vault with settings.yaml
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all:
    - type
    - created
note_types:
  note:
    description: General notes
    folder_hints:
      - Notes/
    properties:
      additional_required: []
      optional: []
    validation:
      allow_empty_up: true
    icon: file
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--vault", str(vault)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Should succeed and output note type info
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "AttributeError" not in result.stderr, f"Method missing: {result.stderr}"
        # Should show the note type name in output
        assert "note" in result.stdout.lower(), f"Missing type in output: {result.stdout}"

    def test_types_show_on_initialized_vault(self, tmp_path: Path) -> None:
        """Test types show subcommand on an initialized vault.

        Regression test: types_command.py called manager.show_type(name) which
        didn't exist! Should use display_type_details().
        """
        # Create a minimal vault with settings.yaml
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: para
core_properties:
  all:
    - type
    - up
    - created
note_types:
  project:
    description: Active projects
    folder_hints:
      - Projects/
    properties:
      additional_required:
        - status
      optional:
        - deadline
    validation:
      allow_empty_up: false
    icon: target
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--vault", str(vault), "show", "project"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Should succeed without AttributeError
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"
        assert "AttributeError" not in result.stderr, f"Method show_type missing: {result.stderr}"
        # Should show project details
        assert "project" in result.stdout.lower(), f"Missing type in output: {result.stdout}"
        assert "active projects" in result.stdout.lower(), f"Missing description: {result.stdout}"

    def test_types_show_nonexistent_type(self, tmp_path: Path) -> None:
        """Test types show with nonexistent type returns proper error."""
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: Notes
    folder_hints: [Notes/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--vault", str(vault), "show", "nonexistent"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Should fail with exit code 1, not crash with AttributeError
        assert result.returncode == 1, "Should return error code for missing type"
        assert "AttributeError" not in result.stderr, f"Crashed: {result.stderr}"
        assert "not found" in result.stdout.lower(), f"Missing error msg: {result.stdout}"

    def test_types_add_noninteractive_with_config(self, tmp_path: Path) -> None:
        """Test types add --config works without interactive prompts.

        Regression test: cmd_add called manager.add_type with wrong signature
        (manager.add_type(name, interactive=..., config=...) but actual signature
        is add_type(name, config)).
        """
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: Notes
    folder_hints: [Notes/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        # Create Notes folder for vault structure
        (vault / "Notes").mkdir()

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        config_json = '{"description": "Meeting notes", "folder": "Meetings"}'
        result = subprocess.run(
            [
                "uv",
                "run",
                str(script),
                "--vault",
                str(vault),
                "add",
                "meeting",
                "--config",
                config_json,
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Should not crash with TypeError about unexpected keyword argument
        assert "TypeError" not in result.stderr, f"Signature mismatch: {result.stderr}"
        assert result.returncode == 0, f"Failed: {result.stderr}\nStdout: {result.stdout}"
        assert "meeting" in result.stdout.lower(), f"Missing confirmation: {result.stdout}"

    def test_types_add_duplicate_returns_error(self, tmp_path: Path) -> None:
        """Test adding duplicate type returns proper error."""
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: Notes
    folder_hints: [Notes/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            [
                "uv",
                "run",
                str(script),
                "--vault",
                str(vault),
                "add",
                "note",  # Already exists
                "--config",
                '{"description": "Duplicate"}',
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        assert result.returncode == 1, "Should fail for duplicate type"
        assert "already exists" in result.stdout.lower(), f"Wrong error: {result.stdout}"

    def test_types_edit_noninteractive_with_config(self, tmp_path: Path) -> None:
        """Test types edit --config works without interactive prompts.

        Regression test: cmd_edit called manager.edit_type which doesn't exist
        (should be update_type).
        """
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: General notes
    folder_hints: [Notes/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        # Create Notes folder for vault structure
        (vault / "Notes").mkdir()

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        config_json = '{"description": "Updated notes"}'
        result = subprocess.run(
            [
                "uv",
                "run",
                str(script),
                "--vault",
                str(vault),
                "edit",
                "note",
                "--config",
                config_json,
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Should not crash with TypeError or AttributeError
        assert "TypeError" not in result.stderr, f"Signature mismatch: {result.stderr}"
        assert "AttributeError" not in result.stderr, f"Method missing: {result.stderr}"
        assert result.returncode == 0, f"Failed: {result.stderr}\nStdout: {result.stdout}"

    def test_types_edit_nonexistent_returns_error(self, tmp_path: Path) -> None:
        """Test editing nonexistent type returns proper error."""
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: Notes
    folder_hints: [Notes/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            [
                "uv",
                "run",
                str(script),
                "--vault",
                str(vault),
                "edit",
                "nonexistent",
                "--config",
                '{"description": "Updated"}',
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        assert result.returncode == 1, "Should fail for nonexistent type"
        assert "not found" in result.stdout.lower(), f"Wrong error: {result.stdout}"

    def test_types_remove_with_yes_flag(self, tmp_path: Path) -> None:
        """Test types remove --yes works without confirmation prompt.

        Regression test: cmd_remove called manager.remove_type which doesn't exist
        (should use handle_remove which calls delete_type).
        """
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: Notes
    folder_hints: [Notes/]
  custom:
    description: Custom type to remove
    folder_hints: [Custom/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        # Create folders for vault structure
        (vault / "Notes").mkdir()
        (vault / "Custom").mkdir()

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            [
                "uv",
                "run",
                str(script),
                "--vault",
                str(vault),
                "remove",
                "custom",
                "--yes",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Should not crash with TypeError or AttributeError
        assert "TypeError" not in result.stderr, f"Signature mismatch: {result.stderr}"
        assert "AttributeError" not in result.stderr, f"Method missing: {result.stderr}"
        assert result.returncode == 0, f"Failed: {result.stderr}\nStdout: {result.stdout}"
        assert "removed" in result.stdout.lower(), f"Missing confirmation: {result.stdout}"

    def test_types_remove_nonexistent_returns_error(self, tmp_path: Path) -> None:
        """Test removing nonexistent type returns proper error."""
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: Notes
    folder_hints: [Notes/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            [
                "uv",
                "run",
                str(script),
                "--vault",
                str(vault),
                "remove",
                "nonexistent",
                "--yes",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        assert result.returncode == 1, "Should fail for nonexistent type"
        assert "not found" in result.stdout.lower(), f"Wrong error: {result.stdout}"

    def test_types_wizard_returns_json_when_noninteractive(self, tmp_path: Path) -> None:
        """Test wizard returns JSON with interactive_required when not in a TTY.

        When invoked through subprocess (non-interactive), the wizard should
        return JSON describing how to use the add command instead of crashing
        with EOFError.
        """
        vault = tmp_path / "test-vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: '1.0'
methodology: minimal
core_properties:
  all: [type, created]
note_types:
  note:
    description: Notes
    folder_hints: [Notes/]
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        script = PROJECT_ROOT / "skills" / "note-types" / "scripts" / "types_command.py"
        result = subprocess.run(
            [
                "uv",
                "run",
                str(script),
                "--vault",
                str(vault),
                "wizard",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Should succeed (not crash with EOFError)
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "EOFError" not in result.stderr, f"Crashed on input: {result.stderr}"

        # Should return JSON with interactive_required
        output = json.loads(result.stdout)
        assert output.get("interactive_required") is True
        assert "existing_types" in output
        assert "note" in output["existing_types"]
        assert "fields" in output
        assert "name" in output["fields"]


class TestConfigCommandInvocation:
    """Test config command can be invoked via subprocess."""

    def test_config_command_help_via_uv_run(self) -> None:
        """Test uv run config_command.py --help works."""
        script = PROJECT_ROOT / "skills" / "config" / "scripts" / "config_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

    def test_config_command_help_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test config_command --help from different directory."""
        script = PROJECT_ROOT / "skills" / "config" / "scripts" / "config_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

    def test_settings_loader_imports_skills_modules(self) -> None:
        """Test that settings_loader.py can import skills.* modules.

        Regression test for ModuleNotFoundError: No module named 'skills'
        """
        script = PROJECT_ROOT / "skills" / "config" / "scripts" / "settings_loader.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert "ModuleNotFoundError" not in result.stderr, f"Import failed: {result.stderr}"
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"


class TestTemplatesCommandInvocation:
    """Test templates command can be invoked via subprocess."""

    def test_templates_command_help_via_uv_run(self) -> None:
        """Test uv run templates_command.py --help works."""
        script = PROJECT_ROOT / "skills" / "templates" / "scripts" / "templates_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"

    def test_templates_command_help_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test templates_command --help from different directory."""
        script = PROJECT_ROOT / "skills" / "templates" / "scripts" / "templates_command.py"
        result = subprocess.run(
            ["uv", "run", str(script), "--help"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, f"Failed with stderr: {result.stderr}"


class TestAllSkillScriptsImportCorrectly:
    """Meta-test: verify all skill scripts can be invoked without import errors.

    This is the key regression test class that would catch the
    'ModuleNotFoundError: No module named skills' bug across ALL scripts.
    """

    def test_all_command_scripts_have_working_help(self) -> None:
        """Test that all *_command.py scripts respond to --help."""
        command_scripts = list(PROJECT_ROOT.glob("skills/*/scripts/*_command.py"))
        assert len(command_scripts) >= 3, "Expected at least 3 command scripts"

        failures = []
        for script in command_scripts:
            result = subprocess.run(
                ["uv", "run", str(script), "--help"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                failures.append(f"{script.name}: {result.stderr[:200]}")
            if "ModuleNotFoundError" in result.stderr:
                failures.append(f"{script.name}: ModuleNotFoundError in imports")

        assert not failures, "Script failures:\n" + "\n".join(failures)

    def test_all_command_scripts_work_from_tmp_dir(self, tmp_path: Path) -> None:
        """Test all *_command.py scripts work from different working directory.

        This catches sys.path issues that only manifest when cwd != project root.
        """
        command_scripts = list(PROJECT_ROOT.glob("skills/*/scripts/*_command.py"))

        failures = []
        for script in command_scripts:
            result = subprocess.run(
                ["uv", "run", str(script), "--help"],
                cwd=tmp_path,  # Different working directory!
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                failures.append(f"{script.name}: exit {result.returncode}")
            if "ModuleNotFoundError" in result.stderr:
                failures.append(f"{script.name}: ModuleNotFoundError")

        assert not failures, "Script failures from tmp_dir:\n" + "\n".join(failures)
