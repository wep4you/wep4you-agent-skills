"""
Tests for the content generation module.

Run with: uv run pytest tests/core/generation/test_content.py -v
"""

from datetime import date
from pathlib import Path

from skills.core.generation.content import (
    generate_home_note,
    generate_note_content,
    generate_sample_notes,
)


class TestGenerateNoteContent:
    """Tests for generate_note_content function."""

    def test_basic_note_content(self):
        """Test generating basic note content with minimal config."""
        type_config = {
            "description": "Atomic notes for single ideas",
        }
        content = generate_note_content(
            "dot",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "---" in content
        assert 'type: "dot"' in content
        assert 'created: "2025-01-15"' in content
        assert "# Getting Started with Dots" in content
        assert "Atomic notes for single ideas" in content

    def test_custom_title(self):
        """Test generating note with custom title."""
        type_config = {"description": "Map notes"}
        content = generate_note_content(
            "map",
            type_config,
            title="My Custom Title",
            created_date=date(2025, 1, 15),
        )

        assert "# My Custom Title" in content

    def test_default_title_generation(self):
        """Test that default title is generated from note type."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "source",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "# Getting Started with Sources" in content

    def test_underscore_note_type_title(self):
        """Test title generation for note types with underscores."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "fleeting_note",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "# Getting Started with Fleeting Notes" in content

    def test_custom_up_link(self):
        """Test generating note with custom up link."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            up_link="[[Atlas]]",
            created_date=date(2025, 1, 15),
        )

        assert 'up: "[[Atlas]]"' in content

    def test_methodology_in_tags(self):
        """Test methodology added to tags."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            methodology="lyt-ace",
            created_date=date(2025, 1, 15),
        )

        assert "tags: [sample, lyt-ace]" in content

    def test_no_methodology_in_tags(self):
        """Test tags without methodology."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            methodology="",
            created_date=date(2025, 1, 15),
        )

        assert "tags: [sample]" in content

    def test_custom_body_content(self):
        """Test generating note with custom body content."""
        type_config = {"description": "Test"}
        custom_body = "# Custom Body\n\nThis is my custom content."
        content = generate_note_content(
            "dot",
            type_config,
            body_content=custom_body,
            created_date=date(2025, 1, 15),
        )

        assert "# Custom Body" in content
        assert "This is my custom content." in content
        # Default body should not be present
        assert "What is a Dot?" not in content

    def test_additional_required_status_property(self):
        """Test additional_required status property."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["status"]},
        }
        content = generate_note_content(
            "project",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert 'status: "active"' in content

    def test_additional_required_rank_property(self):
        """Test additional_required rank property."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["rank"]},
        }
        content = generate_note_content(
            "dot",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "rank: 3" in content

    def test_additional_required_priority_property(self):
        """Test additional_required priority property."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["priority"]},
        }
        content = generate_note_content(
            "project",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert 'priority: "medium"' in content

    def test_additional_required_author_property(self):
        """Test additional_required author property."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["author"]},
        }
        content = generate_note_content(
            "source",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert 'author: "Unknown"' in content

    def test_additional_required_url_property(self):
        """Test additional_required url property."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["url"]},
        }
        content = generate_note_content(
            "source",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert 'url: ""' in content

    def test_additional_required_source_property(self):
        """Test additional_required source property."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["source"]},
        }
        content = generate_note_content(
            "dot",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert 'source: ""' in content

    def test_additional_required_unknown_property(self):
        """Test additional_required with unknown property defaults to empty string."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["custom_field"]},
        }
        content = generate_note_content(
            "dot",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert 'custom_field: ""' in content

    def test_per_type_properties(self):
        """Test per_type_properties are added."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "project",
            type_config,
            per_type_properties={"project": ["deadline", "budget"]},
            created_date=date(2025, 1, 15),
        )

        assert 'deadline: ""' in content
        assert 'budget: ""' in content

    def test_per_type_properties_other_type(self):
        """Test per_type_properties for different type are not added."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            per_type_properties={"project": ["deadline"]},
            created_date=date(2025, 1, 15),
        )

        assert "deadline" not in content

    def test_custom_properties(self):
        """Test custom_properties are added globally."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            custom_properties=["reviewed", "importance"],
            created_date=date(2025, 1, 15),
        )

        assert 'reviewed: ""' in content
        assert 'importance: ""' in content

    def test_custom_properties_not_duplicated(self):
        """Test custom properties are not duplicated if already in additional_required."""
        type_config = {
            "description": "Test",
            "properties": {"additional_required": ["status"]},
        }
        content = generate_note_content(
            "project",
            type_config,
            custom_properties=["status"],
            created_date=date(2025, 1, 15),
        )

        # status should appear only once with value "active"
        assert content.count("status:") == 1
        assert 'status: "active"' in content

    def test_optional_commented_properties(self):
        """Test optional properties are added as comments."""
        type_config = {
            "description": "Test",
            "properties": {"optional": ["summary", "notes"]},
        }
        content = generate_note_content(
            "map",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "# summary: " in content
        assert "# notes: " in content

    def test_optional_not_commented_if_in_per_type(self):
        """Test optional properties not commented if in per_type_properties."""
        type_config = {
            "description": "Test",
            "properties": {"optional": ["summary", "notes"]},
        }
        content = generate_note_content(
            "map",
            type_config,
            per_type_properties={"map": ["summary"]},
            created_date=date(2025, 1, 15),
        )

        # summary should be a real property, not commented
        assert 'summary: ""' in content
        assert "# summary: " not in content
        # notes should still be commented
        assert "# notes: " in content

    def test_custom_core_properties(self):
        """Test custom core_properties list."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            core_properties=["type", "created"],
            created_date=date(2025, 1, 15),
        )

        assert 'type: "dot"' in content
        assert 'created: "2025-01-15"' in content
        # These should not be present since not in core_properties
        assert "tags:" not in content
        assert "collection:" not in content
        assert "related:" not in content

    def test_core_properties_with_daily(self):
        """Test daily link when daily is in core_properties."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            core_properties=["type", "created", "daily"],
            created_date=date(2025, 1, 15),
        )

        assert 'daily: "[[2025-01-15]]"' in content

    def test_core_properties_without_daily(self):
        """Test no daily link when daily is not in core_properties."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            core_properties=["type", "created"],
            created_date=date(2025, 1, 15),
        )

        assert "daily:" not in content

    def test_date_defaults_to_today(self):
        """Test that created_date defaults to today."""
        type_config = {"description": "Test"}
        content = generate_note_content("dot", type_config)

        today = date.today().isoformat()
        assert f'created: "{today}"' in content


