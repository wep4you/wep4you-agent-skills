#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Settings Loader CLI for Obsidian Vault.

Thin CLI wrapper around core settings functionality.
All business logic is in skills.core.settings and skills.core.models.
"""

from __future__ import annotations

import sys
from pathlib import Path

from skills.core.settings import (
    SETTINGS_FILE,
    create_backup,
    create_default_settings,
    diff_settings,
    load_settings,
    set_setting,
    validate_settings,
)

METHODOLOGIES = ["lyt-ace", "para", "zettelkasten", "minimal", "custom"]

# ANSI color codes
C_Y, C_R, C_G, C_0, C_B = "\033[93m", "\033[91m", "\033[92m", "\033[0m", "\033[1m"


def print_reset_help() -> None:
    """Print help for --reset option with examples."""
    print(f"{C_B}Available methodologies for --reset:{C_0}\n")
    descs = {
        "lyt-ace": "Linking Your Thinking with ACE folder structure",
        "para": "Projects, Areas, Resources, Archives",
        "zettelkasten": "Zettelkasten/slip-box method",
        "minimal": "Minimal starter configuration",
        "custom": "Empty custom configuration",
    }
    for m in METHODOLOGIES:
        print(f"  {C_G}{m:<14}{C_0} {descs.get(m, '')}")
    print(f"\n{C_B}Examples:{C_0}")
    print(f"  {C_Y}--reset para{C_0}              # Reset to PARA (with confirmation)")
    print(f"  {C_Y}--reset zettelkasten --yes{C_0} # Reset (skip confirmation)\n")


def edit_settings(vault_path: Path) -> bool:
    """Open settings.yaml in editor. Returns True if successful."""
    import os
    import subprocess

    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        print("Settings file does not exist. Creating default...")
        create_default_settings(vault_path)

    backup_path = create_backup(vault_path)
    if backup_path:
        print(f"Backup created: {backup_path}")

    editor = os.environ.get("EDITOR", "vim")
    try:
        subprocess.run([editor, str(settings_path)], check=True)  # noqa: S603
        print(f"\nSettings edited: {settings_path}")
        try:
            settings = load_settings(vault_path)
            errors = validate_settings(settings)
            if errors:
                print("\nWARNING: Settings have validation errors:")
                for e in errors:
                    print(f"  - {e}")
                if backup_path:
                    print(f"\nBackup available at: {backup_path}")
                return False
            print("Settings are valid")
            return True
        except Exception as e:
            print(f"\nError loading settings: {e}")
            if backup_path:
                print(f"Backup available at: {backup_path}")
            return False
    except subprocess.CalledProcessError:
        print(f"Error opening editor: {editor}")
        return False


def main() -> int:
    """CLI entry point for settings loader."""
    import argparse

    p = argparse.ArgumentParser(
        description="Settings Loader for Obsidian Vault",
        epilog="Use --reset list to see available methodologies with examples.",
    )
    p.add_argument("--vault", type=Path, required=True, help="Path to vault")
    p.add_argument("--create", action="store_true", help="Create default settings if missing")
    p.add_argument("--validate", action="store_true", help="Validate settings structure")
    p.add_argument("--show", action="store_true", help="Show loaded settings")
    p.add_argument("--type", type=str, help="Show config for specific note type")
    p.add_argument("--reset", metavar="METHOD", help="Reset to methodology or 'list' for help")
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation (with --reset)")
    p.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set config value")
    p.add_argument("--edit", action="store_true", help="Open settings in editor")
    p.add_argument("--diff", action="store_true", help="Show diff vs defaults")
    args = p.parse_args()

    try:
        if args.reset:
            if args.reset == "list":
                print_reset_help()
                return 0
            if args.reset not in METHODOLOGIES:
                print(f"{C_R}Invalid methodology: {args.reset}{C_0}\n")
                print_reset_help()
                return 1

            settings_path = args.vault / SETTINGS_FILE
            if settings_path.exists() and not args.yes:
                if not sys.stdin.isatty():
                    print(f"{C_B}{C_Y}WARNING: Cannot confirm interactively.{C_0}")
                    print(f"   Use {C_B}--yes{C_0} to confirm. Example: --reset {args.reset} --yes")
                    return 1
                print(f"{C_B}{C_Y}WARNING: This will overwrite your settings!{C_0}")
                print(f"   Current: {settings_path}\n   New methodology: {C_B}{args.reset}{C_0}\n")
                if input(f"{C_Y}Type 'yes' to confirm: {C_0}").strip().lower() != "yes":
                    print(f"{C_R}Reset cancelled.{C_0}")
                    return 1
                settings_path.unlink()
                print(f"{C_G}Old settings removed.{C_0}")

            new_path = create_default_settings(args.vault, methodology=args.reset)
            print(f"{C_G}Created: {new_path}{C_0}\n   Methodology: {C_B}{args.reset}{C_0}")
            s = load_settings(args.vault)
            print(f"\nVersion: {s.version}\nMethodology: {s.methodology}")
            print(f"Core properties: {s.core_properties}\nNote types: {list(s.note_types.keys())}")
            return 0

        if args.set:
            set_setting(args.vault, args.set[0], args.set[1])
            return 0

        if args.edit:
            return 0 if edit_settings(args.vault) else 1

        if args.diff:
            print("# Configuration Diff (Current vs Default)\n")
            changes = diff_settings(args.vault)
            print("\n".join(changes) if changes else "No differences")
            return 0

        settings = load_settings(args.vault, create_if_missing=args.create)

        if args.validate:
            errors = validate_settings(settings)
            if errors:
                print("Settings validation failed:", file=sys.stderr)
                for e in errors:
                    print(f"  - {e}", file=sys.stderr)
                return 1
            print("Settings are valid")

        if args.type:
            nt = settings.get_note_type(args.type)
            if nt:
                print(f"Note type: {nt.name}\n  Description: {nt.description}")
                print(f"  Folder hints: {nt.folder_hints}\n  Required: {nt.required_properties}")
                print(f"  Optional: {nt.optional_properties}")
            else:
                print(f"Note type '{args.type}' not found", file=sys.stderr)
                return 1

        if args.show:
            print(f"Version: {settings.version}\nMethodology: {settings.methodology}")
            print(f"Core properties: {settings.core_properties}")
            print(f"Note types: {list(settings.note_types.keys())}")
            print(f"Validation rules: {settings.validation}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Use --create to create default settings", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
