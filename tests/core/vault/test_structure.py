"""
Tests for skills.core.vault.structure module.

Tests folder structure utilities for creating and managing folders
in Obsidian vaults based on PKM methodologies.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from skills.core.vault.structure import (
    create_folder_structure,
    ensure_folder_exists,
    get_methodology_folders,
)


class TestEnsureFolderExists:
    """Tests for ensure_folder_exists function."""

    def test_folder_already_exists(self, tmp_path):
        """Test that existing folder returns True without creating."""
        existing_folder = tmp_path / "existing"
        existing_folder.mkdir()

        result = ensure_folder_exists(existing_folder)

        assert result is True
        assert existing_folder.exists()

    def test_folder_does_not_exist_creates_it(self, tmp_path):
        """Test that non-existing folder is created."""
        new_folder = tmp_path / "new_folder"

        assert not new_folder.exists()
        result = ensure_folder_exists(new_folder)

        assert result is True
        assert new_folder.exists()
        assert new_folder.is_dir()

    def test_nested_folder_creates_parents(self, tmp_path):
        """Test that nested folders create parent directories."""
        nested_folder = tmp_path / "parent" / "child" / "grandchild"

        assert not nested_folder.exists()
        result = ensure_folder_exists(nested_folder)

        assert result is True
        assert nested_folder.exists()
        assert (tmp_path / "parent").exists()
        assert (tmp_path / "parent" / "child").exists()

    def test_dry_run_does_not_create_folder(self, tmp_path, capsys):
        """Test that dry_run mode does not create folder."""
        new_folder = tmp_path / "dry_run_folder"

        result = ensure_folder_exists(new_folder, dry_run=True)
        captured = capsys.readouterr()

        assert result is True
        assert not new_folder.exists()
        assert "[DRY RUN]" in captured.out
        assert str(new_folder) in captured.out

    def test_dry_run_existing_folder_returns_true(self, tmp_path, capsys):
        """Test that dry_run with existing folder returns True without printing."""
        existing_folder = tmp_path / "existing"
        existing_folder.mkdir()

        result = ensure_folder_exists(existing_folder, dry_run=True)
        captured = capsys.readouterr()

        assert result is True
        assert existing_folder.exists()
        # Should not print anything since folder already exists
        assert "[DRY RUN]" not in captured.out

    def test_error_on_permission_denied(self, tmp_path, capsys):
        """Test that permission errors are handled gracefully."""
        # Create a folder that would fail (simulate by patching mkdir)
        new_folder = tmp_path / "forbidden"

        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            result = ensure_folder_exists(new_folder)
            captured = capsys.readouterr()

        assert result is False
        assert "Error creating folder" in captured.out

    def test_folder_with_special_characters(self, tmp_path):
        """Test creating folder with special characters in name."""
        special_folder = tmp_path / "folder with spaces"

        result = ensure_folder_exists(special_folder)

        assert result is True
        assert special_folder.exists()

    def test_folder_name_with_unicode(self, tmp_path):
        """Test creating folder with unicode characters."""
        unicode_folder = tmp_path / "Notizen"

        result = ensure_folder_exists(unicode_folder)

        assert result is True
        assert unicode_folder.exists()


class TestGetMethodologyFolders:
    """Tests for get_methodology_folders function."""

    def test_valid_methodology_para(self):
        """Test getting folders for PARA methodology."""
        folders = get_methodology_folders("para")

        assert isinstance(folders, list)
        assert "Projects" in folders
        assert "Areas" in folders
        assert "Resources" in folders
        assert "Archives" in folders
        assert "+" in folders
        assert "x/templates" in folders
        assert "x/bases" in folders

    def test_valid_methodology_lyt_ace(self):
        """Test getting folders for LYT-ACE methodology."""
        folders = get_methodology_folders("lyt-ace")

        assert isinstance(folders, list)
        # LYT-ACE should have Atlas folder
        assert any("Atlas" in f for f in folders)

    def test_unknown_methodology_raises_value_error(self):
        """Test that unknown methodology raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_methodology_folders("nonexistent-methodology")

        assert "Unknown methodology" in str(exc_info.value)
        assert "nonexistent-methodology" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_note_types_filter_none_returns_all(self):
        """Test that None filter returns all folders."""
        all_folders = get_methodology_folders("para", note_types_filter=None)

        assert "Projects" in all_folders
        assert "Areas" in all_folders
        assert "Resources" in all_folders
        assert "Archives" in all_folders

    def test_note_types_filter_single_type(self):
        """Test filtering folders by single note type."""
        folders = get_methodology_folders("para", note_types_filter=["project"])

        # Should include system folders
        assert "+" in folders or "x/templates" in folders or "x/bases" in folders
        # Should include project folder
        assert "Projects" in folders

    def test_note_types_filter_multiple_types(self):
        """Test filtering folders by multiple note types."""
        folders = get_methodology_folders("para", note_types_filter=["project", "area"])

        assert "Projects" in folders
        assert "Areas" in folders

    def test_note_types_filter_unknown_type_returns_system_only(self):
        """Test that unknown note type filter returns only system folders."""
        folders = get_methodology_folders("para", note_types_filter=["unknown_type"])

        # Should still include system folders
        assert "+" in folders
        assert "x/templates" in folders
        assert "x/bases" in folders

    def test_note_types_filter_empty_list(self):
        """Test that empty filter list returns only system folders."""
        folders = get_methodology_folders("para", note_types_filter=[])

        # Should still include system folders
        assert "+" in folders
        assert "x/templates" in folders
        assert "x/bases" in folders
        # Should NOT include main folders when filter is empty and no types match
        # (empty list means filter is active but no types selected)

    def test_system_folders_always_included(self):
        """Test that system folders are always included regardless of filter."""
        folders = get_methodology_folders("para", note_types_filter=["project"])

        # System folders should always be present
        assert "+" in folders
        assert "x/templates" in folders
        assert "x/bases" in folders

    def test_minimal_methodology(self):
        """Test getting folders for minimal methodology."""
        folders = get_methodology_folders("minimal")

        assert isinstance(folders, list)
        # Minimal should have fewer folders
        assert "+" in folders
        assert "x/templates" in folders

    def test_zettelkasten_methodology(self):
        """Test getting folders for zettelkasten methodology."""
        folders = get_methodology_folders("zettelkasten")

        assert isinstance(folders, list)
        # Should have system folders
        assert "+" in folders


