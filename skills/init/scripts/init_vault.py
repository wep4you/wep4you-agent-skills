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
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WizardConfig:
    """Configuration collected from the wizard flow."""

    methodology: str
    note_types: dict[str, dict[str, Any]]
    core_properties: list[str]
    mandatory_properties: list[str] = field(default_factory=list)
    optional_properties: list[str] = field(default_factory=list)
    custom_properties: list[str] = field(default_factory=list)
    create_samples: bool = True
    reset_vault: bool = False

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


# =============================================================================
# Vault Detection & Reset Functions
# =============================================================================


def detect_existing_vault(vault_path: Path) -> dict[str, Any]:
    """Detect existing vault state.

    Args:
        vault_path: Path to check

    Returns:
        Dictionary with vault state information
    """
    if not vault_path.exists():
        return {
            "exists": False,
            "has_obsidian": False,
            "has_claude_config": False,
            "has_content": False,
            "folder_count": 0,
            "file_count": 0,
        }

    has_obsidian = (vault_path / ".obsidian").exists()
    has_claude = (vault_path / ".claude").exists()

    # Count folders and files (excluding hidden)
    folders = [f for f in vault_path.iterdir() if f.is_dir() and not f.name.startswith(".")]
    files = [f for f in vault_path.iterdir() if f.is_file() and not f.name.startswith(".")]

    return {
        "exists": True,
        "has_obsidian": has_obsidian,
        "has_claude_config": has_claude,
        "has_content": len(folders) > 0 or len(files) > 0,
        "folder_count": len(folders),
        "file_count": len(files),
    }


def prompt_existing_vault_action(detection: dict[str, Any]) -> str:
    """Ask user what to do with existing vault.

    Args:
        detection: Result from detect_existing_vault()

    Returns:
        'continue' | 'reset' | 'abort'
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " ⚠️  EXISTING VAULT DETECTED".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")

    if detection["has_obsidian"]:
        line = "│   • Obsidian configuration (.obsidian/)"
        print(line.ljust(59) + "│")
    if detection["has_claude_config"]:
        line = "│   • Claude configuration (.claude/)"
        print(line.ljust(59) + "│")
    if detection["has_content"]:
        folders = detection["folder_count"]
        files = detection["file_count"]
        line = f"│   • Content: {folders} folders, {files} files"
        print(line.ljust(59) + "│")

    print("├" + "─" * 58 + "┤")
    print("│" + " What would you like to do?".ljust(58) + "│")
    print("│".ljust(59) + "│")
    print("│   [a] Abort    - Cancel (default, press Enter)".ljust(59) + "│")
    print("│   [c] Continue - Add new structure to existing vault".ljust(59) + "│")
    print("│   [r] Reset    - Delete all content and start fresh".ljust(59) + "│")
    print("└" + "─" * 58 + "┘")

    while True:
        choice = input("\nYour choice [a]: ").strip().lower()
        # Default is abort (empty input)
        if choice == "" or choice in ("a", "abort"):
            return "abort"
        if choice in ("c", "continue"):
            return "continue"
        if choice in ("r", "reset"):
            print()
            print("  ⚠️  WARNING: This will permanently delete all vault content!")
            confirm = input("  Type 'yes' to confirm reset: ")
            if confirm.strip().lower() == "yes":
                return "reset"
            print("  Reset cancelled.")
            continue
        print("  Invalid choice. Please enter 'a', 'c', or 'r'.")


def reset_vault(vault_path: Path, keep_obsidian: bool = True) -> None:
    """Reset vault to clean state.

    Args:
        vault_path: Path to the vault
        keep_obsidian: If True, keep .obsidian folder (preserves Obsidian settings)
    """
    print("\nResetting vault...")

    for item in vault_path.iterdir():
        # Skip .obsidian if keeping it
        if keep_obsidian and item.name == ".obsidian":
            print(f"  - Keeping: {item.name}/")
            continue

        if item.is_dir():
            shutil.rmtree(item)
            print(f"  - Removed: {item.name}/")
        else:
            item.unlink()
            print(f"  - Removed: {item.name}")

    print("  ✓ Vault reset complete")


# =============================================================================
# Wizard Step Functions
# =============================================================================


def wizard_step_quick_or_custom() -> bool:
    """Ask user whether to use quick setup or customize.

    Returns:
        True for quick setup (use defaults), False for custom configuration
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 2: Setup Mode".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")
    print("│".ljust(59) + "│")
    print("│   [q] Quick Setup  - Use defaults (press Enter)".ljust(59) + "│")
    print("│   [c] Custom Setup - Configure note types & properties".ljust(59) + "│")
    print("│".ljust(59) + "│")
    print("└" + "─" * 58 + "┘")

    while True:
        choice = input("\nYour choice [q]: ").strip().lower()
        if choice == "" or choice in ("q", "quick"):
            return True
        if choice in ("c", "custom"):
            return False
        print("  Invalid choice. Please enter 'q' or 'c'.")


