"""
Tests for skills.core.generation.templates module.

Tests the template loading, rendering, and generation functions.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from skills.core.generation.templates import (
    create_template_notes,
    generate_template_note,
    load_template,
    render_template,
)


class TestLoadTemplate:
    """Tests for load_template function."""

    def test_load_template_success(self, tmp_path: Path) -> None:
        """Test loading a valid template file."""
        template_file = tmp_path / "test.md"
        content = "# {{title}}\n\nContent here"
        template_file.write_text(content)

        result = load_template(template_file)

        assert result == content

    def test_load_template_file_not_found(self, tmp_path: Path) -> None:
        """Test loading a non-existent template raises FileNotFoundError."""
        non_existent = tmp_path / "does_not_exist.md"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_template(non_existent)

        assert "Template not found" in str(exc_info.value)
        assert str(non_existent) in str(exc_info.value)

    def test_load_template_custom_encoding(self, tmp_path: Path) -> None:
        """Test loading a template with custom encoding."""
        template_file = tmp_path / "utf16.md"
        content = "# Template with special chars"
        template_file.write_text(content, encoding="utf-16")

        result = load_template(template_file, encoding="utf-16")

        assert result == content

    def test_load_template_empty_file(self, tmp_path: Path) -> None:
        """Test loading an empty template file."""
        template_file = tmp_path / "empty.md"
        template_file.write_text("")

        result = load_template(template_file)

        assert result == ""

    def test_load_template_with_unicode(self, tmp_path: Path) -> None:
        """Test loading a template with unicode characters."""
        template_file = tmp_path / "unicode.md"
        content = "# Template with unicode chars"
        template_file.write_text(content)

        result = load_template(template_file)

        assert result == content


class TestRenderTemplate:
    """Tests for render_template function."""

    def test_render_template_all_placeholders(self) -> None:
        """Test rendering a template with all standard placeholders."""
        template = """---
type: "{{type}}"
up: "[[{{up}}]]"
created: {{date}}
---

# {{title}}
"""
        test_date = date(2025, 1, 15)

        result = render_template(
            template,
            title="My Note",
            note_type="map",
            up_link="Home",
            created_date=test_date,
        )

        assert 'type: "map"' in result
        assert 'up: "[[Home]]"' in result
        assert "created: 2025-01-15" in result
        assert "# My Note" in result

    def test_render_template_default_date(self) -> None:
        """Test rendering uses today's date when not provided."""
        template = "created: {{date}}"
        today = date.today()

        result = render_template(template)

        assert f"created: {today.isoformat()}" in result

    def test_render_template_no_placeholders(self) -> None:
        """Test rendering a template with no placeholders."""
        template = """---
type: "static"
---

# Static Content
"""
        result = render_template(template)

        assert result == template

    def test_render_template_empty_values(self) -> None:
        """Test rendering with empty string values."""
        template = "title: {{title}}, type: {{type}}"

        result = render_template(template, title="", note_type="")

        assert "title: , type: " in result

    def test_render_template_custom_values(self) -> None:
        """Test rendering with custom placeholder values."""
        template = "Author: {{author}}, Project: {{project}}"

        result = render_template(
            template,
            custom_values={"author": "John Doe", "project": "My Project"},
        )

        assert "Author: John Doe" in result
        assert "Project: My Project" in result

    def test_render_template_mixed_standard_and_custom(self) -> None:
        """Test rendering with both standard and custom placeholders."""
        template = """---
type: "{{type}}"
author: {{author}}
created: {{date}}
---

# {{title}}
"""
        test_date = date(2025, 6, 15)

        result = render_template(
            template,
            title="Project Note",
            note_type="project",
            created_date=test_date,
            custom_values={"author": "Jane Smith"},
        )

        assert 'type: "project"' in result
        assert "author: Jane Smith" in result
        assert "created: 2025-06-15" in result
        assert "# Project Note" in result

    def test_render_template_multiple_occurrences(self) -> None:
        """Test rendering replaces all occurrences of a placeholder."""
        template = "Title: {{title}}, Name: {{title}}, Header: {{title}}"

        result = render_template(template, title="Test")

        assert result == "Title: Test, Name: Test, Header: Test"

    def test_render_template_unmatched_placeholders_remain(self) -> None:
        """Test that placeholders without values remain unchanged."""
        template = "Known: {{title}}, Unknown: {{unknown}}"

        result = render_template(template, title="Test")

        assert "Known: Test" in result
        assert "Unknown: {{unknown}}" in result

    def test_render_template_custom_values_none(self) -> None:
        """Test rendering when custom_values is explicitly None."""
        template = "title: {{title}}"

        result = render_template(template, title="Test", custom_values=None)

        assert "title: Test" in result

    def test_render_template_preserves_whitespace(self) -> None:
        """Test that template whitespace is preserved."""
        template = "  {{title}}  \n\n  Content  "

        result = render_template(template, title="Test")

        assert "  Test  \n\n  Content  " in result