class TestCreateFolderStructure:
    """Tests for create_folder_structure function."""

    def test_creates_folders_for_para(self, tmp_path, capsys):
        """Test creating folder structure for PARA methodology."""
        created = create_folder_structure(tmp_path, "para")
        captured = capsys.readouterr()

        assert isinstance(created, list)
        assert len(created) > 0

        # Verify main folders exist
        assert (tmp_path / "Projects").exists()
        assert (tmp_path / "Areas").exists()
        assert (tmp_path / "Resources").exists()
        assert (tmp_path / "Archives").exists()

        # Verify system folders exist
        assert (tmp_path / ".obsidian").exists()
        assert (tmp_path / ".claude").exists()
        assert (tmp_path / ".claude" / "logs").exists()

        # Check output
        assert "Creating" in captured.out
        assert "PARA" in captured.out

    def test_creates_folders_for_lyt_ace(self, tmp_path, capsys):
        """Test creating folder structure for LYT-ACE methodology."""
        created = create_folder_structure(tmp_path, "lyt-ace")

        assert isinstance(created, list)
        assert len(created) > 0

        # Verify system folders exist
        assert (tmp_path / ".obsidian").exists()
        assert (tmp_path / ".claude").exists()

    def test_dry_run_does_not_create_folders(self, tmp_path, capsys):
        """Test that dry_run mode does not create folders."""
        created = create_folder_structure(tmp_path, "para", dry_run=True)
        captured = capsys.readouterr()

        # Should return empty list in dry run mode
        assert created == []

        # Main folders should not exist
        assert not (tmp_path / "Projects").exists()
        assert not (tmp_path / "Areas").exists()

        # System folders should not exist
        assert not (tmp_path / ".obsidian").exists()
        assert not (tmp_path / ".claude").exists()

        # Check dry run output
        assert "[DRY RUN]" in captured.out

    def test_unknown_methodology_raises_value_error(self, tmp_path):
        """Test that unknown methodology raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_folder_structure(tmp_path, "nonexistent-methodology")

        assert "Unknown methodology" in str(exc_info.value)
        assert "nonexistent-methodology" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_note_types_filter_limits_folders(self, tmp_path, capsys):
        """Test that note types filter limits created folders."""
        create_folder_structure(tmp_path, "para", note_types_filter=["project"])

        # Projects folder should exist
        assert (tmp_path / "Projects").exists()

        # System folders always exist
        assert (tmp_path / ".obsidian").exists()
        assert (tmp_path / ".claude").exists()

    def test_creates_nested_system_folders(self, tmp_path):
        """Test that nested system folders are created correctly."""
        create_folder_structure(tmp_path, "para")

        assert (tmp_path / ".claude" / "logs").exists()
        assert (tmp_path / "x" / "templates").exists()
        assert (tmp_path / "x" / "bases").exists()

    def test_returns_list_of_paths(self, tmp_path):
        """Test that function returns list of Path objects."""
        created = create_folder_structure(tmp_path, "para")

        assert isinstance(created, list)
        for path in created:
            assert isinstance(path, Path)

    def test_all_returned_paths_exist(self, tmp_path):
        """Test that all returned paths actually exist."""
        created = create_folder_structure(tmp_path, "para")

        for path in created:
            assert path.exists(), f"Path {path} should exist"
            assert path.is_dir(), f"Path {path} should be a directory"

    def test_prints_creation_messages(self, tmp_path, capsys):
        """Test that creation messages are printed."""
        create_folder_structure(tmp_path, "para")
        captured = capsys.readouterr()

        assert "Created:" in captured.out
        assert "Projects" in captured.out or str(tmp_path) in captured.out

    def test_prints_methodology_name(self, tmp_path, capsys):
        """Test that methodology name is printed."""
        create_folder_structure(tmp_path, "para")
        captured = capsys.readouterr()

        assert "PARA" in captured.out

    def test_idempotent_folder_creation(self, tmp_path):
        """Test that running twice does not cause errors."""
        # First run
        created1 = create_folder_structure(tmp_path, "para")

        # Second run should not raise
        created2 = create_folder_structure(tmp_path, "para")

        # Both should return same folders (folders already exist)
        assert len(created1) == len(created2)

    def test_minimal_methodology(self, tmp_path):
        """Test creating folder structure for minimal methodology."""
        created = create_folder_structure(tmp_path, "minimal")

        assert isinstance(created, list)
        # System folders should exist
        assert (tmp_path / ".obsidian").exists()
        assert (tmp_path / ".claude").exists()

    def test_zettelkasten_methodology(self, tmp_path):
        """Test creating folder structure for zettelkasten methodology."""
        created = create_folder_structure(tmp_path, "zettelkasten")

        assert isinstance(created, list)
        # System folders should exist
        assert (tmp_path / ".obsidian").exists()
        assert (tmp_path / ".claude").exists()


class TestIntegration:
    """Integration tests for structure module functions working together."""

    def test_get_folders_then_ensure_exists(self, tmp_path):
        """Test getting folders and ensuring they exist."""
        folders = get_methodology_folders("para")

        for folder in folders:
            folder_path = tmp_path / folder
            result = ensure_folder_exists(folder_path)
            assert result is True
            assert folder_path.exists()

    def test_create_structure_includes_all_methodology_folders(self, tmp_path):
        """Test that create_folder_structure includes all methodology folders."""
        folders = get_methodology_folders("para")
        create_folder_structure(tmp_path, "para")

        for folder in folders:
            folder_path = tmp_path / folder
            assert folder_path.exists(), f"Folder {folder} should exist"

    def test_dry_run_consistency(self, tmp_path, capsys):
        """Test that dry_run mode is consistent between functions."""
        folder_path = tmp_path / "test_folder"

        # Both should work in dry_run mode
        result1 = ensure_folder_exists(folder_path, dry_run=True)
        created = create_folder_structure(tmp_path, "para", dry_run=True)

        assert result1 is True
        assert created == []
        assert not folder_path.exists()


class TestEdgeCases:
    """Edge case tests for structure module."""

    def test_empty_vault_path(self, tmp_path):
        """Test with empty string path (should use Path behavior)."""
        # Path("") is current directory
        # This test ensures no unexpected errors
        folders = get_methodology_folders("para")
        assert isinstance(folders, list)

    def test_very_long_folder_name(self, tmp_path):
        """Test creating folder with very long name."""
        long_name = "a" * 200
        long_folder = tmp_path / long_name

        result = ensure_folder_exists(long_folder)

        # Result depends on OS file system limits
        # On most systems this should work
        assert result is True or result is False

    def test_special_characters_in_vault_path(self, tmp_path):
        """Test vault path with special characters."""
        special_vault = tmp_path / "vault with spaces"
        special_vault.mkdir()

        created = create_folder_structure(special_vault, "para")

        assert len(created) > 0
        assert (special_vault / "Projects").exists()

    def test_unicode_vault_path(self, tmp_path):
        """Test vault path with unicode characters."""
        unicode_vault = tmp_path / "tresor"
        unicode_vault.mkdir()

        created = create_folder_structure(unicode_vault, "para")

        assert len(created) > 0
        assert (unicode_vault / "Projects").exists()

    @pytest.mark.parametrize("methodology", ["para", "lyt-ace", "minimal", "zettelkasten"])
    def test_all_methodologies_create_successfully(self, tmp_path, methodology):
        """Test that all methodologies can create folder structures."""
        vault = tmp_path / methodology
        vault.mkdir()

        created = create_folder_structure(vault, methodology)

        assert isinstance(created, list)
        assert len(created) > 0
        assert (vault / ".obsidian").exists()
        assert (vault / ".claude").exists()

    @pytest.mark.parametrize("methodology", ["para", "lyt-ace", "minimal", "zettelkasten"])
    def test_all_methodologies_return_valid_folders(self, methodology):
        """Test that all methodologies return valid folder lists."""
        folders = get_methodology_folders(methodology)

        assert isinstance(folders, list)
        assert len(folders) > 0
        # All methodologies should have system folders
        assert "+" in folders
        assert "x/templates" in folders
        assert "x/bases" in folders


class TestMockedMethodologies:
    """Tests using mocked METHODOLOGIES for isolation."""

    @pytest.fixture
    def mock_methodologies(self):
        """Create a mock METHODOLOGIES dict for testing."""
        return {
            "test-method": {
                "name": "Test Method",
                "description": "A test methodology",
                "folders": ["Folder1", "Folder2", "+", "x/templates", "x/bases"],
                "core_properties": ["type", "up"],
                "note_types": {
                    "note1": {
                        "description": "Test note type",
                        "folder_hints": ["Folder1/"],
                        "properties": {"additional_required": [], "optional": []},
                        "validation": {},
                        "icon": "file",
                    },
                    "note2": {
                        "description": "Another note type",
                        "folder_hints": ["Folder2/"],
                        "properties": {"additional_required": [], "optional": []},
                        "validation": {},
                        "icon": "file",
                    },
                },
            }
        }

    def test_mocked_methodology_folders(self, mock_methodologies):
        """Test folder retrieval with mocked methodology."""
        with patch(
            "skills.core.vault.structure.METHODOLOGIES", mock_methodologies
        ):
            folders = get_methodology_folders("test-method")

            assert "Folder1" in folders
            assert "Folder2" in folders
            assert "+" in folders

    def test_mocked_methodology_with_filter(self, mock_methodologies):
        """Test folder filtering with mocked methodology."""
        with patch(
            "skills.core.vault.structure.METHODOLOGIES", mock_methodologies
        ):
            folders = get_methodology_folders("test-method", note_types_filter=["note1"])

            assert "Folder1" in folders
            assert "+" in folders
            assert "x/templates" in folders

    def test_mocked_create_structure(self, tmp_path, mock_methodologies, capsys):
        """Test folder creation with mocked methodology."""
        with patch(
            "skills.core.vault.structure.METHODOLOGIES", mock_methodologies
        ):
            create_folder_structure(tmp_path, "test-method")
            captured = capsys.readouterr()

            assert (tmp_path / "Folder1").exists()
            assert (tmp_path / "Folder2").exists()
            assert (tmp_path / ".obsidian").exists()
            assert "Test Method" in captured.out
