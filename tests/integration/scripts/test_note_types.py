"""
Tests for Note Types Manager
Tests CRUD operations against .claude/settings.yaml
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

_repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_repo_root / "skills" / "note-types" / "scripts"))

from note_types import NoteTypesManager, display_type_details, display_type_list  # noqa: E402


@pytest.fixture
def temp_vault():
    """Create a temporary vault with settings.yaml"""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir)
        settings_dir = vault_path / ".claude"
        settings_dir.mkdir(parents=True)

        settings = {
            "version": "1.0",
            "methodology": "para",
            "core_properties": {
                "all": ["type", "up", "created", "tags"],
            },
            "note_types": {
                "project": {
                    "description": "Active projects",
                    "folder_hints": ["Projects/"],
                    "properties": {
                        "additional_required": ["status"],
                        "optional": ["deadline"],
                    },
                    "validation": {"allow_empty_up": False},
                    "icon": "target",
                },
                "area": {
                    "description": "Areas of responsibility",
                    "folder_hints": ["Areas/"],
                    "properties": {
                        "additional_required": [],
                        "optional": ["review_frequency"],
                    },
                    "validation": {"allow_empty_up": False},
                    "icon": "home",
                },
            },
            "folder_structure": {
                "templates": "x/templates/",
                "bases": "x/bases/",
            },
            "validation": {"require_core_properties": True},
        }

        settings_file = settings_dir / "settings.yaml"
        with open(settings_file, "w") as f:
            yaml.safe_dump(settings, f)

        yield vault_path


@pytest.fixture
def empty_dir():
    """Create a temporary directory without settings.yaml"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestNoteTypesManager:
    """Test suite for NoteTypesManager class"""

    def test_init_with_vault(self, temp_vault):
        """Test initialization with existing vault settings"""
        manager = NoteTypesManager(str(temp_vault))
        assert len(manager.note_types) == 2
        assert "project" in manager.note_types
        assert "area" in manager.note_types
        assert manager.settings["methodology"] == "para"

    def test_init_no_settings_file(self, empty_dir):
        """Test initialization without settings.yaml exits"""
        with pytest.raises(SystemExit) as exc_info:
            NoteTypesManager(str(empty_dir))
        assert exc_info.value.code == 1

    def test_init_invalid_yaml(self, empty_dir):
        """Test initialization with invalid YAML exits"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("invalid: yaml: content: [[[")

        with pytest.raises(SystemExit) as exc_info:
            NoteTypesManager(str(empty_dir))
        assert exc_info.value.code == 1

    def test_init_empty_note_types(self, empty_dir, capsys):
        """Test initialization with empty note_types"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("version: '1.0'\nmethodology: custom\nnote_types: {}\n")

        manager = NoteTypesManager(str(empty_dir))
        captured = capsys.readouterr()
        # Status messages go to stderr to keep stdout clean for JSON output
        assert "No note types found" in captured.err
        assert manager.note_types == {}

    def test_save_settings(self, temp_vault):
        """Test saving settings back to file"""
        manager = NoteTypesManager(str(temp_vault))
        manager.note_types["custom"] = {
            "description": "Custom notes",
            "folder_hints": ["Custom/"],
            "properties": {"additional_required": [], "optional": []},
            "validation": {"allow_empty_up": False},
            "icon": "file",
        }
        manager._save_settings()

        # Reload and verify
        with open(temp_vault / ".claude" / "settings.yaml") as f:
            saved = yaml.safe_load(f)
        assert "custom" in saved["note_types"]

    def test_format_properties_list(self, temp_vault):
        """Test _format_properties with list format"""
        manager = NoteTypesManager(str(temp_vault))
        config = {"properties": ["type", "up", "status"]}
        result = manager._format_properties(config)
        assert result == ["type", "up", "status"]

    def test_format_properties_dict(self, temp_vault):
        """Test _format_properties with dict format"""
        manager = NoteTypesManager(str(temp_vault))
        config = {
            "properties": {
                "additional_required": ["status"],
                "optional": ["deadline"],
            }
        }
        result = manager._format_properties(config)
        assert result == ["status", "deadline"]

    def test_list_types(self, temp_vault, capsys):
        """Test listing note types"""
        manager = NoteTypesManager(str(temp_vault))
        types = manager.list_types()  # Now returns dict

        # Test the data
        assert len(types) == 2
        assert "project" in types
        assert "area" in types

        # Test display function
        capsys.readouterr()  # Clear the __init__ output
        display_type_list(manager)
        captured = capsys.readouterr()
        assert "Note Types (2)" in captured.out
        assert "Core properties:" in captured.out

    def test_list_types_empty(self, empty_dir, capsys):
        """Test listing when no note types exist"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("version: '1.0'\nnote_types: {}\n")

        manager = NoteTypesManager(str(empty_dir))
        capsys.readouterr()  # Clear the __init__ output
        display_type_list(manager)
        captured = capsys.readouterr()
        assert "No note types defined" in captured.out

    def test_show_type_exists(self, temp_vault, capsys):
        """Test showing details for existing note type"""
        manager = NoteTypesManager(str(temp_vault))
        capsys.readouterr()  # Clear __init__ output
        display_type_details(manager, "project")
        captured = capsys.readouterr()

        assert "Note Type: project" in captured.out
        assert "Active projects" in captured.out
        assert "Projects/" in captured.out
        assert "status" in captured.out

    def test_show_type_not_exists(self, temp_vault, capsys):
        """Test showing non-existent note type"""
        manager = NoteTypesManager(str(temp_vault))
        capsys.readouterr()  # Clear __init__ output
        with pytest.raises(SystemExit) as exc_info:
            display_type_details(manager, "nonexistent")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert "Available:" in captured.out

    def test_add_type_already_exists(self, temp_vault, capsys):
        """Test adding note type that already exists"""
        manager = NoteTypesManager(str(temp_vault))
        with pytest.raises(ValueError) as exc_info:
            manager.add_type("project", {})
        assert "already exists" in str(exc_info.value)

    def test_add_type_non_interactive(self, temp_vault):
        """Test adding note type with minimal config"""
        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("custom", {})  # Empty config uses defaults

        assert "custom" in manager.note_types
        assert manager.note_types["custom"]["folder_hints"] == ["Custom/"]
        assert manager.note_types["custom"]["description"] == "Custom notes"

    def test_add_type_with_config(self, temp_vault):
        """Test adding note type with full config dict (wizard alternative)"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        config = {
            "description": "Meeting notes and action items",
            "folder": "Meetings/",
            "required_props": ["attendees", "date"],
            "optional_props": ["action_items"],
            "icon": "calendar",
        }
        manager.add_type("meeting", config=config)

        assert "meeting" in manager.note_types
        meeting = manager.note_types["meeting"]
        assert meeting["description"] == "Meeting notes and action items"
        assert meeting["folder_hints"] == ["Meetings/"]
        assert meeting["properties"]["additional_required"] == ["attendees", "date"]
        assert meeting["properties"]["optional"] == ["action_items"]
        assert meeting["icon"] == "calendar"

    def test_add_type_with_config_string_props(self, temp_vault):
        """Test that config accepts comma-separated string for properties"""
        manager = NoteTypesManager(str(temp_vault))
        config = {
            "description": "Blog posts",
            "folder": "Blog",
            "required_props": "status, published",
            "optional_props": "tags, author",
        }
        manager.add_type("blog", config=config)

        blog = manager.note_types["blog"]
        assert blog["folder_hints"] == ["Blog/"]  # Trailing slash added
        assert blog["properties"]["additional_required"] == ["status", "published"]
        assert blog["properties"]["optional"] == ["tags", "author"]

    def test_normalize_config_defaults(self, temp_vault):
        """Test that normalize_config applies defaults correctly"""
        manager = NoteTypesManager(str(temp_vault))

        # Minimal config - should get all defaults
        config = manager._normalize_config("test", {})

        assert config["description"] == "Test notes"
        assert config["folder_hints"] == ["Test/"]
        assert config["properties"]["additional_required"] == []
        assert config["properties"]["optional"] == []
        assert config["icon"] == "file"
        assert config["validation"]["allow_empty_up"] is False

    def test_add_type_interactive(self, temp_vault):
        """Test adding note type with config (interactive moved to wizard)"""
        manager = NoteTypesManager(str(temp_vault))

        # New API: add_type(name, config)
        config = {
            "description": "Blog posts",
            "folder": "Blog/Posts/",
            "required_props": ["author", "published"],
            "optional_props": ["featured"],
            "icon": "pencil",
        }
        manager.add_type("blog", config)

        assert "blog" in manager.note_types
        assert manager.note_types["blog"]["folder_hints"] == ["Blog/Posts/"]
        assert manager.note_types["blog"]["properties"]["additional_required"] == [
            "author",
            "published",
        ]

    def test_edit_type_not_exists(self, temp_vault):
        """Test updating non-existent note type"""
        manager = NoteTypesManager(str(temp_vault))
        with pytest.raises(ValueError) as exc_info:
            manager.update_type("nonexistent", {})
        assert "not found" in str(exc_info.value)

    def test_edit_type_interactive(self, temp_vault):
        """Test updating existing note type with config"""
        manager = NoteTypesManager(str(temp_vault))

        # New API: update_type(name, config)
        manager.update_type("project", {"icon": "rocket"})

        assert manager.note_types["project"]["icon"] == "rocket"

    def test_edit_type_non_interactive(self, temp_vault):
        """Test updating note type with full config (CRUD style)"""
        manager = NoteTypesManager(str(temp_vault))

        # Update with specific config
        config = {
            "description": "Updated description",
            "folder": "NewProjects/",
            "required_props": ["status", "priority"],
            "optional_props": ["deadline"],
            "icon": "rocket",
        }
        manager.update_type("project", config)

        updated = manager.note_types["project"]
        assert updated["description"] == "Updated description"
        assert updated["folder_hints"] == ["NewProjects/"]
        assert updated["properties"]["additional_required"] == ["status", "priority"]
        assert updated["properties"]["optional"] == ["deadline"]
        assert updated["icon"] == "rocket"

    def test_edit_type_non_interactive_partial(self, temp_vault):
        """Test partial update only updates provided fields"""
        manager = NoteTypesManager(str(temp_vault))

        original_folder = manager.note_types["project"]["folder_hints"]
        original_props = manager.note_types["project"]["properties"]

        # Only update description and icon
        manager.update_type(
            "project",
            {
                "description": "Just updated",
                "icon": "star",
            },
        )

        config = manager.note_types["project"]
        assert config["description"] == "Just updated"
        assert config["icon"] == "star"
        # These should remain unchanged
        assert config["folder_hints"] == original_folder
        assert config["properties"] == original_props

    def test_edit_type_with_config(self, temp_vault):
        """Test updating note type with full config dict"""
        manager = NoteTypesManager(str(temp_vault))

        config = {
            "description": "Updated via config",
            "required_props": ["new_required"],
            "optional_props": ["new_optional"],
            "icon": "rocket",
        }
        manager.update_type("project", config)

        updated = manager.note_types["project"]
        assert updated["description"] == "Updated via config"
        assert updated["properties"]["additional_required"] == ["new_required"]
        assert updated["properties"]["optional"] == ["new_optional"]
        assert updated["icon"] == "rocket"
        # Folder should remain unchanged (not provided in config)
        assert updated["folder_hints"] == ["Projects/"]

    def test_edit_type_with_config_partial(self, temp_vault):
        """Test that update with config only updates provided fields"""
        manager = NoteTypesManager(str(temp_vault))

        original_icon = manager.note_types["project"]["icon"]

        # Only update description
        config = {"description": "Only description changed"}
        manager.update_type("project", config)

        updated = manager.note_types["project"]
        assert updated["description"] == "Only description changed"
        # Icon should remain unchanged
        assert updated["icon"] == original_icon

    def test_remove_type_not_exists(self, temp_vault):
        """Test deleting non-existent note type"""
        manager = NoteTypesManager(str(temp_vault))
        with pytest.raises(ValueError) as exc_info:
            manager.delete_type("nonexistent")
        assert "not found" in str(exc_info.value)

    def test_remove_type_cancelled(self, temp_vault):
        """Test delete_type removes type (no confirmation in CRUD)"""
        # Note: Confirmation is handled in wizard layer, not CRUD
        manager = NoteTypesManager(str(temp_vault))
        # In new API, delete_type directly removes
        manager.delete_type("project")
        assert "project" not in manager.note_types

    def test_remove_type_confirmed(self, temp_vault):
        """Test delete_type removes and returns config"""
        manager = NoteTypesManager(str(temp_vault))
        # In new CRUD API, delete_type returns the deleted config
        deleted = manager.delete_type("area")
        assert "area" not in manager.note_types
        assert deleted["description"] == "Areas of responsibility"

    def test_remove_type_skip_confirm(self, temp_vault):
        """Test delete_type removes type directly (CRUD operation)"""
        manager = NoteTypesManager(str(temp_vault))
        # New API has no confirmation - that's in the wizard layer
        manager.delete_type("project")
        assert "project" not in manager.note_types

    def test_interactive_type_definition_new(self, temp_vault):
        """Test interactive type definition via wizard module"""
        from note_type_wizard import interactive_type_definition

        inputs = ["My custom notes", "Custom/Notes/", "author", "tags", "star"]
        with patch("builtins.input", side_effect=inputs):
            definition = interactive_type_definition("custom")

        assert definition["description"] == "My custom notes"
        assert definition["folder_hints"] == ["Custom/Notes/"]
        assert definition["properties"]["additional_required"] == ["author"]
        assert definition["properties"]["optional"] == ["tags"]
        assert definition["icon"] == "star"

    def test_interactive_type_definition_keep_defaults(self, temp_vault):
        """Test interactive type definition keeping defaults"""
        from note_type_wizard import interactive_type_definition

        manager = NoteTypesManager(str(temp_vault))
        existing = manager.note_types["project"]

        # Press Enter for all (keep defaults)
        inputs = ["", "", "", "", ""]
        with patch("builtins.input", side_effect=inputs):
            definition = interactive_type_definition("project", existing)

        assert definition["description"] == existing["description"]
        assert definition["folder_hints"] == existing["folder_hints"]

    def test_interactive_type_definition_none_properties(self, temp_vault):
        """Test interactive type definition with 'none' for properties"""
        from note_type_wizard import interactive_type_definition

        inputs = ["Simple notes", "Simple/", "none", "none", "file"]
        with patch("builtins.input", side_effect=inputs):
            definition = interactive_type_definition("simple")

        assert definition["properties"]["additional_required"] == []
        assert definition["properties"]["optional"] == []

    def test_wizard_success(self, temp_vault):
        """Test wizard mode successful creation via CLI"""
        from note_type_wizard import handle_wizard

        manager = NoteTypesManager(str(temp_vault))

        inputs = [
            "meeting",  # name
            "Meeting notes",  # description
            "Meetings/",  # folder
            "date, attendees",  # required
            "action_items",  # optional
            "calendar",  # icon
            "y",  # confirm
        ]
        with patch("builtins.input", side_effect=inputs):
            handle_wizard(manager)

        assert "meeting" in manager.note_types

    def test_wizard_cancelled(self, temp_vault):
        """Test wizard mode cancellation"""
        from note_type_wizard import handle_wizard

        manager = NoteTypesManager(str(temp_vault))

        inputs = [
            "meeting",  # name
            "Meeting notes",  # description
            "Meetings/",  # folder
            "none",  # required
            "none",  # optional
            "file",  # icon
            "n",  # cancel
        ]
        with patch("builtins.input", side_effect=inputs):
            handle_wizard(manager)

        assert "meeting" not in manager.note_types

    def test_wizard_empty_name_retry(self, temp_vault):
        """Test wizard with empty name retries"""
        from note_type_wizard import handle_wizard

        manager = NoteTypesManager(str(temp_vault))

        inputs = [
            "",  # empty (retry)
            "meeting",  # valid name
            "",  # description (default)
            "",  # folder (default)
            "",  # required (default)
            "",  # optional (default)
            "",  # icon (default)
            "y",  # confirm
        ]
        with patch("builtins.input", side_effect=inputs):
            handle_wizard(manager)

        assert "meeting" in manager.note_types

    def test_wizard_duplicate_name_retry(self, temp_vault):
        """Test wizard with duplicate name retries"""
        from note_type_wizard import handle_wizard

        manager = NoteTypesManager(str(temp_vault))

        inputs = [
            "project",  # duplicate (retry)
            "meeting",  # valid name
            "",
            "",
            "",
            "",
            "",
            "y",
        ]
        with patch("builtins.input", side_effect=inputs):
            handle_wizard(manager)

        assert "meeting" in manager.note_types


