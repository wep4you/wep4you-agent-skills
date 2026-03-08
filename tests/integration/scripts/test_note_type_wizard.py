"""Tests for note_type_wizard.py - Interactive and vault operations for note types."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add the scripts path for imports
_SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "note-types" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture
def temp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault with settings."""
    # Create .claude directory
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    # Create settings.yaml
    settings = claude_dir / "settings.yaml"
    settings.write_text(
        """
methodology: lyt-ace
core_properties:
  all:
    - type
    - up
    - created
    - tags
note_types:
  project:
    description: "Project notes"
    folder_hints:
      - "Projects/"
    properties:
      additional_required:
        - status
      optional: []
    icon: target
folder_structure:
  templates: "x/templates/"
  bases: "x/bases/"
"""
    )

    # Create templates folder
    templates_dir = tmp_path / "x" / "templates"
    templates_dir.mkdir(parents=True)

    # Create bases folder
    bases_dir = tmp_path / "x" / "bases"
    bases_dir.mkdir(parents=True)

    # Create all_bases.base
    all_bases = bases_dir / "all_bases.base"
    all_bases.write_text(
        """views:
- type: table
  name: All
  columns:
    - file.name
"""
    )

    return tmp_path


@pytest.fixture
def manager(temp_vault: Path) -> MagicMock:
    """Create a mock NoteTypesManager."""
    from note_types import NoteTypesManager

    return NoteTypesManager(str(temp_vault))


