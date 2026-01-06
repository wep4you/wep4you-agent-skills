"""
Tests for skills.core.vault.detection module.

Tests vault detection utilities including detect_vault, is_obsidian_vault,
and find_vault_root functions.
"""

from skills.core.vault.detection import (
    detect_vault,
    find_vault_root,
    is_obsidian_vault,
)


class TestDetectVault:
    """Tests for detect_vault function."""

    def test_path_does_not_exist(self, tmp_path):
        """Test detection when path does not exist."""
        non_existent = tmp_path / "does_not_exist"
        result = detect_vault(non_existent)

        assert result["exists"] is False
        assert result["has_obsidian"] is False
        assert result["has_claude_config"] is False
        assert result["has_content"] is False
        assert result["folder_count"] == 0
        assert result["file_count"] == 0
        assert result["current_methodology"] is None

    def test_empty_vault(self, tmp_path):
        """Test detection of empty directory."""
        empty_dir = tmp_path / "empty_vault"
        empty_dir.mkdir()

        result = detect_vault(empty_dir)

        assert result["exists"] is True
        assert result["has_obsidian"] is False
        assert result["has_claude_config"] is False
        assert result["has_content"] is False
        assert result["folder_count"] == 0
        assert result["file_count"] == 0
        assert result["current_methodology"] is None

    def test_vault_with_obsidian(self, tmp_path):
        """Test detection of vault with .obsidian directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_obsidian"] is True
        assert result["has_claude_config"] is False
        assert result["has_content"] is False
        assert result["folder_count"] == 0
        assert result["file_count"] == 0

    def test_vault_with_claude_config(self, tmp_path):
        """Test detection of vault with .claude directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".claude").mkdir()

        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_obsidian"] is False
        assert result["has_claude_config"] is True
        assert result["has_content"] is False
        assert result["folder_count"] == 0
        assert result["file_count"] == 0

    def test_vault_with_both_obsidian_and_claude(self, tmp_path):
        """Test detection of vault with both .obsidian and .claude directories."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        (vault / ".claude").mkdir()

        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_obsidian"] is True
        assert result["has_claude_config"] is True
        assert result["has_content"] is False

    def test_vault_with_content_folders(self, tmp_path):
        """Test detection of vault with non-hidden folders."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Projects").mkdir()
        (vault / "Notes").mkdir()
        (vault / "Archive").mkdir()

        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_content"] is True
        assert result["folder_count"] == 3
        assert result["file_count"] == 0

    def test_vault_with_content_files(self, tmp_path):
        """Test detection of vault with non-hidden files."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "note1.md").write_text("# Note 1")
        (vault / "note2.md").write_text("# Note 2")
        (vault / "README.md").write_text("# README")

        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_content"] is True
        assert result["folder_count"] == 0
        assert result["file_count"] == 3

    def test_vault_with_mixed_content(self, tmp_path):
        """Test detection of vault with both folders and files."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Projects").mkdir()
        (vault / "Notes").mkdir()
        (vault / "index.md").write_text("# Index")
        (vault / "config.yaml").write_text("version: 1")

        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_content"] is True
        assert result["folder_count"] == 2
        assert result["file_count"] == 2

    def test_vault_ignores_hidden_content(self, tmp_path):
        """Test that hidden files and folders are not counted."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        (vault / ".claude").mkdir()
        (vault / ".git").mkdir()
        (vault / ".DS_Store").write_text("")
        (vault / ".hidden_file").write_text("")

        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_obsidian"] is True
        assert result["has_claude_config"] is True
        assert result["has_content"] is False
        assert result["folder_count"] == 0
        assert result["file_count"] == 0

    def test_vault_mixed_hidden_and_visible(self, tmp_path):
        """Test vault with both hidden and visible content."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        (vault / ".git").mkdir()
        (vault / "Projects").mkdir()
        (vault / ".DS_Store").write_text("")
        (vault / "note.md").write_text("# Note")

        result = detect_vault(vault)

        assert result["has_content"] is True
        assert result["folder_count"] == 1
        assert result["file_count"] == 1


