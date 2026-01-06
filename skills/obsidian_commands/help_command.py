#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Obsidian Help Command - Central help system for all obsidian commands.

Provides:
- obsidian:help              # Overview of all commands
- obsidian:help init         # Details for init command
- obsidian:help types add    # Details for subcommand
- obsidian:help --json       # Machine-readable output

Usage:
    uv run help_command.py
    uv run help_command.py init
    uv run help_command.py types add
    uv run help_command.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field

# ANSI colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


@dataclass
class SubcommandInfo:
    """Information about a subcommand."""

    name: str
    description: str
    examples: list[str] = field(default_factory=list)


@dataclass
class CommandInfo:
    """Information about a command."""

    name: str
    description: str
    subcommands: list[SubcommandInfo] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


def get_command_registry() -> list[CommandInfo]:
    """Get registry of all obsidian commands with their metadata.

    Returns:
        List of CommandInfo objects
    """
    return [
        CommandInfo(
            name="obsidian:init",
            description="Initialize Obsidian vault with a PKM methodology",
            subcommands=[],
            examples=[
                "obsidian:init /path/to/vault",
                "obsidian:init . --methodology para",
                "obsidian:init --list",
            ],
        ),
        CommandInfo(
            name="obsidian:config",
            description="Configuration management for vault settings",
            subcommands=[
                SubcommandInfo(
                    name="show",
                    description="Show current configuration",
                    examples=[
                        "obsidian:config show",
                        "obsidian:config show --format json",
                        "obsidian:config show --verbose",
                    ],
                ),
                SubcommandInfo(
                    name="edit",
                    description="Edit settings in system editor",
                    examples=["obsidian:config edit"],
                ),
                SubcommandInfo(
                    name="validate",
                    description="Validate configuration structure",
                    examples=[
                        "obsidian:config validate",
                        "obsidian:config validate --format json",
                    ],
                ),
                SubcommandInfo(
                    name="methodologies",
                    description="List available methodologies",
                    examples=[
                        "obsidian:config methodologies",
                        "obsidian:config methodologies --format json",
                    ],
                ),
                SubcommandInfo(
                    name="create",
                    description="Create default settings",
                    examples=[
                        "obsidian:config create --methodology para",
                        "obsidian:config create --force",
                    ],
                ),
            ],
            examples=[
                "obsidian:config",
                "obsidian:config show --format yaml",
            ],
        ),
        CommandInfo(
            name="obsidian:types",
            description="Note type management for defining and organizing note types",
            subcommands=[
                SubcommandInfo(
                    name="list",
                    description="List all note types",
                    examples=[
                        "obsidian:types list",
                        "obsidian:types list --format json",
                    ],
                ),
                SubcommandInfo(
                    name="show",
                    description="Show details for a note type",
                    examples=[
                        "obsidian:types show project",
                        "obsidian:types show map --format json",
                    ],
                ),
                SubcommandInfo(
                    name="add",
                    description="Add a new note type",
                    examples=[
                        "obsidian:types add meeting --config '{\"folder\": \"Meetings/\", \"description\": \"Meeting notes\"}'",
                        "obsidian:types add",  # Interactive
                    ],
                ),
                SubcommandInfo(
                    name="edit",
                    description="Edit an existing note type",
                    examples=[
                        "obsidian:types edit project --config '{\"description\": \"Updated\"}'",
                    ],
                ),
                SubcommandInfo(
                    name="remove",
                    description="Remove a note type",
                    examples=[
                        "obsidian:types remove custom --yes",
                    ],
                ),
                SubcommandInfo(
                    name="wizard",
                    description="Interactive wizard for creating note types",
                    examples=["obsidian:types wizard"],
                ),
            ],
            examples=[
                "obsidian:types",
                "obsidian:types list",
                "obsidian:types show project",
            ],
        ),
        CommandInfo(
            name="obsidian:props",
            description="Property management for frontmatter properties",
            subcommands=[
                SubcommandInfo(
                    name="core",
                    description="List core properties",
                    examples=["obsidian:props core"],
                ),
                SubcommandInfo(
                    name="type",
                    description="List properties for a note type",
                    examples=["obsidian:props type project"],
                ),
                SubcommandInfo(
                    name="required",
                    description="List required properties",
                    examples=["obsidian:props required"],
                ),
                SubcommandInfo(
                    name="add",
                    description="Add a property",
                    examples=["obsidian:props add status --to project"],
                ),
                SubcommandInfo(
                    name="remove",
                    description="Remove a property",
                    examples=["obsidian:props remove status --from project"],
                ),
            ],
            examples=["obsidian:props", "obsidian:props core"],
        ),
        CommandInfo(
            name="obsidian:templates",
            description="Template management for note templates",
            subcommands=[
                SubcommandInfo(
                    name="list",
                    description="List all templates",
                    examples=["obsidian:templates list"],
                ),
                SubcommandInfo(
                    name="show",
                    description="Show template content",
                    examples=["obsidian:templates show project"],
                ),
                SubcommandInfo(
                    name="create",
                    description="Create a new template",
                    examples=["obsidian:templates create meeting"],
                ),
                SubcommandInfo(
                    name="edit",
                    description="Edit an existing template",
                    examples=["obsidian:templates edit project"],
                ),
                SubcommandInfo(
                    name="delete",
                    description="Delete a template",
                    examples=["obsidian:templates delete custom --yes"],
                ),
                SubcommandInfo(
                    name="apply",
                    description="Apply a template to create a note",
                    examples=["obsidian:templates apply meeting --name 'Weekly Sync'"],
                ),
            ],
            examples=["obsidian:templates", "obsidian:templates list"],
        ),
        CommandInfo(
            name="obsidian:validate",
            description="Vault validation and auto-fix for frontmatter issues",
            subcommands=[],
            examples=[
                "obsidian:validate",
                "obsidian:validate --fix",
                "obsidian:validate --type project",
                "obsidian:validate --path Atlas/",
            ],
        ),
        CommandInfo(
            name="obsidian:help",
            description="Show help for all commands or get details for a specific command",
            subcommands=[],
            examples=[
                "obsidian:help",
                "obsidian:help init",
                "obsidian:help types add",
                "obsidian:help --json",
            ],
        ),
    ]


