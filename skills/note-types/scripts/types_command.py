#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Types Command - Unified note type management

Replaces the deprecated /note-types command with obsidian:types:
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
from note_types import NoteTypesManager

# ANSI colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


def show_deprecation_warning() -> None:
    """Show deprecation warning for old command."""
    warning = f"""
{COLOR_YELLOW}{COLOR_BOLD}DEPRECATION WARNING{COLOR_RESET}
{COLOR_YELLOW}The '/note-types' command is deprecated and will be removed in v2.0.0.{COLOR_RESET}
{COLOR_CYAN}Use 'obsidian:types' instead.{COLOR_RESET}
"""
    print(warning, file=sys.stderr)


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
            "core_properties": manager._get_core_properties(),
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

    manager.list_types()
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

    manager.show_type(name)
    return 0


def cmd_add(
    manager: NoteTypesManager,
    name: str,
    config_json: str | None = None,
    interactive: bool = True,
) -> int:
    """Add a new note type.

    Args:
        manager: NoteTypesManager instance
        name: Note type name
        config_json: JSON configuration string
        interactive: Use interactive prompts

    Returns:
        Exit code
    """
    if name in manager.note_types:
        print(f"{COLOR_RED}Note type '{name}' already exists.{COLOR_RESET}")
        print(f"Use {COLOR_CYAN}obsidian:types edit {name}{COLOR_RESET} to modify it.")
        return 1

    config = None
    if config_json:
        try:
            config = json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"{COLOR_RED}Invalid JSON: {e}{COLOR_RESET}")
            return 1

    try:
        manager.add_type(name, interactive=interactive and not config, config=config)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def cmd_edit(
    manager: NoteTypesManager,
    name: str,
    config_json: str | None = None,
    interactive: bool = True,
) -> int:
    """Edit an existing note type.

    Args:
        manager: NoteTypesManager instance
        name: Note type name
        config_json: JSON configuration string
        interactive: Use interactive prompts

    Returns:
        Exit code
    """
    if name not in manager.note_types:
        print(f"{COLOR_RED}Note type '{name}' not found.{COLOR_RESET}")
        print(f"Available: {', '.join(manager.note_types.keys())}")
        return 1

    config = None
    if config_json:
        try:
            config = json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"{COLOR_RED}Invalid JSON: {e}{COLOR_RESET}")
            return 1

    try:
        manager.edit_type(name, interactive=interactive and not config, config=config)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def cmd_remove(manager: NoteTypesManager, name: str, yes: bool = False) -> int:
    """Remove a note type.

    Args:
        manager: NoteTypesManager instance
        name: Note type name
        yes: Skip confirmation

    Returns:
        Exit code
    """
    if name not in manager.note_types:
        print(f"{COLOR_RED}Note type '{name}' not found.{COLOR_RESET}")
        return 1

    try:
        manager.remove_type(name, skip_confirm=yes)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def cmd_wizard(manager: NoteTypesManager) -> int:
    """Run interactive wizard.

    Args:
        manager: NoteTypesManager instance

    Returns:
        Exit code
    """
    try:
        manager.wizard()
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian Note Type Management (obsidian:types)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  (none)           List all note types (same as 'list')
  list             List all note types
  show <name>      Show details for a note type
  add <name>       Add a new note type
  edit <name>      Edit an existing note type
  remove <name>    Remove a note type
  wizard           Interactive wizard

Examples:
  %(prog)s --vault .
  %(prog)s --vault . show map
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
    parser.add_argument(
        "--deprecated-warning",
        action="store_true",
        help=argparse.SUPPRESS,  # Hidden flag to show deprecation warning
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # list
    subparsers.add_parser("list", help="List all note types")

    # show
    show_parser = subparsers.add_parser("show", help="Show note type details")
    show_parser.add_argument("name", help="Note type name")

    # add
    add_parser = subparsers.add_parser("add", help="Add new note type")
    add_parser.add_argument("name", help="Note type name")
    add_parser.add_argument("--config", metavar="JSON", help="JSON configuration")
    add_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use defaults instead of prompts",
    )

    # edit
    edit_parser = subparsers.add_parser("edit", help="Edit note type")
    edit_parser.add_argument("name", help="Note type name")
    edit_parser.add_argument("--config", metavar="JSON", help="JSON configuration")
    edit_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use provided config only",
    )

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove note type")
    remove_parser.add_argument("name", help="Note type name")
    remove_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # wizard
    subparsers.add_parser("wizard", help="Interactive wizard")

    args = parser.parse_args()

    # Show deprecation warning if triggered from old command
    if args.deprecated_warning:
        show_deprecation_warning()

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
        return cmd_add(
            manager,
            args.name,
            args.config,
            not getattr(args, "non_interactive", False),
        )
    elif args.command == "edit":
        return cmd_edit(
            manager,
            args.name,
            args.config,
            not getattr(args, "non_interactive", False),
        )
    elif args.command == "remove":
        return cmd_remove(manager, args.name, args.yes)
    elif args.command == "wizard":
        return cmd_wizard(manager)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
