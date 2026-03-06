#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Config Wizard - Guided configuration editing for Obsidian vaults.

Provides interactive guided editing for vault configuration.
In non-interactive mode (Claude Code), returns JSON with current config.

Usage:
    uv run config_wizard.py /path/to/settings.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


def handle_edit(settings_path: Path) -> None:
    """Handle edit config action.

    Args:
        settings_path: Path to settings.yaml file
    """
    if not settings_path.exists():
        print(json.dumps({"error": f"Settings file not found: {settings_path}"}))
        return

    with open(settings_path) as f:
        config = yaml.safe_load(f) or {}

    if not is_interactive():
        # Non-interactive: return JSON guidance
        result = {
            "interactive_required": True,
            "action": "edit_config",
            "current_config": config,
            "editable_fields": list(config.keys()),
            "hint": "Use obsidian:config show to view, then edit file directly",
        }
        print(json.dumps(result, indent=2, default=str))
        return

    # Interactive wizard
    print()
    print("\u250c" + "\u2500" * 58 + "\u2510")
    print("\u2502" + " EDIT CONFIGURATION".ljust(58) + "\u2502")
    print("\u251c" + "\u2500" * 58 + "\u2524")

    fields = list(config.keys())
    for i, key in enumerate(fields, 1):
        value = str(config[key])[:40]
        if len(str(config[key])) > 40:
            value += "..."
        line = f" {i}. {key}: {value}"
        print("\u2502" + line.ljust(58) + "\u2502")
    print("\u2514" + "\u2500" * 58 + "\u2518")

    # Store original for comparison
    with open(settings_path) as f:
        original = yaml.safe_load(f) or {}

    changed = False
    while True:
        choice = input("\n  Edit field [number, or 'done']: ").strip()
        if choice.lower() == "done" or choice == "":
            break

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(fields):
                raise ValueError()
            key = fields[idx]
        except (ValueError, IndexError):
            print("  \u2717 Invalid selection")
            continue

        current_val = config[key]
        print(f"\n  Current value: {current_val}")
        new_val = input(f"  New value [{current_val}]: ").strip()

        if new_val and new_val != str(current_val):
            # Type conversion based on original type
            if isinstance(current_val, bool):
                config[key] = new_val.lower() in ("true", "yes", "1", "on")
            elif isinstance(current_val, int):
                try:
                    config[key] = int(new_val)
                except ValueError:
                    print("  \u2717 Invalid integer")
                    continue
            elif isinstance(current_val, list):
                config[key] = [x.strip() for x in new_val.split(",")]
            else:
                config[key] = new_val
            print(f"  \u2713 Updated: {key}")
            changed = True

    if not changed:
        print("\n  No changes made")
        return

    # Show summary of changes
    print("\n  Summary of changes:")
    for key in fields:
        if config[key] != original.get(key):
            print(f"    {key}: {original.get(key)} \u2192 {config[key]}")

    if input("\n  Save changes? [y/N]: ").strip().lower() == "y":
        with open(settings_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print("  \u2713 Saved")
    else:
        print("  Cancelled")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Config Wizard - Guided configuration editing",
    )
    parser.add_argument(
        "settings_path",
        type=Path,
        help="Path to settings.yaml file",
    )

    args = parser.parse_args()

    handle_edit(args.settings_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
