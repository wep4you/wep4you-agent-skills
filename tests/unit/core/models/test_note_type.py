"""
Unit tests for NoteTypeConfig dataclass.

Tests cover:
- NoteTypeConfig instantiation with defaults
- NoteTypeConfig with all fields set
- to_dict() - returns correct structure for YAML serialization
- from_dict() - with inherit_core=True (adds core properties)
- from_dict() - with inherit_core=False (uses explicit required)
- from_dict() - old format with "required" key
- from_dict() - new format with "additional_required" key
- get_all_properties() - combines required and optional
"""

from __future__ import annotations

from skills.core.models.note_type import NoteTypeConfig


class TestNoteTypeConfigInstantiation:
    """Tests for NoteTypeConfig instantiation and defaults."""

    def test_instantiation_with_required_fields_only(self):
        """Create NoteTypeConfig with only required fields."""
        config = NoteTypeConfig(
            name="test",
            description="A test note type",
            folder_hints=["test/"],
        )

        assert config.name == "test"
        assert config.description == "A test note type"
        assert config.folder_hints == ["test/"]

    def test_default_required_properties_is_empty_list(self):
        """Default required_properties should be an empty list."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
        )

        assert config.required_properties == []
        assert isinstance(config.required_properties, list)

    def test_default_optional_properties_is_empty_list(self):
        """Default optional_properties should be an empty list."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
        )

        assert config.optional_properties == []
        assert isinstance(config.optional_properties, list)

    def test_default_validation_is_empty_dict(self):
        """Default validation should be an empty dict."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
        )

        assert config.validation == {}
        assert isinstance(config.validation, dict)

    def test_default_icon_is_file(self):
        """Default icon should be 'file'."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
        )

        assert config.icon == "file"

    def test_default_is_custom_is_false(self):
        """Default is_custom should be False."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
        )

        assert config.is_custom is False

    def test_default_inherit_core_is_true(self):
        """Default inherit_core should be True."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
        )

        assert config.inherit_core is True

    def test_instantiation_with_all_fields(self):
        """Create NoteTypeConfig with all fields explicitly set."""
        config = NoteTypeConfig(
            name="project",
            description="Project note type",
            folder_hints=["Projects/", "Work/Projects/"],
            required_properties=["type", "up", "created", "status"],
            optional_properties=["deadline", "priority"],
            validation={"status": {"values": ["active", "completed"]}},
            icon="folder",
            is_custom=True,
            inherit_core=False,
        )

        assert config.name == "project"
        assert config.description == "Project note type"
        assert config.folder_hints == ["Projects/", "Work/Projects/"]
        assert config.required_properties == ["type", "up", "created", "status"]
        assert config.optional_properties == ["deadline", "priority"]
        assert config.validation == {"status": {"values": ["active", "completed"]}}
        assert config.icon == "folder"
        assert config.is_custom is True
        assert config.inherit_core is False

    def test_mutable_defaults_are_independent(self):
        """Each instance should have independent mutable defaults."""
        config1 = NoteTypeConfig(name="test1", description="Test 1", folder_hints=[])
        config2 = NoteTypeConfig(name="test2", description="Test 2", folder_hints=[])

        config1.required_properties.append("type")
        config1.optional_properties.append("tags")
        config1.validation["rule"] = "value"

        assert config2.required_properties == []
        assert config2.optional_properties == []
        assert config2.validation == {}


