"""
Unit tests for skills.core.models.wizard module.

Tests the WizardConfig dataclass including:
- Instantiation with required/optional fields
- Default values for optional fields
- get_all_properties() method with deduplication
- get_properties_for_type() method with and without overrides
"""

from skills.core.models.note_type import NoteTypeConfig
from skills.core.models.wizard import WizardConfig


class TestWizardConfigInstantiation:
    """Tests for WizardConfig instantiation."""

    def test_instantiation_with_required_fields_only(self):
        """Test creating WizardConfig with only required fields."""
        config = WizardConfig(
            methodology="lyt-ace",
            note_types={"Dot": {"description": "A note type"}},
            core_properties=["type", "up", "created"],
        )

        assert config.methodology == "lyt-ace"
        assert config.note_types == {"Dot": {"description": "A note type"}}
        assert config.core_properties == ["type", "up", "created"]

    def test_instantiation_with_all_fields(self):
        """Test creating WizardConfig with all fields set."""
        custom_note_type = NoteTypeConfig(
            name="CustomType",
            description="A custom note type",
            folder_hints=["Custom/"],
            required_properties=["type", "up"],
            optional_properties=["tags"],
        )

        config = WizardConfig(
            methodology="zettelkasten",
            note_types={
                "Permanent": {"description": "Permanent notes"},
                "Literature": {"description": "Literature notes"},
            },
            core_properties=["type", "up", "created"],
            mandatory_properties=["tags", "source"],
            optional_properties=["related", "collection"],
            custom_properties=["custom_field", "project"],
            custom_note_types={"CustomType": custom_note_type},
            per_type_properties={
                "Permanent": {
                    "required": ["type", "up", "created", "tags"],
                    "optional": ["related"],
                },
            },
            create_samples=False,
            reset_vault=True,
            ranking_system="priority",
            init_git=True,
        )

        assert config.methodology == "zettelkasten"
        assert len(config.note_types) == 2
        assert config.core_properties == ["type", "up", "created"]
        assert config.mandatory_properties == ["tags", "source"]
        assert config.optional_properties == ["related", "collection"]
        assert config.custom_properties == ["custom_field", "project"]
        assert "CustomType" in config.custom_note_types
        assert config.custom_note_types["CustomType"].name == "CustomType"
        assert "Permanent" in config.per_type_properties
        assert config.create_samples is False
        assert config.reset_vault is True
        assert config.ranking_system == "priority"
        assert config.init_git is True


class TestWizardConfigDefaultValues:
    """Tests for default values of optional fields."""

    def test_default_mandatory_properties(self):
        """Test that mandatory_properties defaults to empty list."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.mandatory_properties == []

    def test_default_optional_properties(self):
        """Test that optional_properties defaults to empty list."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.optional_properties == []

    def test_default_custom_properties(self):
        """Test that custom_properties defaults to empty list."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.custom_properties == []

    def test_default_custom_note_types(self):
        """Test that custom_note_types defaults to empty dict."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.custom_note_types == {}

    def test_default_per_type_properties(self):
        """Test that per_type_properties defaults to empty dict."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.per_type_properties == {}

    def test_default_create_samples(self):
        """Test that create_samples defaults to True."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.create_samples is True

    def test_default_reset_vault(self):
        """Test that reset_vault defaults to False."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.reset_vault is False

    def test_default_ranking_system(self):
        """Test that ranking_system defaults to 'rank'."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.ranking_system == "rank"

    def test_default_init_git(self):
        """Test that init_git defaults to False."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )
        assert config.init_git is False


class TestGetAllProperties:
    """Tests for get_all_properties() method."""

    def test_get_all_properties_core_only(self):
        """Test get_all_properties with only core properties."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up", "created"],
        )

        all_props = config.get_all_properties()

        assert set(all_props) == {"type", "up", "created"}

    def test_get_all_properties_all_categories(self):
        """Test get_all_properties with all property categories."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up", "created"],
            mandatory_properties=["tags", "source"],
            optional_properties=["related", "collection"],
            custom_properties=["custom_field"],
        )

        all_props = config.get_all_properties()

        expected = {
            "type",
            "up",
            "created",
            "tags",
            "source",
            "related",
            "collection",
            "custom_field",
        }
        assert set(all_props) == expected

    def test_get_all_properties_deduplicates(self):
        """Test that get_all_properties removes duplicates."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up", "created"],
            mandatory_properties=["type", "tags"],  # "type" is duplicate
            optional_properties=["up", "related"],  # "up" is duplicate
            custom_properties=["created", "custom"],  # "created" is duplicate
        )

        all_props = config.get_all_properties()

        # Should have no duplicates
        assert len(all_props) == len(set(all_props))
        # Should contain all unique properties
        expected = {"type", "up", "created", "tags", "related", "custom"}
        assert set(all_props) == expected

    def test_get_all_properties_empty_lists(self):
        """Test get_all_properties with empty property lists."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=[],
            mandatory_properties=[],
            optional_properties=[],
            custom_properties=[],
        )

        all_props = config.get_all_properties()

        assert all_props == []

    def test_get_all_properties_returns_list(self):
        """Test that get_all_properties returns a list (not a set)."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up"],
        )

        all_props = config.get_all_properties()

        assert isinstance(all_props, list)


