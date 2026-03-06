"""
Vault detection utilities for Obsidian vaults.

Provides functions to detect existing vaults, check Obsidian compatibility,
and find the vault root directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def detect_vault(vault_path: Path) -> dict[str, Any]:
    """Detect existing vault state and configuration.

    Examines a directory to determine if it contains an Obsidian vault,
    Claude configuration, and existing content.

    Args:
        vault_path: Path to check for vault presence

    Returns:
        Dictionary with vault state information:
            - exists: Whether the path exists
            - has_obsidian: Whether .obsidian/ directory exists
            - has_claude_config: Whether .claude/ directory exists
            - has_content: Whether non-hidden folders/files exist
            - folder_count: Number of non-hidden folders
            - file_count: Number of non-hidden files
            - current_methodology: Methodology from settings.yaml (if present)

    Example:
        >>> detect_vault(Path("/path/to/vault"))
        {'exists': True, 'has_obsidian': True, 'has_claude_config': True, ...}
    """
    if not vault_path.exists():
        return {
            "exists": False,
            "has_obsidian": False,
            "has_claude_config": False,
            "has_content": False,
            "folder_count": 0,
            "file_count": 0,
            "current_methodology": None,
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
                settings = yaml.safe_load(f)
                current_methodology = settings.get("methodology") if settings else None
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


def is_obsidian_vault(vault_path: Path) -> bool:
    """Check if a directory is an Obsidian vault.

    A directory is considered an Obsidian vault if it contains
    the .obsidian configuration directory.

    Args:
        vault_path: Path to check

    Returns:
        True if the path contains .obsidian directory, False otherwise

    Example:
        >>> is_obsidian_vault(Path("/path/to/vault"))
        True
        >>> is_obsidian_vault(Path("/path/to/regular/dir"))
        False
    """
    if not vault_path.exists():
        return False
    return (vault_path / ".obsidian").is_dir()


def find_vault_root(start_path: Path) -> Path | None:
    """Find the vault root directory by searching upward.

    Searches from the given path upward through parent directories
    to find the vault root (directory containing .obsidian/).

    Args:
        start_path: Starting path to search from

    Returns:
        Path to the vault root if found, None if not in a vault

    Example:
        >>> find_vault_root(Path("/vault/Projects/some_project"))
        Path('/vault')
        >>> find_vault_root(Path("/not/a/vault"))
        None
    """
    current = start_path.resolve()

    # Search upward to find vault root
    while current != current.parent:
        if (current / ".obsidian").is_dir():
            return current
        current = current.parent

    # Check the root directory itself
    if (current / ".obsidian").is_dir():
        return current

    return None
