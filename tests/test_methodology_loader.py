"""Tests for the methodology YAML loader."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Add repo root to path for imports
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config.methodologies.loader import (  # noqa: E402
    METHODOLOGIES,
    MethodologyNotFoundError,
    MethodologyParseError,
    clear_cache,
    get_methodology_names,
    load_all_methodologies,
    load_methodology,
    reload_methodology,
)


class TestGetMethodologyNames:
    """Tests for get_methodology_names()."""

    def test_returns_list(self):
        """Should return a list of methodology names."""
        names = get_methodology_names()
        assert isinstance(names, list)

    def test_contains_expected_methodologies(self):
        """Should contain the four standard methodologies."""
        names = get_methodology_names()
        assert "lyt-ace" in names
        assert "para" in names
        assert "zettelkasten" in names
        assert "minimal" in names

    def test_sorted_alphabetically(self):
        """Should return names in alphabetical order."""
        names = get_methodology_names()
        assert names == sorted(names)

    def test_excludes_readme(self):
        """Should not include README in the list."""
        names = get_methodology_names()
        assert "README" not in names


class TestLoadMethodology:
    """Tests for load_methodology()."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_load_lyt_ace(self):
        """Should load LYT-ACE methodology correctly."""
        method = load_methodology("lyt-ace")
        assert method["name"] == "LYT + ACE Framework"
        assert "folders" in method
        assert "core_properties" in method
        assert "note_types" in method

    def test_load_para(self):
        """Should load PARA methodology correctly."""
        method = load_methodology("para")
        assert method["name"] == "PARA Method"
        assert "Projects" in method["folders"]
        assert "project" in method["note_types"]

    def test_load_zettelkasten(self):
        """Should load Zettelkasten methodology correctly."""
        method = load_methodology("zettelkasten")
        assert method["name"] == "Zettelkasten"
        assert "Permanent" in method["folders"]
        assert "permanent" in method["note_types"]

    def test_load_minimal(self):
        """Should load Minimal methodology correctly."""
        method = load_methodology("minimal")
        assert method["name"] == "Minimal"
        assert "Notes" in method["folders"]
        assert "note" in method["note_types"]

    def test_not_found_raises_error(self):
        """Should raise MethodologyNotFoundError for unknown methodology."""
        with pytest.raises(MethodologyNotFoundError) as exc_info:
            load_methodology("nonexistent")
        assert "nonexistent" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_caching_works(self):
        """Should cache loaded methodologies."""
        clear_cache()
        method1 = load_methodology("para")
        method2 = load_methodology("para")
        assert method1 is method2  # Same object from cache

    def test_bypass_cache(self):
        """Should bypass cache when use_cache=False."""
        clear_cache()
        method1 = load_methodology("para")
        method2 = load_methodology("para", use_cache=False)
        assert method1 is not method2  # Different objects


class TestMethodologyStructure:
    """Tests for methodology structure validation."""

    @pytest.mark.parametrize("name", ["lyt-ace", "para", "zettelkasten", "minimal"])
    def test_has_required_fields(self, name):
        """All methodologies should have required top-level fields."""
        method = load_methodology(name)
        assert "name" in method
        assert "description" in method
        assert "folders" in method
        assert "core_properties" in method
        assert "note_types" in method
        assert "folder_structure" in method
        assert "up_links" in method

    @pytest.mark.parametrize("name", ["lyt-ace", "para", "zettelkasten", "minimal"])
    def test_folders_is_list(self, name):
        """Folders should be a list."""
        method = load_methodology(name)
        assert isinstance(method["folders"], list)
        assert len(method["folders"]) > 0

    @pytest.mark.parametrize("name", ["lyt-ace", "para", "zettelkasten", "minimal"])
    def test_core_properties_is_list(self, name):
        """Core properties should be a list."""
        method = load_methodology(name)
        assert isinstance(method["core_properties"], list)
        assert "type" in method["core_properties"]

    @pytest.mark.parametrize("name", ["lyt-ace", "para", "zettelkasten", "minimal"])
    def test_note_types_structure(self, name):
        """Note types should have correct structure."""
        method = load_methodology(name)
        for nt_name, nt_config in method["note_types"].items():
            assert "description" in nt_config, f"{name}.{nt_name} missing description"
            assert "folder_hints" in nt_config, f"{name}.{nt_name} missing folder_hints"
            assert "properties" in nt_config, f"{name}.{nt_name} missing properties"
            assert "validation" in nt_config, f"{name}.{nt_name} missing validation"
            assert "icon" in nt_config, f"{name}.{nt_name} missing icon"

            # Properties structure
            props = nt_config["properties"]
            assert "additional_required" in props
            assert "optional" in props


