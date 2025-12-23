"""Tests for settings_loader.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from skills.config.scripts.settings_loader import (
    Settings,
    ValidationRules,
    create_default_settings,
    get_all_properties_for_type,
    get_core_properties,
    get_note_type,
    get_up_link_for_path,
    get_validation_rules,
    infer_note_type_from_path,
    is_inbox_path,
    load_settings,
    settings_exist,
    should_exclude,
    validate_settings,
)


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_settings_file_not_found(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised when settings don't exist."""
        with pytest.raises(FileNotFoundError, match="Settings file not found"):
            load_settings(tmp_path)

    def test_load_settings_create_if_missing(self, tmp_path: Path) -> None:
        """Test that settings are created when create_if_missing=True."""
        settings = load_settings(tmp_path, create_if_missing=True)
        assert settings.version == "1.0"
        assert settings.methodology == "lyt-ace"
        assert (tmp_path / ".claude" / "settings.yaml").exists()

    def test_load_settings_invalid_vault_path(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for nonexistent vault path."""
        with pytest.raises(ValueError, match="does not exist"):
            load_settings(tmp_path / "nonexistent")

    def test_load_settings_vault_is_file(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when vault path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        with pytest.raises(ValueError, match="not a directory"):
            load_settings(file_path)

    def test_load_settings_valid(self, tmp_path: Path) -> None:
        """Test loading valid settings file."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        config = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {
                "test": {
                    "description": "Test note type",
                    "folder_hints": ["Test/"],
                    "properties": {"required": ["type", "up"], "optional": ["tags"]},
                    "validation": {"allow_empty_up": False},
                    "icon": "star",
                }
            },
            "validation": {
                "require_core_properties": True,
                "allow_empty_properties": ["tags"],
                "strict_types": False,
            },
            "exclude": {"paths": ["+/"], "files": ["README.md"]},
        }

        with settings_file.open("w") as f:
            yaml.safe_dump(config, f)

        settings = load_settings(tmp_path)

        assert settings.version == "1.0"
        assert settings.methodology == "custom"
        assert settings.core_properties == ["type", "up", "created"]
        assert "test" in settings.note_types
        assert settings.note_types["test"].description == "Test note type"
        assert settings.validation.strict_types is False
        assert settings.exclude_paths == ["+/"]
        assert settings.exclude_files == ["README.md"]

    def test_load_settings_invalid_yaml(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for invalid YAML."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("invalid: yaml: content:")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_settings(tmp_path)

    def test_load_settings_empty_file(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for empty settings file."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("")

        with pytest.raises(ValueError, match="Empty settings file"):
            load_settings(tmp_path)


class TestCreateDefaultSettings:
    """Tests for create_default_settings function."""

    def test_create_default_settings(self, tmp_path: Path) -> None:
        """Test creating default settings."""
        settings_path = create_default_settings(tmp_path)
        assert settings_path.exists()
        assert (tmp_path / ".claude" / "logs").exists()

    def test_create_default_settings_custom_methodology(self, tmp_path: Path) -> None:
        """Test creating settings with custom methodology."""
        create_default_settings(tmp_path, methodology="para")
        settings = load_settings(tmp_path)
        assert settings.methodology == "para"


class TestGetNoteType:
    """Tests for get_note_type function."""

    def test_get_note_type_existing(self, tmp_path: Path) -> None:
        """Test getting an existing note type."""
        settings = load_settings(tmp_path, create_if_missing=True)
        note_type = get_note_type(settings, "map")
        assert note_type is not None
        assert note_type.name == "map"
        assert "Atlas/Maps/" in note_type.folder_hints

    def test_get_note_type_nonexistent(self, tmp_path: Path) -> None:
        """Test getting a nonexistent note type."""
        settings = load_settings(tmp_path, create_if_missing=True)
        note_type = get_note_type(settings, "nonexistent")
        assert note_type is None


class TestGetValidationRules:
    """Tests for get_validation_rules function."""

    def test_get_validation_rules(self, tmp_path: Path) -> None:
        """Test getting validation rules."""
        settings = load_settings(tmp_path, create_if_missing=True)
        rules = get_validation_rules(settings)
        assert isinstance(rules, ValidationRules)
        assert rules.require_core_properties is True
        assert "tags" in rules.allow_empty_properties


class TestGetCoreProperties:
    """Tests for get_core_properties function."""

    def test_get_core_properties(self, tmp_path: Path) -> None:
        """Test getting core properties."""
        settings = load_settings(tmp_path, create_if_missing=True)
        props = get_core_properties(settings)
        assert "type" in props
        assert "up" in props
        assert "created" in props
        assert "daily" in props
        assert "tags" in props


class TestGetAllPropertiesForType:
    """Tests for get_all_properties_for_type function."""

    def test_get_all_properties_for_existing_type(self, tmp_path: Path) -> None:
        """Test getting all properties for existing type."""
        settings = load_settings(tmp_path, create_if_missing=True)
        props = get_all_properties_for_type(settings, "source")
        assert "type" in props
        assert "author" in props
        assert "url" in props

    def test_get_all_properties_for_nonexistent_type(self, tmp_path: Path) -> None:
        """Test getting properties for nonexistent type returns core properties."""
        settings = load_settings(tmp_path, create_if_missing=True)
        props = get_all_properties_for_type(settings, "nonexistent")
        assert props == settings.core_properties


class TestInferNoteTypeFromPath:
    """Tests for infer_note_type_from_path function."""

    def test_infer_map_type(self, tmp_path: Path) -> None:
        """Test inferring map type from path."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Atlas/Maps/Index.md")
        note_type = infer_note_type_from_path(settings, file_path)
        assert note_type == "map"

    def test_infer_dot_type(self, tmp_path: Path) -> None:
        """Test inferring dot type from path."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Atlas/Dots/Concept.md")
        note_type = infer_note_type_from_path(settings, file_path)
        assert note_type == "dot"

    def test_infer_no_match(self, tmp_path: Path) -> None:
        """Test that None is returned when no type matches."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Random/Note.md")
        note_type = infer_note_type_from_path(settings, file_path)
        assert note_type is None


class TestGetUpLinkForPath:
    """Tests for get_up_link_for_path function."""

    def test_get_up_link_for_dots(self, tmp_path: Path) -> None:
        """Test getting up link for dots folder."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Atlas/Dots/Concept.md")
        up_link = get_up_link_for_path(settings, file_path)
        assert up_link == "[[Atlas/Maps/Dots]]"

    def test_get_up_link_for_unknown(self, tmp_path: Path) -> None:
        """Test that None is returned for unknown path."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Random/Note.md")
        up_link = get_up_link_for_path(settings, file_path)
        assert up_link is None


class TestShouldExclude:
    """Tests for should_exclude function."""

    def test_exclude_inbox(self, tmp_path: Path) -> None:
        """Test that inbox files are excluded."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/+/new_note.md")
        assert should_exclude(settings, file_path) is True

    def test_exclude_obsidian(self, tmp_path: Path) -> None:
        """Test that .obsidian files are excluded."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/.obsidian/config.json")
        assert should_exclude(settings, file_path) is True

    def test_exclude_specific_file(self, tmp_path: Path) -> None:
        """Test that specific files are excluded."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Home.md")
        assert should_exclude(settings, file_path) is True

    def test_not_exclude_regular(self, tmp_path: Path) -> None:
        """Test that regular files are not excluded."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Atlas/Dots/Concept.md")
        assert should_exclude(settings, file_path) is False


class TestIsInboxPath:
    """Tests for is_inbox_path function."""

    def test_inbox_path(self, tmp_path: Path) -> None:
        """Test that inbox path is detected."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/+/new_idea.md")
        assert is_inbox_path(settings, file_path) is True

    def test_not_inbox_path(self, tmp_path: Path) -> None:
        """Test that non-inbox path is not detected as inbox."""
        settings = load_settings(tmp_path, create_if_missing=True)
        file_path = Path("/vault/Atlas/Dots/Concept.md")
        assert is_inbox_path(settings, file_path) is False