def display_all_commands() -> None:
    """Display overview of all commands."""
    print(f"\n{COLOR_BOLD}Obsidian Commands{COLOR_RESET}")
    print("=" * 60)
    print()

    for cmd in get_command_registry():
        print(f"  {COLOR_CYAN}{cmd.name}{COLOR_RESET}")
        print(f"    {cmd.description}")
        if cmd.subcommands:
            subcmd_names = [s.name for s in cmd.subcommands]
            print(f"    {COLOR_DIM}Subcommands: {', '.join(subcmd_names)}{COLOR_RESET}")
        print()

    print(f"{COLOR_BOLD}Usage:{COLOR_RESET}")
    print("  obsidian:help              Show this overview")
    print("  obsidian:help <command>    Show command details")
    print("  obsidian:help <cmd> <sub>  Show subcommand details")
    print("  obsidian:help --json       Machine-readable output")
    print()


def display_command_details(cmd: CommandInfo) -> None:
    """Display detailed help for a command."""
    print(f"\n{COLOR_BOLD}{cmd.name}{COLOR_RESET}")
    print("=" * 60)
    print(f"\n{cmd.description}")

    if cmd.subcommands:
        print(f"\n{COLOR_BOLD}Subcommands:{COLOR_RESET}")
        for sub in cmd.subcommands:
            print(f"\n  {COLOR_CYAN}{sub.name}{COLOR_RESET}")
            print(f"    {sub.description}")

    if cmd.examples:
        print(f"\n{COLOR_BOLD}Examples:{COLOR_RESET}")
        for example in cmd.examples:
            print(f"  {COLOR_DIM}{example}{COLOR_RESET}")

    print()


