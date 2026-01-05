#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Prompt output functions for vault initialization.

This module provides JSON prompt generation functions for Claude Code's
interactive vault initialization workflow. Each function outputs a structured
JSON prompt that Claude Code parses to show the correct Tab-style selection UI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.methodologies.loader import METHODOLOGIES
from skills.core.utils import apply_ranking_system


def build_next_step_command(
    vault_path: str,
    action: str | None = None,
    methodology: str | None = None,
    note_types: str | None = None,
    core_properties: str | None = None,
    custom_properties: str | None = None,
    per_type_properties: dict[str, str] | None = None,
    ranking_system: str | None = None,
    placeholder: str | None = None,
) -> str:
    """Build the next_step command string for prompts.

    Args:
        vault_path: Path to the vault
        action: Previous action (continue/reset)
        methodology: Selected methodology
        note_types: Note types string
        core_properties: Core properties string
        custom_properties: Custom properties string
        per_type_properties: Dict of type -> properties string
        ranking_system: Ranking system (rank/priority)
        placeholder: Placeholder for the next parameter

    Returns:
        Command string for next_step
    """
    cmd_parts = [f"uv run ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"]

    if action:
        cmd_parts.append(f"--action={action}")
    if methodology:
        cmd_parts.append(f"-m {methodology}")
    if ranking_system:
        cmd_parts.append(f"--ranking-system={ranking_system}")
    if note_types:
        cmd_parts.append(f"--note-types={note_types}")
    if core_properties:
        cmd_parts.append(f"--core-properties={core_properties}")
    if custom_properties:
        cmd_parts.append(f"--custom-properties={custom_properties}")
    if per_type_properties:
        per_type_str = ";".join(f"{k}:{v}" for k, v in per_type_properties.items())
        cmd_parts.append(f"--per-type-props={per_type_str}")
    if placeholder:
        cmd_parts.append(placeholder)

    return " ".join(cmd_parts)


def output_action_prompt(status: dict[str, Any]) -> None:
    """Output prompt for existing vault action selection."""
    folders = status.get("folders", 0)
    files = status.get("files", 0)
    prompt = {
        "prompt_type": "action_required",
        "message": f"Existing vault detected: {folders} folders, {files} files",
        "vault_path": status.get("path", ""),
        "has_obsidian": status.get("has_obsidian", False),
        "has_claude_config": status.get("has_claude_config", False),
        "question": "What would you like to do with the existing vault?",
        "options": [
            {
                "id": "abort",
                "label": "Abort",
                "description": "Cancel initialization (default)",
                "is_default": True,
            },
            {
                "id": "continue",
                "label": "Continue",
                "description": "Add methodology structure to existing content",
                "is_default": False,
            },
            {
                "id": "reset",
                "label": "Reset",
                "description": "Delete all content and start fresh (DESTRUCTIVE)",
                "is_default": False,
            },
            {
                "id": "migrate",
                "label": "Migrate",
                "description": "Migration feature (coming soon)",
                "is_default": False,
            },
        ],
        "next_step": "Call this script again with --action=<chosen_action>",
    }
    print(json.dumps(prompt, indent=2))


def output_methodology_prompt(vault_path: str, action: str | None = None) -> None:
    """Output prompt for methodology selection."""
    next_cmd = build_next_step_command(vault_path, action=action, placeholder="-m <methodology>")

    prompt = {
        "prompt_type": "methodology_required",
        "message": "Choose a PKM methodology for your vault",
        "vault_path": vault_path,
        "previous_action": action,
        "question": "Which methodology would you like to use?",
        "options": [
            {
                "id": "lyt-ace",
                "label": "LYT-ACE",
                "description": "LYT + ACE Framework - interconnected knowledge",
                "is_default": False,
            },
            {
                "id": "para",
                "label": "PARA",
                "description": "Projects, Areas, Resources, Archives - productivity focused",
                "is_default": False,
            },
            {
                "id": "zettelkasten",
                "label": "Zettelkasten",
                "description": "Traditional slip-box system - research and long-term knowledge",
                "is_default": False,
            },
            {
                "id": "minimal",
                "label": "Minimal",
                "description": "Simple starter structure - for beginners",
                "is_default": False,
            },
        ],
        "next_step": next_cmd,
    }
    print(json.dumps(prompt, indent=2))


def output_ranking_system_prompt(
    vault_path: str,
    methodology: str,
    note_types: str,
    action: str | None = None,
) -> None:
    """Output prompt for ranking system selection (Rank vs Priority)."""
    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        note_types=note_types,
        placeholder="--ranking-system=<selected>",
    )

    prompt = {
        "prompt_type": "ranking_system_required",
        "message": "Choose how to rank projects",
        "vault_path": vault_path,
        "methodology": methodology,
        "note_types": note_types,
        "previous_action": action,
        "question": "How would you like to prioritize projects?",
        "options": [
            {
                "id": "rank",
                "label": "Rank (Recommended)",
                "description": "Numeric 1-5 (5=highest priority, 1=lowest)",
                "is_default": True,
            },
            {
                "id": "priority",
                "label": "Priority",
                "description": "Text-based (high, medium, low)",
                "is_default": False,
            },
        ],
        "next_step": next_cmd,
    }
    print(json.dumps(prompt, indent=2))


