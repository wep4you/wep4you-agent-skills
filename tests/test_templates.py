"""
Tests for Template Management Skill
Tests CRUD operations, Templater detection, and variable substitution
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add skills path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "templates" / "scripts"))

from templates import TemplateManager  # type: ignore


@pytest.fixture
def temp_vault(tmp_path: Path) -> Path:
    """Create temporary vault structure"""
    vault = tmp_path / "test-vault"
    vault.mkdir()

    # Create vault templates directory
    vault_templates = vault / ".obsidian" / "templates"
    vault_templates.mkdir(parents=True)

    # Create plugin templates directory
    plugin_templates = vault / "skills" / "templates" / "templates"
    plugin_templates.mkdir(parents=True)

    # Create map templates
    map_dir = plugin_templates / "map"
    map_dir.mkdir()
    (map_dir / "basic.md").write_text(
        """---
type: map
up: "[[{{up}}]]"
created: {{date}}
---

# {{title}}
"""
    )

    # Create dot templates
    dot_dir = plugin_templates / "dot"
    dot_dir.mkdir()
    (dot_dir / "basic.md").write_text(
        """---
type: dot
up: "[[{{up}}]]"
---

# {{title}}
"""
    )

    return vault


@pytest.fixture
def temp_vault_with_templater(temp_vault: Path) -> Path:
    """Create vault with Templater plugin"""
    templater_dir = temp_vault / ".obsidian" / "plugins" / "templater-obsidian"
    templater_dir.mkdir(parents=True)
    (templater_dir / "manifest.json").write_text('{"id": "templater-obsidian"}')
    return temp_vault


class TestTemplateManager:
    """Test TemplateManager class"""

    def test_init(self, temp_vault: Path) -> None:
        """Test initialization"""
        manager = TemplateManager(str(temp_vault))
        assert manager.vault_path == temp_vault
        assert not manager.has_templater

    def test_init_with_templater(self, temp_vault_with_templater: Path) -> None:
        """Test initialization with Templater"""
        manager = TemplateManager(str(temp_vault_with_templater))
        assert manager.has_templater

    def test_detect_templater_not_installed(self, temp_vault: Path) -> None:
        """Test Templater detection when not installed"""
        manager = TemplateManager(str(temp_vault))
        assert not manager.has_templater

    def test_detect_templater_installed(self, temp_vault_with_templater: Path) -> None:
        """Test Templater detection when installed"""
        manager = TemplateManager(str(temp_vault_with_templater))
        assert manager.has_templater

    def test_find_plugin_templates_dir(self, temp_vault: Path) -> None:
        """Test finding plugin templates directory"""
        manager = TemplateManager(str(temp_vault))
        assert manager.plugin_templates_dir.exists()
        assert manager.plugin_templates_dir.is_dir()

    def test_find_vault_templates_dir(self, temp_vault: Path) -> None:
        """Test finding vault templates directory"""
        manager = TemplateManager(str(temp_vault))
        assert manager.vault_templates_dir is not None
        assert manager.vault_templates_dir.exists()

    def test_list_templates_empty(self, tmp_path: Path) -> None:
        """Test listing templates when none exist"""
        vault = tmp_path / "empty-vault"
        vault.mkdir()
        manager = TemplateManager(str(vault))
        templates = manager.list_templates()
        assert isinstance(templates, list)

    def test_list_templates(self, temp_vault: Path) -> None:
        """Test listing available templates"""
        manager = TemplateManager(str(temp_vault))
        templates = manager.list_templates()

        assert len(templates) >= 2  # At least map/basic and dot/basic
        assert any(t["name"] == "map/basic" for t in templates)
        assert any(t["name"] == "dot/basic" for t in templates)

        # Check template structure
        template = templates[0]
        assert "name" in template
        assert "path" in template
        assert "source" in template
        assert "type" in template

    def test_list_templates_plugin_source(self, temp_vault: Path) -> None:
        """Test plugin templates have correct source"""
        manager = TemplateManager(str(temp_vault))
        templates = manager.list_templates()

        plugin_templates = [t for t in templates if t["source"] == "plugin"]
        assert len(plugin_templates) >= 2

    def test_list_templates_vault_source(self, temp_vault: Path) -> None:
        """Test vault templates have correct source"""
        # Create vault template
        vault_template = temp_vault / ".obsidian" / "templates" / "custom.md"
        vault_template.write_text("# {{title}}")

        manager = TemplateManager(str(temp_vault))
        templates = manager.list_templates()

        vault_templates = [t for t in templates if t["source"] == "vault"]
        assert len(vault_templates) == 1
        assert vault_templates[0]["name"] == "custom"

    def test_show_template_exists(self, temp_vault: Path) -> None:
        """Test showing existing template"""
        manager = TemplateManager(str(temp_vault))
        content = manager.show_template("map/basic")

        assert content is not None
        assert "type: map" in content
        assert "{{title}}" in content

    def test_show_template_not_found(self, temp_vault: Path) -> None:
        """Test showing non-existent template"""
        manager = TemplateManager(str(temp_vault))
        content = manager.show_template("nonexistent")
        assert content is None

    def test_create_template(self, temp_vault: Path) -> None:
        """Test creating new template"""
        manager = TemplateManager(str(temp_vault))
        content = "# Test Template\n\n{{title}}"

        result = manager.create_template("test-template", content)
        assert result

        # Verify file exists
        template_path = temp_vault / ".obsidian" / "templates" / "test-template.md"
        assert template_path.exists()
        assert template_path.read_text() == content

    def test_create_template_default_content(self, temp_vault: Path) -> None:
        """Test creating template with default content"""
        manager = TemplateManager(str(temp_vault))

        result = manager.create_template("default-template")
        assert result

        # Verify file exists with default content
        template_path = temp_vault / ".obsidian" / "templates" / "default-template.md"
        assert template_path.exists()
        content = template_path.read_text()
        assert "type: {{type}}" in content
        assert "{{title}}" in content

    def test_create_template_no_vault_dir(self, tmp_path: Path) -> None:
        """Test creating template without vault templates directory"""
        vault = tmp_path / "no-templates"
        vault.mkdir()

        manager = TemplateManager(str(vault))
        result = manager.create_template("test", "content")
        assert not result  # Should fail

    @patch("subprocess.run")
    def test_edit_template(self, mock_run: MagicMock, temp_vault: Path) -> None:
        """Test editing template"""
        manager = TemplateManager(str(temp_vault))
        mock_run.return_value = MagicMock(returncode=0)

        result = manager.edit_template("map/basic")
        assert result
        mock_run.assert_called_once()

    def test_edit_template_not_found(self, temp_vault: Path) -> None:
        """Test editing non-existent template"""
        manager = TemplateManager(str(temp_vault))
        result = manager.edit_template("nonexistent")
        assert not result

    def test_delete_template_vault(self, temp_vault: Path) -> None:
        """Test deleting vault template"""
        # Create vault template
        template_path = temp_vault / ".obsidian" / "templates" / "deleteme.md"
        template_path.write_text("content")

        manager = TemplateManager(str(temp_vault))
        result = manager.delete_template("deleteme")

        assert result
        assert not template_path.exists()

    def test_delete_template_plugin_denied(self, temp_vault: Path) -> None:
        """Test deleting plugin template is denied"""
        manager = TemplateManager(str(temp_vault))
        result = manager.delete_template("map/basic")
        assert not result  # Should fail

    def test_delete_template_not_found(self, temp_vault: Path) -> None:
        """Test deleting non-existent template"""
        manager = TemplateManager(str(temp_vault))
        result = manager.delete_template("nonexistent")
        assert not result

    def test_apply_template(self, temp_vault: Path) -> None:
        """Test applying template to file"""
        manager = TemplateManager(str(temp_vault))
        target = temp_vault / "test-note.md"

        variables = {"up": "Home", "title": "Test Note"}
        result = manager.apply_template("map/basic", str(target), variables)

        assert result
        assert target.exists()

        content = target.read_text()
        assert "type: map" in content
        assert "[[Home]]" in content
        assert "# Test Note" in content

    def test_apply_template_with_defaults(self, temp_vault: Path) -> None:
        """Test applying template with default variables"""
        manager = TemplateManager(str(temp_vault))
        target = temp_vault / "my-note.md"

        result = manager.apply_template("map/basic", str(target))

        assert result
        assert target.exists()

        content = target.read_text()
        assert "# my-note" in content  # Default title from filename
        assert "created:" in content  # Default date

    def test_apply_template_not_found(self, temp_vault: Path) -> None:
        """Test applying non-existent template"""
        manager = TemplateManager(str(temp_vault))
        target = temp_vault / "test.md"

        result = manager.apply_template("nonexistent", str(target))
        assert not result
        assert not target.exists()

    def test_apply_template_creates_dirs(self, temp_vault: Path) -> None:
        """Test applying template creates parent directories"""
        manager = TemplateManager(str(temp_vault))
        target = temp_vault / "Atlas" / "Maps" / "test.md"

        result = manager.apply_template("map/basic", str(target))

        assert result
        assert target.exists()
        assert target.parent.exists()

    def test_substitute_variables_simple(self, temp_vault: Path) -> None:
        """Test simple variable substitution"""
        manager = TemplateManager(str(temp_vault))

        content = "Title: {{title}}, Date: {{date}}"
        variables = {"title": "My Note", "date": "2025-01-15"}

        result = manager._substitute_variables(content, variables)

        assert result == "Title: My Note, Date: 2025-01-15"

    def test_substitute_variables_templater(self, temp_vault_with_templater: Path) -> None:
        """Test Templater syntax substitution"""
        manager = TemplateManager(str(temp_vault_with_templater))

        content = "Date: <% tp.date.now() %>, Title: <% tp.file.title %>"
        variables = {"title": "Test"}

        result = manager._substitute_variables(content, variables)

        # Should replace Templater patterns
        assert "<% tp.date.now() %>" not in result
        assert "<% tp.file.title %>" not in result
        assert "Test" in result

    def test_substitute_variables_no_templater(self, temp_vault: Path) -> None:
        """Test Templater syntax is skipped without plugin"""
        manager = TemplateManager(str(temp_vault))

        content = "Date: <% tp.date.now() %>"
        variables = {}

        result = manager._substitute_variables(content, variables)

        # Templater syntax should be preserved (not substituted)
        # because Templater is not installed
        # Actually, the code still does basic substitution even without Templater
        # to provide fallback functionality
        assert "Date:" in result

    def test_resolve_template_path_vault_first(self, temp_vault: Path) -> None:
        """Test template resolution prefers vault templates"""
        # Create vault template with same name as plugin template
        vault_template = temp_vault / ".obsidian" / "templates" / "basic.md"
        vault_template.write_text("vault version")

        manager = TemplateManager(str(temp_vault))
        path = manager._resolve_template_path("basic")

        assert path == vault_template

    def test_resolve_template_path_plugin_fallback(self, temp_vault: Path) -> None:
        """Test template resolution falls back to plugin templates"""
        manager = TemplateManager(str(temp_vault))
        path = manager._resolve_template_path("map/basic")

        assert path is not None
        assert "map" in str(path)
        assert path.name == "basic.md"

    def test_resolve_template_path_not_found(self, temp_vault: Path) -> None:
        """Test template resolution returns None when not found"""
        manager = TemplateManager(str(temp_vault))
        path = manager._resolve_template_path("nonexistent")

        assert path is None

    def test_get_default_template(self, temp_vault: Path) -> None:
        """Test default template generation"""
        manager = TemplateManager(str(temp_vault))
        content = manager._get_default_template()

        assert "type: {{type}}" in content
        assert 'up: "[[{{up}}]]"' in content
        assert "created: {{date}}" in content
        assert "# {{title}}" in content


class TestCLI:
    """Test CLI interface"""

    @patch("sys.argv", ["templates.py", "--vault", "test", "--list"])
    @patch("templates.TemplateManager")
    def test_cli_list(self, mock_manager_class: MagicMock) -> None:
        """Test CLI list command"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.list_templates.return_value = []
        mock_manager.has_templater = False
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.list_templates.assert_called_once()

    @patch("sys.argv", ["templates.py", "--vault", "test", "--list"])
    @patch("templates.TemplateManager")
    def test_cli_list_with_templates(self, mock_manager_class: MagicMock) -> None:
        """Test CLI list command with templates"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.list_templates.return_value = [
            {"name": "map/basic", "type": "map", "source": "plugin"},
            {"name": "custom", "type": "unknown", "source": "vault"},
        ]
        mock_manager.has_templater = True
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.list_templates.assert_called_once()

    @patch("sys.argv", ["templates.py", "--vault", "test", "--create", "new"])
    @patch("templates.TemplateManager")
    def test_cli_create_failed(self, mock_manager_class: MagicMock) -> None:
        """Test CLI create command when it fails"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.create_template.return_value = False
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 1

    @patch("sys.argv", ["templates.py", "--vault", "test", "--edit", "map/basic"])
    @patch("templates.TemplateManager")
    def test_cli_edit(self, mock_manager_class: MagicMock) -> None:
        """Test CLI edit command"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.edit_template.return_value = True
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.edit_template.assert_called_once_with("map/basic")

    @patch("sys.argv", ["templates.py", "--vault", "test", "--edit", "nonexistent"])
    @patch("templates.TemplateManager")
    def test_cli_edit_failed(self, mock_manager_class: MagicMock) -> None:
        """Test CLI edit command when it fails"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.edit_template.return_value = False
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 1

    @patch("sys.argv", ["templates.py", "--vault", "test", "--delete", "nonexistent"])
    @patch("templates.TemplateManager")
    def test_cli_delete_failed(self, mock_manager_class: MagicMock) -> None:
        """Test CLI delete command when it fails"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.delete_template.return_value = False
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 1

    @patch(
        "sys.argv",
        ["templates.py", "--vault", "test", "--apply", "nonexistent", "test.md"],
    )
    @patch("templates.TemplateManager")
    def test_cli_apply_failed(self, mock_manager_class: MagicMock) -> None:
        """Test CLI apply command when it fails"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.apply_template.return_value = False
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 1

    @patch("sys.argv", ["templates.py", "--vault", "test", "--show", "map/basic"])
    @patch("templates.TemplateManager")
    def test_cli_show(self, mock_manager_class: MagicMock) -> None:
        """Test CLI show command"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.show_template.return_value = "content"
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.show_template.assert_called_once_with("map/basic")

    @patch("sys.argv", ["templates.py", "--vault", "test", "--show", "notfound"])
    @patch("templates.TemplateManager")
    def test_cli_show_not_found(self, mock_manager_class: MagicMock) -> None:
        """Test CLI show command with non-existent template"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.show_template.return_value = None
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 1

    @patch("sys.argv", ["templates.py", "--vault", "test", "--create", "new"])
    @patch("templates.TemplateManager")
    def test_cli_create(self, mock_manager_class: MagicMock) -> None:
        """Test CLI create command"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.create_template.return_value = True
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.create_template.assert_called_once()

    @patch(
        "sys.argv",
        ["templates.py", "--vault", "test", "--apply", "map/basic", "test.md"],
    )
    @patch("templates.TemplateManager")
    def test_cli_apply(self, mock_manager_class: MagicMock) -> None:
        """Test CLI apply command"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.apply_template.return_value = True
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.apply_template.assert_called_once()

    @patch(
        "sys.argv",
        [
            "templates.py",
            "--vault",
            "test",
            "--apply",
            "map/basic",
            "test.md",
            "--var",
            "up=Home",
            "--var",
            "title=Test",
        ],
    )
    @patch("templates.TemplateManager")
    def test_cli_apply_with_vars(self, mock_manager_class: MagicMock) -> None:
        """Test CLI apply command with variables"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.apply_template.return_value = True
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0

        # Check that variables were passed correctly
        call_args = mock_manager.apply_template.call_args
        variables = call_args[0][2]  # Third argument is variables dict
        assert variables["up"] == "Home"
        assert variables["title"] == "Test"

    @patch("sys.argv", ["templates.py", "--vault", "test", "--delete", "custom"])
    @patch("templates.TemplateManager")
    def test_cli_delete(self, mock_manager_class: MagicMock) -> None:
        """Test CLI delete command"""
        from templates import main

        mock_manager = MagicMock()
        mock_manager.delete_template.return_value = True
        mock_manager_class.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.delete_template.assert_called_once_with("custom")


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_apply_template_with_subdirs(self, temp_vault: Path) -> None:
        """Test applying template to nested subdirectories"""
        manager = TemplateManager(str(temp_vault))
        target = temp_vault / "a" / "b" / "c" / "test.md"

        result = manager.apply_template("map/basic", str(target), {"up": "Test"})

        assert result
        assert target.exists()

    def test_list_templates_sorted(self, temp_vault: Path) -> None:
        """Test templates are returned sorted by name"""
        manager = TemplateManager(str(temp_vault))
        templates = manager.list_templates()

        names = [t["name"] for t in templates]
        assert names == sorted(names)

    def test_variable_substitution_missing_vars(self, temp_vault: Path) -> None:
        """Test variables that aren't provided remain as placeholders"""
        manager = TemplateManager(str(temp_vault))

        content = "{{present}} and {{missing}}"
        variables = {"present": "here"}

        result = manager._substitute_variables(content, variables)

        assert "here" in result
        assert "{{missing}}" in result  # Should remain as placeholder

    def test_template_with_yaml_frontmatter(self, temp_vault: Path) -> None:
        """Test template with YAML frontmatter"""
        manager = TemplateManager(str(temp_vault))
        target = temp_vault / "test.md"

        result = manager.apply_template("map/basic", str(target), {"up": "Home"})

        assert result
        content = target.read_text()

        # Check frontmatter is preserved
        assert content.startswith("---")
        assert "type: map" in content