class TestNoteTypeConfigToDict:
    """Tests for to_dict() method."""

    def test_to_dict_returns_correct_structure(self):
        """to_dict should return a dictionary suitable for YAML serialization."""
        config = NoteTypeConfig(
            name="dot",
            description="Atomic note",
            folder_hints=["Atlas/Dots/"],
            required_properties=["type", "up", "created"],
            optional_properties=["tags", "related"],
            validation={"type": {"values": ["Dot"]}},
            icon="circle",
        )

        result = config.to_dict()

        assert isinstance(result, dict)
        assert "description" in result
        assert "folder_hints" in result
        assert "properties" in result
        assert "validation" in result
        assert "icon" in result

    def test_to_dict_description(self):
        """to_dict should include correct description."""
        config = NoteTypeConfig(
            name="dot",
            description="An atomic note",
            folder_hints=[],
        )

        result = config.to_dict()

        assert result["description"] == "An atomic note"

    def test_to_dict_folder_hints(self):
        """to_dict should include folder_hints."""
        config = NoteTypeConfig(
            name="dot",
            description="Test",
            folder_hints=["Atlas/Dots/", "Notes/Dots/"],
        )

        result = config.to_dict()

        assert result["folder_hints"] == ["Atlas/Dots/", "Notes/Dots/"]

    def test_to_dict_properties_structure(self):
        """to_dict should nest properties correctly."""
        config = NoteTypeConfig(
            name="dot",
            description="Test",
            folder_hints=[],
            required_properties=["type", "created"],
            optional_properties=["tags"],
        )

        result = config.to_dict()

        assert "properties" in result
        assert result["properties"]["additional_required"] == ["type", "created"]
        assert result["properties"]["optional"] == ["tags"]

    def test_to_dict_empty_properties(self):
        """to_dict should handle empty property lists."""
        config = NoteTypeConfig(
            name="dot",
            description="Test",
            folder_hints=[],
        )

        result = config.to_dict()

        assert result["properties"]["additional_required"] == []
        assert result["properties"]["optional"] == []

    def test_to_dict_validation(self):
        """to_dict should include validation rules."""
        validation_rules = {
            "status": {"values": ["active", "completed"]},
            "priority": {"type": "number"},
        }
        config = NoteTypeConfig(
            name="project",
            description="Test",
            folder_hints=[],
            validation=validation_rules,
        )

        result = config.to_dict()

        assert result["validation"] == validation_rules

    def test_to_dict_icon(self):
        """to_dict should include icon."""
        config = NoteTypeConfig(
            name="dot",
            description="Test",
            folder_hints=[],
            icon="star",
        )

        result = config.to_dict()

        assert result["icon"] == "star"

    def test_to_dict_excludes_name_and_flags(self):
        """to_dict should not include name, is_custom, or inherit_core."""
        config = NoteTypeConfig(
            name="dot",
            description="Test",
            folder_hints=[],
            is_custom=True,
            inherit_core=False,
        )

        result = config.to_dict()

        assert "name" not in result
        assert "is_custom" not in result
        assert "inherit_core" not in result


class TestNoteTypeConfigFromDictWithInheritCore:
    """Tests for from_dict() with inherit_core=True (default)."""

    def test_from_dict_with_inherit_core_default(self):
        """from_dict with default inherit_core=True adds core properties."""
        config_dict = {
            "description": "A dot note",
            "folder_hints": ["Atlas/Dots/"],
            "properties": {
                "additional_required": ["tags"],
                "optional": ["related"],
            },
        }
        core_properties = ["type", "up", "created"]

        result = NoteTypeConfig.from_dict("dot", config_dict, core_properties)

        assert result.name == "dot"
        assert result.inherit_core is True
        # Core properties should be prepended
        assert result.required_properties == ["type", "up", "created", "tags"]
        assert result.optional_properties == ["related"]

    def test_from_dict_with_explicit_inherit_core_true(self):
        """from_dict with explicit inherit_core=True adds core properties."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "inherit_core": True,
            "properties": {
                "additional_required": ["status"],
            },
        }
        core_properties = ["type", "up"]

        result = NoteTypeConfig.from_dict("project", config_dict, core_properties)

        assert result.required_properties == ["type", "up", "status"]

    def test_from_dict_with_empty_core_properties(self):
        """from_dict with empty core_properties list."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "properties": {
                "additional_required": ["field1"],
            },
        }

        result = NoteTypeConfig.from_dict("custom", config_dict, [])

        assert result.required_properties == ["field1"]

    def test_from_dict_with_none_core_properties(self):
        """from_dict with None core_properties defaults to empty list."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "properties": {
                "additional_required": ["field1"],
            },
        }

        result = NoteTypeConfig.from_dict("custom", config_dict, None)

        assert result.required_properties == ["field1"]


class TestNoteTypeConfigFromDictWithoutInheritCore:
    """Tests for from_dict() with inherit_core=False."""

    def test_from_dict_with_inherit_core_false(self):
        """from_dict with inherit_core=False uses explicit required list only."""
        config_dict = {
            "description": "Custom type",
            "folder_hints": ["Custom/"],
            "inherit_core": False,
            "properties": {
                "required": ["field1", "field2"],
                "optional": ["field3"],
            },
        }
        core_properties = ["type", "up", "created"]

        result = NoteTypeConfig.from_dict("custom", config_dict, core_properties)

        assert result.inherit_core is False
        # Should NOT include core properties
        assert result.required_properties == ["field1", "field2"]
        assert result.optional_properties == ["field3"]

    def test_from_dict_with_inherit_core_false_empty_required(self):
        """from_dict with inherit_core=False and no required properties."""
        config_dict = {
            "description": "Minimal type",
            "folder_hints": [],
            "inherit_core": False,
            "properties": {},
        }

        result = NoteTypeConfig.from_dict("minimal", config_dict, ["type", "up"])

        assert result.required_properties == []


class TestNoteTypeConfigFromDictOldFormat:
    """Tests for from_dict() with old format using "required" key."""

    def test_from_dict_old_format_with_required_key(self):
        """from_dict recognizes old format with 'required' key when inherit_core=True."""
        config_dict = {
            "description": "Old format type",
            "folder_hints": ["Old/"],
            "properties": {
                "required": ["type", "up", "created", "status"],
                "optional": ["tags"],
            },
        }
        core_properties = ["type", "up", "created"]

        result = NoteTypeConfig.from_dict("old", config_dict, core_properties)

        # Old format: required contains everything, so use it as-is
        assert result.required_properties == ["type", "up", "created", "status"]
        assert result.optional_properties == ["tags"]

    def test_from_dict_old_format_priority(self):
        """from_dict uses required key when additional_required is empty."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "properties": {
                "required": ["a", "b", "c"],
                "additional_required": [],  # Empty list is falsy
            },
        }

        result = NoteTypeConfig.from_dict("test", config_dict, ["type"])

        # When additional_required is empty (falsy), old format with required takes precedence
        assert result.required_properties == ["a", "b", "c"]