class TestGenerateTemplateNote:
    """Tests for generate_template_note function."""

    def test_generate_template_note_basic(self) -> None:
        """Test generating a basic template note."""
        type_config = {"description": "Map of content"}
        core_properties = ["type", "up", "created"]

        result = generate_template_note("map", type_config, core_properties)

        assert "---" in result
        assert 'type: "map"' in result
        assert 'up: "[[{{up}}]]"' in result
        assert "created: {{date}}" in result
        assert "# {{title}}" in result
        assert "Template for **Map** notes: Map of content" in result

    def test_generate_template_note_with_tags(self) -> None:
        """Test generating a template note with tags property."""
        type_config = {"description": "Test"}
        core_properties = ["type", "created", "tags"]

        result = generate_template_note("dot", type_config, core_properties)

        assert "tags: []" in result

    def test_generate_template_note_with_related(self) -> None:
        """Test generating a template note with related property."""
        type_config = {"description": "Test"}
        core_properties = ["type", "created", "related"]

        result = generate_template_note("dot", type_config, core_properties)

        assert "related: []" in result

    def test_generate_template_note_with_daily(self) -> None:
        """Test generating a template note with daily property."""
        type_config = {"description": "Test"}
        core_properties = ["type", "created", "daily"]

        result = generate_template_note("dot", type_config, core_properties)

        assert "daily: " in result

    def test_generate_template_note_with_collection(self) -> None:
        """Test generating a template note with collection property."""
        type_config = {"description": "Test"}
        core_properties = ["type", "created", "collection"]

        result = generate_template_note("dot", type_config, core_properties)

        assert "collection: " in result

    def test_generate_template_note_with_additional_required(self) -> None:
        """Test generating a template with additional required properties."""
        type_config = {
            "description": "Project note",
            "properties": {"additional_required": ["status", "author", "url"]},
        }
        core_properties = ["type", "created"]

        result = generate_template_note("project", type_config, core_properties)

        assert 'status: "active"' in result
        assert "author: " in result
        assert "url: " in result

    def test_generate_template_note_with_optional_properties(self) -> None:
        """Test generating a template with optional properties as comments."""
        type_config = {
            "description": "Test",
            "properties": {"optional": ["priority", "deadline"]},
        }
        core_properties = ["type", "created"]

        result = generate_template_note("task", type_config, core_properties)

        assert "# priority: " in result
        assert "# deadline: " in result

    def test_generate_template_note_with_core_properties_filter(self) -> None:
        """Test filtering core properties."""
        type_config = {"description": "Test"}
        core_properties = ["type", "up", "created", "tags", "daily"]
        core_properties_filter = ["type", "created", "up"]

        result = generate_template_note(
            "dot",
            type_config,
            core_properties,
            core_properties_filter=core_properties_filter,
        )

        assert 'type: "dot"' in result
        assert "created: {{date}}" in result
        assert 'up: "[[{{up}}]]"' in result
        # tags and daily should be filtered out (not in filter list)
        assert "tags:" not in result
        assert "daily:" not in result

    def test_generate_template_note_mandatory_properties_always_included(self) -> None:
        """Test that type and created are always included even when filtered."""
        type_config = {"description": "Test"}
        core_properties = ["type", "up", "created", "tags"]
        # Filter that doesn't include type or created
        core_properties_filter = ["up"]

        result = generate_template_note(
            "dot",
            type_config,
            core_properties,
            core_properties_filter=core_properties_filter,
        )

        # type and created should still be included as mandatory
        assert 'type: "dot"' in result
        assert "created: {{date}}" in result
        assert 'up: "[[{{up}}]]"' in result
        # tags should be filtered out
        assert "tags:" not in result

    def test_generate_template_note_with_custom_properties(self) -> None:
        """Test adding custom global properties."""
        type_config = {"description": "Test"}
        core_properties = ["type", "created"]
        custom_properties = ["custom_field", "another_field"]

        result = generate_template_note(
            "dot",
            type_config,
            core_properties,
            custom_properties=custom_properties,
        )

        assert "custom_field: " in result
        assert "another_field: " in result

    def test_generate_template_note_with_per_type_properties(self) -> None:
        """Test adding per-type custom properties."""
        type_config = {"description": "Test"}
        core_properties = ["type", "created"]
        per_type_properties = {
            "project": ["priority", "deadline"],
            "area": ["scope"],
        }

        result = generate_template_note(
            "project",
            type_config,
            core_properties,
            per_type_properties=per_type_properties,
        )

        assert "priority: " in result
        assert "deadline: " in result
        # area properties should not be included
        assert "scope:" not in result

    def test_generate_template_note_per_type_no_duplicates(self) -> None:
        """Test that per-type properties don't duplicate additional_required."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["status"]},
        }
        core_properties = ["type", "created"]
        per_type_properties = {"project": ["status", "deadline"]}

        result = generate_template_note(
            "project",
            type_config,
            core_properties,
            per_type_properties=per_type_properties,
        )

        # status should only appear once (from additional_required)
        assert result.count("status:") == 1
        assert "deadline: " in result

    def test_generate_template_note_optional_not_duplicated_by_per_type(self) -> None:
        """Test that optional properties skip per-type properties."""
        type_config = {
            "description": "Test",
            "properties": {"optional": ["deadline", "notes"]},
        }
        core_properties = ["type", "created"]
        per_type_properties = {"project": ["deadline"]}

        result = generate_template_note(
            "project",
            type_config,
            core_properties,
            per_type_properties=per_type_properties,
        )

        # deadline is already added as per-type, so it shouldn't be in comments
        assert "deadline: " in result  # As per-type property (not commented)
        assert "# notes: " in result  # As optional (commented)
        # Should not have "# deadline: " as commented optional
        lines = result.split("\n")
        deadline_lines = [line for line in lines if "deadline" in line]
        assert len(deadline_lines) == 1

    def test_generate_template_note_default_description(self) -> None:
        """Test default description when not provided in config."""
        type_config = {}  # No description
        core_properties = ["type", "created"]

        result = generate_template_note("custom_type", type_config, core_properties)

        assert "Template for **Custom Type** notes: Custom_Type note" in result

    def test_generate_template_note_underscore_in_type_name(self) -> None:
        """Test type name with underscores is formatted correctly."""
        type_config = {"description": "Test"}
        core_properties = ["type", "created"]

        result = generate_template_note("knowledge_base", type_config, core_properties)

        assert "Template for **Knowledge Base** notes" in result

    def test_generate_template_note_structure(self) -> None:
        """Test the overall structure of generated template."""
        type_config = {"description": "Test note"}
        core_properties = ["type", "created"]

        result = generate_template_note("test", type_config, core_properties)

        lines = result.split("\n")

        # Check structure
        assert lines[0] == "---"
        assert "---" in lines  # Closing frontmatter
        assert "# {{title}}" in result
        assert "## Content" in result
        assert "<!-- Your content here -->" in result
        assert "## Related" in result
        assert "- [[]]" in result


class TestCreateTemplateNotes:
    """Tests for create_template_notes function."""

    def test_create_template_notes_basic(self, tmp_path: Path) -> None:
        """Test creating template notes for multiple types."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {
            "map": {"description": "Map notes"},
            "dot": {"description": "Dot notes"},
        }
        core_properties = ["type", "up", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
        )

        assert len(created) == 2
        assert (vault_path / "x/templates/map.md").exists()
        assert (vault_path / "x/templates/dot.md").exists()

    def test_create_template_notes_custom_folder(self, tmp_path: Path) -> None:
        """Test creating templates in custom folder."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {"test": {"description": "Test"}}
        core_properties = ["type", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
            templates_folder="custom/templates/",
        )

        assert len(created) == 1
        assert (vault_path / "custom/templates/test.md").exists()

    def test_create_template_notes_skips_daily(self, tmp_path: Path) -> None:
        """Test that daily note type is skipped."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {
            "map": {"description": "Map notes"},
            "daily": {"description": "Daily notes"},  # Should be skipped
        }
        core_properties = ["type", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
        )

        assert len(created) == 1
        assert (vault_path / "x/templates/map.md").exists()
        assert not (vault_path / "x/templates/daily.md").exists()

    def test_create_template_notes_dry_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test dry run mode doesn't create files."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {
            "map": {"description": "Map notes"},
            "dot": {"description": "Dot notes"},
        }
        core_properties = ["type", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
            dry_run=True,
        )

        # No files should be created
        assert len(created) == 0
        assert not (vault_path / "x/templates").exists()

        # Check dry run messages
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "Would create" in captured.out

    def test_create_template_notes_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that parent directories are created."""
        vault_path = tmp_path / "vault"
        # Don't create vault_path - it should be created

        note_types = {"test": {"description": "Test"}}
        core_properties = ["type", "created"]

        # This should create the vault_path and templates folder
        vault_path.mkdir()  # Need at least the root to exist
        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
            templates_folder="deeply/nested/templates/",
        )

        assert len(created) == 1
        assert (vault_path / "deeply/nested/templates/test.md").exists()

    def test_create_template_notes_with_filter(self, tmp_path: Path) -> None:
        """Test creating templates with core properties filter."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {"test": {"description": "Test"}}
        core_properties = ["type", "up", "created", "tags"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
            core_properties_filter=["type", "created"],
        )

        assert len(created) == 1
        content = (vault_path / "x/templates/test.md").read_text()
        assert "type:" in content
        assert "created:" in content
        # up and tags should be filtered out
        assert "up:" not in content
        assert "tags:" not in content

    def test_create_template_notes_with_custom_properties(self, tmp_path: Path) -> None:
        """Test creating templates with custom global properties."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {"test": {"description": "Test"}}
        core_properties = ["type", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
            custom_properties=["custom_field"],
        )

        assert len(created) == 1
        content = (vault_path / "x/templates/test.md").read_text()
        assert "custom_field: " in content

    def test_create_template_notes_with_per_type_properties(self, tmp_path: Path) -> None:
        """Test creating templates with per-type custom properties."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {
            "project": {"description": "Project"},
            "area": {"description": "Area"},
        }
        core_properties = ["type", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
            per_type_properties={
                "project": ["priority"],
                "area": ["scope"],
            },
        )

        assert len(created) == 2

        project_content = (vault_path / "x/templates/project.md").read_text()
        assert "priority: " in project_content
        assert "scope:" not in project_content

        area_content = (vault_path / "x/templates/area.md").read_text()
        assert "scope: " in area_content
        assert "priority:" not in area_content

    def test_create_template_notes_empty_types(self, tmp_path: Path) -> None:
        """Test creating templates with no note types."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types: dict[str, dict] = {}
        core_properties = ["type", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
        )

        assert len(created) == 0

    def test_create_template_notes_content_format(self, tmp_path: Path) -> None:
        """Test that created templates have correct content format."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {"map": {"description": "Maps of content"}}
        core_properties = ["type", "up", "created"]

        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
        )

        assert len(created) == 1
        content = (vault_path / "x/templates/map.md").read_text()

        # Check frontmatter
        assert content.startswith("---")
        assert 'type: "map"' in content
        assert 'up: "[[{{up}}]]"' in content
        assert "created: {{date}}" in content

        # Check body
        assert "# {{title}}" in content
        assert "Template for **Map** notes: Maps of content" in content
        assert "## Content" in content
        assert "## Related" in content

    def test_create_template_notes_prints_created_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that created files are printed."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {"test": {"description": "Test"}}
        core_properties = ["type", "created"]

        create_template_notes(vault_path, note_types, core_properties)

        captured = capsys.readouterr()
        assert "Created:" in captured.out


