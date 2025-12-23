"""
Tests for config_loader.py

Comprehensive test suite with 90%+ coverage for configuration loading,
merging, validation, and vault-specific overrides.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

# Import the config_loader module
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "config" / "scripts"))
from config_loader import (
    DEFAULT_CONFIG,
    get_note_type_config,
    infer_note_type,
    load_config,
    merge_configs,
    save_config,
    validate_config,
)


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_with_nonexistent_vault(self, tmp_path: Path) -> None:
        """Test that load_config raises ValueError for nonexistent vault."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(ValueError, match="Vault path does not exist"):
            load_config(nonexistent)

    def test_load_config_with_file_not_directory(self, tmp_path: Path) -> None:
        """Test that load_config raises ValueError when vault path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="not a directory"):
            load_config(file_path)

    def test_load_config_returns_default_config(self, tmp_path: Path) -> None:
        """Test that load_config returns default config when no overrides exist."""
        config = load_config(tmp_path)
        assert "core_properties" in config
        assert "note_types" in config
        assert config["core_properties"] == DEFAULT_CONFIG["core_properties"]

    def test_load_config_with_vault_override(self, tmp_path: Path) -> None:
        """Test that vault-specific config overrides defaults."""
        # Create vault config directory
        vault_config_dir = tmp_path / ".claude" / "config"
        vault_config_dir.mkdir(parents=True)

        # Create override config
        override = {
            "core_properties": ["type", "created"],  # Override with fewer properties
            "custom_setting": "vault-specific",
        }
        config_file = vault_config_dir / "default.yaml"
        with config_file.open("w") as f:
            yaml.safe_dump(override, f)

        # Load config
        config = load_config(tmp_path)

        # Check overrides applied
        assert config["core_properties"] == ["type", "created"]
        assert config["custom_setting"] == "vault-specific"
        # Default note_types should still be present (merged)
        assert "note_types" in config

    def test_load_config_with_custom_name(self, tmp_path: Path) -> None:
        """Test loading config with custom filename."""
        vault_config_dir = tmp_path / ".claude" / "config"
        vault_config_dir.mkdir(parents=True)

        custom_config = {"custom_key": "custom_value"}
        config_file = vault_config_dir / "custom.yaml"
        with config_file.open("w") as f:
            yaml.safe_dump(custom_config, f)

        config = load_config(tmp_path, "custom.yaml")
        assert config["custom_key"] == "custom_value"

    def test_load_config_with_invalid_yaml(self, tmp_path: Path, capsys) -> None:
        """Test that invalid YAML in vault config prints warning but doesn't crash."""
        vault_config_dir = tmp_path / ".claude" / "config"
        vault_config_dir.mkdir(parents=True)

        config_file = vault_config_dir / "default.yaml"
        config_file.write_text("invalid: yaml: content: [")

        # Should not raise, just warn
        config = load_config(tmp_path)
        captured = capsys.readouterr()
        assert "Warning" in captured.err or "warning" in captured.err.lower()
        # Should still return default config
        assert "core_properties" in config


