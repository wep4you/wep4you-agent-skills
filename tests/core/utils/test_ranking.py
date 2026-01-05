"""
Tests for skills.core.utils.ranking module.

Tests ranking system utilities that apply rank or priority
properties to project-like notes in vault configuration.
"""

import pytest

from skills.core.utils.ranking import (
    RANKABLE_NOTE_TYPES,
    apply_ranking_system,
)


class TestRankableNoteTypes:
    """Tests for RANKABLE_NOTE_TYPES constant."""

    def test_is_frozenset(self):
        """Test that RANKABLE_NOTE_TYPES is a frozenset."""
        assert isinstance(RANKABLE_NOTE_TYPES, frozenset)

    def test_contains_project(self):
        """Test that project is in rankable types."""
        assert "project" in RANKABLE_NOTE_TYPES

    def test_contains_area(self):
        """Test that area is in rankable types."""
        assert "area" in RANKABLE_NOTE_TYPES

    def test_exact_contents(self):
        """Test exact contents of RANKABLE_NOTE_TYPES."""
        assert RANKABLE_NOTE_TYPES == frozenset({"project", "area"})

    def test_immutable(self):
        """Test that frozenset is immutable."""
        with pytest.raises(AttributeError):
            RANKABLE_NOTE_TYPES.add("new_type")

    def test_does_not_contain_other_types(self):
        """Test that non-project types are not in rankable types."""
        assert "dot" not in RANKABLE_NOTE_TYPES
        assert "daily" not in RANKABLE_NOTE_TYPES
        assert "source" not in RANKABLE_NOTE_TYPES
        assert "map" not in RANKABLE_NOTE_TYPES


class TestApplyRankingSystemWithRank:
    """Tests for apply_ranking_system with 'rank' system."""

    def test_adds_rank_to_project(self):
        """Test that rank is added to project additional_required."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "rank" in result["project"]["properties"]["additional_required"]

    def test_adds_rank_to_area(self):
        """Test that rank is added to area additional_required."""
        note_types = {
            "area": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "rank" in result["area"]["properties"]["additional_required"]

    def test_adds_rank_to_both_project_and_area(self):
        """Test that rank is added to both project and area."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            },
            "area": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            },
        }
        result = apply_ranking_system(note_types, "rank")
        assert "rank" in result["project"]["properties"]["additional_required"]
        assert "rank" in result["area"]["properties"]["additional_required"]

    def test_removes_priority_from_optional_when_rank_selected(self):
        """Test that priority is removed from optional when rank is selected."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": ["priority", "other_prop"],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "priority" not in result["project"]["properties"]["optional"]
        assert "other_prop" in result["project"]["properties"]["optional"]

    def test_preserves_existing_additional_required(self):
        """Test that existing additional_required properties are preserved."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": ["due_date", "status"],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "due_date" in result["project"]["properties"]["additional_required"]
        assert "status" in result["project"]["properties"]["additional_required"]
        assert "rank" in result["project"]["properties"]["additional_required"]


