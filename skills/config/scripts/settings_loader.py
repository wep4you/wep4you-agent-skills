#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Settings Loader for Obsidian Vault

Loads and validates user settings from .claude/settings.yaml.
This is the PRIMARY source of truth for all validation and configuration.

Usage:
    from settings_loader import load_settings, get_note_type, get_validation_rules

    # Load settings (creates default if not exists)
    settings = load_settings(Path("/path/to/vault"))

    # Get note type configuration
    note_type = get_note_type(settings, "map")

    # Get validation rules
    rules = get_validation_rules(settings)
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ValidationRules:
    """Validation rules from settings."""

    require_core_properties: bool = True
    allow_empty_properties: list[str] = field(default_factory=list)
    strict_types: bool = True
    check_templates: bool = True
    check_up_links: bool = True
    check_inbox_no_frontmatter: bool = True


@dataclass
class NoteTypeConfig:
    """Configuration for a note type."""

    name: str
    description: str
    folder_hints: list[str]
    required_properties: list[str]
    optional_properties: list[str]
    validation: dict[str, Any]
    icon: str = ""
    inherit_core: bool = True  # Whether this type inherits core_properties


@dataclass
class Settings:
    """User settings loaded from settings.yaml."""

    version: str
    methodology: str
    core_properties: list[str]
    note_types: dict[str, NoteTypeConfig]
    validation: ValidationRules
    folder_structure: dict[str, Any]
    up_links: dict[str, str]
    exclude_paths: list[str]
    exclude_files: list[str]
    exclude_patterns: list[str]
    formats: dict[str, Any]
    logging: dict[str, Any]
    raw: dict[str, Any]  # Original YAML dict for access to any custom fields


SETTINGS_FILE = ".claude/settings.yaml"
TEMPLATE_FILE = Path(__file__).parent.parent / "templates" / "settings.yaml"


def load_settings(vault_path: Path, create_if_missing: bool = False) -> Settings:
    """
    Load settings from .claude/settings.yaml.

    Args:
        vault_path: Path to Obsidian vault root
        create_if_missing: If True, create default settings.yaml if not found

    Returns:
        Settings object with all configuration

    Raises:
        FileNotFoundError: If settings.yaml doesn't exist and create_if_missing is False
        ValueError: If settings.yaml is invalid or vault_path is not a directory
    """
    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise ValueError(f"Vault path is not a directory: {vault_path}")

    settings_path = vault_path / SETTINGS_FILE

    if not settings_path.exists():
        if create_if_missing:
            create_default_settings(vault_path)
        else:
            raise FileNotFoundError(
                f"Settings file not found: {settings_path}\n"
                "Run 'init' skill to create settings or use create_if_missing=True"
            )

    try:
        with settings_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in settings file: {e}") from e

    if not raw:
        raise ValueError(f"Empty settings file: {settings_path}")

    return _parse_settings(raw)


def _parse_settings(raw: dict[str, Any]) -> Settings:
    """Parse raw YAML dict into Settings object."""
    # Handle both formats:
    # - Old: core_properties: [type, up, created, tags]
    # - New: core_properties: {all: [type, up, ...], mandatory: [...], optional: [...]}
    core_props_raw = raw.get("core_properties", [])
    if isinstance(core_props_raw, dict):
        # New format: use the 'all' key
        core_properties = core_props_raw.get("all", [])
    else:
        # Old format: direct list
        core_properties = core_props_raw

    # Parse note types with inheritance support
    note_types = {}
    for name, config in raw.get("note_types", {}).items():
        props = config.get("properties", {})
        inherit_core = config.get("inherit_core", True)  # Default: inherit

        # Compute required properties based on inheritance
        if inherit_core:
            # New format: core + additional_required
            additional_required = props.get("additional_required", [])
            # Backward compat: if "required" exists and no "additional_required", use required
            explicit_required = props.get("required", [])

            if explicit_required and not additional_required:
                # Old format: required contains everything
                required_properties = explicit_required
            else:
                # New format: core + additional
                required_properties = list(core_properties) + additional_required
        else:
            # No inheritance: use explicit required list only
            required_properties = props.get("required", [])

        note_types[name] = NoteTypeConfig(
            name=name,
            description=config.get("description", ""),
            folder_hints=config.get("folder_hints", []),
            required_properties=required_properties,
            optional_properties=props.get("optional", []),
            validation=config.get("validation", {}),
            icon=config.get("icon", ""),
            inherit_core=inherit_core,
        )

    # Parse validation rules
    val_raw = raw.get("validation", {})
    validation = ValidationRules(
        require_core_properties=val_raw.get("require_core_properties", True),
        allow_empty_properties=val_raw.get("allow_empty_properties", []),
        strict_types=val_raw.get("strict_types", True),
        check_templates=val_raw.get("check_templates", True),
        check_up_links=val_raw.get("check_up_links", True),
        check_inbox_no_frontmatter=val_raw.get("check_inbox_no_frontmatter", True),
    )

    # Parse exclusions
    exclude = raw.get("exclude", {})

    return Settings(
        version=raw.get("version", "1.0"),
        methodology=raw.get("methodology", "custom"),
        core_properties=core_properties,
        note_types=note_types,
        validation=validation,
        folder_structure=raw.get("folder_structure", {}),
        up_links=raw.get("up_links", {}),
        exclude_paths=exclude.get("paths", []),
        exclude_files=exclude.get("files", []),
        exclude_patterns=exclude.get("patterns", []),
        formats=raw.get("formats", {}),
        logging=raw.get("logging", {}),
        raw=raw,
    )


