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

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "note-types" / "scripts"))

from note_types import NoteTypesManager


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
        assert "No note types found" in captured.out
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
        manager.list_types()
        captured = capsys.readouterr()

        assert "Note Types (2)" in captured.out
        assert "project" in captured.out
        assert "area" in captured.out
        assert "Core properties:" in captured.out

    def test_list_types_empty(self, empty_dir, capsys):
        """Test listing when no note types exist"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.yaml"
        settings_file.write_text("version: '1.0'\nnote_types: {}\n")

        manager = NoteTypesManager(str(empty_dir))
        manager.list_types()
        captured = capsys.readouterr()
        assert "No note types defined" in captured.out

    def test_show_type_exists(self, temp_vault, capsys):
        """Test showing details for existing note type"""
        manager = NoteTypesManager(str(temp_vault))
        manager.show_type("project")
        captured = capsys.readouterr()

        assert "Note Type: project" in captured.out
        assert "Active projects" in captured.out
        assert "Projects/" in captured.out
        assert "status" in captured.out

    def test_show_type_not_exists(self, temp_vault, capsys):
        """Test showing non-existent note type"""
        manager = NoteTypesManager(str(temp_vault))
        with pytest.raises(SystemExit) as exc_info:
            manager.show_type("nonexistent")
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert "Available:" in captured.out

    def test_add_type_already_exists(self, temp_vault, capsys):
        """Test adding note type that already exists"""
        manager = NoteTypesManager(str(temp_vault))
        with pytest.raises(SystemExit) as exc_info:
            manager.add_type("project", interactive=False)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_add_type_non_interactive(self, temp_vault):
        """Test adding note type in non-interactive mode"""
        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("custom", interactive=False)

        assert "custom" in manager.note_types
        assert manager.note_types["custom"]["folder_hints"] == ["Custom/"]
        assert manager.note_types["custom"]["description"] == "Custom notes"

    def test_add_type_interactive(self, temp_vault):
        """Test adding note type in interactive mode"""
        manager = NoteTypesManager(str(temp_vault))

        inputs = [
            "Blog posts",  # description
            "Blog/Posts/",  # folder
            "author, published",  # required
            "featured",  # optional
            "pencil",  # icon
        ]
        with patch("builtins.input", side_effect=inputs):
            manager.add_type("blog", interactive=True)

        assert "blog" in manager.note_types
        assert manager.note_types["blog"]["folder_hints"] == ["Blog/Posts/"]
        assert manager.note_types["blog"]["properties"]["additional_required"] == [
            "author",
            "published",
        ]

    def test_edit_type_not_exists(self, temp_vault):
        """Test editing non-existent note type"""
        manager = NoteTypesManager(str(temp_vault))
        with pytest.raises(SystemExit) as exc_info:
            manager.edit_type("nonexistent")
        assert exc_info.value.code == 1

    def test_edit_type_interactive(self, temp_vault):
        """Test editing existing note type"""
        manager = NoteTypesManager(str(temp_vault))

        # Keep all defaults except icon
        inputs = ["", "", "", "", "rocket"]
        with patch("builtins.input", side_effect=inputs):
            manager.edit_type("project")

        assert manager.note_types["project"]["icon"] == "rocket"

    def test_remove_type_not_exists(self, temp_vault):
        """Test removing non-existent note type"""
        manager = NoteTypesManager(str(temp_vault))
        with pytest.raises(SystemExit) as exc_info:
            manager.remove_type("nonexistent")
        assert exc_info.value.code == 1

    def test_remove_type_cancelled(self, temp_vault):
        """Test removing note type but cancel"""
        manager = NoteTypesManager(str(temp_vault))
        with patch("builtins.input", return_value="n"):
            manager.remove_type("project")
        assert "project" in manager.note_types

    def test_remove_type_confirmed(self, temp_vault):
        """Test removing note type with confirmation"""
        manager = NoteTypesManager(str(temp_vault))
        with patch("builtins.input", return_value="y"):
            manager.remove_type("project")
        assert "project" not in manager.note_types

    def test_remove_type_skip_confirm(self, temp_vault):
        """Test removing note type with skip_confirm flag"""
        manager = NoteTypesManager(str(temp_vault))
        manager.remove_type("project", skip_confirm=True)
        assert "project" not in manager.note_types

    def test_interactive_type_definition_new(self, temp_vault):
        """Test interactive type definition for new type"""
        manager = NoteTypesManager(str(temp_vault))

        inputs = ["My custom notes", "Custom/Notes/", "author", "tags", "star"]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("custom")

        assert definition["description"] == "My custom notes"
        assert definition["folder_hints"] == ["Custom/Notes/"]
        assert definition["properties"]["additional_required"] == ["author"]
        assert definition["properties"]["optional"] == ["tags"]
        assert definition["icon"] == "star"

    def test_interactive_type_definition_keep_defaults(self, temp_vault):
        """Test interactive type definition keeping defaults"""
        manager = NoteTypesManager(str(temp_vault))
        existing = manager.note_types["project"]

        # Press Enter for all (keep defaults)
        inputs = ["", "", "", "", ""]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("project", existing)

        assert definition["description"] == existing["description"]
        assert definition["folder_hints"] == existing["folder_hints"]

    def test_interactive_type_definition_none_properties(self, temp_vault):
        """Test interactive type definition with 'none' for properties"""
        manager = NoteTypesManager(str(temp_vault))

        inputs = ["Simple notes", "Simple/", "none", "none", "file"]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("simple")

        assert definition["properties"]["additional_required"] == []
        assert definition["properties"]["optional"] == []

    def test_wizard_success(self, temp_vault):
        """Test wizard mode successful creation"""
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
            manager.wizard()

        assert "meeting" in manager.note_types

    def test_wizard_cancelled(self, temp_vault):
        """Test wizard mode cancellation"""
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
            manager.wizard()

        assert "meeting" not in manager.note_types

    def test_wizard_empty_name_retry(self, temp_vault):
        """Test wizard with empty name retries"""
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
            manager.wizard()

        assert "meeting" in manager.note_types

    def test_wizard_duplicate_name_retry(self, temp_vault):
        """Test wizard with duplicate name retries"""
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
            manager.wizard()

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

    def test_main_edit(self, temp_vault):
        """Test main with --edit"""
        inputs = ["", "", "", "", ""]  # Keep all defaults
        with patch("builtins.input", side_effect=inputs):
            with patch(
                "sys.argv", ["note_types.py", "--vault", str(temp_vault), "--edit", "project"]
            ):
                from note_types import main

                main()

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


class TestVaultStructure:
    """Test vault structure creation"""

    def test_add_creates_folder(self, temp_vault):
        """Test that add creates the folder"""
        # Create bases folder and file
        bases_folder = temp_vault / "_system" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("# All\n\nExisting content\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        folder = temp_vault / "Blog"
        assert folder.exists()

    def test_add_creates_readme(self, temp_vault):
        """Test that add creates _Readme.md in folder"""
        bases_folder = temp_vault / "_system" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("# All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        readme = temp_vault / "Blog" / "_Readme.md"
        assert readme.exists()
        content = readme.read_text()
        assert "type: map" in content
        assert "Blog" in content

    def test_add_updates_bases_file(self, temp_vault):
        """Test that add updates all_bases.base"""
        bases_folder = temp_vault / "_system" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("# All\n\nExisting\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        content = (bases_folder / "all_bases.base").read_text()
        assert "# Blog" in content
        assert 'FROM "Blog"' in content

    def test_remove_updates_bases_file(self, temp_vault):
        """Test that remove updates all_bases.base"""
        bases_folder = temp_vault / "_system" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text(
            "# All\n\n# Project\n\n```dataview\nFROM Projects\n```\n"
        )

        manager = NoteTypesManager(str(temp_vault))
        manager.remove_type("project", skip_confirm=True)

        content = (bases_folder / "all_bases.base").read_text()
        assert "# Project" not in content

    def test_lyt_methodology_uses_x_prefix(self, empty_dir):
        """Test that LYT methodology uses x/ prefix"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings = {
            "version": "1.0",
            "methodology": "lyt-ace",
            "note_types": {"map": {"folder_hints": ["Atlas/Maps/"]}},
        }
        with open(settings_dir / "settings.yaml", "w") as f:
            yaml.safe_dump(settings, f)

        manager = NoteTypesManager(str(empty_dir))
        assert manager.system_prefix == "x"

    def test_para_methodology_uses_system_prefix(self, temp_vault):
        """Test that PARA methodology uses _system/ prefix"""
        manager = NoteTypesManager(str(temp_vault))
        assert manager.system_prefix == "_system"

    def test_add_creates_template(self, temp_vault):
        """Test that add creates a template file"""
        bases_folder = temp_vault / "_system" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("# All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        template = temp_vault / "_system" / "templates" / "blog.md"
        assert template.exists()
        content = template.read_text()
        assert "type: blog" in content
        assert "{{title}}" in content

    def test_add_creates_sample_note(self, temp_vault):
        """Test that add creates a sample note"""
        bases_folder = temp_vault / "_system" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("# All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        sample = temp_vault / "Blog" / "Sample Blog.md"
        assert sample.exists()
        content = sample.read_text()
        assert "type: blog" in content
        assert "Sample Blog" in content


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_properties_with_whitespace(self, temp_vault):
        """Test properties parsing with extra whitespace"""
        manager = NoteTypesManager(str(temp_vault))

        inputs = ["Desc", "Folder/", "  type  ,  up  ", "  opt1  ,  opt2  ", "icon"]
        with patch("builtins.input", side_effect=inputs):
            definition = manager._interactive_type_definition("custom")

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
        manager.list_types()  # Should not crash

    def test_show_type_with_template(self, temp_vault, capsys):
        """Test showing note type that has a template"""
        manager = NoteTypesManager(str(temp_vault))
        manager.note_types["project"]["template"] = "templates/project.md"

        manager.show_type("project")
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

        manager.show_type("legacy")
        captured = capsys.readouterr()
        assert "type, up, custom" in captured.out

    def test_uses_cwd_when_no_vault(self, temp_vault):
        """Test that cwd is used when vault not specified"""
        with patch("pathlib.Path.cwd", return_value=temp_vault):
            manager = NoteTypesManager()
            assert manager.vault_path == temp_vault