class TestNoteTypeConfigFromDictNewFormat:
    """Tests for from_dict() with new format using "additional_required" key."""

    def test_from_dict_new_format_with_additional_required(self):
        """from_dict uses new format with 'additional_required' key."""
        config_dict = {
            "description": "New format type",
            "folder_hints": ["New/"],
            "properties": {
                "additional_required": ["status", "deadline"],
                "optional": ["priority"],
            },
        }
        core_properties = ["type", "up", "created"]

        result = NoteTypeConfig.from_dict("new", config_dict, core_properties)

        # New format: core + additional
        assert result.required_properties == [
            "type",
            "up",
            "created",
            "status",
            "deadline",
        ]
        assert result.optional_properties == ["priority"]

    def test_from_dict_new_format_overrides_old_format(self):
        """from_dict prefers additional_required over required when both present."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "properties": {
                "required": ["should", "not", "use"],
                "additional_required": ["status"],
            },
        }
        core_properties = ["type", "up"]

        result = NoteTypeConfig.from_dict("test", config_dict, core_properties)

        # additional_required is non-empty, so new format is used
        assert result.required_properties == ["type", "up", "status"]
        assert "should" not in result.required_properties


class TestNoteTypeConfigFromDictOtherFields:
    """Tests for from_dict() handling of other fields."""

    def test_from_dict_description(self):
        """from_dict extracts description correctly."""
        config_dict = {
            "description": "A detailed description",
            "folder_hints": [],
        }

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.description == "A detailed description"

    def test_from_dict_description_default(self):
        """from_dict defaults description to empty string."""
        config_dict = {"folder_hints": []}

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.description == ""

    def test_from_dict_folder_hints(self):
        """from_dict extracts folder_hints correctly."""
        config_dict = {
            "description": "Test",
            "folder_hints": ["Folder1/", "Folder2/Sub/"],
        }

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.folder_hints == ["Folder1/", "Folder2/Sub/"]

    def test_from_dict_folder_hints_default(self):
        """from_dict defaults folder_hints to empty list."""
        config_dict = {"description": "Test"}

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.folder_hints == []

    def test_from_dict_validation(self):
        """from_dict extracts validation rules."""
        validation = {"status": {"values": ["a", "b"]}}
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "validation": validation,
        }

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.validation == validation

    def test_from_dict_validation_default(self):
        """from_dict defaults validation to empty dict."""
        config_dict = {"description": "Test", "folder_hints": []}

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.validation == {}

    def test_from_dict_icon(self):
        """from_dict extracts icon."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "icon": "star",
        }

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.icon == "star"

    def test_from_dict_icon_default(self):
        """from_dict defaults icon to 'file'."""
        config_dict = {"description": "Test", "folder_hints": []}

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.icon == "file"

    def test_from_dict_is_custom(self):
        """from_dict extracts is_custom flag."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "is_custom": True,
        }

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.is_custom is True

    def test_from_dict_is_custom_default(self):
        """from_dict defaults is_custom to False."""
        config_dict = {"description": "Test", "folder_hints": []}

        result = NoteTypeConfig.from_dict("test", config_dict, [])

        assert result.is_custom is False


class TestNoteTypeConfigGetAllProperties:
    """Tests for get_all_properties() method."""

    def test_get_all_properties_combines_required_and_optional(self):
        """get_all_properties returns required + optional."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
            required_properties=["type", "up", "created"],
            optional_properties=["tags", "related"],
        )

        result = config.get_all_properties()

        assert result == ["type", "up", "created", "tags", "related"]

    def test_get_all_properties_with_empty_required(self):
        """get_all_properties with empty required_properties."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
            required_properties=[],
            optional_properties=["field1", "field2"],
        )

        result = config.get_all_properties()

        assert result == ["field1", "field2"]

    def test_get_all_properties_with_empty_optional(self):
        """get_all_properties with empty optional_properties."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
            required_properties=["type", "up"],
            optional_properties=[],
        )

        result = config.get_all_properties()

        assert result == ["type", "up"]

    def test_get_all_properties_with_both_empty(self):
        """get_all_properties with both lists empty."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
        )

        result = config.get_all_properties()

        assert result == []

    def test_get_all_properties_maintains_order(self):
        """get_all_properties preserves order (required first, then optional)."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
            required_properties=["c", "a"],
            optional_properties=["d", "b"],
        )

        result = config.get_all_properties()

        assert result == ["c", "a", "d", "b"]

    def test_get_all_properties_returns_new_list(self):
        """get_all_properties returns a new list, not a reference."""
        config = NoteTypeConfig(
            name="test",
            description="Test",
            folder_hints=[],
            required_properties=["type"],
            optional_properties=["tags"],
        )

        result1 = config.get_all_properties()
        result2 = config.get_all_properties()

        assert result1 is not result2
        assert result1 == result2


