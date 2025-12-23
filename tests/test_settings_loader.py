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


class TestPropertyInheritance:
    """Tests for property inheritance (inherit_core field)."""

    def test_default_inherit_core_true(self, tmp_path: Path) -> None:
        """Test that note types inherit core_properties by default."""
        settings = load_settings(tmp_path, create_if_missing=True)
        # Default template has inherit_core: true (default)
        map_type = get_note_type(settings, "map")
        assert map_type is not None
        # Should have all core_properties
        for prop in settings.core_properties:
            assert prop in map_type.required_properties

    def test_additional_required_with_inheritance(self, tmp_path: Path) -> None:
        """Test that additional_required is added to core_properties."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        config = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {
                "source": {
                    "description": "Source notes",
                    "folder_hints": ["Sources/"],
                    # inherit_core: true is default
                    "properties": {
                        "additional_required": ["author", "url"],
                        "optional": ["published"],
                    },
                }
            },
        }

        with settings_file.open("w") as f:
            yaml.safe_dump(config, f)

        settings = load_settings(tmp_path)
        source_type = get_note_type(settings, "source")
        assert source_type is not None
        # Should have core + additional_required
        assert "type" in source_type.required_properties
        assert "up" in source_type.required_properties
        assert "created" in source_type.required_properties
        assert "author" in source_type.required_properties
        assert "url" in source_type.required_properties
        assert "published" in source_type.optional_properties

    def test_explicit_inherit_core_false(self, tmp_path: Path) -> None:
        """Test that inherit_core: false uses explicit required list only."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        config = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {
                "custom": {
                    "description": "Custom note type",
                    "folder_hints": ["Custom/"],
                    "inherit_core": False,  # Explicit no inheritance
                    "properties": {
                        "required": ["title", "status"],
                        "optional": [],
                    },
                }
            },
        }

        with settings_file.open("w") as f:
            yaml.safe_dump(config, f)

        settings = load_settings(tmp_path)
        custom_type = get_note_type(settings, "custom")
        assert custom_type is not None
        assert custom_type.inherit_core is False
        # Should NOT have core_properties
        assert "type" not in custom_type.required_properties
        assert "up" not in custom_type.required_properties
        # Should have explicit required only
        assert "title" in custom_type.required_properties
        assert "status" in custom_type.required_properties

    def test_backward_compat_explicit_required(self, tmp_path: Path) -> None:
        """Test backward compatibility with old 'required' format."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"

        config = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {
                "old_format": {
                    "description": "Old format note type",
                    "folder_hints": ["Old/"],
                    # Old format: explicit required list (no additional_required)
                    "properties": {
                        "required": ["type", "up", "custom_prop"],
                        "optional": [],
                    },
                }
            },
        }

        with settings_file.open("w") as f:
            yaml.safe_dump(config, f)

        settings = load_settings(tmp_path)
        old_type = get_note_type(settings, "old_format")
        assert old_type is not None
        # Should use explicit required as-is
        assert "type" in old_type.required_properties
        assert "up" in old_type.required_properties
        assert "custom_prop" in old_type.required_properties

    def test_validate_inheritance_missing_core(self, tmp_path: Path) -> None:
        """Test validation catches missing core properties with inherit_core=True."""
        from skills.config.scripts.settings_loader import NoteTypeConfig

        settings = Settings(
            version="1.0",
            methodology="custom",
            core_properties=["type", "up", "created"],
            note_types={
                "broken": NoteTypeConfig(
                    name="broken",
                    description="Broken type",
                    folder_hints=["Broken/"],
                    required_properties=["type"],  # Missing up, created
                    optional_properties=[],
                    validation={},
                    inherit_core=True,  # Claims to inherit but doesn't have all core
                )
            },
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
        assert any("missing core properties" in e for e in errors)


class TestSettingsLoaderCLI:
    """Tests for CLI main function."""

    def test_main_show(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --show option."""
        import sys

        from skills.config.scripts.settings_loader import main

        create_default_settings(tmp_path)
        old_argv = sys.argv
        try:
            sys.argv = ["settings_loader", "--vault", str(tmp_path), "--show"]
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "Version:" in captured.out
            assert "Methodology:" in captured.out
        finally:
            sys.argv = old_argv

    def test_main_validate(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --validate option."""
        import sys

        from skills.config.scripts.settings_loader import main

        create_default_settings(tmp_path)
        old_argv = sys.argv
        try:
            sys.argv = ["settings_loader", "--vault", str(tmp_path), "--validate"]
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "Settings are valid" in captured.out
        finally:
            sys.argv = old_argv

    def test_main_type(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --type option."""
        import sys

        from skills.config.scripts.settings_loader import main

        create_default_settings(tmp_path)
        old_argv = sys.argv
        try:
            sys.argv = ["settings_loader", "--vault", str(tmp_path), "--type", "map"]
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "Note type: map" in captured.out
            assert "Description:" in captured.out
        finally:
            sys.argv = old_argv

    def test_main_type_not_found(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --type option with nonexistent type."""
        import sys

        from skills.config.scripts.settings_loader import main

        create_default_settings(tmp_path)
        old_argv = sys.argv
        try:
            sys.argv = [
                "settings_loader",
                "--vault",
                str(tmp_path),
                "--type",
                "nonexistent",
            ]
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "not found" in captured.err
        finally:
            sys.argv = old_argv

    def test_main_create(self, tmp_path: Path) -> None:
        """Test --create option."""
        import sys

        from skills.config.scripts.settings_loader import main

        old_argv = sys.argv
        try:
            sys.argv = ["settings_loader", "--vault", str(tmp_path), "--create"]
            result = main()
            assert result == 0
            assert (tmp_path / ".claude" / "settings.yaml").exists()
        finally:
            sys.argv = old_argv

    def test_main_missing_settings(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test error when settings don't exist."""
        import sys

        from skills.config.scripts.settings_loader import main

        old_argv = sys.argv
        try:
            sys.argv = ["settings_loader", "--vault", str(tmp_path)]
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Error:" in captured.err
        finally:
            sys.argv = old_argv

    def test_main_reset_list(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --reset list option."""
        import sys

        from skills.config.scripts.settings_loader import main

        old_argv = sys.argv
        try:
            sys.argv = ["settings_loader", "--vault", str(tmp_path), "--reset", "list"]
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "Available methodologies" in captured.out
            assert "lyt-ace" in captured.out
            assert "para" in captured.out
        finally:
            sys.argv = old_argv

    def test_main_reset_invalid_methodology(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test --reset with invalid methodology."""
        import sys

        from skills.config.scripts.settings_loader import main

        old_argv = sys.argv
        try:
            sys.argv = [
                "settings_loader",
                "--vault",
                str(tmp_path),
                "--reset",
                "invalid",
            ]
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "Invalid methodology" in captured.out
        finally:
            sys.argv = old_argv

    def test_main_reset_with_yes(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --reset with --yes option."""
        import sys

        from skills.config.scripts.settings_loader import main

        # Create initial settings
        create_default_settings(tmp_path)

        old_argv = sys.argv
        try:
            sys.argv = [
                "settings_loader",
                "--vault",
                str(tmp_path),
                "--reset",
                "para",
                "--yes",
            ]
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "Created new settings" in captured.out
            # Verify methodology was changed
            settings = load_settings(tmp_path)
            assert settings.methodology == "para"
        finally:
            sys.argv = old_argv

    def test_main_reset_without_yes_non_interactive(
        self, tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test --reset without --yes in non-interactive mode."""
        import sys
        from io import StringIO

        from skills.config.scripts.settings_loader import main

        # Create initial settings
        create_default_settings(tmp_path)

        # Create a non-tty stdin
        fake_stdin = StringIO()
        monkeypatch.setattr(sys, "stdin", fake_stdin)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "settings_loader",
                "--vault",
                str(tmp_path),
                "--reset",
                "para",
            ],
        )

        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Cannot confirm interactively" in captured.out

    def test_main_reset_new_settings(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --reset creating new settings when none exist."""
        import sys

        from skills.config.scripts.settings_loader import main

        old_argv = sys.argv
        try:
            sys.argv = [
                "settings_loader",
                "--vault",
                str(tmp_path),
                "--reset",
                "zettelkasten",
            ]
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "Created new settings" in captured.out
            settings = load_settings(tmp_path)
            assert settings.methodology == "zettelkasten"
        finally:
            sys.argv = old_argv


class TestPrintResetHelp:
    """Tests for print_reset_help function."""

    def test_print_reset_help(self, capsys: pytest.CaptureFixture) -> None:
        """Test print_reset_help output."""
        from skills.config.scripts.settings_loader import print_reset_help

        print_reset_help()
        captured = capsys.readouterr()
        assert "Available methodologies" in captured.out
        assert "lyt-ace" in captured.out
        assert "para" in captured.out
        assert "zettelkasten" in captured.out
        assert "minimal" in captured.out
        assert "custom" in captured.out
        assert "Examples:" in captured.out