class TestMethodologiesProxy:
    """Tests for the METHODOLOGIES proxy object."""

    def test_getitem(self):
        """Should support dict-like access."""
        para = METHODOLOGIES["para"]
        assert para["name"] == "PARA Method"

    def test_contains(self):
        """Should support 'in' operator."""
        assert "para" in METHODOLOGIES
        assert "lyt-ace" in METHODOLOGIES
        assert "nonexistent" not in METHODOLOGIES

    def test_keys(self):
        """Should support keys() method."""
        keys = METHODOLOGIES.keys()
        assert "para" in keys
        assert "lyt-ace" in keys

    def test_iter(self):
        """Should be iterable."""
        names = list(METHODOLOGIES)
        assert "para" in names
        assert "lyt-ace" in names

    def test_get_existing(self):
        """Should support get() for existing key."""
        para = METHODOLOGIES.get("para")
        assert para is not None
        assert para["name"] == "PARA Method"

    def test_get_nonexistent(self):
        """Should return default for nonexistent key."""
        result = METHODOLOGIES.get("nonexistent", "default")
        assert result == "default"

    def test_get_nonexistent_none(self):
        """Should return None for nonexistent key without default."""
        result = METHODOLOGIES.get("nonexistent")
        assert result is None


class TestLoadAllMethodologies:
    """Tests for load_all_methodologies()."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        all_methods = load_all_methodologies()
        assert isinstance(all_methods, dict)

    def test_contains_all_methodologies(self):
        """Should contain all four methodologies."""
        all_methods = load_all_methodologies()
        assert "lyt-ace" in all_methods
        assert "para" in all_methods
        assert "zettelkasten" in all_methods
        assert "minimal" in all_methods

    def test_each_methodology_valid(self):
        """Each methodology should have valid structure."""
        all_methods = load_all_methodologies()
        for _name, method in all_methods.items():
            assert "name" in method
            assert "folders" in method
            assert "note_types" in method


class TestReloadMethodology:
    """Tests for reload_methodology()."""

    def test_reload_clears_cache(self):
        """Reload should return fresh data."""
        clear_cache()
        method1 = load_methodology("para")
        method2 = reload_methodology("para")
        # Should be different objects
        assert method1 is not method2

    def test_reload_without_cache(self):
        """Reload should work even if not cached."""
        clear_cache()
        # Reload without first loading (cache is empty)
        method = reload_methodology("para")
        assert method["name"] == "PARA Method"


class TestClearCache:
    """Tests for clear_cache()."""

    def test_cache_cleared(self):
        """Cache should be cleared."""
        load_methodology("para")
        clear_cache()
        # After clearing, next load should create new object
        method1 = load_methodology("para")
        clear_cache()
        method2 = load_methodology("para")
        assert method1 is not method2


class TestInvalidYaml:
    """Tests for handling invalid YAML files."""

    def test_missing_required_field(self):
        """Should raise error for YAML missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid YAML
            yaml_path = Path(tmpdir) / "invalid.yaml"
            yaml_path.write_text("name: Test\n")  # Missing other required fields

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("invalid")
                assert "missing required fields" in str(exc_info.value)

    def test_empty_yaml(self):
        """Should raise error for empty YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "empty.yaml"
            yaml_path.write_text("")

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("empty")
                assert "Empty YAML" in str(exc_info.value)

    def test_invalid_yaml_syntax(self):
        """Should raise error for invalid YAML syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "broken.yaml"
            yaml_path.write_text("name: [unclosed bracket")

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("broken")
                assert "Invalid YAML" in str(exc_info.value)