class TestVaultStructureManager:
    """Tests for VaultStructureManager class."""

    def test_init(self, temp_vault: Path) -> None:
        """Test VaultStructureManager initialization."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        assert vsm.vault_path == temp_vault
        assert vsm.templates_folder == temp_vault / "x" / "templates"
        assert vsm.bases_folder == temp_vault / "x" / "bases"
        assert vsm.system_prefix == "x"
        assert vsm.core_properties == ["type", "up", "created"]

    def test_create_structure_creates_folder(self, temp_vault: Path) -> None:
        """Test that create_structure creates the folder."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "description": "Test notes",
            "folder_hints": ["Test/"],
            "properties": {"additional_required": [], "optional": []},
            "icon": "file",
        }

        vsm.create_structure("test", config)

        assert (temp_vault / "Test").exists()

    def test_create_structure_creates_template(self, temp_vault: Path) -> None:
        """Test that create_structure creates the template."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "description": "Test notes",
            "folder_hints": ["Test/"],
            "properties": {"additional_required": [], "optional": []},
            "icon": "file",
        }

        vsm.create_structure("test", config)

        template_path = temp_vault / "x" / "templates" / "test.md"
        assert template_path.exists()
        content = template_path.read_text()
        assert 'type: "test"' in content

    def test_create_structure_creates_sample_note(self, temp_vault: Path) -> None:
        """Test that create_structure creates a sample note."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "description": "Test notes",
            "folder_hints": ["Test/"],
            "properties": {"additional_required": [], "optional": []},
            "icon": "file",
        }

        vsm.create_structure("test", config)

        sample_path = temp_vault / "Test" / "Sample Test.md"
        assert sample_path.exists()

    def test_create_structure_creates_moc(self, temp_vault: Path) -> None:
        """Test that create_structure creates an MOC file."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "description": "Test notes",
            "folder_hints": ["Test/"],
            "properties": {"additional_required": [], "optional": []},
            "icon": "file",
        }

        vsm.create_structure("test", config)

        moc_path = temp_vault / "Test" / "_Test_MOC.md"
        assert moc_path.exists()

    def test_create_structure_updates_bases(self, temp_vault: Path) -> None:
        """Test that create_structure updates all_bases.base."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "description": "Test notes",
            "folder_hints": ["Test/"],
            "properties": {"additional_required": [], "optional": []},
            "icon": "file",
        }

        vsm.create_structure("test", config)

        bases_content = (temp_vault / "x" / "bases" / "all_bases.base").read_text()
        assert "name: Test" in bases_content

    def test_remove_structure_removes_folder(self, temp_vault: Path) -> None:
        """Test that remove_structure removes folder."""
        from note_type_wizard import VaultStructureManager

        # Create folder to remove
        folder = temp_vault / "ToRemove"
        folder.mkdir()

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "folder_hints": ["ToRemove/"],
        }

        vsm.remove_structure("toremove", config, remove_folder=True)

        assert not folder.exists()

    def test_remove_structure_removes_template(self, temp_vault: Path) -> None:
        """Test that remove_structure removes template."""
        from note_type_wizard import VaultStructureManager

        # Create template to remove
        template_path = temp_vault / "x" / "templates" / "toremove.md"
        template_path.write_text("---\ntype: toremove\n---\n")

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        vsm.remove_structure("toremove", {}, remove_folder=False)

        assert not template_path.exists()

    def test_remove_structure_keeps_folder_with_files(self, temp_vault: Path) -> None:
        """Test that remove_structure keeps folder if it has files."""
        from note_type_wizard import VaultStructureManager

        # Create folder with file
        folder = temp_vault / "ToRemove"
        folder.mkdir()
        (folder / "important.md").write_text("Important content")

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {"folder_hints": ["ToRemove/"]}

        vsm.remove_structure("toremove", config, remove_folder=True)

        # Folder should still exist because it has files
        assert folder.exists()

    def test_rename_folder(self, temp_vault: Path) -> None:
        """Test folder renaming."""
        from note_type_wizard import VaultStructureManager

        # Create old folder
        old_folder = temp_vault / "OldName"
        old_folder.mkdir()

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        vsm.rename_folder("test", "OldName", "NewName")

        assert not old_folder.exists()
        assert (temp_vault / "NewName").exists()

    def test_rename_folder_creates_if_old_missing(self, temp_vault: Path) -> None:
        """Test that rename_folder creates new folder if old doesn't exist."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        vsm.rename_folder("test", "NonExistent", "NewFolder")

        assert (temp_vault / "NewFolder").exists()

    def test_rename_folder_skips_if_target_exists(self, temp_vault: Path) -> None:
        """Test that rename_folder skips if target already exists."""
        from note_type_wizard import VaultStructureManager

        # Create both folders
        old_folder = temp_vault / "OldName"
        old_folder.mkdir()
        new_folder = temp_vault / "NewName"
        new_folder.mkdir()

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        vsm.rename_folder("test", "OldName", "NewName")

        # Both folders should still exist
        assert old_folder.exists()
        assert new_folder.exists()

    def test_update_template(self, temp_vault: Path) -> None:
        """Test template updating."""
        from note_type_wizard import VaultStructureManager

        # Create template
        template_path = temp_vault / "x" / "templates" / "test.md"
        template_path.write_text(
            """---
type: "test"
up: ""
created: {{date}}
---

> Template for test notes
"""
        )

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "description": "Updated description",
            "properties": {"additional_required": ["newprop"], "optional": []},
        }

        vsm.update_template("test", config)

        content = template_path.read_text()
        assert "newprop:" in content

    def test_update_notes_frontmatter(self, temp_vault: Path) -> None:
        """Test updating frontmatter in existing notes."""
        from note_type_wizard import VaultStructureManager

        # Create folder and note
        folder = temp_vault / "TestNotes"
        folder.mkdir()
        note_path = folder / "test.md"
        note_path.write_text(
            """---
type: test
up: ""
created: 2025-01-01
---

Content
"""
        )

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "properties": {"additional_required": ["newprop"], "optional": []},
        }

        vsm.update_notes_frontmatter("test", config, folder)

        content = note_path.read_text()
        assert "newprop:" in content

    def test_update_notes_frontmatter_skips_moc(self, temp_vault: Path) -> None:
        """Test that update_notes_frontmatter skips MOC files."""
        from note_type_wizard import VaultStructureManager

        # Create folder and MOC
        folder = temp_vault / "TestNotes"
        folder.mkdir()
        moc_path = folder / "_TestNotes_MOC.md"
        original_content = """---
