"""
Tests for skills.core.utils.paths module.

Tests path utility functions for MOC filenames, links, and folder extraction.
"""

import pytest

from skills.core.utils.paths import (
    extract_folder_name,
    get_moc_filename,
    get_moc_link,
)


class TestGetMocFilename:
    """Tests for get_moc_filename function."""

    def test_simple_folder_name(self):
        """Test MOC filename for simple folder name."""
        result = get_moc_filename("Projects")
        assert result == "_Projects_MOC.md"

    def test_single_word_folder(self):
        """Test MOC filename for single word folder."""
        result = get_moc_filename("Atlas")
        assert result == "_Atlas_MOC.md"

    def test_camel_case_folder(self):
        """Test MOC filename preserves case."""
        result = get_moc_filename("MyFolder")
        assert result == "_MyFolder_MOC.md"

    def test_lowercase_folder(self):
        """Test MOC filename for lowercase folder."""
        result = get_moc_filename("notes")
        assert result == "_notes_MOC.md"

    def test_folder_with_spaces(self):
        """Test MOC filename for folder with spaces."""
        result = get_moc_filename("My Notes")
        assert result == "_My Notes_MOC.md"

    def test_folder_with_numbers(self):
        """Test MOC filename for folder with numbers."""
        result = get_moc_filename("2024Notes")
        assert result == "_2024Notes_MOC.md"

    def test_folder_with_underscore(self):
        """Test MOC filename for folder with underscore."""
        result = get_moc_filename("my_notes")
        assert result == "_my_notes_MOC.md"

    def test_folder_with_hyphen(self):
        """Test MOC filename for folder with hyphen."""
        result = get_moc_filename("my-notes")
        assert result == "_my-notes_MOC.md"

    def test_empty_folder_name(self):
        """Test MOC filename for empty folder name."""
        result = get_moc_filename("")
        assert result == "__MOC.md"

    def test_folder_with_unicode(self):
        """Test MOC filename for folder with unicode characters."""
        result = get_moc_filename("Notizen")
        assert result == "_Notizen_MOC.md"

    def test_folder_with_special_chars(self):
        """Test MOC filename for folder with special characters."""
        result = get_moc_filename("Notes (Archive)")
        assert result == "_Notes (Archive)_MOC.md"

    @pytest.mark.parametrize(
        "folder_name,expected",
        [
            ("Projects", "_Projects_MOC.md"),
            ("Areas", "_Areas_MOC.md"),
            ("Resources", "_Resources_MOC.md"),
            ("Archive", "_Archive_MOC.md"),
            ("Dots", "_Dots_MOC.md"),
            ("Maps", "_Maps_MOC.md"),
            ("Calendar", "_Calendar_MOC.md"),
            ("Daily", "_Daily_MOC.md"),
        ],
    )
    def test_common_folder_names(self, folder_name, expected):
        """Test MOC filename for common folder names."""
        result = get_moc_filename(folder_name)
        assert result == expected


class TestGetMocLink:
    """Tests for get_moc_link function."""

    def test_simple_folder_name(self):
        """Test MOC link for simple folder name."""
        result = get_moc_link("Projects")
        assert result == "[[_Projects_MOC]]"

    def test_single_word_folder(self):
        """Test MOC link for single word folder."""
        result = get_moc_link("Atlas")
        assert result == "[[_Atlas_MOC]]"

    def test_camel_case_folder(self):
        """Test MOC link preserves case."""
        result = get_moc_link("MyFolder")
        assert result == "[[_MyFolder_MOC]]"

    def test_lowercase_folder(self):
        """Test MOC link for lowercase folder."""
        result = get_moc_link("notes")
        assert result == "[[_notes_MOC]]"

    def test_folder_with_spaces(self):
        """Test MOC link for folder with spaces."""
        result = get_moc_link("My Notes")
        assert result == "[[_My Notes_MOC]]"

    def test_folder_with_numbers(self):
        """Test MOC link for folder with numbers."""
        result = get_moc_link("2024Notes")
        assert result == "[[_2024Notes_MOC]]"

    def test_folder_with_underscore(self):
        """Test MOC link for folder with underscore."""
        result = get_moc_link("my_notes")
        assert result == "[[_my_notes_MOC]]"

    def test_folder_with_hyphen(self):
        """Test MOC link for folder with hyphen."""
        result = get_moc_link("my-notes")
        assert result == "[[_my-notes_MOC]]"

    def test_empty_folder_name(self):
        """Test MOC link for empty folder name."""
        result = get_moc_link("")
        assert result == "[[__MOC]]"

    def test_link_is_wikilink_format(self):
        """Test that result is in wikilink format."""
        result = get_moc_link("Test")
        assert result.startswith("[[")
        assert result.endswith("]]")

    def test_link_does_not_include_extension(self):
        """Test that link does not include .md extension."""
        result = get_moc_link("Projects")
        assert ".md" not in result

    @pytest.mark.parametrize(
        "folder_name,expected",
        [
            ("Projects", "[[_Projects_MOC]]"),
            ("Areas", "[[_Areas_MOC]]"),
            ("Resources", "[[_Resources_MOC]]"),
            ("Archive", "[[_Archive_MOC]]"),
            ("Dots", "[[_Dots_MOC]]"),
            ("Maps", "[[_Maps_MOC]]"),
        ],
    )
    def test_common_folder_links(self, folder_name, expected):
        """Test MOC link for common folder names."""
        result = get_moc_link(folder_name)
        assert result == expected


