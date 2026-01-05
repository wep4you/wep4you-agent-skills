#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Config Command - Unified configuration management

Consolidates all config-related commands under obsidian:config:
- obsidian:config          Show current configuration
- obsidian:config show     Show detailed configuration
- obsidian:config edit     Edit settings in editor
- obsidian:config validate Validate configuration structure
- obsidian:config methodologies  List available methodologies
- obsidian:config create   Create default settings

Usage:
    uv run config_command.py --vault /path/to/vault
    uv run config_command.py --vault /path/to/vault show
    uv run config_command.py --vault /path/to/vault edit
    uv run config_command.py --vault /path/to/vault validate
    uv run config_command.py --vault /path/to/vault methodologies
    uv run config_command.py --vault /path/to/vault create --methodology para
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

# Import from settings_loader in same directory
sys.path.insert(0, str(Path(__file__).parent))
from settings_loader import (
    METHODOLOGIES,
    create_backup,
    create_default_settings,
    diff_settings,
    edit_settings,
    load_settings,
    validate_settings,
)

# ANSI colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


def cmd_show(vault_path: Path, output_format: str = "text", verbose: bool = False) -> int:
    """Show current vault configuration.

    Args:
        vault_path: Path to vault
        output_format: Output format (text, json, yaml)
        verbose: Show all details

    Returns:
        Exit code
    """
    try:
        settings = load_settings(vault_path)
    except FileNotFoundError:
        print(f"{COLOR_RED}No settings.yaml found.{COLOR_RESET}")
        print(f"Run {COLOR_CYAN}obsidian:config create{COLOR_RESET} to initialize.")
        return 1
    except ValueError as e:
        print(f"{COLOR_RED}Invalid settings: {e}{COLOR_RESET}")
        return 1

    if output_format == "json":
        print(json.dumps(settings.raw, indent=2))
        return 0

    if output_format == "yaml":
        print(yaml.dump(settings.raw, default_flow_style=False, sort_keys=False))
        return 0

    # Text format
    print(f"\n{COLOR_BOLD}Vault Configuration{COLOR_RESET}")
    print("=" * 50)
    print(f"\n{COLOR_CYAN}Path:{COLOR_RESET} {vault_path}")
    print(f"{COLOR_CYAN}Version:{COLOR_RESET} {settings.version}")
    print(f"{COLOR_CYAN}Methodology:{COLOR_RESET} {settings.methodology}")

    print(f"\n{COLOR_BOLD}Core Properties{COLOR_RESET}")
    print("-" * 30)
    for prop in settings.core_properties:
        print(f"  - {prop}")

    print(f"\n{COLOR_BOLD}Note Types ({len(settings.note_types)}){COLOR_RESET}")
    print("-" * 30)
    for name, config in sorted(settings.note_types.items()):
        icon = config.icon or ""
        folders = ", ".join(config.folder_hints) if config.folder_hints else "-"
        print(f"  {icon} {name}: {folders}")

    if verbose:
        print(f"\n{COLOR_BOLD}Validation Rules{COLOR_RESET}")
        print("-" * 30)
        print(f"  Require core properties: {settings.validation.require_core_properties}")
        print(f"  Strict types: {settings.validation.strict_types}")
        print(f"  Check templates: {settings.validation.check_templates}")
        print(f"  Check up links: {settings.validation.check_up_links}")

        print(f"\n{COLOR_BOLD}Exclusions{COLOR_RESET}")
        print("-" * 30)
        print(f"  Paths: {', '.join(settings.exclude_paths)}")
        print(f"  Files: {', '.join(settings.exclude_files)}")

    print()
    return 0


def cmd_edit(vault_path: Path) -> int:
    """Open settings in editor.

    Args:
        vault_path: Path to vault

    Returns:
        Exit code
    """
    success = edit_settings(vault_path)
    return 0 if success else 1


def cmd_validate(vault_path: Path, output_format: str = "text") -> int:
    """Validate configuration structure.

    Args:
        vault_path: Path to vault
        output_format: Output format (text, json)

    Returns:
        Exit code (0 if valid)
    """
    try:
        settings = load_settings(vault_path)
    except FileNotFoundError:
        if output_format == "json":
            print(json.dumps({"valid": False, "error": "Settings file not found"}))
        else:
            print(f"{COLOR_RED}No settings.yaml found.{COLOR_RESET}")
        return 1
    except ValueError as e:
        if output_format == "json":
            print(json.dumps({"valid": False, "error": str(e)}))
        else:
            print(f"{COLOR_RED}Invalid YAML: {e}{COLOR_RESET}")
        return 1

    errors = validate_settings(settings)

    if output_format == "json":
        print(
            json.dumps(
                {
                    "valid": len(errors) == 0,
                    "errors": errors,
                    "methodology": settings.methodology,
                    "version": settings.version,
                }
            )
        )
        return 0 if not errors else 1

    if errors:
        print(f"{COLOR_RED}Configuration has {len(errors)} error(s):{COLOR_RESET}\n")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"{COLOR_GREEN}Configuration is valid.{COLOR_RESET}")
    print(f"  Methodology: {settings.methodology}")
    print(f"  Note types: {len(settings.note_types)}")
    print(f"  Core properties: {len(settings.core_properties)}")
    return 0


