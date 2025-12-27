"""
Tests for frontmatter skill

Run with: uv run pytest tests/test_frontmatter.py -v --cov
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add skills directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "frontmatter" / "scripts"))


class TestFrontmatterManagerInit:
    """Test FrontmatterManager initialization"""

    def test_init_default_path(self):
        """Test initialization with default path"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager()

        assert manager.vault_path == Path.cwd()
        assert manager.config_dir == Path.cwd() / ".claude" / "config"
        assert manager.config_file == Path.cwd() / ".claude" / "config" / "frontmatter.yaml"

    def test_init_custom_path(self, tmp_path):
        """Test initialization with custom vault path"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))

        assert manager.vault_path == tmp_path
        assert manager.config_dir == tmp_path / ".claude" / "config"

    def test_default_properties_loaded(self):
        """Test that default properties are loaded"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager()

        assert "type" in manager.core_properties
        assert "created" in manager.core_properties
        assert "up" in manager.core_properties
        assert manager.core_properties["type"]["required"] is True
        assert manager.core_properties["created"]["required"] is True

    def test_default_type_properties_loaded(self):
        """Test that default type properties are loaded"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager()

        assert "dot" in manager.type_properties
        assert "map" in manager.type_properties
        assert "project" in manager.type_properties
        assert "status" in manager.type_properties["project"]


class TestConfigLoading:
    """Test configuration file loading"""

    def test_load_nonexistent_config(self, tmp_path):
        """Test loading when config file doesn't exist"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))

        # Should use defaults
        assert "type" in manager.core_properties
        assert "dot" in manager.type_properties

    def test_load_valid_config(self, tmp_path):
        """Test loading valid config file"""
        from frontmatter import FrontmatterManager

        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "frontmatter.yaml"

        config = {
            "core_properties": {
                "custom": {
                    "required": True,
                    "type": "string",
                    "description": "Custom property",
                }
            },
            "type_properties": {
                "custom_type": {"custom_prop": {"required": False, "type": "string"}}
            },
        }

        config_file.write_text(yaml.dump(config))

        manager = FrontmatterManager(str(tmp_path))

        assert "custom" in manager.core_properties
        assert "custom_type" in manager.type_properties

    def test_load_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML config"""
        from frontmatter import FrontmatterManager

        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "frontmatter.yaml"

        config_file.write_text("invalid: yaml: [")

        # Should not crash, fall back to defaults
        manager = FrontmatterManager(str(tmp_path))
        assert "type" in manager.core_properties

    def test_load_empty_config(self, tmp_path):
        """Test loading empty config file"""
        from frontmatter import FrontmatterManager

        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "frontmatter.yaml"

        config_file.write_text("")

        manager = FrontmatterManager(str(tmp_path))
        assert "type" in manager.core_properties


class TestSaveConfig:
    """Test configuration saving"""

    def test_save_creates_directory(self, tmp_path):
        """Test that save creates config directory"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.save_config()

        assert manager.config_dir.exists()
        assert manager.config_file.exists()

    def test_save_writes_yaml(self, tmp_path):
        """Test that save writes valid YAML"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("test", "string", required=True)
        manager.save_config()

        with open(manager.config_file) as f:
            config = yaml.safe_load(f)

        assert "core_properties" in config
        assert "test" in config["core_properties"]

    def test_save_roundtrip(self, tmp_path):
        """Test save and load roundtrip"""
        from frontmatter import FrontmatterManager

        manager1 = FrontmatterManager(str(tmp_path))
        manager1.add_core_property("roundtrip", "string", description="Test")
        manager1.save_config()

        manager2 = FrontmatterManager(str(tmp_path))
        assert "roundtrip" in manager2.core_properties
        assert manager2.core_properties["roundtrip"]["description"] == "Test"


class TestListCoreProperties:
    """Test listing core properties"""

    def test_list_core_text_format(self, tmp_path, capsys):
        """Test listing core properties in text format"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_core_properties("text")

        captured = capsys.readouterr()
        assert "Core Properties:" in captured.out
        assert "type:" in captured.out
        assert "created:" in captured.out

    def test_list_core_json_format(self, tmp_path, capsys):
        """Test listing core properties in JSON format"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_core_properties("json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "type" in data
        assert data["type"]["required"] is True

    def test_list_core_yaml_format(self, tmp_path, capsys):
        """Test listing core properties in YAML format"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_core_properties("yaml")

        captured = capsys.readouterr()
        data = yaml.safe_load(captured.out)

        assert "type" in data
        assert data["type"]["required"] is True


