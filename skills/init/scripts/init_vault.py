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

# Add repository root to path for importing methodology loader
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Import methodology definitions from YAML loader
from config.methodologies.loader import METHODOLOGIES  # noqa: E402


@dataclass
class NoteTypeConfig:
    """Configuration for a single note type."""

    name: str
    description: str
    folder_hints: list[str]
    required_properties: list[str] = field(default_factory=list)
    optional_properties: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    icon: str = "file"
    is_custom: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for settings.yaml."""
        return {
            "description": self.description,
            "folder_hints": self.folder_hints,
            "properties": {
                "additional_required": self.required_properties,
                "optional": self.optional_properties,
            },
            "validation": self.validation,
            "icon": self.icon,
        }


@dataclass
class WizardConfig:
    """Configuration collected from the wizard flow."""

    methodology: str
    note_types: dict[str, dict[str, Any]]
    core_properties: list[str]
    mandatory_properties: list[str] = field(default_factory=list)
    optional_properties: list[str] = field(default_factory=list)
    custom_properties: list[str] = field(default_factory=list)
    custom_note_types: dict[str, NoteTypeConfig] = field(default_factory=dict)
    per_type_properties: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    create_samples: bool = True
    reset_vault: bool = False
    ranking_system: str = "rank"  # "rank" (1-5) or "priority" (text)
    init_git: bool = False  # Initialize git repository


# METHODOLOGIES is imported from config.methodologies.loader (see import at top)
# The definitions are loaded from YAML files in config/methodologies/

# Folders protected during vault reset (never deleted)
# Note: .git is NOT protected - reset should allow fresh git initialization
PROTECTED_FOLDERS = frozenset({".obsidian", ".github", ".vscode"})

# Folders to exclude from backups (large or regenerable)
BACKUP_EXCLUDE_FOLDERS = frozenset({".obsidian", ".git", ".github", ".vscode"})

# Files protected during vault reset (kept and updated instead of deleted)
PROTECTED_FILES = frozenset({"README.md", "AGENTS.md", "CLAUDE.md", "Home.md", ".gitignore"})

# Note types that support ranking (project-like notes)
RANKABLE_NOTE_TYPES = frozenset({"project", "area"})


def apply_ranking_system(
    note_types: dict[str, dict[str, Any]], ranking_system: str
) -> dict[str, dict[str, Any]]:
    """Apply ranking system choice to note types.

    Adds either 'rank' or 'priority' as a required property for project-like notes.

    Args:
        note_types: Dictionary of note type configurations
        ranking_system: Either "rank" (1-5 numeric) or "priority" (text)

    Returns:
        Modified note_types with ranking property added
    """
    import copy

    modified = copy.deepcopy(note_types)

    for type_name, type_config in modified.items():
        # Only apply to project-like notes
        if type_name not in RANKABLE_NOTE_TYPES:
            continue

        props = type_config.get("properties", {})
        additional_required = list(props.get("additional_required", []))
        optional = list(props.get("optional", []))

        if ranking_system == "rank":
            # Add rank as required (if not already there)
            if "rank" not in additional_required:
                additional_required.append("rank")
            # Remove priority from optional if present
            if "priority" in optional:
                optional.remove("priority")
        else:
            # Move priority from optional to required
            if "priority" not in additional_required:
                additional_required.append("priority")
            if "priority" in optional:
                optional.remove("priority")

        # Update the config
        if "properties" not in type_config:
            type_config["properties"] = {}
        type_config["properties"]["additional_required"] = additional_required
        type_config["properties"]["optional"] = optional

    return modified


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

    # Try to read current methodology from settings.yaml
    current_methodology = None
    settings_file = vault_path / ".claude" / "settings.yaml"
    if settings_file.exists():
        try:
            import yaml

            with open(settings_file) as f:
                settings = yaml.safe_load(f)
                current_methodology = settings.get("methodology")
        except (OSError, yaml.YAMLError):
            # Settings file unreadable or invalid - treat as no methodology
            pass

    return {
        "exists": True,
        "has_obsidian": has_obsidian,
        "has_claude_config": has_claude,
        "has_content": len(folders) > 0 or len(files) > 0,
        "folder_count": len(folders),
        "file_count": len(files),
        "current_methodology": current_methodology,
    }


def prompt_existing_vault_action(detection: dict[str, Any]) -> str:  # pragma: no cover
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


def create_vault_backup(vault_path: Path) -> Path | None:
    """Create a ZIP backup of the vault before reset.

    Args:
        vault_path: Path to the vault

    Returns:
        Path to the backup file, or None if backup failed
    """
    import zipfile
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"vault_backup_{timestamp}.zip"
    backup_path = vault_path.parent / backup_name

    print(f"\n  Creating backup: {backup_name}")

    try:
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for item in vault_path.rglob("*"):
                # Skip folders excluded from backup (.obsidian, .git, .github, .vscode)
                if any(excluded in item.parts for excluded in BACKUP_EXCLUDE_FOLDERS):
                    continue
                if item.is_file():
                    arcname = item.relative_to(vault_path)
                    zipf.write(item, arcname)
                    print(f"    + {arcname}")

        print(f"  ✓ Backup saved: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"  ⚠️  Backup failed: {e}")
        return None


def reset_vault(vault_path: Path) -> None:
    """Reset vault to clean state.

    Creates a backup ZIP before deleting any files.
    Protected folders (.obsidian, .github, .vscode) are preserved.
    Note: .git is deleted to allow fresh git initialization.
    Protected files (README.md, AGENTS.md, CLAUDE.md, Home.md, .gitignore)
    are preserved and will be updated during initialization.

    Args:
        vault_path: Path to the vault
    """
    # Create backup first
    backup_path = create_vault_backup(vault_path)
    if backup_path is None:
        print("  ⚠️  Continuing without backup...")

    print("\nResetting vault...")

    for item in vault_path.iterdir():
        # Skip protected system folders (.obsidian, .github, .vscode)
        # Note: .git is NOT protected - it will be deleted for fresh init
        if item.name in PROTECTED_FOLDERS:
            print(f"  - Keeping: {item.name}/")
            continue

        # Skip protected root files (will be updated during init)
        if item.name in PROTECTED_FILES:
            print(f"  - Keeping: {item.name} (will be updated)")
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


def wizard_step_quick_or_custom() -> bool:  # pragma: no cover
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


def wizard_step_note_types(methodology: str) -> dict[str, dict[str, Any]]:  # pragma: no cover
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


def wizard_step_frontmatter(  # pragma: no cover
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


def wizard_step_per_type_properties(  # pragma: no cover
    note_types: dict[str, dict[str, Any]],
) -> dict[str, dict[str, list[str]]]:
    """Configure properties for each note type.

    Args:
        note_types: Dictionary of enabled note types

    Returns:
        Dictionary mapping type names to property configurations
        {type_name: {"required": [...], "optional": [...]}}
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 5: Per-Type Properties".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Configure properties for each note type".ljust(58) + "│")
    print("│".ljust(59) + "│")
    print("│   [a] Accept defaults for all types (press Enter)".ljust(59) + "│")
    print("│   [c] Customize per-type properties".ljust(59) + "│")
    print("└" + "─" * 58 + "┘")

    choice = input("\nYour choice [a]: ").strip().lower()

    if choice == "" or choice in ("a", "accept"):
        print("  ✓ Using default properties for all types")
        return {}

    per_type: dict[str, dict[str, list[str]]] = {}

    for type_name, type_config in note_types.items():
        current_required = type_config.get("properties", {}).get("additional_required", [])
        current_optional = type_config.get("properties", {}).get("optional", [])

        print()
        print("┌" + "─" * 58 + "┐")
        line = f"│  Note Type: {type_name}"
        print(line.ljust(59) + "│")
        print("├" + "─" * 58 + "┤")

        # Show current required properties
        if current_required:
            print("│" + " Required properties:".ljust(58) + "│")
            for i, prop in enumerate(current_required, 1):
                line = f"│   {i}. {prop}"
                print(line.ljust(59) + "│")
        else:
            print("│" + " Required properties: (none)".ljust(58) + "│")

        # Show current optional properties
        if current_optional:
            print("│" + " Optional properties:".ljust(58) + "│")
            for prop in current_optional:
                line = f"│   - {prop}"
                print(line.ljust(59) + "│")
        else:
            print("│" + " Optional properties: (none)".ljust(58) + "│")

        print("├" + "─" * 58 + "┤")
        print("│" + " [Enter] Keep defaults  [e] Edit properties".ljust(58) + "│")
        print("└" + "─" * 58 + "┘")

        edit_choice = input(f"\nEdit {type_name} properties? [n]: ").strip().lower()

        if edit_choice not in ("e", "edit", "y", "yes"):
            continue

        # Edit required properties
        print(f"\n  Current required: {', '.join(current_required) or '(none)'}")
        print("  Enter new required properties (comma-separated)")
        print("  Or press Enter to keep current, '-' to clear all")
        new_required_input = input("  Required: ").strip()

        if new_required_input == "-":
            new_required: list[str] = []
            print("  ✓ Cleared required properties")
        elif new_required_input:
            new_required = [p.strip() for p in new_required_input.split(",") if p.strip()]
            print(f"  ✓ Set required: {', '.join(new_required)}")
        else:
            new_required = list(current_required)

        # Edit optional properties
        print(f"\n  Current optional: {', '.join(current_optional) or '(none)'}")
        print("  Enter new optional properties (comma-separated)")
        print("  Or press Enter to keep current, '-' to clear all")
        new_optional_input = input("  Optional: ").strip()

        if new_optional_input == "-":
            new_optional: list[str] = []
            print("  ✓ Cleared optional properties")
        elif new_optional_input:
            new_optional = [p.strip() for p in new_optional_input.split(",") if p.strip()]
            print(f"  ✓ Set optional: {', '.join(new_optional)}")
        else:
            new_optional = list(current_optional)

        per_type[type_name] = {
            "required": new_required,
            "optional": new_optional,
        }

    return per_type