class TestDetectVaultMethodology:
    """Tests for methodology reading in detect_vault."""

    def test_reads_methodology_from_settings_yaml(self, tmp_path):
        """Test that methodology is read from settings.yaml."""
        vault = tmp_path / "vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
methodology: lyt-ace
version: "1.0"
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        result = detect_vault(vault)

        assert result["current_methodology"] == "lyt-ace"

    def test_methodology_para(self, tmp_path):
        """Test reading PARA methodology from settings."""
        vault = tmp_path / "vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
methodology: para
version: "2.0"
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        result = detect_vault(vault)

        assert result["current_methodology"] == "para"

    def test_methodology_johnny_decimal(self, tmp_path):
        """Test reading Johnny Decimal methodology from settings."""
        vault = tmp_path / "vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
methodology: johnny-decimal
version: "1.0"
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        result = detect_vault(vault)

        assert result["current_methodology"] == "johnny-decimal"

    def test_no_methodology_in_settings(self, tmp_path):
        """Test when settings.yaml exists but has no methodology key."""
        vault = tmp_path / "vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        settings_content = """
version: "1.0"
logging:
  level: INFO
"""
        (claude_dir / "settings.yaml").write_text(settings_content)

        result = detect_vault(vault)

        assert result["current_methodology"] is None

    def test_empty_settings_file(self, tmp_path):
        """Test when settings.yaml is empty."""
        vault = tmp_path / "vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.yaml").write_text("")

        result = detect_vault(vault)

        assert result["current_methodology"] is None

    def test_invalid_yaml_in_settings(self, tmp_path):
        """Test when settings.yaml contains invalid YAML."""
        vault = tmp_path / "vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        invalid_yaml = """
methodology: lyt-ace
  invalid: indentation
    broken: yaml