class TestAddCoreProperty:
    """Test adding core properties"""

    def test_add_simple_property(self, tmp_path, capsys):
        """Test adding a simple core property"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("test", "string")

        assert "test" in manager.core_properties
        assert manager.core_properties["test"]["type"] == "string"
        assert manager.core_properties["test"]["required"] is False

        captured = capsys.readouterr()
        assert "Added/updated core property: test" in captured.out

    def test_add_required_property(self, tmp_path):
        """Test adding required core property"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("required_test", "string", required=True)

        assert manager.core_properties["required_test"]["required"] is True

    def test_add_property_with_description(self, tmp_path):
        """Test adding property with description"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("desc_test", "string", description="Test description")

        assert manager.core_properties["desc_test"]["description"] == "Test description"

    def test_add_property_with_format(self, tmp_path):
        """Test adding property with format spec"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("date_test", "date", format="YYYY-MM-DD")

        assert manager.core_properties["date_test"]["format"] == "YYYY-MM-DD"

    def test_update_existing_property(self, tmp_path):
        """Test updating an existing property"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("update_test", "string", required=False)
        manager.add_core_property("update_test", "date", required=True)

        assert manager.core_properties["update_test"]["type"] == "date"
        assert manager.core_properties["update_test"]["required"] is True


class TestRemoveCoreProperty:
    """Test removing core properties"""

    def test_remove_existing_property(self, tmp_path, capsys):
        """Test removing an existing property"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("to_remove", "string")
        manager.remove_core_property("to_remove")

        assert "to_remove" not in manager.core_properties
        captured = capsys.readouterr()
        assert "Removed core property: to_remove" in captured.out

    def test_remove_nonexistent_property(self, tmp_path):
        """Test removing a property that doesn't exist"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))

        with pytest.raises(SystemExit) as exc_info:
            manager.remove_core_property("nonexistent")

        assert exc_info.value.code == 1


class TestListTypeProperties:
    """Test listing type-specific properties"""

    def test_list_all_types_text(self, tmp_path, capsys):
        """Test listing all type properties in text format"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_type_properties(None, "text")

        captured = capsys.readouterr()
        assert "Type-Specific Properties:" in captured.out
        assert "dot:" in captured.out
        assert "project:" in captured.out

    def test_list_specific_type_text(self, tmp_path, capsys):
        """Test listing specific type properties in text format"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_type_properties("project", "text")

        captured = capsys.readouterr()
        assert "project:" in captured.out
        assert "status:" in captured.out

    def test_list_type_json_format(self, tmp_path, capsys):
        """Test listing type properties in JSON format"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_type_properties("dot", "json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "dot" in data

    def test_list_type_yaml_format(self, tmp_path, capsys):
        """Test listing type properties in YAML format"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_type_properties("map", "yaml")

        captured = capsys.readouterr()
        data = yaml.safe_load(captured.out)

        assert "map" in data

    def test_list_nonexistent_type(self, tmp_path):
        """Test listing properties for nonexistent type"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))

        with pytest.raises(SystemExit) as exc_info:
            manager.list_type_properties("nonexistent", "text")

        assert exc_info.value.code == 1


class TestAddTypeProperty:
    """Test adding type-specific properties"""

    def test_add_property_to_existing_type(self, tmp_path, capsys):
        """Test adding property to existing type"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_type_property("dot", "new_prop", "string", description="New property")

        assert "new_prop" in manager.type_properties["dot"]
        assert manager.type_properties["dot"]["new_prop"]["type"] == "string"

        captured = capsys.readouterr()
        assert "Added/updated property 'new_prop' for type 'dot'" in captured.out

    def test_add_property_to_new_type(self, tmp_path):
        """Test adding property creates new type"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_type_property("new_type", "prop", "string")

        assert "new_type" in manager.type_properties
        assert "prop" in manager.type_properties["new_type"]

    def test_add_required_type_property(self, tmp_path):
        """Test adding required type property"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_type_property("dot", "required_prop", "string", required=True)

        assert manager.type_properties["dot"]["required_prop"]["required"] is True

    def test_update_existing_type_property(self, tmp_path):
        """Test updating existing type property"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_type_property("dot", "tags", "list[string]", description="Updated")

        assert manager.type_properties["dot"]["tags"]["description"] == "Updated"


