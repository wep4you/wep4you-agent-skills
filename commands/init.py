#!/usr/bin/env python3
"""
Vault Initialization Wrapper for Claude Code.

This wrapper enforces the correct workflow order:
1. Check vault status FIRST
2. If existing vault: Ask user what to do (Abort/Continue/Reset/Migrate)
3. Then ask for methodology
4. Execute init_vault.py with chosen options

The wrapper outputs structured JSON that Claude Code parses to show
the correct Tab-style selection UI.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_script_path() -> Path:
    """Get path to init_vault.py script."""
    commands_dir = Path(__file__).parent
    plugin_root = commands_dir.parent
    return plugin_root / "skills" / "init" / "scripts" / "init_vault.py"


def get_note_types_for_methodology(methodology: str) -> dict:
    """Get note types for a methodology by calling init_vault.py."""
    script = get_script_path()

    try:
        cmd = ["uv", "run", str(script), "--list-note-types", methodology]
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr or "Failed to get note types"}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {"error": str(e)}


def check_vault_status(vault_path: Path) -> dict:
    """Check vault status using init_vault.py --check."""
    script = get_script_path()

    try:
        cmd = ["uv", "run", str(script), str(vault_path), "--check"]
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {
                "status": "error",
                "message": result.stderr or "Failed to check vault status",
            }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Timeout checking vault status"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON from vault check"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def output_action_prompt(status: dict) -> None:
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
    """Output prompt for methodology selection.

    Args:
        vault_path: Path to the vault
        action: Previous action (continue/reset) to preserve in next command
    """
    # Build the next_step command - use wrapper to preserve action
    base_cmd = f"python3 ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"
    if action:
        next_cmd = f"{base_cmd} --action={action} -m <methodology>"
    else:
        next_cmd = f"{base_cmd} -m <methodology>"

    prompt = {
        "prompt_type": "methodology_required",
        "message": "Choose a PKM methodology for your vault",
        "vault_path": vault_path,
        "previous_action": action,  # Include for Claude Code to track
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


def output_note_types_prompt(
    vault_path: str,
    methodology: str,
    action: str | None = None,
) -> None:
    """Output prompt for note type selection (All vs Custom choice).

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        action: Previous action (continue/reset) to preserve in next command
    """
    note_types_data = get_note_types_for_methodology(methodology)
    type_names = list(note_types_data.keys()) if "error" not in note_types_data else []
    type_list = ", ".join(type_names) if type_names else "all types"

    # Build the next_step command
    cmd_parts = [f"python3 ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"]
    if action:
        cmd_parts.append(f"--action={action}")
    cmd_parts.append(f"-m {methodology}")
    cmd_parts.append("--note-types=<choice>")
    next_cmd = " ".join(cmd_parts)

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
    action: str | None = None,
) -> None:
    """Output prompt for individual note type selection (multi-select).

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        action: Previous action (continue/reset) to preserve in next command
    """
    note_types_data = get_note_types_for_methodology(methodology)

    if "error" in note_types_data:
        print(json.dumps({
            "status": "error",
            "message": f"Could not load note types: {note_types_data['error']}",
        }, indent=2))
        return

    # Build options from note types
    options = []
    for type_id, type_info in note_types_data.items():
        options.append({
            "id": type_id,
            "label": type_id.capitalize(),
            "description": type_info.get("description", ""),
            "selected": True,  # All selected by default
        })

    # Build the next_step command
    cmd_parts = [f"python3 ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"]
    if action:
        cmd_parts.append(f"--action={action}")
    cmd_parts.append(f"-m {methodology}")
    cmd_parts.append("--note-types=<selected_types>")
    next_cmd = " ".join(cmd_parts)

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


def get_core_properties_for_methodology(methodology: str) -> list[str]:
    """Get core properties for a methodology by calling init_vault.py."""
    script = get_script_path()

    try:
        cmd = ["uv", "run", str(script), "--list-note-types", methodology]
        result = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # The note types JSON doesn't include core_properties directly
            # We need to get them from methodology config
            # For now, call --list and parse or hardcode common ones
            pass
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Fallback: common core properties (will be replaced with actual call)
    # These are defined in METHODOLOGIES in init_vault.py
    core_props_by_methodology = {
        "lyt-ace": ["type", "up", "created", "daily", "tags", "collection", "related"],
        "para": ["type", "up", "created", "tags"],
        "zettelkasten": ["type", "up", "created", "tags", "source", "related"],
        "minimal": ["type", "created", "tags"],
    }
    return core_props_by_methodology.get(methodology, ["type", "up", "created", "tags"])


def output_properties_prompt(
    vault_path: str,
    methodology: str,
    note_types: str,
    action: str | None = None,
) -> None:
    """Output prompt for property selection (All vs Custom choice).

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        note_types: Comma-separated list of selected note types
        action: Previous action (continue/reset) to preserve in next command
    """
    core_properties = get_core_properties_for_methodology(methodology)
    props_list = ", ".join(core_properties)

    # Build the next_step command
    cmd_parts = [f"python3 ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"]
    if action:
        cmd_parts.append(f"--action={action}")
    cmd_parts.append(f"-m {methodology}")
    cmd_parts.append(f"--note-types={note_types}")
    cmd_parts.append("--core-properties=<choice>")
    next_cmd = " ".join(cmd_parts)

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
    """Output prompt for individual property selection (multi-select).

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        note_types: Comma-separated list of selected note types
        action: Previous action (continue/reset) to preserve in next command
    """
    core_properties = get_core_properties_for_methodology(methodology)

    # Build options from core properties
    # type and created are mandatory, others are optional
    mandatory = {"type", "created"}
    options = []
    for prop in core_properties:
        is_mandatory = prop in mandatory
        options.append({
            "id": prop,
            "label": prop.capitalize(),
            "description": f"{'Required - always included' if is_mandatory else 'Optional'}",
            "selected": True,  # All selected by default
            "disabled": is_mandatory,  # Can't deselect mandatory
        })

    # Build the next_step command
    cmd_parts = [f"python3 ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"]
    if action:
        cmd_parts.append(f"--action={action}")
    cmd_parts.append(f"-m {methodology}")
    cmd_parts.append(f"--note-types={note_types}")
    cmd_parts.append("--core-properties=<selected_properties>")
    next_cmd = " ".join(cmd_parts)

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
    """Output prompt for custom property input.

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        note_types: Comma-separated list of selected note types
        core_properties: Comma-separated list of selected core properties
        action: Previous action (continue/reset)
    """
    # Build the next_step command
    cmd_parts = [f"python3 ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"]
    if action:
        cmd_parts.append(f"--action={action}")
    cmd_parts.append(f"-m {methodology}")
    cmd_parts.append(f"--note-types={note_types}")
    cmd_parts.append(f"--core-properties={core_properties}")
    cmd_parts.append("--custom-properties=<custom_props_or_none>")
    next_cmd = " ".join(cmd_parts)

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
    current_type: str,
    remaining_types: list[str],
    action: str | None = None,
    per_type_properties: dict[str, str] | None = None,
) -> None:
    """Output prompt for per-note-type additional properties.

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        note_types: Comma-separated list of selected note types
        core_properties: Comma-separated list of core properties
        custom_properties: Comma-separated list of custom properties
        current_type: The note type to configure
        remaining_types: List of remaining types to configure
        action: Previous action
        per_type_properties: Already configured per-type properties
    """
    # Get the type's predefined additional_required properties
    type_data = get_note_types_for_methodology(methodology)
    type_config = type_data.get(current_type, {})
    props = type_config.get("properties", {})
    additional_required = props.get("additional_required", [])
    optional = props.get("optional", [])

    # Build options
    options = []
    for prop in additional_required:
        options.append({
            "id": prop,
            "label": prop.capitalize(),
            "description": "Required for this type",
            "selected": True,
            "disabled": True,  # Required can't be deselected
        })
    for prop in optional:
        options.append({
            "id": prop,
            "label": prop.capitalize(),
            "description": "Optional",
            "selected": False,
        })

    # Build per_type_props string for next command
    per_type_str = ""
    if per_type_properties:
        per_type_str = ";".join(f"{k}:{v}" for k, v in per_type_properties.items())

    # Build the next_step command
    cmd_parts = [f"python3 ${{CLAUDE_PLUGIN_ROOT}}/commands/init.py {vault_path}"]
    if action:
        cmd_parts.append(f"--action={action}")
    cmd_parts.append(f"-m {methodology}")
    cmd_parts.append(f"--note-types={note_types}")
    cmd_parts.append(f"--core-properties={core_properties}")
    if custom_properties and custom_properties.lower() != "none":
        cmd_parts.append(f"--custom-properties={custom_properties}")
    cmd_parts.append(f"--per-type-props={current_type}:<selected>")
    if per_type_str:
        cmd_parts[-1] = f"--per-type-props={per_type_str};{current_type}:<selected>"
    next_cmd = " ".join(cmd_parts)

    # Count remaining types
    types_remaining = len(remaining_types)
    progress_msg = (
        f"Type {len(note_types.split(',')) - types_remaining} of {len(note_types.split(','))}"
        if note_types != "all" else ""
    )

    prompt = {
        "prompt_type": "per_type_properties",
        "message": f"Configure properties for '{current_type}' notes",
        "vault_path": vault_path,
        "methodology": methodology,
        "note_types": note_types,
        "core_properties": core_properties,
        "custom_properties": custom_properties,
        "current_type": current_type,
        "remaining_types": remaining_types,
        "types_remaining_count": types_remaining,
        "progress": progress_msg,
        "previous_action": action,
        "question": f"Configure additional properties for '{current_type}' notes:",
        "multi_select": True,
        "options": options,
        "allow_custom_input": True,
        "custom_input_hint": "Add custom properties (comma-separated, e.g., deadline, priority):",
        "next_step": next_cmd,
        "hint": (
            f"Select predefined properties or add custom ones for '{current_type}' notes. "
            "Enter 'none' to skip. "
            f"({types_remaining} more note type(s) to configure after this.)"
            if types_remaining > 0
            else f"Select predefined properties or add custom ones for '{current_type}' notes. "
            "Enter 'none' to skip. This is the last note type to configure."
        ),
        "format_hint": "Comma-separated property names (e.g., deadline, budget, priority)",
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


def execute_init(
    vault_path: Path,
    methodology: str,
    reset: bool = False,
    note_types: list[str] | None = None,
    core_properties: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> int:
    """Execute the actual vault initialization.

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        reset: Whether to reset the vault
        note_types: List of note types to include (None = all)
        core_properties: List of core properties to include (None = all)
        custom_properties: List of custom properties to add globally
        per_type_properties: Dict of type -> list of additional properties
    """
    script = get_script_path()

    cmd = ["uv", "run", str(script), str(vault_path), "-m", methodology, "--defaults"]
    if reset:
        cmd.append("--reset")
    if note_types:
        cmd.extend(["--note-types", ",".join(note_types)])
    if core_properties:
        cmd.extend(["--core-properties", ",".join(core_properties)])
    if custom_properties:
        cmd.extend(["--custom-properties", ",".join(custom_properties)])
    if per_type_properties:
        # Format: type1:prop1,prop2;type2:prop3,prop4
        per_type_str = ";".join(
            f"{k}:{','.join(v)}" for k, v in per_type_properties.items()
        )
        cmd.extend(["--per-type-props", per_type_str])

    # Set environment variable to indicate we're calling from wrapper
    import os

    env = os.environ.copy()
    env["INIT_FROM_WRAPPER"] = "1"

    # Run and stream output
    result = subprocess.run(cmd, env=env)  # noqa: S603
    return result.returncode


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Vault initialization wrapper for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "vault_path",
        nargs="?",
        default=".",
        help="Path to vault (default: current directory)",
    )

    parser.add_argument(
        "--action",
        choices=["abort", "continue", "reset", "migrate"],
        help="Action for existing vault (from previous prompt)",
    )

    parser.add_argument(
        "-m",
        "--methodology",
        choices=["lyt-ace", "para", "zettelkasten", "minimal"],
        help="PKM methodology to use",
    )

    parser.add_argument(
        "--note-types",
        help="Comma-separated list of note types to include",
    )

    parser.add_argument(
        "--core-properties",
        help="Comma-separated list of core properties to include",
    )

    parser.add_argument(
        "--custom-properties",
        help="Comma-separated list of custom properties to add (global)",
    )

    parser.add_argument(
        "--per-type-props",
        help="Per-type properties in format: type1:prop1,prop2;type2:prop3,prop4",
    )

    parser.add_argument(
        "--defaults",
        action="store_true",
        help="Use all defaults (skip note type and property selection)",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Just check vault status (pass-through to init_vault.py)",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List methodologies (pass-through to init_vault.py)",
    )

    args = parser.parse_args()
    vault_path = Path(args.vault_path).resolve()

    # Parse note types if provided
    note_types = None
    note_types_is_custom = False
    if args.note_types:
        if args.note_types.lower() == "custom":
            note_types_is_custom = True
        elif args.note_types.lower() == "all":
            note_types = None  # None means all types
        else:
            note_types = [t.strip() for t in args.note_types.split(",") if t.strip()]

    # Parse core properties if provided
    core_properties = None
    core_properties_is_custom = False
    if args.core_properties:
        if args.core_properties.lower() == "custom":
            core_properties_is_custom = True
        elif args.core_properties.lower() == "all":
            core_properties = None  # None means all properties
        else:
            core_properties = [p.strip() for p in args.core_properties.split(",") if p.strip()]

    # Parse custom properties if provided
    custom_properties: list[str] | None = None
    if args.custom_properties:
        if args.custom_properties.lower() not in ("none", "skip", ""):
            custom_properties = [
                p.strip() for p in args.custom_properties.split(",") if p.strip()
            ]

    # Parse per-type properties if provided (format: type1:prop1,prop2;type2:prop3)
    # Use "none" or empty string to mark a type as configured without properties
    per_type_properties: dict[str, list[str]] = {}
    if args.per_type_props:
        for type_spec in args.per_type_props.split(";"):
            if ":" in type_spec:
                type_name, props = type_spec.split(":", 1)
                type_name = type_name.strip()
                props = props.strip()
                # Empty string or "none" means type is configured but with no extra props
                if props.lower() in ("none", "skip", ""):
                    prop_list = []
                else:
                    prop_list = [p.strip() for p in props.split(",") if p.strip()]
                if type_name:
                    per_type_properties[type_name] = prop_list

    # Pass-through: --list
    if args.list:
        script = get_script_path()
        cmd = ["uv", "run", str(script), "--list"]
        result = subprocess.run(cmd)  # noqa: S603
        return result.returncode

    # Pass-through: --check
    if args.check:
        status = check_vault_status(vault_path)
        print(json.dumps(status, indent=2))
        return 0

    # STEP 1: Check vault status FIRST (always)
    status = check_vault_status(vault_path)

    if status.get("status") == "error":
        print(json.dumps(status, indent=2))
        return 1

    # STEP 2: Handle based on vault status
    is_existing = status.get("status") == "existing"

    if is_existing and not args.action:
        # Existing vault but no action specified - prompt for action
        output_action_prompt(status)
        return 0

    if args.action:
        # Action was specified
        if args.action == "abort":
            output_abort()
            return 0
        elif args.action == "migrate":
            output_migrate_hint()
            return 0
        elif args.action in ("continue", "reset"):
            # Proceed to methodology selection
            if not args.methodology:
                output_methodology_prompt(str(vault_path), action=args.action)
                return 0

            # Methodology specified - check for note types
            if not args.defaults:
                # Need note types selection
                if not args.note_types:
                    # No note types argument at all - show All/Custom choice
                    output_note_types_prompt(str(vault_path), args.methodology, args.action)
                    return 0
                elif note_types_is_custom:
                    # User chose "custom" - show multi-select
                    output_note_types_select_prompt(str(vault_path), args.methodology, args.action)
                    return 0
                # note_types_is_all or explicit list - continue to properties

            # Note types specified - check for core properties
            if not args.defaults:
                if not args.core_properties:
                    # No core properties argument at all - show All/Custom choice
                    output_properties_prompt(
                        str(vault_path),
                        args.methodology,
                        args.note_types or "all",
                        args.action,
                    )
                    return 0
                elif core_properties_is_custom:
                    # User chose "custom" - show multi-select
                    output_properties_select_prompt(
                        str(vault_path),
                        args.methodology,
                        args.note_types or "all",
                        args.action,
                    )
                    return 0
                # core_properties_is_all or explicit list - continue to custom props

            # Core properties specified - check for custom properties
            if not args.defaults and args.custom_properties is None:
                output_custom_properties_prompt(
                    str(vault_path),
                    args.methodology,
                    args.note_types or "all",
                    args.core_properties or "all",
                    args.action,
                )
                return 0

            # Custom properties handled - check for per-type properties
            # Get the selected note types to check if we need per-type config
            selected_types = note_types or list(
                get_note_types_for_methodology(args.methodology).keys()
            )
            types_needing_config = []
            for type_name in selected_types:
                if type_name not in per_type_properties:
                    type_data = get_note_types_for_methodology(args.methodology)
                    type_config = type_data.get(type_name, {})
                    props = type_config.get("properties", {})
                    # Check if type has additional_required or optional properties
                    if (props.get("additional_required") or props.get("optional")):
                        types_needing_config.append(type_name)

            # If there are types that need per-type configuration
            if not args.defaults and types_needing_config:
                current_type = types_needing_config[0]
                remaining = types_needing_config[1:]
                output_per_type_properties_prompt(
                    str(vault_path),
                    args.methodology,
                    args.note_types or "all",
                    args.core_properties or "all",
                    args.custom_properties or "none",
                    current_type,
                    remaining,
                    args.action,
                    {k: ",".join(v) for k, v in per_type_properties.items()},
                )
                return 0

            # Execute with all parameters
            return execute_init(
                vault_path,
                args.methodology,
                reset=(args.action == "reset"),
                note_types=note_types,
                core_properties=core_properties,
                custom_properties=custom_properties,
                per_type_properties=per_type_properties,
            )

    # STEP 3: New/empty vault - prompt for methodology
    if not args.methodology:
        output_methodology_prompt(str(vault_path))
        return 0

    # STEP 4: Methodology specified - check for note types
    if not args.defaults:
        if not args.note_types:
            # No note types argument - show All/Custom choice
            output_note_types_prompt(str(vault_path), args.methodology)
            return 0
        elif note_types_is_custom:
            # User chose "custom" - show multi-select
            output_note_types_select_prompt(str(vault_path), args.methodology)
            return 0
        # note_types_is_all or explicit list - continue to properties

    # STEP 5: Note types specified - check for core properties
    if not args.defaults:
        if not args.core_properties:
            # No core properties argument - show All/Custom choice
            output_properties_prompt(
                str(vault_path),
                args.methodology,
                args.note_types or "all",
            )
            return 0
        elif core_properties_is_custom:
            # User chose "custom" - show multi-select
            output_properties_select_prompt(
                str(vault_path),
                args.methodology,
                args.note_types or "all",
            )
            return 0
        # core_properties_is_all or explicit list - continue to custom props

    # STEP 6: Core properties specified - check for custom properties
    if not args.defaults and args.custom_properties is None:
        output_custom_properties_prompt(
            str(vault_path),
            args.methodology,
            args.note_types or "all",
            args.core_properties or "all",
        )
        return 0

    # STEP 7: Custom properties handled - check for per-type properties
    selected_types = note_types or list(
        get_note_types_for_methodology(args.methodology).keys()
    )
    types_needing_config = []
    for type_name in selected_types:
        if type_name not in per_type_properties:
            type_data = get_note_types_for_methodology(args.methodology)
            type_config = type_data.get(type_name, {})
            props = type_config.get("properties", {})
            if (props.get("additional_required") or props.get("optional")):
                types_needing_config.append(type_name)

    if not args.defaults and types_needing_config:
        current_type = types_needing_config[0]
        remaining = types_needing_config[1:]
        output_per_type_properties_prompt(
            str(vault_path),
            args.methodology,
            args.note_types or "all",
            args.core_properties or "all",
            args.custom_properties or "none",
            current_type,
            remaining,
            per_type_properties={k: ",".join(v) for k, v in per_type_properties.items()},
        )
        return 0

    # STEP 8: Execute initialization
    return execute_init(
        vault_path,
        args.methodology,
        note_types=note_types,
        core_properties=core_properties,
        custom_properties=custom_properties,
        per_type_properties=per_type_properties,
    )


if __name__ == "__main__":
    sys.exit(main())
