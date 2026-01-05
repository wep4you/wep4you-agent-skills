"""
Comprehensive unit tests for skills/core/settings/loader.py.

Tests cover all public functions and internal helpers for loading,
saving, and managing settings from .claude/settings.yaml.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from skills.core.models.settings import Settings, ValidationRules
from skills.core.settings.loader import (
    SETTINGS_FILE,
    _diff_dicts,
    _parse_settings,
    create_backup,
    create_default_settings,
    diff_settings,
    get_backup_dir,
    get_default_settings_dict,
    load_settings,
    save_settings,
    set_setting,
    settings_exist,
)

# =============================================================================
# Test load_settings
# =============================================================================


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_settings_file_not_found(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised when settings don't exist."""
        with pytest.raises(FileNotFoundError, match="Settings file not found"):
            load_settings(tmp_path)

    def test_load_settings_file_not_found_message_contains_path(
        self, tmp_path: Path
    ) -> None:
        """Test that error message contains the expected path."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_settings(tmp_path)
        assert str(tmp_path / SETTINGS_FILE) in str(exc_info.value)

    def test_load_settings_creates_when_missing(self, tmp_path: Path) -> None:
        """Test that settings are created when create_if_missing=True."""
        settings = load_settings(tmp_path, create_if_missing=True)

        assert isinstance(settings, Settings)
        assert settings.version == "1.0"
        assert (tmp_path / ".claude" / "settings.yaml").exists()

    def test_load_settings_valid_file(self, tmp_path: Path) -> None:
        """Test loading a valid settings file."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        config = {
            "version": "2.0",
            "methodology": "zettelkasten",
            "core_properties": ["type", "up", "created", "tags"],
            "note_types": {},
            "validation": {"require_core_properties": False},
            "exclude": {"paths": [".git/"], "files": []},
        }

        with settings_file.open("w") as f:
            yaml.safe_dump(config, f)

        settings = load_settings(tmp_path)

        assert settings.version == "2.0"
        assert settings.methodology == "zettelkasten"
        assert settings.core_properties == ["type", "up", "created", "tags"]
        assert settings.validation.require_core_properties is False

    def test_load_settings_invalid_yaml(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for invalid YAML."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_settings(tmp_path)

    def test_load_settings_invalid_yaml_preserves_cause(self, tmp_path: Path) -> None:
        """Test that ValueError preserves the YAML error as cause."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError) as exc_info:
            load_settings(tmp_path)
        assert exc_info.value.__cause__ is not None

    def test_load_settings_empty_file(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for empty settings file."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("")

        with pytest.raises(ValueError, match="Empty settings file"):
            load_settings(tmp_path)

    def test_load_settings_yaml_null_only(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when YAML parses to null."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("null")

        with pytest.raises(ValueError, match="Empty settings file"):
            load_settings(tmp_path)

    def test_load_settings_vault_does_not_exist(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for nonexistent vault path."""
        with pytest.raises(ValueError, match="does not exist"):
            load_settings(tmp_path / "nonexistent")

    def test_load_settings_vault_is_file(self, tmp_path: Path) -> None:
        """Test that ValueError is raised when vault path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        with pytest.raises(ValueError, match="not a directory"):
            load_settings(file_path)


# =============================================================================
# Test _parse_settings
# =============================================================================


class TestParseSettings:
    """Tests for _parse_settings function."""

    def test_parse_settings_old_format_core_properties_list(self) -> None:
        """Test parsing old format where core_properties is a direct list."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {},
            "validation": {},
            "exclude": {},
        }

        settings = _parse_settings(raw)

        assert settings.core_properties == ["type", "up", "created"]

    def test_parse_settings_new_format_core_properties_dict(self) -> None:
        """Test parsing new format where core_properties is a dict with 'all' key."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": {
                "all": ["type", "up", "created", "daily"],
                "mandatory": ["type", "up"],
                "optional": ["daily"],
            },
            "note_types": {},
            "validation": {},
            "exclude": {},
        }

        settings = _parse_settings(raw)

        assert settings.core_properties == ["type", "up", "created", "daily"]

    def test_parse_settings_note_types_parsing(self) -> None:
        """Test that note types are parsed correctly."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up"],
            "note_types": {
                "map": {
                    "description": "Maps organize content",
                    "folder_hints": ["Atlas/Maps/"],
                    "properties": {
                        "additional_required": ["scope"],
                        "optional": ["aliases"],
                    },
                    "icon": "globe",
                },
                "dot": {
                    "description": "Atomic notes",
                    "folder_hints": ["Atlas/Dots/"],
                    "properties": {"required": ["type", "up"], "optional": []},
                },
            },
            "validation": {},
            "exclude": {},
        }

        settings = _parse_settings(raw)

        assert "map" in settings.note_types
        assert "dot" in settings.note_types
        assert settings.note_types["map"].description == "Maps organize content"
        assert settings.note_types["map"].folder_hints == ["Atlas/Maps/"]
        assert settings.note_types["map"].icon == "globe"

    def test_parse_settings_note_types_with_inheritance(self) -> None:
        """Test that note types correctly inherit core properties."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {
                "source": {
                    "description": "Source notes",
                    "folder_hints": ["Sources/"],
                    "inherit_core": True,
                    "properties": {
                        "additional_required": ["author", "url"],
                        "optional": ["published"],
                    },
                }
            },
            "validation": {},
            "exclude": {},
        }

        settings = _parse_settings(raw)
        source_type = settings.note_types["source"]

        # Should have core properties + additional_required
        assert "type" in source_type.required_properties
        assert "up" in source_type.required_properties
        assert "created" in source_type.required_properties
        assert "author" in source_type.required_properties
        assert "url" in source_type.required_properties
        assert "published" in source_type.optional_properties

    def test_parse_settings_note_types_no_inheritance(self) -> None:
        """Test that note types with inherit_core=False don't inherit."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {
                "custom": {
                    "description": "Custom type",
                    "folder_hints": ["Custom/"],
                    "inherit_core": False,
                    "properties": {"required": ["title", "status"], "optional": []},
                }
            },
            "validation": {},
            "exclude": {},
        }

        settings = _parse_settings(raw)
        custom_type = settings.note_types["custom"]

        # Should NOT have core properties
        assert "type" not in custom_type.required_properties
        assert "up" not in custom_type.required_properties
        assert "title" in custom_type.required_properties
        assert "status" in custom_type.required_properties

    def test_parse_settings_validation_rules(self) -> None:
        """Test that validation rules are parsed correctly."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": [],
            "note_types": {},
            "validation": {
                "require_core_properties": False,
                "allow_empty_properties": ["tags", "related"],
                "strict_types": False,
                "check_templates": True,
                "check_up_links": False,
                "check_inbox_no_frontmatter": True,
            },
            "exclude": {},
        }

        settings = _parse_settings(raw)

        assert settings.validation.require_core_properties is False
        assert settings.validation.allow_empty_properties == ["tags", "related"]
        assert settings.validation.strict_types is False
        assert settings.validation.check_templates is True
        assert settings.validation.check_up_links is False
        assert settings.validation.check_inbox_no_frontmatter is True

    def test_parse_settings_exclude_sections(self) -> None:
        """Test that exclude sections are parsed correctly."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": [],
            "note_types": {},
            "validation": {},
            "exclude": {
                "paths": ["+/", "x/", ".obsidian/"],
                "files": ["Home.md", "README.md"],
                "patterns": ["*_MOC.md", "*.excalidraw.md"],
            },
        }

        settings = _parse_settings(raw)

        assert settings.exclude_paths == ["+/", "x/", ".obsidian/"]
        assert settings.exclude_files == ["Home.md", "README.md"]
        assert settings.exclude_patterns == ["*_MOC.md", "*.excalidraw.md"]

    def test_parse_settings_preserves_raw(self) -> None:
        """Test that raw dict is preserved in settings."""
        raw = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": [],
            "note_types": {},
            "validation": {},
            "exclude": {},
            "custom_field": "custom_value",
        }

        settings = _parse_settings(raw)

        assert settings.raw == raw
        assert settings.raw["custom_field"] == "custom_value"

    def test_parse_settings_defaults_for_missing_fields(self) -> None:
        """Test that missing fields get default values."""
        raw = {"version": "1.0"}

        settings = _parse_settings(raw)

        assert settings.methodology == "custom"
        assert settings.core_properties == []
        assert settings.note_types == {}
        assert settings.exclude_paths == []
        assert settings.exclude_files == []
        assert settings.exclude_patterns == []
        assert settings.folder_structure == {}
        assert settings.up_links == {}
        assert settings.formats == {}
        assert settings.logging == {}