class TestRemoveTypeProperty:
    """Test removing type-specific properties"""

    def test_remove_existing_property(self, tmp_path, capsys):
        """Test removing existing type property"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_type_property("dot", "to_remove", "string")
        manager.remove_type_property("dot", "to_remove")

        assert "to_remove" not in manager.type_properties["dot"]
        captured = capsys.readouterr()
        assert "Removed property 'to_remove' from type 'dot'" in captured.out

    def test_remove_from_nonexistent_type(self, tmp_path):
        """Test removing property from nonexistent type"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))

        with pytest.raises(SystemExit) as exc_info:
            manager.remove_type_property("nonexistent", "prop")

        assert exc_info.value.code == 1

    def test_remove_nonexistent_property(self, tmp_path):
        """Test removing nonexistent property from type"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))

        with pytest.raises(SystemExit) as exc_info:
            manager.remove_type_property("dot", "nonexistent")

        assert exc_info.value.code == 1


class TestListTypes:
    """Test listing note types"""

    def test_list_types(self, tmp_path, capsys):
        """Test listing all configured types"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.list_types()

        captured = capsys.readouterr()
        assert "Configured Note Types:" in captured.out
        assert "dot:" in captured.out
        assert "map:" in captured.out
        assert "project:" in captured.out


class TestGetRequiredProperties:
    """Test getting required properties"""

    def test_get_core_required_only(self):
        """Test getting core required properties only"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager()
        required = manager.get_required_properties(None)

        assert "type" in required
        assert "created" in required
        assert "up" not in required  # Optional

    def test_get_required_for_type(self):
        """Test getting required properties for specific type"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager()
        required = manager.get_required_properties("project")

        assert "type" in required  # Core required
        assert "created" in required  # Core required
        assert "status" in required  # Type-specific required

    def test_get_required_nonexistent_type(self):
        """Test getting required for nonexistent type"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager()
        required = manager.get_required_properties("nonexistent")

        # Should still return core required
        assert "type" in required
        assert "created" in required


class TestCLI:
    """Test command-line interface"""

    def test_no_command_shows_help(self, tmp_path):
        """Test running with no command shows help"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(sys, "argv", ["frontmatter.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_list_core_command(self, tmp_path, capsys):
        """Test list-core command"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "list-core"]):
            main()

        captured = capsys.readouterr()
        assert "Core Properties:" in captured.out

    def test_add_core_command(self, tmp_path):
        """Test add-core command"""
        import sys
        from unittest.mock import patch

        from frontmatter import FrontmatterManager, main

        args = [
            "frontmatter.py",
            "--vault",
            str(tmp_path),
            "add-core",
            "test_prop",
            "string",
            "--required",
            "--description",
            "Test",
        ]

        with patch.object(sys, "argv", args):
            main()

        # Verify property was added
        manager = FrontmatterManager(str(tmp_path))
        assert "test_prop" in manager.core_properties

    def test_remove_core_command(self, tmp_path):
        """Test remove-core command"""
        import sys
        from unittest.mock import patch

        from frontmatter import FrontmatterManager, main

        manager = FrontmatterManager(str(tmp_path))
        manager.add_core_property("to_remove", "string")
        manager.save_config()

        args = ["frontmatter.py", "--vault", str(tmp_path), "remove-core", "to_remove"]

        with patch.object(sys, "argv", args):
            main()

        manager2 = FrontmatterManager(str(tmp_path))
        assert "to_remove" not in manager2.core_properties

    def test_list_type_command(self, tmp_path, capsys):
        """Test list-type command"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "list-type"]):
            main()

        captured = capsys.readouterr()
        assert "Type-Specific Properties:" in captured.out

    def test_list_type_with_arg(self, tmp_path, capsys):
        """Test list-type command with type argument"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(
            sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "list-type", "dot"]
        ):
            main()

        captured = capsys.readouterr()
        assert "dot:" in captured.out

    def test_add_type_prop_command(self, tmp_path):
        """Test add-type-prop command"""
        import sys
        from unittest.mock import patch

        from frontmatter import FrontmatterManager, main

        args = [
            "frontmatter.py",
            "--vault",
            str(tmp_path),
            "add-type-prop",
            "dot",
            "new_prop",
            "string",
            "--required",
        ]

        with patch.object(sys, "argv", args):
            main()

        manager = FrontmatterManager(str(tmp_path))
        assert "new_prop" in manager.type_properties["dot"]

    def test_remove_type_prop_command(self, tmp_path):
        """Test remove-type-prop command"""
        import sys
        from unittest.mock import patch

        from frontmatter import FrontmatterManager, main

        manager = FrontmatterManager(str(tmp_path))
        manager.add_type_property("dot", "to_remove", "string")
        manager.save_config()

        args = [
            "frontmatter.py",
            "--vault",
            str(tmp_path),
            "remove-type-prop",
            "dot",
            "to_remove",
        ]

        with patch.object(sys, "argv", args):
            main()

        manager2 = FrontmatterManager(str(tmp_path))
        assert "to_remove" not in manager2.type_properties["dot"]

    def test_list_types_command(self, tmp_path, capsys):
        """Test list-types command"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "list-types"]):
            main()

        captured = capsys.readouterr()
        assert "Configured Note Types:" in captured.out

    def test_get_required_command(self, tmp_path, capsys):
        """Test get-required command"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(
            sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "get-required"]
        ):
            main()

        captured = capsys.readouterr()
        assert "Required Properties" in captured.out

    def test_get_required_with_type(self, tmp_path, capsys):
        """Test get-required command with type"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(
            sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "get-required", "project"]
        ):
            main()

        captured = capsys.readouterr()
        assert "Required Properties for type 'project'" in captured.out

    def test_save_command(self, tmp_path, capsys):
        """Test save command"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "save"]):
            main()

        captured = capsys.readouterr()
        assert "Configuration saved" in captured.out

    def test_json_output_format(self, tmp_path, capsys):
        """Test JSON output format"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(
            sys,
            "argv",
            ["frontmatter.py", "--vault", str(tmp_path), "--format", "json", "list-core"],
        ):
            main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "type" in data

    def test_yaml_output_format(self, tmp_path, capsys):
        """Test YAML output format"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(
            sys,
            "argv",
            ["frontmatter.py", "--vault", str(tmp_path), "--format", "yaml", "list-core"],
        ):
            main()

        captured = capsys.readouterr()
        data = yaml.safe_load(captured.out)
        assert "type" in data

    def test_get_required_json_format(self, tmp_path, capsys):
        """Test get-required with JSON format"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(
            sys,
            "argv",
            ["frontmatter.py", "--vault", str(tmp_path), "--format", "json", "get-required"],
        ):
            main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "type" in data

    def test_get_required_yaml_format(self, tmp_path, capsys):
        """Test get-required with YAML format"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        with patch.object(
            sys,
            "argv",
            ["frontmatter.py", "--vault", str(tmp_path), "--format", "yaml", "get-required"],
        ):
            main()

        captured = capsys.readouterr()
        data = yaml.safe_load(captured.out)
        assert "type" in data


class TestDefaultProperties:
    """Test default property definitions"""

    def test_default_core_properties_structure(self):
        """Test default core properties have correct structure"""
        from frontmatter import DEFAULT_CORE_PROPERTIES

        assert isinstance(DEFAULT_CORE_PROPERTIES, dict)

        for _name, spec in DEFAULT_CORE_PROPERTIES.items():
            assert "required" in spec
            assert "type" in spec
            assert isinstance(spec["required"], bool)
            assert isinstance(spec["type"], str)

    def test_default_type_properties_structure(self):
        """Test default type properties have correct structure"""
        from frontmatter import DEFAULT_TYPE_PROPERTIES

        assert isinstance(DEFAULT_TYPE_PROPERTIES, dict)

        for _type_name, properties in DEFAULT_TYPE_PROPERTIES.items():
            assert isinstance(properties, dict)
            for _prop_name, spec in properties.items():
                assert "required" in spec
                assert "type" in spec


class TestErrorHandling:
    """Test error handling"""

    def test_cli_error_handling(self, tmp_path):
        """Test CLI error handling"""
        import sys
        from unittest.mock import patch

        from frontmatter import main

        # Try to remove non-existent property
        with patch.object(
            sys, "argv", ["frontmatter.py", "--vault", str(tmp_path), "remove-core", "nonexistent"]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_config_load_exception_handling(self, tmp_path, monkeypatch):
        """Test exception handling during config load"""
        from frontmatter import FrontmatterManager

        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "frontmatter.yaml"
        config_file.write_text("valid: yaml")

        # Mock open to raise exception
        original_open = open

        def mock_open(*args, **kwargs):  # type: ignore[no-untyped-def]
            if "frontmatter.yaml" in str(args[0]):
                raise PermissionError("Test error")
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        # Should not crash
        manager = FrontmatterManager(str(tmp_path))
        assert "type" in manager.core_properties


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_type_properties(self, tmp_path):
        """Test type with no additional properties"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.type_properties["empty_type"] = {}

        required = manager.get_required_properties("empty_type")
        # Should only have core required
        assert "type" in required
        assert "created" in required

    def test_property_with_values_list(self, tmp_path):
        """Test property with values constraint"""
        from frontmatter import FrontmatterManager

        manager = FrontmatterManager(str(tmp_path))
        manager.add_type_property(
            "test_type",
            "status",
            "string",
            values=["active", "inactive"],
            description="Status",
        )

        assert "values" in manager.type_properties["test_type"]["status"]
        assert manager.type_properties["test_type"]["status"]["values"] == [
            "active",
            "inactive",
        ]