class TestNoteTypeValidation:
    """Tests for note type validation."""

    def test_missing_note_type_field(self):
        """Should raise error for note type missing required field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_data = {
                "name": "Test",
                "description": "Test",
                "folders": ["test"],
                "core_properties": ["type"],
                "note_types": {
                    "test": {
                        "description": "Test note",
                        # Missing folder_hints, properties, validation, icon
                    }
                },
            }
            yaml_path = Path(tmpdir) / "incomplete.yaml"
            with yaml_path.open("w") as f:
                yaml.dump(invalid_data, f)

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("incomplete")
                assert "missing" in str(exc_info.value).lower()

    def test_folders_not_list(self):
        """Should raise error if folders is not a list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_data = {
                "name": "Test",
                "description": "Test",
                "folders": "not-a-list",  # Should be a list
                "core_properties": ["type"],
                "note_types": {},
            }
            yaml_path = Path(tmpdir) / "badfolders.yaml"
            with yaml_path.open("w") as f:
                yaml.dump(invalid_data, f)

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("badfolders")
                assert "folders" in str(exc_info.value)
                assert "list" in str(exc_info.value)

    def test_core_properties_not_list(self):
        """Should raise error if core_properties is not a list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_data = {
                "name": "Test",
                "description": "Test",
                "folders": ["test"],
                "core_properties": "not-a-list",  # Should be a list
                "note_types": {},
            }
            yaml_path = Path(tmpdir) / "badprops.yaml"
            with yaml_path.open("w") as f:
                yaml.dump(invalid_data, f)

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("badprops")
                assert "core_properties" in str(exc_info.value)
                assert "list" in str(exc_info.value)

    def test_missing_additional_required(self):
        """Should raise error if properties.additional_required is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_data = {
                "name": "Test",
                "description": "Test",
                "folders": ["test"],
                "core_properties": ["type"],
                "note_types": {
                    "test": {
                        "description": "Test note",
                        "folder_hints": ["test/"],
                        "properties": {"optional": []},  # Missing additional_required
                        "validation": {},
                        "icon": "file",
                    }
                },
            }
            yaml_path = Path(tmpdir) / "noadditional.yaml"
            with yaml_path.open("w") as f:
                yaml.dump(invalid_data, f)

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("noadditional")
                assert "additional_required" in str(exc_info.value)

    def test_missing_optional(self):
        """Should raise error if properties.optional is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_data = {
                "name": "Test",
                "description": "Test",
                "folders": ["test"],
                "core_properties": ["type"],
                "note_types": {
                    "test": {
                        "description": "Test note",
                        "folder_hints": ["test/"],
                        "properties": {"additional_required": []},  # Missing optional
                        "validation": {},
                        "icon": "file",
                    }
                },
            }
            yaml_path = Path(tmpdir) / "nooptional.yaml"
            with yaml_path.open("w") as f:
                yaml.dump(invalid_data, f)

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                with pytest.raises(MethodologyParseError) as exc_info:
                    load_methodology("nooptional")
                assert "optional" in str(exc_info.value)


class TestMethodologiesProxyAdvanced:
    """Additional tests for METHODOLOGIES proxy coverage."""

    def test_values(self):
        """Should return list of methodology configs."""
        values = METHODOLOGIES.values()
        assert len(values) >= 4
        for v in values:
            assert "name" in v
            assert "folders" in v

    def test_items(self):
        """Should return list of (name, config) tuples."""
        items = METHODOLOGIES.items()
        assert len(items) >= 4
        for name, config in items:
            assert isinstance(name, str)
            assert config["name"] is not None


class TestLoadAllMethodologiesErrors:
    """Tests for load_all_methodologies error handling."""

    def test_continues_on_error(self, capsys):
        """Should continue loading other methodologies when one fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create one valid and one invalid methodology
            valid_data = {
                "name": "Valid",
                "description": "Valid test",
                "folders": ["test"],
                "core_properties": ["type"],
                "note_types": {},
                "folder_structure": {},
                "up_links": {},
            }
            valid_path = Path(tmpdir) / "valid.yaml"
            with valid_path.open("w") as f:
                yaml.dump(valid_data, f)

            invalid_path = Path(tmpdir) / "invalid.yaml"
            invalid_path.write_text("name: [broken")

            with patch(
                "config.methodologies.loader.METHODOLOGIES_DIR", Path(tmpdir)
            ):
                clear_cache()
                result = load_all_methodologies()
                # Should have loaded the valid one
                assert "valid" in result
                # Should have printed warning for invalid
                captured = capsys.readouterr()
                assert "Warning" in captured.out or "invalid" in str(result)


class TestCLI:
    """Tests for CLI functionality."""

    def test_cli_list_methodologies(self):
        """Should list methodologies when run without args."""
        result = subprocess.run(
            ["uv", "run", "python", "config/methodologies/loader.py"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "lyt-ace" in result.stdout
        assert "para" in result.stdout

    def test_cli_show_methodology(self):
        """Should show methodology details when name provided."""
        result = subprocess.run(
            ["uv", "run", "python", "config/methodologies/loader.py", "para"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "PARA Method" in result.stdout
        assert "Folders:" in result.stdout

    def test_cli_error_handling(self):
        """Should exit with error for invalid methodology."""
        result = subprocess.run(
            ["uv", "run", "python", "config/methodologies/loader.py", "nonexistent"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "Error" in result.stderr or "not found" in result.stderr
