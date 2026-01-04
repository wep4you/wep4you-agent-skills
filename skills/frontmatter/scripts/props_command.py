#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Props Command - Property management for Obsidian notes

Replaces the deprecated /frontmatter command with obsidian:props:
- obsidian:props              List core properties
- obsidian:props core         List core properties (explicit)
- obsidian:props core add     Add core property
- obsidian:props core remove  Remove core property
- obsidian:props type <name>  List properties for note type
- obsidian:props required     List all required properties
- obsidian:props types        List all note types with properties

Usage:
    uv run props_command.py --vault /path/to/vault
    uv run props_command.py --vault /path/to/vault core
    uv run props_command.py --vault /path/to/vault type project
    uv run props_command.py --vault /path/to/vault required
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

# ANSI colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"

# Default core properties with metadata
DEFAULT_CORE_PROPERTIES = {
    "type": {"required": True, "type": "string", "description": "Note type classification"},
    "up": {"required": False, "type": "wikilink", "description": "Parent note in hierarchy"},
    "created": {
        "required": True,
        "type": "date",
        "format": "YYYY-MM-DD",
        "description": "Creation date",
    },
    "daily": {"required": False, "type": "wikilink", "description": "Associated daily note"},
    "tags": {"required": False, "type": "list[string]", "description": "Topic tags"},
    "collection": {"required": False, "type": "wikilink", "description": "Collection link"},
    "related": {"required": False, "type": "list[wikilink]", "description": "Related notes"},
}


