#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Vault utility functions for Obsidian vault initialization.

This module provides helper functions for vault backup, reset, and
content folder management during initialization.
"""

from __future__ import annotations

import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Add repository root to path for importing methodology loader
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config.methodologies.loader import METHODOLOGIES  # noqa: E402

# Folders protected during vault reset (never deleted automatically)
# Note: .git is protected by default - user can choose to reset it separately
PROTECTED_FOLDERS = frozenset({".obsidian", ".git", ".github", ".vscode"})

# Folders to exclude from backups (large or regenerable)
BACKUP_EXCLUDE_FOLDERS = frozenset({".obsidian", ".git", ".github", ".vscode"})

# Files protected during vault reset (kept and updated instead of deleted)
PROTECTED_FILES = frozenset({"README.md", "AGENTS.md", "CLAUDE.md", "HOME.md", ".gitignore"})


def create_vault_backup(vault_path: Path) -> Path | None:
    """Create a ZIP backup of the vault before reset.

    Args:
        vault_path: Path to the vault

    Returns:
        Path to the backup file, or None if backup failed
    """
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

        print(f"  Backup saved: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"  Backup failed: {e}")
        return None


def reset_vault(vault_path: Path) -> None:
    """Reset vault to clean state.

    Creates a backup ZIP before deleting any files.
    Protected folders (.obsidian, .git, .github, .vscode) are preserved.
    Protected files (README.md, AGENTS.md, CLAUDE.md, HOME.md, .gitignore)
    are preserved and will be updated during initialization.

    Args:
        vault_path: Path to the vault
    """
    # Create backup first
    backup_path = create_vault_backup(vault_path)
    if backup_path is None:
        print("  Continuing without backup...")

    print("\nResetting vault...")

    for item in vault_path.iterdir():
        # Skip protected system folders (.obsidian, .git, .github, .vscode)
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

    print("  Vault reset complete")


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