def output_note_types_prompt(
    vault_path: str,
    methodology: str,
    type_names: list[str],
    action: str | None = None,
) -> None:
    """Output prompt for note type selection (All vs Custom choice)."""
    type_list = ", ".join(type_names) if type_names else "all types"
    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        placeholder="--note-types=<choice>",
    )

    prompt = {
        "prompt_type": "note_types_required",
        "message": f"Note types for {methodology}: {type_list}",
        "vault_path": vault_path,
        "methodology": methodology,
        "previous_action": action,
        "question": "Which note types do you want to include?",
        "multi_select": False,
        "options": [
            {
                "id": "all",
                "label": "All (Recommended)",
                "description": f"Include all note types: {type_list}",
            },
            {
                "id": "custom",
                "label": "Custom",
                "description": "Select individual note types to include",
            },
        ],
        "next_step": next_cmd,
    }
    print(json.dumps(prompt, indent=2))


def output_note_types_select_prompt(
    vault_path: str,
    methodology: str,
    note_types_data: dict[str, Any],
    action: str | None = None,
) -> None:
    """Output prompt for individual note type selection (multi-select)."""
    if "error" in note_types_data:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": f"Could not load note types: {note_types_data['error']}",
                },
                indent=2,
            )
        )
        return

    options = []
    for type_id, type_info in note_types_data.items():
        options.append(
            {
                "id": type_id,
                "label": type_id.capitalize(),
                "description": type_info.get("description", ""),
                "selected": True,
            }
        )

    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        placeholder="--note-types=<selected_types>",
    )

    prompt = {
        "prompt_type": "note_types_select",
        "message": f"Select note types for {methodology}",
        "vault_path": vault_path,
        "methodology": methodology,
        "previous_action": action,
        "question": "Select the note types to include:",
        "multi_select": True,
        "options": options,
        "next_step": next_cmd,
    }
    print(json.dumps(prompt, indent=2))


def output_properties_prompt(
    vault_path: str,
    methodology: str,
    note_types: str,
    action: str | None = None,
) -> None:
    """Output prompt for property selection (All vs Custom choice)."""
    method = METHODOLOGIES.get(methodology)
    core_properties = method.get("core_properties", ["type", "up", "created", "tags"]) if method else []
    props_list = ", ".join(core_properties)

    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        note_types=note_types,
        placeholder="--core-properties=<choice>",
    )

    prompt = {
        "prompt_type": "properties_required",
        "message": f"Core properties: {props_list}",
        "vault_path": vault_path,
        "methodology": methodology,
        "note_types": note_types,
        "previous_action": action,
        "question": "Which properties do you want to use?",
        "multi_select": False,
        "options": [
            {
                "id": "all",
                "label": "All (Recommended)",
                "description": f"Include all properties: {props_list}",
            },
            {
                "id": "custom",
                "label": "Custom",
                "description": "Select individual properties (type and created are mandatory)",
            },
        ],
        "next_step": next_cmd,
    }
    print(json.dumps(prompt, indent=2))


def output_properties_select_prompt(
    vault_path: str,
    methodology: str,
    note_types: str,
    action: str | None = None,
) -> None:
    """Output prompt for individual property selection (multi-select)."""
    method = METHODOLOGIES.get(methodology)
    core_properties = method.get("core_properties", ["type", "up", "created", "tags"]) if method else []

    mandatory = {"type", "created"}
    options = []
    for prop in core_properties:
        is_mandatory = prop in mandatory
        options.append(
            {
                "id": prop,
                "label": prop.capitalize(),
                "description": "Required - always included" if is_mandatory else "Optional",
                "selected": True,
                "disabled": is_mandatory,
            }
        )

    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        note_types=note_types,
        placeholder="--core-properties=<selected_properties>",
    )

    prompt = {
        "prompt_type": "properties_select",
        "message": "Select core properties",
        "vault_path": vault_path,
        "methodology": methodology,
        "note_types": note_types,
        "previous_action": action,
        "question": "Select the properties to include:",
        "multi_select": True,
        "options": options,
        "next_step": next_cmd,
        "hint": "type and created are mandatory and cannot be deselected.",
    }
    print(json.dumps(prompt, indent=2))


def output_custom_properties_prompt(
    vault_path: str,
    methodology: str,
    note_types: str,
    core_properties: str,
    action: str | None = None,
) -> None:
    """Output prompt for custom property input."""
    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        note_types=note_types,
        core_properties=core_properties,
        placeholder="--custom-properties=<custom_props_or_none>",
    )

    prompt = {
        "prompt_type": "custom_properties_input",
        "message": "Add custom global properties",
        "vault_path": vault_path,
        "methodology": methodology,
        "note_types": note_types,
        "core_properties": core_properties,
        "previous_action": action,
        "question": "Do you want to add custom properties that apply to ALL note types?",
        "input_type": "text",
        "placeholder": "priority, rating, source_url",
        "next_step": next_cmd,
        "hint": (
            "Enter property names separated by commas (e.g., priority, rating). "
            "These will be added to all notes. Enter 'none' or leave empty to skip."
        ),
        "format_hint": "Comma-separated property names (e.g., myProp1, myProp2, anotherProp)",
    }
    print(json.dumps(prompt, indent=2))