# =============================================================================
# Test save_settings
# =============================================================================


class TestSaveSettings:
    """Tests for save_settings function."""

    def test_save_settings_creates_directories(self, tmp_path: Path) -> None:
        """Test that save_settings creates .claude directory if missing."""
        settings = Settings(
            version="1.0",
            methodology="custom",
            core_properties=["type"],
            note_types={},
            validation=ValidationRules(),
            folder_structure={},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw={"version": "1.0", "methodology": "custom"},
        )

        assert not (tmp_path / ".claude").exists()

        result = save_settings(tmp_path, settings)

        assert (tmp_path / ".claude").exists()
        assert result.exists()

    def test_save_settings_writes_yaml(self, tmp_path: Path) -> None:
        """Test that save_settings writes valid YAML content."""
        raw = {
            "version": "2.0",
            "methodology": "para",
            "core_properties": ["type", "up"],
        }
        settings = Settings(
            version="2.0",
            methodology="para",
            core_properties=["type", "up"],
            note_types={},
            validation=ValidationRules(),
            folder_structure={},
            up_links={},
            exclude_paths=[],
            exclude_files=[],
            exclude_patterns=[],
            formats={},
            logging={},
            raw=raw,
        )

        result = save_settings(tmp_path, settings)

        with result.open() as f:
            loaded = yaml.safe_load(f)

        assert loaded["version"] == "2.0"
        assert loaded["methodology"] == "para"
        assert loaded["core_properties"] == ["type", "up"]

    def test_save_settings_returns_path(self, tmp_path: Path) -> None:
        """Test that save_settings returns the correct path."""
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
            exclude_patterns=[],
            formats={},
            logging={},
            raw={},
        )

        result = save_settings(tmp_path, settings)

        assert result == tmp_path / ".claude" / "settings.yaml"

    def test_save_settings_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that save_settings overwrites existing file."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("old_content: true")

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
            exclude_patterns=[],
            formats={},
            logging={},
            raw={"new_content": True},
        )

        save_settings(tmp_path, settings)

        with settings_file.open() as f:
            loaded = yaml.safe_load(f)

        assert "old_content" not in loaded
        assert loaded.get("new_content") is True


