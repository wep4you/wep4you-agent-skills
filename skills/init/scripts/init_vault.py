#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Vault Initializer

Creates a new Obsidian vault with a chosen PKM methodology and settings.yaml configuration.

Usage:
    # Interactive mode (prompts for methodology)
    uv run init_vault.py --vault /path/to/vault

    # Flag-based mode (specify methodology)
    uv run init_vault.py --vault /path/to/vault --methodology lyt-ace

    # Dry-run mode (show what would be created)
    uv run init_vault.py --vault /path/to/vault --methodology para --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# Methodology definitions with folder structures, note types, and descriptions
METHODOLOGIES: dict[str, dict[str, Any]] = {
    "lyt-ace": {
        "name": "LYT + ACE Framework",
        "description": "Linking Your Thinking combined with Atlas/Calendar/Efforts structure",
        "folders": [
            "Atlas/Maps",
            "Atlas/Dots",
            "Atlas/Sources",
            "Calendar/daily",
            "Efforts/Projects",
            "Efforts/Areas",
            "+",  # Inbox
            "x/templates",  # System
        ],
        "core_properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        "note_types": {
            "map": {
                "description": "Map of Content - Overview and navigation notes",
                "folder_hints": ["Atlas/Maps/"],
                "properties": {"additional_required": [], "optional": ["description"]},
                "validation": {"allow_empty_up": False, "require_daily_link": True},
                "icon": "map",
            },
            "dot": {
                "description": "Dot notes - Atomic concepts and ideas",
                "folder_hints": ["Atlas/Dots/"],
                "properties": {"additional_required": [], "optional": []},
                "validation": {"allow_empty_up": False, "require_daily_link": True},
                "icon": "circle",
            },
            "source": {
                "description": "Source notes - External references and citations",
                "folder_hints": ["Atlas/Sources/"],
                "properties": {"additional_required": ["author", "url"], "optional": ["published"]},
                "validation": {"allow_empty_up": False, "require_daily_link": True},
                "icon": "book",
            },
            "project": {
                "description": "Project notes - Defined outcomes with deadlines",
                "folder_hints": ["Efforts/Projects/"],
                "properties": {
                    "additional_required": ["status"],
                    "optional": ["deadline", "priority"],
                },
                "validation": {
                    "allow_empty_up": False,
                    "require_daily_link": True,
                    "require_status": True,
                },
                "icon": "target",
            },
            "area": {
                "description": "Area notes - Ongoing responsibilities",
                "folder_hints": ["Efforts/Areas/"],
                "properties": {"additional_required": [], "optional": ["review_frequency"]},
                "validation": {"allow_empty_up": False, "require_daily_link": True},
                "icon": "home",
            },
            "daily": {
                "description": "Daily notes - Date-based journal entries",
                "folder_hints": ["Calendar/daily/"],
                "properties": {"additional_required": [], "optional": ["mood", "weather"]},
                "validation": {"allow_empty_up": True, "require_daily_link": True},
                "icon": "calendar",
            },
        },
        "folder_structure": {
            "inbox": "+/",
            "system": "x/",
            "templates": "x/templates/",
            "maps": "Atlas/Maps/",
            "knowledge": ["Atlas/Dots/", "Atlas/Sources/"],
            "efforts": ["Efforts/Projects/", "Efforts/Areas/"],
            "calendar": "Calendar/daily/",
        },
        "up_links": {
            "Atlas/Dots/": "[[Atlas/Maps/Dots]]",
            "Atlas/Sources/": "[[Atlas/Maps/Sources]]",
            "Efforts/Projects/": "[[Atlas/Maps/Projects]]",
            "Efforts/Areas/": "[[Atlas/Maps/Areas]]",
            "Calendar/daily/": "[[Atlas/Maps/Calendar]]",
        },
    },
    "para": {
        "name": "PARA Method",
        "description": "Tiago Forte's Projects, Areas, Resources, Archives system",
        "folders": [
            "Projects",
            "Areas",
            "Resources",
            "Archives",
            "+",  # Inbox
        ],
        "core_properties": ["type", "up", "created", "tags"],
        "note_types": {
            "project": {
                "description": "Active projects with defined outcomes",
                "folder_hints": ["Projects/"],
                "properties": {
                    "additional_required": ["status"],
                    "optional": ["deadline", "priority"],
                },
                "validation": {"allow_empty_up": False},
                "icon": "target",
            },
            "area": {
                "description": "Areas of responsibility",
                "folder_hints": ["Areas/"],
                "properties": {"additional_required": [], "optional": ["review_frequency"]},
                "validation": {"allow_empty_up": False},
                "icon": "home",
            },
            "resource": {
                "description": "Reference materials and resources",
                "folder_hints": ["Resources/"],
                "properties": {"additional_required": [], "optional": ["source"]},
                "validation": {"allow_empty_up": True},
                "icon": "book",
            },
            "archive": {
                "description": "Completed or inactive items",
                "folder_hints": ["Archives/"],
                "properties": {"additional_required": [], "optional": ["archived_date"]},
                "validation": {"allow_empty_up": True},
                "icon": "archive",
            },
        },
        "folder_structure": {
            "inbox": "+/",
            "projects": "Projects/",
            "areas": "Areas/",
            "resources": "Resources/",
            "archives": "Archives/",
        },
        "up_links": {
            "Projects/": "[[Projects]]",
            "Areas/": "[[Areas]]",
            "Resources/": "[[Resources]]",
            "Archives/": "[[Archives]]",
        },
    },
    "zettelkasten": {
        "name": "Zettelkasten",
        "description": "Traditional slip-box system with permanent, literature, and fleeting notes",
        "folders": [
            "Permanent",
            "Literature",
            "Fleeting",
            "References",
            "+",  # Inbox
        ],
        "core_properties": ["type", "up", "created", "tags", "related"],
        "note_types": {
            "permanent": {
                "description": "Permanent notes - Your own ideas and insights",
                "folder_hints": ["Permanent/"],
                "properties": {"additional_required": [], "optional": []},
                "validation": {"allow_empty_up": False},
                "icon": "file-text",
            },
            "literature": {
                "description": "Literature notes - Notes from reading",
                "folder_hints": ["Literature/"],
                "properties": {"additional_required": ["source"], "optional": ["author", "page"]},
                "validation": {"allow_empty_up": True},
                "icon": "book-open",
            },
            "fleeting": {
                "description": "Fleeting notes - Quick captures to process",
                "folder_hints": ["Fleeting/"],
                "properties": {"additional_required": [], "optional": []},
                "validation": {"allow_empty_up": True},
                "icon": "zap",
            },
            "reference": {
                "description": "Reference notes - External sources",
                "folder_hints": ["References/"],
                "properties": {"additional_required": ["url"], "optional": ["author"]},
                "validation": {"allow_empty_up": True},
                "icon": "link",
            },
        },
        "folder_structure": {
            "inbox": "+/",
            "permanent": "Permanent/",
            "literature": "Literature/",
            "fleeting": "Fleeting/",
            "references": "References/",
        },
        "up_links": {
            "Permanent/": "[[Index]]",
            "Literature/": "[[Literature Index]]",
        },
    },
    "minimal": {
        "name": "Minimal",
        "description": "Simple folder structure for getting started",
        "folders": [
            "Notes",
            "Daily",
            "+",  # Inbox
        ],
        "core_properties": ["type", "created", "tags"],
        "note_types": {
            "note": {
                "description": "General notes",
                "folder_hints": ["Notes/"],
                "properties": {"additional_required": [], "optional": []},
                "validation": {"allow_empty_up": True},
                "icon": "file",
            },
            "daily": {
                "description": "Daily journal entries",
                "folder_hints": ["Daily/"],
                "properties": {"additional_required": [], "optional": ["mood"]},
                "validation": {"allow_empty_up": True},
                "icon": "calendar",
            },
        },
        "folder_structure": {
            "inbox": "+/",
            "notes": "Notes/",
            "daily": "Daily/",
        },
        "up_links": {},
    },
}


