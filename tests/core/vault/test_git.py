"""
Tests for skills.core.vault.git module.

Tests git utilities for Obsidian vault operations including:
- DEFAULT_GITIGNORE constant
- is_git_repo function
- create_gitignore function
- init_git_repo function
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skills.core.vault.git import (
    DEFAULT_GITIGNORE,
    create_gitignore,
    init_git_repo,
    is_git_repo,
)


class TestDefaultGitignore:
    """Tests for DEFAULT_GITIGNORE constant."""

    def test_contains_obsidian_workspace(self):
        """Test that gitignore contains Obsidian workspace patterns."""
        assert ".obsidian/workspace.json" in DEFAULT_GITIGNORE
        assert ".obsidian/workspace-mobile.json" in DEFAULT_GITIGNORE

    def test_contains_obsidian_cache(self):
        """Test that gitignore contains Obsidian cache pattern."""
        assert ".obsidian/cache" in DEFAULT_GITIGNORE

    def test_contains_obsidian_plugin_data(self):
        """Test that gitignore contains Obsidian plugin data pattern."""
        assert ".obsidian/plugins/*/data.json" in DEFAULT_GITIGNORE

    def test_contains_system_files(self):
        """Test that gitignore contains system file patterns."""
        assert ".DS_Store" in DEFAULT_GITIGNORE
        assert ".Trash/" in DEFAULT_GITIGNORE
        assert "Thumbs.db" in DEFAULT_GITIGNORE

    def test_contains_claude_code_patterns(self):
        """Test that gitignore contains Claude Code patterns."""
        assert ".claude/logs/" in DEFAULT_GITIGNORE
        assert ".claude/backups/" in DEFAULT_GITIGNORE

    def test_contains_editor_patterns(self):
        """Test that gitignore contains editor temporary file patterns."""
        assert "*.swp" in DEFAULT_GITIGNORE
        assert "*.swo" in DEFAULT_GITIGNORE
        assert "*~" in DEFAULT_GITIGNORE

    def test_has_section_comments(self):
        """Test that gitignore has section comments for organization."""
        assert "# Obsidian" in DEFAULT_GITIGNORE
        assert "# System" in DEFAULT_GITIGNORE
        assert "# Claude Code" in DEFAULT_GITIGNORE
        assert "# Editor" in DEFAULT_GITIGNORE

    def test_is_non_empty_string(self):
        """Test that DEFAULT_GITIGNORE is a non-empty string."""
        assert isinstance(DEFAULT_GITIGNORE, str)
        assert len(DEFAULT_GITIGNORE) > 0

    def test_starts_with_comment(self):
        """Test that gitignore starts with a comment (Obsidian section)."""
        assert DEFAULT_GITIGNORE.strip().startswith("# Obsidian")


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_returns_true_when_git_directory_exists(self, tmp_path):
        """Test that is_git_repo returns True when .git directory exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = is_git_repo(tmp_path)

        assert result is True

    def test_returns_false_when_no_git_directory(self, tmp_path):
        """Test that is_git_repo returns False when .git directory does not exist."""
        result = is_git_repo(tmp_path)

        assert result is False

    def test_returns_false_when_path_does_not_exist(self, tmp_path):
        """Test that is_git_repo returns False when path does not exist."""
        non_existent_path = tmp_path / "non_existent"

        result = is_git_repo(non_existent_path)

        assert result is False

    def test_returns_false_when_git_is_file_not_directory(self, tmp_path):
        """Test that is_git_repo returns False when .git is a file, not a directory."""
        git_file = tmp_path / ".git"
        git_file.write_text("ref: refs/heads/main")

        result = is_git_repo(tmp_path)

        assert result is False

    def test_with_nested_directories(self, tmp_path):
        """Test is_git_repo works with nested directory structures."""
        nested_path = tmp_path / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)
        git_dir = nested_path / ".git"
        git_dir.mkdir()

        result = is_git_repo(nested_path)

        assert result is True

    def test_does_not_check_parent_directories(self, tmp_path):
        """Test that is_git_repo only checks the given path, not parents."""
        # Create .git in parent
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Create child directory without .git
        child_dir = tmp_path / "child"
        child_dir.mkdir()

        result = is_git_repo(child_dir)

        assert result is False