def display_subcommand_details(cmd: CommandInfo, subcmd: SubcommandInfo) -> None:
    """Display detailed help for a subcommand."""
    print(f"\n{COLOR_BOLD}{cmd.name} {subcmd.name}{COLOR_RESET}")
    print("=" * 60)
    print(f"\n{subcmd.description}")

    if subcmd.examples:
        print(f"\n{COLOR_BOLD}Examples:{COLOR_RESET}")
        for example in subcmd.examples:
            print(f"  {COLOR_DIM}{example}{COLOR_RESET}")

    print()


def get_all_commands_json() -> dict:
    """Get all commands as JSON-serializable dict."""
    commands = []
    for cmd in get_command_registry():
        subcmds = []
        for sub in cmd.subcommands:
            subcmds.append(
                {
                    "name": sub.name,
                    "description": sub.description,
                    "examples": sub.examples,
                }
            )
        commands.append(
            {
                "name": cmd.name,
                "description": cmd.description,
                "subcommands": subcmds,
                "examples": cmd.examples,
            }
        )
    return {"commands": commands}


def get_command_json(cmd: CommandInfo) -> dict:
    """Get single command as JSON-serializable dict."""
    subcmds = []
    for sub in cmd.subcommands:
        subcmds.append(
            {
                "name": sub.name,
                "description": sub.description,
                "examples": sub.examples,
            }
        )
    return {
        "name": cmd.name,
        "description": cmd.description,
        "subcommands": subcmds,
        "examples": cmd.examples,
    }


def find_command(name: str) -> CommandInfo | None:
    """Find a command by name."""
    name_lower = name.lower()
    for cmd in get_command_registry():
        # Match full name or short name
        if cmd.name.lower() == name_lower:
            return cmd
        # Match without obsidian: prefix
        short_name = cmd.name.replace("obsidian:", "")
        if short_name.lower() == name_lower:
            return cmd
    return None


def find_subcommand(cmd: CommandInfo, name: str) -> SubcommandInfo | None:
    """Find a subcommand by name."""
    name_lower = name.lower()
    for sub in cmd.subcommands:
        if sub.name.lower() == name_lower:
            return sub
    return None


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian Help - Central help system for all commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                  Show all commands
  %(prog)s init             Show help for init command
  %(prog)s types add        Show help for types add subcommand
  %(prog)s --json           Get all commands as JSON
  %(prog)s types --json     Get types command as JSON
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="Command to get help for (e.g., init, config, types)",
    )
    parser.add_argument(
        "subcommand",
        nargs="?",
        help="Subcommand to get help for (e.g., add, show, list)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    args = parser.parse_args()

    # No command specified - show all
    if args.command is None:
        if args.json:
            print(json.dumps(get_all_commands_json(), indent=2))
        else:
            display_all_commands()
        return 0

    # Find the command
    cmd = find_command(args.command)
    if cmd is None:
        print(f"{COLOR_RED}Unknown command: {args.command}{COLOR_RESET}", file=sys.stderr)
        print("\nAvailable commands:", file=sys.stderr)
        for c in get_command_registry():
            print(f"  {c.name}", file=sys.stderr)
        return 1

    # Subcommand specified
    if args.subcommand:
        subcmd = find_subcommand(cmd, args.subcommand)
        if subcmd is None:
            print(
                f"{COLOR_RED}Unknown subcommand: {args.subcommand}{COLOR_RESET}",
                file=sys.stderr,
            )
            if cmd.subcommands:
                print(f"\nAvailable subcommands for {cmd.name}:", file=sys.stderr)
                for s in cmd.subcommands:
                    print(f"  {s.name}", file=sys.stderr)
            return 1

        if args.json:
            data = {
                "name": f"{cmd.name} {subcmd.name}",
                "description": subcmd.description,
                "examples": subcmd.examples,
            }
            print(json.dumps(data, indent=2))
        else:
            display_subcommand_details(cmd, subcmd)
        return 0

    # Just command, no subcommand
    if args.json:
        print(json.dumps(get_command_json(cmd), indent=2))
    else:
        display_command_details(cmd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
