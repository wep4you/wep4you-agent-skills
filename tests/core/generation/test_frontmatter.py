"""
Unit tests for the frontmatter module.

Tests cover:
- generate_frontmatter(): Creates YAML frontmatter with various parameters
- parse_frontmatter(): Parses frontmatter from markdown content
- update_frontmatter(): Updates frontmatter in markdown content
- get_property_default(): Gets default value for a property
- Constants: DEFAULT_CORE_PROPERTIES, DEFAULT_TYPE_PROPERTIES
"""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from skills.core.generation.frontmatter import (
    DEFAULT_CORE_PROPERTIES,
    DEFAULT_TYPE_PROPERTIES,
    generate_frontmatter,
    get_property_default,
    parse_frontmatter,
    update_frontmatter,
)


class TestDefaultCoreProperties:
    """Tests for DEFAULT_CORE_PROPERTIES constant."""

    def test_contains_required_properties(self):
        """Verify all expected core properties are present."""
        expected_keys = {"type", "up", "created", "daily", "collection", "related"}
        assert expected_keys == set(DEFAULT_CORE_PROPERTIES.keys())

    def test_type_property_is_required(self):
        """Type property should be marked as required."""
        assert DEFAULT_CORE_PROPERTIES["type"]["required"] is True
        assert DEFAULT_CORE_PROPERTIES["type"]["type"] == "string"

    def test_created_property_has_date_format(self):
        """Created property should have date type and format."""
        created = DEFAULT_CORE_PROPERTIES["created"]
        assert created["required"] is True
        assert created["type"] == "date"
        assert created["format"] == "YYYY-MM-DD"

    def test_related_property_is_list(self):
        """Related property should be a list of wikilinks."""
        related = DEFAULT_CORE_PROPERTIES["related"]
        assert related["required"] is False
        assert related["type"] == "list[wikilink]"


class TestDefaultTypeProperties:
    """Tests for DEFAULT_TYPE_PROPERTIES constant."""

    def test_contains_expected_note_types(self):
        """Verify all expected note types are present."""
        expected_types = {"dot", "map", "source", "project", "daily"}
        assert expected_types == set(DEFAULT_TYPE_PROPERTIES.keys())

    def test_dot_type_has_tags(self):
        """Dot type should have tags property."""
        dot_props = DEFAULT_TYPE_PROPERTIES["dot"]
        assert "tags" in dot_props
        assert dot_props["tags"]["type"] == "list[string]"

    def test_project_status_has_allowed_values(self):
        """Project status should have specific allowed values."""
        project_props = DEFAULT_TYPE_PROPERTIES["project"]
        assert "status" in project_props
        assert project_props["status"]["required"] is True
        assert project_props["status"]["values"] == [
            "active",
            "completed",
            "archived",
            "planning",
        ]

    def test_source_has_author_and_url(self):
        """Source type should have author and url properties."""
        source_props = DEFAULT_TYPE_PROPERTIES["source"]
        assert "author" in source_props
        assert "url" in source_props
        assert "published" in source_props

    def test_daily_mood_has_values(self):
        """Daily type should have mood with allowed values."""
        daily_props = DEFAULT_TYPE_PROPERTIES["daily"]
        assert "mood" in daily_props
        assert daily_props["mood"]["values"] == ["great", "good", "neutral", "bad"]