class TestMainFunction:
    """Test the main CLI function"""

    def test_main_no_args(self):
        """Test main with no arguments shows help"""
        with patch("sys.argv", ["note_types.py"]):
            with pytest.raises(SystemExit) as exc_info:
                from note_types import main

                main()
            assert exc_info.value.code == 1

    def test_main_list(self, temp_vault):
        """Test main with --list"""
        with patch("sys.argv", ["note_types.py", "--vault", str(temp_vault), "--list"]):
            from note_types import main

            main()

    def test_main_show(self, temp_vault):
        """Test main with --show"""
        with patch("sys.argv", ["note_types.py", "--vault", str(temp_vault), "--show", "project"]):
            from note_types import main

            main()

    def test_main_add_non_interactive(self, temp_vault):
        """Test main with --add --non-interactive"""
        with patch(
            "sys.argv",
            ["note_types.py", "--vault", str(temp_vault), "--add", "custom", "--non-interactive"],
        ):
            from note_types import main

            main()

        # Verify file was updated
        with open(temp_vault / ".claude" / "settings.yaml") as f:
            settings = yaml.safe_load(f)
            assert "custom" in settings["note_types"]

    def test_main_add_with_config(self, temp_vault):
        """Test main with --add --config (wizard alternative)"""
        config_json = (
            '{"description": "Meeting notes", "folder": "Meetings/", '
            '"required_props": ["date"], "icon": "calendar"}'
        )

        with patch(
            "sys.argv",
            [
                "note_types.py",
                "--vault",
                str(temp_vault),
                "--add",
                "meeting",
                "--config",
                config_json,
            ],
        ):
            from note_types import main

            main()

        # Verify file was updated with full config
        with open(temp_vault / ".claude" / "settings.yaml") as f:
            settings = yaml.safe_load(f)
            meeting = settings["note_types"]["meeting"]
            assert meeting["description"] == "Meeting notes"
            assert meeting["folder_hints"] == ["Meetings/"]
            assert meeting["properties"]["additional_required"] == ["date"]
            assert meeting["icon"] == "calendar"

    def test_main_add_with_invalid_config(self, temp_vault, capsys):
        """Test main with invalid JSON config"""
        with patch(
            "sys.argv",
            [
                "note_types.py",
                "--vault",
                str(temp_vault),
                "--add",
                "meeting",
                "--config",
                "not valid json",
            ],
        ):
            from note_types import main

            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.out

    def test_main_edit(self, temp_vault):
        """Test main with --edit"""
        inputs = ["", "", "", "", ""]  # Keep all defaults
        with patch("builtins.input", side_effect=inputs):
            with patch(
                "sys.argv", ["note_types.py", "--vault", str(temp_vault), "--edit", "project"]
            ):
                from note_types import main

                main()

    def test_main_edit_non_interactive(self, temp_vault):
        """Test main with --edit --non-interactive and parameters"""
        with patch(
            "sys.argv",
            [
                "note_types.py",
                "--vault",
                str(temp_vault),
                "--edit",
                "project",
                "--non-interactive",
                "--description",
                "New description",
                "--folder",
                "NewFolder/",
                "--required-props",
                "status,priority",
                "--optional-props",
                "deadline,notes",
                "--icon",
                "rocket",
            ],
        ):
            from note_types import main

            main()

        # Verify the settings were updated
        import yaml

        settings_path = temp_vault / ".claude" / "settings.yaml"
        with open(settings_path) as f:
            settings = yaml.safe_load(f)

        project = settings["note_types"]["project"]
        assert project["description"] == "New description"
        assert project["folder_hints"] == ["NewFolder/"]
        assert project["properties"]["additional_required"] == ["status", "priority"]
        assert project["properties"]["optional"] == ["deadline", "notes"]
        assert project["icon"] == "rocket"

    def test_main_edit_with_config(self, temp_vault):
        """Test main with --edit --config"""
        config_json = (
            '{"description": "Edited via config", "required_props": ["priority"], "icon": "star"}'
        )

        with patch(
            "sys.argv",
            [
                "note_types.py",
                "--vault",
                str(temp_vault),
                "--edit",
                "project",
                "--config",
                config_json,
            ],
        ):
            from note_types import main

            main()

        # Verify the settings were updated
        with open(temp_vault / ".claude" / "settings.yaml") as f:
            settings = yaml.safe_load(f)
            project = settings["note_types"]["project"]
            assert project["description"] == "Edited via config"
            assert project["properties"]["additional_required"] == ["priority"]
            assert project["icon"] == "star"

    def test_main_remove(self, temp_vault):
        """Test main with --remove"""
        with patch("builtins.input", return_value="y"):
            with patch(
                "sys.argv", ["note_types.py", "--vault", str(temp_vault), "--remove", "area"]
            ):
                from note_types import main

                main()

        with open(temp_vault / ".claude" / "settings.yaml") as f:
            settings = yaml.safe_load(f)
            assert "area" not in settings["note_types"]

    def test_main_remove_with_yes(self, temp_vault):
        """Test main with --remove --yes (skip confirmation)"""
        with patch(
            "sys.argv", ["note_types.py", "--vault", str(temp_vault), "--remove", "area", "--yes"]
        ):
            from note_types import main

            main()

        with open(temp_vault / ".claude" / "settings.yaml") as f:
            settings = yaml.safe_load(f)
            assert "area" not in settings["note_types"]

    def test_main_wizard(self, temp_vault):
        """Test main with --wizard"""
        inputs = ["custom", "", "", "", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            with patch("sys.argv", ["note_types.py", "--vault", str(temp_vault), "--wizard"]):
                from note_types import main

                main()


class TestCorePropertiesIntegration:
    """Test that core properties are correctly applied to all generated files"""

    def test_get_core_properties_dict_format(self, temp_vault):
        """Test _get_core_properties with dict format"""
        manager = NoteTypesManager(str(temp_vault))
        core_props = manager.get_core_properties()
        assert core_props == ["type", "up", "created", "tags"]

    def test_get_core_properties_list_format(self, empty_dir):
        """Test _get_core_properties with list format"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],
            "note_types": {},
        }
        with open(settings_dir / "settings.yaml", "w") as f:
            yaml.safe_dump(settings, f)

        manager = NoteTypesManager(str(empty_dir))
        core_props = manager.get_core_properties()
        assert core_props == ["type", "up", "created"]

    def test_get_core_properties_fallback(self, empty_dir):
        """Test _get_core_properties with no core_properties defined"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings = {
            "version": "1.0",
            "methodology": "custom",
            "note_types": {},
        }
        with open(settings_dir / "settings.yaml", "w") as f:
            yaml.safe_dump(settings, f)

        manager = NoteTypesManager(str(empty_dir))
        core_props = manager.get_core_properties()
        assert core_props == ["type", "up", "created"]


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_properties_with_whitespace(self, temp_vault):
        """Test properties parsing with extra whitespace via wizard"""
        from note_type_wizard import interactive_type_definition

        inputs = ["Desc", "Folder/", "  type  ,  up  ", "  opt1  ,  opt2  ", "icon"]
        with patch("builtins.input", side_effect=inputs):
            definition = interactive_type_definition("custom")

        assert definition["properties"]["additional_required"] == ["type", "up"]
        assert definition["properties"]["optional"] == ["opt1", "opt2"]

    def test_core_properties_list_format(self, empty_dir):
        """Test handling core_properties as list (old format)"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],  # Old list format
            "note_types": {
                "test": {
                    "description": "Test",
                    "folder_hints": ["Test/"],
                    "properties": {"additional_required": [], "optional": []},
                    "validation": {},
                    "icon": "file",
                }
            },
        }
        with open(settings_file, "w") as f:
            yaml.safe_dump(settings, f)

        manager = NoteTypesManager(str(empty_dir))
        types = manager.list_types()  # Now returns dict, should not crash
        assert isinstance(types, dict)

    def test_show_type_with_template(self, temp_vault, capsys):
        """Test showing note type that has a template"""
        manager = NoteTypesManager(str(temp_vault))
        manager.note_types["project"]["template"] = "templates/project.md"

        capsys.readouterr()  # Clear __init__ output
        display_type_details(manager, "project")
        captured = capsys.readouterr()
        assert "templates/project.md" in captured.out

    def test_show_type_properties_list_format(self, temp_vault, capsys):
        """Test showing note type with properties as list"""
        manager = NoteTypesManager(str(temp_vault))
        manager.note_types["legacy"] = {
            "description": "Legacy format",
            "folder_hints": ["Legacy/"],
            "properties": ["type", "up", "custom"],
            "validation": {},
            "icon": "file",
        }

        capsys.readouterr()  # Clear __init__ output
        display_type_details(manager, "legacy")
        captured = capsys.readouterr()
        assert "type, up, custom" in captured.out

    def test_uses_cwd_when_no_vault(self, temp_vault):
        """Test that cwd is used when vault not specified"""
        with patch("pathlib.Path.cwd", return_value=temp_vault):
            manager = NoteTypesManager()
            assert manager.vault_path == temp_vault