def wizard_step_note_types(methodology: str) -> dict[str, dict[str, Any]]:
    """Configure which note types to enable.

    Args:
        methodology: Selected methodology key

    Returns:
        Dictionary of enabled note types with their configurations
    """
    method_config = METHODOLOGIES[methodology]
    available_types = method_config["note_types"]

    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 3: Note Types".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Available note types:".ljust(58) + "│")
    print("│".ljust(59) + "│")

    for i, (type_name, type_config) in enumerate(available_types.items(), 1):
        desc = type_config["description"][:40]
        line = f"│   {i}. {type_name:12} {desc}"
        print(line.ljust(59) + "│")

    print("│".ljust(59) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Press Enter to keep all, or enter numbers to disable".ljust(58) + "│")
    print("│" + " Example: '1 3' disables types 1 and 3".ljust(58) + "│")
    print("└" + "─" * 58 + "┘")

    choice = input("\nDisable types [none]: ").strip()

    if not choice:
        print("  ✓ Keeping all note types enabled")
        return dict(available_types)

    # Parse which types to toggle
    enabled = dict(available_types)
    try:
        indices = [int(x) for x in choice.split()]
        type_names = list(available_types.keys())
        for idx in indices:
            if 1 <= idx <= len(type_names):
                type_name = type_names[idx - 1]
                if type_name in enabled:
                    del enabled[type_name]
                    print(f"  ✓ Disabled: {type_name}")
    except ValueError:
        print("  Invalid input, keeping all types enabled.")

    return enabled


def wizard_step_frontmatter(
    core_properties: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """Configure frontmatter properties.

    Args:
        core_properties: Default core properties for the methodology

    Returns:
        Tuple of (mandatory, optional, custom) property lists
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 4: Frontmatter Properties".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Core properties (all mandatory by default):".ljust(58) + "│")
    print("│".ljust(59) + "│")

    for i, prop in enumerate(core_properties, 1):
        line = f"│   {i}. {prop}"
        print(line.ljust(59) + "│")

    print("│".ljust(59) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Enter numbers to make optional, or press Enter to skip".ljust(58) + "│")
    print("└" + "─" * 58 + "┘")

    choice = input("\nMake optional [none]: ").strip()

    mandatory = list(core_properties)
    optional: list[str] = []

    if choice:
        try:
            indices = [int(x) for x in choice.split()]
            for idx in indices:
                if 1 <= idx <= len(core_properties):
                    prop = core_properties[idx - 1]
                    if prop in mandatory:
                        mandatory.remove(prop)
                        optional.append(prop)
                        print(f"  ✓ Made optional: {prop}")
        except ValueError:
            print("  Invalid input, keeping all mandatory.")

    # Ask for custom properties
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " Custom Properties (optional)".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Add your own properties (comma-separated)".ljust(58) + "│")
    print("│" + " Example: priority, due_date, project".ljust(58) + "│")
    print("└" + "─" * 58 + "┘")

    custom_input = input("\nCustom properties [none]: ").strip()

    custom: list[str] = []
    if custom_input:
        custom = [p.strip() for p in custom_input.split(",") if p.strip()]
        print(f"  ✓ Added: {', '.join(custom)}")

    return mandatory, optional, custom


def wizard_step_confirm(config: WizardConfig) -> bool:
    """Show summary and ask for confirmation.

    Args:
        config: The collected wizard configuration

    Returns:
        True to proceed, False to go back
    """
    method = METHODOLOGIES[config.methodology]

    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 5: Confirm Configuration".ljust(58) + "│")
    print("╞" + "═" * 58 + "╡")

    line = f"│   Methodology:  {method['name']}"
    print(line.ljust(59) + "│")

    line = f"│   Note Types:   {', '.join(config.note_types.keys())}"
    if len(line) > 58:
        line = line[:55] + "..."
    print(line.ljust(59) + "│")

    line = f"│   Mandatory:    {', '.join(config.mandatory_properties) or '(none)'}"
    if len(line) > 58:
        line = line[:55] + "..."
    print(line.ljust(59) + "│")

    line = f"│   Optional:     {', '.join(config.optional_properties) or '(none)'}"
    print(line.ljust(59) + "│")

    line = f"│   Custom:       {', '.join(config.custom_properties) or '(none)'}"
    print(line.ljust(59) + "│")

    line = f"│   Sample Notes: {'Yes' if config.create_samples else 'No'}"
    print(line.ljust(59) + "│")

    print("├" + "─" * 58 + "┤")
    print("│" + " [y] Proceed (default)   [n] Start over".ljust(58) + "│")
    print("└" + "─" * 58 + "┘")

    while True:
        choice = input("\nProceed? [y]: ").strip().lower()
        if choice == "" or choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("  Please enter 'y' or 'n'.")


def wizard_full_flow(vault_path: Path) -> WizardConfig | None:
    """Run the complete interactive wizard.

    Args:
        vault_path: Path to the vault being initialized

    Returns:
        WizardConfig with all user choices, or None if aborted
    """
    # Welcome banner
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " OBSIDIAN VAULT INITIALIZATION WIZARD".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print(f"  Vault: {vault_path}")

    # STEP 0: Check for existing vault FIRST (before anything else)
    detection = detect_existing_vault(vault_path)
    if detection["exists"] and detection["has_content"]:
        action = prompt_existing_vault_action(detection)
        if action == "abort":
            print()
            print("  Initialization cancelled.")
            return None
        if action == "reset":
            reset_vault(vault_path, keep_obsidian=True)

    # STEP 1: Choose methodology
    methodology = wizard_step_methodology()
    method_config = METHODOLOGIES[methodology]

    # STEP 2: Quick or custom setup
    use_defaults = wizard_step_quick_or_custom()

    if use_defaults:
        # Quick setup - use all defaults
        config = WizardConfig(
            methodology=methodology,
            note_types=dict(method_config["note_types"]),
            core_properties=list(method_config["core_properties"]),
            mandatory_properties=list(method_config["core_properties"]),
            optional_properties=[],
            custom_properties=[],
            create_samples=True,
        )
    else:
        # Custom setup
        # STEP 3: Configure note types
        note_types = wizard_step_note_types(methodology)

        # STEP 4: Configure frontmatter
        mandatory, optional, custom = wizard_step_frontmatter(method_config["core_properties"])

        config = WizardConfig(
            methodology=methodology,
            note_types=note_types,
            core_properties=list(method_config["core_properties"]),
            mandatory_properties=mandatory,
            optional_properties=optional,
            custom_properties=custom,
            create_samples=True,
        )

    # STEP 5: Confirmation
    if not wizard_step_confirm(config):
        print("\n  Restarting wizard...\n")
        return wizard_full_flow(vault_path)

    return config


def wizard_step_methodology() -> str:
    """Choose a methodology with nice formatting.

    Returns:
        Selected methodology key
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 1: Choose Methodology".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")

    methods = list(METHODOLOGIES.items())
    for i, (_key, method) in enumerate(methods, 1):
        line = f"│   {i}. {method['name']:20} {method['description'][:30]}"
        print(line.ljust(59) + "│")

    print("│".ljust(59) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Enter number (1-4) or name (lyt-ace, para, etc.)".ljust(58) + "│")
    print("└" + "─" * 58 + "┘")

    while True:
        choice = input("\nMethodology [1]: ").strip().lower()

        # Default to first option
        if choice == "":
            selected = methods[0][0]
            print(f"  ✓ Selected: {METHODOLOGIES[selected]['name']}")
            return selected

        # Try as number
        try:
            idx = int(choice)
            if 1 <= idx <= len(methods):
                selected = methods[idx - 1][0]
                print(f"  ✓ Selected: {METHODOLOGIES[selected]['name']}")
                return selected
        except ValueError:
            pass

        # Try as name
        if choice in METHODOLOGIES:
            print(f"  ✓ Selected: {METHODOLOGIES[choice]['name']}")
            return choice

        print(f"  Invalid choice: {choice}. Enter 1-{len(methods)} or name.")


# =============================================================================
# Sample Note Generation
# =============================================================================


def generate_sample_note(
    note_type: str,
    note_type_config: dict[str, Any],
    core_properties: list[str],
    methodology: str,
    up_links: dict[str, str],
) -> str:
    """Generate sample note content dynamically.

    Args:
        note_type: Type name (map, dot, source, etc.)
        note_type_config: Config with folder_hints, properties, validation
        core_properties: List of core frontmatter properties
        methodology: Selected methodology name
        up_links: UP link mappings for folders

    Returns:
        Complete markdown content with frontmatter and helpful body
    """
    today = date.today().isoformat()
    folder_hint = note_type_config.get("folder_hints", [""])[0]
    description = note_type_config.get("description", f"{note_type.title()} notes")

    # Determine up link
    up_link = up_links.get(folder_hint, "[[Home]]")

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f'type: "{note_type}"',
        f'up: "{up_link}"',
        f'created: "{today}"',
    ]

    # Add daily link if in core properties
    if "daily" in core_properties:
        frontmatter_lines.append(f'daily: "[[{today}]]"')

    # Add tags
    if "tags" in core_properties:
        frontmatter_lines.append(f"tags: [sample, {methodology}]")

    # Add collection and related if in core properties
    if "collection" in core_properties:
        frontmatter_lines.append('collection: ""')
    if "related" in core_properties:
        frontmatter_lines.append("related: []")

    # Add additional_required properties with placeholder values
    additional_required = note_type_config.get("properties", {}).get("additional_required", [])
    for prop in additional_required:
        if prop == "status":
            frontmatter_lines.append('status: "active"')
        elif prop == "author":
            frontmatter_lines.append('author: "Unknown"')
        elif prop == "url":
            frontmatter_lines.append('url: ""')
        elif prop == "source":
            frontmatter_lines.append('source: ""')
        else:
            frontmatter_lines.append(f'{prop}: ""')

    # Add optional properties (commented)
    optional_props = note_type_config.get("properties", {}).get("optional", [])
    for prop in optional_props:
        frontmatter_lines.append(f"# {prop}: ")

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    # Build body content
    type_title = note_type.replace("_", " ").title()
    body = f"""
# Getting Started with {type_title}s

Welcome to your first **{type_title}** note!

## What is a {type_title}?

{description}

## Recommended Structure

"""

    # Add type-specific structure suggestions
    if note_type == "map":
        body += """- **Overview**: Brief description of what this map covers
- **Contents**: Links to related notes organized by topic
- **Related Maps**: Links to other relevant maps
"""
    elif note_type == "dot":
        body += """- **Core Idea**: One atomic concept per note
- **Details**: Explanation and context
- **See Also**: Links to related concepts
"""
    elif note_type == "source":
        body += """- **Summary**: Key points from the source
- **Quotes**: Important quotes with page references
- **My Thoughts**: Your own reflections
"""
    elif note_type == "project":
        body += """- **Outcome**: What does "done" look like?
- **Tasks**: Actionable next steps
- **Resources**: Links to relevant materials
"""
    elif note_type == "daily":
        body += """- **Tasks**: What to accomplish today
- **Notes**: Capture thoughts and ideas
- **Reflections**: End-of-day review
"""
    else:
        body += """- **Main Content**: Your notes and ideas
- **Related**: Links to connected topics
"""

    body += """
## Tips

1. Use the `up` link to navigate to parent notes
2. Add tags to make notes discoverable
3. Link liberally to other notes

---
*This is a sample note. Feel free to edit or delete it.*

[[Home]]
"""

    return frontmatter + body


def create_sample_notes(
    vault_path: Path,
    methodology: str,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
    dry_run: bool = False,
) -> list[Path]:
    """Create sample notes for each enabled note type.

    Args:
        vault_path: Path to the vault root
        methodology: Selected methodology
        note_types: Dictionary of enabled note types
        core_properties: List of core properties
        dry_run: If True, only print what would be created

    Returns:
        List of created file paths
    """
    method_config = METHODOLOGIES[methodology]
    up_links = method_config.get("up_links", {})
    created_files: list[Path] = []

    print("\nCreating sample notes...")

    for note_type, type_config in note_types.items():
        folder_hints = type_config.get("folder_hints", [])
        if not folder_hints:
            continue

        folder = folder_hints[0].rstrip("/")
        type_title = note_type.replace("_", " ").title()

        # Special handling for daily notes
        if note_type == "daily":
            today = date.today().isoformat()
            filename = f"{today}.md"
        else:
            filename = f"Getting Started with {type_title}s.md"

        file_path = vault_path / folder / filename

        content = generate_sample_note(
            note_type, type_config, core_properties, methodology, up_links
        )

        if dry_run:
            print(f"  [DRY RUN] Would create: {file_path}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"  ✓ Created: {file_path}")
            created_files.append(file_path)

    return created_files


def show_migration_hint(has_existing_content: bool) -> None:
    """Show hint about future migration feature.

    Args:
        has_existing_content: Whether the vault had existing content
    """
    if has_existing_content:
        print("\n" + "-" * 40)
        print("NOTE: Migration Feature Coming Soon")
        print("-" * 40)
        print("Migration of existing notes to the new methodology")
        print("is planned for a future release.")
        print("Your existing content remains untouched.")


# =============================================================================
# Original Functions
# =============================================================================


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


def init_vault(
    vault_path: Path,
    methodology: str | None = None,
    dry_run: bool = False,
    use_wizard: bool = False,
    use_defaults: bool = False,
) -> None:
    """Initialize an Obsidian vault with chosen methodology.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key (if None, prompt interactively)
        dry_run: If True, only show what would be created
        use_wizard: If True, run the full interactive wizard
        use_defaults: If True, skip confirmations and use defaults
    """
    # Check for existing vault first
    detection = detect_existing_vault(vault_path)
    has_existing = detection["exists"] and detection["has_content"]

    # Ensure vault path exists
    if not dry_run:
        vault_path.mkdir(parents=True, exist_ok=True)

    # Determine configuration source
    if use_wizard and methodology is None:
        # Full wizard mode - handles everything including existing vault check
        config = wizard_full_flow(vault_path)
        if config is None:
            return  # User aborted
        methodology = config.methodology
        note_types = config.note_types
        core_properties = config.core_properties
        create_samples = config.create_samples
    else:
        # Direct mode (with or without methodology flag)
        # Handle existing vault FIRST, before methodology selection
        if has_existing and not use_defaults:
            print()
            print(f"  Vault: {vault_path}")
            action = prompt_existing_vault_action(detection)
            if action == "abort":
                print("\n  Initialization cancelled.")
                return
            if action == "reset":
                reset_vault(vault_path, keep_obsidian=True)

        # Now select methodology if not provided
        if methodology is None:
            methodology = choose_methodology_interactive()

        method_config = METHODOLOGIES[methodology]
        note_types = method_config["note_types"]
        core_properties = method_config["core_properties"]
        create_samples = True

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

    # Create sample notes
    if create_samples:
        create_sample_notes(vault_path, methodology, note_types, core_properties, dry_run)

    # Show migration hint if there was existing content
    if has_existing:
        show_migration_hint(has_existing)

    print(f"\n{'=' * 60}")
    print("Vault initialization complete!")
    print(f"{'=' * 60}")

    if not dry_run:
        print(f"\nYour vault is ready at: {vault_path}")
        print("\nNext steps:")
        print("  1. Open the vault in Obsidian")
        print("  2. Explore the sample notes in each folder")
        print("  3. Run validation: /obsidian:validate")
        print("  4. View settings: /obsidian:config-show")


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize an Obsidian vault with a PKM methodology",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick setup with defaults
  init_vault.py /path/to/vault -m lyt-ace --defaults

  # Interactive wizard
  init_vault.py /path/to/vault --wizard

  # Dry run to preview changes
  init_vault.py /path/to/vault -m para --dry-run

  # List available methodologies
  init_vault.py --list
""",
    )
    parser.add_argument(
        "vault",
        type=Path,
        nargs="?",
        help="Path to the vault (will be created if doesn't exist)",
    )
    # Keep --vault for backward compatibility
    parser.add_argument(
        "--vault",
        type=Path,
        dest="vault_legacy",
        help=argparse.SUPPRESS,  # Hidden, for backward compatibility
    )
    parser.add_argument(
        "-m", "--methodology",
        choices=list(METHODOLOGIES.keys()),
        help="Methodology to use (lyt-ace, para, zettelkasten, minimal)",
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
    parser.add_argument(
        "--wizard",
        action="store_true",
        help="Run the full interactive wizard",
    )
    parser.add_argument(
        "--defaults",
        action="store_true",
        help="Use default settings without prompts (requires --methodology)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing vault before initializing",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if vault exists and show status (no changes made)",
    )

    args = parser.parse_args()

    if args.list:
        print_methodologies()
        return 0

    # Handle backward compatibility for --vault
    vault_path = args.vault or args.vault_legacy

    # Vault is required if not listing
    if not vault_path:
        print("Error: Vault path is required.", file=sys.stderr)
        print("\nUsage: init_vault.py <vault_path> -m <methodology> [--defaults]", file=sys.stderr)
        print("       init_vault.py --list", file=sys.stderr)
        print("\nRun 'init_vault.py --help' for more options.", file=sys.stderr)
        return 1

    # STEP 1: Detect existing vault FIRST (before any interactive checks)
    detection = detect_existing_vault(vault_path)
    has_existing = detection["exists"] and detection["has_content"]

    # Handle --check flag: JSON output for Claude Code integration
    if args.check:
        import json

        if not detection["exists"]:
            status = "empty"
        elif not detection["has_content"]:
            status = "new"
        else:
            status = "existing"

        result = {
            "status": status,
            "path": str(vault_path),
            "folders": detection["folder_count"],
            "files": detection["file_count"],
            "has_obsidian": detection["has_obsidian"],
            "has_claude_config": detection["has_claude_config"],
        }
        print(json.dumps(result, indent=2))
        return 0

    # STEP 2: Check if we need interactive mode
    needs_interactive = (
        args.wizard
        or (args.methodology is None and not args.defaults)
        or (args.reset and not args.defaults)
        or (has_existing and not args.defaults)  # Existing vault needs confirmation
    )

    # STEP 3: Handle non-interactive mode with JSON output
    if needs_interactive and not is_interactive():
        import json

        result = {
            "error": "interactive_required",
            "message": "This command requires interactive input or explicit flags",
            "path": str(vault_path),
            "has_existing_content": has_existing,
            "folders": detection["folder_count"],
            "files": detection["file_count"],
            "suggestion": "Use: init_vault.py <path> -m <methodology> --defaults",
        }
        print(json.dumps(result, indent=2))
        return 0  # Not an error, just info

    # Handle reset flag
    if args.reset:
        if detection["exists"]:
            print(f"\nResetting vault at: {vault_path}")
            if is_interactive():
                confirm = input("Are you sure? This will delete content! (yes/no): ")
                if confirm.strip().lower() != "yes":
                    print("Reset cancelled.")
                    return 0
            reset_vault(vault_path, keep_obsidian=True)

    # Determine if wizard mode
    use_wizard = args.wizard or (args.methodology is None and not args.defaults)

    try:
        init_vault(
            vault_path,
            args.methodology,
            args.dry_run,
            use_wizard=use_wizard,
            use_defaults=args.defaults,
        )
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except EOFError:
        print("\nInteractive input required. Use --defaults for non-interactive mode.")
        return 1
    except KeyboardInterrupt:
        print("\n\nInitialization cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