class TestCreateGitignore:
    """Tests for create_gitignore function."""

    def test_creates_gitignore_file(self, tmp_path, capsys):
        """Test that create_gitignore creates .gitignore file with default content."""
        result = create_gitignore(tmp_path)

        assert result is True
        gitignore_path = tmp_path / ".gitignore"
        assert gitignore_path.exists()
        assert gitignore_path.read_text() == DEFAULT_GITIGNORE

        captured = capsys.readouterr()
        assert "Created: .gitignore" in captured.out

    def test_returns_true_when_gitignore_already_exists(self, tmp_path, capsys):
        """Test that create_gitignore returns True when .gitignore already exists."""
        gitignore_path = tmp_path / ".gitignore"
        existing_content = "# Existing content\n*.log"
        gitignore_path.write_text(existing_content)

        result = create_gitignore(tmp_path)

        assert result is True
        # Should not modify existing file
        assert gitignore_path.read_text() == existing_content

        captured = capsys.readouterr()
        assert "Created: .gitignore" not in captured.out

    def test_dry_run_does_not_create_file(self, tmp_path, capsys):
        """Test that create_gitignore with dry_run=True does not create file."""
        result = create_gitignore(tmp_path, dry_run=True)

        assert result is True
        gitignore_path = tmp_path / ".gitignore"
        assert not gitignore_path.exists()

        captured = capsys.readouterr()
        assert "[DRY RUN] Would create .gitignore" in captured.out

    def test_dry_run_with_existing_file_returns_true(self, tmp_path, capsys):
        """Test that create_gitignore with dry_run=True returns True when file exists."""
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("# Existing")

        result = create_gitignore(tmp_path, dry_run=True)

        assert result is True
        captured = capsys.readouterr()
        # Should not print dry run message since file exists
        assert "[DRY RUN]" not in captured.out

    def test_returns_false_on_write_error(self, tmp_path, capsys):
        """Test that create_gitignore returns False when write fails."""
        # Mock Path.write_text to raise an OSError
        with patch.object(Path, "write_text", side_effect=OSError("Permission denied")):
            result = create_gitignore(tmp_path)

            assert result is False
            captured = capsys.readouterr()
            assert "Error creating .gitignore:" in captured.out

    def test_gitignore_content_is_complete(self, tmp_path):
        """Test that created .gitignore contains all expected patterns."""
        create_gitignore(tmp_path)

        content = (tmp_path / ".gitignore").read_text()
        # Verify essential patterns are present
        assert ".obsidian/workspace.json" in content
        assert ".DS_Store" in content
        assert ".claude/logs/" in content
        assert "*.swp" in content


