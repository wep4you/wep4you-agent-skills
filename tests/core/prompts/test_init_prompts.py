"""
Tests for skills.core.prompts.init_prompts module.

Tests JSON prompt generation functions for vault initialization workflow.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from skills.core.prompts.init_prompts import (
    build_next_step_command,
    output_abort,
    output_action_prompt,
    output_custom_properties_prompt,
    output_git_init_prompt,
    output_methodology_prompt,
    output_migrate_hint,
    output_note_types_prompt,
    output_note_types_select_prompt,
    output_per_type_properties_prompt,
    output_properties_prompt,
    output_properties_select_prompt,
    output_ranking_system_prompt,
)


class TestBuildNextStepCommand:
    """Tests for build_next_step_command function."""

    def test_basic_command_with_vault_path(self):
        """Test building command with only vault path."""
        result = build_next_step_command("/path/to/vault")
        assert result == "uv run ${CLAUDE_PLUGIN_ROOT}/commands/init.py /path/to/vault"

    def test_command_with_action(self):
        """Test building command with action parameter."""
        result = build_next_step_command("/vault", action="continue")
        assert "--action=continue" in result

    def test_command_with_methodology(self):
        """Test building command with methodology parameter."""
        result = build_next_step_command("/vault", methodology="lyt-ace")
        assert "-m lyt-ace" in result

    def test_command_with_ranking_system(self):
        """Test building command with ranking system parameter."""
        result = build_next_step_command("/vault", ranking_system="rank")
        assert "--ranking-system=rank" in result

    def test_command_with_note_types(self):
        """Test building command with note types parameter."""
        result = build_next_step_command("/vault", note_types="map,dot,source")
        assert "--note-types=map,dot,source" in result

    def test_command_with_core_properties(self):
        """Test building command with core properties parameter."""
        result = build_next_step_command("/vault", core_properties="type,up,created")
        assert "--core-properties=type,up,created" in result

    def test_command_with_custom_properties(self):
        """Test building command with custom properties parameter."""
        result = build_next_step_command("/vault", custom_properties="priority,rating")
        assert "--custom-properties=priority,rating" in result

    def test_command_with_per_type_properties(self):
        """Test building command with per-type properties parameter."""
        result = build_next_step_command(
            "/vault", per_type_properties={"map": "summary", "project": "status,deadline"}
        )
        assert "--per-type-props=" in result
        assert "map:summary" in result
        assert "project:status,deadline" in result

    def test_command_with_placeholder(self):
        """Test building command with placeholder parameter."""
        result = build_next_step_command("/vault", placeholder="-m <methodology>")
        assert result.endswith("-m <methodology>")

    def test_command_with_all_parameters(self):
        """Test building command with all parameters."""
        result = build_next_step_command(
            "/vault",
            action="continue",
            methodology="lyt-ace",
            note_types="map,dot",
            core_properties="type,up",
            custom_properties="priority",
            per_type_properties={"map": "summary"},
            ranking_system="rank",
            placeholder="--git=<choice>",
        )
        assert "/vault" in result
        assert "--action=continue" in result
        assert "-m lyt-ace" in result
        assert "--note-types=map,dot" in result
        assert "--core-properties=type,up" in result
        assert "--custom-properties=priority" in result
        assert "--per-type-props=map:summary" in result
        assert "--ranking-system=rank" in result
        assert result.endswith("--git=<choice>")


class TestOutputActionPrompt:
    """Tests for output_action_prompt function."""

    def test_basic_action_prompt(self, capsys):
        """Test basic action prompt output."""
        status = {
            "folders": 5,
            "files": 10,
            "path": "/vault",
            "has_obsidian": True,
            "has_claude_config": False,
        }
        output_action_prompt(status)
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "action_required"
        assert "5 folders, 10 files" in result["message"]
        assert result["vault_path"] == "/vault"
        assert result["has_obsidian"] is True
        assert result["has_claude_config"] is False
        assert len(result["options"]) == 4

    def test_action_prompt_options(self, capsys):
        """Test action prompt contains all expected options."""
        status = {"folders": 0, "files": 0, "path": "/vault"}
        output_action_prompt(status)
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        option_ids = [opt["id"] for opt in result["options"]]
        assert "abort" in option_ids
        assert "continue" in option_ids
        assert "reset" in option_ids
        assert "migrate" in option_ids

    def test_action_prompt_default_option(self, capsys):
        """Test abort is the default option."""
        status = {"folders": 0, "files": 0}
        output_action_prompt(status)
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        abort_option = next(opt for opt in result["options"] if opt["id"] == "abort")
        assert abort_option["is_default"] is True

    def test_action_prompt_missing_keys(self, capsys):
        """Test action prompt with missing status keys."""
        status = {}
        output_action_prompt(status)
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["vault_path"] == ""
        assert result["has_obsidian"] is False
        assert result["has_claude_config"] is False


class TestOutputMethodologyPrompt:
    """Tests for output_methodology_prompt function."""

    def test_basic_methodology_prompt(self, capsys):
        """Test basic methodology prompt output."""
        output_methodology_prompt("/vault")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "methodology_required"
        assert result["vault_path"] == "/vault"
        assert result["previous_action"] is None
        assert len(result["options"]) == 4

    def test_methodology_prompt_with_action(self, capsys):
        """Test methodology prompt with previous action."""
        output_methodology_prompt("/vault", action="continue")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["previous_action"] == "continue"
        assert "--action=continue" in result["next_step"]

    def test_methodology_options(self, capsys):
        """Test methodology prompt contains expected methodologies."""
        output_methodology_prompt("/vault")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        option_ids = [opt["id"] for opt in result["options"]]
        assert "lyt-ace" in option_ids
        assert "para" in option_ids
        assert "zettelkasten" in option_ids
        assert "minimal" in option_ids

    def test_methodology_prompt_next_step(self, capsys):
        """Test methodology prompt next_step contains placeholder."""
        output_methodology_prompt("/vault")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "-m <methodology>" in result["next_step"]


class TestOutputRankingSystemPrompt:
    """Tests for output_ranking_system_prompt function."""

    def test_basic_ranking_system_prompt(self, capsys):
        """Test basic ranking system prompt output."""
        output_ranking_system_prompt("/vault", "lyt-ace", "map,dot")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "ranking_system_required"
        assert result["vault_path"] == "/vault"
        assert result["methodology"] == "lyt-ace"
        assert result["note_types"] == "map,dot"
        assert len(result["options"]) == 2

    def test_ranking_system_options(self, capsys):
        """Test ranking system prompt options."""
        output_ranking_system_prompt("/vault", "lyt-ace", "map")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        option_ids = [opt["id"] for opt in result["options"]]
        assert "rank" in option_ids
        assert "priority" in option_ids

    def test_ranking_system_default(self, capsys):
        """Test rank is the default option."""
        output_ranking_system_prompt("/vault", "lyt-ace", "map")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        rank_option = next(opt for opt in result["options"] if opt["id"] == "rank")
        assert rank_option["is_default"] is True

    def test_ranking_system_with_action(self, capsys):
        """Test ranking system prompt with previous action."""
        output_ranking_system_prompt("/vault", "lyt-ace", "map", action="continue")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["previous_action"] == "continue"


class TestOutputNoteTypesPrompt:
    """Tests for output_note_types_prompt function."""

    def test_basic_note_types_prompt(self, capsys):
        """Test basic note types prompt output."""
        output_note_types_prompt("/vault", "lyt-ace", ["map", "dot", "source"])
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "note_types_required"
        assert result["vault_path"] == "/vault"
        assert result["methodology"] == "lyt-ace"
        assert "map, dot, source" in result["message"]
        assert result["multi_select"] is False

    def test_note_types_prompt_options(self, capsys):
        """Test note types prompt has all and custom options."""
        output_note_types_prompt("/vault", "lyt-ace", ["map"])
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        option_ids = [opt["id"] for opt in result["options"]]
        assert "all" in option_ids
        assert "custom" in option_ids

    def test_note_types_prompt_empty_types(self, capsys):
        """Test note types prompt with empty type list."""
        output_note_types_prompt("/vault", "lyt-ace", [])
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "all types" in result["message"]

    def test_note_types_prompt_with_action(self, capsys):
        """Test note types prompt with previous action."""
        output_note_types_prompt("/vault", "lyt-ace", ["map"], action="reset")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["previous_action"] == "reset"


class TestOutputNoteTypesSelectPrompt:
    """Tests for output_note_types_select_prompt function."""

    def test_basic_note_types_select_prompt(self, capsys):
        """Test basic note types select prompt output."""
        note_types_data = {
            "map": {"description": "Map of content"},
            "dot": {"description": "Atomic note"},
        }
        output_note_types_select_prompt("/vault", "lyt-ace", note_types_data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "note_types_select"
        assert result["multi_select"] is True
        assert len(result["options"]) == 2

    def test_note_types_select_options_structure(self, capsys):
        """Test note types select options have correct structure."""
        note_types_data = {"map": {"description": "Map of content"}}
        output_note_types_select_prompt("/vault", "lyt-ace", note_types_data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        opt = result["options"][0]
        assert opt["id"] == "map"
        assert opt["label"] == "Map"
        assert opt["description"] == "Map of content"
        assert opt["selected"] is True

    def test_note_types_select_error_handling(self, capsys):
        """Test note types select handles error in data."""
        note_types_data = {"error": "Could not load note types"}
        output_note_types_select_prompt("/vault", "lyt-ace", note_types_data)
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["status"] == "error"
        assert "Could not load note types" in result["message"]

    def test_note_types_select_with_action(self, capsys):
        """Test note types select with previous action."""
        note_types_data = {"map": {"description": "Map"}}
        output_note_types_select_prompt("/vault", "lyt-ace", note_types_data, action="continue")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["previous_action"] == "continue"


class TestOutputPropertiesPrompt:
    """Tests for output_properties_prompt function."""

    @patch("skills.core.prompts.init_prompts.METHODOLOGIES")
    def test_basic_properties_prompt(self, mock_methodologies, capsys):
        """Test basic properties prompt output."""
        mock_methodologies.get.return_value = {
            "core_properties": ["type", "up", "created", "tags"]
        }
        output_properties_prompt("/vault", "lyt-ace", "map,dot")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "properties_required"
        assert result["vault_path"] == "/vault"
        assert result["methodology"] == "lyt-ace"
        assert result["note_types"] == "map,dot"
        assert result["multi_select"] is False

    @patch("skills.core.prompts.init_prompts.METHODOLOGIES")
    def test_properties_prompt_options(self, mock_methodologies, capsys):
        """Test properties prompt has all and custom options."""
        mock_methodologies.get.return_value = {"core_properties": ["type", "up"]}
        output_properties_prompt("/vault", "lyt-ace", "map")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        option_ids = [opt["id"] for opt in result["options"]]
        assert "all" in option_ids
        assert "custom" in option_ids

    @patch("skills.core.prompts.init_prompts.METHODOLOGIES")
    def test_properties_prompt_missing_methodology(self, mock_methodologies, capsys):
        """Test properties prompt with missing methodology."""
        mock_methodologies.get.return_value = None
        output_properties_prompt("/vault", "unknown", "map")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Should still work with empty properties
        assert result["prompt_type"] == "properties_required"


class TestOutputPropertiesSelectPrompt:
    """Tests for output_properties_select_prompt function."""

    @patch("skills.core.prompts.init_prompts.METHODOLOGIES")
    def test_basic_properties_select_prompt(self, mock_methodologies, capsys):
        """Test basic properties select prompt output."""
        mock_methodologies.get.return_value = {
            "core_properties": ["type", "up", "created", "tags"]
        }
        output_properties_select_prompt("/vault", "lyt-ace", "map,dot")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "properties_select"
        assert result["multi_select"] is True
        assert len(result["options"]) == 4

    @patch("skills.core.prompts.init_prompts.METHODOLOGIES")
    def test_properties_select_mandatory_disabled(self, mock_methodologies, capsys):
        """Test mandatory properties are disabled."""
        mock_methodologies.get.return_value = {
            "core_properties": ["type", "created", "up"]
        }
        output_properties_select_prompt("/vault", "lyt-ace", "map")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        type_opt = next(opt for opt in result["options"] if opt["id"] == "type")
        created_opt = next(opt for opt in result["options"] if opt["id"] == "created")
        up_opt = next(opt for opt in result["options"] if opt["id"] == "up")

        assert type_opt["disabled"] is True
        assert created_opt["disabled"] is True
        assert up_opt["disabled"] is False

    @patch("skills.core.prompts.init_prompts.METHODOLOGIES")
    def test_properties_select_hint(self, mock_methodologies, capsys):
        """Test properties select has hint about mandatory."""
        mock_methodologies.get.return_value = {"core_properties": ["type", "created"]}
        output_properties_select_prompt("/vault", "lyt-ace", "map")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "type and created are mandatory" in result["hint"]


class TestOutputCustomPropertiesPrompt:
    """Tests for output_custom_properties_prompt function."""

    def test_basic_custom_properties_prompt(self, capsys):
        """Test basic custom properties prompt output."""
        output_custom_properties_prompt("/vault", "lyt-ace", "map,dot", "type,up,created")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "custom_properties_input"
        assert result["vault_path"] == "/vault"
        assert result["methodology"] == "lyt-ace"
        assert result["note_types"] == "map,dot"
        assert result["core_properties"] == "type,up,created"
        assert result["input_type"] == "text"

    def test_custom_properties_prompt_placeholder(self, capsys):
        """Test custom properties prompt has placeholder."""
        output_custom_properties_prompt("/vault", "lyt-ace", "map", "type,up")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["placeholder"] == "priority, rating, source_url"

    def test_custom_properties_prompt_hint(self, capsys):
        """Test custom properties prompt has hint."""
        output_custom_properties_prompt("/vault", "lyt-ace", "map", "type")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "Enter property names separated by commas" in result["hint"]
        assert "none" in result["hint"]

    def test_custom_properties_prompt_with_action(self, capsys):
        """Test custom properties prompt with previous action."""
        output_custom_properties_prompt("/vault", "lyt-ace", "map", "type", action="continue")
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["previous_action"] == "continue"


class TestOutputPerTypePropertiesPrompt:
    """Tests for output_per_type_properties_prompt function."""

    @patch("skills.core.prompts.init_prompts.apply_ranking_system")
    def test_basic_per_type_properties_prompt(self, mock_apply_ranking, capsys):
        """Test basic per-type properties prompt output."""
        type_data = {
            "map": {
                "properties": {
                    "additional_required": ["summary"],
                    "optional": ["icon"],
                }
            }
        }
        mock_apply_ranking.return_value = type_data

        output_per_type_properties_prompt(
            "/vault", "lyt-ace", "map", "type,up", "priority", ["map"], type_data
        )
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "per_type_properties_combined"
        assert len(result["type_sections"]) == 1

    @patch("skills.core.prompts.init_prompts.apply_ranking_system")
    def test_per_type_properties_section_structure(self, mock_apply_ranking, capsys):
        """Test per-type properties section structure."""
        type_data = {
            "project": {
                "properties": {
                    "additional_required": ["status"],
                    "optional": ["deadline", "priority"],
                }
            }
        }
        mock_apply_ranking.return_value = type_data

        output_per_type_properties_prompt(
            "/vault", "lyt-ace", "project", "type", "none", ["project"], type_data
        )
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        section = result["type_sections"][0]
        assert section["type_name"] == "project"
        assert section["required"] == ["status"]
        assert section["optional"] == ["deadline", "priority"]

    @patch("skills.core.prompts.init_prompts.apply_ranking_system")
    def test_per_type_properties_required_disabled(self, mock_apply_ranking, capsys):
        """Test required properties are disabled in options."""
        type_data = {
            "project": {
                "properties": {
                    "additional_required": ["status"],
                    "optional": ["deadline"],
                }
            }
        }
        mock_apply_ranking.return_value = type_data

        output_per_type_properties_prompt(
            "/vault", "lyt-ace", "project", "type", "none", ["project"], type_data
        )
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        section = result["type_sections"][0]
        status_opt = next(opt for opt in section["options"] if opt["id"] == "status")
        deadline_opt = next(opt for opt in section["options"] if opt["id"] == "deadline")

        assert status_opt["disabled"] is True
        assert status_opt["selected"] is True
        # Optional properties don't have disabled key (defaults to not disabled)
        assert deadline_opt.get("disabled", False) is False
        assert deadline_opt["selected"] is False

    @patch("skills.core.prompts.init_prompts.apply_ranking_system")
    def test_per_type_properties_multiple_types(self, mock_apply_ranking, capsys):
        """Test per-type properties with multiple types."""
        type_data = {
            "map": {"properties": {"additional_required": [], "optional": ["summary"]}},
            "dot": {"properties": {"additional_required": [], "optional": ["tags"]}},
        }
        mock_apply_ranking.return_value = type_data

        output_per_type_properties_prompt(
            "/vault", "lyt-ace", "map,dot", "type", "none", ["map", "dot"], type_data
        )
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert len(result["type_sections"]) == 2
        type_names = [s["type_name"] for s in result["type_sections"]]
        assert "map" in type_names
        assert "dot" in type_names


class TestOutputGitInitPrompt:
    """Tests for output_git_init_prompt function."""

    def test_git_init_prompt_no_existing_git(self, capsys, tmp_path):
        """Test git init prompt when no .git exists."""
        vault_path = str(tmp_path)
        output_git_init_prompt(vault_path, "lyt-ace", "map", "type,up", "none", {})
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "git_init_required"
        assert len(result["options"]) == 2

        option_ids = [opt["id"] for opt in result["options"]]
        assert "yes" in option_ids
        assert "no" in option_ids

    def test_git_init_prompt_existing_git(self, capsys, tmp_path):
        """Test git init prompt when .git already exists."""
        (tmp_path / ".git").mkdir()
        vault_path = str(tmp_path)
        output_git_init_prompt(vault_path, "lyt-ace", "map", "type,up", "none", {})
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["prompt_type"] == "git_existing"

        option_ids = [opt["id"] for opt in result["options"]]
        assert "keep" in option_ids
        assert "yes" in option_ids

    def test_git_init_default_option_no_git(self, capsys, tmp_path):
        """Test yes is default when no .git exists."""
        vault_path = str(tmp_path)
        output_git_init_prompt(vault_path, "lyt-ace", "map", "type", "none", {})
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        yes_opt = next(opt for opt in result["options"] if opt["id"] == "yes")
        assert yes_opt["is_default"] is True

    def test_git_init_default_option_existing_git(self, capsys, tmp_path):
        """Test keep is default when .git exists."""
        (tmp_path / ".git").mkdir()
        vault_path = str(tmp_path)
        output_git_init_prompt(vault_path, "lyt-ace", "map", "type", "none", {})
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        keep_opt = next(opt for opt in result["options"] if opt["id"] == "keep")
        assert keep_opt["is_default"] is True

    def test_git_init_prompt_with_per_type_props(self, capsys, tmp_path):
        """Test git init prompt with per-type properties."""
        vault_path = str(tmp_path)
        per_type_props = {"map": "summary", "project": "status"}
        output_git_init_prompt(
            vault_path, "lyt-ace", "map,project", "type,up", "priority", per_type_props
        )
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "--per-type-props=" in result["next_step"]
        assert "map:summary" in result["next_step"]

    def test_git_init_prompt_with_ranking_system(self, capsys, tmp_path):
        """Test git init prompt with ranking system."""
        vault_path = str(tmp_path)
        output_git_init_prompt(
            vault_path, "lyt-ace", "map", "type", "none", {}, ranking_system="priority"
        )
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "--ranking-system=priority" in result["next_step"]


class TestOutputAbort:
    """Tests for output_abort function."""

    def test_output_abort(self, capsys):
        """Test abort output."""
        output_abort()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["status"] == "aborted"
        assert "cancelled" in result["message"].lower()


class TestOutputMigrateHint:
    """Tests for output_migrate_hint function."""

    def test_output_migrate_hint(self, capsys):
        """Test migrate hint output."""
        output_migrate_hint()
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result["status"] == "migration_not_available"
        assert "future release" in result["message"]
        assert "Continue" in result["suggestion"]


class TestPromptIntegration:
    """Integration tests for prompt workflow."""

    @patch("skills.core.prompts.init_prompts.METHODOLOGIES")
    @patch("skills.core.prompts.init_prompts.apply_ranking_system")
    def test_full_workflow_prompts(self, mock_apply_ranking, mock_methodologies, capsys, tmp_path):
        """Test prompts can be generated in sequence without errors."""
        mock_methodologies.get.return_value = {
            "core_properties": ["type", "up", "created", "tags"]
        }
        mock_apply_ranking.return_value = {
            "map": {"properties": {"additional_required": [], "optional": ["summary"]}}
        }

        vault_path = str(tmp_path)

        # Simulate workflow
        status = {"folders": 0, "files": 0, "path": vault_path}
        output_action_prompt(status)

        output_methodology_prompt(vault_path, action="continue")

        output_note_types_prompt(vault_path, "lyt-ace", ["map", "dot"])

        output_ranking_system_prompt(vault_path, "lyt-ace", "map,dot")

        output_properties_prompt(vault_path, "lyt-ace", "map,dot")

        output_custom_properties_prompt(vault_path, "lyt-ace", "map,dot", "type,up,created")

        output_per_type_properties_prompt(
            vault_path,
            "lyt-ace",
            "map",
            "type,up",
            "none",
            ["map"],
            {"map": {"properties": {"additional_required": [], "optional": ["summary"]}}},
        )

        output_git_init_prompt(vault_path, "lyt-ace", "map", "type,up", "none", {})

        # All prompts should have been generated
        captured = capsys.readouterr()
        outputs = captured.out.strip().split("\n}")

        # Should have 8 separate JSON outputs (minus last empty split)
        assert len(outputs) >= 8

    def test_prompt_json_validity(self, capsys, tmp_path):
        """Test all prompts produce valid JSON."""
        vault_path = str(tmp_path)
        status = {"folders": 1, "files": 5}

        # Generate various prompts
        output_action_prompt(status)
        output_methodology_prompt(vault_path)
        output_abort()
        output_migrate_hint()

        captured = capsys.readouterr()

        # Split by closing brace and newline to separate JSON objects
        json_strings = captured.out.strip().replace("}\n{", "}|||{").split("|||")

        for json_str in json_strings:
            # Each should be valid JSON
            result = json.loads(json_str)
            assert isinstance(result, dict)