def output_per_type_properties_prompt(
    vault_path: str,
    methodology: str,
    note_types: str,
    core_properties: str,
    custom_properties: str,
    types_to_configure: list[str],
    type_data: dict[str, Any],
    action: str | None = None,
    ranking_system: str = "rank",
) -> None:
    """Output combined prompt for ALL note type properties at once."""
    # Apply ranking system to type data
    type_data = apply_ranking_system(type_data, ranking_system)

    type_sections = []
    for type_name in types_to_configure:
        type_config = type_data.get(type_name, {})
        props = type_config.get("properties", {})
        additional_required = props.get("additional_required", [])
        optional = props.get("optional", [])

        options = []
        for prop in additional_required:
            options.append(
                {
                    "id": prop,
                    "label": prop.capitalize(),
                    "description": "Required",
                    "selected": True,
                    "disabled": True,
                }
            )
        for prop in optional:
            options.append(
                {
                    "id": prop,
                    "label": prop.capitalize(),
                    "description": "Optional",
                    "selected": False,
                }
            )

        type_sections.append(
            {
                "type_name": type_name,
                "label": type_name.capitalize(),
                "required": additional_required,
                "optional": optional,
                "options": options,
                "default": "none",
            }
        )

    per_type_placeholder = ";".join(f"{t}:<{t}_selected>" for t in types_to_configure)
    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        ranking_system=ranking_system,
        note_types=note_types,
        core_properties=core_properties,
        custom_properties=custom_properties or "none",
        placeholder=f"--per-type-props={per_type_placeholder}",
    )

    prompt = {
        "prompt_type": "per_type_properties_combined",
        "message": f"Configure properties for {len(types_to_configure)} note types",
        "vault_path": vault_path,
        "methodology": methodology,
        "note_types": note_types,
        "core_properties": core_properties,
        "custom_properties": custom_properties,
        "previous_action": action,
        "question": "Configure additional properties for each note type:",
        "type_sections": type_sections,
        "next_step": next_cmd,
        "hint": (
            "For each note type, select optional properties to include. "
            "Required properties are pre-selected and cannot be changed. "
            "Leave optional properties unselected to use only required ones."
        ),
        "format_hint": "Format: type1:prop1,prop2;type2:none (use 'none' for no optional)",
    }
    print(json.dumps(prompt, indent=2))


def output_git_init_prompt(
    vault_path: str,
    methodology: str,
    note_types: str,
    core_properties: str,
    custom_properties: str,
    per_type_properties: dict[str, str],
    action: str | None = None,
    ranking_system: str = "rank",
) -> None:
    """Output prompt for git initialization."""
    git_exists = Path(vault_path).joinpath(".git").exists()

    next_cmd = build_next_step_command(
        vault_path,
        action=action,
        methodology=methodology,
        note_types=note_types,
        ranking_system=ranking_system,
        core_properties=core_properties,
        custom_properties=custom_properties,
        per_type_properties=per_type_properties if per_type_properties else None,
        placeholder="--git=<choice>",
    )

    if git_exists:
        prompt = {
            "prompt_type": "git_existing",
            "message": "Git repository already exists",
            "vault_path": vault_path,
            "methodology": methodology,
            "question": "A git repository already exists. What would you like to do?",
            "options": [
                {
                    "id": "keep",
                    "label": "Keep (Recommended)",
                    "description": "Keep existing .git folder and history",
                    "is_default": True,
                },
                {
                    "id": "yes",
                    "label": "Reset",
                    "description": "Delete .git and create fresh repository",
                    "is_default": False,
                },
            ],
            "next_step": next_cmd,
        }
    else:
        prompt = {
            "prompt_type": "git_init_required",
            "message": "Initialize git repository?",
            "vault_path": vault_path,
            "methodology": methodology,
            "question": "Would you like to initialize a git repository?",
            "options": [
                {
                    "id": "yes",
                    "label": "Yes (Recommended)",
                    "description": "Create .git folder and .gitignore with initial commit",
                    "is_default": True,
                },
                {
                    "id": "no",
                    "label": "No",
                    "description": "Skip git initialization",
                    "is_default": False,
                },
            ],
            "next_step": next_cmd,
        }
    print(json.dumps(prompt, indent=2))


def output_abort() -> None:
    """Output abort confirmation."""
    result = {
        "status": "aborted",
        "message": "Vault initialization cancelled by user.",
    }
    print(json.dumps(result, indent=2))


def output_migrate_hint() -> None:
    """Output migration feature hint."""
    result = {
        "status": "migration_not_available",
        "message": "Migration feature is planned for a future release.",
        "suggestion": "Use 'Continue' to add structure without modifying files.",
    }
    print(json.dumps(result, indent=2))