class TestExtractFolderName:
    """Tests for extract_folder_name function."""

    def test_simple_folder_name(self):
        """Test extracting simple folder name (no path)."""
        result = extract_folder_name("Projects")
        assert result == "Projects"

    def test_nested_path_one_level(self):
        """Test extracting folder from one-level nested path."""
        result = extract_folder_name("Efforts/Projects")
        assert result == "Projects"

    def test_nested_path_two_levels(self):
        """Test extracting folder from two-level nested path."""
        result = extract_folder_name("Atlas/Notes/Ideas")
        assert result == "Ideas"

    def test_nested_path_three_levels(self):
        """Test extracting folder from three-level nested path."""
        result = extract_folder_name("Root/Level1/Level2/Final")
        assert result == "Final"

    def test_trailing_slash(self):
        """Test handling of trailing slash."""
        result = extract_folder_name("Projects/")
        # With trailing slash, the last split element is empty
        assert result == ""

    def test_empty_string(self):
        """Test extracting from empty string."""
        result = extract_folder_name("")
        assert result == ""

    def test_single_slash(self):
        """Test handling of single slash."""
        result = extract_folder_name("/")
        assert result == ""

    def test_folder_with_spaces(self):
        """Test extracting folder with spaces."""
        result = extract_folder_name("My Folder/Sub Folder")
        assert result == "Sub Folder"

    def test_folder_with_underscore(self):
        """Test extracting folder with underscore."""
        result = extract_folder_name("parent/my_folder")
        assert result == "my_folder"

    def test_folder_with_hyphen(self):
        """Test extracting folder with hyphen."""
        result = extract_folder_name("parent/my-folder")
        assert result == "my-folder"

    def test_folder_with_numbers(self):
        """Test extracting folder with numbers."""
        result = extract_folder_name("Archive/2024")
        assert result == "2024"

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("Atlas/Dots", "Dots"),
            ("Atlas/Maps", "Maps"),
            ("Atlas/Sources", "Sources"),
            ("Calendar/Daily", "Daily"),
            ("Efforts/Projects", "Projects"),
            ("Efforts/Areas", "Areas"),
        ],
    )
    def test_common_vault_paths(self, path, expected):
        """Test extracting folder from common vault paths."""
        result = extract_folder_name(path)
        assert result == expected


class TestIntegration:
    """Integration tests for path utilities working together."""

    def test_extract_then_get_moc_filename(self):
        """Test extracting folder name then getting MOC filename."""
        path = "Efforts/Projects"
        folder_name = extract_folder_name(path)
        moc_filename = get_moc_filename(folder_name)
        assert moc_filename == "_Projects_MOC.md"

    def test_extract_then_get_moc_link(self):
        """Test extracting folder name then getting MOC link."""
        path = "Atlas/Dots"
        folder_name = extract_folder_name(path)
        moc_link = get_moc_link(folder_name)
        assert moc_link == "[[_Dots_MOC]]"

    def test_filename_and_link_consistency(self):
        """Test that filename and link refer to same MOC."""
        folder_name = "Projects"
        filename = get_moc_filename(folder_name)
        link = get_moc_link(folder_name)

        # Link should reference the same file (minus .md extension)
        expected_name = filename.replace(".md", "")
        assert expected_name in link

    @pytest.mark.parametrize(
        "path",
        [
            "Projects",
            "Efforts/Projects",
            "Atlas/Notes/Ideas",
            "Root/A/B/C/Deep",
        ],
    )
    def test_workflow_for_various_paths(self, path):
        """Test complete workflow for various path depths."""
        folder_name = extract_folder_name(path)
        filename = get_moc_filename(folder_name)
        link = get_moc_link(folder_name)

        # All should be non-empty for non-empty folder names
        if folder_name:
            assert filename.startswith("_")
            assert filename.endswith("_MOC.md")
            assert link.startswith("[[_")
            assert link.endswith("_MOC]]")


class TestEdgeCases:
    """Edge case tests for path utilities."""

    def test_very_long_folder_name(self):
        """Test handling of very long folder name."""
        long_name = "A" * 200
        filename = get_moc_filename(long_name)
        link = get_moc_link(long_name)

        assert filename == f"_{long_name}_MOC.md"
        assert link == f"[[_{long_name}_MOC]]"

    def test_folder_name_with_brackets(self):
        """Test folder name containing brackets."""
        folder_name = "[Important]"
        filename = get_moc_filename(folder_name)
        link = get_moc_link(folder_name)

        assert filename == "_[Important]_MOC.md"
        # Link with brackets in name
        assert link == "[[_[Important]_MOC]]"

    def test_folder_name_with_pipe(self):
        """Test folder name containing pipe character."""
        folder_name = "Notes|Archive"
        filename = get_moc_filename(folder_name)
        assert filename == "_Notes|Archive_MOC.md"

    def test_path_with_backslash(self):
        """Test path with backslash (Windows-style)."""
        # Note: function only handles forward slashes
        result = extract_folder_name("Parent\\Child")
        # Backslash is not treated as separator
        assert result == "Parent\\Child"

    def test_path_with_dot(self):
        """Test path with dot in folder name."""
        result = extract_folder_name("Archive/2024.01")
        assert result == "2024.01"

    def test_only_slash_characters(self):
        """Test path with only slashes."""
        result = extract_folder_name("///")
        assert result == ""

    def test_multiple_consecutive_slashes(self):
        """Test path with multiple consecutive slashes."""
        result = extract_folder_name("Parent//Child")
        assert result == "Child"

    def test_whitespace_folder_name(self):
        """Test folder name with only whitespace."""
        filename = get_moc_filename("   ")
        assert filename == "_   _MOC.md"

    def test_newline_in_folder_name(self):
        """Test folder name with newline."""
        folder_name = "Line1\nLine2"
        filename = get_moc_filename(folder_name)
        assert "Line1\nLine2" in filename