def print_methodologies() -> None:
    """Print available methodologies with descriptions."""
    print("\nAvailable methodologies:\n")
    for key, method in METHODOLOGIES.items():
        print(f"  {key:15} - {method['name']}")
        print(f"  {' ' * 17} {method['description']}")
        print(f"  {' ' * 17} Folders: {', '.join(method['folders'])}\n")


def choose_methodology_interactive() -> str:
    """Interactively choose a methodology."""
    print_methodologies()

    while True:
        choice = input("Select methodology (lyt-ace/para/zettelkasten/minimal): ").strip().lower()
        if choice in METHODOLOGIES:
            return choice
        print(f"Invalid choice: {choice}. Please try again.")


def create_folder_structure(vault_path: Path, methodology: str, dry_run: bool = False) -> None:
    """Create folder structure based on methodology.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key (e.g., 'lyt-ace', 'para')
        dry_run: If True, only print what would be created without creating
    """
    if methodology not in METHODOLOGIES:
        available = ", ".join(METHODOLOGIES.keys())
        raise ValueError(f"Unknown methodology: {methodology}. Available: {available}")

    method_config = METHODOLOGIES[methodology]
    folders = method_config["folders"]

    print(f"\nCreating {method_config['name']} folder structure...")

    for folder in folders:
        folder_path = vault_path / folder
        if dry_run:
            print(f"  [DRY RUN] Would create: {folder_path}")
        else:
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {folder_path}")

    # Create system folders
    system_folders = [".obsidian", ".claude", ".claude/logs"]
    for folder in system_folders:
        folder_path = vault_path / folder
        if dry_run:
            print(f"  [DRY RUN] Would create: {folder_path}")
        else:
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {folder_path}")