def create_default_settings(vault_path: Path, methodology: str = "lyt-ace") -> Path:
    """
    Create default settings.yaml in vault.

    Args:
        vault_path: Path to vault root
        methodology: Methodology template to use

    Returns:
        Path to created settings file
    """
    settings_dir = vault_path / ".claude"
    settings_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = settings_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    settings_path = settings_dir / "settings.yaml"

    if TEMPLATE_FILE.exists():
        shutil.copy(TEMPLATE_FILE, settings_path)
        # Update methodology if different from default
        if methodology != "lyt-ace":
            with settings_path.open("r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace('methodology: "lyt-ace"', f'methodology: "{methodology}"')
            with settings_path.open("w", encoding="utf-8") as f:
                f.write(content)
    else:
        # Fallback: create minimal settings
        minimal = {
            "version": "1.0",
            "methodology": methodology,
            "core_properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
            "note_types": {},
            "validation": {"require_core_properties": True},
            "exclude": {"paths": ["+/", "x/", ".obsidian/", ".claude/", ".git/"]},
        }
        with settings_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(minimal, f, default_flow_style=False, sort_keys=False)

    return settings_path


def get_note_type(settings: Settings, type_name: str) -> NoteTypeConfig | None:
    """Get configuration for a specific note type."""
    return settings.note_types.get(type_name)


def get_validation_rules(settings: Settings) -> ValidationRules:
    """Get validation rules from settings."""
    return settings.validation


def get_core_properties(settings: Settings) -> list[str]:
    """Get list of core properties required in all notes."""
    return settings.core_properties


def get_all_properties_for_type(settings: Settings, type_name: str) -> list[str]:
    """Get all properties (required + optional) for a note type."""
    note_type = get_note_type(settings, type_name)
    if not note_type:
        return settings.core_properties.copy()
    return note_type.required_properties + note_type.optional_properties


def infer_note_type_from_path(settings: Settings, file_path: Path) -> str | None:
    """Infer note type from file path based on folder hints."""
    file_path_str = str(file_path)

    for type_name, config in settings.note_types.items():
        for hint in config.folder_hints:
            if hint in file_path_str:
                return type_name

    return None


def get_up_link_for_path(settings: Settings, file_path: Path) -> str | None:
    """Get expected UP link for a file based on its path."""
    file_path_str = str(file_path)

    for folder_pattern, up_link in settings.up_links.items():
        if folder_pattern in file_path_str:
            return up_link

    return None


def should_exclude(settings: Settings, file_path: Path) -> bool:
    """Check if a file should be excluded from validation."""
    import fnmatch

    file_path_str = str(file_path)

    # Check excluded paths
    for excluded_path in settings.exclude_paths:
        if excluded_path in file_path_str:
            return True

    # Check excluded files
    if file_path.name in settings.exclude_files:
        return True

    # Check excluded patterns (glob-style matching)
    for pattern in settings.exclude_patterns:
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

    # Always exclude system documentation files in vault root
    # These files use type: "system" and don't follow note type validation rules
    system_files = {"AGENTS.md", "CLAUDE.md", "README.md", "Home.md"}
    if file_path.name in system_files:
        # Only exclude if in vault root (check no subfolder in path)
        # If none of these methodology folders appear in path, file is in vault root
        methodology_folders = [
            "Atlas/",
            "Calendar/",
            "Efforts/",
            "Projects/",
            "Areas/",
            "Resources/",
            "Archives/",
            "Notes/",
            "Daily/",
            "Zettel/",
            "References/",
            "Literature/",
        ]
        if not any(folder in file_path_str for folder in methodology_folders):
            return True

    return False


def is_inbox_path(settings: Settings, file_path: Path) -> bool:
    """Check if a file is in the inbox (no frontmatter required)."""
    inbox_path = settings.folder_structure.get("inbox", "+/")
    return inbox_path in str(file_path)


def validate_settings(settings: Settings) -> list[str]:
    """
    Validate settings structure.

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Check version
    if not settings.version:
        errors.append("Missing 'version' in settings")

    # Check core_properties
    if not settings.core_properties:
        errors.append("Missing or empty 'core_properties'")

    # Check required properties in note types
    for type_name, config in settings.note_types.items():
        if not config.required_properties:
            errors.append(f"Note type '{type_name}' has no required properties")

        # Validate inheritance
        if config.inherit_core:
            # When inheriting, required_properties should include all core properties
            missing_core = [
                p for p in settings.core_properties if p not in config.required_properties
            ]
            if missing_core:
                errors.append(
                    f"Note type '{type_name}' has inherit_core=True but "
                    f"missing core properties: {missing_core}"
                )

    return errors


def settings_exist(vault_path: Path) -> bool:
    """Check if settings.yaml exists in vault."""
    return (vault_path / SETTINGS_FILE).exists()


def get_backup_dir(vault_path: Path) -> Path:
    """Get backup directory path."""
    return vault_path / ".claude" / "backups"


def create_backup(vault_path: Path) -> Path | None:
    """
    Create backup of current settings.yaml.

    Returns:
        Path to backup file, or None if no settings exist
    """
    from datetime import datetime

    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        return None

    backup_dir = get_backup_dir(vault_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"settings_{timestamp}.yaml"

    shutil.copy2(settings_path, backup_path)
    return backup_path


def set_setting(vault_path: Path, key: str, value: str, create_backup_file: bool = True) -> None:
    """
    Set a configuration value in settings.yaml.

    Args:
        vault_path: Path to vault root
        key: Dot-separated key path (e.g., "validation.strict_types")
        value: Value to set (auto-converted to bool/int if applicable)
        create_backup_file: Whether to create backup before modifying

    Raises:
        FileNotFoundError: If settings.yaml doesn't exist
        ValueError: If key path is invalid
    """
    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

    # Create backup before modifying
    if create_backup_file:
        backup_path = create_backup(vault_path)
        if backup_path:
            print(f"Backup created: {backup_path}")

    # Load raw YAML
    with settings_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # Parse key path
    keys = key.split(".")
    if not keys:
        raise ValueError("Key cannot be empty")

    # Navigate to the right location
    current = config
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            raise ValueError(f"Cannot set nested key: {k} is not a dict")
        current = current[k]

    # Convert value to appropriate type
    final_key = keys[-1]
    if value.lower() in ("true", "false"):
        current[final_key] = value.lower() == "true"
    elif value.isdigit():
        current[final_key] = int(value)
    elif value.startswith("[") and value.endswith("]"):
        # Simple list parsing
        items = value[1:-1].split(",")
        current[final_key] = [item.strip().strip("'\"") for item in items if item.strip()]
    else:
        current[final_key] = value

    # Save
    with settings_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

    print(f"Set {key} = {current[final_key]}")
    print(f"Saved to: {settings_path}")


def get_default_settings_dict() -> dict:
    """Get default settings as a dictionary for comparison."""
    return {
        "version": "1.0",
        "methodology": "custom",
        "core_properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        "note_types": {},
        "validation": {
            "require_core_properties": True,
            "allow_empty_properties": ["tags", "collection", "related"],
            "strict_types": True,
            "check_templates": True,
            "check_up_links": True,
            "check_inbox_no_frontmatter": True,
        },
        "exclude": {
            "paths": ["+/", "x/", ".obsidian/", ".claude/", ".git/"],
            "files": ["Home.md", "README.md"],
            "patterns": ["_*_MOC.md"],  # MOC files in each folder
        },
    }


def diff_settings(vault_path: Path) -> list[str]:
    """
    Compare current settings with defaults.

    Returns:
        List of difference strings
    """
    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        return ["Settings file does not exist - using defaults"]

    with settings_path.open("r", encoding="utf-8") as f:
        current = yaml.safe_load(f) or {}

    default = get_default_settings_dict()
    return _diff_dicts(default, current, "")


def _diff_dicts(d1: dict, d2: dict, path: str = "") -> list[str]:
    """Recursively find differences between two dicts."""
    changes = []

    all_keys = set(d1.keys()) | set(d2.keys())

    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key

        if key not in d2:
            changes.append(f"- {current_path}: REMOVED (was: {d1[key]})")
        elif key not in d1:
            changes.append(f"+ {current_path}: ADDED (value: {d2[key]})")
        else:
            v1, v2 = d1[key], d2[key]
            if isinstance(v1, dict) and isinstance(v2, dict):
                changes.extend(_diff_dicts(v1, v2, current_path))
            elif v1 != v2:
                changes.append(f"~ {current_path}: {v1} → {v2}")

    return changes


def edit_settings(vault_path: Path) -> bool:
    """
    Open settings.yaml in editor.

    Returns:
        True if edit was successful
    """
    import os
    import subprocess

    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        print("Settings file does not exist. Creating default...")
        create_default_settings(vault_path)

    # Create backup before editing
    backup_path = create_backup(vault_path)
    if backup_path:
        print(f"Backup created: {backup_path}")

    editor = os.environ.get("EDITOR", "vim")

    try:
        subprocess.run([editor, str(settings_path)], check=True)  # noqa: S603
        print(f"\nSettings edited: {settings_path}")

        # Validate after editing
        try:
            settings = load_settings(vault_path)
            errors = validate_settings(settings)
            if errors:
                print("\n⚠️  WARNING: Settings have validation errors:")
                for error in errors:
                    print(f"  - {error}")
                if backup_path:
                    print(f"\nBackup available at: {backup_path}")
                return False
            print("✅ Settings are valid")
            return True
        except Exception as e:
            print(f"\n❌ Error loading settings: {e}")
            if backup_path:
                print(f"Backup available at: {backup_path}")
            return False

    except subprocess.CalledProcessError:
        print(f"Error opening editor: {editor}")
        return False


METHODOLOGIES = ["lyt-ace", "para", "zettelkasten", "minimal", "custom"]

# ANSI color codes
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"


def print_reset_help() -> None:
    """Print help for --reset option with examples."""
    print(f"{COLOR_BOLD}Available methodologies for --reset:{COLOR_RESET}\n")
    methodology_descriptions = {
        "lyt-ace": "Linking Your Thinking with ACE folder structure",
        "para": "Projects, Areas, Resources, Archives",
        "zettelkasten": "Zettelkasten/slip-box method",
        "minimal": "Minimal starter configuration",
        "custom": "Empty custom configuration",
    }
    for method in METHODOLOGIES:
        desc = methodology_descriptions.get(method, "")
        print(f"  {COLOR_GREEN}{method:<14}{COLOR_RESET} {desc}")

    print(f"\n{COLOR_BOLD}Examples:{COLOR_RESET}\n")
    print("  # Reset to PARA methodology (with confirmation)")
    print(f"  {COLOR_YELLOW}--reset para{COLOR_RESET}\n")
    print("  # Reset to Zettelkasten (skip confirmation)")
    print(f"  {COLOR_YELLOW}--reset zettelkasten --yes{COLOR_RESET}\n")


def main() -> int:
    """CLI entry point for testing settings loader."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Settings Loader for Obsidian Vault",
        epilog="Use --reset list to see available methodologies with examples.",
    )
    parser.add_argument("--vault", type=Path, required=True, help="Path to vault")
    parser.add_argument("--create", action="store_true", help="Create default settings if missing")
    parser.add_argument("--validate", action="store_true", help="Validate settings structure")
    parser.add_argument("--show", action="store_true", help="Show loaded settings")
    parser.add_argument("--type", type=str, help="Show config for specific note type")
    parser.add_argument(
        "--reset",
        metavar="METHODOLOGY",
        help=f"Reset settings to methodology ({', '.join(METHODOLOGIES)}) or 'list' for help",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt (use with --reset)"
    )
    parser.add_argument(
        "--set",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Set configuration value (e.g., --set validation.strict_types false)",
    )
    parser.add_argument("--edit", action="store_true", help="Open settings in editor")
    parser.add_argument(
        "--diff", action="store_true", help="Show diff between current and defaults"
    )

    args = parser.parse_args()

    try:
        # Handle reset operation
        if args.reset:
            # Show help if 'list' is specified
            if args.reset == "list":
                print_reset_help()
                return 0

            # Validate methodology choice
            if args.reset not in METHODOLOGIES:
                print(f"{COLOR_RED}❌ Invalid methodology: {args.reset}{COLOR_RESET}\n")
                print_reset_help()
                return 1

            settings_path = args.vault / SETTINGS_FILE
            if settings_path.exists():
                if not args.yes:
                    # Check if running interactively
                    if not sys.stdin.isatty():
                        warn = f"{COLOR_BOLD}{COLOR_YELLOW}⚠️  WARNING: "
                        warn += f"Cannot confirm interactively.{COLOR_RESET}"
                        print(warn)
                        print(f"   Use {COLOR_BOLD}--yes{COLOR_RESET} flag to confirm reset.")
                        print(f"   Example: --reset {args.reset} --yes")
                        return 1

                    warn = f"{COLOR_BOLD}{COLOR_YELLOW}⚠️  WARNING: "
                    warn += f"This will overwrite your existing settings!{COLOR_RESET}"
                    print(warn)
                    print(f"   Current file: {settings_path}")
                    print(f"   New methodology: {COLOR_BOLD}{args.reset}{COLOR_RESET}")
                    print()
                    confirm = (
                        input(f"{COLOR_YELLOW}Type 'yes' to confirm reset: {COLOR_RESET}")
                        .strip()
                        .lower()
                    )
                    if confirm != "yes":
                        print(f"{COLOR_RED}❌ Reset cancelled.{COLOR_RESET}")
                        return 1
                # Remove existing settings
                settings_path.unlink()
                print(f"{COLOR_GREEN}✅ Old settings removed.{COLOR_RESET}")

            # Create new settings with specified methodology
            new_path = create_default_settings(args.vault, methodology=args.reset)
            print(f"{COLOR_GREEN}✅ Created new settings: {new_path}{COLOR_RESET}")
            print(f"   Methodology: {COLOR_BOLD}{args.reset}{COLOR_RESET}")

            # Load and show the new settings
            settings = load_settings(args.vault)
            print(f"\nVersion: {settings.version}")
            print(f"Methodology: {settings.methodology}")
            print(f"Core properties: {settings.core_properties}")
            print(f"Note types: {list(settings.note_types.keys())}")
            return 0

        # Handle set operation
        if args.set:
            key, value = args.set
            set_setting(args.vault, key, value)
            return 0

        # Handle edit operation
        if args.edit:
            success = edit_settings(args.vault)
            return 0 if success else 1

        # Handle diff operation
        if args.diff:
            print("# Configuration Diff (Current vs Default)\n")
            changes = diff_settings(args.vault)
            if not changes:
                print("No differences - current config matches defaults")
            else:
                for change in changes:
                    print(change)
            return 0

        settings = load_settings(args.vault, create_if_missing=args.create)

        if args.validate:
            errors = validate_settings(settings)
            if errors:
                print("❌ Settings validation failed:", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
                return 1
            print("✅ Settings are valid")

        if args.type:
            note_type = get_note_type(settings, args.type)
            if note_type:
                print(f"Note type: {note_type.name}")
                print(f"  Description: {note_type.description}")
                print(f"  Folder hints: {note_type.folder_hints}")
                print(f"  Required: {note_type.required_properties}")
                print(f"  Optional: {note_type.optional_properties}")
            else:
                print(f"Note type '{args.type}' not found", file=sys.stderr)
                return 1

        if args.show:
            print(f"Version: {settings.version}")
            print(f"Methodology: {settings.methodology}")
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