class PropsManager:
    """Manages frontmatter property definitions."""

    def __init__(self, vault_path: str | None = None) -> None:
        """Initialize props manager.

        Args:
            vault_path: Path to vault (default: current directory)
        """
        self.vault_path = Path(vault_path) if vault_path else Path.cwd()
        self.settings_path = self.vault_path / ".claude" / "settings.yaml"
        self.settings: dict = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from settings.yaml."""
        if not self.settings_path.exists():
            print(f"{COLOR_YELLOW}No settings.yaml found. Using defaults.{COLOR_RESET}")
            self.settings = {
                "core_properties": list(DEFAULT_CORE_PROPERTIES.keys()),
                "note_types": {},
            }
            return

        with self.settings_path.open() as f:
            self.settings = yaml.safe_load(f) or {}

    def _save_settings(self) -> None:
        """Save settings to settings.yaml."""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_path.open("w") as f:
            yaml.safe_dump(self.settings, f, default_flow_style=False, sort_keys=False)
        print(f"{COLOR_GREEN}Saved to: {self.settings_path}{COLOR_RESET}")

    def get_core_properties(self) -> list[str]:
        """Get list of core properties.

        Returns:
            List of core property names
        """
        core = self.settings.get("core_properties", {})
        if isinstance(core, dict):
            return list(core.get("all", DEFAULT_CORE_PROPERTIES.keys()))
        elif isinstance(core, list):
            return core
        return list(DEFAULT_CORE_PROPERTIES.keys())

    def get_property_info(self, name: str) -> dict:
        """Get metadata for a property.

        Args:
            name: Property name

        Returns:
            Property metadata dict
        """
        return DEFAULT_CORE_PROPERTIES.get(
            name,
            {"required": False, "type": "string", "description": "Custom property"},
        )


def cmd_core_list(manager: PropsManager, output_format: str = "text") -> int:
    """List core properties.

    Args:
        manager: PropsManager instance
        output_format: Output format

    Returns:
        Exit code
    """
    props = manager.get_core_properties()

    if output_format == "json":
        data = {name: manager.get_property_info(name) for name in props}
        print(json.dumps(data, indent=2))
        return 0

    print(f"\n{COLOR_BOLD}Core Properties{COLOR_RESET}")
    print("=" * 50)

    for name in props:
        info = manager.get_property_info(name)
        required = f"{COLOR_GREEN}required{COLOR_RESET}" if info.get("required") else "optional"
        prop_type = info.get("type", "string")
        desc = info.get("description", "")

        print(f"\n  {COLOR_CYAN}{name}{COLOR_RESET} ({prop_type})")
        print(f"    {required} - {desc}")
        if "format" in info:
            print(f"    Format: {info['format']}")

    print()
    return 0


def cmd_core_add(manager: PropsManager, name: str, prop_type: str = "string") -> int:
    """Add a core property.

    Args:
        manager: PropsManager instance
        name: Property name
        prop_type: Property type

    Returns:
        Exit code
    """
    props = manager.get_core_properties()

    if name in props:
        print(f"{COLOR_YELLOW}Property '{name}' already exists.{COLOR_RESET}")
        return 0

    props.append(name)
    manager.settings["core_properties"] = props
    manager._save_settings()

    print(f"{COLOR_GREEN}Added core property: {name} ({prop_type}){COLOR_RESET}")
    return 0


def cmd_core_remove(manager: PropsManager, name: str) -> int:
    """Remove a core property.

    Args:
        manager: PropsManager instance
        name: Property name

    Returns:
        Exit code
    """
    props = manager.get_core_properties()

    if name not in props:
        print(f"{COLOR_RED}Property '{name}' not found.{COLOR_RESET}")
        return 1

    # Prevent removing essential properties
    essential = ["type", "created"]
    if name in essential:
        print(f"{COLOR_RED}Cannot remove essential property: {name}{COLOR_RESET}")
        return 1

    props.remove(name)
    manager.settings["core_properties"] = props
    manager._save_settings()

    print(f"{COLOR_GREEN}Removed core property: {name}{COLOR_RESET}")
    return 0


def cmd_type_props(manager: PropsManager, type_name: str, output_format: str = "text") -> int:
    """List properties for a note type.

    Args:
        manager: PropsManager instance
        type_name: Note type name
        output_format: Output format

    Returns:
        Exit code
    """
    note_types = manager.settings.get("note_types", {})

    if type_name not in note_types:
        print(f"{COLOR_RED}Note type '{type_name}' not found.{COLOR_RESET}")
        available = list(note_types.keys())
        if available:
            print(f"Available types: {', '.join(available)}")
        return 1

    config = note_types[type_name]
    core_props = manager.get_core_properties()

    # Get additional properties
    props = config.get("properties", {})
    if isinstance(props, dict):
        additional_required = props.get("additional_required", [])
        optional = props.get("optional", [])
    else:
        additional_required = props if isinstance(props, list) else []
        optional = []

    if output_format == "json":
        data = {
            "type": type_name,
            "core_properties": core_props,
            "additional_required": additional_required,
            "optional": optional,
            "all_required": core_props + additional_required,
        }
        print(json.dumps(data, indent=2))
        return 0

    print(f"\n{COLOR_BOLD}Properties for '{type_name}'{COLOR_RESET}")
    print("=" * 50)

    print(f"\n{COLOR_CYAN}Core Properties (inherited):{COLOR_RESET}")
    for prop in core_props:
        print(f"  - {prop}")

    if additional_required:
        print(f"\n{COLOR_CYAN}Additional Required:{COLOR_RESET}")
        for prop in additional_required:
            print(f"  - {prop}")

    if optional:
        print(f"\n{COLOR_CYAN}Optional:{COLOR_RESET}")
        for prop in optional:
            print(f"  - {prop}")

    print()
    return 0


def cmd_required(
    manager: PropsManager,
    type_name: str | None = None,
    output_format: str = "text",
) -> int:
    """List all required properties.

    Args:
        manager: PropsManager instance
        type_name: Optional note type to filter by
        output_format: Output format

    Returns:
        Exit code
    """
    core_props = manager.get_core_properties()
    core_required = [p for p in core_props if manager.get_property_info(p).get("required", False)]

    if type_name:
        note_types = manager.settings.get("note_types", {})
        if type_name not in note_types:
            print(f"{COLOR_RED}Note type '{type_name}' not found.{COLOR_RESET}")
            return 1

        config = note_types[type_name]
        props = config.get("properties", {})
        additional = props.get("additional_required", []) if isinstance(props, dict) else []
        all_required = core_required + additional

        if output_format == "json":
            print(json.dumps({"type": type_name, "required": all_required}))
            return 0

        print(f"\n{COLOR_BOLD}Required Properties for '{type_name}'{COLOR_RESET}")
        print("-" * 40)
        for prop in all_required:
            print(f"  - {prop}")
        print()
        return 0

    if output_format == "json":
        print(json.dumps({"required": core_required}))
        return 0

    print(f"\n{COLOR_BOLD}Required Core Properties{COLOR_RESET}")
    print("-" * 40)
    for prop in core_required:
        info = manager.get_property_info(prop)
        print(f"  - {prop}: {info.get('description', '')}")
    print()
    return 0


def cmd_types_list(manager: PropsManager, output_format: str = "text") -> int:
    """List all note types with their properties.

    Args:
        manager: PropsManager instance
        output_format: Output format

    Returns:
        Exit code
    """
    note_types = manager.settings.get("note_types", {})

    if not note_types:
        print(f"{COLOR_YELLOW}No note types defined.{COLOR_RESET}")
        return 0

    if output_format == "json":
        data = {}
        for name, config in note_types.items():
            props = config.get("properties", {})
            add_req = props.get("additional_required", []) if isinstance(props, dict) else []
            optional = props.get("optional", []) if isinstance(props, dict) else []
            data[name] = {
                "additional_required": add_req,
                "optional": optional,
            }
        print(json.dumps(data, indent=2))
        return 0

    print(f"\n{COLOR_BOLD}Note Type Properties{COLOR_RESET}")
    print("=" * 50)

    for name, config in sorted(note_types.items()):
        props = config.get("properties", {})
        if isinstance(props, dict):
            req = props.get("additional_required", [])
            opt = props.get("optional", [])
        else:
            req = props if isinstance(props, list) else []
            opt = []

        print(f"\n  {COLOR_CYAN}{name}{COLOR_RESET}")
        if req:
            print(f"    Required: {', '.join(req)}")
        if opt:
            print(f"    Optional: {', '.join(opt)}")
        if not req and not opt:
            print(f"    {COLOR_DIM}(core properties only){COLOR_RESET}")

    print()
    return 0


def show_deprecation_warning() -> None:
    """Show deprecation warning for old command."""
    warning = f"""
{COLOR_YELLOW}{COLOR_BOLD}DEPRECATION WARNING{COLOR_RESET}
{COLOR_YELLOW}The '/frontmatter' command is deprecated and will be removed in v2.0.0.{COLOR_RESET}
{COLOR_CYAN}Use 'obsidian:props' instead.{COLOR_RESET}
"""
    print(warning, file=sys.stderr)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian Property Management (obsidian:props)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  (none)           List core properties (same as 'core')
  core             List core properties
  core add <name>  Add a core property
  core remove <name> Remove a core property
  type <name>      List properties for a note type
  required         List all required properties
  types            List all note types with properties

Examples:
  %(prog)s --vault .
  %(prog)s --vault . core
  %(prog)s --vault . type project
  %(prog)s --vault . required --type daily
  %(prog)s --vault . types --format json
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
        help=argparse.SUPPRESS,
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # core
    core_parser = subparsers.add_parser("core", help="Core property management")
    core_sub = core_parser.add_subparsers(dest="core_action")

    add_parser = core_sub.add_parser("add", help="Add core property")
    add_parser.add_argument("name", help="Property name")
    add_parser.add_argument("--type", default="string", help="Property type")

    remove_parser = core_sub.add_parser("remove", help="Remove core property")
    remove_parser.add_argument("name", help="Property name")

    # type
    type_parser = subparsers.add_parser("type", help="Type-specific properties")
    type_parser.add_argument("name", help="Note type name")

    # required
    required_parser = subparsers.add_parser("required", help="Required properties")
    required_parser.add_argument("--type", dest="type_name", help="Filter by note type")

    # types
    subparsers.add_parser("types", help="List all types with properties")

    args = parser.parse_args()

    # Show deprecation warning if triggered
    if args.deprecated_warning:
        show_deprecation_warning()

    # Initialize manager
    manager = PropsManager(args.vault)

    # Route to handler
    if args.command is None or args.command == "core":
        if hasattr(args, "core_action") and args.core_action == "add":
            return cmd_core_add(manager, args.name, args.type)
        elif hasattr(args, "core_action") and args.core_action == "remove":
            return cmd_core_remove(manager, args.name)
        else:
            return cmd_core_list(manager, args.format)
    elif args.command == "type":
        return cmd_type_props(manager, args.name, args.format)
    elif args.command == "required":
        return cmd_required(manager, getattr(args, "type_name", None), args.format)
    elif args.command == "types":
        return cmd_types_list(manager, args.format)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