class TestValidateSettings:
    """Tests for validate_settings function."""

    def test_validate_valid_settings(self, tmp_path: Path) -> None:
        """Test validating valid settings."""
        settings = load_settings(tmp_path, create_if_missing=True)
        errors = validate_settings(settings)
        assert errors == []

    def test_validate_missing_version(self, tmp_path: Path) -> None:
        """Test validating settings with missing version."""
        settings = Settings(
            version="",
            methodology="custom",
            core_properties=["type"],
            note_types={},
            validation=ValidationRules(),
            folder_structure={},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        assert "Missing 'version'" in errors[0]

    def test_validate_empty_core_properties(self, tmp_path: Path) -> None:
        """Test validating settings with empty core properties."""
        settings = Settings(
            version="1.0",
            methodology="custom",
            core_properties=[],
            note_types={},
            validation=ValidationRules(),
            folder_structure={},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            formats={},
            logging={},
            raw={},
        )
        errors = validate_settings(settings)
        assert any("core_properties" in e for e in errors)


class TestSettingsExist:
    """Tests for settings_exist function."""

    def test_settings_exist_true(self, tmp_path: Path) -> None:
        """Test that settings_exist returns True when file exists."""
        create_default_settings(tmp_path)
        assert settings_exist(tmp_path) is True

    def test_settings_exist_false(self, tmp_path: Path) -> None:
        """Test that settings_exist returns False when file doesn't exist."""
        assert settings_exist(tmp_path) is False