"""
        (claude_dir / "settings.yaml").write_text(invalid_yaml)

        result = detect_vault(vault)

        assert result["current_methodology"] is None

    def test_no_settings_file(self, tmp_path):
        """Test when .claude directory exists but settings.yaml does not."""
        vault = tmp_path / "vault"
        vault.mkdir()
        claude_dir = vault / ".claude"
        claude_dir.mkdir()

        result = detect_vault(vault)

        assert result["current_methodology"] is None
        assert result["has_claude_config"] is True

    def test_no_claude_directory(self, tmp_path):
        """Test when .claude directory does not exist."""
        vault = tmp_path / "vault"
        vault.mkdir()

        result = detect_vault(vault)

        assert result["current_methodology"] is None
        assert result["has_claude_config"] is False


class TestIsObsidianVault:
    """Tests for is_obsidian_vault function."""

    def test_has_obsidian_directory(self, tmp_path):
        """Test returns True when .obsidian directory exists."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        assert is_obsidian_vault(vault) is True

    def test_no_obsidian_directory(self, tmp_path):
        """Test returns False when .obsidian directory does not exist."""
        vault = tmp_path / "vault"
        vault.mkdir()

        assert is_obsidian_vault(vault) is False

    def test_path_does_not_exist(self, tmp_path):
        """Test returns False when path does not exist."""
        non_existent = tmp_path / "does_not_exist"

        assert is_obsidian_vault(non_existent) is False

    def test_obsidian_is_file_not_directory(self, tmp_path):
        """Test returns False when .obsidian is a file, not a directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").write_text("not a directory")

        assert is_obsidian_vault(vault) is False

    def test_empty_vault_with_obsidian(self, tmp_path):
        """Test empty vault with .obsidian is still detected as Obsidian vault."""
        vault = tmp_path / "vault"
        vault.mkdir()
        obsidian_dir = vault / ".obsidian"
        obsidian_dir.mkdir()

        assert is_obsidian_vault(vault) is True

    def test_vault_with_other_hidden_dirs(self, tmp_path):
        """Test vault with other hidden dirs but no .obsidian."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".git").mkdir()
        (vault / ".vscode").mkdir()
        (vault / ".claude").mkdir()

        assert is_obsidian_vault(vault) is False

    def test_vault_with_obsidian_and_other_dirs(self, tmp_path):
        """Test vault with .obsidian and other hidden directories."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        (vault / ".git").mkdir()
        (vault / ".claude").mkdir()

        assert is_obsidian_vault(vault) is True

    def test_nested_obsidian_not_detected(self, tmp_path):
        """Test that nested .obsidian is not detected at parent level."""
        vault = tmp_path / "vault"
        vault.mkdir()
        subdir = vault / "subvault"
        subdir.mkdir()
        (subdir / ".obsidian").mkdir()

        # Parent should not be detected as Obsidian vault
        assert is_obsidian_vault(vault) is False
        # Subdirectory should be detected
        assert is_obsidian_vault(subdir) is True


class TestFindVaultRoot:
    """Tests for find_vault_root function."""

    def test_finds_root_from_vault_root(self, tmp_path):
        """Test finding vault root when starting at the root."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        result = find_vault_root(vault)

        assert result == vault

    def test_finds_root_from_subdirectory(self, tmp_path):
        """Test finding vault root from a subdirectory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        subdir = vault / "Projects"
        subdir.mkdir()

        result = find_vault_root(subdir)

        assert result == vault

    def test_finds_root_from_deeply_nested_directory(self, tmp_path):
        """Test finding vault root from deeply nested subdirectory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        deep_dir = vault / "Projects" / "Active" / "MyProject" / "notes"
        deep_dir.mkdir(parents=True)

        result = find_vault_root(deep_dir)

        assert result == vault

    def test_returns_none_if_not_in_vault(self, tmp_path):
        """Test returns None when not in an Obsidian vault."""
        not_vault = tmp_path / "not_a_vault"
        not_vault.mkdir()
        subdir = not_vault / "some" / "path"
        subdir.mkdir(parents=True)

        result = find_vault_root(subdir)

        assert result is None

    def test_returns_none_for_non_existent_path(self, tmp_path):
        """Test returns None for non-existent starting path."""
        non_existent = tmp_path / "does" / "not" / "exist"

        result = find_vault_root(non_existent)

        assert result is None

    def test_finds_correct_root_with_nested_vaults(self, tmp_path):
        """Test finds nearest vault root when vaults are nested."""
        outer_vault = tmp_path / "outer_vault"
        outer_vault.mkdir()
        (outer_vault / ".obsidian").mkdir()

        inner_vault = outer_vault / "projects" / "inner_vault"
        inner_vault.mkdir(parents=True)
        (inner_vault / ".obsidian").mkdir()

        subdir = inner_vault / "notes"
        subdir.mkdir()

        result = find_vault_root(subdir)

        assert result == inner_vault

    def test_finds_outer_vault_from_non_vault_nested_dir(self, tmp_path):
        """Test finds outer vault when nested directory is not a vault."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        # Create nested non-vault directory
        nested_dir = vault / "projects" / "code"
        nested_dir.mkdir(parents=True)

        result = find_vault_root(nested_dir)

        assert result == vault

    def test_finds_root_with_file_as_start_path(self, tmp_path):
        """Test finding vault root when starting from a file path."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        notes_dir = vault / "notes"
        notes_dir.mkdir()
        note_file = notes_dir / "note.md"
        note_file.write_text("# Note")

        # Starting from file should find vault root via parent
        result = find_vault_root(note_file)

        assert result == vault

    def test_resolves_symlinks(self, tmp_path):
        """Test that symlinks are resolved when finding vault root."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        subdir = vault / "notes"
        subdir.mkdir()

        # Create symlink pointing to subdir
        link = tmp_path / "link_to_notes"
        link.symlink_to(subdir)

        result = find_vault_root(link)

        assert result == vault


class TestFindVaultRootEdgeCases:
    """Edge case tests for find_vault_root function."""

    def test_empty_vault_with_obsidian(self, tmp_path):
        """Test finding root of empty vault with only .obsidian."""
        vault = tmp_path / "empty_vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        result = find_vault_root(vault)

        assert result == vault

    def test_vault_at_tmp_path_root(self, tmp_path):
        """Test vault located at the tmp_path root level."""
        (tmp_path / ".obsidian").mkdir()

        subdir = tmp_path / "notes"
        subdir.mkdir()

        result = find_vault_root(subdir)

        assert result == tmp_path

    def test_relative_paths_resolved(self, tmp_path):
        """Test that relative paths are properly resolved."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        subdir = vault / "notes"
        subdir.mkdir()

        # find_vault_root should resolve the path
        result = find_vault_root(subdir)

        assert result is not None
        assert result.is_absolute()