def build_settings_yaml(methodology: str) -> dict[str, Any]:
    """Build settings.yaml content for a methodology.

    Args:
        methodology: Methodology key

    Returns:
        Dictionary representing the settings.yaml content
    """
    method_config = METHODOLOGIES[methodology]

    settings: dict[str, Any] = {
        "version": "1.0",
        "methodology": methodology,
        "core_properties": method_config["core_properties"],
        "note_types": method_config["note_types"],
        "validation": {
            "require_core_properties": True,
            "allow_empty_properties": ["tags", "collection", "related"],
            "strict_types": True,
            "check_templates": True,
            "check_up_links": True,
            "check_inbox_no_frontmatter": True,
        },
        "folder_structure": method_config.get("folder_structure", {}),
        "up_links": method_config.get("up_links", {}),
        "exclude": {
            "paths": ["+/", "x/", ".obsidian/", ".claude/", ".git/"],
            "files": ["Home.md", "README.md"],
        },
        "formats": {
            "date": "YYYY-MM-DD",
            "daily_link": "[[{date}]]",
            "wikilink_quoted": True,
        },
        "logging": {
            "enabled": True,
            "format": "jsonl",
            "directory": ".claude/logs/",
            "retention_days": 30,
        },
    }

    return settings


def create_settings_yaml(vault_path: Path, methodology: str, dry_run: bool = False) -> None:
    """Create settings.yaml for the vault.

    This is the PRIMARY source of truth for all vault configuration.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        dry_run: If True, only print what would be created
    """
    settings = build_settings_yaml(methodology)
    settings_path = vault_path / ".claude" / "settings.yaml"

    # Build YAML with header comments
    header = """# .claude/settings.yaml - Obsidian Vault Settings
# This is the PRIMARY source of truth for all validation and configuration.
# Generated by init-skill. Manual editing supported.
#
# IMPORTANT: All skills read from this file. Changes here affect:
# - Validation rules
# - Note type definitions
# - Folder structure expectations
# - Template generation

"""

    yaml_content = yaml.dump(
        settings, default_flow_style=False, sort_keys=False, allow_unicode=True
    )

    print("\nCreating settings.yaml (primary configuration)...")

    if dry_run:
        print(f"  [DRY RUN] Would create: {settings_path}")
        print("  [DRY RUN] Content preview:")
        print(header)
        print(yaml_content)
    else:
        # Ensure directory exists
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(header + yaml_content)
        print(f"  ✓ Created: {settings_path}")


