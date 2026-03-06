#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Interactive wizard for Obsidian vault initialization.

This module provides the wizard step functions for configuring vault
initialization options interactively. It is designed to be self-contained
and imports shared models from skills.core.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add repository root to path for importing methodology loader
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config.methodologies.loader import METHODOLOGIES  # noqa: E402
from skills.core.models import NoteTypeConfig, WizardConfig  # noqa: E402
from skills.core.utils import apply_ranking_system  # noqa: E402

# =============================================================================
# Wizard Step Functions
# =============================================================================


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


def wizard_step_git_reset() -> str:  # pragma: no cover
    """Ask user how to handle git during reset.

    Returns:
        'keep' to keep .git and commit changes,
        'reset' to delete .git and create fresh repo,
        'skip' to not touch git at all
    """
    print()
    print("┌" + "─" * 58 + "┐")
    print("│" + " Git Repository Detected".ljust(58) + "│")
    print("├" + "─" * 58 + "┤")
    print("│".ljust(59) + "│")
    print("│  How should git be handled?".ljust(59) + "│")
    print("│".ljust(59) + "│")
    print("│  [k] Keep history - commit new changes".ljust(59) + "│")
    print("│  [r] Reset - delete .git and start fresh".ljust(59) + "│")
    print("│  [s] Skip - don't touch git".ljust(59) + "│")
    print("│".ljust(59) + "│")
    print("└" + "─" * 58 + "┘")

    while True:
        choice = input("\nChoice [k/r/s] (default: k): ").strip().lower()
        if choice in ("", "k", "keep"):
            return "keep"
        elif choice in ("r", "reset"):
            return "reset"
        elif choice in ("s", "skip"):
            return "skip"
        print("  Please enter 'k', 'r', or 's'.")


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


# =============================================================================
# Vault Detection Functions
# =============================================================================


def detect_existing_vault(vault_path: Path) -> dict[str, Any]:
    """Detect existing vault state.

    Args:
        vault_path: Path to check

    Returns:
        Dictionary with vault state information
    """
    import yaml as yaml_lib

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
            with open(settings_file) as f:
                settings = yaml_lib.safe_load(f)
                current_methodology = settings.get("methodology")
        except (OSError, yaml_lib.YAMLError):
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


# =============================================================================
# Full Wizard Flow
# =============================================================================


def wizard_full_flow(vault_path: Path) -> WizardConfig | None:  # pragma: no cover
    """Run the complete interactive wizard.

    Args:
        vault_path: Path to the vault being initialized

    Returns:
        WizardConfig with all user choices, or None if aborted
    """
    from skills.init.scripts.vault_utils import reset_vault

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
