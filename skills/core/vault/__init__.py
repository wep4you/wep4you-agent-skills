"""
Core vault operations for Obsidian vault skills.

This module provides shared vault functions for detection, folder structure
management, and git operations.
"""

from skills.core.vault.detection import (
    detect_vault,
    find_vault_root,
    is_obsidian_vault,
)
from skills.core.vault.git import (
    create_gitignore,
    init_git_repo,
    is_git_repo,
)
from skills.core.vault.structure import (
    create_folder_structure,
    ensure_folder_exists,
    get_methodology_folders,
)

__all__ = [
    "create_folder_structure",
    "create_gitignore",
    "detect_vault",
    "ensure_folder_exists",
    "find_vault_root",
    "get_methodology_folders",
    "init_git_repo",
    "is_git_repo",
    "is_obsidian_vault",
]
