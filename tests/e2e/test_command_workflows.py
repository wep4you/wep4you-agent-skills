"""
E2E tests for obsidian command workflows.

Tests the complete command workflows as they would be executed by Claude Code.
Each test creates a fresh vault and runs the full command sequence.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def commands_dir(project_root: Path) -> Path:
    """Get commands directory."""
    return project_root / "commands"


@pytest.fixture
def skills_dir(project_root: Path) -> Path:
    """Get skills directory."""
    return project_root / "skills"


def run_command(
    cmd: list[str], project_root: Path, cwd: Path | None = None
) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr.

    Args:
        cmd: Full command list to execute
        project_root: Path to project root
        cwd: Working directory (defaults to project_root)

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        cmd,
        cwd=cwd or project_root,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(project_root)},
        stdin=subprocess.DEVNULL,
    )
    return result.returncode, result.stdout, result.stderr


# =============================================================================
# INIT WORKFLOW TESTS
# =============================================================================


class TestInitWorkflow:
    """E2E tests for obsidian:init command workflow."""

    def test_init_step1_methodology_required(
        self, tmp_path: Path, project_root: Path, commands_dir: Path
    ):
        """Step 1: Initial call returns methodology_required prompt."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = ["uv", "run", str(commands_dir / "init.py"), str(vault)]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data["prompt_type"] == "methodology_required"
        assert len(data["options"]) == 4  # lyt-ace, para, zettelkasten, minimal

    def test_init_step2_note_types_required(
        self, tmp_path: Path, project_root: Path, commands_dir: Path
    ):
        """Step 2: With methodology, returns note_types_required prompt."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = ["uv", "run", str(commands_dir / "init.py"), str(vault), "-m", "para"]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data["prompt_type"] == "note_types_required"
        assert data["methodology"] == "para"

    def test_init_step3_ranking_system_required(
        self, tmp_path: Path, project_root: Path, commands_dir: Path
    ):
        """Step 3: With note types, returns ranking_system_required prompt."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data["prompt_type"] == "ranking_system_required"

    def test_init_step4_properties_required(
        self, tmp_path: Path, project_root: Path, commands_dir: Path
    ):
        """Step 4: With ranking system, returns properties_required prompt."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
            "--ranking-system=rank",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        data = json.loads(stdout)
        assert data["prompt_type"] == "properties_required"

    def test_init_full_workflow_creates_vault(
        self, tmp_path: Path, project_root: Path, commands_dir: Path
    ):
        """Full workflow: All parameters creates complete vault."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
            "--ranking-system=rank",
            "--core-properties=all",
            "--custom-properties=none",
            "--per-type-props=project:none;area:none;resource:none;archive:none",
            "--git=no",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"

        # Verify vault structure
        assert (vault / ".claude" / "settings.yaml").exists()
        assert (vault / "Projects").is_dir()
        assert (vault / "Areas").is_dir()
        assert (vault / "Resources").is_dir()
        assert (vault / "Archives").is_dir()
        assert (vault / "x" / "templates").is_dir()

        # Verify settings content
        settings = yaml.safe_load((vault / ".claude" / "settings.yaml").read_text())
        assert settings["methodology"] == "para"
        assert "project" in settings["note_types"]


# =============================================================================
# CONFIG WORKFLOW TESTS
# =============================================================================