def wizard_step_custom_note_types(  # pragma: no cover
    methodology: str,
    existing_types: dict[str, dict[str, Any]],
) -> dict[str, NoteTypeConfig]:
    """Add custom note types beyond methodology defaults.

    Args:
        methodology: Selected methodology key
        existing_types: Already configured note types

    Returns:
        Dictionary of custom note type configurations
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 6: Custom Note Types (Optional)".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")
    print("│" + " Add your own note types beyond the methodology defaults".ljust(58) + "│")
    print("│".ljust(59) + "│")
    print("│   [n] No custom types (press Enter)".ljust(59) + "│")
    print("│   [a] Add custom note types".ljust(59) + "│")
    print("└" + "─" * 58 + "┘")

    choice = input("\nYour choice [n]: ").strip().lower()

    if choice == "" or choice in ("n", "no"):
        return {}

    custom_types: dict[str, NoteTypeConfig] = {}
    method_config = METHODOLOGIES[methodology]
    folders = method_config["folders"]

    while True:
        print()
        print("┌" + "─" * 58 + "┐")
        print("│" + " New Custom Note Type".ljust(58) + "│")
        print("└" + "─" * 58 + "┘")

        # Get type name
        type_name = input("\nType name (e.g., 'meeting', 'recipe'): ").strip().lower()
        if not type_name:
            break

        # Check for conflicts
        if type_name in existing_types or type_name in custom_types:
            print(f"  ⚠️  Type '{type_name}' already exists. Choose another name.")
            continue

        # Get description
        description = input("Description: ").strip()
        if not description:
            description = f"Custom {type_name} notes"

        # Choose folder
        print("\n  Available folders:")
        for i, folder in enumerate(folders, 1):
            print(f"    {i}. {folder}")
        print(f"    {len(folders) + 1}. (Create new folder)")

        folder_choice = input("\n  Folder [1]: ").strip()
        if not folder_choice:
            folder_idx = 0
        else:
            try:
                folder_idx = int(folder_choice) - 1
            except ValueError:
                folder_idx = 0

        if 0 <= folder_idx < len(folders):
            folder_hint = folders[folder_idx]
            if not folder_hint.endswith("/"):
                folder_hint += "/"
        else:
            new_folder = input("  New folder name: ").strip()
            folder_hint = new_folder.rstrip("/") + "/" if new_folder else "Notes/"

        # Get required properties
        req_input = input("\nRequired properties (comma-separated, or Enter for none): ").strip()
        required_props = [p.strip() for p in req_input.split(",") if p.strip()] if req_input else []

        # Get optional properties
        opt_input = input("Optional properties (comma-separated, or Enter for none): ").strip()
        optional_props = [p.strip() for p in opt_input.split(",") if p.strip()] if opt_input else []

        # Create config
        custom_types[type_name] = NoteTypeConfig(
            name=type_name,
            description=description,
            folder_hints=[folder_hint],
            required_properties=required_props,
            optional_properties=optional_props,
            validation={"allow_empty_up": True},
            icon="file",
            is_custom=True,
        )

        print(f"\n  ✓ Added custom type: {type_name}")
        print(f"    Folder: {folder_hint}")
        print(f"    Required: {', '.join(required_props) or '(none)'}")
        print(f"    Optional: {', '.join(optional_props) or '(none)'}")

        # Ask if they want to add more
        more = input("\nAdd another custom type? [n]: ").strip().lower()
        if more not in ("y", "yes"):
            break

    return custom_types


def wizard_step_ranking_system() -> str:  # pragma: no cover
    """Ask user to choose ranking system for projects.

    Returns:
        "rank" for numeric 1-5 scale, "priority" for text-based
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " Project Ranking System".ljust(58) + "│")
    print("╞" + "═" * 58 + "╡")
    print("│  How should projects be prioritized?".ljust(59) + "│")
    print("│".ljust(59) + "│")
    print("│  [r] Rank (1-5 numeric scale, 5=highest) - Recommended".ljust(59) + "│")
    print("│  [p] Priority (text: low/medium/high/critical)".ljust(59) + "│")
    print("└" + "─" * 58 + "┘")

    while True:
        choice = input("\n  Choose ranking system [r]: ").strip().lower()
        if choice == "" or choice == "r":
            print("  → Using rank (1-5 numeric scale)")
            return "rank"
        if choice == "p":
            print("  → Using priority (text-based)")
            return "priority"
        print("  Please enter 'r' or 'p'.")


