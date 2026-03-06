#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Note Types Manager - CRUD operations for Obsidian note types.

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

# Add project root to path for imports
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.core.settings import settings_exist  # noqa: E402

# Settings file path (relative to vault root)
SETTINGS_FILE = ".claude/settings.yaml"


class NoteTypesManager:
    """Manages note type definitions in .claude/settings.yaml.

    This class provides pure CRUD operations for note types:
    - list_types(): List all note types
    - get_type(name): Get a specific note type
    - add_type(name, config): Add a new note type
    - update_type(name, config): Update an existing note type
    - delete_type(name): Delete a note type

    Vault structure operations (folder creation, templates, MOCs) are
    handled by VaultStructureManager in note_type_wizard.py.
    """

    def __init__(self, vault_path: str | None = None) -> None:
        """Initialize the note types manager.

        Args:
            vault_path: Path to vault root. If None, uses current directory.
        """
        self.vault_path = Path(vault_path) if vault_path else Path.cwd()
        self.settings_path = self.vault_path / SETTINGS_FILE
        self.settings: dict[str, Any] = {}
        self.note_types: dict[str, dict[str, Any]] = {}
        self._load_settings()

        # Read folder paths from folder_structure
        folder_structure = self.settings.get("folder_structure", {})
        templates_path = folder_structure.get("templates", "x/templates/").rstrip("/")
        bases_path = folder_structure.get("bases", "x/bases/").rstrip("/")

        self.system_prefix = templates_path.split("/")[0] if "/" in templates_path else "x"
        self.templates_folder = self.vault_path / templates_path
        self.bases_folder = self.vault_path / bases_path

    def _load_settings(self) -> None:
        """Load settings from .claude/settings.yaml."""
        if not settings_exist(self.vault_path):
            print(f"Settings file not found: {self.settings_path}")
            print("Run 'obsidian:init' first to initialize your vault.")
            sys.exit(1)

        try:
            with open(self.settings_path, encoding="utf-8") as f:
                self.settings = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error parsing settings.yaml: {e}")
            sys.exit(1)

        self.note_types = self.settings.get("note_types", {})
        if not self.note_types:
            print("No note types found in settings.yaml", file=sys.stderr)
            print("The vault may not be properly initialized.", file=sys.stderr)
        else:
            methodology = self.settings.get("methodology", "unknown")
            msg = f"Loaded {len(self.note_types)} note types ({methodology} methodology)\n"
            print(msg, file=sys.stderr)

    def _save_settings(self) -> None:
        """Save settings back to .claude/settings.yaml."""
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
            print(f"Saved settings to {self.settings_path}")
        except OSError as e:
            print(f"Error saving settings: {e}")
            sys.exit(1)

    def get_core_properties(self) -> list[str]:
        """Get list of core properties from settings.

        Returns:
            List of core property names
        """
        core_props = self.settings.get("core_properties", {})
        if isinstance(core_props, dict):
            result = core_props.get("all", ["type", "up", "created"])
            return list(result) if result else ["type", "up", "created"]
        elif isinstance(core_props, list):
            return core_props
        return ["type", "up", "created"]

    def _format_properties(self, nt_config: dict[str, Any]) -> list[str]:
        """Extract all properties from note type config.

        Args:
            nt_config: Note type configuration dict

        Returns:
            List of all property names
        """
        props = nt_config.get("properties", {})
        if isinstance(props, list):
            return props

        all_props: list[str] = []
        if "additional_required" in props:
            all_props.extend(props.get("additional_required", []))
        if "optional" in props:
            all_props.extend(props.get("optional", []))
        return all_props

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def list_types(self) -> dict[str, dict[str, Any]]:
        """List all note types.

        Returns:
            Dictionary of all note types
        """
        return self.note_types.copy()

    def get_type(self, name: str) -> dict[str, Any] | None:
        """Get a specific note type configuration.

        Args:
            name: Name of the note type

        Returns:
            Note type configuration or None if not found
        """
        return self.note_types.get(name)

    def add_type(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Add a new note type.

        Args:
            name: Name of the note type
            config: Note type configuration

        Returns:
            The added configuration

        Raises:
            ValueError: If note type already exists
        """
        if name in self.note_types:
            raise ValueError(f"Note type '{name}' already exists")

        normalized = self._normalize_config(name, config)
        self.note_types[name] = normalized
        self._save_settings()
        return normalized

    def update_type(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Update an existing note type.

        Args:
            name: Name of the note type
            config: Updated configuration (partial or full)

        Returns:
            The updated configuration

        Raises:
            ValueError: If note type doesn't exist
        """
        if name not in self.note_types:
            raise ValueError(f"Note type '{name}' not found")

        existing = self.note_types[name].copy()
        merged = self._merge_config(existing, config)
        self.note_types[name] = merged
        self._save_settings()
        return merged

    def delete_type(self, name: str) -> dict[str, Any]:
        """Delete a note type.

        Args:
            name: Name of the note type

        Returns:
            The deleted configuration

        Raises:
            ValueError: If note type doesn't exist
        """
        if name not in self.note_types:
            raise ValueError(f"Note type '{name}' not found")

        config = self.note_types.pop(name)
        self._save_settings()
        return config

    # =========================================================================
    # Config Normalization
    # =========================================================================

    def _normalize_config(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Normalize a config dict to the expected structure.

        Args:
            name: Note type name (for defaults)
            config: Input config dict

        Returns:
            Normalized config dict
        """
        normalized: dict[str, Any] = {
            "description": config.get("description", f"{name.capitalize()} notes"),
            "folder_hints": [],
            "properties": {
                "additional_required": [],
                "optional": [],
            },
            "validation": {
                "allow_empty_up": config.get("allow_empty_up", False),
            },
            "icon": config.get("icon", "file"),
        }

        # Handle folder/folder_hints
        if "folder" in config:
            folder = config["folder"]
            normalized["folder_hints"] = [folder if folder.endswith("/") else f"{folder}/"]
        elif "folder_hints" in config:
            normalized["folder_hints"] = config["folder_hints"]
        else:
            normalized["folder_hints"] = [f"{name.capitalize()}/"]

        # Handle properties
        if "required_props" in config or "required" in config:
            props = config.get("required_props", config.get("required", []))
            if isinstance(props, str):
                props = [p.strip() for p in props.split(",")]
            normalized["properties"]["additional_required"] = props

        if "optional_props" in config or "optional" in config:
            props = config.get("optional_props", config.get("optional", []))
            if isinstance(props, str):
                props = [p.strip() for p in props.split(",")]
            normalized["properties"]["optional"] = props

        # Handle nested properties format
        if "properties" in config and isinstance(config["properties"], dict):
            if "additional_required" in config["properties"]:
                normalized["properties"]["additional_required"] = config["properties"][
                    "additional_required"
                ]
            if "optional" in config["properties"]:
                normalized["properties"]["optional"] = config["properties"]["optional"]

        return normalized

    def _merge_config(self, existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        """Merge updates into existing config.

        Args:
            existing: Existing configuration
            updates: Updates to apply

        Returns:
            Merged configuration
        """
        result = existing.copy()

        if "description" in updates:
            result["description"] = updates["description"]

        if "folder" in updates or "folder_hints" in updates:
            folder = updates.get("folder", updates.get("folder_hints", [None])[0])
            if folder:
                result["folder_hints"] = [folder if folder.endswith("/") else f"{folder}/"]

        if "icon" in updates:
            result["icon"] = updates["icon"]

        if "allow_empty_up" in updates:
            result.setdefault("validation", {})["allow_empty_up"] = updates["allow_empty_up"]

        # Handle properties updates
        if any(
            k in updates
            for k in ["required_props", "required", "optional_props", "optional", "properties"]
        ):
            props = result.get("properties", {})
            if not isinstance(props, dict):
                props = {"additional_required": [], "optional": []}

            if "required_props" in updates or "required" in updates:
                req = updates.get("required_props", updates.get("required", []))
                if isinstance(req, str):
                    req = [p.strip() for p in req.split(",")]
                props["additional_required"] = req

            if "optional_props" in updates or "optional" in updates:
                opt = updates.get("optional_props", updates.get("optional", []))
                if isinstance(opt, str):
                    opt = [p.strip() for p in opt.split(",")]
                props["optional"] = opt

            if "properties" in updates and isinstance(updates["properties"], dict):
                if "additional_required" in updates["properties"]:
                    props["additional_required"] = updates["properties"]["additional_required"]
                if "optional" in updates["properties"]:
                    props["optional"] = updates["properties"]["optional"]

            result["properties"] = props

        return result


# =============================================================================
# CLI Display Functions
# =============================================================================


def display_type_list(manager: NoteTypesManager) -> None:
    """Display list of all note types."""
    note_types = manager.list_types()
    if not note_types:
        print("No note types defined.")
        return

    core_props = manager.get_core_properties()

    print(f"Note Types ({len(note_types)}):\n")
    print(f"   Core properties: {', '.join(core_props)}\n")

    for name, config in sorted(note_types.items()):
        description = config.get("description", "")
        folder_hints = config.get("folder_hints", [])
        props = manager._format_properties(config)
        icon = config.get("icon", "")

        print(f"  {icon} {name}")
        if description:
            print(f"    Description: {description}")
        print(f"    Folders: {', '.join(folder_hints)}")
        if props:
            print(f"    Additional properties: {', '.join(props)}")
        print()


def display_type_details(manager: NoteTypesManager, name: str) -> None:
    """Display details for a specific note type."""
    config = manager.get_type(name)
    if not config:
        print(f"Note type '{name}' not found")
        print(f"Available: {', '.join(manager.list_types().keys())}")
        sys.exit(1)

    icon = config.get("icon", "file")

    print(f"{icon} Note Type: {name}\n")
    print(f"  Description: {config.get('description', '-')}")
    print(f"  Folders: {', '.join(config.get('folder_hints', []))}")
    print(f"  Core properties: {', '.join(manager.get_core_properties())}")

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


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage Obsidian note types in settings.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES

List & Show:
  %(prog)s --list                           # List all note types
  %(prog)s --show project                   # Show details for 'project'

Add with JSON config (RECOMMENDED):
  %(prog)s --add meeting --config '{
    "description": "Meeting notes",
    "folder": "Meetings/",
    "required_props": ["attendees", "date"],
    "optional_props": ["action_items"],
    "icon": "calendar"
  }'

Add with minimal defaults:
  %(prog)s --add blog --non-interactive     # Creates Blog/ with defaults

Edit with JSON config (RECOMMENDED):
  %(prog)s --edit meeting --config '{
    "description": "Updated description",
    "required_props": ["attendees", "date", "location"]
  }'

Edit with individual parameters:
  %(prog)s --edit project --non-interactive --description "New desc" --icon "rocket"
  %(prog)s --edit project --non-interactive --required-props "status,priority"
  %(prog)s --edit project --non-interactive --folder "NewFolder/"

Remove:
  %(prog)s --remove meeting --yes           # Remove without confirmation

CONFIG JSON FIELDS
  description     : Note type description (string)
  folder          : Folder path, e.g. "Meetings/" (string)
  required_props  : Required properties (array or comma-separated string)
  optional_props  : Optional properties (array or comma-separated string)
  icon            : Lucide icon name, e.g. "calendar" (string)
  allow_empty_up  : Allow empty up links (boolean, default: false)
        """,
    )

    parser.add_argument("--vault", help="Path to vault root (default: current directory)")
    parser.add_argument("--list", action="store_true", help="List all note types")
    parser.add_argument("--show", metavar="NAME", help="Show details for a note type")
    parser.add_argument("--add", metavar="NAME", help="Add a new note type")
    parser.add_argument("--edit", metavar="NAME", help="Edit an existing note type")
    parser.add_argument("--remove", metavar="NAME", help="Remove a note type")
    parser.add_argument("--wizard", action="store_true", help="Interactive wizard (terminal only)")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use minimal defaults (for --add) or individual params (for --edit)",
    )
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation (for --remove)")
    parser.add_argument(
        "--config",
        metavar="JSON",
        help="Full JSON config for --add/--edit (RECOMMENDED)",
    )
    # Individual edit parameters
    parser.add_argument("--description", help="Note type description")
    parser.add_argument("--folder", help="Folder path (e.g., Meetings/)")
    parser.add_argument(
        "--required-props", metavar="PROPS", help="Comma-separated required properties"
    )
    parser.add_argument(
        "--optional-props", metavar="PROPS", help="Comma-separated optional properties"
    )
    parser.add_argument("--icon", help="Lucide icon name (e.g., calendar, file, target)")

    args = parser.parse_args()

    actions = [args.list, args.show, args.add, args.edit, args.remove, args.wizard]
    if not any(actions):
        parser.print_help()
        sys.exit(1)

    manager = NoteTypesManager(args.vault)

    if args.list:
        display_type_list(manager)
    elif args.show:
        display_type_details(manager, args.show)
    elif args.add:
        from note_type_wizard import handle_add

        handle_add(manager, args.add, args.config, args.non_interactive)
        display_type_details(manager, args.add)
    elif args.edit:
        print(f"Editing note type: {args.edit}\n")
        display_type_details(manager, args.edit)

        from note_type_wizard import handle_edit

        handle_edit(manager, args.edit, args.config, args.non_interactive, args)
        display_type_details(manager, args.edit)
    elif args.remove:
        from note_type_wizard import handle_remove

        handle_remove(manager, args.remove, args.yes)
    elif args.wizard:
        from note_type_wizard import handle_wizard

        handle_wizard(manager)


if __name__ == "__main__":
    main()