class TestNoteTypeConfigIntegration:
    """Integration tests combining multiple NoteTypeConfig operations."""

    def test_from_dict_then_to_dict_roundtrip(self):
        """Create from_dict then convert to_dict for roundtrip."""
        original_dict = {
            "description": "A project note",
            "folder_hints": ["Projects/"],
            "properties": {
                "additional_required": ["status"],
                "optional": ["deadline", "priority"],
            },
            "validation": {"status": {"values": ["active", "done"]}},
            "icon": "folder",
        }
        core_properties = ["type", "up", "created"]

        # Create from dict
        config = NoteTypeConfig.from_dict("project", original_dict, core_properties)

        # Convert back to dict
        result_dict = config.to_dict()

        # Verify structure is preserved
        assert result_dict["description"] == "A project note"
        assert result_dict["folder_hints"] == ["Projects/"]
        assert result_dict["icon"] == "folder"
        assert result_dict["validation"] == {"status": {"values": ["active", "done"]}}

        # Note: required_properties includes core, so additional_required differs
        assert "status" in result_dict["properties"]["additional_required"]
        assert result_dict["properties"]["optional"] == ["deadline", "priority"]

    def test_get_all_properties_after_from_dict(self):
        """get_all_properties works correctly after from_dict."""
        config_dict = {
            "description": "Test",
            "folder_hints": [],
            "properties": {
                "additional_required": ["status"],
                "optional": ["tags", "related"],
            },
        }
        core_properties = ["type", "up", "created"]

        config = NoteTypeConfig.from_dict("test", config_dict, core_properties)
        all_props = config.get_all_properties()

        assert all_props == ["type", "up", "created", "status", "tags", "related"]