def wizard_step_git_init() -> bool:  # pragma: no cover
    """Ask user if they want to initialize a git repository.

    Returns:
        True to initialize git, False to skip
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " Git Repository".ljust(58) + "│")
    print("╞" + "═" * 58 + "╡")
    print("│  Initialize a git repository for version control?".ljust(59) + "│")
    print("│".ljust(59) + "│")
    print("│  [y] Yes - Create git repo with initial commit".ljust(59) + "│")
    print("│  [n] No  - Skip git initialization (default)".ljust(59) + "│")
    print("└" + "─" * 58 + "┘")

    while True:
        choice = input("\n  Initialize git repository? [n]: ").strip().lower()
        if choice == "" or choice == "n":
            print("  → Skipping git initialization")
            return False
        if choice == "y":
            print("  → Will initialize git repository")
            return True
        print("  Please enter 'y' or 'n'.")


def create_gitignore(vault_path: Path, dry_run: bool = False) -> None:
    """Create .gitignore file for the vault if it doesn't exist.

    Args:
        vault_path: Path to the vault root
        dry_run: If True, only print what would be done
    """
    gitignore_path = vault_path / ".gitignore"

    # Skip if already exists
    if gitignore_path.exists():
        return

    gitignore_content = """# Obsidian
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
.obsidian/plugins/*/data.json

# System
.DS_Store
.Trash/
Thumbs.db

# Claude Code
.claude/logs/
.claude/backups/

# Editor
*.swp
*.swo
*~
"""
    if dry_run:
        print("[DRY RUN] Would create .gitignore")
        return

    gitignore_path.write_text(gitignore_content)
    print("✓ Created: .gitignore")


def init_git_repo(vault_path: Path, methodology: str, dry_run: bool = False) -> bool:
    """Initialize a git repository in the vault.

    Initializes git and makes initial commit. Assumes .gitignore already exists.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology name for commit message
        dry_run: If True, only print what would be done

    Returns:
        True if successful, False if git not available or failed
    """
    import shutil
    import subprocess

    # Check if git is available and get full path
    git_path = shutil.which("git")
    if not git_path:
        print("  ⚠ Git not found in PATH, skipping git initialization")
        return False

    # Check if already a git repo
    if (vault_path / ".git").exists():
        print("  → Git repository already exists, skipping")
        return True

    method_config = METHODOLOGIES[methodology]
    method_name = method_config["name"]

    if dry_run:
        print("[DRY RUN] Would initialize git repository")
        print(f'[DRY RUN] Would commit: "Initial vault setup with {method_name}"')
        return True

    try:
        # Initialize git repo
        # Security: git_path is from shutil.which(), args are hardcoded
        subprocess.run(  # noqa: S603
            [git_path, "init"],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )
        print("✓ Initialized git repository")

        # Stage all files
        subprocess.run(  # noqa: S603
            [git_path, "add", "."],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )

        # Create initial commit
        commit_message = f"Initial vault setup with {method_name}"
        subprocess.run(  # noqa: S603
            [git_path, "commit", "-m", commit_message],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f'✓ Created initial commit: "{commit_message}"')

        return True
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ Git initialization failed: {e}")
        return False


def wizard_step_confirm(config: WizardConfig) -> bool:  # pragma: no cover
    """Show summary and ask for confirmation.

    Args:
        config: The collected wizard configuration

    Returns:
        True to proceed, False to go back
    """
    method = METHODOLOGIES[config.methodology]

    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " STEP 7: Confirm Configuration".ljust(58) + "│")
    print("╞" + "═" * 58 + "╡")

    line = f"│   Methodology:  {method['name']}"
    print(line.ljust(59) + "│")

    # Show note types including custom ones
    all_types = list(config.note_types.keys()) + list(config.custom_note_types.keys())
    line = f"│   Note Types:   {', '.join(all_types)}"
    if len(line) > 58:
        line = line[:55] + "..."
    print(line.ljust(59) + "│")

    # Show custom types if any
    if config.custom_note_types:
        custom_names = list(config.custom_note_types.keys())
        line = f"│   Custom Types: {', '.join(custom_names)}"
        if len(line) > 58:
            line = line[:55] + "..."
        print(line.ljust(59) + "│")

    line = f"│   Mandatory:    {', '.join(config.mandatory_properties) or '(none)'}"
    if len(line) > 58:
        line = line[:55] + "..."
    print(line.ljust(59) + "│")

    line = f"│   Optional:     {', '.join(config.optional_properties) or '(none)'}"
    print(line.ljust(59) + "│")

    line = f"│   Custom Props: {', '.join(config.custom_properties) or '(none)'}"
    print(line.ljust(59) + "│")

    # Show per-type customizations if any
    if config.per_type_properties:
        print("│".ljust(59) + "│")
        print("│   Per-Type Customizations:".ljust(59) + "│")
        for type_name, props in config.per_type_properties.items():
            req = props.get("required", [])
            opt = props.get("optional", [])
            if req or opt:
                line = f"│     {type_name}: req={len(req)}, opt={len(opt)}"
                print(line.ljust(59) + "│")

    line = f"│   Sample Notes: {'Yes' if config.create_samples else 'No'}"
    print(line.ljust(59) + "│")

    line = f"│   Git Init:     {'Yes' if config.init_git else 'No'}"
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


def wizard_full_flow(vault_path: Path) -> WizardConfig | None:  # pragma: no cover
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
            reset_vault(vault_path)

    # STEP 1: Choose methodology
    methodology = wizard_step_methodology()
    method_config = METHODOLOGIES[methodology]

    # STEP 2: Quick or custom setup
    use_defaults = wizard_step_quick_or_custom()

    # STEP 3 (for both paths): Choose ranking system
    ranking_system = wizard_step_ranking_system()

    # STEP 4 (for both paths): Ask about git initialization
    init_git = wizard_step_git_init()

    if use_defaults:
        # Quick setup - use all defaults
        # Apply ranking system to note types for correct property display
        quick_note_types = apply_ranking_system(dict(method_config["note_types"]), ranking_system)
        config = WizardConfig(
            methodology=methodology,
            note_types=quick_note_types,
            core_properties=list(method_config["core_properties"]),
            mandatory_properties=list(method_config["core_properties"]),
            optional_properties=[],
            custom_properties=[],
            custom_note_types={},
            per_type_properties={},
            create_samples=True,
            ranking_system=ranking_system,
            init_git=init_git,
        )
    else:
        # Custom setup
        # STEP 5: Configure note types
        note_types = wizard_step_note_types(methodology)

        # Apply ranking system choice to note types BEFORE showing per-type properties
        # This ensures options show "rank" or "priority" based on user's choice
        note_types = apply_ranking_system(note_types, ranking_system)

        # STEP 6: Configure frontmatter (core properties)
        mandatory, optional, custom = wizard_step_frontmatter(method_config["core_properties"])

        # STEP 7: Configure per-type properties
        per_type_props = wizard_step_per_type_properties(note_types)

        # STEP 8: Add custom note types
        custom_types = wizard_step_custom_note_types(methodology, note_types)

        config = WizardConfig(
            methodology=methodology,
            note_types=note_types,
            core_properties=list(method_config["core_properties"]),
            mandatory_properties=mandatory,
            optional_properties=optional,
            custom_properties=custom,
            custom_note_types=custom_types,
            per_type_properties=per_type_props,
            create_samples=True,
            ranking_system=ranking_system,
            init_git=init_git,
        )

    # STEP 9: Confirmation
    if not wizard_step_confirm(config):
        print("\n  Restarting wizard...\n")
        return wizard_full_flow(vault_path)

    return config


def wizard_step_methodology() -> str:  # pragma: no cover
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
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> str:
    """Generate sample note content dynamically.

    Args:
        note_type: Type name (map, dot, source, etc.)
        note_type_config: Config with folder_hints, properties, validation
        core_properties: List of core frontmatter properties
        methodology: Selected methodology name
        up_links: UP link mappings for folders
        core_properties_filter: Optional filter for which properties to include
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

    Returns:
        Complete markdown content with frontmatter and helpful body
    """
    today = date.today().isoformat()
    folder_hint = note_type_config.get("folder_hints", [""])[0]
    description = note_type_config.get("description", f"{note_type.title()} notes")

    # Determine up link
    up_link = up_links.get(folder_hint, "[[Home]]")

    # Filter core properties if filter is provided
    # Always include 'type' and 'created' as mandatory
    active_properties = list(core_properties)
    if core_properties_filter:
        mandatory = {"type", "created"}
        active_properties = [
            p for p in core_properties if p in core_properties_filter or p in mandatory
        ]

    # Add custom properties
    if custom_properties:
        active_properties = list(active_properties) + custom_properties

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f'type: "{note_type}"',
    ]

    # Add up link if in active properties
    if "up" in active_properties:
        frontmatter_lines.append(f'up: "{up_link}"')

    # Add created (always included)
    frontmatter_lines.append(f'created: "{today}"')

    # Add daily link if in active properties
    if "daily" in active_properties:
        frontmatter_lines.append(f'daily: "[[{today}]]"')

    # Add tags
    if "tags" in active_properties:
        frontmatter_lines.append(f"tags: [sample, {methodology}]")

    # Add collection and related if in active properties
    if "collection" in active_properties:
        frontmatter_lines.append('collection: ""')
    if "related" in active_properties:
        frontmatter_lines.append("related: []")

    # Add additional_required properties with placeholder values
    additional_required = note_type_config.get("properties", {}).get("additional_required", [])
    for prop in additional_required:
        if prop == "status":
            frontmatter_lines.append('status: "active"')
        elif prop == "rank":
            frontmatter_lines.append("rank: 3")  # Default middle rank (1-5, 5=highest)
        elif prop == "priority":
            frontmatter_lines.append('priority: "medium"')
        elif prop == "author":
            frontmatter_lines.append('author: "Unknown"')
        elif prop == "url":
            frontmatter_lines.append('url: ""')
        elif prop == "source":
            frontmatter_lines.append('source: ""')
        else:
            frontmatter_lines.append(f'{prop}: ""')

    # Add per-type custom properties (if any)
    if per_type_properties and note_type in per_type_properties:
        for prop in per_type_properties[note_type]:
            if prop not in additional_required:  # Avoid duplicates
                frontmatter_lines.append(f'{prop}: ""')

    # Add custom global properties
    if custom_properties:
        # Track properties already written to frontmatter
        written_props = {"type", "up", "created", "daily", "tags", "collection", "related"}
        written_props.update(additional_required)
        if per_type_properties and note_type in per_type_properties:
            written_props.update(per_type_properties[note_type])

        for prop in custom_properties:
            if prop not in written_props:
                frontmatter_lines.append(f'{prop}: ""')

    # Add optional properties (commented) - skip if already added via per-type
    optional_props = note_type_config.get("properties", {}).get("optional", [])
    per_type_props_for_this_type = (
        per_type_properties.get(note_type, []) if per_type_properties else []
    )
    for prop in optional_props:
        # Skip if already added as per-type property
        if prop not in per_type_props_for_this_type:
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
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> list[Path]:
    """Create sample notes for each enabled note type.

    Args:
        vault_path: Path to the vault root
        methodology: Selected methodology
        note_types: Dictionary of enabled note types
        core_properties: List of core properties
        dry_run: If True, only print what would be created
        core_properties_filter: Optional filter for which properties to include
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

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
            note_type,
            type_config,
            core_properties,
            methodology,
            up_links,
            core_properties_filter=core_properties_filter,
            custom_properties=custom_properties,
            per_type_properties=per_type_properties,
        )

        if dry_run:
            print(f"  [DRY RUN] Would create: {file_path}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"  ✓ Created: {file_path}")
            created_files.append(file_path)

    return created_files


def generate_template_note(
    note_type: str,
    type_config: dict[str, Any],
    core_properties: list[str],
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> str:
    """Generate a template note for a specific note type.

    Args:
        note_type: The type of note (e.g., 'map', 'dot', 'project')
        type_config: Configuration for this note type
        core_properties: List of core properties
        core_properties_filter: Optional filter for which properties to include
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

    Returns:
        Template content as string
    """
    # Filter core properties if filter is provided
    # Always include 'type' and 'created' as mandatory
    active_properties = list(core_properties)
    if core_properties_filter:
        mandatory = {"type", "created"}
        active_properties = [
            p for p in core_properties if p in core_properties_filter or p in mandatory
        ]

    # Add custom properties
    if custom_properties:
        active_properties = list(active_properties) + custom_properties

    # Build frontmatter with all properties as placeholders
    lines = ["---"]
    lines.append(f'type: "{note_type}"')

    # Add core properties (except type which is already added)
    for prop in active_properties:
        if prop == "type":
            continue
        elif prop == "up":
            lines.append('up: "[[{{up}}]]"')
        elif prop == "created":
            lines.append("created: {{date}}")
        elif prop == "tags":
            lines.append("tags: []")
        elif prop == "daily":
            lines.append("daily: ")
        elif prop == "collection":
            lines.append("collection: ")
        elif prop == "related":
            lines.append("related: []")
        else:
            lines.append(f"{prop}: ")

    # Add type-specific required properties
    props = type_config.get("properties", {})
    additional_required = props.get("additional_required", [])
    for prop in additional_required:
        if prop == "status":
            lines.append('status: "active"')
        elif prop == "author":
            lines.append("author: ")
        elif prop == "url":
            lines.append("url: ")
        else:
            lines.append(f"{prop}: ")

    # Add per-type custom properties (if any)
    if per_type_properties and note_type in per_type_properties:
        for prop in per_type_properties[note_type]:
            if prop not in additional_required:  # Avoid duplicates
                lines.append(f"{prop}: ")

    # Add optional properties as comments - skip if already added via per-type
    optional = props.get("optional", [])
    per_type_props_for_this_type = (
        per_type_properties.get(note_type, []) if per_type_properties else []
    )
    for prop in optional:
        # Skip if already added as per-type property
        if prop not in per_type_props_for_this_type:
            lines.append(f"# {prop}: ")

    lines.append("---")
    lines.append("")

    # Add template body
    description = type_config.get("description", f"{note_type.title()} note")
    type_title = note_type.replace("_", " ").title()

    lines.append("# {{title}}")
    lines.append("")
    lines.append(f"> Template for **{type_title}** notes: {description}")
    lines.append("")
    lines.append("## Content")
    lines.append("")
    lines.append("<!-- Your content here -->")
    lines.append("")
    lines.append("## Related")
    lines.append("")
    lines.append("- [[]]")
    lines.append("")

    return "\n".join(lines)


def create_template_notes(
    vault_path: Path,
    methodology: str,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
    dry_run: bool = False,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> list[Path]:
    """Create template notes for each note type.

    Args:
        vault_path: Path to the vault root
        methodology: Selected methodology
        note_types: Dictionary of enabled note types
        core_properties: List of core properties
        dry_run: If True, only print what would be created
        core_properties_filter: Optional filter for which properties to include
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

    Returns:
        List of created file paths
    """
    method_config = METHODOLOGIES[methodology]
    folder_structure = method_config.get("folder_structure", {})
    templates_folder = folder_structure.get("templates", "x/templates/")
    templates_path = vault_path / templates_folder

    created_files: list[Path] = []

    print("\nCreating template notes...")

    for note_type, type_config in note_types.items():
        # Skip daily notes - they use a different template system
        if note_type == "daily":
            continue

        template_file = templates_path / f"{note_type}.md"
        content = generate_template_note(
            note_type,
            type_config,
            core_properties,
            core_properties_filter=core_properties_filter,
            custom_properties=custom_properties,
            per_type_properties=per_type_properties,
        )

        if dry_run:
            print(f"  [DRY RUN] Would create: {template_file}")
        else:
            template_file.parent.mkdir(parents=True, exist_ok=True)
            template_file.write_text(content)
            print(f"  ✓ Created: {template_file}")
            created_files.append(template_file)

    return created_files


def get_content_folders(methodology: str) -> list[str]:
    """Get top-level content folders for a methodology (excluding + and x).

    Used for base views - returns only top-level folders.

    Args:
        methodology: Methodology key

    Returns:
        List of top-level folder names for views
    """
    method_config = METHODOLOGIES[methodology]
    folders = method_config["folders"]

    # Extract unique top-level folders, excluding + and x
    content_folders = set()
    for folder in folders:
        # Skip inbox and system folders
        if folder.startswith("+") or folder.startswith("x"):
            continue
        # Get top-level folder name
        top_level = folder.split("/")[0]
        content_folders.add(top_level)

    # Return sorted list for consistent ordering
    return sorted(content_folders)


def get_all_content_folders(methodology: str) -> list[str]:
    """Get all content folders including subfolders (excluding + and x).

    Used for MOC file generation - returns all folders.

    Args:
        methodology: Methodology key

    Returns:
        List of all folder paths for readme generation
    """
    method_config = METHODOLOGIES[methodology]
    folders = method_config["folders"]

    # Get all folders excluding + and x, plus top-level folders
    content_folders = set()
    for folder in folders:
        # Skip inbox and system folders
        if folder.startswith("+") or folder.startswith("x"):
            continue
        # Add the folder itself
        content_folders.add(folder.rstrip("/"))
        # Also add top-level folder if it's a subfolder
        if "/" in folder:
            top_level = folder.split("/")[0]
            content_folders.add(top_level)

    # Return sorted list for consistent ordering
    return sorted(content_folders)


def generate_all_bases_content(methodology: str) -> str:
    """Generate the all_bases.base file content for a methodology.

    Args:
        methodology: Methodology key

    Returns:
        YAML content for the .base file
    """
    # Use all content folders including subfolders for views
    content_folders = get_all_content_folders(methodology)

    # Build the YAML structure manually for proper formatting
    lines = [
        "filters:",
        "  and:",
        "    - '!file.inFolder(\"+\")'",
        "    - '!file.inFolder(\"x\")'",
        '    - file.folder != "/"',
        '    - \'!file.name.startsWith("_") || !file.name.endsWith("_MOC")\'',
        "views:",
        "  - type: table",
        "    name: All",
        "    groupBy:",
        "      property: file.folder",
        "      direction: ASC",
        "    order:",
        "      - file.name",
        "      - type",
        "      - up",
    ]

    # Add a view for each content folder
    for folder in content_folders:
        # Use last part of path as view name (e.g., "Dots" not "Atlas/Dots")
        view_name = folder.split("/")[-1] if "/" in folder else folder
        lines.extend(
            [
                "  - type: table",
                f"    name: {view_name}",
                "    filters:",
                "      and:",
                f'        - file.inFolder("{folder}")',
                "    order:",
                "      - file.name",
                "      - type",
                "      - up",
            ]
        )

    return "\n".join(lines) + "\n"


def create_all_bases_file(
    vault_path: Path,
    methodology: str,
    dry_run: bool = False,
) -> Path | None:
    """Create the all_bases.base file for the vault.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        dry_run: If True, only print what would be created

    Returns:
        Path to created file, or None if dry run
    """
    # Create in x/bases/ folder
    bases_folder = vault_path / "x" / "bases"
    base_file = bases_folder / "all_bases.base"

    content = generate_all_bases_content(methodology)

    print("\nCreating all_bases.base (Obsidian Bases views)...")

    if dry_run:
        print(f"  [DRY RUN] Would create: {base_file}")
        print("  [DRY RUN] Content preview:")
        for line in content.split("\n")[:10]:
            print(f"    {line}")
        print("    ...")
        return None
    else:
        bases_folder.mkdir(parents=True, exist_ok=True)
        base_file.write_text(content)
        print(f"  ✓ Created: {base_file}")
        return base_file


# Folder descriptions for each methodology
FOLDER_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "lyt-ace": {
        "Atlas": "Knowledge repository containing Maps of Content, atomic concepts, and sources.",
        "Atlas/Maps": "Maps of Content - Overview and navigation notes.",
        "Atlas/Dots": "Atomic concepts and ideas - one idea per note.",
        "Atlas/Sources": "External references, citations, and source materials.",
        "Calendar": "Time-based notes including daily journals and periodic reviews.",
        "Calendar/daily": "Daily journal entries and reflections.",
        "Efforts": "Active work including projects and ongoing areas of responsibility.",
        "Efforts/Projects": "Projects with defined outcomes and deadlines.",
        "Efforts/Areas": "Ongoing areas of responsibility.",
    },
    "para": {
        "Projects": "Active projects with defined outcomes and deadlines.",
        "Areas": "Ongoing areas of responsibility that require maintenance.",
        "Resources": "Reference materials and resources for future use.",
        "Archives": "Completed or inactive items preserved for reference.",
    },
    "zettelkasten": {
        "Permanent": "Your own ideas and insights - the core of your knowledge base.",
        "Literature": "Notes from reading and external sources.",
        "Fleeting": "Quick captures and ideas to process later.",
        "References": "External sources and citations.",
    },
    "minimal": {
        "Notes": "General notes and ideas.",
        "Daily": "Daily journal entries and reflections.",
    },
}


def get_moc_filename(folder_path: str) -> str:
    """Get the MOC filename for a folder.

    Args:
        folder_path: Path of the folder (e.g., "Projects", "Atlas/Dots")

    Returns:
        MOC filename (e.g., "_Projects_MOC.md", "_Dots_MOC.md")
    """
    # Get display name (last part of path)
    display_name = folder_path.rstrip("/").split("/")[-1]
    return f"_{display_name}_MOC.md"


def get_moc_link(folder_path: str) -> str:
    """Get the wikilink to a folder's MOC file.

    Args:
        folder_path: Path of the folder (e.g., "Projects/", "Atlas/Dots/")

    Returns:
        Wikilink to MOC (e.g., "[[Projects/_Projects_MOC]]")
    """
    folder = folder_path.rstrip("/")
    display_name = folder.split("/")[-1]
    return f"[[{folder}/_{display_name}_MOC]]"


def generate_folder_moc_content(
    folder_path: str,
    methodology: str,
) -> str:
    """Generate MOC (Map of Content) file content for a folder.

    Args:
        folder_path: Path of the folder (e.g., "Projects", "Atlas/Dots")
        methodology: Methodology key

    Returns:
        Markdown content for the MOC file
    """
    descriptions = FOLDER_DESCRIPTIONS.get(methodology, {})
    description = descriptions.get(folder_path, f"Notes and content for {folder_path}.")

    # Get display name (last part of path) - also used as base view name
    display_name = folder_path.split("/")[-1] if "/" in folder_path else folder_path

    content = f"""---
type: map
created: "{{{{date}}}}"
---

# {display_name}

{description}

## Contents

![[all_bases.base#{display_name}]]
"""
    return content


def create_folder_mocs(
    vault_path: Path,
    methodology: str,
    dry_run: bool = False,
    note_types_filter: list[str] | None = None,
) -> list[Path]:
    """Create MOC (Map of Content) files in each content folder.

    MOC files are named _<FolderName>_MOC.md (e.g., _Projects_MOC.md).

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        dry_run: If True, only print what would be created
        note_types_filter: List of note type names to include (None = all)

    Returns:
        List of created file paths
    """
    # Get folders that should exist based on note type filter
    selected_folders = set(get_folders_for_note_types(methodology, note_types_filter))
    content_folders = get_all_content_folders(methodology)
    created_files: list[Path] = []

    print("\nCreating folder MOC files...")

    for folder in content_folders:
        # Skip folders that weren't created due to filtering
        folder_created = folder in selected_folders
        # For subfolders, check if parent is in selected folders
        if "/" in folder and not folder_created:
            parent = folder.split("/")[0]
            # Check if any subfolder of this parent is in selected_folders
            folder_created = any(
                sf.startswith(parent + "/") or sf == parent for sf in selected_folders
            )

        if not folder_created and note_types_filter is not None:
            continue

        folder_path = vault_path / folder
        # Also skip if folder doesn't actually exist (double check)
        if not dry_run and not folder_path.exists():
            continue

        moc_filename = get_moc_filename(folder)
        moc_path = folder_path / moc_filename
        content = generate_folder_moc_content(folder, methodology)

        if dry_run:
            print(f"  [DRY RUN] Would create: {moc_path}")
        else:
            moc_path.parent.mkdir(parents=True, exist_ok=True)
            moc_path.write_text(content)
            print(f"  ✓ Created: {moc_path}")
            created_files.append(moc_path)

    return created_files


# Backward compatibility alias
create_folder_readmes = create_folder_mocs


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


def choose_methodology_interactive() -> str:  # pragma: no cover
    """Interactively choose a methodology."""
    print_methodologies()

    while True:
        choice = input("Select methodology (lyt-ace/para/zettelkasten/minimal): ").strip().lower()
        if choice in METHODOLOGIES:
            return choice
        print(f"Invalid choice: {choice}. Please try again.")


def get_folders_for_note_types(
    methodology: str,
    note_types_filter: list[str] | None = None,
) -> list[str]:
    """Get list of folders to create based on selected note types.

    Args:
        methodology: Methodology key (e.g., 'lyt-ace', 'para')
        note_types_filter: List of note type names to include (None = all)

    Returns:
        List of folder paths to create
    """
    method_config = METHODOLOGIES[methodology]
    all_folders: list[str] = method_config["folders"]
    note_types = method_config.get("note_types", {})

    # System folders always included (inbox, templates, bases)
    system_folders = ["+", "x/templates", "x/bases"]

    if note_types_filter is None:
        # No filter - return all folders
        return all_folders

    # Build set of folders for selected note types
    selected_folders: set[str] = set()

    for type_name in note_types_filter:
        if type_name in note_types:
            hints = note_types[type_name].get("folder_hints", [])
            for hint in hints:
                # folder_hint is like "Projects/" - strip trailing slash
                folder = hint.rstrip("/")
                selected_folders.add(folder)

    # Add system folders and filter main folders list
    result = []
    for folder in all_folders:
        # Always include system folders
        if folder in system_folders or folder.startswith("x/"):
            result.append(folder)
        # Include if it matches a selected note type's folder
        elif folder in selected_folders:
            result.append(folder)
        # For LYT-ACE nested folders like "Atlas/Maps", check parent too
        elif "/" in folder:
            parent = folder.split("/")[0]
            if folder in selected_folders or parent in selected_folders:
                result.append(folder)

    return result


def create_folder_structure(
    vault_path: Path,
    methodology: str,
    dry_run: bool = False,
    note_types_filter: list[str] | None = None,
) -> None:
    """Create folder structure based on methodology and selected note types.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key (e.g., 'lyt-ace', 'para')
        dry_run: If True, only print what would be created without creating
        note_types_filter: List of note type names to include (None = all)
    """
    if methodology not in METHODOLOGIES:
        available = ", ".join(METHODOLOGIES.keys())
        raise ValueError(f"Unknown methodology: {methodology}. Available: {available}")

    method_config = METHODOLOGIES[methodology]
    folders = get_folders_for_note_types(methodology, note_types_filter)

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


def build_settings_yaml(
    methodology: str,
    config: WizardConfig | None = None,
    note_types_filter: list[str] | None = None,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Build settings.yaml content for a methodology.

    Args:
        methodology: Methodology key
        config: Optional WizardConfig with user customizations
        note_types_filter: List of note type names to include (None = all)
        core_properties_filter: List of core properties to include (None = all)
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

    Returns:
        Dictionary representing the settings.yaml content
    """
    method_config = METHODOLOGIES[methodology]

    # Start with methodology defaults for note types
    note_types = dict(method_config["note_types"])

    # Apply per-type property customizations from direct parameter
    if per_type_properties:
        for type_name, props_list in per_type_properties.items():
            if type_name in note_types:
                note_types[type_name] = dict(note_types[type_name])
                # Merge with existing properties
                existing_props = note_types[type_name].get("properties", {})
                existing_required = existing_props.get("additional_required", [])
                existing_optional = existing_props.get("optional", [])
                # Add new props as additional_required
                new_required = list(set(existing_required + props_list))
                note_types[type_name]["properties"] = {
                    "additional_required": new_required,
                    "optional": existing_optional,
                }

    # Apply per-type property customizations if provided via config
    if config and config.per_type_properties:
        for type_name, props in config.per_type_properties.items():
            if type_name in note_types:
                note_types[type_name] = dict(note_types[type_name])
                note_types[type_name]["properties"] = {
                    "additional_required": props.get("required", []),
                    "optional": props.get("optional", []),
                }

    # Add custom note types if provided
    if config and config.custom_note_types:
        for type_name, type_config in config.custom_note_types.items():
            note_types[type_name] = type_config.to_dict()

    # Use configured note types if provided (for disabled types)
    if config and config.note_types:
        # Only keep types that are in config.note_types
        filtered_types = {}
        for type_name in config.note_types:
            if type_name in note_types:
                filtered_types[type_name] = note_types[type_name]
        # Also include any custom types
        if config.custom_note_types:
            for type_name, type_config in config.custom_note_types.items():
                filtered_types[type_name] = type_config.to_dict()
        note_types = filtered_types

    # Apply note types filter if provided (from --note-types argument)
    if note_types_filter:
        note_types = {k: v for k, v in note_types.items() if k in note_types_filter}

    # Build core properties configuration
    all_core_properties = list(method_config["core_properties"])

    # Apply core properties filter if provided (from --core-properties argument)
    if core_properties_filter:
        # Always include 'type' and 'created' as mandatory
        mandatory = {"type", "created"}
        filtered_props = [
            p for p in all_core_properties if p in core_properties_filter or p in mandatory
        ]
        all_core_properties = filtered_props

    core_properties_config: dict[str, Any] = {
        "all": all_core_properties,
    }

    # Add custom properties from direct parameter
    if custom_properties:
        core_properties_config["custom"] = custom_properties
        # Add custom properties to the 'all' list
        all_core_properties = list(all_core_properties) + custom_properties
        core_properties_config["all"] = all_core_properties

    # Add mandatory/optional classification if customized via config
    if config:
        if config.mandatory_properties:
            core_properties_config["mandatory"] = config.mandatory_properties
        if config.optional_properties:
            core_properties_config["optional"] = config.optional_properties
        if config.custom_properties:
            # Merge with directly passed custom properties
            existing_custom = core_properties_config.get("custom", [])
            all_custom = list(set(existing_custom + config.custom_properties))
            core_properties_config["custom"] = all_custom
            # Add custom properties to the 'all' list
            base_props = list(method_config["core_properties"])
            if core_properties_filter:
                mandatory = {"type", "created"}
                base_props = [
                    p for p in base_props if p in core_properties_filter or p in mandatory
                ]
            core_properties_config["all"] = base_props + all_custom

    settings: dict[str, Any] = {
        "version": "1.0",
        "methodology": methodology,
        "core_properties": core_properties_config,
        "note_types": note_types,
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
            "patterns": ["_*_MOC.md"],  # MOC files in each folder
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


def create_settings_yaml(
    vault_path: Path,
    methodology: str,
    dry_run: bool = False,
    config: WizardConfig | None = None,
    note_types_filter: list[str] | None = None,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> None:
    """Create settings.yaml for the vault.

    This is the PRIMARY source of truth for all vault configuration.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        dry_run: If True, only print what would be created
        config: Optional WizardConfig with user customizations
        note_types_filter: List of note type names to include (None = all)
        core_properties_filter: List of core properties to include (None = all)
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties
    """
    settings = build_settings_yaml(
        methodology,
        config,
        note_types_filter,
        core_properties_filter,
        custom_properties=custom_properties,
        per_type_properties=per_type_properties,
    )
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

---

## Slash Command Reference

### Validation (`/obsidian:validate`)

| Command | Description |
|---------|-------------|
| `/obsidian:validate` | Validate all notes |
| `/obsidian:validate --fix` | Auto-fix issues |
| `/obsidian:validate --type project` | Validate specific type |
| `/obsidian:validate --path Atlas/` | Validate specific path |
| `/obsidian:validate --report report.md` | Save report to file |

### Configuration (`/obsidian:config`)

| Command | Description |
|---------|-------------|
| `/obsidian:config` | Show current configuration |
| `/obsidian:config show --verbose` | Show detailed config |
| `/obsidian:config show --format json` | JSON output |
| `/obsidian:config validate` | Validate settings.yaml |
| `/obsidian:config edit` | Open in editor |
| `/obsidian:config diff` | Compare with defaults |
| `/obsidian:config methodologies` | List methodologies |

### Note Types (`/obsidian:types`)

| Command | Description |
|---------|-------------|
| `/obsidian:types` | List all note types |
| `/obsidian:types show project` | Show type details |
| `/obsidian:types add meeting` | Add new type |
| `/obsidian:types edit project` | Edit type |
| `/obsidian:types remove meeting` | Remove type |
| `/obsidian:types wizard` | Interactive wizard |

### Properties (`/obsidian:props`)

| Command | Description |
|---------|-------------|
| `/obsidian:props` | List core properties |
| `/obsidian:props core add rank` | Add core property |
| `/obsidian:props core remove rank` | Remove core property |
| `/obsidian:props type project` | Show type properties |
| `/obsidian:props required --type project` | Required properties |

### Templates (`/obsidian:templates`)

| Command | Description |
|---------|-------------|
| `/obsidian:templates` | List vault templates |
| `/obsidian:templates --source plugin` | List plugin templates |
| `/obsidian:templates --source all` | List all templates |
| `/obsidian:templates show area` | Show template content |
| `/obsidian:templates create meeting` | Create new template |
| `/obsidian:templates edit area` | Edit template |
| `/obsidian:templates delete meeting` | Delete template |
| `/obsidian:templates apply area Note.md --var up=Home` | Apply template |

### Re-Initialize (`/obsidian:init`)

| Command | Description |
|---------|-------------|
| `/obsidian:init --action reset` | Reset vault |
| `/obsidian:init --action continue` | Update existing |
| `/obsidian:init --check` | Check vault status |

---

## Templates

Templates are stored in `x/templates/` as `{type}.md` files.

Use `{{variable}}` syntax for placeholders:
- `{{title}}` - Note title
- `{{date}}` - Current date (YYYY-MM-DD)
- `{{up}}` - Parent link
- `{{time}}` - Current time

Example: `/obsidian:templates apply area Areas/NewArea.md --var up="Home"`
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
type: map
created: "{{{{date}}}}"
---

# Home

Welcome to your **{method_config["name"]}** vault!

## All Notes

![[all_bases.base#All]]

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


def generate_agents_md(
    methodology: str,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
) -> str:
    """Generate AGENTS.md content for the vault.

    Creates agent-focused instructions following the AGENTS.md standard.
    See https://agents.md/ for the specification.

    Args:
        methodology: Selected methodology name
        note_types: Dictionary of note type configurations (unused, kept for API compat)
        core_properties: List of core frontmatter properties (unused, kept for API compat)

    Returns:
        Complete markdown content for AGENTS.md
    """
    # Note: note_types and core_properties kept for backward compatibility
    # but we now reference settings.yaml instead of hardcoding
    _ = note_types, core_properties  # Explicitly mark as intentionally unused

    method_config = METHODOLOGIES[methodology]
    method_name = method_config["name"]
    folders = method_config.get("folders", [])

    # Build folder list for structure section
    folder_list = "\n".join(f"- `{f}/`" for f in folders[:6])  # Top 6 folders

    today = date.today().isoformat()
    content = f"""---
type: "system"
created: "{today}"
tags: [system, agents]
---

# AGENTS.md

Instructions for AI coding agents working with this Obsidian vault.

## Project Overview

This is an Obsidian vault using the **{method_name}** methodology.

- **Config**: `.claude/settings.yaml` (single source of truth)
- **Templates**: `x/templates/`
- **Validation**: Run after any note changes

## Commands

```bash
# Validate all notes
/obsidian:validate

# Auto-fix frontmatter issues
/obsidian:validate --fix

# Show current configuration
/obsidian:config show

# List note types with requirements
/obsidian:types
```

## Project Structure

{folder_list}
- `x/templates/` - Note templates
- `.claude/` - Configuration

Each note type has a designated folder. Check `settings.yaml` for mappings.

## Code Style (Frontmatter)

**Required properties (ALL notes):**
```yaml
---
type: "project"      # Note type (project, area, resource, etc.)
created: "{today}"   # ISO date
up: "[[Parent Note]]" # Link to logical parent or MOC
---
```

**Type-specific properties:** Check `settings.yaml` → `note_types` → `<type>`

## Testing

After creating or modifying notes:
```bash
/obsidian:validate --fix
```

The validator checks:
- Required frontmatter exists
- Note is in correct folder
- UP-links are valid wikilinks

## Boundaries

### ✅ Always Do
- Read `settings.yaml` before creating notes
- Use templates from `x/templates/`
- Set `type`, `created`, and `up` properties
- Validate after changes

### ⚠️ Ask First
- Creating new note types
- Modifying `settings.yaml`
- Moving notes between folders

### 🚫 Never Do
- Create notes without frontmatter
- Place notes outside designated folders
- Delete `Home.md` or system files
- Modify `.obsidian/` folder

## UP-Links

The `up` property creates a navigation hierarchy:
- Links to the **logical parent** note or a **MOC (Map of Content)**
- MOCs link upward to `[[Home]]`
- Every note should be reachable from Home via UP-links

## Git Workflow

If git is initialized:
- Commit after significant changes
- Use descriptive commit messages
- Don't commit `.obsidian/workspace.json`
"""
    return content


def generate_claude_md() -> str:
    """Generate CLAUDE.md content for the vault.

    Creates a minimal file that includes AGENTS.md via @ reference.
    Claude Code will automatically load AGENTS.md content.

    Returns:
        Complete markdown content for CLAUDE.md
    """
    today = date.today().isoformat()
    content = f"""---
type: "system"
created: "{today}"
tags: [system]
---

# CLAUDE.md

See @AGENTS.md for complete agent instructions.

## Claude-Specific

- Use `/memory` to edit this file
- Use `/init` to re-initialize vault configuration
- Modular rules can be added in `.claude/rules/*.md`

## Obsidian Plugin

This vault uses the Obsidian plugin. Key commands:

```bash
/obsidian:validate --fix  # Validate and fix notes
/obsidian:config show     # Show current settings
/obsidian:types           # List note types
```
"""
    return content


def create_agent_docs(
    vault_path: Path,
    methodology: str,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
    dry_run: bool = False,
) -> None:
    """Create AGENTS.md and CLAUDE.md in the vault root.

    Args:
        vault_path: Path to the vault root
        methodology: Selected methodology name
        note_types: Dictionary of note type configurations
        core_properties: List of core frontmatter properties
        dry_run: If True, only print what would be created
    """
    # Generate AGENTS.md
    agents_content = generate_agents_md(methodology, note_types, core_properties)
    agents_path = vault_path / "AGENTS.md"

    if dry_run:
        print(f"[DRY RUN] Would create: {agents_path}")
    else:
        agents_path.write_text(agents_content)
        print(f"✓ Created: {agents_path}")

    # Generate CLAUDE.md
    claude_content = generate_claude_md()
    claude_path = vault_path / "CLAUDE.md"

    if dry_run:
        print(f"[DRY RUN] Would create: {claude_path}")
    else:
        claude_path.write_text(claude_content)
        print(f"✓ Created: {claude_path}")


def init_vault(
    vault_path: Path,
    methodology: str | None = None,
    dry_run: bool = False,
    use_wizard: bool = False,
    use_defaults: bool = False,
    note_types_filter: list[str] | None = None,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
    ranking_system: str = "rank",
) -> None:
    """Initialize an Obsidian vault with chosen methodology.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key (if None, prompt interactively)
        dry_run: If True, only show what would be created
        use_wizard: If True, run the full interactive wizard
        use_defaults: If True, skip confirmations and use defaults
        note_types_filter: List of note type names to include (None = all)
        core_properties_filter: List of core properties to include (None = all)
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties
        ranking_system: Ranking system for projects ('rank' or 'priority')
    """
    # Check for existing vault first
    detection = detect_existing_vault(vault_path)
    has_existing = detection["exists"] and detection["has_content"]

    # Ensure vault path exists
    if not dry_run:
        vault_path.mkdir(parents=True, exist_ok=True)

    # Determine configuration source
    config: WizardConfig | None = None

    if use_wizard and methodology is None:
        # Full wizard mode - handles everything including existing vault check
        config = wizard_full_flow(vault_path)
        if config is None:
            return  # User aborted
        methodology = config.methodology
        # Merge custom note types with methodology types
        note_types = dict(config.note_types)
        for type_name, type_config in config.custom_note_types.items():
            note_types[type_name] = type_config.to_dict()
        # Apply ranking system (rank or priority) to project-like notes
        note_types = apply_ranking_system(note_types, config.ranking_system)
        core_properties = config.core_properties
        create_samples = config.create_samples
    else:
        # Direct mode (with or without methodology flag)
        # Handle existing vault FIRST, before methodology selection
        # NOTE: Files are ONLY deleted when user explicitly chooses "reset"
        if has_existing and not use_defaults:
            print()
            print(f"  Vault: {vault_path}")
            action = prompt_existing_vault_action(detection)
            if action == "abort":
                print("\n  Initialization cancelled.")
                return
            if action == "reset":
                reset_vault(vault_path)
            # "continue" - do nothing, keep existing content

        # Now select methodology if not provided
        if methodology is None:
            methodology = choose_methodology_interactive()

        method_config = METHODOLOGIES[methodology]
        note_types = method_config["note_types"]
        # Apply ranking system (rank or priority) to project-like notes
        note_types = apply_ranking_system(note_types, ranking_system)
        core_properties = method_config["core_properties"]
        create_samples = True
        # NOTE: No auto-reset! Files are NEVER deleted except via explicit reset

    # Apply note types filter if provided
    if note_types_filter:
        note_types = {k: v for k, v in note_types.items() if k in note_types_filter}

    print(f"\n{'=' * 60}")
    print(f"Initializing vault at: {vault_path}")
    print(f"Methodology: {METHODOLOGIES[methodology]['name']}")
    print(f"{'=' * 60}")

    if dry_run:
        print("\n*** DRY RUN MODE - No files will be created ***\n")

    # Create folder structure (filtered by selected note types)
    create_folder_structure(vault_path, methodology, dry_run, note_types_filter)

    # Create settings.yaml (PRIMARY configuration) with user customizations
    create_settings_yaml(
        vault_path,
        methodology,
        dry_run,
        config,
        note_types_filter,
        core_properties_filter,
        custom_properties=custom_properties,
        per_type_properties=per_type_properties,
    )

    # Create README
    create_readme(vault_path, methodology, dry_run)

    # Create Home note
    create_home_note(vault_path, methodology, dry_run)

    # Create agent documentation (AGENTS.md and CLAUDE.md)
    create_agent_docs(vault_path, methodology, note_types, core_properties, dry_run)

    # Create sample notes
    if create_samples:
        create_sample_notes(
            vault_path,
            methodology,
            note_types,
            core_properties,
            dry_run,
            core_properties_filter=core_properties_filter,
            custom_properties=custom_properties,
            per_type_properties=per_type_properties,
        )

    # Create template notes for each note type
    create_template_notes(
        vault_path,
        methodology,
        note_types,
        core_properties,
        dry_run,
        core_properties_filter=core_properties_filter,
        custom_properties=custom_properties,
        per_type_properties=per_type_properties,
    )

    # Create all_bases.base for Obsidian Bases plugin
    create_all_bases_file(vault_path, methodology, dry_run)

    # Create MOC file (_<FolderName>_MOC.md) in each content folder
    create_folder_mocs(vault_path, methodology, dry_run, note_types_filter)

    # Create .gitignore (always, regardless of git init choice)
    create_gitignore(vault_path, dry_run)

    # Initialize git repository if requested
    if config is not None and config.init_git:
        print("\nInitializing git repository...")
        init_git_repo(vault_path, methodology, dry_run)

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
        print("  4. View settings: /obsidian:config show")


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


def main() -> int:  # pragma: no cover
    """Main entry point."""
    import json
    import os

    # Check if called from wrapper (required for Claude Code integration)
    # Allow: --list, --list-note-types, --check (query operations only)
    # Block: ALL direct calls with -m/--methodology (even with --defaults)
    from_wrapper = os.environ.get("INIT_FROM_WRAPPER") == "1"
    raw_args = sys.argv[1:]

    # If not from wrapper and trying to initialize with methodology
    has_methodology = "-m" in raw_args or "--methodology" in raw_args
    is_query = "--list" in raw_args or "--list-note-types" in raw_args or "--check" in raw_args

    if has_methodology and not from_wrapper and not is_query:
        error_msg = {
            "error": "Direct call not allowed",
            "message": (
                "This script must be called through the wrapper. "
                "Use: python3 ${CLAUDE_PLUGIN_ROOT}/commands/init.py"
            ),
            "hint": (
                "The wrapper handles the interactive workflow and calls this script internally."
            ),
        }
        print(json.dumps(error_msg, indent=2))
        return 1

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
        "-m",
        "--methodology",
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
        "--git",
        action="store_true",
        help="Initialize git repository with initial commit",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if vault exists and show status (no changes made)",
    )
    parser.add_argument(
        "--list-note-types",
        metavar="METHODOLOGY",
        help="List note types for a methodology as JSON",
    )
    parser.add_argument(
        "--note-types",
        help="Comma-separated list of note types to include (default: all)",
    )
    parser.add_argument(
        "--core-properties",
        help="Comma-separated list of core properties to include (default: all)",
    )
    parser.add_argument(
        "--custom-properties",
        help="Comma-separated list of custom properties to add globally",
    )
    parser.add_argument(
        "--per-type-props",
        help="Per-type properties in format: type1:prop1,prop2;type2:prop3,prop4",
    )
    parser.add_argument(
        "--ranking-system",
        choices=["rank", "priority"],
        default="rank",
        help="Ranking system for projects: 'rank' (1-5 numeric) or 'priority' (text)",
    )

    args = parser.parse_args()

    if args.list:
        print_methodologies()
        return 0

    # Handle --list-note-types
    if args.list_note_types:
        import json

        methodology = args.list_note_types
        if methodology not in METHODOLOGIES:
            print(json.dumps({"error": f"Unknown methodology: {methodology}"}))
            return 1
        note_types = METHODOLOGIES[methodology].get("note_types", {})
        print(json.dumps(note_types, indent=2))
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

    # Determine if wizard mode (needed early for git init decision)
    use_wizard = args.wizard or (args.methodology is None and not args.defaults)

    # Handle reset flag
    init_git_after_reset = False
    if args.reset:
        if detection["exists"]:
            print(f"\nResetting vault at: {vault_path}")
            if is_interactive():
                confirm = input("Are you sure? This will delete content! (yes/no): ")
                if confirm.strip().lower() != "yes":
                    print("Reset cancelled.")
                    return 0
            reset_vault(vault_path)

            # After reset, check if .git is missing and offer to initialize
            # Only prompt if:
            # - .git doesn't exist
            # - --git flag not used (which forces git init)
            # - Not in wizard mode (wizard prompts for git init itself)
            # - Interactive mode
            git_path = vault_path / ".git"
            if not git_path.exists() and not args.git and not use_wizard and is_interactive():
                init_git_after_reset = wizard_step_git_init()

    # Parse note types filter
    note_types_filter = None
    if args.note_types:
        note_types_filter = [t.strip() for t in args.note_types.split(",") if t.strip()]

    # Parse core properties filter
    core_properties_filter = None
    if args.core_properties:
        core_properties_filter = [p.strip() for p in args.core_properties.split(",") if p.strip()]

    # Parse custom properties
    custom_properties_list = None
    if args.custom_properties:
        custom_properties_list = [p.strip() for p in args.custom_properties.split(",") if p.strip()]

    # Parse per-type properties (format: type1:prop1,prop2;type2:prop3)
    per_type_properties: dict[str, list[str]] = {}
    if args.per_type_props:
        for type_spec in args.per_type_props.split(";"):
            if ":" in type_spec:
                type_name, props = type_spec.split(":", 1)
                type_name = type_name.strip()
                prop_list = [p.strip() for p in props.split(",") if p.strip()]
                if type_name and prop_list:
                    per_type_properties[type_name] = prop_list

    try:
        init_vault(
            vault_path,
            args.methodology,
            args.dry_run,
            use_wizard=use_wizard,
            use_defaults=args.defaults,
            note_types_filter=note_types_filter,
            core_properties_filter=core_properties_filter,
            custom_properties=custom_properties_list,
            per_type_properties=per_type_properties if per_type_properties else None,
            ranking_system=args.ranking_system,
        )

        # Handle git initialization for non-wizard mode
        # (wizard handles it via config.init_git)
        should_init_git = args.git or init_git_after_reset
        if should_init_git and not use_wizard:
            print("\nInitializing git repository...")
            init_git_repo(vault_path, args.methodology or "minimal", args.dry_run)

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
