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
    """Output prompt for note type selection.

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        action: Previous action (continue/reset) to preserve in next command
    """
    note_types_data = get_note_types_for_methodology(methodology)

    if "error" in note_types_data:
        # Fallback - skip note type selection
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
        "prompt_type": "note_types_required",
        "message": f"Select note types for {methodology}",
        "vault_path": vault_path,
        "methodology": methodology,
        "previous_action": action,
        "question": "Which note types do you want to include?",
        "multi_select": True,
        "options": options,
        "next_step": next_cmd,
        "hint": "Use --defaults to skip this step and include all note types",
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
) -> int:
    """Execute the actual vault initialization.

    Args:
        vault_path: Path to the vault
        methodology: Selected methodology
        reset: Whether to reset the vault
        note_types: List of note types to include (None = all)
    """
    script = get_script_path()

    cmd = ["uv", "run", str(script), str(vault_path), "-m", methodology, "--defaults"]
    if reset:
        cmd.append("--reset")
    if note_types:
        cmd.extend(["--note-types", ",".join(note_types)])

    # Run and stream output
    result = subprocess.run(cmd)  # noqa: S603
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
        "--defaults",
        action="store_true",
        help="Use all default note types (skip note type selection)",
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
    if args.note_types:
        note_types = [t.strip() for t in args.note_types.split(",") if t.strip()]

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
            if not args.defaults and not note_types:
                output_note_types_prompt(str(vault_path), args.methodology, args.action)
                return 0
            # Execute with methodology and note types
            return execute_init(
                vault_path,
                args.methodology,
                reset=(args.action == "reset"),
                note_types=note_types,
            )

    # STEP 3: New/empty vault - prompt for methodology
    if not args.methodology:
        output_methodology_prompt(str(vault_path))
        return 0

    # STEP 4: Methodology specified - check for note types
    if not args.defaults and not note_types:
        output_note_types_prompt(str(vault_path), args.methodology)
        return 0

    # STEP 5: Execute initialization
    return execute_init(vault_path, args.methodology, note_types=note_types)


if __name__ == "__main__":
    sys.exit(main())