class TestInitGitRepo:
    """Tests for init_git_repo function."""

    def test_dry_run_prints_messages(self, tmp_path, capsys):
        """Test that init_git_repo with dry_run=True prints expected messages."""
        with patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"):
            result = init_git_repo(
                tmp_path, commit_message="Test commit", dry_run=True
            )

        assert result is True
        captured = capsys.readouterr()
        assert "[DRY RUN] Would initialize git repository" in captured.out
        assert '[DRY RUN] Would commit: "Test commit"' in captured.out

    def test_dry_run_does_not_create_git_repo(self, tmp_path):
        """Test that init_git_repo with dry_run=True does not create .git directory."""
        with patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"):
            init_git_repo(tmp_path, dry_run=True)

        git_dir = tmp_path / ".git"
        assert not git_dir.exists()

    def test_returns_true_when_already_git_repo(self, tmp_path, capsys):
        """Test that init_git_repo returns True when already a git repository."""
        # Create .git directory to simulate existing repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"):
            result = init_git_repo(tmp_path)

        assert result is True
        captured = capsys.readouterr()
        assert "Git repository already exists, skipping" in captured.out

    def test_returns_false_when_git_not_available(self, tmp_path, capsys):
        """Test that init_git_repo returns False when git is not in PATH."""
        with patch("skills.core.vault.git.shutil.which", return_value=None):
            result = init_git_repo(tmp_path)

        assert result is False
        captured = capsys.readouterr()
        assert "Git not found in PATH, skipping git initialization" in captured.out

    def test_successful_init_calls_git_commands(self, tmp_path, capsys):
        """Test that init_git_repo calls correct git commands on success."""
        mock_run = MagicMock()

        with (
            patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            result = init_git_repo(tmp_path, commit_message="Initial setup")

        assert result is True

        # Verify git init was called
        init_call = mock_run.call_args_list[0]
        assert init_call[0][0] == ["/usr/bin/git", "init"]
        assert init_call[1]["cwd"] == tmp_path
        assert init_call[1]["check"] is True

        # Verify git add was called
        add_call = mock_run.call_args_list[1]
        assert add_call[0][0] == ["/usr/bin/git", "add", "."]
        assert add_call[1]["cwd"] == tmp_path

        # Verify git commit was called
        commit_call = mock_run.call_args_list[2]
        assert commit_call[0][0] == ["/usr/bin/git", "commit", "-m", "Initial setup"]
        assert commit_call[1]["cwd"] == tmp_path

        captured = capsys.readouterr()
        assert "Initialized git repository" in captured.out
        assert 'Created initial commit: "Initial setup"' in captured.out

    def test_uses_default_commit_message(self, tmp_path):
        """Test that init_git_repo uses default commit message when not specified."""
        mock_run = MagicMock()

        with (
            patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            init_git_repo(tmp_path)

        # Verify default commit message was used
        commit_call = mock_run.call_args_list[2]
        assert commit_call[0][0][3] == "Initial vault setup"

    def test_returns_false_on_subprocess_error(self, tmp_path, capsys):
        """Test that init_git_repo returns False when subprocess fails."""
        import subprocess

        mock_run = MagicMock(
            side_effect=subprocess.CalledProcessError(1, "git init")
        )

        with (
            patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            result = init_git_repo(tmp_path)

        assert result is False
        captured = capsys.readouterr()
        assert "Git initialization failed:" in captured.out

    def test_subprocess_called_with_capture_output(self, tmp_path):
        """Test that subprocess.run is called with capture_output=True."""
        mock_run = MagicMock()

        with (
            patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            init_git_repo(tmp_path)

        for call in mock_run.call_args_list:
            assert call[1]["capture_output"] is True
            assert call[1]["text"] is True

    def test_custom_commit_message(self, tmp_path):
        """Test that init_git_repo uses custom commit message."""
        mock_run = MagicMock()
        custom_message = "Custom setup with PARA methodology"

        with (
            patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            init_git_repo(tmp_path, commit_message=custom_message)

        commit_call = mock_run.call_args_list[2]
        assert commit_call[0][0][3] == custom_message

    def test_dry_run_skips_when_already_git_repo(self, tmp_path, capsys):
        """Test that dry_run mode still checks for existing repo first."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"):
            result = init_git_repo(tmp_path, dry_run=True)

        assert result is True
        captured = capsys.readouterr()
        assert "Git repository already exists, skipping" in captured.out
        # Should not print dry run message since repo already exists
        assert "[DRY RUN]" not in captured.out


class TestIntegration:
    """Integration tests for git utilities."""

    def test_is_git_repo_after_simulated_init(self, tmp_path):
        """Test is_git_repo correctly detects repo after simulated init."""
        # Initially not a repo
        assert is_git_repo(tmp_path) is False

        # Simulate git init by creating .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Now should be a repo
        assert is_git_repo(tmp_path) is True

    def test_create_gitignore_then_check_content(self, tmp_path):
        """Test create_gitignore creates file with correct content."""
        create_gitignore(tmp_path)

        gitignore_path = tmp_path / ".gitignore"
        assert gitignore_path.exists()

        content = gitignore_path.read_text()
        # Verify it matches the constant
        assert content == DEFAULT_GITIGNORE

    def test_gitignore_persistence_across_calls(self, tmp_path):
        """Test that gitignore is not overwritten on subsequent calls."""
        # First call creates the file
        create_gitignore(tmp_path)

        # Modify the file
        gitignore_path = tmp_path / ".gitignore"
        modified_content = "# Modified content\n*.custom"
        gitignore_path.write_text(modified_content)

        # Second call should not modify it
        create_gitignore(tmp_path)

        assert gitignore_path.read_text() == modified_content


class TestEdgeCases:
    """Edge case tests for git utilities."""

    def test_is_git_repo_with_empty_git_directory(self, tmp_path):
        """Test is_git_repo with empty .git directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = is_git_repo(tmp_path)

        assert result is True

    def test_create_gitignore_in_nested_path(self, tmp_path):
        """Test create_gitignore works in deeply nested path."""
        nested_path = tmp_path / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)

        result = create_gitignore(nested_path)

        assert result is True
        assert (nested_path / ".gitignore").exists()

    def test_init_git_repo_with_empty_commit_message(self, tmp_path):
        """Test init_git_repo with empty commit message."""
        mock_run = MagicMock()

        with (
            patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            init_git_repo(tmp_path, commit_message="")

        commit_call = mock_run.call_args_list[2]
        assert commit_call[0][0][3] == ""

    def test_init_git_repo_with_special_characters_in_message(self, tmp_path):
        """Test init_git_repo with special characters in commit message."""
        mock_run = MagicMock()
        special_message = 'Initial "setup" with <special> & chars!'

        with (
            patch("skills.core.vault.git.shutil.which", return_value="/usr/bin/git"),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            init_git_repo(tmp_path, commit_message=special_message)

        commit_call = mock_run.call_args_list[2]
        assert commit_call[0][0][3] == special_message

    def test_create_gitignore_unicode_path(self, tmp_path):
        """Test create_gitignore with unicode characters in path."""
        unicode_path = tmp_path / "vault_notizen"
        unicode_path.mkdir()

        result = create_gitignore(unicode_path)

        assert result is True
        assert (unicode_path / ".gitignore").exists()

    @pytest.mark.parametrize(
        "git_path",
        [
            "/usr/bin/git",
            "/usr/local/bin/git",
            "/opt/homebrew/bin/git",
            "C:\\Program Files\\Git\\bin\\git.exe",
        ],
    )
    def test_init_git_repo_various_git_paths(self, tmp_path, git_path):
        """Test init_git_repo works with various git executable paths."""
        mock_run = MagicMock()

        with (
            patch("skills.core.vault.git.shutil.which", return_value=git_path),
            patch("skills.core.vault.git.subprocess.run", mock_run),
        ):
            result = init_git_repo(tmp_path)

        assert result is True
        # Verify the correct git path was used
        init_call = mock_run.call_args_list[0]
        assert init_call[0][0][0] == git_path