class TestApplyRankingSystemWithPriority:
    """Tests for apply_ranking_system with 'priority' system."""

    def test_adds_priority_to_project(self):
        """Test that priority is added to project additional_required."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "priority")
        assert "priority" in result["project"]["properties"]["additional_required"]

    def test_adds_priority_to_area(self):
        """Test that priority is added to area additional_required."""
        note_types = {
            "area": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "priority")
        assert "priority" in result["area"]["properties"]["additional_required"]

    def test_removes_priority_from_optional_when_moving_to_required(self):
        """Test that priority is removed from optional when added to required."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": ["priority", "tags"],
                }
            }
        }
        result = apply_ranking_system(note_types, "priority")
        assert "priority" in result["project"]["properties"]["additional_required"]
        assert "priority" not in result["project"]["properties"]["optional"]
        assert "tags" in result["project"]["properties"]["optional"]

    def test_preserves_existing_additional_required(self):
        """Test that existing additional_required properties are preserved."""
        note_types = {
            "area": {
                "properties": {
                    "additional_required": ["scope", "owner"],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "priority")
        assert "scope" in result["area"]["properties"]["additional_required"]
        assert "owner" in result["area"]["properties"]["additional_required"]
        assert "priority" in result["area"]["properties"]["additional_required"]


class TestNonRankableTypes:
    """Tests for non-rankable note types."""

    def test_dot_type_not_modified(self):
        """Test that dot type is not modified."""
        note_types = {
            "dot": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "rank" not in result["dot"]["properties"]["additional_required"]
        assert "priority" not in result["dot"]["properties"]["additional_required"]

    def test_daily_type_not_modified(self):
        """Test that daily type is not modified."""
        note_types = {
            "daily": {
                "properties": {
                    "additional_required": ["date"],
                    "optional": ["mood"],
                }
            }
        }
        result = apply_ranking_system(note_types, "priority")
        assert result["daily"]["properties"]["additional_required"] == ["date"]
        assert result["daily"]["properties"]["optional"] == ["mood"]

    def test_mixed_types_only_rankable_modified(self):
        """Test that only rankable types are modified in mixed config."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            },
            "dot": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            },
            "daily": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            },
        }
        result = apply_ranking_system(note_types, "rank")

        # Project should have rank
        assert "rank" in result["project"]["properties"]["additional_required"]

        # Dot and daily should not have rank
        assert "rank" not in result["dot"]["properties"]["additional_required"]
        assert "rank" not in result["daily"]["properties"]["additional_required"]

    @pytest.mark.parametrize(
        "note_type",
        ["dot", "daily", "source", "map", "meeting", "resource"],
    )
    def test_various_non_rankable_types(self, note_type):
        """Test that various non-rankable types are not modified."""
        note_types = {
            note_type: {
                "properties": {
                    "additional_required": ["existing"],
                    "optional": ["other"],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert result[note_type]["properties"]["additional_required"] == ["existing"]
        assert result[note_type]["properties"]["optional"] == ["other"]


class TestDeepCopy:
    """Tests for deep copy behavior."""

    def test_original_not_modified_rank(self):
        """Test that original dict is not modified when applying rank."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        original_required = note_types["project"]["properties"]["additional_required"]

        apply_ranking_system(note_types, "rank")

        # Original should still be empty
        assert original_required == []
        assert note_types["project"]["properties"]["additional_required"] == []

    def test_original_not_modified_priority(self):
        """Test that original dict is not modified when applying priority."""
        note_types = {
            "area": {
                "properties": {
                    "additional_required": ["existing"],
                    "optional": ["priority"],
                }
            }
        }
        original_optional = list(note_types["area"]["properties"]["optional"])

        apply_ranking_system(note_types, "priority")

        # Original should still have priority in optional
        assert "priority" in note_types["area"]["properties"]["optional"]
        assert note_types["area"]["properties"]["optional"] == original_optional

    def test_deep_copy_nested_structures(self):
        """Test that nested structures are deep copied."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": ["a", "b"],
                    "optional": ["c", "d"],
                },
                "other_config": {"nested": ["value"]},
            }
        }

        result = apply_ranking_system(note_types, "rank")

        # Modify result to verify independence
        result["project"]["other_config"]["nested"].append("new")

        # Original should be unchanged
        assert note_types["project"]["other_config"]["nested"] == ["value"]

    def test_returns_new_dict(self):
        """Test that a new dict is returned."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert result is not note_types


class TestEmptyNoteTypes:
    """Tests for empty note_types dict."""

    def test_empty_dict_returns_empty(self):
        """Test that empty dict returns empty dict."""
        result = apply_ranking_system({}, "rank")
        assert result == {}

    def test_empty_dict_returns_new_dict(self):
        """Test that empty dict returns a new empty dict."""
        note_types = {}
        result = apply_ranking_system(note_types, "rank")
        assert result is not note_types
        assert result == {}


class TestMissingPropertiesDict:
    """Tests for missing properties dict in type config."""

    def test_missing_properties_creates_it(self):
        """Test that missing properties dict is created."""
        note_types = {"project": {}}
        result = apply_ranking_system(note_types, "rank")
        assert "properties" in result["project"]
        assert "additional_required" in result["project"]["properties"]
        assert "rank" in result["project"]["properties"]["additional_required"]

    def test_missing_additional_required_creates_it(self):
        """Test that missing additional_required list is created."""
        note_types = {
            "project": {
                "properties": {
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "additional_required" in result["project"]["properties"]
        assert "rank" in result["project"]["properties"]["additional_required"]

    def test_missing_optional_creates_it(self):
        """Test that missing optional list is created."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "optional" in result["project"]["properties"]


class TestIdempotency:
    """Tests for idempotent behavior."""

    def test_rank_already_present_no_duplicate(self):
        """Test that rank is not duplicated if already present."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": ["rank"],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        rank_count = result["project"]["properties"]["additional_required"].count("rank")
        assert rank_count == 1

    def test_priority_already_present_no_duplicate(self):
        """Test that priority is not duplicated if already present."""
        note_types = {
            "area": {
                "properties": {
                    "additional_required": ["priority"],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "priority")
        priority_count = result["area"]["properties"]["additional_required"].count("priority")
        assert priority_count == 1

    def test_applying_twice_same_result(self):
        """Test that applying twice gives same result."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": ["priority"],
                }
            }
        }
        result1 = apply_ranking_system(note_types, "rank")
        result2 = apply_ranking_system(result1, "rank")

        assert (
            result1["project"]["properties"]["additional_required"]
            == result2["project"]["properties"]["additional_required"]
        )
        assert (
            result1["project"]["properties"]["optional"]
            == result2["project"]["properties"]["optional"]
        )


class TestPriorityInOptionalList:
    """Tests for priority removal from optional list."""

    def test_priority_removed_from_optional_when_rank(self):
        """Test priority removed from optional when rank system selected."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": ["priority", "tags", "due_date"],
                }
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert "priority" not in result["project"]["properties"]["optional"]
        assert "tags" in result["project"]["properties"]["optional"]
        assert "due_date" in result["project"]["properties"]["optional"]

    def test_priority_removed_from_optional_when_priority(self):
        """Test priority removed from optional when priority system selected."""
        note_types = {
            "area": {
                "properties": {
                    "additional_required": [],
                    "optional": ["priority", "owner"],
                }
            }
        }
        result = apply_ranking_system(note_types, "priority")
        assert "priority" not in result["area"]["properties"]["optional"]
        assert "priority" in result["area"]["properties"]["additional_required"]
        assert "owner" in result["area"]["properties"]["optional"]

    def test_priority_not_in_optional_no_error(self):
        """Test no error when priority not in optional list."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": ["tags"],
                }
            }
        }
        # Should not raise an error
        result = apply_ranking_system(note_types, "rank")
        assert "tags" in result["project"]["properties"]["optional"]


class TestEdgeCases:
    """Edge case tests for apply_ranking_system."""

    def test_unknown_ranking_system_adds_priority(self):
        """Test that unknown ranking system defaults to priority behavior."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        # Any value other than "rank" uses priority logic
        result = apply_ranking_system(note_types, "unknown")
        assert "priority" in result["project"]["properties"]["additional_required"]
        assert "rank" not in result["project"]["properties"]["additional_required"]

    def test_empty_string_ranking_system(self):
        """Test empty string ranking system uses priority logic."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, "")
        assert "priority" in result["project"]["properties"]["additional_required"]

    def test_case_sensitive_rank(self):
        """Test that ranking system comparison is case sensitive."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        # "Rank" (capitalized) should use priority logic since it's not "rank"
        result = apply_ranking_system(note_types, "Rank")
        assert "priority" in result["project"]["properties"]["additional_required"]
        assert "rank" not in result["project"]["properties"]["additional_required"]

    def test_preserves_additional_config(self):
        """Test that additional configuration in type config is preserved."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                },
                "folder": "Projects",
                "template": "project.md",
                "icon": "folder",
            }
        }
        result = apply_ranking_system(note_types, "rank")
        assert result["project"]["folder"] == "Projects"
        assert result["project"]["template"] == "project.md"
        assert result["project"]["icon"] == "folder"

    def test_type_config_with_none_properties_raises_error(self):
        """Test that None properties value raises AttributeError."""
        note_types = {
            "project": {
                "properties": None,
            }
        }
        # When properties is explicitly set to None (rather than missing),
        # the .get() call on None raises AttributeError
        with pytest.raises(AttributeError):
            apply_ranking_system(note_types, "rank")


class TestIntegration:
    """Integration tests for ranking system."""

    def test_realistic_vault_config(self):
        """Test with a realistic vault configuration."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": ["status", "due_date"],
                    "optional": ["priority", "tags", "assignee"],
                },
                "folder": "Efforts/Projects",
                "template": "templates/project.md",
            },
            "area": {
                "properties": {
                    "additional_required": ["scope"],
                    "optional": ["priority", "owner"],
                },
                "folder": "Efforts/Areas",
            },
            "dot": {
                "properties": {
                    "additional_required": [],
                    "optional": ["tags"],
                },
                "folder": "Atlas/Dots",
            },
            "daily": {
                "properties": {
                    "additional_required": ["date"],
                    "optional": ["mood", "energy"],
                },
                "folder": "Calendar/Daily",
            },
        }

        result = apply_ranking_system(note_types, "rank")

        # Project should have rank added, priority removed from optional
        assert "rank" in result["project"]["properties"]["additional_required"]
        assert "status" in result["project"]["properties"]["additional_required"]
        assert "due_date" in result["project"]["properties"]["additional_required"]
        assert "priority" not in result["project"]["properties"]["optional"]
        assert "tags" in result["project"]["properties"]["optional"]

        # Area should have rank added, priority removed from optional
        assert "rank" in result["area"]["properties"]["additional_required"]
        assert "scope" in result["area"]["properties"]["additional_required"]
        assert "priority" not in result["area"]["properties"]["optional"]

        # Dot should be unchanged
        assert result["dot"]["properties"]["additional_required"] == []
        assert result["dot"]["properties"]["optional"] == ["tags"]

        # Daily should be unchanged
        assert result["daily"]["properties"]["additional_required"] == ["date"]
        assert result["daily"]["properties"]["optional"] == ["mood", "energy"]

        # Original should be unchanged
        assert "priority" in note_types["project"]["properties"]["optional"]
        assert "rank" not in note_types["project"]["properties"]["additional_required"]

    @pytest.mark.parametrize(
        "ranking_system,expected_prop",
        [
            ("rank", "rank"),
            ("priority", "priority"),
        ],
    )
    def test_both_ranking_systems(self, ranking_system, expected_prop):
        """Test both ranking systems add correct property."""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            }
        }
        result = apply_ranking_system(note_types, ranking_system)
        assert expected_prop in result["project"]["properties"]["additional_required"]