class TestGenerateDefaultBody:
    """Tests for _generate_default_body (tested indirectly)."""

    def test_map_body_structure(self):
        """Test default body for map note type."""
        type_config = {"description": "Index notes for organizing content"}
        content = generate_note_content(
            "map",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "What is a Map?" in content
        assert "Overview" in content
        assert "Contents" in content
        assert "Related Maps" in content

    def test_dot_body_structure(self):
        """Test default body for dot note type."""
        type_config = {"description": "Atomic notes for ideas"}
        content = generate_note_content(
            "dot",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "What is a Dot?" in content
        assert "Core Idea" in content
        assert "See Also" in content

    def test_source_body_structure(self):
        """Test default body for source note type."""
        type_config = {"description": "Notes from external sources"}
        content = generate_note_content(
            "source",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "What is a Source?" in content
        assert "Summary" in content
        assert "Quotes" in content
        assert "My Thoughts" in content

    def test_project_body_structure(self):
        """Test default body for project note type."""
        type_config = {"description": "Project tracking notes"}
        content = generate_note_content(
            "project",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "What is a Project?" in content
        assert "Outcome" in content
        assert "Tasks" in content
        assert "Resources" in content

    def test_daily_body_structure(self):
        """Test default body for daily note type."""
        type_config = {"description": "Daily journal entries"}
        content = generate_note_content(
            "daily",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "What is a Daily?" in content
        assert "Tasks" in content
        assert "Notes" in content
        assert "Reflections" in content

    def test_unknown_type_body_structure(self):
        """Test default body for unknown note types."""
        type_config = {"description": "Custom note type"}
        content = generate_note_content(
            "custom",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "What is a Custom?" in content
        assert "Main Content" in content
        assert "Related" in content

    def test_body_includes_tips(self):
        """Test that body includes tips section."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "Tips" in content
        assert "`up` link" in content
        assert "[[Home]]" in content

    def test_body_includes_sample_note_disclaimer(self):
        """Test that body includes sample note disclaimer."""
        type_config = {"description": "Test"}
        content = generate_note_content(
            "dot",
            type_config,
            created_date=date(2025, 1, 15),
        )

        assert "This is a sample note" in content


class TestGenerateSampleNotes:
    """Tests for generate_sample_notes function."""

    def test_creates_notes_for_enabled_types(self, tmp_path):
        """Test that sample notes are created for enabled types."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
            "map": {
                "description": "Index notes",
                "folder_hints": ["Atlas/Maps/"],
            },
        }
        up_links = {
            "Atlas/Dots/": "[[Atlas]]",
            "Atlas/Maps/": "[[Atlas]]",
        }

        created = generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created", "up", "tags"],
            up_links,
        )

        assert len(created) == 2
        assert (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").exists()
        assert (tmp_path / "Atlas" / "Maps" / "Getting Started with Maps.md").exists()

    def test_skips_types_without_folder_hints(self, tmp_path):
        """Test that types without folder_hints are skipped."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
            "orphan": {
                "description": "No folder",
                "folder_hints": [],
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas]]"}

        created = generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created"],
            up_links,
        )

        assert len(created) == 1
        assert (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").exists()

    def test_daily_note_uses_date_filename(self, tmp_path):
        """Test that daily notes use ISO date as filename."""
        note_types = {
            "daily": {
                "description": "Daily journal",
                "folder_hints": ["Calendar/daily/"],
            },
        }
        up_links = {"Calendar/daily/": "[[Calendar]]"}

        created = generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created"],
            up_links,
        )

        assert len(created) == 1
        today = date.today().isoformat()
        assert (tmp_path / "Calendar" / "daily" / f"{today}.md").exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Deep/Nested/Path/"],
            },
        }
        up_links = {"Deep/Nested/Path/": "[[Home]]"}

        created = generate_sample_notes(
            tmp_path,
            "minimal",
            note_types,
            ["type", "created"],
            up_links,
        )

        assert len(created) == 1
        assert (tmp_path / "Deep" / "Nested" / "Path").is_dir()

    def test_uses_correct_up_link(self, tmp_path):
        """Test that correct up link is used for each note."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas MOC]]"}

        generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created", "up"],
            up_links,
        )

        content = (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").read_text()
        assert 'up: "[[Atlas MOC]]"' in content

    def test_defaults_to_home_up_link(self, tmp_path):
        """Test that [[Home]] is used when up link not in up_links dict."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
        }
        up_links = {}  # Empty dict

        generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created", "up"],
            up_links,
        )

        content = (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").read_text()
        assert 'up: "[[Home]]"' in content

    def test_dry_run_does_not_create_files(self, tmp_path, capsys):
        """Test that dry_run mode does not create files."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas]]"}

        created = generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created"],
            up_links,
            dry_run=True,
        )

        assert len(created) == 0
        assert not (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").exists()

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out

    def test_prints_created_file_path(self, tmp_path, capsys):
        """Test that created file path is printed."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas]]"}

        generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created"],
            up_links,
        )

        captured = capsys.readouterr()
        assert "Created:" in captured.out

    def test_returns_list_of_paths(self, tmp_path):
        """Test that function returns list of Path objects."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas]]"}

        created = generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created"],
            up_links,
        )

        assert all(isinstance(p, Path) for p in created)

    def test_passes_custom_properties(self, tmp_path):
        """Test that custom_properties are passed to generate_note_content."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas]]"}

        generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created"],
            up_links,
            custom_properties=["importance"],
        )

        content = (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").read_text()
        assert 'importance: ""' in content

    def test_passes_per_type_properties(self, tmp_path):
        """Test that per_type_properties are passed to generate_note_content."""
        note_types = {
            "project": {
                "description": "Project notes",
                "folder_hints": ["Projects/"],
            },
        }
        up_links = {"Projects/": "[[Home]]"}

        generate_sample_notes(
            tmp_path,
            "para",
            note_types,
            ["type", "created"],
            up_links,
            per_type_properties={"project": ["deadline"]},
        )

        content = (tmp_path / "Projects" / "Getting Started with Projects.md").read_text()
        assert 'deadline: ""' in content

    def test_strips_trailing_slash_from_folder(self, tmp_path):
        """Test that trailing slash is stripped from folder_hints."""
        note_types = {
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],  # Trailing slash
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas]]"}

        generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            ["type", "created"],
            up_links,
        )

        # Should create in Atlas/Dots, not Atlas/Dots/
        assert (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").exists()


class TestGenerateHomeNote:
    """Tests for generate_home_note function."""

    def test_basic_home_note_structure(self):
        """Test basic structure of home note."""
        content = generate_home_note(
            "lyt-ace",
            ["map", "dot", "source"],
            created_date=date(2025, 1, 15),
        )

        assert "---" in content
        assert 'type: "map"' in content
        assert 'created: "2025-01-15"' in content
        assert "# Home" in content
        assert "LYT-ACE" in content

    def test_lyt_ace_methodology_links(self):
        """Test LYT-ACE methodology links."""
        content = generate_home_note(
            "lyt-ace",
            ["map", "dot"],
            created_date=date(2025, 1, 15),
        )

        assert "[[Atlas/_Atlas_MOC|Atlas]]" in content
        assert "[[Calendar/_Calendar_MOC|Calendar]]" in content
        assert "[[Efforts/_Efforts_MOC|Efforts]]" in content

    def test_para_methodology_links(self):
        """Test PARA methodology links."""
        content = generate_home_note(
            "para",
            ["project", "area"],
            created_date=date(2025, 1, 15),
        )

        assert "[[Projects/_Projects_MOC|Projects]]" in content
        assert "[[Areas/_Areas_MOC|Areas]]" in content
        assert "[[Resources/_Resources_MOC|Resources]]" in content
        assert "[[Archive/_Archive_MOC|Archive]]" in content

    def test_zettelkasten_methodology_links(self):
        """Test Zettelkasten methodology links."""
        content = generate_home_note(
            "zettelkasten",
            ["permanent", "literature", "fleeting"],
            created_date=date(2025, 1, 15),
        )

        assert "[[Permanent/_Permanent_MOC|Permanent Notes]]" in content
        assert "[[Literature/_Literature_MOC|Literature Notes]]" in content
        assert "[[Fleeting/_Fleeting_MOC|Fleeting Notes]]" in content

    def test_minimal_methodology_links(self):
        """Test minimal methodology links."""
        content = generate_home_note(
            "minimal",
            ["note"],
            created_date=date(2025, 1, 15),
        )

        assert "[[Notes/_Notes_MOC|Notes]]" in content
        # Should not have LYT-ACE or PARA specific links
        assert "[[Atlas/" not in content
        assert "[[Projects/" not in content

    def test_unknown_methodology_uses_minimal(self):
        """Test unknown methodology falls back to minimal."""
        content = generate_home_note(
            "custom-methodology",
            ["note"],
            created_date=date(2025, 1, 15),
        )

        assert "[[Notes/_Notes_MOC|Notes]]" in content

    def test_methodology_name_uppercased(self):
        """Test methodology name is uppercased in content."""
        content = generate_home_note(
            "lyt-ace",
            ["map"],
            created_date=date(2025, 1, 15),
        )

        assert "LYT-ACE" in content

    def test_includes_getting_started_section(self):
        """Test home note includes getting started section."""
        content = generate_home_note(
            "lyt-ace",
            ["map"],
            created_date=date(2025, 1, 15),
        )

        assert "Getting Started" in content
        assert "Capture ideas" in content
        assert "Process and refine" in content

    def test_includes_customization_note(self):
        """Test home note includes customization note."""
        content = generate_home_note(
            "lyt-ace",
            ["map"],
            created_date=date(2025, 1, 15),
        )

        assert "This is your home base" in content
        assert "Customize it" in content

    def test_date_defaults_to_today(self):
        """Test that created_date defaults to today."""
        content = generate_home_note("minimal", ["note"])

        today = date.today().isoformat()
        assert f'created: "{today}"' in content

    def test_note_types_parameter_not_used_in_output(self):
        """Test that note_types parameter exists but links are methodology-based."""
        # This tests that note_types is accepted but the links
        # are determined by methodology, not note_types
        content1 = generate_home_note(
            "lyt-ace",
            ["map", "dot"],
            created_date=date(2025, 1, 15),
        )
        content2 = generate_home_note(
            "lyt-ace",
            ["project", "source", "daily"],
            created_date=date(2025, 1, 15),
        )

        # Both should have same LYT-ACE links regardless of note_types
        assert "[[Atlas/_Atlas_MOC|Atlas]]" in content1
        assert "[[Atlas/_Atlas_MOC|Atlas]]" in content2


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_generate_sample_notes_content_matches_generate_note_content(self, tmp_path):
        """Test that generate_sample_notes uses generate_note_content correctly."""
        note_types = {
            "dot": {
                "description": "Atomic notes for single ideas",
                "folder_hints": ["Atlas/Dots/"],
            },
        }
        up_links = {"Atlas/Dots/": "[[Atlas]]"}
        core_props = ["type", "created", "up", "tags"]

        generate_sample_notes(
            tmp_path,
            "lyt-ace",
            note_types,
            core_props,
            up_links,
        )

        file_content = (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").read_text()

        # Verify frontmatter
        assert 'type: "dot"' in file_content
        assert 'up: "[[Atlas]]"' in file_content
        assert "tags: [sample, lyt-ace]" in file_content

        # Verify body
        assert "# Getting Started with Dots" in file_content
        assert "Atomic notes for single ideas" in file_content

    def test_complete_vault_setup(self, tmp_path):
        """Test generating a complete vault with home note and sample notes."""
        methodology = "lyt-ace"
        note_types = {
            "map": {
                "description": "Index notes",
                "folder_hints": ["Atlas/Maps/"],
            },
            "dot": {
                "description": "Atomic notes",
                "folder_hints": ["Atlas/Dots/"],
            },
            "daily": {
                "description": "Daily journals",
                "folder_hints": ["Calendar/daily/"],
            },
        }
        up_links = {
            "Atlas/Maps/": "[[Atlas]]",
            "Atlas/Dots/": "[[Atlas]]",
            "Calendar/daily/": "[[Calendar]]",
        }
        core_props = ["type", "created", "up", "daily", "tags"]

        # Generate home note
        home_content = generate_home_note(
            methodology,
            list(note_types.keys()),
            created_date=date(2025, 1, 15),
        )
        home_path = tmp_path / "Home.md"
        home_path.write_text(home_content)

        # Generate sample notes
        created = generate_sample_notes(
            tmp_path,
            methodology,
            note_types,
            core_props,
            up_links,
        )

        # Verify all files created
        assert home_path.exists()
        assert len(created) == 3

        # Verify home note content
        assert "LYT-ACE" in home_content
        assert "[[Atlas/_Atlas_MOC|Atlas]]" in home_content

        # Verify sample notes exist
        assert (tmp_path / "Atlas" / "Maps" / "Getting Started with Maps.md").exists()
        assert (tmp_path / "Atlas" / "Dots" / "Getting Started with Dots.md").exists()