# =============================================================================
# Test create_default_settings
# =============================================================================


class TestCreateDefaultSettings:
    """Tests for create_default_settings function."""

    def test_create_default_settings_creates_file(self, tmp_path: Path) -> None:
        """Test that default settings file is created."""
        result = create_default_settings(tmp_path)

        assert result.exists()
        assert result == tmp_path / ".claude" / "settings.yaml"

    def test_create_default_settings_creates_logs_dir(self, tmp_path: Path) -> None:
        """Test that logs directory is created."""
        create_default_settings(tmp_path)

        assert (tmp_path / ".claude" / "logs").exists()
        assert (tmp_path / ".claude" / "logs").is_dir()

    def test_create_default_settings_default_methodology(self, tmp_path: Path) -> None:
        """Test that default methodology is lyt-ace."""
        create_default_settings(tmp_path)

        settings = load_settings(tmp_path)
        assert settings.methodology == "lyt-ace"

    def test_create_default_settings_custom_methodology(self, tmp_path: Path) -> None:
        """Test creating settings with custom methodology."""
        create_default_settings(tmp_path, methodology="para")

        settings = load_settings(tmp_path)
        assert settings.methodology == "para"

    def test_create_default_settings_fallback_when_no_template(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test fallback behavior when template file doesn't exist."""
        import skills.core.settings.loader as loader

        fake_template = tmp_path / "nonexistent_template.yaml"
        monkeypatch.setattr(loader, "TEMPLATE_FILE", fake_template)

        settings_path = create_default_settings(tmp_path, methodology="zettelkasten")

        assert settings_path.exists()
        settings = load_settings(tmp_path)
        assert settings.methodology == "zettelkasten"
        assert "type" in settings.core_properties

    def test_create_default_settings_fallback_has_minimal_structure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that fallback creates minimal but valid structure."""
        import skills.core.settings.loader as loader

        fake_template = tmp_path / "nonexistent.yaml"
        monkeypatch.setattr(loader, "TEMPLATE_FILE", fake_template)

        create_default_settings(tmp_path)

        with (tmp_path / ".claude" / "settings.yaml").open() as f:
            config = yaml.safe_load(f)

        assert "version" in config
        assert "methodology" in config
        assert "core_properties" in config
        assert "validation" in config
        assert "exclude" in config


# =============================================================================
# Test settings_exist
# =============================================================================


class TestSettingsExist:
    """Tests for settings_exist function."""

    def test_settings_exist_true(self, tmp_path: Path) -> None:
        """Test that settings_exist returns True when file exists."""
        create_default_settings(tmp_path)

        assert settings_exist(tmp_path) is True

    def test_settings_exist_false_empty_vault(self, tmp_path: Path) -> None:
        """Test that settings_exist returns False when file doesn't exist."""
        assert settings_exist(tmp_path) is False

    def test_settings_exist_false_partial_path(self, tmp_path: Path) -> None:
        """Test settings_exist returns False when only .claude dir exists."""
        (tmp_path / ".claude").mkdir()

        assert settings_exist(tmp_path) is False


# =============================================================================
# Test get_backup_dir
# =============================================================================


class TestGetBackupDir:
    """Tests for get_backup_dir function."""

    def test_get_backup_dir_returns_correct_path(self, tmp_path: Path) -> None:
        """Test that correct backup directory path is returned."""
        result = get_backup_dir(tmp_path)

        assert result == tmp_path / ".claude" / "backups"

    def test_get_backup_dir_does_not_create_dir(self, tmp_path: Path) -> None:
        """Test that get_backup_dir doesn't create the directory."""
        result = get_backup_dir(tmp_path)

        assert not result.exists()


# =============================================================================
# Test create_backup
# =============================================================================


class TestCreateBackup:
    """Tests for create_backup function."""

    def test_create_backup_returns_none_when_no_settings(
        self, tmp_path: Path
    ) -> None:
        """Test that None is returned when no settings exist."""
        result = create_backup(tmp_path)

        assert result is None

    def test_create_backup_creates_backup_file(self, tmp_path: Path) -> None:
        """Test that backup file is created."""
        create_default_settings(tmp_path)

        result = create_backup(tmp_path)

        assert result is not None
        assert result.exists()

    def test_create_backup_creates_backup_dir(self, tmp_path: Path) -> None:
        """Test that backup directory is created if missing."""
        create_default_settings(tmp_path)
        backup_dir = tmp_path / ".claude" / "backups"

        assert not backup_dir.exists()

        create_backup(tmp_path)

        assert backup_dir.exists()

    def test_create_backup_filename_has_timestamp(self, tmp_path: Path) -> None:
        """Test that backup filename contains timestamp."""
        create_default_settings(tmp_path)

        result = create_backup(tmp_path)

        assert result is not None
        # Filename pattern: settings_YYYYMMDD_HHMMSS.yaml
        pattern = r"settings_\d{8}_\d{6}\.yaml"
        assert re.match(pattern, result.name)

    def test_create_backup_in_correct_location(self, tmp_path: Path) -> None:
        """Test that backup is created in .claude/backups."""
        create_default_settings(tmp_path)

        result = create_backup(tmp_path)

        assert result is not None
        assert result.parent == tmp_path / ".claude" / "backups"

    def test_create_backup_content_matches_original(self, tmp_path: Path) -> None:
        """Test that backup content matches original settings."""
        create_default_settings(tmp_path)
        original_path = tmp_path / ".claude" / "settings.yaml"
        original_content = original_path.read_text()

        result = create_backup(tmp_path)

        assert result is not None
        backup_content = result.read_text()
        assert backup_content == original_content


# =============================================================================
# Test set_setting
# =============================================================================


class TestSetSetting:
    """Tests for set_setting function."""

    def test_set_setting_string_value(self, tmp_path: Path) -> None:
        """Test setting a string value."""
        create_default_settings(tmp_path)

        set_setting(tmp_path, "methodology", "para", create_backup_file=False)

        settings = load_settings(tmp_path)
        assert settings.methodology == "para"

    def test_set_setting_boolean_true(self, tmp_path: Path) -> None:
        """Test setting a boolean true value."""
        create_default_settings(tmp_path)

        set_setting(
            tmp_path, "validation.strict_types", "true", create_backup_file=False
        )

        settings = load_settings(tmp_path)
        assert settings.validation.strict_types is True

    def test_set_setting_boolean_false(self, tmp_path: Path) -> None:
        """Test setting a boolean false value."""
        create_default_settings(tmp_path)

        set_setting(
            tmp_path, "validation.strict_types", "false", create_backup_file=False
        )

        settings = load_settings(tmp_path)
        assert settings.validation.strict_types is False

    def test_set_setting_boolean_case_insensitive(self, tmp_path: Path) -> None:
        """Test that boolean parsing is case insensitive."""
        create_default_settings(tmp_path)

        set_setting(
            tmp_path, "validation.check_templates", "FALSE", create_backup_file=False
        )

        settings = load_settings(tmp_path)
        assert settings.validation.check_templates is False

    def test_set_setting_integer_value(self, tmp_path: Path) -> None:
        """Test setting an integer value."""
        create_default_settings(tmp_path)

        set_setting(tmp_path, "logging.max_files", "10", create_backup_file=False)

        with (tmp_path / ".claude" / "settings.yaml").open() as f:
            config = yaml.safe_load(f)

        assert config["logging"]["max_files"] == 10
        assert isinstance(config["logging"]["max_files"], int)

    def test_set_setting_list_value(self, tmp_path: Path) -> None:
        """Test setting a list value."""
        create_default_settings(tmp_path)

        set_setting(
            tmp_path,
            "exclude.files",
            "[README.md, CHANGELOG.md, LICENSE]",
            create_backup_file=False,
        )

        with (tmp_path / ".claude" / "settings.yaml").open() as f:
            config = yaml.safe_load(f)

        assert config["exclude"]["files"] == ["README.md", "CHANGELOG.md", "LICENSE"]

    def test_set_setting_list_with_quotes(self, tmp_path: Path) -> None:
        """Test setting a list value with quoted items."""
        create_default_settings(tmp_path)

        set_setting(
            tmp_path,
            "core_properties",
            "['type', 'up', 'created']",
            create_backup_file=False,
        )

        with (tmp_path / ".claude" / "settings.yaml").open() as f:
            config = yaml.safe_load(f)

        assert config["core_properties"] == ["type", "up", "created"]

    def test_set_setting_nested_key(self, tmp_path: Path) -> None:
        """Test setting a nested key value."""
        create_default_settings(tmp_path)

        set_setting(
            tmp_path, "validation.check_up_links", "false", create_backup_file=False
        )

        settings = load_settings(tmp_path)
        assert settings.validation.check_up_links is False

    def test_set_setting_creates_nested_dict(self, tmp_path: Path) -> None:
        """Test that nested dicts are created if they don't exist."""
        create_default_settings(tmp_path)

        set_setting(
            tmp_path, "custom.nested.deeply.value", "test", create_backup_file=False
        )

        with (tmp_path / ".claude" / "settings.yaml").open() as f:
            config = yaml.safe_load(f)

        assert config["custom"]["nested"]["deeply"]["value"] == "test"

    def test_set_setting_creates_backup_by_default(self, tmp_path: Path) -> None:
        """Test that backup is created by default."""
        create_default_settings(tmp_path)
        backup_dir = tmp_path / ".claude" / "backups"

        assert not backup_dir.exists()

        set_setting(tmp_path, "methodology", "para")

        assert backup_dir.exists()
        backups = list(backup_dir.glob("settings_*.yaml"))
        assert len(backups) == 1

    def test_set_setting_no_backup_when_disabled(self, tmp_path: Path) -> None:
        """Test that no backup is created when disabled."""
        create_default_settings(tmp_path)
        backup_dir = tmp_path / ".claude" / "backups"

        set_setting(tmp_path, "methodology", "para", create_backup_file=False)

        assert not backup_dir.exists()

    def test_set_setting_file_not_found(self, tmp_path: Path) -> None:
        """Test that FileNotFoundError is raised when no settings exist."""
        with pytest.raises(FileNotFoundError):
            set_setting(tmp_path, "methodology", "para")

    def test_set_setting_invalid_nested_path(self, tmp_path: Path) -> None:
        """Test that ValueError is raised for invalid nested key path."""
        create_default_settings(tmp_path)

        # Set a string value first
        set_setting(tmp_path, "methodology", "para", create_backup_file=False)

        # Try to set a nested key under the string value
        with pytest.raises(ValueError, match="not a dict"):
            set_setting(
                tmp_path, "methodology.nested", "value", create_backup_file=False
            )


# =============================================================================
# Test get_default_settings_dict
# =============================================================================


class TestGetDefaultSettingsDict:
    """Tests for get_default_settings_dict function."""

    def test_get_default_settings_dict_returns_dict(self) -> None:
        """Test that function returns a dictionary."""
        result = get_default_settings_dict()

        assert isinstance(result, dict)

    def test_get_default_settings_dict_has_version(self) -> None:
        """Test that defaults include version."""
        result = get_default_settings_dict()

        assert result["version"] == "1.0"

    def test_get_default_settings_dict_has_methodology(self) -> None:
        """Test that defaults include methodology."""
        result = get_default_settings_dict()

        assert result["methodology"] == "custom"

    def test_get_default_settings_dict_has_core_properties(self) -> None:
        """Test that defaults include core properties."""
        result = get_default_settings_dict()

        assert "core_properties" in result
        assert "type" in result["core_properties"]
        assert "up" in result["core_properties"]
        assert "created" in result["core_properties"]

    def test_get_default_settings_dict_has_validation(self) -> None:
        """Test that defaults include validation section."""
        result = get_default_settings_dict()

        assert "validation" in result
        assert result["validation"]["require_core_properties"] is True
        assert "allow_empty_properties" in result["validation"]

    def test_get_default_settings_dict_has_exclude(self) -> None:
        """Test that defaults include exclude section."""
        result = get_default_settings_dict()

        assert "exclude" in result
        assert "paths" in result["exclude"]
        assert "files" in result["exclude"]
        assert "patterns" in result["exclude"]


# =============================================================================
# Test diff_settings
# =============================================================================


class TestDiffSettings:
    """Tests for diff_settings function."""

    def test_diff_settings_no_file_exists(self, tmp_path: Path) -> None:
        """Test diff when settings file doesn't exist."""
        result = diff_settings(tmp_path)

        assert len(result) == 1
        assert "does not exist" in result[0]

    def test_diff_settings_detects_added_values(self, tmp_path: Path) -> None:
        """Test that added values are detected."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        # Create settings with extra field not in defaults
        defaults = get_default_settings_dict()
        defaults["custom_field"] = "custom_value"
        with settings_file.open("w") as f:
            yaml.safe_dump(defaults, f)

        result = diff_settings(tmp_path)

        changes_str = "\n".join(result)
        assert "ADDED" in changes_str
        assert "custom_field" in changes_str

    def test_diff_settings_detects_removed_values(self, tmp_path: Path) -> None:
        """Test that removed values are detected."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        # Create settings missing a field from defaults
        config = {"version": "1.0", "methodology": "custom"}
        with settings_file.open("w") as f:
            yaml.safe_dump(config, f)

        result = diff_settings(tmp_path)

        changes_str = "\n".join(result)
        assert "REMOVED" in changes_str

    def test_diff_settings_detects_changed_values(self, tmp_path: Path) -> None:
        """Test that changed values are detected."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        # Create settings with different methodology
        defaults = get_default_settings_dict()
        defaults["methodology"] = "para"
        with settings_file.open("w") as f:
            yaml.safe_dump(defaults, f)

        result = diff_settings(tmp_path)

        changes_str = "\n".join(result)
        # Changed value indicator
        assert "methodology" in changes_str

    def test_diff_settings_no_changes(self, tmp_path: Path) -> None:
        """Test when current settings match defaults exactly."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        defaults = get_default_settings_dict()
        with settings_file.open("w") as f:
            yaml.safe_dump(defaults, f)

        result = diff_settings(tmp_path)

        assert result == []


# =============================================================================
# Test _diff_dicts
# =============================================================================


class TestDiffDicts:
    """Tests for _diff_dicts internal function."""

    def test_diff_dicts_added_key(self) -> None:
        """Test detection of added keys."""
        d1 = {"a": 1}
        d2 = {"a": 1, "b": 2}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "ADDED" in result[0]
        assert "b" in result[0]
        assert "2" in result[0]

    def test_diff_dicts_removed_key(self) -> None:
        """Test detection of removed keys."""
        d1 = {"a": 1, "b": 2}
        d2 = {"a": 1}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "REMOVED" in result[0]
        assert "b" in result[0]
        assert "2" in result[0]

    def test_diff_dicts_changed_value(self) -> None:
        """Test detection of changed values."""
        d1 = {"a": 1}
        d2 = {"a": 2}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "a" in result[0]
        # Arrow indicates change
        assert "1" in result[0]
        assert "2" in result[0]

    def test_diff_dicts_no_changes(self) -> None:
        """Test when dicts are identical."""
        d1 = {"a": 1, "b": 2}
        d2 = {"a": 1, "b": 2}

        result = _diff_dicts(d1, d2, "")

        assert result == []

    def test_diff_dicts_nested_changes(self) -> None:
        """Test detection of nested changes."""
        d1 = {"outer": {"inner": 1}}
        d2 = {"outer": {"inner": 2}}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "outer.inner" in result[0]

    def test_diff_dicts_nested_added(self) -> None:
        """Test detection of added nested keys."""
        d1 = {"outer": {"a": 1}}
        d2 = {"outer": {"a": 1, "b": 2}}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "outer.b" in result[0]
        assert "ADDED" in result[0]

    def test_diff_dicts_nested_removed(self) -> None:
        """Test detection of removed nested keys."""
        d1 = {"outer": {"a": 1, "b": 2}}
        d2 = {"outer": {"a": 1}}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "outer.b" in result[0]
        assert "REMOVED" in result[0]

    def test_diff_dicts_with_path_prefix(self) -> None:
        """Test that path prefix is included in output."""
        d1 = {"a": 1}
        d2 = {"a": 2}

        result = _diff_dicts(d1, d2, "root")

        assert "root.a" in result[0]

    def test_diff_dicts_multiple_changes(self) -> None:
        """Test detection of multiple simultaneous changes."""
        d1 = {"a": 1, "b": 2, "c": 3}
        d2 = {"a": 10, "c": 3, "d": 4}

        result = _diff_dicts(d1, d2, "")

        # a changed, b removed, d added
        assert len(result) == 3
        changes_str = "\n".join(result)
        assert "a" in changes_str
        assert "b" in changes_str
        assert "d" in changes_str

    def test_diff_dicts_deeply_nested(self) -> None:
        """Test handling of deeply nested structures."""
        d1 = {"l1": {"l2": {"l3": {"value": "old"}}}}
        d2 = {"l1": {"l2": {"l3": {"value": "new"}}}}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "l1.l2.l3.value" in result[0]

    def test_diff_dicts_type_change(self) -> None:
        """Test when value type changes (e.g., dict to string)."""
        d1 = {"a": {"nested": 1}}
        d2 = {"a": "string_now"}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "a" in result[0]

    def test_diff_dicts_empty_dicts(self) -> None:
        """Test comparison of empty dicts."""
        d1 = {}
        d2 = {}

        result = _diff_dicts(d1, d2, "")

        assert result == []

    def test_diff_dicts_list_values(self) -> None:
        """Test comparison of list values."""
        d1 = {"items": [1, 2, 3]}
        d2 = {"items": [1, 2, 3, 4]}

        result = _diff_dicts(d1, d2, "")

        assert len(result) == 1
        assert "items" in result[0]