class TestSaveConfig:
    """Test save_config function."""

    def test_save_config_creates_directory(self, tmp_path: Path) -> None:
        """Test that save_config creates .claude/config directory."""
        config = {"test_key": "test_value"}
        save_config(tmp_path, config, "test.yaml")

        config_file = tmp_path / ".claude" / "config" / "test.yaml"
        assert config_file.exists()

        # Verify content
        with config_file.open() as f:
            loaded = yaml.safe_load(f)
        assert loaded["test_key"] == "test_value"

    def test_save_config_with_nonexistent_vault(self, tmp_path: Path) -> None:
        """Test that save_config raises ValueError for nonexistent vault."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(ValueError, match="Vault path does not exist"):
            save_config(nonexistent, {}, "test.yaml")

    def test_save_config_with_file_not_directory(self, tmp_path: Path) -> None:
        """Test that save_config raises ValueError when vault is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="not a directory"):
            save_config(file_path, {}, "test.yaml")

    def test_save_config_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that save_config overwrites existing config file."""
        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "test.yaml"
        config_file.write_text("old: value")

        new_config = {"new": "value"}
        save_config(tmp_path, new_config, "test.yaml")

        with config_file.open() as f:
            loaded = yaml.safe_load(f)
        assert loaded == {"new": "value"}
        assert "old" not in loaded


class TestMergeConfigs:
    """Test merge_configs function."""

    def test_merge_configs_simple_merge(self) -> None:
        """Test simple key-value merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge_configs(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_configs_nested_dicts(self) -> None:
        """Test that nested dictionaries are merged recursively."""
        base = {"level1": {"level2": {"a": 1, "b": 2}}}
        override = {"level1": {"level2": {"b": 3, "c": 4}}}
        result = merge_configs(base, override)

        expected = {"level1": {"level2": {"a": 1, "b": 3, "c": 4}}}
        assert result == expected

    def test_merge_configs_lists_replace(self) -> None:
        """Test that lists are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = merge_configs(base, override)

        assert result["items"] == [4, 5]

    def test_merge_configs_mixed_types(self) -> None:
        """Test merging with different value types."""
        base = {"a": [1, 2], "b": {"nested": "value"}}
        override = {"a": "string", "b": [1, 2, 3]}
        result = merge_configs(base, override)

        assert result["a"] == "string"
        assert result["b"] == [1, 2, 3]

    def test_merge_configs_empty_dicts(self) -> None:
        """Test merging with empty dictionaries."""
        base = {"a": 1}
        override = {}
        result = merge_configs(base, override)
        assert result == {"a": 1}

        base = {}
        override = {"a": 1}
        result = merge_configs(base, override)
        assert result == {"a": 1}

    def test_merge_configs_deep_nesting(self) -> None:
        """Test merging deeply nested structures."""
        base = {"l1": {"l2": {"l3": {"l4": {"value": "base"}}}}}
        override = {"l1": {"l2": {"l3": {"l4": {"value": "override", "new": "field"}}}}}
        result = merge_configs(base, override)
        assert result["l1"]["l2"]["l3"]["l4"]["value"] == "override"
        assert result["l1"]["l2"]["l3"]["l4"]["new"] == "field"


class TestGetNoteTypeConfig:
    """Test get_note_type_config function."""

    def test_get_note_type_config_existing_type(self) -> None:
        """Test getting config for existing note type."""
        config = DEFAULT_CONFIG.copy()
        map_config = get_note_type_config(config, "map")

        assert map_config is not None
        assert map_config["description"] == "Map of Content - Overview and navigation notes"
        assert "properties" in map_config

    def test_get_note_type_config_nonexistent_type(self) -> None:
        """Test getting config for nonexistent note type."""
        config = DEFAULT_CONFIG.copy()
        result = get_note_type_config(config, "nonexistent")
        assert result is None

    def test_get_note_type_config_empty_config(self) -> None:
        """Test getting note type from empty config."""
        config = {}
        result = get_note_type_config(config, "map")
        assert result is None

    def test_get_note_type_config_all_default_types(self) -> None:
        """Test that all default note types are accessible."""
        config = DEFAULT_CONFIG.copy()
        expected_types = ["map", "dot", "source", "effort", "project", "area", "daily"]

        for note_type in expected_types:
            result = get_note_type_config(config, note_type)
            assert result is not None
            assert "description" in result
            assert "properties" in result


class TestInferNoteType:
    """Test infer_note_type function."""

    def test_infer_note_type_from_map_folder(self, tmp_path: Path) -> None:
        """Test inferring map type from folder path."""
        config = DEFAULT_CONFIG.copy()
        file_path = tmp_path / "Atlas" / "Maps" / "My Map.md"

        note_type = infer_note_type(file_path, config)
        assert note_type == "map"

    def test_infer_note_type_from_dot_folder(self, tmp_path: Path) -> None:
        """Test inferring dot type from folder path."""
        config = DEFAULT_CONFIG.copy()
        file_path = tmp_path / "Atlas" / "Dots" / "Concept.md"

        note_type = infer_note_type(file_path, config)
        assert note_type == "dot"

    def test_infer_note_type_from_project_folder(self, tmp_path: Path) -> None:
        """Test inferring project type from folder path."""
        config = DEFAULT_CONFIG.copy()
        file_path = tmp_path / "Efforts" / "Projects" / "New Project.md"

        note_type = infer_note_type(file_path, config)
        assert note_type == "project"

    def test_infer_note_type_no_match(self, tmp_path: Path) -> None:
        """Test that None is returned when no folder hint matches."""
        config = DEFAULT_CONFIG.copy()
        file_path = tmp_path / "Random" / "Folder" / "File.md"

        note_type = infer_note_type(file_path, config)
        assert note_type is None

    def test_infer_note_type_multiple_hints(self, tmp_path: Path) -> None:
        """Test that first matching hint is used."""
        config = {
            "note_types": {
                "type1": {"folder_hints": ["FolderA/"]},
                "type2": {"folder_hints": ["FolderB/", "FolderA/"]},
            }
        }
        file_path = tmp_path / "FolderA" / "File.md"

        note_type = infer_note_type(file_path, config)
        assert note_type == "type1"  # First match wins

    def test_infer_note_type_empty_config(self, tmp_path: Path) -> None:
        """Test inference with empty config."""
        config = {}
        file_path = tmp_path / "Some" / "Path" / "File.md"

        note_type = infer_note_type(file_path, config)
        assert note_type is None


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_valid_default(self) -> None:
        """Test that default config is valid."""
        errors = validate_config(DEFAULT_CONFIG)
        assert len(errors) == 0

    def test_validate_config_missing_core_properties(self) -> None:
        """Test validation fails when core_properties is missing."""
        config = {"note_types": {}}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("core_properties" in error for error in errors)

    def test_validate_config_invalid_core_properties_type(self) -> None:
        """Test validation fails when core_properties is not a list."""
        config = {"core_properties": "not a list", "note_types": {}}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("must be a list" in error for error in errors)

    def test_validate_config_empty_core_properties(self) -> None:
        """Test validation fails when core_properties is empty."""
        config = {"core_properties": [], "note_types": {}}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("cannot be empty" in error for error in errors)

    def test_validate_config_missing_note_types(self) -> None:
        """Test validation fails when note_types is missing."""
        config = {"core_properties": ["type"]}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("note_types" in error for error in errors)

    def test_validate_config_invalid_note_types_type(self) -> None:
        """Test validation fails when note_types is not a dict."""
        config = {"core_properties": ["type"], "note_types": []}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("must be a dictionary" in error for error in errors)

    def test_validate_config_empty_note_types(self) -> None:
        """Test validation fails when note_types is empty."""
        config = {"core_properties": ["type"], "note_types": {}}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("cannot be empty" in error for error in errors)

    def test_validate_config_invalid_note_type_structure(self) -> None:
        """Test validation fails when note type is not a dict."""
        config = {"core_properties": ["type"], "note_types": {"map": "not a dict"}}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("must be a dictionary" in error for error in errors)

    def test_validate_config_missing_properties_in_note_type(self) -> None:
        """Test validation fails when note type missing properties."""
        config = {
            "core_properties": ["type"],
            "note_types": {
                "map": {"description": "test"}  # Missing 'properties'
            },
        }
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("missing 'properties'" in error for error in errors)

    def test_validate_config_invalid_properties_type(self) -> None:
        """Test validation fails when properties is not a list."""
        config = {"core_properties": ["type"], "note_types": {"map": {"properties": "not a list"}}}
        errors = validate_config(config)

        assert len(errors) > 0
        assert any("'properties' must be a list" in error for error in errors)

    def test_validate_config_multiple_errors(self) -> None:
        """Test that multiple validation errors are returned."""
        config = {
            "core_properties": [],  # Empty
            "note_types": {
                "map": "not a dict",  # Invalid structure
                "dot": {"description": "test"},  # Missing properties
            },
        }
        errors = validate_config(config)

        assert len(errors) >= 3  # At least 3 different errors


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_config_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow: load, modify, save, reload."""
        # 1. Load default config
        config = load_config(tmp_path)
        assert "core_properties" in config

        # 2. Modify config
        config["custom_field"] = "custom_value"
        config["core_properties"] = ["type", "created"]

        # 3. Save modified config
        save_config(tmp_path, config, "custom.yaml")

        # 4. Reload custom config
        reloaded = load_config(tmp_path, "custom.yaml")
        assert reloaded["custom_field"] == "custom_value"
        assert reloaded["core_properties"] == ["type", "created"]

    def test_hierarchical_config_merge(self, tmp_path: Path) -> None:
        """Test that vault config properly overrides defaults."""
        # Create vault override
        vault_config_dir = tmp_path / ".claude" / "config"
        vault_config_dir.mkdir(parents=True)

        override = {
            "note_types": {
                "custom": {
                    "description": "Custom type",
                    "folder_hints": ["Custom/"],
                    "properties": ["type", "up"],
                }
            }
        }
        config_file = vault_config_dir / "default.yaml"
        with config_file.open("w") as f:
            yaml.safe_dump(override, f)

        # Load config
        config = load_config(tmp_path)

        # Should have both default and custom note types
        assert "map" in config["note_types"]  # From defaults
        assert "custom" in config["note_types"]  # From override

        # Test custom type
        custom_config = get_note_type_config(config, "custom")
        assert custom_config is not None
        assert custom_config["description"] == "Custom type"

    def test_infer_and_validate_workflow(self, tmp_path: Path) -> None:
        """Test workflow of inferring type and validating config."""
        # Load config
        config = load_config(tmp_path)

        # Validate it
        errors = validate_config(config)
        assert len(errors) == 0

        # Infer type from path
        file_path = tmp_path / "Atlas" / "Maps" / "Test.md"
        note_type = infer_note_type(file_path, config)
        assert note_type == "map"

        # Get type config
        type_config = get_note_type_config(config, note_type)
        assert type_config is not None
        assert "properties" in type_config
