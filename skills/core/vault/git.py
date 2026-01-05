"""
Git utilities for Obsidian vault operations.

Provides functions for initializing and managing git repositories
within Obsidian vaults.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Default .gitignore content for Obsidian vaults
DEFAULT_GITIGNORE = """# Obsidian
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


def is_git_repo(path: Path) -> bool:
    """Check if a directory is a git repository.

    Args:
        path: Path to check

    Returns:
        True if the path contains a .git directory, False otherwise

    Example:
        >>> is_git_repo(Path("/path/to/repo"))
        True
        >>> is_git_repo(Path("/path/to/non-repo"))
        False
    """
    if not path.exists():
        return False
    return (path / ".git").is_dir()


def create_gitignore(vault_path: Path, dry_run: bool = False) -> bool:
    """Create .gitignore file for the vault if it doesn't exist.

    Creates a default .gitignore file suitable for Obsidian vaults,
    ignoring workspace files, system files, and temporary files.

    Args:
        vault_path: Path to the vault root
        dry_run: If True, only print what would be done

    Returns:
        True if file was created or already exists, False on error

    Example:
        >>> create_gitignore(Path("/vault"))
        True
    """
    gitignore_path = vault_path / ".gitignore"

    # Skip if already exists
    if gitignore_path.exists():
        return True

    if dry_run:
        print("[DRY RUN] Would create .gitignore")
        return True

    try:
        gitignore_path.write_text(DEFAULT_GITIGNORE)
        print("Created: .gitignore")
        return True
    except OSError as e:
        print(f"Error creating .gitignore: {e}")
        return False


def init_git_repo(
    vault_path: Path,
    commit_message: str = "Initial vault setup",
    dry_run: bool = False,
) -> bool:
    """Initialize a git repository in the vault.

    Initializes git and makes an initial commit. Creates .gitignore if needed.

    Args:
        vault_path: Path to the vault root
        commit_message: Message for the initial commit
        dry_run: If True, only print what would be done

    Returns:
        True if successful, False if git not available or failed

    Example:
        >>> init_git_repo(Path("/vault"), "Initial setup with PARA")
        True
    """
    # Check if git is available and get full path
    git_path = shutil.which("git")
    if not git_path:
        print("  Git not found in PATH, skipping git initialization")
        return False

    # Check if already a git repo
    if is_git_repo(vault_path):
        print("  Git repository already exists, skipping")
        return True

    if dry_run:
        print("[DRY RUN] Would initialize git repository")
        print(f'[DRY RUN] Would commit: "{commit_message}"')
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
        print("Initialized git repository")

        # Stage all files
        subprocess.run(  # noqa: S603
            [git_path, "add", "."],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )

        # Create initial commit
        subprocess.run(  # noqa: S603
            [git_path, "commit", "-m", commit_message],
            cwd=vault_path,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f'Created initial commit: "{commit_message}"')

        return True
    except subprocess.CalledProcessError as e:
        print(f"  Git initialization failed: {e}")
        return False
