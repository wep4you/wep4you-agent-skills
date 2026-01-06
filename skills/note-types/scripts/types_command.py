#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Types Command - Unified note type management

Commands:
- obsidian:types              List all note types
- obsidian:types list         List all note types (explicit)
- obsidian:types show <name>  Show details for specific type
- obsidian:types add <name>   Add new note type
- obsidian:types edit <name>  Edit existing note type
- obsidian:types remove <name> Remove note type
- obsidian:types wizard       Interactive wizard

Usage:
    uv run types_command.py --vault /path/to/vault
    uv run types_command.py --vault /path/to/vault show map
    uv run types_command.py --vault /path/to/vault add meeting --config '{...}'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Import from note_types in same directory
sys.path.insert(0, str(Path(__file__).parent))
from note_type_wizard import handle_add, handle_edit, handle_remove, handle_wizard
from note_types import NoteTypesManager, display_type_details, display_type_list

# ANSI colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


def cmd_list(manager: NoteTypesManager, output_format: str = "text") -> int:
    """List all note types.

    Args:
        manager: NoteTypesManager instance
        output_format: Output format (text, json)

    Returns:
        Exit code
    """
    if output_format == "json":
        data = {
            "methodology": manager.settings.get("methodology", "unknown"),
            "core_properties": manager.get_core_properties(),
            "note_types": {},
        }
        for name, config in manager.note_types.items():
            data["note_types"][name] = {
                "description": config.get("description", ""),
                "folder_hints": config.get("folder_hints", []),
                "icon": config.get("icon", ""),
                "properties": config.get("properties", {}),
            }
        print(json.dumps(data, indent=2))
        return 0

    display_type_list(manager)
    return 0


def cmd_show(manager: NoteTypesManager, name: str, output_format: str = "text") -> int:
    """Show details for a note type.

    Args:
        manager: NoteTypesManager instance
        name: Note type name
        output_format: Output format (text, json)

    Returns:
        Exit code
    """
    if name not in manager.note_types:
        print(f"{COLOR_RED}Note type '{name}' not found.{COLOR_RESET}")
        print(f"Available: {', '.join(manager.note_types.keys())}")
        return 1

    if output_format == "json":
        config = manager.note_types[name]
        data = {
            "name": name,
            "description": config.get("description", ""),
            "folder_hints": config.get("folder_hints", []),
            "icon": config.get("icon", ""),
            "properties": config.get("properties", {}),
            "validation": config.get("validation", {}),
            "template": config.get("template", ""),
        }
        print(json.dumps(data, indent=2))
        return 0

    display_type_details(manager, name)
    return 0


def cmd_add(
    manager: NoteTypesManager,
    name: str,
    config_json: str | None = None,
) -> int:
    """Add a new note type.

    Args:
        manager: NoteTypesManager instance
        name: Note type name
        config_json: JSON configuration string (if None, interactive mode)

    Returns:
        Exit code
    """
    if name in manager.note_types:
        print(f"{COLOR_RED}Note type '{name}' already exists.{COLOR_RESET}")
        print(f"Use {COLOR_CYAN}obsidian:types edit {name}{COLOR_RESET} to modify it.")
        return 1

    # If no config and not interactive, return JSON guidance
    if not config_json and not is_interactive():
        result = {
            "interactive_required": True,
            "action": "add",
            "name": name,
            "message": f"Provide --config JSON to add note type '{name}'",
            "config_schema": {
                "description": "Brief description of the note type (required)",
                "folder": "Folder path, e.g. 'Meetings/' (required)",
                "required_props": "List of additional required properties (optional)",
                "optional_props": "List of optional properties (optional)",
                "icon": "Lucide icon name, e.g. 'users', 'calendar' (optional)",
            },
            "example": {
                "command": f"obsidian:types add {name} --config '{{...}}'",
                "config": {
                    "description": "Meeting notes",
                    "folder": "Meetings/",
                    "required_props": ["attendees", "date"],
                    "optional_props": ["action_items"],
                    "icon": "users",
                },
            },
        }
        print(json.dumps(result, indent=2))
        return 0

    try:
        # non_interactive=False means use interactive prompts if no config
        handle_add(manager, name, config_json, non_interactive=bool(config_json))
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def cmd_edit(
    manager: NoteTypesManager,
    name: str,
    config_json: str | None = None,
) -> int:
    """Edit an existing note type.

    Args:
        manager: NoteTypesManager instance
        name: Note type name
        config_json: JSON configuration string (if None, interactive mode)

    Returns:
        Exit code
    """
    if name not in manager.note_types:
        print(f"{COLOR_RED}Note type '{name}' not found.{COLOR_RESET}")
        print(f"Available: {', '.join(manager.note_types.keys())}")
        return 1

    # If no config and not interactive, return JSON guidance with current values
    if not config_json and not is_interactive():
        current = manager.note_types[name]
        result = {
            "interactive_required": True,
            "action": "edit",
            "name": name,
            "message": f"Provide --config JSON to edit note type '{name}'",
            "current_config": {
                "description": current.get("description", ""),
                "folder_hints": current.get("folder_hints", []),
                "properties": current.get("properties", {}),
                "icon": current.get("icon", ""),
            },
            "config_schema": {
                "description": "Brief description of the note type",
                "folder": "Folder path, e.g. 'Meetings/'",
                "required_props": "List of additional required properties",
                "optional_props": "List of optional properties",
                "icon": "Lucide icon name, e.g. 'users', 'calendar'",
            },
            "example": {
                "command": f"obsidian:types edit {name} --config '{{...}}'",
                "config": {
                    "description": "Updated description",
                    "required_props": ["status", "priority"],
                },
            },
        }
        print(json.dumps(result, indent=2))
        return 0

    try:
        # Create minimal args namespace for handle_edit compatibility
        args = argparse.Namespace(
            description=None, folder=None, required_props=None, optional_props=None, icon=None
        )
        handle_edit(manager, name, config_json, non_interactive=bool(config_json), args=args)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def cmd_remove(manager: NoteTypesManager, name: str, yes: bool = False) -> int:
    """Remove a note type.

    Args:
        manager: NoteTypesManager instance
        name: Note type name
        yes: Skip confirmation (--yes flag)

    Returns:
        Exit code
    """
    if name not in manager.note_types:
        print(f"{COLOR_RED}Note type '{name}' not found.{COLOR_RESET}")
        return 1

    # If no --yes flag and not interactive, return JSON asking for confirmation
    if not yes and not is_interactive():
        current = manager.note_types[name]
        result = {
            "interactive_required": True,
            "action": "remove",
            "name": name,
            "message": f"Add --yes flag to confirm removal of note type '{name}'",
            "type_to_remove": {
                "name": name,
                "description": current.get("description", ""),
                "folder_hints": current.get("folder_hints", []),
            },
            "warning": "This will remove the note type from settings. "
            "Notes in the folder will NOT be deleted.",
            "confirm_command": f"obsidian:types remove {name} --yes",
        }
        print(json.dumps(result, indent=2))
        return 0

    try:
        handle_remove(manager, name, skip_confirm=yes)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


