#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Props Wizard - Interactive property management for Obsidian vaults.

Provides interactive wizards for adding and removing core properties.
In non-interactive mode (Claude Code), returns JSON guidance.

Usage:
    uv run props_wizard.py add [--vault /path] [--yes]
    uv run props_wizard.py remove [--vault /path] [--yes]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

# Default core properties
DEFAULT_CORE_PROPERTIES = ["type", "up", "created", "daily", "tags", "collection", "related"]

# Essential properties that cannot be removed
ESSENTIAL_PROPERTIES = ["type", "created"]


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


class PropsManager:
    """Manages frontmatter property definitions."""

    def __init__(self, vault_path: str | None = None) -> None:
        """Initialize props manager."""
        self.vault_path = Path(vault_path) if vault_path else Path.cwd()
        self.settings_path = self.vault_path / ".claude" / "settings.yaml"
        self.settings: dict = {}
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from settings.yaml."""
        if not self.settings_path.exists():
            self.settings = {"core_properties": list(DEFAULT_CORE_PROPERTIES)}
            return

        with self.settings_path.open() as f:
            self.settings = yaml.safe_load(f) or {}

    def _save_settings(self) -> None:
        """Save settings to settings.yaml."""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_path.open("w") as f:
            yaml.safe_dump(self.settings, f, default_flow_style=False, sort_keys=False)

    def get_core_properties(self) -> list[str]:
        """Get list of core properties."""
        core = self.settings.get("core_properties", {})
        if isinstance(core, dict):
            return list(core.get("all", DEFAULT_CORE_PROPERTIES))
        elif isinstance(core, list):
            return core
        return list(DEFAULT_CORE_PROPERTIES)


def handle_add(manager: PropsManager, yes: bool = False) -> None:
    """Handle add property action.

    Args:
        manager: PropsManager instance
        yes: Skip confirmation if True
    """
    if not is_interactive():
        # Non-interactive: return JSON guidance
        result = {
            "interactive_required": True,
            "action": "add_property",
            "message": "Provide property name and type, or use interactive mode",
            "schema": {
                "name": "Property name (lowercase, no spaces)",
                "type": "Property type: string, list, date, wikilink",
            },
            "current_properties": manager.get_core_properties(),
            "example": {"command": "obsidian:props core add status --type string --yes"},
        }
        print(json.dumps(result, indent=2))
        return

    # Interactive wizard with Box UI
    current = manager.get_core_properties()

    print()
    print("\u250c" + "\u2500" * 58 + "\u2510")
    print("\u2502" + " ADD PROPERTY".ljust(58) + "\u2502")
    print("\u251c" + "\u2500" * 58 + "\u2524")
    print("\u2502" + f" Current: {', '.join(current)}".ljust(58) + "\u2502")
    print("\u2514" + "\u2500" * 58 + "\u2518")

    name = input("\n  Property name: ").strip().lower()
    if not name:
        print("  \u2717 Name cannot be empty")
        return
    if name in current:
        print(f"  \u2717 Property '{name}' already exists")
        return

    prop_type = input("  Type [string]: ").strip() or "string"

    print(f"\n  \u2192 Add '{name}' ({prop_type}) to core properties?")
    if input("  Confirm [y/N]: ").strip().lower() != "y":
        print("  Cancelled")
        return

    current.append(name)
    manager.settings["core_properties"] = current
    manager._save_settings()
    print(f"  \u2713 Added: {name}")


def handle_remove(manager: PropsManager, yes: bool = False) -> None:
    """Handle remove property action.

    Args:
        manager: PropsManager instance
        yes: Skip confirmation if True
    """
    props = manager.get_core_properties()
    # Filter out essential properties
    removable = [p for p in props if p not in ESSENTIAL_PROPERTIES]

    if not is_interactive():
        # Non-interactive: return JSON guidance
        result = {
            "interactive_required": True,
            "action": "remove_property",
            "message": "Select a property to remove",
            "current_properties": props,
            "removable_properties": removable,
            "essential_properties": ESSENTIAL_PROPERTIES,
            "confirm_command": "obsidian:props core remove <name> --yes",
        }
        print(json.dumps(result, indent=2))
        return

    # Interactive: show list with selection
    print()
    print("\u250c" + "\u2500" * 58 + "\u2510")
    print("\u2502" + " REMOVE PROPERTY".ljust(58) + "\u2502")
    print("\u251c" + "\u2500" * 58 + "\u2524")
    for i, p in enumerate(removable, 1):
        print("\u2502" + f" {i}. {p}".ljust(58) + "\u2502")
    if not removable:
        print("\u2502" + " (no removable properties)".ljust(58) + "\u2502")
    print("\u251c" + "\u2500" * 58 + "\u2524")
    essential_str = ", ".join(ESSENTIAL_PROPERTIES)
    print("\u2502" + f" Essential (cannot remove): {essential_str}".ljust(58) + "\u2502")
    print("\u2514" + "\u2500" * 58 + "\u2518")

    if not removable:
        print("\n  No properties can be removed.")
        return

    choice = input("\n  Remove [number or name]: ").strip()

    # Try to parse as number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(removable):
            name = removable[idx]
        else:
            print(f"  \u2717 Invalid selection: {choice}")
            return
    except ValueError:
        name = choice.lower()

    if name not in props:
        print(f"  \u2717 Property '{name}' not found")
        return

    if name in ESSENTIAL_PROPERTIES:
        print(f"  \u2717 Cannot remove essential property: {name}")
        return

    if input(f"  Delete '{name}'? [y/N]: ").strip().lower() != "y":
        print("  Cancelled")
        return

    props.remove(name)
    manager.settings["core_properties"] = props
    manager._save_settings()
    print(f"  \u2713 Removed: {name}")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Props Wizard - Interactive property management",
    )
    parser.add_argument(
        "action",
        choices=["add", "remove"],
        help="Action to perform",
    )
    parser.add_argument(
        "--vault",
        type=str,
        default=".",
        help="Path to vault (default: current directory)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation (for non-interactive use)",
    )

    args = parser.parse_args()

    manager = PropsManager(args.vault)

    if args.action == "add":
        handle_add(manager, args.yes)
    elif args.action == "remove":
        handle_remove(manager, args.yes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