def cmd_methodologies(output_format: str = "text") -> int:
    """List available methodologies.

    Args:
        output_format: Output format (text, json)

    Returns:
        Exit code
    """
    methodology_info = {
        "lyt-ace": {
            "name": "LYT-ACE",
            "description": "Linking Your Thinking with ACE folder structure",
            "folders": ["Atlas/Maps", "Atlas/Dots", "Atlas/Sources", "Calendar", "Efforts"],
        },
        "para": {
            "name": "PARA",
            "description": "Projects, Areas, Resources, Archives",
            "folders": ["Projects", "Areas", "Resources", "Archive"],
        },
        "zettelkasten": {
            "name": "Zettelkasten",
            "description": "Slip-box method for networked thought",
            "folders": ["Zettel", "Index", "Archive"],
        },
        "minimal": {
            "name": "Minimal",
            "description": "Simple starter configuration",
            "folders": ["Notes", "Archive"],
        },
        "custom": {
            "name": "Custom",
            "description": "Empty configuration for custom setup",
            "folders": [],
        },
    }

    if output_format == "json":
        print(json.dumps(methodology_info, indent=2))
        return 0

    print(f"\n{COLOR_BOLD}Available Methodologies{COLOR_RESET}")
    print("=" * 60)

    for method_id in METHODOLOGIES:
        info = methodology_info.get(method_id, {})
        name = info.get("name", method_id)
        desc = info.get("description", "")
        folders = info.get("folders", [])

        print(f"\n{COLOR_CYAN}{name}{COLOR_RESET} ({method_id})")
        print(f"  {desc}")
        if folders:
            print(f"  {COLOR_DIM}Folders: {', '.join(folders)}{COLOR_RESET}")

    print(f"\n{COLOR_BOLD}Usage:{COLOR_RESET}")
    print("  obsidian:config create --methodology <name>")
    print()
    return 0


def cmd_create(
    vault_path: Path,
    methodology: str = "lyt-ace",
    force: bool = False,
) -> int:
    """Create default settings.

    Args:
        vault_path: Path to vault
        methodology: Methodology to use
        force: Overwrite existing settings

    Returns:
        Exit code
    """
    if methodology not in METHODOLOGIES:
        print(f"{COLOR_RED}Invalid methodology: {methodology}{COLOR_RESET}")
        print(f"Available: {', '.join(METHODOLOGIES)}")
        return 1

    settings_path = vault_path / ".claude" / "settings.yaml"

    if settings_path.exists() and not force:
        print(f"{COLOR_YELLOW}Settings already exist: {settings_path}{COLOR_RESET}")
        print(f"Use {COLOR_CYAN}--force{COLOR_RESET} to overwrite.")
        return 1

    if settings_path.exists():
        backup_path = create_backup(vault_path)
        if backup_path:
            print(f"{COLOR_GREEN}Backup created: {backup_path}{COLOR_RESET}")

    new_path = create_default_settings(vault_path, methodology=methodology)
    print(f"{COLOR_GREEN}Created settings: {new_path}{COLOR_RESET}")
    print(f"Methodology: {COLOR_BOLD}{methodology}{COLOR_RESET}")

    return 0


def cmd_diff(vault_path: Path) -> int:
    """Show difference from defaults.

    Args:
        vault_path: Path to vault

    Returns:
        Exit code
    """
    changes = diff_settings(vault_path)

    print(f"\n{COLOR_BOLD}Configuration Changes{COLOR_RESET}")
    print("=" * 50)

    if not changes:
        print(f"\n{COLOR_GREEN}No changes from defaults.{COLOR_RESET}\n")
        return 0

    print()
    for change in changes:
        if change.startswith("+"):
            print(f"  {COLOR_GREEN}{change}{COLOR_RESET}")
        elif change.startswith("-"):
            print(f"  {COLOR_RED}{change}{COLOR_RESET}")
        elif change.startswith("~"):
            print(f"  {COLOR_YELLOW}{change}{COLOR_RESET}")
        else:
            print(f"  {change}")

    print()
    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian Configuration Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  (none)           Show current configuration (same as 'show')
  show             Show detailed configuration
  edit             Edit settings in system editor
  validate         Validate configuration structure
  methodologies    List available methodologies
  create           Create default settings
  diff             Show difference from defaults

Examples:
  %(prog)s --vault /path/to/vault
  %(prog)s --vault . show --verbose
  %(prog)s --vault . validate --format json
  %(prog)s --vault . create --methodology para
        """,
    )

    parser.add_argument(
        "--vault",
        type=Path,
        default=Path.cwd(),
        help="Path to vault (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format (default: text)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # show
    show_parser = subparsers.add_parser("show", help="Show configuration")
    show_parser.add_argument("--verbose", "-v", action="store_true", help="Show all details")

    # edit
    subparsers.add_parser("edit", help="Edit settings in editor")

    # validate
    subparsers.add_parser("validate", help="Validate configuration")

    # methodologies
    subparsers.add_parser("methodologies", help="List methodologies")

    # create
    create_parser = subparsers.add_parser("create", help="Create default settings")
    create_parser.add_argument(
        "--methodology",
        "-m",
        default="lyt-ace",
        choices=METHODOLOGIES,
        help="Methodology to use",
    )
    create_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing settings",
    )

    # diff
    subparsers.add_parser("diff", help="Show difference from defaults")

    args = parser.parse_args()

    # Route to appropriate handler
    if args.command is None or args.command == "show":
        verbose = getattr(args, "verbose", False)
        return cmd_show(args.vault, args.format, verbose)
    elif args.command == "edit":
        return cmd_edit(args.vault)
    elif args.command == "validate":
        return cmd_validate(args.vault, args.format)
    elif args.command == "methodologies":
        return cmd_methodologies(args.format)
    elif args.command == "create":
        return cmd_create(args.vault, args.methodology, args.force)
    elif args.command == "diff":
        return cmd_diff(args.vault)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
