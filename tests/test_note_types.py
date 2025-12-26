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

    def test_edit_type_non_interactive(self, temp_vault):
        """Test editing note type non-interactively (for Claude Code)"""
        manager = NoteTypesManager(str(temp_vault))

        # Edit with specific parameters
        manager.edit_type(
            "project",
            interactive=False,
            description="Updated description",
            folder="NewProjects/",
            required_props=["status", "priority"],
            optional_props=["deadline"],
            icon="rocket",
        )

        config = manager.note_types["project"]
        assert config["description"] == "Updated description"
        assert config["folder_hints"] == ["NewProjects/"]
        assert config["properties"]["additional_required"] == ["status", "priority"]
        assert config["properties"]["optional"] == ["deadline"]
        assert config["icon"] == "rocket"

    def test_edit_type_non_interactive_partial(self, temp_vault):
        """Test non-interactive edit only updates provided fields"""
        manager = NoteTypesManager(str(temp_vault))

        original_folder = manager.note_types["project"]["folder_hints"]
        original_props = manager.note_types["project"]["properties"]

        # Only update description and icon
        manager.edit_type(
            "project",
            interactive=False,
            description="Just updated",
            icon="star",
        )

        config = manager.note_types["project"]
        assert config["description"] == "Just updated"
        assert config["icon"] == "star"
        # These should remain unchanged
        assert config["folder_hints"] == original_folder
        assert config["properties"] == original_props

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
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("# All\n\nExisting content\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        folder = temp_vault / "Blog"
        assert folder.exists()

    def test_add_creates_readme(self, temp_vault):
        """Test that add creates _Readme.md in folder"""
        bases_folder = temp_vault / "x" / "bases"
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
        """Test that add updates all_bases.base with YAML view"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        # Create proper YAML-formatted bases file
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        content = (bases_folder / "all_bases.base").read_text()
        assert "name: Blog" in content
        assert 'file.inFolder("Blog")' in content

    def test_remove_updates_bases_file(self, temp_vault):
        """Test that remove updates all_bases.base (YAML view format)"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        # Create YAML-formatted bases file with a Projects view
        bases_content = """views:
  - type: table
    name: All
  - type: table
    name: Projects
    filters:
      and:
        - file.inFolder("Projects")
    order:
      - file.name
      - type
      - up
"""
        (bases_folder / "all_bases.base").write_text(bases_content)

        manager = NoteTypesManager(str(temp_vault))
        manager.remove_type("project", skip_confirm=True)

        content = (bases_folder / "all_bases.base").read_text()
        assert "name: Projects" not in content
        assert "name: All" in content  # Other views should remain

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

    def test_reads_paths_from_folder_structure(self, temp_vault):
        """Test that paths are read from folder_structure setting"""
        manager = NoteTypesManager(str(temp_vault))
        # Reads from folder_structure.templates which is "x/templates/"
        assert manager.system_prefix == "x"
        assert manager.templates_folder == temp_vault / "x" / "templates"
        assert manager.bases_folder == temp_vault / "x" / "bases"

    def test_add_creates_template(self, temp_vault):
        """Test that add creates a template file (init skill format)"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        template = temp_vault / "x" / "templates" / "blog.md"
        assert template.exists()
        content = template.read_text()
        assert 'type: "blog"' in content  # Quoted value (init format)
        assert "{{title}}" in content
        assert "## Content" in content  # Template structure
        assert "## Related" in content

    def test_add_creates_sample_note(self, temp_vault):
        """Test that add creates a sample note (matches template structure)"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        sample = temp_vault / "Blog" / "Sample Blog.md"
        assert sample.exists()
        content = sample.read_text()
        assert 'type: "blog"' in content  # Quoted value (init format)
        assert "Sample Blog" in content
        assert "## Content" in content  # Matches template structure
        assert "## Related" in content


class TestCorePropertiesIntegration:
    """Test that core properties are correctly applied to all generated files"""

    def test_get_core_properties_dict_format(self, temp_vault):
        """Test _get_core_properties with dict format"""
        manager = NoteTypesManager(str(temp_vault))
        core_props = manager._get_core_properties()
        assert core_props == ["type", "up", "created", "tags"]

    def test_get_core_properties_list_format(self, empty_dir):
        """Test _get_core_properties with list format"""
        settings_dir = empty_dir / ".claude"
        settings_dir.mkdir(parents=True)
        settings = {
            "version": "1.0",
            "methodology": "custom",
            "core_properties": ["type", "up", "created"],  # List format
            "note_types": {},
        }
        with open(settings_dir / "settings.yaml", "w") as f:
            yaml.safe_dump(settings, f)

        manager = NoteTypesManager(str(empty_dir))
        core_props = manager._get_core_properties()
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
        core_props = manager._get_core_properties()
        assert core_props == ["type", "up", "created"]  # Default fallback

    def test_build_frontmatter_includes_core_properties(self, temp_vault):
        """Test _build_frontmatter includes all core properties"""
        manager = NoteTypesManager(str(temp_vault))
        config = {
            "properties": {
                "additional_required": ["status"],
                "optional": ["deadline"],
            }
        }
        frontmatter = manager._build_frontmatter("project", config, use_placeholders=False)

        # All core properties should be present
        assert "type: project" in frontmatter
        assert "up:" in frontmatter
        assert "created:" in frontmatter
        assert "tags:" in frontmatter
        # Additional required should be present
        assert "status:" in frontmatter

    def test_build_frontmatter_with_placeholders(self, temp_vault):
        """Test _build_frontmatter with template placeholders"""
        manager = NoteTypesManager(str(temp_vault))
        config = {"properties": {"additional_required": [], "optional": []}}
        frontmatter = manager._build_frontmatter("blog", config, use_placeholders=True)

        assert "type: blog" in frontmatter
        assert "{{date}}" in frontmatter
        assert 'up: ""' in frontmatter
        assert "tags: []" in frontmatter

    def test_template_has_all_core_properties(self, temp_vault):
        """Test that created template includes all core properties (init format)"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        template = temp_vault / "x" / "templates" / "blog.md"
        content = template.read_text()

        # All core properties should be in template (init format)
        assert 'type: "blog"' in content  # Quoted value
        assert 'up: "[[]]"' in content  # Empty link
        assert "created: {{date}}" in content  # Placeholder
        assert "tags: []" in content  # Empty array

    def test_sample_note_has_all_core_properties(self, temp_vault):
        """Test that created sample note includes all core properties (init format)"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        sample = temp_vault / "Blog" / "Sample Blog.md"
        content = sample.read_text()

        # All core properties should be in sample (init format, with values)
        assert 'type: "blog"' in content  # Quoted value
        assert 'up: "[[_Readme]]"' in content  # Link to readme
        assert "created:" in content  # Date filled in
        assert "tags: [blog]" in content  # Type tag

    def test_readme_has_init_format(self, temp_vault):
        """Test that created _Readme.md matches init skill format (simple MAP)"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        readme = temp_vault / "Blog" / "_Readme.md"
        content = readme.read_text()

        # Readme uses init skill's simple MAP format
        assert "type: map" in content
        assert 'created: "{{date}}"' in content  # Placeholder
        assert "## Contents" in content  # Section header
        assert "![[all_bases.base#Blog]]" in content  # Embed


class TestCompleteAddRemoveCycle:
    """Test full add/remove cycle verifies all artifacts are created and removed"""

    def test_add_creates_all_artifacts(self, temp_vault):
        """Test that add creates folder, readme, template, sample, and base view"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("meeting", interactive=False)

        # Check all artifacts exist
        assert (temp_vault / "Meeting").exists(), "Folder not created"
        assert (temp_vault / "Meeting" / "_Readme.md").exists(), "Readme not created"
        assert (temp_vault / "Meeting" / "Sample Meeting.md").exists(), "Sample not created"
        template = temp_vault / "x" / "templates" / "meeting.md"
        assert template.exists(), "Template not created"

        # Check base view (YAML format)
        bases_content = (bases_folder / "all_bases.base").read_text()
        assert "name: Meeting" in bases_content, "Base view not created"
        assert 'file.inFolder("Meeting")' in bases_content, "Base view filter not created"

    def test_remove_removes_all_artifacts(self, temp_vault):
        """Test that remove removes all created artifacts"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("meeting", interactive=False)

        # Verify artifacts exist before remove
        assert (temp_vault / "Meeting" / "_Readme.md").exists()
        assert (temp_vault / "Meeting" / "Sample Meeting.md").exists()
        assert (temp_vault / "x" / "templates" / "meeting.md").exists()

        # Remove the type
        manager.remove_type("meeting", skip_confirm=True)

        # Check all artifacts are removed
        template = temp_vault / "x" / "templates" / "meeting.md"
        assert not template.exists(), "Template not removed"
        assert not (temp_vault / "Meeting" / "_Readme.md").exists(), "Readme not removed"
        assert not (temp_vault / "Meeting" / "Sample Meeting.md").exists(), "Sample not removed"

        # Folder should be removed if empty
        assert not (temp_vault / "Meeting").exists(), "Empty folder not removed"

        # Base view should be removed (YAML format)
        bases_content = (bases_folder / "all_bases.base").read_text()
        assert "name: Meeting" not in bases_content, "Base view not removed"

    def test_remove_keeps_folder_with_other_files(self, temp_vault):
        """Test that remove keeps folder if it contains other files"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        (bases_folder / "all_bases.base").write_text("views:\n  - type: table\n    name: All\n")

        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("meeting", interactive=False)

        # Add an extra file to the folder
        (temp_vault / "Meeting" / "My Meeting.md").write_text("# My Meeting\n")

        manager.remove_type("meeting", skip_confirm=True)

        # Folder should still exist with the user's file
        assert (temp_vault / "Meeting").exists(), "Folder with user files was removed"
        assert (temp_vault / "Meeting" / "My Meeting.md").exists(), "User file was removed"
        # But readme and sample should be gone
        assert not (temp_vault / "Meeting" / "_Readme.md").exists()
        assert not (temp_vault / "Meeting" / "Sample Meeting.md").exists()

    def test_add_skips_bases_if_missing(self, temp_vault, capsys):
        """Test that add warns if all_bases.base doesn't exist (requires init)"""
        manager = NoteTypesManager(str(temp_vault))
        manager.add_type("blog", interactive=False)

        # Bases file should not be created - init must be run first
        bases_file = temp_vault / "x" / "bases" / "all_bases.base"
        assert not bases_file.exists(), "Bases file should not be auto-created"

        # Should print warning message
        captured = capsys.readouterr()
        assert "Base file not found" in captured.out
        assert "Run 'obsidian:init' first" in captured.out

    def test_remove_from_bases_handles_yaml_views(self, temp_vault):
        """Test that remove correctly handles YAML view entries"""
        bases_folder = temp_vault / "x" / "bases"
        bases_folder.mkdir(parents=True)
        bases_content = """views:
  - type: table
    name: All
  - type: table
    name: Projects
    filters:
      and:
        - file.inFolder("Projects")
    order:
      - file.name
      - type
      - up
  - type: table
    name: Areas
    filters:
      and:
        - file.inFolder("Areas")
    order:
      - file.name
      - type
      - up
"""
        (bases_folder / "all_bases.base").write_text(bases_content)

        manager = NoteTypesManager(str(temp_vault))
        manager._remove_from_bases_file("project", "Projects")

        content = (bases_folder / "all_bases.base").read_text()
        assert "name: Projects" not in content
        assert "name: Areas" in content
        assert 'file.inFolder("Areas")' in content


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
