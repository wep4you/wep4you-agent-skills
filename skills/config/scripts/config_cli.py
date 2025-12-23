#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Vault Configuration Management CLI

Manage validator configuration files with show, edit, set, reset, and validate commands.

Usage:
    uv run skills/config/scripts/config_cli.py --show
    uv run skills/config/scripts/config_cli.py --show-defaults
    uv run skills/config/scripts/config_cli.py --edit
    uv run skills/config/scripts/config_cli.py --set auto_fix.empty_types true
    uv run skills/config/scripts/config_cli.py --reset
    uv run skills/config/scripts/config_cli.py --validate
    uv run skills/config/scripts/config_cli.py --diff
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class ConfigManager:
    """Manage Obsidian vault validator configuration"""

    def __init__(self):
        self.vault_path = self._find_vault_root()
        self.config_path = self.vault_path / ".claude" / "config" / "validator.yaml"
        self.backup_dir = self.vault_path / ".claude" / "config" / "backups"

        # Default config embedded in script
        self.default_config = self._get_default_config()

    def _find_vault_root(self) -> Path:
        """Find vault root by looking for .obsidian directory"""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".obsidian").exists():
                return current
            current = current.parent

        # Fallback to current directory
        return Path.cwd()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "default_mode": "interactive",
            "exclude_paths": [
                "+/",
                "x/",
                ".obsidian/",
                ".git/",
                ".trash/",
                ".DS_Store",
                ".beads/",
                ".claude/",
            ],
            "exclude_files": [
                "Home.md",
                "README.md",
                "AGENTS.md",
            ],
            "auto_fix": {
                "empty_types": True,
                "daily_links": True,
                "wikilink_quotes": True,
                "invalid_created": True,
                "title_properties": True,
                "date_mismatches": True,
                "folder_renames": False,
            },
            "require_confirmation": [
                "folder_renames",
                "type_changes_bulk",
            ],
            "type_rules": {
                "Atlas/Maps/": "map",
                "Atlas/Dots/": "dot",
                "Atlas/Sources/": "source",
                "+/copilot-conversations/": "conversation",
                "+/": "source",
                "Efforts/Projects/": "project",
                "Efforts/Works/": "work",
                "Efforts/Areas/": "area",
                "Calendar/daily/": "daily",
                "Calendar/weekly/": "weekly",
                "Calendar/monthly/": "monthly",
                "Calendar/yearly/": "OKRs",
            },
            "report": {
                "format": "markdown",
                "save_to": ".claude/validation-reports/",
                "include_timestamp": True,
                "max_files_per_issue": 10,
                "verbose": False,
            },
            "git": {
                "auto_commit": False,
                "commit_message_prefix": "Vault validation: ",
                "create_branch": False,
                "branch_name_prefix": "validation-",
            },
            "performance": {
                "parallel_processing": False,
                "max_workers": 4,
                "cache_file_reads": True,
                "incremental_mode": False,
            },
            "thresholds": {
                "max_issues_auto_fix": 100,
                "critical_issue_count": 10,
            },
            "skip_code_blocks": True,
            "skip_frontmatter_examples": True,
            "version": "1.0.2",
            "compatible_with_vault": "6.11+",
        }

    def _load_config(self) -> dict[str, Any]:
        """Load current configuration or return defaults"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        return self.default_config.copy()

    def _save_config(self, config: dict[str, Any]) -> None:
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

    def _create_backup(self) -> Path | None:
        """Create backup of current config"""
        if not self.config_path.exists():
            return None

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"validator_{timestamp}.yaml"

        shutil.copy2(self.config_path, backup_path)
        return backup_path

    def show(self, defaults: bool = False) -> None:
        """Show current or default configuration"""
        if defaults:
            config = self.default_config
            print("# Default Configuration\n")
        else:
            config = self._load_config()
            print("# Current Configuration")
            print(f"# Path: {self.config_path}\n")

        print(yaml.safe_dump(config, default_flow_style=False, sort_keys=False, indent=2))

    def edit(self) -> None:
        """Open configuration in editor"""
        # Ensure config exists
        if not self.config_path.exists():
            print("Config file does not exist. Creating from defaults...")
            self._save_config(self.default_config)

        # Create backup before editing
        backup_path = self._create_backup()
        if backup_path:
            print(f"Backup created: {backup_path}")

        # Determine editor
        editor = os.environ.get("EDITOR", "vim")

        try:
            subprocess.run([editor, str(self.config_path)], check=True)  # noqa: S603
            print(f"\nConfiguration edited: {self.config_path}")

            # Validate after editing
            if self.validate():
                print("Configuration is valid!")
            else:
                print("\nWARNING: Configuration has validation errors!")
                if backup_path:
                    print(f"Backup available at: {backup_path}")
        except subprocess.CalledProcessError:
            print(f"Error opening editor: {editor}")
            sys.exit(1)

    def set_value(self, key: str, value: str) -> None:
        """Set a configuration value"""
        # Create backup
        backup_path = self._create_backup()
        if backup_path:
            print(f"Backup created: {backup_path}")

        # Load current config
        config = self._load_config()

        # Parse key path (e.g., "auto_fix.empty_types")
        keys = key.split(".")

        # Navigate to the right location
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Convert value to appropriate type
        final_key = keys[-1]
        if value.lower() in ("true", "false"):
            current[final_key] = value.lower() == "true"
        elif value.isdigit():
            current[final_key] = int(value)
        else:
            current[final_key] = value

        # Save
        self._save_config(config)
        print(f"Set {key} = {current[final_key]}")
        print(f"Saved to: {self.config_path}")

    def reset(self) -> None:
        """Reset configuration to defaults"""
        # Create backup
        backup_path = self._create_backup()
        if backup_path:
            print(f"Backup created: {backup_path}")

        # Save defaults
        self._save_config(self.default_config)
        print("Configuration reset to defaults")
        print(f"Saved to: {self.config_path}")

    def validate(self) -> bool:
        """Validate configuration structure"""
        try:
            config = self._load_config()

            errors = []

            # Check required top-level keys
            required_keys = ["auto_fix", "exclude_paths", "type_rules"]
            for key in required_keys:
                if key not in config:
                    errors.append(f"Missing required key: {key}")

            # Validate auto_fix is a dict
            if "auto_fix" in config and not isinstance(config["auto_fix"], dict):
                errors.append("auto_fix must be a dictionary")

            # Validate exclude_paths is a list
            if "exclude_paths" in config and not isinstance(config["exclude_paths"], list):
                errors.append("exclude_paths must be a list")

            # Validate type_rules is a dict
            if "type_rules" in config and not isinstance(config["type_rules"], dict):
                errors.append("type_rules must be a dictionary")

            if errors:
                print("Configuration validation FAILED:\n")
                for error in errors:
                    print(f"  - {error}")
                return False

            print("Configuration validation PASSED")
            return True

        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            print(f"Validation error: {e}")
            return False

    def diff(self) -> None:
        """Show difference between current and default config"""
        current = self._load_config()
        default = self.default_config

        print("# Configuration Diff (Current vs Default)\n")

        # Find differences
        changes = self._diff_dicts(default, current, "")

        if not changes:
            print("No differences - current config matches defaults")
        else:
            for change in changes:
                print(change)

    def _diff_dicts(self, d1: dict, d2: dict, path: str = "") -> list[str]:
        """Recursively find differences between two dicts"""
        changes = []

        # Check all keys in both dicts
        all_keys = set(d1.keys()) | set(d2.keys())

        for key in sorted(all_keys):
            current_path = f"{path}.{key}" if path else key

            # Key only in d1 (default)
            if key not in d2:
                changes.append(f"- {current_path}: REMOVED (was: {d1[key]})")

            # Key only in d2 (current)
            elif key not in d1:
                changes.append(f"+ {current_path}: ADDED (value: {d2[key]})")

            # Key in both
            else:
                v1, v2 = d1[key], d2[key]

                # Both are dicts - recurse
                if isinstance(v1, dict) and isinstance(v2, dict):
                    changes.extend(self._diff_dicts(v1, v2, current_path))

                # Values differ
                elif v1 != v2:
                    changes.append(f"~ {current_path}: {v1} → {v2}")

        return changes


def main():
    parser = argparse.ArgumentParser(
        description="Manage Obsidian vault validator configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --show                           # Show current config
  %(prog)s --show-defaults                  # Show default config
  %(prog)s --edit                           # Edit config in $EDITOR
  %(prog)s --set auto_fix.empty_types false # Set specific value
  %(prog)s --reset                          # Reset to defaults
  %(prog)s --validate                       # Validate config
  %(prog)s --diff                           # Show diff vs defaults
        """,
    )

    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--show-defaults", action="store_true", help="Show default configuration")
    parser.add_argument("--edit", action="store_true", help="Open configuration in editor")
    parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value")
    parser.add_argument("--reset", action="store_true", help="Reset configuration to defaults")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument(
        "--diff", action="store_true", help="Show diff between current and defaults"
    )

    args = parser.parse_args()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    manager = ConfigManager()

    # Execute command
    if args.show:
        manager.show(defaults=False)
    elif args.show_defaults:
        manager.show(defaults=True)
    elif args.edit:
        manager.edit()
    elif args.set:
        key, value = args.set
        manager.set_value(key, value)
    elif args.reset:
        manager.reset()
    elif args.validate:
        success = manager.validate()
        sys.exit(0 if success else 1)
    elif args.diff:
        manager.diff()


if __name__ == "__main__":
    main()