def create_readme(vault_path: Path, methodology: str, dry_run: bool = False) -> None:
    """Create a README.md file in the vault root.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        dry_run: If True, only print what would be created
    """
    method_config = METHODOLOGIES[methodology]
    readme_path = vault_path / "README.md"

    content = f"""# {vault_path.name}

This Obsidian vault uses the **{method_config["name"]}** methodology.

## Methodology

{method_config["description"]}

## Folder Structure

"""
    for folder in method_config["folders"]:
        content += f"- `{folder}/`\n"

    content += """
## Configuration

Vault configuration is stored in `.claude/settings.yaml`.

This is the **primary source of truth** for:
- Core frontmatter properties
- Note type definitions
- Validation rules
- Folder structure

## Validation

To validate this vault, run:

```bash
/obsidian:validate
```

Or via CLI:

```bash
uv run skills/validate/scripts/validator.py --vault . --mode report
```

## Managing Settings

View current settings:
```bash
/obsidian:config-show
```

Validate settings:
```bash
/obsidian:config-validate
```
"""

    if dry_run:
        print(f"\n[DRY RUN] Would create: {readme_path}")
    else:
        readme_path.write_text(content)
        print(f"\n✓ Created: {readme_path}")


def create_home_note(vault_path: Path, methodology: str, dry_run: bool = False) -> None:
    """Create a Home.md file in the vault root.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        dry_run: If True, only print what would be created
    """
    method_config = METHODOLOGIES[methodology]
    home_path = vault_path / "Home.md"

    content = f"""---
type: home
created: "{{{{date}}}}"
---

# Home

Welcome to your **{method_config["name"]}** vault!

## Quick Navigation

"""
    # Add links based on methodology folders
    for folder in method_config["folders"]:
        if not folder.startswith("+") and not folder.startswith("x"):
            folder_name = folder.split("/")[-1] if "/" in folder else folder
            content += f"- [[{folder_name}]]\n"

    content += """
## Getting Started

1. Start capturing ideas in the `+/` inbox
2. Process inbox items into appropriate folders
3. Run `/obsidian:validate` to check your notes

## Configuration

Your vault settings are in `.claude/settings.yaml`.
"""

    if dry_run:
        print(f"[DRY RUN] Would create: {home_path}")
    else:
        home_path.write_text(content)
        print(f"✓ Created: {home_path}")


def init_vault(vault_path: Path, methodology: str | None = None, dry_run: bool = False) -> None:
    """Initialize an Obsidian vault with chosen methodology.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key (if None, prompt interactively)
        dry_run: If True, only show what would be created
    """
    # Ensure vault path exists
    if not dry_run:
        vault_path.mkdir(parents=True, exist_ok=True)

    # Choose methodology
    if methodology is None:
        methodology = choose_methodology_interactive()

    print(f"\n{'=' * 60}")
    print(f"Initializing vault at: {vault_path}")
    print(f"Methodology: {METHODOLOGIES[methodology]['name']}")
    print(f"{'=' * 60}")

    if dry_run:
        print("\n*** DRY RUN MODE - No files will be created ***\n")

    # Create folder structure
    create_folder_structure(vault_path, methodology, dry_run)

    # Create settings.yaml (PRIMARY configuration)
    create_settings_yaml(vault_path, methodology, dry_run)

    # Create README
    create_readme(vault_path, methodology, dry_run)

    # Create Home note
    create_home_note(vault_path, methodology, dry_run)

    print(f"\n{'=' * 60}")
    print("✓ Vault initialization complete!")
    print(f"{'=' * 60}")

    if not dry_run:
        print(f"\nYour vault is ready at: {vault_path}")
        print("\nNext steps:")
        print("  1. Open the vault in Obsidian")
        print("  2. Start creating notes based on your chosen methodology")
        print("  3. Run validation: /obsidian:validate")
        print("  4. View settings: /obsidian:config-show")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize an Obsidian vault with a PKM methodology"
    )
    parser.add_argument(
        "--vault",
        type=Path,
        help="Path to the vault (will be created if doesn't exist)",
    )
    parser.add_argument(
        "--methodology",
        choices=list(METHODOLOGIES.keys()),
        help="Methodology to use (if not specified, will prompt interactively)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating files",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available methodologies and exit",
    )

    args = parser.parse_args()

    if args.list:
        print_methodologies()
        return 0

    # Vault is required if not listing
    if not args.vault:
        parser.error("the following arguments are required: --vault")

    try:
        init_vault(args.vault, args.methodology, args.dry_run)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