type: map
---
# MOC
"""
        moc_path.write_text(original_content)

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {
            "properties": {"additional_required": ["newprop"], "optional": []},
        }

        vsm.update_notes_frontmatter("test", config, folder)

        # MOC should be unchanged
        content = moc_path.read_text()
        assert "newprop:" not in content


class TestCliHandlers:
    """Tests for CLI command handlers."""

    def test_handle_add_with_json_config(self, manager: MagicMock) -> None:
        """Test handle_add with JSON config."""
        from note_type_wizard import handle_add

        config_json = '{"description": "Meeting notes", "folder": "Meetings/"}'

        handle_add(manager, "meeting", config_json, non_interactive=True)

        assert "meeting" in manager.note_types

    def test_handle_add_non_interactive(self, manager: MagicMock) -> None:
        """Test handle_add in non-interactive mode."""
        from note_type_wizard import handle_add

        handle_add(manager, "blog", None, non_interactive=True)

        assert "blog" in manager.note_types

    def test_handle_add_with_invalid_json(self, manager: MagicMock) -> None:
        """Test handle_add with invalid JSON."""
        from note_type_wizard import handle_add

        with pytest.raises(SystemExit):
            handle_add(manager, "test", "{invalid", non_interactive=True)

    def test_handle_edit_with_json_config(self, manager: MagicMock) -> None:
        """Test handle_edit with JSON config."""
        from note_type_wizard import handle_edit

        # Create args namespace
        args = MagicMock()
        args.description = None
        args.folder = None
        args.required_props = None
        args.optional_props = None
        args.icon = None

        config_json = '{"description": "Updated project notes"}'

        handle_edit(manager, "project", config_json, non_interactive=True, args=args)

        assert manager.note_types["project"]["description"] == "Updated project notes"

    def test_handle_edit_non_interactive_with_args(self, manager: MagicMock) -> None:
        """Test handle_edit with CLI arguments."""
        from note_type_wizard import handle_edit

        args = MagicMock()
        args.description = "New description"
        args.folder = "NewFolder/"
        args.required_props = "prop1,prop2"
        args.optional_props = None
        args.icon = "star"

        handle_edit(manager, "project", None, non_interactive=True, args=args)

        updated = manager.note_types["project"]
        assert updated["description"] == "New description"
        assert updated["icon"] == "star"

    def test_handle_edit_not_found(self, manager: MagicMock) -> None:
        """Test handle_edit with non-existent type."""
        from note_type_wizard import handle_edit

        args = MagicMock()

        with pytest.raises(SystemExit):
            handle_edit(manager, "nonexistent", None, non_interactive=True, args=args)

    def test_handle_remove_with_skip_confirm(self, manager: MagicMock) -> None:
        """Test handle_remove with --yes flag."""
        from note_type_wizard import handle_remove

        handle_remove(manager, "project", skip_confirm=True)

        assert "project" not in manager.note_types

    def test_handle_remove_not_found(self, manager: MagicMock) -> None:
        """Test handle_remove with non-existent type."""
        from note_type_wizard import handle_remove

        with pytest.raises(SystemExit):
            handle_remove(manager, "nonexistent", skip_confirm=True)

    def test_handle_remove_cancelled(self, manager: MagicMock) -> None:
        """Test handle_remove when user cancels."""
        from note_type_wizard import handle_remove

        with patch("builtins.input", return_value="n"):
            handle_remove(manager, "project", skip_confirm=False)

        # Project should still exist
        assert "project" in manager.note_types


class TestInteractiveTypeDef:
    """Tests for interactive_type_definition function."""

    def test_with_defaults(self) -> None:
        """Test interactive_type_definition using defaults."""
        from note_type_wizard import interactive_type_definition

        inputs = ["", "", "", "", ""]  # Press Enter for all prompts
        with patch("builtins.input", side_effect=inputs):
            result = interactive_type_definition("test")

        assert result["description"] == "Test notes"
        assert result["folder_hints"] == ["Test/"]
        assert result["icon"] == "file"

    def test_with_custom_values(self) -> None:
        """Test interactive_type_definition with custom input."""
        from note_type_wizard import interactive_type_definition

        inputs = ["Custom description", "CustomFolder/", "prop1, prop2", "opt1", "star"]
        with patch("builtins.input", side_effect=inputs):
            result = interactive_type_definition("custom")

        assert result["description"] == "Custom description"
        assert result["folder_hints"] == ["CustomFolder/"]
        assert result["properties"]["additional_required"] == ["prop1", "prop2"]
        assert result["properties"]["optional"] == ["opt1"]
        assert result["icon"] == "star"

    def test_with_existing_config(self) -> None:
        """Test interactive_type_definition with existing config."""
        from note_type_wizard import interactive_type_definition

        existing = {
            "description": "Existing desc",
            "folder_hints": ["ExistingFolder/"],
            "properties": {"additional_required": ["existing"], "optional": []},
            "icon": "rocket",
        }

        inputs = ["", "", "", "", ""]  # Accept all defaults
        with patch("builtins.input", side_effect=inputs):
            result = interactive_type_definition("test", existing)

        assert result["description"] == "Existing desc"
        assert result["folder_hints"] == ["ExistingFolder/"]
        assert result["properties"]["additional_required"] == ["existing"]
        assert result["icon"] == "rocket"

    def test_with_none_values(self) -> None:
        """Test interactive_type_definition with 'none' for properties."""
        from note_type_wizard import interactive_type_definition

        inputs = ["", "", "none", "none", ""]
        with patch("builtins.input", side_effect=inputs):
            result = interactive_type_definition("test")

        assert result["properties"]["additional_required"] == []
        assert result["properties"]["optional"] == []


class TestWizard:
    """Tests for wizard functions."""

    def test_run_wizard_create_new(self) -> None:
        """Test wizard creating new type."""
        from note_type_wizard import run_wizard

        created = []

        def on_create(name: str, config: dict) -> None:
            created.append((name, config))

        existing_types = {}
        # name, description, folders, required, optional, icon, confirm
        inputs = ["blog", "", "", "", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            run_wizard(existing_types, on_create)

        assert len(created) == 1
        assert created[0][0] == "blog"

    def test_run_wizard_cancel(self) -> None:
        """Test wizard cancellation."""
        from note_type_wizard import run_wizard

        created = []

        def on_create(name: str, config: dict) -> None:
            created.append((name, config))

        existing_types = {}
        # name, description, folders, required, optional, icon, confirm=n
        inputs = ["blog", "", "", "", "", "", "n"]
        with patch("builtins.input", side_effect=inputs):
            run_wizard(existing_types, on_create)

        assert len(created) == 0

    def test_run_wizard_duplicate_name(self) -> None:
        """Test wizard with duplicate name."""
        from note_type_wizard import run_wizard

        created = []

        def on_create(name: str, config: dict) -> None:
            created.append((name, config))

        existing_types = {"project": {"description": "Projects"}}
        # First try duplicate, then use valid name
        inputs = ["project", "blog", "", "", "", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            run_wizard(existing_types, on_create)

        assert len(created) == 1
        assert created[0][0] == "blog"

    def test_run_wizard_empty_name(self) -> None:
        """Test wizard with empty name."""
        from note_type_wizard import run_wizard

        created = []

        def on_create(name: str, config: dict) -> None:
            created.append((name, config))

        existing_types = {}
        # Empty name first, then valid
        inputs = ["", "blog", "", "", "", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            run_wizard(existing_types, on_create)

        assert len(created) == 1


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_vault_manager(self, manager: MagicMock) -> None:
        """Test _create_vault_manager."""
        from note_type_wizard import _create_vault_manager

        vault_mgr = _create_vault_manager(manager)

        assert vault_mgr.vault_path == manager.vault_path
        assert vault_mgr.templates_folder == manager.templates_folder

    def test_get_additional_properties(self, temp_vault: Path) -> None:
        """Test _get_additional_properties with various configs."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        # Test with dict properties
        config1 = {"properties": {"additional_required": ["status"], "optional": ["notes"]}}
        req, opt = vsm._get_additional_properties(config1)
        assert req == ["status"]
        assert opt == ["notes"]

        # Test with list properties
        config2 = {"properties": ["prop1", "prop2"]}
        req, opt = vsm._get_additional_properties(config2)
        assert req == ["prop1", "prop2"]
        assert opt == []

        # Test with no properties
        config3 = {}
        req, opt = vsm._get_additional_properties(config3)
        assert req == []
        assert opt == []


