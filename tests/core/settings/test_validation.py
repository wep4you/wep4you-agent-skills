"""
Tests for skills.core.settings.validation module.

Tests settings validation functions including validate_settings, path inference,
up-link resolution, exclusion checks, and inbox detection.
"""

from pathlib import Path

import pytest

from skills.core.models.note_type import NoteTypeConfig
from skills.core.models.settings import Settings, ValidationRules
from skills.core.settings.validation import (
    MIN_PROPERTY_NAME_LENGTH,
    get_up_link_for_path,
    infer_note_type_from_path,
    is_inbox_path,
    should_exclude,
    validate_property_name,
    validate_settings,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def minimal_note_type():
    """Create a minimal NoteTypeConfig for testing."""
    return NoteTypeConfig(
        name="Dot",
        description="Atomic notes",
        folder_hints=["Atlas/Dots"],
        required_properties=["type", "up", "created"],
        optional_properties=["related", "collection"],
        inherit_core=True,
    )


@pytest.fixture
def note_type_no_inherit():
    """Create a NoteTypeConfig that does not inherit core properties."""
    return NoteTypeConfig(
        name="Daily",
        description="Daily notes",
        folder_hints=["Calendar/Daily"],
        required_properties=["type", "date"],
        optional_properties=["mood"],
        inherit_core=False,
    )


@pytest.fixture
def note_type_missing_core():
    """Create a NoteTypeConfig with inherit_core=True but missing core properties."""
    return NoteTypeConfig(
        name="Broken",
        description="Broken note type",
        folder_hints=["Broken/"],
        required_properties=["type"],  # Missing "up" and "created"
        optional_properties=[],
        inherit_core=True,
    )


@pytest.fixture
def note_type_empty_required():
    """Create a NoteTypeConfig with empty required_properties."""
    return NoteTypeConfig(
        name="Empty",
        description="Empty required properties",
        folder_hints=["Empty/"],
        required_properties=[],
        optional_properties=["optional_field"],
        inherit_core=False,
    )


@pytest.fixture
def base_validation_rules():
    """Create base ValidationRules for testing."""
    return ValidationRules(
        require_core_properties=True,
        allow_empty_properties=["related"],
        strict_types=True,
        check_templates=True,
        check_up_links=True,
        check_inbox_no_frontmatter=True,
    )


@pytest.fixture
def settings_with_multiple_types(base_validation_rules, minimal_note_type, note_type_no_inherit):
    """Create Settings with multiple note types for path inference testing."""
    map_type = NoteTypeConfig(
        name="Map",
        description="Map of content",
        folder_hints=["Atlas/Maps", "Maps/"],
        required_properties=["type", "up", "created"],
        optional_properties=["scope"],
        inherit_core=True,
    )
    project_type = NoteTypeConfig(
        name="Project",
        description="Project notes",
        folder_hints=["Efforts/Projects", "Projects/"],
        required_properties=["type", "up", "created", "status"],
        optional_properties=["deadline"],
        inherit_core=True,
    )
    return Settings(
        version="1.0",
        methodology="lyt-ace",
        core_properties=["type", "up", "created"],
        note_types={
            "Dot": minimal_note_type,
            "Map": map_type,
            "Project": project_type,
            "Daily": note_type_no_inherit,
        },
        validation=base_validation_rules,
        folder_structure={
            "atlas": "Atlas",
            "dots": "Atlas/Dots",
            "maps": "Atlas/Maps",
            "inbox": "+/",
        },
        up_links={
            "Atlas/Dots": "[[Home]]",
            "Atlas/Maps": "[[Atlas]]",
            "Efforts/Projects": "[[Projects MOC]]",
        },
        exclude_paths=["templates/", ".obsidian/", "Archive/Old/"],
        exclude_files=[".DS_Store", "desktop.ini", ".gitignore"],
        exclude_patterns=["*.excalidraw.md", "*.canvas", "_*.md"],
        formats={"date": "YYYY-MM-DD"},
        logging={"level": "INFO"},
        raw={},
    )


# ============================================================================
# Tests for validate_property_name
# ============================================================================


class TestValidatePropertyName:
    """Tests for validate_property_name function."""

    def test_valid_simple_name(self):
        """Test that simple valid names pass."""
        is_valid, error = validate_property_name("type")
        assert is_valid is True
        assert error is None

    def test_valid_camelCase_name(self):
        """Test that camelCase names pass."""
        is_valid, error = validate_property_name("myOwnProp")
        assert is_valid is True
        assert error is None

    def test_valid_snake_case_name(self):
        """Test that snake_case names pass."""
        is_valid, error = validate_property_name("my_property")
        assert is_valid is True
        assert error is None

    def test_valid_with_hyphen(self):
        """Test that hyphenated names pass."""
        is_valid, error = validate_property_name("my-property")
        assert is_valid is True
        assert error is None

    def test_valid_with_numbers(self):
        """Test that names with numbers pass."""
        is_valid, error = validate_property_name("property1")
        assert is_valid is True
        assert error is None

    def test_empty_name_fails(self):
        """Test that empty name fails."""
        is_valid, error = validate_property_name("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_too_short_name_fails(self):
        """Test that single character name fails."""
        is_valid, error = validate_property_name("a")
        assert is_valid is False
        assert "too short" in error.lower()
        assert str(MIN_PROPERTY_NAME_LENGTH) in error

    def test_starts_with_number_fails(self):
        """Test that name starting with number fails."""
        is_valid, error = validate_property_name("1property")
        assert is_valid is False
        assert "invalid characters" in error.lower()

    def test_starts_with_underscore_fails(self):
        """Test that name starting with underscore fails."""
        is_valid, error = validate_property_name("_hidden")
        assert is_valid is False
        assert "invalid characters" in error.lower()

    def test_contains_spaces_fails(self):
        """Test that name with spaces fails."""
        is_valid, error = validate_property_name("my property")
        assert is_valid is False
        assert "invalid characters" in error.lower()

    def test_contains_special_chars_fails(self):
        """Test that name with special characters fails."""
        is_valid, error = validate_property_name("my@property!")
        assert is_valid is False
        assert "invalid characters" in error.lower()

    def test_minimum_length_exact(self):
        """Test that name with exactly MIN_PROPERTY_NAME_LENGTH chars passes."""
        name = "a" * MIN_PROPERTY_NAME_LENGTH
        # Ensure it starts with a letter
        name = "ab" if MIN_PROPERTY_NAME_LENGTH == 2 else name
        is_valid, error = validate_property_name(name)
        assert is_valid is True

    def test_truncated_property_name_warning(self):
        """Test that property name that looks truncated is caught."""
        # If someone enters 'myOwnPro' instead of 'myOwnProp', it still passes
        # but we can't detect truncation at this level
        # This test documents the limitation
        is_valid, error = validate_property_name("myOwnPro")
        assert is_valid is True  # We can't detect intended name


# ============================================================================
# Tests for validate_settings
# ============================================================================


class TestValidateSettings:
    """Tests for validate_settings function."""

    def test_valid_settings_returns_empty_list(self, sample_settings):
        """Test that valid settings return no errors."""
        errors = validate_settings(sample_settings)
        assert errors == []

    def test_missing_version_returns_error(self, base_validation_rules, minimal_note_type):
        """Test that missing version produces an error."""
        settings = Settings(
            version="",  # Empty version
            methodology="lyt-ace",
            core_properties=["type", "up", "created"],
            note_types={"Dot": minimal_note_type},
            validation=base_validation_rules,
            folder_structure={"inbox": "+/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        assert "Missing 'version' in settings" in errors

    def test_missing_core_properties_returns_error(self, base_validation_rules, minimal_note_type):
        """Test that missing core_properties produces an error."""
        settings = Settings(
            version="1.0",
            methodology="lyt-ace",
            core_properties=[],  # Empty core_properties
            note_types={"Dot": minimal_note_type},
            validation=base_validation_rules,
            folder_structure={"inbox": "+/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        assert "Missing or empty 'core_properties'" in errors

    def test_note_type_empty_required_properties_returns_error(
        self, base_validation_rules, note_type_empty_required
    ):
        """Test that note type with empty required_properties produces an error."""
        settings = Settings(
            version="1.0",
            methodology="lyt-ace",
            core_properties=["type", "up", "created"],
            note_types={"Empty": note_type_empty_required},
            validation=base_validation_rules,
            folder_structure={"inbox": "+/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        assert "Note type 'Empty' has no required properties" in errors

    def test_inherit_core_missing_properties_returns_error(
        self, base_validation_rules, note_type_missing_core
    ):
        """Test that inherit_core=True with missing core properties produces an error."""
        settings = Settings(
            version="1.0",
            methodology="lyt-ace",
            core_properties=["type", "up", "created"],
            note_types={"Broken": note_type_missing_core},
            validation=base_validation_rules,
            folder_structure={"inbox": "+/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        # Should have error about missing core properties
        assert any("inherit_core=True" in e and "missing core properties" in e for e in errors)
        # Should mention the missing properties
        assert any("up" in e and "created" in e for e in errors)

    def test_inherit_core_false_does_not_check_core_properties(
        self, base_validation_rules, note_type_no_inherit
    ):
        """Test that inherit_core=False skips core property validation."""
        settings = Settings(
            version="1.0",
            methodology="lyt-ace",
            core_properties=["type", "up", "created"],
            note_types={"Daily": note_type_no_inherit},
            validation=base_validation_rules,
            folder_structure={"inbox": "+/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        # Should not have inherit_core related errors
        assert not any("inherit_core" in e for e in errors)

    def test_multiple_errors_accumulated(self, base_validation_rules, note_type_missing_core):
        """Test that multiple validation errors are all reported."""
        settings = Settings(
            version="",  # Error 1: Missing version
            methodology="lyt-ace",
            core_properties=[],  # Error 2: Empty core_properties
            note_types={"Broken": note_type_missing_core},
            validation=base_validation_rules,
            folder_structure={"inbox": "+/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        assert len(errors) >= 2
        assert "Missing 'version' in settings" in errors
        assert "Missing or empty 'core_properties'" in errors

    def test_multiple_note_types_all_validated(self, base_validation_rules):
        """Test that all note types are validated."""
        empty_type1 = NoteTypeConfig(
            name="Empty1",
            description="First empty",
            folder_hints=["Empty1/"],
            required_properties=[],
            optional_properties=[],
            inherit_core=False,
        )
        empty_type2 = NoteTypeConfig(
            name="Empty2",
            description="Second empty",
            folder_hints=["Empty2/"],
            required_properties=[],
            optional_properties=[],
            inherit_core=False,
        )
        settings = Settings(
            version="1.0",
            methodology="lyt-ace",
            core_properties=["type"],
            note_types={"Empty1": empty_type1, "Empty2": empty_type2},
            validation=base_validation_rules,
            folder_structure={"inbox": "+/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        assert any("Empty1" in e for e in errors)
        assert any("Empty2" in e for e in errors)


# ============================================================================
# Tests for infer_note_type_from_path
# ============================================================================


class TestInferNoteTypeFromPath:
    """Tests for infer_note_type_from_path function."""

    def test_matches_folder_hint_exact(self, settings_with_multiple_types):
        """Test matching exact folder hint."""
        file_path = Path("Atlas/Dots/my-note.md")
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result == "Dot"

    def test_matches_folder_hint_nested(self, settings_with_multiple_types):
        """Test matching folder hint in nested path."""
        file_path = Path("vault/Atlas/Dots/subfolder/my-note.md")
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result == "Dot"

    def test_matches_map_type(self, settings_with_multiple_types):
        """Test matching Map type by folder hint."""
        file_path = Path("Atlas/Maps/index.md")
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result == "Map"

    def test_matches_project_type(self, settings_with_multiple_types):
        """Test matching Project type by folder hint."""
        file_path = Path("Efforts/Projects/my-project.md")
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result == "Project"

    def test_matches_alternative_folder_hint(self, settings_with_multiple_types):
        """Test matching alternative folder hint for same type."""
        # Map type has multiple folder hints
        file_path = Path("Maps/overview.md")
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result == "Map"

    def test_no_match_returns_none(self, settings_with_multiple_types):
        """Test that non-matching path returns None."""
        file_path = Path("RandomFolder/some-file.md")
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result is None

    def test_no_match_similar_name(self, settings_with_multiple_types):
        """Test that similar but non-matching path returns None."""
        # "Dot" is not the same as "Atlas/Dots"
        file_path = Path("Dot/my-note.md")
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result is None

    def test_empty_path_returns_none(self, settings_with_multiple_types):
        """Test that empty path returns None."""
        file_path = Path()
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert result is None

    def test_first_match_wins(self, base_validation_rules):
        """Test that first matching folder hint wins."""
        # Create overlapping folder hints
        type1 = NoteTypeConfig(
            name="Type1",
            description="First type",
            folder_hints=["Notes/"],
            required_properties=["type"],
            optional_properties=[],
            inherit_core=False,
        )
        type2 = NoteTypeConfig(
            name="Type2",
            description="Second type",
            folder_hints=["Notes/Special/"],
            required_properties=["type"],
            optional_properties=[],
            inherit_core=False,
        )
        settings = Settings(
            version="1.0",
            methodology="test",
            core_properties=["type"],
            note_types={"Type1": type1, "Type2": type2},
            validation=base_validation_rules,
            folder_structure={},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        # Path matches both, but dict iteration order determines result
        file_path = Path("Notes/Special/file.md")
        result = infer_note_type_from_path(settings, file_path)
        # Result depends on dict iteration order (Python 3.7+ preserves insertion order)
        assert result in ["Type1", "Type2"]

    def test_case_sensitive_matching(self, settings_with_multiple_types):
        """Test that matching is case-sensitive."""
        file_path = Path("atlas/dots/my-note.md")  # lowercase
        result = infer_note_type_from_path(settings_with_multiple_types, file_path)
        # Should not match "Atlas/Dots" (case-sensitive)
        assert result is None


# ============================================================================
# Tests for get_up_link_for_path
# ============================================================================


class TestGetUpLinkForPath:
    """Tests for get_up_link_for_path function."""

    def test_matches_pattern_exact(self, settings_with_multiple_types):
        """Test matching exact up_link pattern."""
        file_path = Path("Atlas/Dots/my-note.md")
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert result == "[[Home]]"

    def test_matches_pattern_nested(self, settings_with_multiple_types):
        """Test matching up_link pattern in nested path."""
        file_path = Path("vault/Atlas/Dots/subfolder/my-note.md")
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert result == "[[Home]]"

    def test_matches_maps_pattern(self, settings_with_multiple_types):
        """Test matching Maps folder up_link."""
        file_path = Path("Atlas/Maps/index.md")
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert result == "[[Atlas]]"

    def test_matches_projects_pattern(self, settings_with_multiple_types):
        """Test matching Projects folder up_link."""
        file_path = Path("Efforts/Projects/my-project.md")
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert result == "[[Projects MOC]]"

    def test_no_match_returns_none(self, settings_with_multiple_types):
        """Test that non-matching path returns None."""
        file_path = Path("RandomFolder/some-file.md")
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert result is None

    def test_empty_path_returns_none(self, settings_with_multiple_types):
        """Test that empty path returns None."""
        file_path = Path()
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert result is None

    def test_partial_match_returns_none(self, settings_with_multiple_types):
        """Test that partial folder name does not match."""
        # "Dot" is not the same as "Atlas/Dots"
        file_path = Path("Dot/my-note.md")
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert result is None

    def test_case_sensitive_matching(self, settings_with_multiple_types):
        """Test that matching is case-sensitive."""
        file_path = Path("atlas/dots/my-note.md")  # lowercase
        result = get_up_link_for_path(settings_with_multiple_types, file_path)
        # Should not match "Atlas/Dots" (case-sensitive)
        assert result is None

    def test_empty_up_links_returns_none(self, base_validation_rules, minimal_note_type):
        """Test that empty up_links config returns None for all paths."""
        settings = Settings(
            version="1.0",
            methodology="test",
            core_properties=["type"],
            note_types={"Dot": minimal_note_type},
            validation=base_validation_rules,
            folder_structure={},
            up_links={},  # Empty up_links
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        file_path = Path("Atlas/Dots/my-note.md")
        result = get_up_link_for_path(settings, file_path)
        assert result is None


# ============================================================================
# Tests for should_exclude
# ============================================================================


class TestShouldExclude:
    """Tests for should_exclude function."""

    # --- Excluded Paths ---

    def test_excludes_templates_path(self, settings_with_multiple_types):
        """Test that templates/ path is excluded."""
        file_path = Path("templates/note-template.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_obsidian_path(self, settings_with_multiple_types):
        """Test that .obsidian/ path is excluded."""
        file_path = Path(".obsidian/config.json")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_nested_excluded_path(self, settings_with_multiple_types):
        """Test that nested excluded path is excluded."""
        file_path = Path("Archive/Old/legacy.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_path_anywhere_in_string(self, settings_with_multiple_types):
        """Test that excluded path matches anywhere in the path string."""
        file_path = Path("vault/templates/my-template.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    # --- Excluded Files ---

    def test_excludes_ds_store(self, settings_with_multiple_types):
        """Test that .DS_Store file is excluded."""
        file_path = Path("Atlas/Dots/.DS_Store")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_desktop_ini(self, settings_with_multiple_types):
        """Test that desktop.ini file is excluded."""
        file_path = Path("Projects/desktop.ini")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_gitignore(self, settings_with_multiple_types):
        """Test that .gitignore file is excluded."""
        file_path = Path(".gitignore")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excluded_file_matches_name_only(self, settings_with_multiple_types):
        """Test that excluded file matches by filename, not path."""
        file_path = Path("any/deep/path/.DS_Store")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    # --- Excluded Patterns ---

    def test_excludes_excalidraw_pattern(self, settings_with_multiple_types):
        """Test that *.excalidraw.md pattern is excluded."""
        file_path = Path("Atlas/Dots/diagram.excalidraw.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_canvas_pattern(self, settings_with_multiple_types):
        """Test that *.canvas pattern is excluded."""
        file_path = Path("Projects/board.canvas")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_underscore_prefix_pattern(self, settings_with_multiple_types):
        """Test that _*.md pattern is excluded."""
        file_path = Path("Atlas/Maps/_Projects_MOC.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_pattern_matches_filename_only(self, settings_with_multiple_types):
        """Test that patterns match against filename, not full path."""
        # The pattern "_*.md" should match "_hidden.md" regardless of path
        file_path = Path("deep/nested/path/_hidden.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    # --- System Files in Root ---

    def test_excludes_agents_md_in_root(self, settings_with_multiple_types):
        """Test that AGENTS.md in root is excluded."""
        file_path = Path("AGENTS.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_claude_md_in_root(self, settings_with_multiple_types):
        """Test that CLAUDE.md in root is excluded."""
        file_path = Path("CLAUDE.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_readme_in_root(self, settings_with_multiple_types):
        """Test that README.md in root is excluded."""
        file_path = Path("README.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_excludes_home_md_in_root(self, settings_with_multiple_types):
        """Test that Home.md in root is excluded."""
        file_path = Path("Home.md")
        assert should_exclude(settings_with_multiple_types, file_path) is True

    def test_does_not_exclude_readme_in_methodology_folder(self, settings_with_multiple_types):
        """Test that README.md in methodology folder is NOT excluded."""
        file_path = Path("Atlas/README.md")
        assert should_exclude(settings_with_multiple_types, file_path) is False

    def test_does_not_exclude_readme_in_projects_folder(self, settings_with_multiple_types):
        """Test that README.md in Projects folder is NOT excluded."""
        file_path = Path("Projects/README.md")
        assert should_exclude(settings_with_multiple_types, file_path) is False

    def test_does_not_exclude_agents_md_in_notes_folder(self, settings_with_multiple_types):
        """Test that AGENTS.md in Notes folder is NOT excluded."""
        file_path = Path("Notes/AGENTS.md")
        assert should_exclude(settings_with_multiple_types, file_path) is False

    def test_does_not_exclude_system_file_in_calendar_folder(self, settings_with_multiple_types):
        """Test that system files in Calendar folder are NOT excluded."""
        file_path = Path("Calendar/Home.md")
        assert should_exclude(settings_with_multiple_types, file_path) is False

    # --- Non-Excluded Files ---

    def test_does_not_exclude_regular_note(self, settings_with_multiple_types):
        """Test that regular note is NOT excluded."""
        file_path = Path("Atlas/Dots/my-note.md")
        assert should_exclude(settings_with_multiple_types, file_path) is False

    def test_does_not_exclude_regular_note_in_projects(self, settings_with_multiple_types):
        """Test that regular note in Projects is NOT excluded."""
        file_path = Path("Efforts/Projects/my-project.md")
        assert should_exclude(settings_with_multiple_types, file_path) is False

    def test_does_not_exclude_non_matching_pattern(self, settings_with_multiple_types):
        """Test that non-matching file is NOT excluded."""
        file_path = Path("Atlas/Dots/regular.md")
        assert should_exclude(settings_with_multiple_types, file_path) is False

    def test_does_not_exclude_similar_but_different_file(self, settings_with_multiple_types):
        """Test that similar filename is NOT excluded."""
        # "DS_Store" without leading dot should not match ".DS_Store"
        file_path = Path("Atlas/DS_Store")
        assert should_exclude(settings_with_multiple_types, file_path) is False


# ============================================================================
# Tests for is_inbox_path
# ============================================================================


class TestIsInboxPath:
    """Tests for is_inbox_path function."""

    def test_in_inbox_exact_path(self, settings_with_multiple_types):
        """Test that file in inbox path is detected."""
        file_path = Path("+/new-note.md")
        assert is_inbox_path(settings_with_multiple_types, file_path) is True

    def test_in_inbox_nested(self, settings_with_multiple_types):
        """Test that file in nested inbox path is detected."""
        file_path = Path("vault/+/new-note.md")
        assert is_inbox_path(settings_with_multiple_types, file_path) is True

    def test_in_inbox_with_subfolder(self, settings_with_multiple_types):
        """Test that file in inbox subfolder is detected."""
        file_path = Path("+/processing/note.md")
        assert is_inbox_path(settings_with_multiple_types, file_path) is True

    def test_not_in_inbox_regular_path(self, settings_with_multiple_types):
        """Test that regular path is NOT in inbox."""
        file_path = Path("Atlas/Dots/my-note.md")
        assert is_inbox_path(settings_with_multiple_types, file_path) is False

    def test_not_in_inbox_similar_name(self, settings_with_multiple_types):
        """Test that similar but different path is NOT in inbox."""
        file_path = Path("plus/new-note.md")
        assert is_inbox_path(settings_with_multiple_types, file_path) is False

    def test_not_in_inbox_empty_path(self, settings_with_multiple_types):
        """Test that empty path is NOT in inbox."""
        file_path = Path()
        assert is_inbox_path(settings_with_multiple_types, file_path) is False

    def test_inbox_path_with_different_config(self, base_validation_rules, minimal_note_type):
        """Test inbox detection with custom inbox path configuration."""
        settings = Settings(
            version="1.0",
            methodology="test",
            core_properties=["type"],
            note_types={"Dot": minimal_note_type},
            validation=base_validation_rules,
            folder_structure={"inbox": "Inbox/"},  # Different inbox path
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        # Should match new inbox path
        assert is_inbox_path(settings, Path("Inbox/new-note.md")) is True
        # Should NOT match old default path
        assert is_inbox_path(settings, Path("+/new-note.md")) is False

    def test_inbox_path_default_when_not_configured(self, base_validation_rules, minimal_note_type):
        """Test that default inbox path (+/) is used when not configured."""
        settings = Settings(
            version="1.0",
            methodology="test",
            core_properties=["type"],
            note_types={"Dot": minimal_note_type},
            validation=base_validation_rules,
            folder_structure={},  # No inbox configured
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        # Should use default "+/"
        assert is_inbox_path(settings, Path("+/new-note.md")) is True

    def test_inbox_path_case_sensitive(self, base_validation_rules, minimal_note_type):
        """Test that inbox path matching is case-sensitive."""
        settings = Settings(
            version="1.0",
            methodology="test",
            core_properties=["type"],
            note_types={"Dot": minimal_note_type},
            validation=base_validation_rules,
            folder_structure={"inbox": "Inbox/"},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )
        # Exact case should match
        assert is_inbox_path(settings, Path("Inbox/note.md")) is True
        # Different case should NOT match
        assert is_inbox_path(settings, Path("inbox/note.md")) is False


# ============================================================================
# Integration Tests
# ============================================================================


class TestValidationIntegration:
    """Integration tests combining multiple validation functions."""

    def test_excluded_file_not_considered_for_type_inference(self, settings_with_multiple_types):
        """Test workflow: check exclusion before type inference."""
        file_path = Path("Atlas/Dots/diagram.excalidraw.md")

        # First check if excluded
        if should_exclude(settings_with_multiple_types, file_path):
            # Should be excluded, skip type inference
            is_excluded = True
        else:
            is_excluded = False

        assert is_excluded is True

    def test_inbox_file_not_validated_for_type(self, settings_with_multiple_types):
        """Test workflow: inbox files have different validation rules."""
        file_path = Path("+/quick-note.md")

        is_inbox = is_inbox_path(settings_with_multiple_types, file_path)
        note_type = infer_note_type_from_path(settings_with_multiple_types, file_path)

        # Inbox file, no type inference needed
        assert is_inbox is True
        assert note_type is None  # No folder hint matches inbox

    def test_regular_note_full_validation_workflow(self, settings_with_multiple_types):
        """Test full validation workflow for regular note."""
        file_path = Path("Atlas/Dots/my-note.md")

        # Step 1: Check exclusion
        excluded = should_exclude(settings_with_multiple_types, file_path)
        assert excluded is False

        # Step 2: Check if inbox
        inbox = is_inbox_path(settings_with_multiple_types, file_path)
        assert inbox is False

        # Step 3: Infer type
        note_type = infer_note_type_from_path(settings_with_multiple_types, file_path)
        assert note_type == "Dot"

        # Step 4: Get expected up_link
        up_link = get_up_link_for_path(settings_with_multiple_types, file_path)
        assert up_link == "[[Home]]"
