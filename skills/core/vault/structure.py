"""
Vault folder structure utilities.

Provides functions for creating and managing folder structures
in Obsidian vaults based on PKM methodologies.
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


def ensure_folder_exists(folder_path: Path, dry_run: bool = False) -> bool:
    """Ensure a folder exists, creating it if necessary.

    Creates the folder and any parent directories if they don't exist.

    Args:
        folder_path: Path to the folder to create
        dry_run: If True, only print what would be done

    Returns:
        True if folder exists or was created, False on error

    Example:
        >>> ensure_folder_exists(Path("/vault/Projects"))
        True
    """
    if folder_path.exists():
        return True

    if dry_run:
        print(f"  [DRY RUN] Would create: {folder_path}")
        return True

    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"  Error creating folder {folder_path}: {e}")
        return False


def get_methodology_folders(
    methodology: str,
    note_types_filter: list[str] | None = None,
) -> list[str]:
    """Get list of folders to create based on methodology and note types.

    Returns the folders defined for a methodology, optionally filtered
    to only include folders needed for specific note types.

    Args:
        methodology: Methodology key (e.g., 'lyt-ace', 'para')
        note_types_filter: List of note type names to include (None = all)

    Returns:
        List of folder paths to create (relative to vault root)

    Raises:
        ValueError: If methodology is not recognized

    Example:
        >>> get_methodology_folders("para")
        ['Projects', 'Areas', 'Resources', 'Archive', '+', 'x/templates', 'x/bases']
    """
    if methodology not in METHODOLOGIES:
        available = ", ".join(METHODOLOGIES.keys())
        raise ValueError(f"Unknown methodology: {methodology}. Available: {available}")

    method_config = METHODOLOGIES[methodology]
    all_folders: list[str] = method_config["folders"]
    note_types: dict[str, Any] = method_config.get("note_types", {})

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
) -> list[Path]:
    """Create folder structure based on methodology and selected note types.

    Creates all folders defined for the methodology, including system
    folders for Obsidian and Claude configuration.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key (e.g., 'lyt-ace', 'para')
        dry_run: If True, only print what would be created without creating
        note_types_filter: List of note type names to include (None = all)

    Returns:
        List of created folder paths

    Raises:
        ValueError: If methodology is not recognized

    Example:
        >>> create_folder_structure(Path("/vault"), "para")
        [Path('/vault/Projects'), Path('/vault/Areas'), ...]
    """
    if methodology not in METHODOLOGIES:
        available = ", ".join(METHODOLOGIES.keys())
        raise ValueError(f"Unknown methodology: {methodology}. Available: {available}")

    method_config = METHODOLOGIES[methodology]
    folders = get_methodology_folders(methodology, note_types_filter)
    created_folders: list[Path] = []

    print(f"\nCreating {method_config['name']} folder structure...")

    for folder in folders:
        folder_path = vault_path / folder
        if dry_run:
            print(f"  [DRY RUN] Would create: {folder_path}")
        else:
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {folder_path}")
            created_folders.append(folder_path)

    # Create system folders
    system_folders = [".obsidian", ".claude", ".claude/logs"]
    for folder in system_folders:
        folder_path = vault_path / folder
        if dry_run:
            print(f"  [DRY RUN] Would create: {folder_path}")
        else:
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {folder_path}")
            created_folders.append(folder_path)

    return created_folders