def cmd_wizard(manager: NoteTypesManager) -> int:
    """Run interactive wizard.

    Args:
        manager: NoteTypesManager instance

    Returns:
        Exit code
    """
    # If not running interactively, return JSON for Claude Code to handle
    if not is_interactive():
        existing_types = list(manager.note_types.keys())
        result = {
            "interactive_required": True,
            "message": "Use 'add' subcommand with --config to create a note type non-interactively",
            "existing_types": existing_types,
            "fields": {
                "name": "Note type name (lowercase, no spaces)",
                "description": "Brief description of the note type",
                "folder": "Folder path for notes (e.g., 'Meetings/')",
                "required_props": "Additional required properties (optional, comma-separated)",
                "optional_props": "Optional properties (optional, comma-separated)",
                "icon": "Lucide icon name (optional, e.g., 'calendar', 'users')",
            },
            "example": {
                "command": "obsidian:types add meeting --config '{...}'",
                "config": {
                    "description": "Meeting notes",
                    "folder": "Meetings",
                    "required_props": ["attendees", "date"],
                    "optional_props": ["action_items"],
                    "icon": "users",
                },
            },
        }
        print(json.dumps(result, indent=2))
        return 0

    try:
        handle_wizard(manager)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def main() -> int:
    """CLI entry point."""
    config_help = """\
JSON object with these fields:
  description   - Brief description (required for add)
  folder        - Folder path, e.g. 'Meetings/' (required for add)
  required_props - List of additional required properties
  optional_props - List of optional properties
  icon          - Lucide icon name, e.g. 'users', 'calendar'

Example: '{"description": "Meeting notes", "folder": "Meetings/", "icon": "users"}'"""

    parser = argparse.ArgumentParser(
        description="Obsidian Note Type Management (obsidian:types)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  (none)           List all note types (same as 'list')
  list             List all note types
  show <name>      Show details for a note type
  add <name>       Add a new note type (interactive, or use --config)
  edit <name>      Edit an existing note type (interactive, or use --config)
  remove <name>    Remove a note type (interactive, or use --yes)
  wizard           Interactive wizard (same as add without name)

Interactive Mode:
  By default, add/edit/remove run interactively with prompts.
  Use --config or --yes to run non-interactively.

Examples:
  %(prog)s --vault .
  %(prog)s --vault . show map
  %(prog)s --vault . add meeting
  %(prog)s --vault . add meeting --config '{"description": "Meeting notes", "folder": "Meetings/"}'
  %(prog)s --vault . edit project --config '{"required_props": ["status", "deadline"]}'
  %(prog)s --vault . remove custom --yes
        """,
    )

    parser.add_argument(
        "--vault",
        type=str,
        default=".",
        help="Path to vault (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # list
    subparsers.add_parser("list", help="List all note types")

    # show
    show_parser = subparsers.add_parser("show", help="Show note type details")
    show_parser.add_argument("name", help="Note type name")

    # add
    add_parser = subparsers.add_parser(
        "add",
        help="Add new note type (interactive by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_parser.add_argument("name", help="Note type name (lowercase, no spaces)")
    add_parser.add_argument(
        "--config",
        metavar="JSON",
        help=config_help,
    )

    # edit
    edit_parser = subparsers.add_parser(
        "edit",
        help="Edit note type (interactive by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    edit_parser.add_argument("name", help="Note type name")
    edit_parser.add_argument(
        "--config",
        metavar="JSON",
        help=config_help,
    )

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove note type")
    remove_parser.add_argument("name", help="Note type name")
    remove_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt (required for non-interactive)",
    )

    # wizard
    subparsers.add_parser("wizard", help="Interactive wizard for creating note types")

    args = parser.parse_args()

    # Initialize manager
    try:
        manager = NoteTypesManager(args.vault)
    except SystemExit:
        return 1

    # Route to appropriate handler
    if args.command is None or args.command == "list":
        return cmd_list(manager, args.format)
    elif args.command == "show":
        return cmd_show(manager, args.name, args.format)
    elif args.command == "add":
        return cmd_add(manager, args.name, args.config)
    elif args.command == "edit":
        return cmd_edit(manager, args.name, args.config)
    elif args.command == "remove":
        return cmd_remove(manager, args.name, args.yes)
    elif args.command == "wizard":
        return cmd_wizard(manager)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
