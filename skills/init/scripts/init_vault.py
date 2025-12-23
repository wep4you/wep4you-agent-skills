#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Vault Initializer

Creates a new Obsidian vault with a chosen PKM methodology and configuration files.

Usage:
    # Interactive mode (prompts for methodology)
    uv run init_vault.py --vault /path/to/vault

    # Flag-based mode (specify methodology)
    uv run init_vault.py --vault /path/to/vault --methodology lyt-ace

    # Dry-run mode (show what would be created)
    uv run init_vault.py --vault /path/to/vault --methodology para --dry-run
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

# Methodology definitions with folder structures and descriptions
METHODOLOGIES: dict[str, dict[str, Any]] = {
    "lyt-ace": {
        "name": "LYT + ACE Framework",
        "description": "Linking Your Thinking combined with Atlas/Calendar/Efforts structure",
        "folders": [
            "Atlas/Maps",
            "Atlas/Dots",
            "Atlas/Sources",
            "Calendar/Daily",
            "Efforts/Projects",
            "Efforts/Areas",
        ],
        "default_type_rules": {
            "Atlas/Maps/": "map",
            "Atlas/Dots/": "dot",
            "Atlas/Sources/": "source",
            "Calendar/Daily/": "daily",
            "Efforts/Projects/": "project",
            "Efforts/Areas/": "area",
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
        ],
        "default_type_rules": {
            "Projects/": "project",
            "Areas/": "area",
            "Resources/": "resource",
            "Archives/": "archive",
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
        ],
        "default_type_rules": {
            "Permanent/": "permanent",
            "Literature/": "literature",
            "Fleeting/": "fleeting",
            "References/": "reference",
        },
    },
    "minimal": {
        "name": "Minimal",
        "description": "Simple folder structure for getting started",
        "folders": [
            "Notes",
            "Daily",
        ],
        "default_type_rules": {
            "Notes/": "note",
            "Daily/": "daily",
        },
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
            print(f"  Created: {folder_path}")

    # Create system folders
    system_folders = [".obsidian", ".claude/config"]
    for folder in system_folders:
        folder_path = vault_path / folder
        if dry_run:
            print(f"  [DRY RUN] Would create: {folder_path}")
        else:
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {folder_path}")


def create_config_files(vault_path: Path, methodology: str, dry_run: bool = False) -> None:
    """Create configuration files for the vault.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        dry_run: If True, only print what would be created
    """
    method_config = METHODOLOGIES[methodology]
    config_dir = vault_path / ".claude" / "config"

    # 1. Create validator.yaml
    validator_config = {
        "exclude_paths": [
            "+/",  # Inbox
            "x/",  # System files
            ".obsidian/",
            ".claude/",
        ],
        "exclude_files": [
            "Home.md",
            "README.md",
        ],
        "type_rules": method_config["default_type_rules"],
        "auto_fix": {
            "empty_types": True,
            "daily_links": True,
            "wikilink_quotes": True,
            "title_properties": True,
        },
    }

    # 2. Create frontmatter.yaml (property definitions)
    frontmatter_config = {
        "properties": {
            "type": {
                "description": "Note type classification",
                "type": "text",
                "required": True,
            },
            "up": {
                "description": "Parent note link",
                "type": "wikilink",
                "required": True,
            },
            "created": {
                "description": "Creation date",
                "type": "date",
                "required": True,
            },
            "daily": {
                "description": "Daily note link",
                "type": "wikilink",
                "required": True,
            },
            "collection": {
                "description": "Collection classification",
                "type": "text",
                "required": False,
            },
            "related": {
                "description": "Related notes",
                "type": "multitext",
                "required": False,
            },
        },
    }

    # 3. Create note-types.yaml (note type definitions)
    # Extract unique note types from type_rules
    note_types = set(method_config["default_type_rules"].values())
    note_types_config = {
        "note_types": {
            note_type: {
                "description": f"{note_type.capitalize()} note",
                "template": None,  # Can be customized later
            }
            for note_type in sorted(note_types)
        },
    }

    # Write config files
    configs = {
        "validator.yaml": validator_config,
        "frontmatter.yaml": frontmatter_config,
        "note-types.yaml": note_types_config,
    }

    print("\nCreating configuration files...")

    # Ensure config directory exists
    if not dry_run:
        config_dir.mkdir(parents=True, exist_ok=True)

    for filename, config_data in configs.items():
        config_path = config_dir / filename
        if dry_run:
            print(f"  [DRY RUN] Would create: {config_path}")
            print("  [DRY RUN] Content preview:")
            print(yaml.dump(config_data, indent=2, default_flow_style=False))
        else:
            config_path.write_text(yaml.dump(config_data, indent=2, default_flow_style=False))
            print(f"  Created: {config_path}")


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

Vault configuration is stored in `.claude/config/`:
- `validator.yaml` - Frontmatter validation rules
- `frontmatter.yaml` - Property definitions
- `note-types.yaml` - Note type definitions

## Validation

To validate this vault, run:

```bash
uv run skills/validate/scripts/validator.py --vault . --mode report
```

To auto-fix issues:

```bash
uv run skills/validate/scripts/validator.py --vault . --mode auto
```
"""

    if dry_run:
        print(f"\n[DRY RUN] Would create: {readme_path}")
        print(f"[DRY RUN] Content:\n{content}")
    else:
        readme_path.write_text(content)
        print(f"\nCreated: {readme_path}")


def init_vault(vault_path: Path, methodology: Optional[str] = None, dry_run: bool = False) -> None:
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

    print(f"\nInitializing vault at: {vault_path}")
    print(f"Methodology: {METHODOLOGIES[methodology]['name']}")

    if dry_run:
        print("\n*** DRY RUN MODE - No files will be created ***\n")

    # Create folder structure
    create_folder_structure(vault_path, methodology, dry_run)

    # Create config files
    create_config_files(vault_path, methodology, dry_run)

    # Create README
    create_readme(vault_path, methodology, dry_run)

    print("\n✓ Vault initialization complete!")
    if not dry_run:
        print(f"\nYour vault is ready at: {vault_path}")
        print("\nNext steps:")
        print("  1. Open the vault in Obsidian")
        print("  2. Start creating notes based on your chosen methodology")
        print("  3. Run validation to check frontmatter: /obsidian:validate")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize an Obsidian vault with a PKM methodology"
    )
    parser.add_argument(
        "--vault",
        type=Path,
        required=True,
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

    try:
        init_vault(args.vault, args.methodology, args.dry_run)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
