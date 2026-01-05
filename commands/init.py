#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
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
import shutil
import subprocess
import sys
from pathlib import Path

# Add project root to path for imports (needed when running as standalone script)
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from skills.core.prompts import (  # noqa: E402
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


def get_script_path() -> Path:
    """Get path to init_vault.py script."""
    commands_dir = Path(__file__).parent
    plugin_root = commands_dir.parent
    return plugin_root / "skills" / "init" / "scripts" / "init_vault.py"


def get_uv_path() -> str:
    """Get the full path to the uv executable."""
    uv_path = shutil.which("uv")
    if uv_path is None:
        # Fallback to just "uv" if not found (will fail with clear error)
        return "uv"
    return uv_path


def get_note_types_for_methodology(methodology: str) -> dict:
    """Get note types for a methodology by calling init_vault.py."""
    script = get_script_path()

    try:
        cmd = [get_uv_path(), "run", str(script), "--list-note-types", methodology]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # noqa: S603

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
        cmd = [get_uv_path(), "run", str(script), str(vault_path), "--check"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # noqa: S603

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"status": "error", "message": result.stderr or "Failed to check vault status"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Timeout checking vault status"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON from vault check"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def execute_init(
    vault_path: Path,
    methodology: str,
    reset: bool = False,
    note_types: list[str] | None = None,
    core_properties: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
    ranking_system: str = "rank",
    git_action: str = "no",
) -> int:
    """Execute the actual vault initialization."""
    import os

    script = get_script_path()

    cmd = [get_uv_path(), "run", str(script), str(vault_path), "-m", methodology, "--defaults"]
    cmd.extend(["--ranking-system", ranking_system])
    if reset:
        cmd.append("--reset")
    if git_action == "yes":
        cmd.append("--git")
    elif git_action == "keep":
        cmd.append("--git-keep")
    if note_types:
        cmd.extend(["--note-types", ",".join(note_types)])
    if core_properties:
        cmd.extend(["--core-properties", ",".join(core_properties)])
    if custom_properties:
        cmd.extend(["--custom-properties", ",".join(custom_properties)])
    if per_type_properties:
        per_type_str = ";".join(f"{k}:{','.join(v)}" for k, v in per_type_properties.items())
        cmd.extend(["--per-type-props", per_type_str])

    env = os.environ.copy()
    env["INIT_FROM_WRAPPER"] = "1"

    result = subprocess.run(cmd, env=env)  # noqa: S603
    return result.returncode


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Vault initialization wrapper for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("vault_path", nargs="?", default=".", help="Path to vault")
    parser.add_argument("--action", choices=["abort", "continue", "reset", "migrate"])
    parser.add_argument(
        "-m", "--methodology", choices=["lyt-ace", "para", "zettelkasten", "minimal"]
    )
    parser.add_argument("--note-types", help="Comma-separated list of note types")
    parser.add_argument("--core-properties", help="Comma-separated list of core properties")
    parser.add_argument("--custom-properties", help="Comma-separated list of custom properties")
    parser.add_argument(
        "--per-type-props", help="Per-type properties: type1:prop1,prop2;type2:prop3"
    )
    parser.add_argument("--ranking-system", choices=["rank", "priority"])
    parser.add_argument("--git", choices=["yes", "no", "keep"])
    parser.add_argument("--defaults", action="store_true", help="Use all defaults")
    parser.add_argument("--check", action="store_true", help="Check vault status")
    parser.add_argument("--list", action="store_true", help="List methodologies")

    return parser.parse_args()


def parse_list_arg(
    value: str | None, special_values: set[str] | None = None
) -> tuple[list[str] | None, bool]:
    """Parse a comma-separated list argument.

    Args:
        value: Argument value
        special_values: Set of special values that trigger custom handling

    Returns:
        Tuple of (parsed list or None, is_special_value)
    """
    special_values = special_values or {"custom", "all"}
    if not value:
        return None, False
    if value.lower() in special_values:
        return None, value.lower() == "custom"
    return [v.strip() for v in value.split(",") if v.strip()], False


def parse_per_type_properties(value: str | None) -> dict[str, list[str]]:
    """Parse per-type properties argument (format: type1:prop1,prop2;type2:prop3)."""
    result: dict[str, list[str]] = {}
    if not value:
        return result

    for type_spec in value.split(";"):
        if ":" not in type_spec:
            continue
        type_name, props = type_spec.split(":", 1)
        type_name = type_name.strip()
        props = props.strip()

        if props.lower() in ("none", "skip", ""):
            prop_list = []
        else:
            prop_list = [p.strip() for p in props.split(",") if p.strip()]

        if type_name:
            result[type_name] = prop_list

    return result


def get_types_needing_config(methodology: str, selected_types: list[str] | None) -> list[str]:
    """Get list of note types that have configurable properties."""
    type_data = get_note_types_for_methodology(methodology)
    all_types = selected_types or list(type_data.keys())

    types_needing_config = []
    for type_name in all_types:
        type_config = type_data.get(type_name, {})
        props = type_config.get("properties", {})
        if props.get("additional_required") or props.get("optional"):
            types_needing_config.append(type_name)

    return types_needing_config


def handle_workflow(
    args: argparse.Namespace,
    vault_path: Path,
    note_types: list[str] | None,
    note_types_is_custom: bool,
    core_properties: list[str] | None,
    core_properties_is_custom: bool,
    custom_properties: list[str] | None,
    per_type_properties: dict[str, list[str]],
) -> int:
    """Handle the main workflow logic.

    Returns:
        Exit code (0 for prompts, non-zero for errors)
    """
    # Note types prompt
    if not args.defaults and not args.note_types:
        type_data = get_note_types_for_methodology(args.methodology)
        type_names = list(type_data.keys()) if "error" not in type_data else []
        output_note_types_prompt(str(vault_path), args.methodology, type_names, args.action)
        return 0

    if note_types_is_custom:
        type_data = get_note_types_for_methodology(args.methodology)
        output_note_types_select_prompt(str(vault_path), args.methodology, type_data, args.action)
        return 0

    # Ranking system prompt (only if project type selected)
    selected_note_types = args.note_types or "all"
    has_project_type = selected_note_types == "all" or "project" in selected_note_types
    if has_project_type and not args.ranking_system:
        output_ranking_system_prompt(
            str(vault_path), args.methodology, selected_note_types, args.action
        )
        return 0

    # Core properties prompt
    if not args.defaults and not args.core_properties:
        output_properties_prompt(
            str(vault_path), args.methodology, args.note_types or "all", args.action
        )
        return 0

    if core_properties_is_custom:
        output_properties_select_prompt(
            str(vault_path), args.methodology, args.note_types or "all", args.action
        )
        return 0

    # Custom properties prompt
    if not args.defaults and args.custom_properties is None:
        output_custom_properties_prompt(
            str(vault_path),
            args.methodology,
            args.note_types or "all",
            args.core_properties or "all",
            args.action,
        )
        return 0

    # Per-type properties prompt
    types_needing_config = get_types_needing_config(args.methodology, note_types)
    if not args.defaults and types_needing_config and not per_type_properties:
        type_data = get_note_types_for_methodology(args.methodology)
        output_per_type_properties_prompt(
            str(vault_path),
            args.methodology,
            args.note_types or "all",
            args.core_properties or "all",
            args.custom_properties or "none",
            types_needing_config,
            type_data,
            args.action,
            args.ranking_system or "rank",
        )
        return 0

    # Git init prompt
    if not args.defaults and args.git is None:
        output_git_init_prompt(
            str(vault_path),
            args.methodology,
            args.note_types or "all",
            args.core_properties or "all",
            args.custom_properties or "none",
            {k: ",".join(v) for k, v in per_type_properties.items()},
            args.action,
            args.ranking_system or "rank",
        )
        return 0

    # Execute initialization
    return execute_init(
        vault_path,
        args.methodology,
        reset=(args.action == "reset"),
        note_types=note_types,
        core_properties=core_properties,
        custom_properties=custom_properties,
        per_type_properties=per_type_properties,
        ranking_system=args.ranking_system or "rank",
        git_action=args.git or "no",
    )


def main() -> int:
    """Main entry point."""
    args = parse_arguments()
    vault_path = Path(args.vault_path).resolve()

    # Parse arguments
    note_types, note_types_is_custom = parse_list_arg(args.note_types)
    core_properties, core_properties_is_custom = parse_list_arg(args.core_properties)
    custom_properties: list[str] | None = None
    if args.custom_properties and args.custom_properties.lower() not in ("none", "skip", ""):
        custom_properties = [p.strip() for p in args.custom_properties.split(",") if p.strip()]
    per_type_properties = parse_per_type_properties(args.per_type_props)

    # Pass-through: --list
    if args.list:
        script = get_script_path()
        result = subprocess.run([get_uv_path(), "run", str(script), "--list"])  # noqa: S603
        return result.returncode

    # Pass-through: --check
    if args.check:
        status = check_vault_status(vault_path)
        print(json.dumps(status, indent=2))
        return 0

    # Check vault status
    status = check_vault_status(vault_path)
    if status.get("status") == "error":
        print(json.dumps(status, indent=2))
        return 1

    is_existing = status.get("status") == "existing"

    # Handle existing vault without action
    if is_existing and not args.action:
        output_action_prompt(status)
        return 0

    # Handle action responses
    if args.action:
        if args.action == "abort":
            output_abort()
            return 0
        elif args.action == "migrate":
            output_migrate_hint()
            return 0
        elif args.action in ("continue", "reset"):
            if not args.methodology:
                output_methodology_prompt(str(vault_path), action=args.action)
                return 0

            return handle_workflow(
                args,
                vault_path,
                note_types,
                note_types_is_custom,
                core_properties,
                core_properties_is_custom,
                custom_properties,
                per_type_properties,
            )

    # New/empty vault - prompt for methodology
    if not args.methodology:
        output_methodology_prompt(str(vault_path))
        return 0

    # Handle workflow for new vault
    return handle_workflow(
        args,
        vault_path,
        note_types,
        note_types_is_custom,
        core_properties,
        core_properties_is_custom,
        custom_properties,
        per_type_properties,
    )


if __name__ == "__main__":
    sys.exit(main())
