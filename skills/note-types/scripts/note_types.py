#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Note Types Manager - CRUD operations for Obsidian note types
Manages note type definitions including folders, properties, and templates

Usage:
    uv run scripts/note_types.py --list
    uv run scripts/note_types.py --show map
    uv run scripts/note_types.py --add project
    uv run scripts/note_types.py --edit project
    uv run scripts/note_types.py --remove project
    uv run scripts/note_types.py --wizard
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# Default note types embedded in the script
DEFAULT_NOTE_TYPES = {
    "map": {"folder": "Atlas/Maps/", "properties": ["type", "up", "related"]},
    "dot": {"folder": "Atlas/Dots/", "properties": ["type", "up"]},
    "source": {"folder": "Atlas/Sources/", "properties": ["type", "author", "url"]},
    "project": {"folder": "Efforts/Projects/", "properties": ["type", "status", "due"]},
    "daily": {"folder": "Calendar/Daily/", "properties": ["type", "daily"]},
}


class NoteTypesManager:
    """Manages note type definitions for Obsidian vault"""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize the note types manager

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        self.config_path = self._resolve_config_path(config_path)
        self.note_types = self._load_note_types()

    def _resolve_config_path(self, config_path: str | None) -> Path:
        """Resolve the configuration file path

        Args:
            config_path: Optional path to config file

        Returns:
            Path to the config file
        """
        if config_path:
            return Path(config_path)

        # Look for config in standard locations
        candidates = [
            Path.cwd() / ".claude" / "config" / "note-types.yaml",
            Path.cwd() / ".obsidian" / "note-types.yaml",
            Path.home() / ".config" / "obsidian" / "note-types.yaml",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        # Default to .claude config location
        return Path.cwd() / ".claude" / "config" / "note-types.yaml"

    def _load_note_types(self) -> dict[str, dict[str, Any]]:
        """Load note types from config file or use defaults

        Returns:
            Dictionary of note type definitions
        """
        if not self.config_path.exists():
            print(f"ℹ️  Config file not found: {self.config_path}")
            print("   Using default note types\n")
            return dict(DEFAULT_NOTE_TYPES)

        try:
            with open(self.config_path) as f:
                config: dict[str, Any] = yaml.safe_load(f) or {}
                note_types = config.get("note_types", {})
                if not note_types:
                    print("⚠️  No note types found in config, using defaults\n")
                    return dict(DEFAULT_NOTE_TYPES)
                print(f"✅ Loaded {len(note_types)} note types from {self.config_path}\n")
                return note_types  # type: ignore[return-value]
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            print("   Using default note types\n")
            return dict(DEFAULT_NOTE_TYPES)

    def _save_note_types(self) -> None:
        """Save note types to config file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {"note_types": self.note_types}

        try:
            with open(self.config_path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"✅ Saved note types to {self.config_path}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            sys.exit(1)

    def list_types(self) -> None:
        """List all note types"""
        if not self.note_types:
            print("No note types defined.")
            return

        print(f"📋 Note Types ({len(self.note_types)}):\n")
        for name, definition in sorted(self.note_types.items()):
            folder = definition.get("folder", "")
            properties = definition.get("properties", [])
            template = definition.get("template", "")

            print(f"  {name}")
            print(f"    Folder: {folder}")
            print(f"    Properties: {', '.join(properties)}")
            if template:
                print(f"    Template: {template}")
            print()

    def show_type(self, name: str) -> None:
        """Show details for a specific note type

        Args:
            name: Name of the note type
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            sys.exit(1)

        definition = self.note_types[name]
        print(f"📄 Note Type: {name}\n")
        print(f"  Folder: {definition.get('folder', '')}")
        print(f"  Properties: {', '.join(definition.get('properties', []))}")
        if "template" in definition:
            print(f"  Template: {definition['template']}")
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
            definition = self._interactive_type_definition(name)
        else:
            # Non-interactive mode: use minimal defaults
            definition = {
                "folder": f"{name.capitalize()}/",
                "properties": ["type", "up"],
            }

        self.note_types[name] = definition
        self._save_note_types()
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

        definition = self._interactive_type_definition(name, self.note_types[name])
        self.note_types[name] = definition
        self._save_note_types()
        print(f"✅ Updated note type '{name}'")
        self.show_type(name)

    def remove_type(self, name: str) -> None:
        """Remove a note type

        Args:
            name: Name of the note type
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            sys.exit(1)

        # Confirm deletion
        response = input(f"⚠️  Delete note type '{name}'? (y/N): ").strip().lower()
        if response != "y":
            print("Cancelled")
            return

        del self.note_types[name]
        self._save_note_types()
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

        # Folder
        default_folder = existing.get("folder", f"{name.capitalize()}/")
        folder = input(f"  Folder [{default_folder}]: ").strip()
        folder = folder if folder else default_folder

        # Properties
        default_props = existing.get("properties", ["type", "up"])
        props_str = ", ".join(default_props)
        properties_input = input(f"  Properties (comma-separated) [{props_str}]: ").strip()
        if properties_input:
            properties = [p.strip() for p in properties_input.split(",")]
        else:
            properties = default_props

        # Template
        default_template = existing.get("template", "")
        template = input(f"  Template [{default_template or 'none'}]: ").strip()
        template = template if template else default_template

        # Build definition
        definition: dict[str, Any] = {
            "folder": folder,
            "properties": properties,
        }

        if template:
            definition["template"] = template

        return definition

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
        definition = self._interactive_type_definition(name)

        # Show summary
        print("\n📋 Summary:")
        print(f"  Name: {name}")
        print(f"  Folder: {definition['folder']}")
        print(f"  Properties: {', '.join(definition['properties'])}")
        if "template" in definition:
            print(f"  Template: {definition['template']}")

        # Confirm
        response = input("\n✅ Create this note type? (Y/n): ").strip().lower()
        if response and response != "y":
            print("Cancelled")
            return

        self.note_types[name] = definition
        self._save_note_types()
        print(f"\n✅ Created note type '{name}'")


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage Obsidian note types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list
  %(prog)s --show map
  %(prog)s --add project
  %(prog)s --edit project
  %(prog)s --remove project
  %(prog)s --wizard
        """,
    )

    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--list", action="store_true", help="List all note types")
    parser.add_argument("--show", metavar="NAME", help="Show details for a note type")
    parser.add_argument("--add", metavar="NAME", help="Add a new note type")
    parser.add_argument("--edit", metavar="NAME", help="Edit an existing note type")
    parser.add_argument("--remove", metavar="NAME", help="Remove a note type")
    parser.add_argument("--wizard", action="store_true", help="Interactive wizard mode")
    parser.add_argument(
        "--non-interactive", action="store_true", help="Non-interactive mode for --add"
    )

    args = parser.parse_args()

    # Check that at least one action is specified
    actions = [args.list, args.show, args.add, args.edit, args.remove, args.wizard]
    if not any(actions):
        parser.print_help()
        sys.exit(1)

    manager = NoteTypesManager(args.config)

    if args.list:
        manager.list_types()
    elif args.show:
        manager.show_type(args.show)
    elif args.add:
        manager.add_type(args.add, interactive=not args.non_interactive)
    elif args.edit:
        manager.edit_type(args.edit)
    elif args.remove:
        manager.remove_type(args.remove)
    elif args.wizard:
        manager.wizard()


if __name__ == "__main__":
    main()