class TestIntegration:
    """Integration tests for vault detection functions."""

    def test_detect_and_is_obsidian_consistent(self, tmp_path):
        """Test that detect_vault and is_obsidian_vault are consistent."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        detect_result = detect_vault(vault)
        is_obsidian_result = is_obsidian_vault(vault)

        assert detect_result["has_obsidian"] == is_obsidian_result

    def test_detect_and_find_root_consistent(self, tmp_path):
        """Test that detect_vault and find_vault_root are consistent."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        subdir = vault / "notes"
        subdir.mkdir()

        root = find_vault_root(subdir)
        detect_result = detect_vault(root)

        assert root == vault
        assert detect_result["has_obsidian"] is True

    def test_full_vault_setup(self, tmp_path):
        """Test detection on a complete vault setup."""
        vault = tmp_path / "vault"
        vault.mkdir()

        # Set up .obsidian
        obsidian_dir = vault / ".obsidian"
        obsidian_dir.mkdir()
        (obsidian_dir / "app.json").write_text('{"theme": "dark"}')

        # Set up .claude with settings
        claude_dir = vault / ".claude"
        claude_dir.mkdir()
        settings_yaml = """
methodology: lyt-ace
version: "1.0"
"""
        (claude_dir / "settings.yaml").write_text(settings_yaml)

        # Set up content
        (vault / "Atlas" / "Dots").mkdir(parents=True)
        (vault / "Atlas" / "Maps").mkdir(parents=True)
        (vault / "Projects").mkdir()
        (vault / "index.md").write_text("# Home")
        (vault / "README.md").write_text("# My Vault")

        # Test detection
        result = detect_vault(vault)

        assert result["exists"] is True
        assert result["has_obsidian"] is True
        assert result["has_claude_config"] is True
        assert result["has_content"] is True
        assert result["folder_count"] == 2  # Atlas and Projects
        assert result["file_count"] == 2  # index.md and README.md
        assert result["current_methodology"] == "lyt-ace"

        # Test is_obsidian_vault
        assert is_obsidian_vault(vault) is True

        # Test find_vault_root from subdirectory
        deep_path = vault / "Atlas" / "Dots"
        found_root = find_vault_root(deep_path)
        assert found_root == vault

    def test_non_vault_directory_all_functions(self, tmp_path):
        """Test all functions return expected values for non-vault directory."""
        not_vault = tmp_path / "regular_dir"
        not_vault.mkdir()
        (not_vault / "file.txt").write_text("content")
        (not_vault / "subdir").mkdir()

        # detect_vault
        detect_result = detect_vault(not_vault)
        assert detect_result["exists"] is True
        assert detect_result["has_obsidian"] is False
        assert detect_result["has_content"] is True

        # is_obsidian_vault
        assert is_obsidian_vault(not_vault) is False

        # find_vault_root
        assert find_vault_root(not_vault) is None