class TestGetPropertiesForType:
    """Tests for get_properties_for_type() method."""

    def test_get_properties_for_type_with_override(self):
        """Test get_properties_for_type when per_type_properties has an override."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up", "created"],
            mandatory_properties=["tags"],
            optional_properties=["related", "collection"],
            per_type_properties={
                "Project": {
                    "required": ["type", "up", "created", "status", "deadline"],
                    "optional": ["assignee", "priority"],
                },
            },
        )

        result = config.get_properties_for_type("Project")

        assert result == {
            "required": ["type", "up", "created", "status", "deadline"],
            "optional": ["assignee", "priority"],
        }

    def test_get_properties_for_type_without_override(self):
        """Test get_properties_for_type when no override exists (returns defaults)."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up", "created"],
            mandatory_properties=["tags", "source"],
            optional_properties=["related", "collection"],
        )

        result = config.get_properties_for_type("Dot")

        expected = {
            "required": ["type", "up", "created", "tags", "source"],
            "optional": ["related", "collection"],
        }
        assert result == expected

    def test_get_properties_for_type_default_with_empty_mandatory(self):
        """Test default properties when mandatory_properties is empty."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up"],
            mandatory_properties=[],
            optional_properties=["related"],
        )

        result = config.get_properties_for_type("SomeType")

        assert result == {
            "required": ["type", "up"],
            "optional": ["related"],
        }

    def test_get_properties_for_type_default_with_empty_optional(self):
        """Test default properties when optional_properties is empty."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up"],
            mandatory_properties=["tags"],
            optional_properties=[],
        )

        result = config.get_properties_for_type("SomeType")

        assert result == {
            "required": ["type", "up", "tags"],
            "optional": [],
        }

    def test_get_properties_for_type_multiple_overrides(self):
        """Test that correct override is selected from multiple per_type_properties."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
            per_type_properties={
                "TypeA": {
                    "required": ["type", "field_a"],
                    "optional": ["opt_a"],
                },
                "TypeB": {
                    "required": ["type", "field_b"],
                    "optional": ["opt_b"],
                },
                "TypeC": {
                    "required": ["type", "field_c"],
                    "optional": ["opt_c"],
                },
            },
        )

        result_a = config.get_properties_for_type("TypeA")
        result_b = config.get_properties_for_type("TypeB")
        result_c = config.get_properties_for_type("TypeC")

        assert result_a["required"] == ["type", "field_a"]
        assert result_a["optional"] == ["opt_a"]
        assert result_b["required"] == ["type", "field_b"]
        assert result_b["optional"] == ["opt_b"]
        assert result_c["required"] == ["type", "field_c"]
        assert result_c["optional"] == ["opt_c"]

    def test_get_properties_for_type_nonexistent_type_uses_default(self):
        """Test that a type not in per_type_properties uses defaults."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up"],
            mandatory_properties=["tags"],
            optional_properties=["related"],
            per_type_properties={
                "SpecialType": {
                    "required": ["type", "special"],
                    "optional": [],
                },
            },
        )

        # Request a type that doesn't have an override
        result = config.get_properties_for_type("RegularType")

        assert result == {
            "required": ["type", "up", "tags"],
            "optional": ["related"],
        }

    def test_get_properties_for_type_empty_override(self):
        """Test that empty override values are returned correctly."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type", "up"],
            mandatory_properties=["tags"],
            optional_properties=["related"],
            per_type_properties={
                "MinimalType": {
                    "required": [],
                    "optional": [],
                },
            },
        )

        result = config.get_properties_for_type("MinimalType")

        assert result == {
            "required": [],
            "optional": [],
        }


class TestWizardConfigDataclassBehavior:
    """Tests for dataclass-specific behavior."""

    def test_equality_same_values(self):
        """Test that two configs with same values are equal."""
        config1 = WizardConfig(
            methodology="test",
            note_types={"A": {}},
            core_properties=["type"],
        )
        config2 = WizardConfig(
            methodology="test",
            note_types={"A": {}},
            core_properties=["type"],
        )

        assert config1 == config2

    def test_equality_different_values(self):
        """Test that configs with different values are not equal."""
        config1 = WizardConfig(
            methodology="test1",
            note_types={},
            core_properties=["type"],
        )
        config2 = WizardConfig(
            methodology="test2",
            note_types={},
            core_properties=["type"],
        )

        assert config1 != config2

    def test_field_mutability(self):
        """Test that mutable fields can be modified after creation."""
        config = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=["type"],
        )

        # Modify mutable fields
        config.core_properties.append("up")
        config.mandatory_properties.append("tags")
        config.note_types["NewType"] = {"description": "Added"}

        assert "up" in config.core_properties
        assert "tags" in config.mandatory_properties
        assert "NewType" in config.note_types

    def test_default_factory_creates_new_instances(self):
        """Test that default_factory creates new list/dict instances."""
        config1 = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=[],
        )
        config2 = WizardConfig(
            methodology="test",
            note_types={},
            core_properties=[],
        )

        # Modify config1's mutable defaults
        config1.mandatory_properties.append("modified")
        config1.per_type_properties["key"] = {"value": []}

        # config2 should not be affected
        assert config2.mandatory_properties == []
        assert config2.per_type_properties == {}