class TestIntegration:
    """Integration tests for template functions working together."""

    def test_load_render_workflow(self, tmp_path: Path) -> None:
        """Test the complete load -> render workflow."""
        # Create a template file
        template_file = tmp_path / "note.md"
        template_content = """---
type: "{{type}}"
up: "[[{{up}}]]"
created: {{date}}
---

# {{title}}

Content goes here.
"""
        template_file.write_text(template_content)

        # Load the template
        loaded = load_template(template_file)
        assert loaded == template_content

        # Render the template
        test_date = date(2025, 3, 15)
        rendered = render_template(
            loaded,
            title="My Project",
            note_type="project",
            up_link="Projects MOC",
            created_date=test_date,
        )

        assert 'type: "project"' in rendered
        assert 'up: "[[Projects MOC]]"' in rendered
        assert "created: 2025-03-15" in rendered
        assert "# My Project" in rendered

    def test_generate_and_create_workflow(self, tmp_path: Path) -> None:
        """Test generate_template_note creates valid templates."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        note_types = {"project": {"description": "Project notes"}}
        core_properties = ["type", "up", "created"]

        # Create templates
        created = create_template_notes(
            vault_path,
            note_types,
            core_properties,
        )

        # Load the created template
        template_path = created[0]
        loaded = load_template(template_path)

        # Render it with values
        rendered = render_template(
            loaded,
            title="New Project",
            note_type="project",
            up_link="Home",
            created_date=date(2025, 1, 1),
        )

        # Verify the rendered content
        assert 'type: "project"' in rendered
        assert 'up: "[[Home]]"' in rendered
        assert "created: 2025-01-01" in rendered
        assert "# New Project" in rendered