class TestVaultStructureManagerExtended:
    """Extended tests for uncovered paths in VaultStructureManager."""

    def _make_vsm(self, temp_vault: Path) -> Any:
        """Helper to create a VaultStructureManager."""
        from note_type_wizard import VaultStructureManager

        return VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created", "tags", "daily", "collection", "related"],
        )

    def test_create_structure_default_folder_hints(self, temp_vault: Path) -> None:
        """Test create_structure generates default folder_hints if missing."""
        vsm = self._make_vsm(temp_vault)
        config: dict[str, Any] = {
            "description": "Test notes",
            "properties": {"additional_required": [], "optional": []},
        }

        vsm.create_structure("blog", config)

        assert (temp_vault / "Blog").exists()
        assert config["folder_hints"] == ["Blog/"]

    def test_create_moc_already_exists(self, temp_vault: Path) -> None:
        """Test _create_moc skips if MOC already exists."""
        vsm = self._make_vsm(temp_vault)
        folder = temp_vault / "Test"
        folder.mkdir()
        moc_path = folder / "_Test_MOC.md"
        moc_path.write_text("# Existing MOC")

        config = {"description": "Test", "folder_hints": ["Test/"]}
        vsm._create_moc("test", config, folder)

        assert moc_path.read_text() == "# Existing MOC"

    def test_update_bases_view_already_exists(
        self, temp_vault: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test _update_bases_file skips if view already exists."""
        vsm = self._make_vsm(temp_vault)

        vsm._update_bases_file("test", "Test")
        vsm._update_bases_file("test", "Test")

        assert "already exists" in capsys.readouterr().out

    def test_create_template_already_exists(
        self, temp_vault: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test _create_template skips if template exists."""
        vsm = self._make_vsm(temp_vault)
        template_path = temp_vault / "x" / "templates" / "test.md"
        template_path.write_text("existing")

        config = {"description": "Test", "properties": {}}
        vsm._create_template("test", config)

        assert "already exists" in capsys.readouterr().out

    def test_create_template_with_all_property_types(self, temp_vault: Path) -> None:
        """Test _create_template handles all core property types."""
        vsm = self._make_vsm(temp_vault)

        config = {
            "description": "Test notes",
            "properties": {
                "additional_required": ["status", "custom_field"],
                "optional": ["opt1"],
            },
        }

        vsm._create_template("test", config)

        content = (temp_vault / "x" / "templates" / "test.md").read_text()
        assert 'up: "[[{{up}}]]"' in content
        assert "created: {{date}}" in content
        assert "tags: []" in content
        assert "daily: " in content
        assert "collection: " in content
        assert "related: []" in content
        assert 'status: "active"' in content
        assert "custom_field: " in content
        assert "opt1: " in content

    def test_create_sample_note_already_exists(
        self, temp_vault: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Test _create_sample_note skips if sample exists."""
        vsm = self._make_vsm(temp_vault)
        folder = temp_vault / "Test"
        folder.mkdir()
        sample = folder / "Sample Test.md"
        sample.write_text("existing")

        config = {"description": "Test", "properties": {}}
        vsm._create_sample_note("test", config, folder)

        assert "already exists" in capsys.readouterr().out

    def test_create_sample_note_with_all_properties(self, temp_vault: Path) -> None:
        """Test _create_sample_note handles all core property types and custom props."""
        vsm = self._make_vsm(temp_vault)
        folder = temp_vault / "Test"
        folder.mkdir()

        config = {
            "description": "Test notes",
            "properties": {
                "additional_required": ["status", "source"],
                "optional": ["rating"],
            },
        }

        vsm._create_sample_note("test", config, folder)

        content = (folder / "Sample Test.md").read_text()
        assert 'type: "test"' in content
        assert "daily:" in content
        assert "collection:" in content
        assert "related: []" in content
        assert 'status: "active"' in content
        assert "source: " in content
        assert "rating: " in content

    def test_remove_structure_removes_sample_and_moc(self, temp_vault: Path) -> None:
        """Test remove_structure removes sample note and MOC file."""
        vsm = self._make_vsm(temp_vault)
        folder = temp_vault / "Blog"
        folder.mkdir()

        sample = folder / "Sample Blog.md"
        sample.write_text("---\ntype: blog\n---")
        moc = folder / "_Blog_MOC.md"
        moc.write_text("---\ntype: map\n---")

        config = {"folder_hints": ["Blog/"]}
        vsm.remove_structure("blog", config, remove_folder=True)

        assert not sample.exists()
        assert not moc.exists()
        assert not folder.exists()

    def test_remove_from_bases_file_removes_view(self, temp_vault: Path) -> None:
        """Test _remove_from_bases_file correctly removes a view entry."""
        vsm = self._make_vsm(temp_vault)

        vsm._update_bases_file("blog", "Blog")

        bases = temp_vault / "x" / "bases" / "all_bases.base"
        assert "name: Blog" in bases.read_text()

        vsm._remove_from_bases_file("blog", "Blog")

        assert "name: Blog" not in bases.read_text()

    def test_remove_from_bases_file_no_folder(self, temp_vault: Path) -> None:
        """Test _remove_from_bases_file uses capitalized name when no folder."""
        vsm = self._make_vsm(temp_vault)

        vsm._update_bases_file("blog", "Blog")
        vsm._remove_from_bases_file("blog", None)

        bases = temp_vault / "x" / "bases" / "all_bases.base"
        assert "name: Blog" not in bases.read_text()

    def test_rename_folder_os_error(self, temp_vault: Path, capsys: pytest.CaptureFixture) -> None:
        """Test rename_folder handles OSError."""
        vsm = self._make_vsm(temp_vault)
        old_folder = temp_vault / "OldName"
        old_folder.mkdir()

        with patch.object(Path, "rename", side_effect=OSError("Permission denied")):
            vsm.rename_folder("test", "OldName", "NewName")

        assert "Failed to rename" in capsys.readouterr().out

    def test_rename_folder_with_moc(self, temp_vault: Path) -> None:
        """Test rename_folder updates MOC file during rename."""
        vsm = self._make_vsm(temp_vault)
        old_folder = temp_vault / "OldName"
        old_folder.mkdir()
        moc = old_folder / "_OldName_MOC.md"
        moc.write_text("# OldName\n![[all_bases.base##OldName]]")

        vsm.rename_folder("test", "OldName", "NewName")

        new_moc = temp_vault / "NewName" / "_NewName_MOC.md"
        assert new_moc.exists()
        content = new_moc.read_text()
        assert "# NewName" in content

    def test_update_template_no_frontmatter(self, temp_vault: Path) -> None:
        """Test update_template with no frontmatter in template."""
        vsm = self._make_vsm(temp_vault)
        template = temp_vault / "x" / "templates" / "test.md"
        template.write_text("No frontmatter here")

        vsm.update_template("test", {"properties": {}})

        assert template.read_text() == "No frontmatter here"

    def test_update_template_incomplete_frontmatter(self, temp_vault: Path) -> None:
        """Test update_template with only one --- delimiter."""
        vsm = self._make_vsm(temp_vault)
        template = temp_vault / "x" / "templates" / "test.md"
        template.write_text("---\nincomplete")

        vsm.update_template("test", {"properties": {}})

        assert template.read_text() == "---\nincomplete"

    def test_update_template_full_rebuild(self, temp_vault: Path) -> None:
        """Test update_template rebuilds frontmatter with all properties."""
        vsm = self._make_vsm(temp_vault)
        template = temp_vault / "x" / "templates" / "test.md"
        template.write_text(
            '---\ntype: "test"\n---\n\n# Test\n\n> Template for **Test** notes: Old desc\n'
        )

        config = {
            "description": "New desc",
            "properties": {
                "additional_required": ["status", "custom"],
                "optional": ["opt1"],
            },
        }
        vsm.update_template("test", config)

        content = template.read_text()
        assert "daily:" in content
        assert "collection:" in content
        assert "related: []" in content
        assert 'status: "active"' in content
        assert "custom:" in content
        assert "opt1:" in content
        assert "New desc" in content

    def test_update_notes_frontmatter_adds_missing_props(self, temp_vault: Path) -> None:
        """Test update_notes_frontmatter adds properties to notes."""
        vsm = self._make_vsm(temp_vault)
        folder = temp_vault / "Notes"
        folder.mkdir()

        note = folder / "test.md"
        note.write_text("---\ntype: test\n---\n\nContent")

        config = {
            "properties": {"additional_required": ["status"], "optional": ["rating"]},
        }
        vsm.update_notes_frontmatter("test", config, folder)

        content = note.read_text()
        assert "status:" in content
        assert "rating:" in content

    def test_update_notes_frontmatter_no_changes_needed(self, temp_vault: Path) -> None:
        """Test update_notes_frontmatter skips notes with all properties present."""
        vsm = self._make_vsm(temp_vault)
        folder = temp_vault / "Notes"
        folder.mkdir()

        note = folder / "test.md"
        note.write_text(
            '---\ntype: test\nup: ""\ncreated: 2025-01-01\ntags: []\n'
            "daily: \ncollection: \nrelated: []\n---\n\nContent"
        )

        config = {"properties": {"additional_required": [], "optional": []}}
        vsm.update_notes_frontmatter("test", config, folder)

        # Note should be unchanged (no missing props)

    def test_update_notes_frontmatter_nonexistent_folder(self, temp_vault: Path) -> None:
        """Test update_notes_frontmatter with nonexistent folder."""
        vsm = self._make_vsm(temp_vault)
        folder = temp_vault / "NonExistent"

        vsm.update_notes_frontmatter("test", {"properties": {}}, folder)
        # Should not raise


class TestCliHandlersExtended:
    """Extended tests for CLI handler coverage."""

    def test_handle_add_interactive(self, manager: MagicMock) -> None:
        """Test handle_add in interactive mode."""
        from note_type_wizard import handle_add

        inputs = ["Meeting notes", "Meetings/", "none", "none", "calendar"]
        with patch("builtins.input", side_effect=inputs):
            handle_add(manager, "meeting", None, non_interactive=False)

        assert "meeting" in manager.note_types

    def test_handle_edit_interactive(self, manager: MagicMock) -> None:
        """Test handle_edit in interactive mode."""
        from note_type_wizard import handle_edit

        args = MagicMock()
        inputs = ["Updated desc", "", "", "", ""]
        with patch("builtins.input", side_effect=inputs):
            handle_edit(manager, "project", None, non_interactive=False, args=args)

    def test_handle_edit_non_interactive_all_args(self, manager: MagicMock) -> None:
        """Test handle_edit with all CLI args set."""
        from note_type_wizard import handle_edit

        args = MagicMock()
        args.description = "New desc"
        args.folder = "NewFolder/"
        args.required_props = "a,b"
        args.optional_props = "c,d"
        args.icon = "star"

        handle_edit(manager, "project", None, non_interactive=True, args=args)

        updated = manager.note_types["project"]
        assert updated["description"] == "New desc"

    def test_handle_remove_confirmed(self, manager: MagicMock) -> None:
        """Test handle_remove with user confirmation."""
        from note_type_wizard import handle_remove

        with patch("builtins.input", return_value="y"):
            handle_remove(manager, "project", skip_confirm=False)

        assert "project" not in manager.note_types

    def test_handle_wizard(self, manager: MagicMock) -> None:
        """Test handle_wizard creates type via wizard."""
        from note_type_wizard import handle_wizard

        # name, desc, folders, required, optional, icon, confirm
        inputs = ["newtype", "", "", "", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            handle_wizard(manager)

        assert "newtype" in manager.note_types


class TestInteractiveTypeDefExtended:
    """Extended tests for interactive_type_definition edge cases."""

    def test_with_list_properties(self) -> None:
        """Test interactive_type_definition when existing has list-style properties."""
        from note_type_wizard import interactive_type_definition

        existing = {
            "description": "Test",
            "folder_hints": ["Test/"],
            "properties": ["prop1", "prop2"],
            "icon": "file",
        }

        inputs = ["", "", "", "", ""]
        with patch("builtins.input", side_effect=inputs):
            result = interactive_type_definition("test", existing)

        assert result["properties"]["additional_required"] == ["prop1", "prop2"]
        assert result["properties"]["optional"] == []


class TestRunWizardExtended:
    """Extended tests for run_wizard."""

    def test_run_wizard_with_required_properties(self) -> None:
        """Test run_wizard prints required and optional in summary."""
        from note_type_wizard import run_wizard

        created = []

        def on_create(name: str, config: dict) -> None:
            created.append((name, config))

        # name, desc, folders, required, optional, icon, confirm
        inputs = ["blog", "Blog posts", "Blogs/", "author, category", "rating", "pen", "y"]
        with patch("builtins.input", side_effect=inputs):
            run_wizard({}, on_create)

        assert len(created) == 1
        assert created[0][1]["properties"]["additional_required"] == ["author", "category"]
        assert created[0][1]["properties"]["optional"] == ["rating"]


class TestEdgeCases:
    """Tests for edge cases."""

    def test_create_structure_missing_bases_folder(self, temp_vault: Path) -> None:
        """Test create_structure when bases folder doesn't exist."""
        # Remove bases folder
        import shutil

        from note_type_wizard import VaultStructureManager

        shutil.rmtree(temp_vault / "x" / "bases")

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        config = {"description": "Test", "folder_hints": ["Test/"], "properties": {}}

        # Should not raise
        vsm.create_structure("test", config)

    def test_remove_from_bases_no_match(self, temp_vault: Path) -> None:
        """Test _remove_from_bases_file when view doesn't exist."""
        from note_type_wizard import VaultStructureManager

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        original_content = (temp_vault / "x" / "bases" / "all_bases.base").read_text()

        vsm._remove_from_bases_file("nonexistent", "NonExistent")

        # Content should be unchanged
        new_content = (temp_vault / "x" / "bases" / "all_bases.base").read_text()
        assert original_content == new_content

    def test_update_moc_content(self, temp_vault: Path) -> None:
        """Test _update_moc_content."""
        from note_type_wizard import VaultStructureManager

        # Create MOC file
        folder = temp_vault / "TestFolder"
        folder.mkdir()
        moc_path = folder / "_OldName_MOC.md"
        moc_path.write_text("# OldName\n![[all_bases.base##OldName]]")

        vsm = VaultStructureManager(
            temp_vault,
            temp_vault / "x" / "templates",
            temp_vault / "x" / "bases",
            "x",
            ["type", "up", "created"],
        )

        vsm._update_moc_content(moc_path, "OldName", "NewName")

        content = moc_path.read_text()
        assert "# NewName" in content
        assert "##NewName]]" in content
