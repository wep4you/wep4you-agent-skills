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