class TestConfigWorkflow:
    """E2E tests for obsidian:config command workflow."""

    @pytest.fixture
    def initialized_vault(self, tmp_path: Path, project_root: Path, commands_dir: Path) -> Path:
        """Create an initialized vault for config tests."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
            "--ranking-system=rank",
            "--core-properties=all",
            "--custom-properties=none",
            "--per-type-props=project:none;area:none;resource:none;archive:none",
            "--git=no",
        ]
        run_command(cmd, project_root)
        return vault

    def test_config_show_displays_settings(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """config --show displays vault settings."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "config" / "scripts" / "settings_loader.py"),
            "--vault",
            str(initialized_vault),
            "--show",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "Methodology: para" in stdout
        assert "Note types:" in stdout

    def test_config_validate_passes_for_valid_config(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """config --validate passes for valid configuration."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "config" / "scripts" / "settings_loader.py"),
            "--vault",
            str(initialized_vault),
            "--validate",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "valid" in stdout.lower()

    def test_config_diff_shows_differences(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """config --diff shows differences from defaults."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "config" / "scripts" / "settings_loader.py"),
            "--vault",
            str(initialized_vault),
            "--diff",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "methodology" in stdout.lower()

    def test_config_reset_list_shows_methodologies(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """config --reset list shows available methodologies."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "config" / "scripts" / "settings_loader.py"),
            "--vault",
            str(initialized_vault),
            "--reset",
            "list",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "lyt-ace" in stdout.lower()
        assert "para" in stdout.lower()
        assert "zettelkasten" in stdout.lower()


# =============================================================================
# VALIDATE WORKFLOW TESTS
# =============================================================================


class TestValidateWorkflow:
    """E2E tests for obsidian:validate command workflow."""

    @pytest.fixture
    def initialized_vault(self, tmp_path: Path, project_root: Path, commands_dir: Path) -> Path:
        """Create an initialized vault for validate tests."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
            "--ranking-system=rank",
            "--core-properties=all",
            "--custom-properties=none",
            "--per-type-props=project:none;area:none;resource:none;archive:none",
            "--git=no",
        ]
        run_command(cmd, project_root)
        return vault

    def test_validate_clean_vault_passes(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """Validation passes for a clean initialized vault."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "validate" / "scripts" / "validator.py"),
            "--vault",
            str(initialized_vault),
            "--no-jsonl",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "No issues found" in stdout

    def test_validate_detects_empty_type(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """Validation detects notes with empty type property."""
        # Create a note with empty type
        bad_note = initialized_vault / "Projects" / "Bad Note.md"
        bad_note.write_text(
            """---
type:
up: "[[Projects/_Projects_MOC]]"
created: 2025-01-06
tags: []
---

# Bad Note
"""
        )

        cmd = [
            "uv",
            "run",
            str(skills_dir / "validate" / "scripts" / "validator.py"),
            "--vault",
            str(initialized_vault),
            "--no-jsonl",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 1, "Should fail with issues"
        assert "Empty Types" in stdout

    def test_validate_auto_mode_fixes_issues(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """Validation auto mode fixes detectable issues."""
        # Create a note with empty type
        bad_note = initialized_vault / "Projects" / "Bad Note.md"
        bad_note.write_text(
            """---
type:
up: "[[Projects/_Projects_MOC]]"
created: 2025-01-06
tags: []
---

# Bad Note
"""
        )

        cmd = [
            "uv",
            "run",
            str(skills_dir / "validate" / "scripts" / "validator.py"),
            "--vault",
            str(initialized_vault),
            "--mode",
            "auto",
            "--no-jsonl",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Auto-fix should succeed: {stderr}"
        assert "Fixed empty type" in stdout or "No issues found" in stdout


# =============================================================================
# TYPES WORKFLOW TESTS
# =============================================================================


class TestTypesWorkflow:
    """E2E tests for obsidian:types command workflow."""

    @pytest.fixture
    def initialized_vault(self, tmp_path: Path, project_root: Path, commands_dir: Path) -> Path:
        """Create an initialized vault for types tests."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
            "--ranking-system=rank",
            "--core-properties=all",
            "--custom-properties=none",
            "--per-type-props=project:none;area:none;resource:none;archive:none",
            "--git=no",
        ]
        run_command(cmd, project_root)
        return vault

    def test_types_list_shows_all_types(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """types --list shows all configured note types."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "note-types" / "scripts" / "note_types.py"),
            "--vault",
            str(initialized_vault),
            "--list",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "project" in stdout.lower()
        assert "area" in stdout.lower()
        assert "resource" in stdout.lower()
        assert "archive" in stdout.lower()

    def test_types_show_displays_type_details(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """types --show displays details for a specific type."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "note-types" / "scripts" / "note_types.py"),
            "--vault",
            str(initialized_vault),
            "--show",
            "project",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "project" in stdout.lower()
        assert "Projects/" in stdout

    def test_types_add_creates_new_type(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """types --add creates a new note type with config."""
        config = json.dumps(
            {
                "description": "Meeting notes",
                "folder": "Meetings/",
                "required_props": ["date"],
                "icon": "calendar",
            }
        )
        cmd = [
            "uv",
            "run",
            str(skills_dir / "note-types" / "scripts" / "note_types.py"),
            "--vault",
            str(initialized_vault),
            "--add",
            "meeting",
            "--config",
            config,
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert (initialized_vault / "Meetings").is_dir()
        assert (initialized_vault / "x" / "templates" / "meeting.md").exists()

    def test_types_remove_deletes_type(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """types --remove deletes a note type."""
        # First add a type
        config = json.dumps({"description": "Test", "folder": "Test/", "icon": "test"})
        add_cmd = [
            "uv",
            "run",
            str(skills_dir / "note-types" / "scripts" / "note_types.py"),
            "--vault",
            str(initialized_vault),
            "--add",
            "testtype",
            "--config",
            config,
        ]
        run_command(add_cmd, project_root)

        # Then remove it
        cmd = [
            "uv",
            "run",
            str(skills_dir / "note-types" / "scripts" / "note_types.py"),
            "--vault",
            str(initialized_vault),
            "--remove",
            "testtype",
            "--yes",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "Removed" in stdout


# =============================================================================
# PROPS WORKFLOW TESTS
# =============================================================================


class TestPropsWorkflow:
    """E2E tests for obsidian:props command workflow."""

    @pytest.fixture
    def initialized_vault(self, tmp_path: Path, project_root: Path, commands_dir: Path) -> Path:
        """Create an initialized vault for props tests."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
            "--ranking-system=rank",
            "--core-properties=all",
            "--custom-properties=none",
            "--per-type-props=project:none;area:none;resource:none;archive:none",
            "--git=no",
        ]
        run_command(cmd, project_root)
        return vault

    def test_props_list_core_shows_properties(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """props list-core shows all core properties."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "frontmatter" / "scripts" / "frontmatter.py"),
            "--vault",
            str(initialized_vault),
            "list-core",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "type" in stdout.lower()
        assert "created" in stdout.lower()

    def test_props_list_type_shows_type_properties(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """props list-type shows properties for a specific type."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "frontmatter" / "scripts" / "frontmatter.py"),
            "--vault",
            str(initialized_vault),
            "list-type",
            "project",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "status" in stdout.lower()

    def test_props_add_core_creates_property(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """props add-core creates a new core property."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "frontmatter" / "scripts" / "frontmatter.py"),
            "--vault",
            str(initialized_vault),
            "add-core",
            "author",
            "string",
            "--description",
            "Note author",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "Added" in stdout or "author" in stdout.lower()

    def test_props_remove_core_deletes_property(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """props remove-core deletes a core property."""
        # First add a property
        add_cmd = [
            "uv",
            "run",
            str(skills_dir / "frontmatter" / "scripts" / "frontmatter.py"),
            "--vault",
            str(initialized_vault),
            "add-core",
            "testprop",
            "string",
        ]
        run_command(add_cmd, project_root)

        # Then remove it
        cmd = [
            "uv",
            "run",
            str(skills_dir / "frontmatter" / "scripts" / "frontmatter.py"),
            "--vault",
            str(initialized_vault),
            "remove-core",
            "testprop",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "Removed" in stdout


# =============================================================================
# TEMPLATES WORKFLOW TESTS
# =============================================================================


class TestTemplatesWorkflow:
    """E2E tests for obsidian:templates command workflow."""

    @pytest.fixture
    def initialized_vault(self, tmp_path: Path, project_root: Path, commands_dir: Path) -> Path:
        """Create an initialized vault for templates tests."""
        vault = tmp_path / "vault"
        vault.mkdir()

        cmd = [
            "uv",
            "run",
            str(commands_dir / "init.py"),
            str(vault),
            "-m",
            "para",
            "--note-types=all",
            "--ranking-system=rank",
            "--core-properties=all",
            "--custom-properties=none",
            "--per-type-props=project:none;area:none;resource:none;archive:none",
            "--git=no",
        ]
        run_command(cmd, project_root)
        return vault

    def test_templates_list_shows_all_templates(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """templates --list shows all available templates."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "templates" / "scripts" / "templates.py"),
            "--vault",
            str(initialized_vault),
            "--list",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "project" in stdout.lower()
        assert "Total:" in stdout

    def test_templates_show_displays_content(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """templates --show displays template content."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "templates" / "scripts" / "templates.py"),
            "--vault",
            str(initialized_vault),
            "--show",
            "project",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert "type:" in stdout.lower()

    def test_templates_create_makes_new_template(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """templates --create creates a new template."""
        cmd = [
            "uv",
            "run",
            str(skills_dir / "templates" / "scripts" / "templates.py"),
            "--vault",
            str(initialized_vault),
            "--create",
            "test-template",
            "--content",
            "# {{title}}\n\nTest template content.",
        ]
        exit_code, stdout, stderr = run_command(cmd, project_root)

        assert exit_code == 0, f"Command failed: {stderr}"
        assert (initialized_vault / "x" / "templates" / "test-template.md").exists()

    def test_templates_delete_removes_template(
        self, initialized_vault: Path, project_root: Path, skills_dir: Path
    ):
        """templates --delete removes a vault template."""
        # First create a template
        create_cmd = [
            "uv",
            "run",
            str(skills_dir / "templates" / "scripts" / "templates.py"),
            "--vault",
            str(initialized_vault),
            "--create",
            "to-delete",
            "--content",
            "# Delete me",
        ]
        run_command(create_cmd, project_root)

        # Delete requires interactive confirmation, so we use subprocess with input
        cmd = [
            "uv",
            "run",
            str(skills_dir / "templates" / "scripts" / "templates.py"),
            "--vault",
            str(initialized_vault),
            "--delete",
            "to-delete",
        ]
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            input="y\n",
            env={**os.environ, "PYTHONPATH": str(project_root)},
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert not (initialized_vault / "x" / "templates" / "to-delete.md").exists()
