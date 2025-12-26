#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Note Types Manager - CRUD operations for Obsidian note types

Manages note type definitions by reading from and writing to .claude/settings.yaml.
This integrates with the init skill and settings_loader for a unified configuration.

Usage:
    uv run scripts/note_types.py --list
    uv run scripts/note_types.py --show map
    uv run scripts/note_types.py --add blog
    uv run scripts/note_types.py --edit project
    uv run scripts/note_types.py --remove custom
    uv run scripts/note_types.py --wizard
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# Settings file path (relative to vault root)
SETTINGS_FILE = ".claude/settings.yaml"


class NoteTypesManager:
    """Manages note type definitions in .claude/settings.yaml"""

    def __init__(self, vault_path: str | None = None) -> None:
        """Initialize the note types manager

        Args:
            vault_path: Path to vault root. If None, uses current directory.
        """
        self.vault_path = Path(vault_path) if vault_path else Path.cwd()
        self.settings_path = self.vault_path / SETTINGS_FILE
        self.settings: dict[str, Any] = {}
        self.note_types: dict[str, dict[str, Any]] = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from .claude/settings.yaml"""
        if not self.settings_path.exists():
            print(f"❌ Settings file not found: {self.settings_path}")
            print("   Run 'obsidian:init' first to initialize your vault.")
            sys.exit(1)

        try:
            with open(self.settings_path, encoding="utf-8") as f:
                self.settings = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"❌ Error parsing settings.yaml: {e}")
            sys.exit(1)

        # Extract note_types section
        self.note_types = self.settings.get("note_types", {})
        if not self.note_types:
            print("⚠️  No note types found in settings.yaml")
            print("   The vault may not be properly initialized.")
        else:
            methodology = self.settings.get("methodology", "unknown")
            print(f"✅ Loaded {len(self.note_types)} note types ({methodology} methodology)\n")

    def _save_settings(self) -> None:
        """Save settings back to .claude/settings.yaml"""
        self.settings["note_types"] = self.note_types

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    self.settings,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            print(f"✅ Saved settings to {self.settings_path}")
        except OSError as e:
            print(f"❌ Error saving settings: {e}")
            sys.exit(1)

    def _format_properties(self, nt_config: dict[str, Any]) -> list[str]:
        """Extract all properties from note type config

        Args:
            nt_config: Note type configuration dict

        Returns:
            List of all property names
        """
        props = nt_config.get("properties", {})
        if isinstance(props, list):
            return props

        # Handle structured properties format
        all_props: list[str] = []
        if "additional_required" in props:
            all_props.extend(props.get("additional_required", []))
        if "optional" in props:
            all_props.extend(props.get("optional", []))
        return all_props

    def list_types(self) -> None:
        """List all note types"""
        if not self.note_types:
            print("No note types defined.")
            return

        core_props = self.settings.get("core_properties", {})
        if isinstance(core_props, dict):
            core_props = core_props.get("all", [])

        print(f"📋 Note Types ({len(self.note_types)}):\n")
        print(f"   Core properties: {', '.join(core_props)}\n")

        for name, config in sorted(self.note_types.items()):
            description = config.get("description", "")
            folder_hints = config.get("folder_hints", [])
            props = self._format_properties(config)
            icon = config.get("icon", "")

            print(f"  {icon} {name}")
            if description:
                print(f"    Description: {description}")
            print(f"    Folders: {', '.join(folder_hints)}")
            if props:
                print(f"    Additional properties: {', '.join(props)}")
            print()

    def show_type(self, name: str) -> None:
        """Show details for a specific note type

        Args:
            name: Name of the note type
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            print(f"   Available: {', '.join(self.note_types.keys())}")
            sys.exit(1)

        config = self.note_types[name]
        icon = config.get("icon", "📄")

        print(f"{icon} Note Type: {name}\n")
        print(f"  Description: {config.get('description', '-')}")
        print(f"  Folders: {', '.join(config.get('folder_hints', []))}")

        props = config.get("properties", {})
        if isinstance(props, dict):
            req = props.get("additional_required", [])
            opt = props.get("optional", [])
            if req:
                print(f"  Required properties: {', '.join(req)}")
            if opt:
                print(f"  Optional properties: {', '.join(opt)}")
        elif isinstance(props, list):
            print(f"  Properties: {', '.join(props)}")

        validation = config.get("validation", {})
        if validation:
            print(f"  Validation: {validation}")

        if "template" in config:
            print(f"  Template: {config['template']}")
        print()

    def add_type(self, name: str, interactive: bool = True) -> None:
        """Add a new note type

        Args:
            name: Name of the note type
            interactive: Whether to prompt for details interactively
        """
        if name in self.note_types:
            print(f"❌ Note type '{name}' already exists")
            print("   Use --edit to modify it")
            sys.exit(1)

        if interactive:
            config = self._interactive_type_definition(name)
        else:
            # Non-interactive mode: use minimal defaults
            config = {
                "description": f"{name.capitalize()} notes",
                "folder_hints": [f"{name.capitalize()}/"],
                "properties": {
                    "additional_required": [],
                    "optional": [],
                },
                "validation": {
                    "allow_empty_up": False,
                },
                "icon": "file",
            }

        self.note_types[name] = config
        self._save_settings()
        print(f"✅ Added note type '{name}'")
        self.show_type(name)

    def edit_type(self, name: str) -> None:
        """Edit an existing note type

        Args:
            name: Name of the note type
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            sys.exit(1)

        print(f"📝 Editing note type: {name}\n")
        self.show_type(name)

        config = self._interactive_type_definition(name, self.note_types[name])
        self.note_types[name] = config
        self._save_settings()
        print(f"✅ Updated note type '{name}'")
        self.show_type(name)

    def remove_type(self, name: str, skip_confirm: bool = False) -> None:
        """Remove a note type

        Args:
            name: Name of the note type
            skip_confirm: Skip confirmation prompt (for non-interactive use)
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            sys.exit(1)

        # Confirm deletion unless skipped
        if not skip_confirm:
            response = input(f"⚠️  Delete note type '{name}'? (y/N): ").strip().lower()
            if response != "y":
                print("Cancelled")
                return

        del self.note_types[name]
        self._save_settings()
        print(f"✅ Removed note type '{name}'")

    def _interactive_type_definition(
        self, name: str, existing: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Interactively build a note type definition

        Args:
            name: Name of the note type
            existing: Existing definition to use as defaults

        Returns:
            Note type definition dictionary
        """
        existing = existing or {}

        print(f"Define note type: {name}")
        print("(Press Enter to keep current value or use default)\n")

        # Description
        default_desc = existing.get("description", f"{name.capitalize()} notes")
        description = input(f"  Description [{default_desc}]: ").strip()
        description = description if description else default_desc

        # Folder hints
        default_folders = existing.get("folder_hints", [f"{name.capitalize()}/"])
        folders_str = ", ".join(default_folders)
        folders_input = input(f"  Folders (comma-separated) [{folders_str}]: ").strip()
        if folders_input:
            folder_hints = [f.strip() for f in folders_input.split(",")]
        else:
            folder_hints = default_folders

        # Properties
        existing_props = existing.get("properties", {})
        if isinstance(existing_props, dict):
            default_req = existing_props.get("additional_required", [])
            default_opt = existing_props.get("optional", [])
        else:
            default_req = existing_props if isinstance(existing_props, list) else []
            default_opt = []

        req_str = ", ".join(default_req) if default_req else "none"
        req_input = input(f"  Required properties [{req_str}]: ").strip()
        if req_input and req_input.lower() != "none":
            additional_required = [p.strip() for p in req_input.split(",")]
        elif req_input.lower() == "none":
            additional_required = []
        else:
            additional_required = default_req

        opt_str = ", ".join(default_opt) if default_opt else "none"
        opt_input = input(f"  Optional properties [{opt_str}]: ").strip()
        if opt_input and opt_input.lower() != "none":
            optional = [p.strip() for p in opt_input.split(",")]
        elif opt_input.lower() == "none":
            optional = []
        else:
            optional = default_opt

        # Icon
        default_icon = existing.get("icon", "file")
        icon = input(f"  Icon [{default_icon}]: ").strip()
        icon = icon if icon else default_icon

        # Build config in settings.yaml format
        config: dict[str, Any] = {
            "description": description,
            "folder_hints": folder_hints,
            "properties": {
                "additional_required": additional_required,
                "optional": optional,
            },
            "validation": existing.get("validation", {"allow_empty_up": False}),
            "icon": icon,
        }

        return config

    def wizard(self) -> None:
        """Interactive wizard to create a new note type"""
        print("🧙 Note Type Wizard\n")
        print("Let's create a new note type for your Obsidian vault.\n")

        # Get name
        while True:
            name = input("Note type name: ").strip().lower()
            if not name:
                print("❌ Name cannot be empty")
                continue
            if name in self.note_types:
                print(f"❌ Note type '{name}' already exists")
                continue
            break

        # Build definition interactively
        config = self._interactive_type_definition(name)

        # Show summary
        print("\n📋 Summary:")
        print(f"  Name: {name}")
        print(f"  Description: {config['description']}")
        print(f"  Folders: {', '.join(config['folder_hints'])}")
        req = config["properties"]["additional_required"]
        opt = config["properties"]["optional"]
        if req:
            print(f"  Required: {', '.join(req)}")
        if opt:
            print(f"  Optional: {', '.join(opt)}")
        print(f"  Icon: {config['icon']}")

        # Confirm
        response = input("\n✅ Create this note type? (Y/n): ").strip().lower()
        if response and response != "y":
            print("Cancelled")
            return

        self.note_types[name] = config
        self._save_settings()
        print(f"\n✅ Created note type '{name}'")


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage Obsidian note types in settings.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list
  %(prog)s --show map
  %(prog)s --add blog
  %(prog)s --edit project
  %(prog)s --remove custom
  %(prog)s --wizard
        """,
    )

    parser.add_argument("--vault", help="Path to vault root (default: current directory)")
    parser.add_argument("--list", action="store_true", help="List all note types")
    parser.add_argument("--show", metavar="NAME", help="Show details for a note type")
    parser.add_argument("--add", metavar="NAME", help="Add a new note type")
    parser.add_argument("--edit", metavar="NAME", help="Edit an existing note type")
    parser.add_argument("--remove", metavar="NAME", help="Remove a note type")
    parser.add_argument("--wizard", action="store_true", help="Interactive wizard mode")
    parser.add_argument(
        "--non-interactive", action="store_true", help="Non-interactive mode for --add"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompts (for --remove)"
    )

    args = parser.parse_args()

    # Check that at least one action is specified
    actions = [args.list, args.show, args.add, args.edit, args.remove, args.wizard]
    if not any(actions):
        parser.print_help()
        sys.exit(1)

    manager = NoteTypesManager(args.vault)

    if args.list:
        manager.list_types()
    elif args.show:
        manager.show_type(args.show)
    elif args.add:
        manager.add_type(args.add, interactive=not args.non_interactive)
    elif args.edit:
        manager.edit_type(args.edit)
    elif args.remove:
        manager.remove_type(args.remove, skip_confirm=args.yes)
    elif args.wizard:
        manager.wizard()


if __name__ == "__main__":
    main()