class TestGenerateFrontmatter:
    """Tests for generate_frontmatter function."""

    def test_basic_frontmatter_generation(self):
        """Generate basic frontmatter with just note type."""
        result = generate_frontmatter("dot", created_date=date(2025, 1, 15))

        assert result.startswith("---")
        assert result.endswith("---")
        assert 'type: "dot"' in result
        assert 'created: "2025-01-15"' in result

    def test_frontmatter_with_up_link(self):
        """Generate frontmatter with parent link."""
        result = generate_frontmatter(
            "dot",
            up_link="[[Home]]",
            created_date=date(2025, 1, 15),
        )

        assert 'up: "[[Home]]"' in result

    def test_frontmatter_with_daily_link(self):
        """Generate frontmatter with daily note link."""
        result = generate_frontmatter(
            "dot",
            daily_link="[[2025-01-15]]",
            created_date=date(2025, 1, 15),
        )

        assert 'daily: "[[2025-01-15]]"' in result

    def test_frontmatter_with_tags(self):
        """Generate frontmatter with tags."""
        result = generate_frontmatter(
            "dot",
            tags=["python", "testing"],
            created_date=date(2025, 1, 15),
        )

        assert "tags: [python, testing]" in result

    def test_frontmatter_with_empty_tags(self):
        """Generate frontmatter with empty tags list."""
        result = generate_frontmatter(
            "dot",
            tags=[],
            created_date=date(2025, 1, 15),
        )

        assert "tags: []" in result

    def test_frontmatter_with_no_tags_provided(self):
        """Generate frontmatter when tags is None uses empty list."""
        result = generate_frontmatter(
            "dot",
            created_date=date(2025, 1, 15),
        )

        assert "tags: []" in result

    def test_frontmatter_with_collection(self):
        """Generate frontmatter with collection."""
        result = generate_frontmatter(
            "dot",
            collection="[[Software]]",
            created_date=date(2025, 1, 15),
        )

        assert 'collection: "[[Software]]"' in result

    def test_frontmatter_with_empty_collection(self):
        """Generate frontmatter with empty collection."""
        result = generate_frontmatter(
            "dot",
            collection=None,
            created_date=date(2025, 1, 15),
        )

        assert 'collection: ""' in result

    def test_frontmatter_with_related_links(self):
        """Generate frontmatter with related links."""
        result = generate_frontmatter(
            "dot",
            related=["[[Python]]", "[[Testing]]"],
            created_date=date(2025, 1, 15),
        )

        assert 'related: ["[[Python]]", "[[Testing]]"]' in result

    def test_frontmatter_with_empty_related(self):
        """Generate frontmatter with empty related list."""
        result = generate_frontmatter(
            "dot",
            related=[],
            created_date=date(2025, 1, 15),
        )

        assert "related: []" in result

    def test_frontmatter_with_additional_string_property(self):
        """Generate frontmatter with additional string properties."""
        result = generate_frontmatter(
            "source",
            additional_properties={"author": "John Doe"},
            created_date=date(2025, 1, 15),
        )

        assert 'author: "John Doe"' in result

    def test_frontmatter_with_additional_boolean_property(self):
        """Generate frontmatter with additional boolean property."""
        result = generate_frontmatter(
            "dot",
            additional_properties={"completed": True, "archived": False},
            created_date=date(2025, 1, 15),
        )

        assert "completed: true" in result
        assert "archived: false" in result

    def test_frontmatter_with_additional_list_property(self):
        """Generate frontmatter with additional list property."""
        result = generate_frontmatter(
            "dot",
            additional_properties={"links": ["a", "b", "c"]},
            created_date=date(2025, 1, 15),
        )

        assert 'links: ["a", "b", "c"]' in result

    def test_frontmatter_with_additional_empty_list_property(self):
        """Generate frontmatter with additional empty list property."""
        result = generate_frontmatter(
            "dot",
            additional_properties={"links": []},
            created_date=date(2025, 1, 15),
        )

        assert "links: []" in result

    def test_frontmatter_with_additional_numeric_property(self):
        """Generate frontmatter with additional numeric property."""
        result = generate_frontmatter(
            "dot",
            additional_properties={"rank": 5, "score": 3.14},
            created_date=date(2025, 1, 15),
        )

        assert "rank: 5" in result
        assert "score: 3.14" in result

    def test_frontmatter_with_additional_none_property(self):
        """Generate frontmatter with additional None property (becomes empty string)."""
        result = generate_frontmatter(
            "dot",
            additional_properties={"custom": None},
            created_date=date(2025, 1, 15),
        )

        assert 'custom: ""' in result

    def test_frontmatter_with_optional_commented_properties(self):
        """Generate frontmatter with commented optional properties."""
        result = generate_frontmatter(
            "source",
            optional_commented=["author", "url"],
            created_date=date(2025, 1, 15),
        )

        assert "# author: " in result
        assert "# url: " in result

    def test_frontmatter_with_custom_core_properties(self):
        """Generate frontmatter with custom subset of core properties."""
        result = generate_frontmatter(
            "dot",
            core_properties=["type", "created"],
            created_date=date(2025, 1, 15),
        )

        assert 'type: "dot"' in result
        assert 'created: "2025-01-15"' in result
        # These should not be present
        assert "tags:" not in result
        assert "collection:" not in result
        assert "related:" not in result

    def test_frontmatter_defaults_to_today_date(self):
        """Generate frontmatter uses today's date when not specified."""
        with patch("skills.core.generation.frontmatter.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
            result = generate_frontmatter("dot", core_properties=["type", "created"])

        assert 'created: "2025-06-15"' in result

    def test_frontmatter_property_order(self):
        """Verify properties appear in expected order."""
        result = generate_frontmatter(
            "dot",
            up_link="[[Home]]",
            daily_link="[[2025-01-15]]",
            tags=["test"],
            collection="[[Software]]",
            related=["[[Python]]"],
            created_date=date(2025, 1, 15),
        )

        lines = result.strip().split("\n")
        # Skip --- delimiters
        content_lines = [line for line in lines if line != "---"]

        # Type should be first
        assert content_lines[0] == 'type: "dot"'

        # Check relative ordering
        type_idx = content_lines.index('type: "dot"')
        up_idx = content_lines.index('up: "[[Home]]"')
        created_idx = content_lines.index('created: "2025-01-15"')
        daily_idx = content_lines.index('daily: "[[2025-01-15]]"')

        assert type_idx < up_idx < created_idx < daily_idx


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_parse_simple_frontmatter(self, sample_frontmatter_yaml):
        """Parse simple frontmatter successfully."""
        content = sample_frontmatter_yaml + "\n\nSome body content."

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["type"] == "Dot"
        assert frontmatter["up"] == "[[Home]]"
        # YAML may parse date as date object or string depending on format
        assert frontmatter["created"] in [date(2025, 1, 15), "2025-01-15"]
        assert body == "Some body content."

    def test_parse_frontmatter_with_list_values(self, sample_frontmatter_yaml):
        """Parse frontmatter with list values."""
        content = sample_frontmatter_yaml + "\n\nBody"

        frontmatter, _ = parse_frontmatter(content)

        assert frontmatter["collection"] == ["[[Software]]"]
        assert frontmatter["related"] == ["[[Python]]"]

    def test_parse_content_without_frontmatter(self):
        """Parse content without frontmatter returns empty dict and full content."""
        content = "# Just a heading\n\nSome content here."

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_parse_empty_content(self):
        """Parse empty content returns empty dict and empty string."""
        frontmatter, body = parse_frontmatter("")

        assert frontmatter == {}
        assert body == ""

    def test_parse_whitespace_only_content(self):
        """Parse whitespace-only content returns empty dict."""
        frontmatter, body = parse_frontmatter("   \n\n   ")

        assert frontmatter == {}
        assert body == ""

    def test_parse_frontmatter_missing_closing_delimiter(self):
        """Parse frontmatter with missing closing --- raises ValueError."""
        content = "---\ntype: Dot\n\nSome content"

        with pytest.raises(ValueError, match="missing closing ---"):
            parse_frontmatter(content)

    def test_parse_frontmatter_invalid_yaml(self):
        """Parse frontmatter with invalid YAML raises ValueError."""
        content = "---\ntype: [unclosed\n---\n\nBody"

        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_frontmatter(content)

    def test_parse_empty_frontmatter(self):
        """Parse empty frontmatter returns empty dict."""
        content = "---\n---\n\nBody content"

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == "Body content"

    def test_parse_frontmatter_with_boolean_values(self):
        """Parse frontmatter with boolean values."""
        content = "---\ncompleted: true\narchived: false\n---\n\nBody"

        frontmatter, _ = parse_frontmatter(content)

        assert frontmatter["completed"] is True
        assert frontmatter["archived"] is False

    def test_parse_frontmatter_with_numeric_values(self):
        """Parse frontmatter with numeric values."""
        content = "---\nrank: 5\nscore: 3.14\n---\n\nBody"

        frontmatter, _ = parse_frontmatter(content)

        assert frontmatter["rank"] == 5
        assert frontmatter["score"] == 3.14

    def test_parse_frontmatter_with_date_value(self):
        """Parse frontmatter with date value (parsed as date or string)."""
        content = "---\ncreated: 2025-01-15\n---\n\nBody"

        frontmatter, _ = parse_frontmatter(content)

        # YAML may parse this as a date object or string
        assert frontmatter["created"] in [date(2025, 1, 15), "2025-01-15"]

    def test_parse_frontmatter_with_multiline_body(self):
        """Parse frontmatter with multiline body content."""
        content = "---\ntype: Dot\n---\n\n# Heading\n\nParagraph 1\n\nParagraph 2"

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["type"] == "Dot"
        assert "# Heading" in body
        assert "Paragraph 1" in body
        assert "Paragraph 2" in body

    def test_parse_frontmatter_with_triple_dashes_in_body(self):
        """Parse content where body contains triple dashes (not at line start)."""
        content = "---\ntype: Dot\n---\n\nBody with --- in middle"

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["type"] == "Dot"
        assert "Body with --- in middle" in body

    def test_parse_frontmatter_with_inline_list(self):
        """Parse frontmatter with inline list syntax."""
        content = "---\ntags: [python, testing, code]\n---\n\nBody"

        frontmatter, _ = parse_frontmatter(content)

        assert frontmatter["tags"] == ["python", "testing", "code"]

    def test_parse_frontmatter_with_quoted_strings(self):
        """Parse frontmatter with quoted string values."""
        content = '---\nup: "[[Home]]"\ndaily: \'[[2025-01-15]]\'\n---\n\nBody'

        frontmatter, _ = parse_frontmatter(content)

        assert frontmatter["up"] == "[[Home]]"
        assert frontmatter["daily"] == "[[2025-01-15]]"


class TestUpdateFrontmatter:
    """Tests for update_frontmatter function."""

    def test_update_single_property(self, sample_frontmatter_yaml):
        """Update a single frontmatter property."""
        content = sample_frontmatter_yaml + "\n\nBody content"

        result = update_frontmatter(content, {"type": "Map"})

        assert "type: Map" in result
        assert "Body content" in result

    def test_update_multiple_properties(self, sample_frontmatter_yaml):
        """Update multiple frontmatter properties."""
        content = sample_frontmatter_yaml + "\n\nBody content"

        result = update_frontmatter(content, {"type": "Map", "up": "[[New Parent]]"})

        assert "type: Map" in result
        assert "up: '[[New Parent]]'" in result

    def test_add_new_property(self, sample_frontmatter_yaml):
        """Add a new property to existing frontmatter."""
        content = sample_frontmatter_yaml + "\n\nBody content"

        result = update_frontmatter(content, {"author": "John Doe"})

        assert "author: John Doe" in result

    def test_remove_property(self, sample_frontmatter_yaml):
        """Remove a property from frontmatter."""
        content = sample_frontmatter_yaml + "\n\nBody content"

        result = update_frontmatter(content, {}, remove_keys=["daily"])

        assert "daily:" not in result
        assert "type:" in result  # Other props remain

    def test_update_and_remove_properties(self, sample_frontmatter_yaml):
        """Update and remove properties simultaneously."""
        content = sample_frontmatter_yaml + "\n\nBody content"

        result = update_frontmatter(
            content,
            {"type": "Source"},
            remove_keys=["daily", "collection"],
        )

        assert "type: Source" in result
        assert "daily:" not in result
        assert "collection:" not in result

    def test_update_preserves_body_content(self, sample_frontmatter_yaml):
        """Update preserves the body content after frontmatter."""
        body = """# Heading

Paragraph with some content.

- List item 1
- List item 2
"""
        content = sample_frontmatter_yaml + "\n\n" + body

        result = update_frontmatter(content, {"type": "Map"})

        assert "# Heading" in result
        assert "Paragraph with some content." in result
        assert "- List item 1" in result

    def test_update_content_without_frontmatter(self):
        """Update content that has no frontmatter adds frontmatter."""
        content = "# Just a heading\n\nSome content."

        result = update_frontmatter(content, {"type": "Dot"})

        assert result.startswith("---")
        assert "type: Dot" in result
        assert "# Just a heading" in result

    def test_update_with_empty_updates_preserves_frontmatter(
        self, sample_frontmatter_yaml
    ):
        """Empty updates dict preserves all existing frontmatter."""
        content = sample_frontmatter_yaml + "\n\nBody"

        result = update_frontmatter(content, {})

        # All original properties should be preserved
        assert "type:" in result
        assert "up:" in result
        assert "created:" in result

    def test_update_with_list_value(self, sample_frontmatter_yaml):
        """Update with a list value."""
        content = sample_frontmatter_yaml + "\n\nBody"

        result = update_frontmatter(
            content, {"related": ["[[New Note 1]]", "[[New Note 2]]"]}
        )

        assert "[[New Note 1]]" in result
        assert "[[New Note 2]]" in result

    def test_update_with_boolean_value(self, sample_frontmatter_yaml):
        """Update with boolean value."""
        content = sample_frontmatter_yaml + "\n\nBody"

        result = update_frontmatter(content, {"completed": True})

        assert "completed: true" in result

    def test_update_removes_all_properties_returns_body_only(self):
        """Removing all properties returns just the body."""
        content = "---\ntype: Dot\n---\n\nBody content only"

        result = update_frontmatter(content, {}, remove_keys=["type"])

        assert result == "Body content only"
        assert "---" not in result

    def test_update_malformed_frontmatter_raises_error(self):
        """Update on malformed frontmatter raises ValueError."""
        content = "---\ntype: Dot\n\nBody without closing"

        with pytest.raises(ValueError):
            update_frontmatter(content, {"type": "Map"})

    def test_update_removes_nonexistent_key_silently(self, sample_frontmatter_yaml):
        """Removing a non-existent key does not raise error."""
        content = sample_frontmatter_yaml + "\n\nBody"

        # Should not raise
        result = update_frontmatter(content, {}, remove_keys=["nonexistent_key"])

        assert "---" in result  # Frontmatter preserved


class TestGetPropertyDefault:
    """Tests for get_property_default function."""

    def test_get_default_for_core_string_property(self):
        """Get default for core string property returns empty string."""
        result = get_property_default("type")

        assert result == ""

    def test_get_default_for_core_date_property(self):
        """Get default for core date property returns today's date."""
        with patch("skills.core.generation.frontmatter.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)

            result = get_property_default("created")

        assert result == "2025-06-15"

    def test_get_default_for_core_list_property(self):
        """Get default for core list property returns empty list."""
        result = get_property_default("related")

        assert result == []

    def test_get_default_for_type_specific_property_with_values(self):
        """Get default for type property with allowed values returns first value."""
        result = get_property_default("status", note_type="project")

        assert result == "active"

    def test_get_default_for_type_specific_list_property(self):
        """Get default for type-specific list property returns empty list."""
        result = get_property_default("tags", note_type="dot")

        assert result == []

    def test_get_default_for_type_specific_string_property(self):
        """Get default for type-specific string property returns empty string."""
        result = get_property_default("author", note_type="source")

        assert result == ""

    def test_get_default_for_special_status_property(self):
        """Get default for status property without type returns active."""
        result = get_property_default("status")

        assert result == "active"

    def test_get_default_for_special_rank_property(self):
        """Get default for rank property returns 3."""
        result = get_property_default("rank")

        assert result == 3

    def test_get_default_for_special_priority_property(self):
        """Get default for priority property returns medium."""
        result = get_property_default("priority")

        assert result == "medium"

    def test_get_default_for_unknown_property(self):
        """Get default for unknown property returns empty string."""
        result = get_property_default("totally_unknown_property")

        assert result == ""

    def test_get_default_with_nonexistent_note_type(self):
        """Get default with non-existent note type checks core properties."""
        result = get_property_default("related", note_type="nonexistent")

        assert result == []  # Falls back to core property default

    def test_get_default_daily_mood_property(self):
        """Get default for daily mood returns first allowed value."""
        result = get_property_default("mood", note_type="daily")

        assert result == "great"


class TestFrontmatterIntegration:
    """Integration tests combining multiple frontmatter functions."""

    def test_generate_then_parse_roundtrip(self):
        """Generate frontmatter then parse it back."""
        generated = generate_frontmatter(
            "dot",
            up_link="[[Home]]",
            tags=["python", "testing"],
            related=["[[Note A]]"],
            created_date=date(2025, 1, 15),
        )

        # Add body content
        full_content = generated + "\n\n# Body\n\nContent here."

        # Parse it back
        frontmatter, body = parse_frontmatter(full_content)

        assert frontmatter["type"] == "dot"
        assert frontmatter["up"] == "[[Home]]"
        assert "python" in frontmatter["tags"]
        assert "testing" in frontmatter["tags"]
        assert "# Body" in body

    def test_generate_update_parse_cycle(self):
        """Generate, update, then parse frontmatter."""
        generated = generate_frontmatter(
            "dot",
            up_link="[[Home]]",
            created_date=date(2025, 1, 15),
        )

        full_content = generated + "\n\nBody content"

        # Update it
        updated = update_frontmatter(
            full_content,
            {"type": "map", "summary": "New summary"},
            remove_keys=["up"],
        )

        # Parse the updated version
        frontmatter, body = parse_frontmatter(updated)

        assert frontmatter["type"] == "map"
        assert frontmatter["summary"] == "New summary"
        assert "up" not in frontmatter
        assert "Body content" in body

    def test_update_with_property_defaults(self):
        """Use get_property_default to set defaults when updating."""
        content = "---\ntype: project\n---\n\nBody"

        # Get default status for project type
        default_status = get_property_default("status", note_type="project")

        # Update with the default
        result = update_frontmatter(content, {"status": default_status})

        assert "status: active" in result
