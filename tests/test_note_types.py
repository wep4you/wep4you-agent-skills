"""
Tests for Note Types Manager
Ensures 90%+ code coverage for CRUD operations and wizard functionality
"""

from __future__ import annotations

# Import the module - adjust path as needed
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "note-types" / "scripts"))

from note_types import DEFAULT_NOTE_TYPES, NoteTypesManager


@pytest.fixture
def temp_config():
    """Create a temporary config file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config = {
            "note_types": {
                "test": {"folder": "Test/", "properties": ["type", "up"]},
                "demo": {
                    "folder": "Demo/",
                    "properties": ["type", "up", "status"],
                    "template": "templates/demo.md",
                },
            }
        }
        yaml.safe_dump(config, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for config tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestNoteTypesManager:
    """Test suite for NoteTypesManager class"""

    def test_init_with_config(self, temp_config):
        """Test initialization with existing config file"""
        manager = NoteTypesManager(str(temp_config))
        assert len(manager.note_types) == 2
        assert "test" in manager.note_types
        assert "demo" in manager.note_types

    def test_init_without_config(self, temp_dir):
        """Test initialization without config file (uses defaults)"""
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            manager = NoteTypesManager()
            assert manager.note_types == DEFAULT_NOTE_TYPES
            assert len(manager.note_types) == 5

    def test_init_with_empty_config(self, temp_dir):
        """Test initialization with empty config file"""
        config_path = temp_dir / "empty.yaml"
        config_path.write_text("note_types: {}\n")

        manager = NoteTypesManager(str(config_path))
        assert manager.note_types == DEFAULT_NOTE_TYPES

    def test_init_with_invalid_config(self, temp_dir):
        """Test initialization with invalid YAML"""
        config_path = temp_dir / "invalid.yaml"
        config_path.write_text("invalid: yaml: content: [[[")

        manager = NoteTypesManager(str(config_path))
        assert manager.note_types == DEFAULT_NOTE_TYPES

    def test_resolve_config_path_explicit(self, temp_config):
        """Test config path resolution with explicit path"""
        manager = NoteTypesManager(str(temp_config))
        assert manager.config_path == temp_config

    def test_resolve_config_path_default_locations(self, temp_dir):
        """Test config path resolution checks standard locations"""
        # Create .claude/config directory
        claude_dir = temp_dir / ".claude" / "config"
        claude_dir.mkdir(parents=True)
        config_file = claude_dir / "note-types.yaml"
        config_file.write_text("note_types: {}\n")

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            manager = NoteTypesManager()
            assert manager.config_path == config_file

    def test_save_note_types(self, temp_dir):
        """Test saving note types to config file"""
        config_path = temp_dir / ".claude" / "config" / "note-types.yaml"

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            manager = NoteTypesManager()
            manager.note_types["custom"] = {
                "folder": "Custom/",
                "properties": ["type", "up"],
            }
            manager._save_note_types()

            assert config_path.exists()
            with open(config_path) as f:
                saved = yaml.safe_load(f)
                assert "custom" in saved["note_types"]

    def test_list_types_empty(self, capsys):
        """Test listing when no note types exist"""
        with patch.object(NoteTypesManager, "_load_note_types", return_value={}):
            manager = NoteTypesManager()
            manager.list_types()
            captured = capsys.readouterr()
            assert "No note types defined" in captured.out

    def test_list_types_with_data(self, temp_config, capsys):
        """Test listing note types"""
        manager = NoteTypesManager(str(temp_config))
        manager.list_types()
        captured = capsys.readouterr()

        assert "Note Types (2)" in captured.out
        assert "test" in captured.out
        assert "Test/" in captured.out
        assert "demo" in captured.out
        assert "templates/demo.md" in captured.out

    def test_show_type_exists(self, temp_config, capsys):
        """Test showing details for an existing note type"""
        manager = NoteTypesManager(str(temp_config))
        manager.show_type("demo")
        captured = capsys.readouterr()

        assert "Note Type: demo" in captured.out
        assert "Demo/" in captured.out
        assert "type, up, status" in captured.out
        assert "templates/demo.md" in captured.out

    def test_show_type_not_exists(self, temp_config):
        """Test showing details for non-existent note type"""
        manager = NoteTypesManager(str(temp_config))
        with pytest.raises(SystemExit) as exc_info:
            manager.show_type("nonexistent")
        assert exc_info.value.code == 1

    def test_add_type_already_exists(self, temp_config):
        """Test adding a note type that already exists"""
        manager = NoteTypesManager(str(temp_config))
        with pytest.raises(SystemExit) as exc_info:
            manager.add_type("test", interactive=False)
        assert exc_info.value.code == 1

    def test_add_type_non_interactive(self, temp_dir):
        """Test adding note type in non-interactive mode"""
        config_path = temp_dir / "config.yaml"

        manager = NoteTypesManager(str(config_path))
        manager.note_types = {}  # Start empty

        with patch.object(manager, "_save_note_types"):
            manager.add_type("custom", interactive=False)

        assert "custom" in manager.note_types
        assert manager.note_types["custom"]["folder"] == "Custom/"
        assert manager.note_types["custom"]["properties"] == ["type", "up"]

    def test_add_type_interactive(self, temp_dir):
        """Test adding note type in interactive mode"""
        config_path = temp_dir / "config.yaml"
        manager = NoteTypesManager(str(config_path))
        manager.note_types = {}

        # Mock user inputs
        inputs = ["Custom/Folder/", "type, up, custom_prop", "templates/custom.md"]
        with patch("builtins.input", side_effect=inputs):
            with patch.object(manager, "_save_note_types"):
                manager.add_type("custom", interactive=True)

        assert "custom" in manager.note_types
        assert manager.note_types["custom"]["folder"] == "Custom/Folder/"
        assert manager.note_types["custom"]["properties"] == ["type", "up", "custom_prop"]
        assert manager.note_types["custom"]["template"] == "templates/custom.md"

    def test_edit_type_not_exists(self, temp_config):
        """Test editing non-existent note type"""
        manager = NoteTypesManager(str(temp_config))
        with pytest.raises(SystemExit) as exc_info:
            manager.edit_type("nonexistent")
        assert exc_info.value.code == 1

    def test_edit_type_interactive(self, temp_config):
        """Test editing existing note type"""
        manager = NoteTypesManager(str(temp_config))

        # Mock user inputs (press Enter to keep defaults, then change template)
        inputs = ["", "", "templates/new-template.md"]
        with patch("builtins.input", side_effect=inputs):
            with patch.object(manager, "_save_note_types"):
                manager.edit_type("test")

        assert manager.note_types["test"]["template"] == "templates/new-template.md"

    def test_remove_type_not_exists(self, temp_config):
        """Test removing non-existent note type"""
        manager = NoteTypesManager(str(temp_config))
        with pytest.raises(SystemExit) as exc_info:
            manager.remove_type("nonexistent")
        assert exc_info.value.code == 1

    def test_remove_type_cancelled(self, temp_config):
        """Test removing note type but cancel"""
        manager = NoteTypesManager(str(temp_config))
        with patch("builtins.input", return_value="n"):
            manager.remove_type("test")
        assert "test" in manager.note_types

    def test_remove_type_confirmed(self, temp_config):
        """Test removing note type with confirmation"""
        manager = NoteTypesManager(str(temp_config))
        with patch("builtins.input", return_value="y"):
            with patch.object(manager, "_save_note_types"):
                manager.remove_type("test")
        assert "test" not in manager.note_types

    def test_interactive_type_definition_new(self):
        """Test interactive type definition for new type"""
        manager = NoteTypesManager()

        inputs = ["Custom/", "type, up, custom", "templates/custom.md"]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("custom")

        assert definition["folder"] == "Custom/"
        assert definition["properties"] == ["type", "up", "custom"]
        assert definition["template"] == "templates/custom.md"

    def test_interactive_type_definition_existing(self, temp_config):
        """Test interactive type definition with existing values"""
        manager = NoteTypesManager(str(temp_config))
        existing = manager.note_types["demo"]

        # Press Enter for all (keep defaults)
        inputs = ["", "", ""]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("demo", existing)

        assert definition["folder"] == existing["folder"]
        assert definition["properties"] == existing["properties"]
        assert definition["template"] == existing["template"]

    def test_interactive_type_definition_no_template(self):
        """Test interactive type definition without template"""
        manager = NoteTypesManager()

        inputs = ["Custom/", "type, up", ""]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("custom")

        assert definition["folder"] == "Custom/"
        assert definition["properties"] == ["type", "up"]
        assert "template" not in definition

    def test_wizard_success(self, temp_dir):
        """Test wizard mode successful creation"""
        config_path = temp_dir / "config.yaml"
        manager = NoteTypesManager(str(config_path))
        manager.note_types = {}

        inputs = [
            "meeting",  # name
            "Efforts/Meetings/",  # folder
            "type, up, date, attendees",  # properties
            "templates/meeting.md",  # template
            "y",  # confirm
        ]

        with patch("builtins.input", side_effect=inputs):
            with patch.object(manager, "_save_note_types"):
                manager.wizard()

        assert "meeting" in manager.note_types
        assert manager.note_types["meeting"]["folder"] == "Efforts/Meetings/"
        assert manager.note_types["meeting"]["properties"] == ["type", "up", "date", "attendees"]
        assert manager.note_types["meeting"]["template"] == "templates/meeting.md"

    def test_wizard_cancelled(self, temp_dir):
        """Test wizard mode cancellation"""
        config_path = temp_dir / "config.yaml"
        manager = NoteTypesManager(str(config_path))
        manager.note_types = {}

        inputs = [
            "meeting",  # name
            "Efforts/Meetings/",  # folder
            "type, up",  # properties
            "",  # no template
            "n",  # cancel
        ]

        with patch("builtins.input", side_effect=inputs):
            manager.wizard()

        assert "meeting" not in manager.note_types

    def test_wizard_empty_name(self, temp_dir):
        """Test wizard with empty name (retries)"""
        config_path = temp_dir / "config.yaml"
        manager = NoteTypesManager(str(config_path))
        manager.note_types = {}

        inputs = [
            "",  # empty name (retry)
            "meeting",  # valid name
            "",  # folder (use default)
            "",  # properties (use default)
            "",  # template (none)
            "y",  # confirm
        ]

        with patch("builtins.input", side_effect=inputs):
            with patch.object(manager, "_save_note_types"):
                manager.wizard()

        assert "meeting" in manager.note_types

    def test_wizard_duplicate_name(self, temp_config):
        """Test wizard with duplicate name (retries)"""
        manager = NoteTypesManager(str(temp_config))

        inputs = [
            "test",  # duplicate name (retry)
            "custom",  # valid name
            "",  # folder (use default)
            "",  # properties (use default)
            "",  # template (none)
            "y",  # confirm
        ]

        with patch("builtins.input", side_effect=inputs):
            with patch.object(manager, "_save_note_types"):
                manager.wizard()

        assert "custom" in manager.note_types

    def test_default_note_types_structure(self):
        """Test that default note types have correct structure"""
        assert len(DEFAULT_NOTE_TYPES) == 5

        for _name, definition in DEFAULT_NOTE_TYPES.items():
            assert "folder" in definition
            assert "properties" in definition
            assert isinstance(definition["folder"], str)
            assert isinstance(definition["properties"], list)
            assert len(definition["properties"]) > 0

    def test_config_path_resolution_fallback(self, temp_dir):
        """Test config path fallback to default location"""
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch("pathlib.Path.home", return_value=temp_dir):
                manager = NoteTypesManager()
                expected_path = temp_dir / ".claude" / "config" / "note-types.yaml"
                assert manager.config_path == expected_path


class TestMainFunction:
    """Test the main CLI function"""

    def test_main_no_args(self):
        """Test main with no arguments (shows help)"""
        with patch("sys.argv", ["note_types.py"]):
            with pytest.raises(SystemExit) as exc_info:
                from note_types import main

                main()
            assert exc_info.value.code == 1

    def test_main_list(self, temp_dir):
        """Test main with --list"""
        config_path = temp_dir / "config.yaml"
        config_path.write_text("note_types:\n  test:\n    folder: Test/\n    properties: [type]\n")

        with patch("sys.argv", ["note_types.py", "--config", str(config_path), "--list"]):
            from note_types import main

            main()  # Should not raise

    def test_main_show(self, temp_dir):
        """Test main with --show"""
        config_path = temp_dir / "config.yaml"
        config_path.write_text("note_types:\n  test:\n    folder: Test/\n    properties: [type]\n")

        with patch("sys.argv", ["note_types.py", "--config", str(config_path), "--show", "test"]):
            from note_types import main

            main()  # Should not raise

    def test_main_add_non_interactive(self, temp_dir):
        """Test main with --add --non-interactive"""
        config_path = temp_dir / "config.yaml"

        with patch(
            "sys.argv",
            ["note_types.py", "--config", str(config_path), "--add", "test", "--non-interactive"],
        ):
            from note_types import main

            main()

        # Verify file was created
        assert config_path.exists()
        with open(config_path) as f:
            config = yaml.safe_load(f)
            assert "test" in config["note_types"]

    def test_main_wizard(self, temp_dir):
        """Test main with --wizard"""
        config_path = temp_dir / "config.yaml"

        inputs = ["custom", "", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            with patch("sys.argv", ["note_types.py", "--config", str(config_path), "--wizard"]):
                from note_types import main

                main()

        assert config_path.exists()


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_properties_with_whitespace(self):
        """Test properties parsing with extra whitespace"""
        manager = NoteTypesManager()

        inputs = ["Custom/", "  type  ,  up  ,  custom  ", ""]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("custom")

        assert definition["properties"] == ["type", "up", "custom"]

    def test_folder_with_trailing_slash(self):
        """Test folder handling with and without trailing slash"""
        manager = NoteTypesManager()

        inputs = ["Custom", "type, up", ""]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("custom")

        # Folder should be stored as provided by user
        assert definition["folder"] == "Custom"

    def test_save_creates_parent_directories(self, temp_dir):
        """Test that save creates parent directories if they don't exist"""
        config_path = temp_dir / "deep" / "nested" / "config.yaml"
        manager = NoteTypesManager(str(config_path))
        manager.note_types["test"] = {"folder": "Test/", "properties": ["type"]}

        manager._save_note_types()

        assert config_path.exists()
        assert config_path.parent.exists()
