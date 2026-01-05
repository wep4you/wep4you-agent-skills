"""
Settings validation for Obsidian vault configuration.

Provides functions to validate settings structure and check file paths
against exclusion rules.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skills.core.models.settings import Settings


def validate_settings(settings: Settings) -> list[str]:
    """Validate settings structure.

    Args:
        settings: Settings object to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Check version
    if not settings.version:
        errors.append("Missing 'version' in settings")

    # Check core_properties
    if not settings.core_properties:
        errors.append("Missing or empty 'core_properties'")

    # Check required properties in note types
    for type_name, config in settings.note_types.items():
        if not config.required_properties:
            errors.append(f"Note type '{type_name}' has no required properties")

        # Validate inheritance
        if config.inherit_core:
            # When inheriting, required_properties should include all core properties
            missing_core = [
                p for p in settings.core_properties if p not in config.required_properties
            ]
            if missing_core:
                errors.append(
                    f"Note type '{type_name}' has inherit_core=True but "
                    f"missing core properties: {missing_core}"
                )

    return errors


def infer_note_type_from_path(settings: Settings, file_path: Path) -> str | None:
    """Infer note type from file path based on folder hints.

    Args:
        settings: Settings object with note type configurations
        file_path: Path to the file to check

    Returns:
        Note type name if matched, None otherwise
    """
    file_path_str = str(file_path)

    for type_name, config in settings.note_types.items():
        for hint in config.folder_hints:
            if hint in file_path_str:
                return type_name

    return None


def get_up_link_for_path(settings: Settings, file_path: Path) -> str | None:
    """Get expected UP link for a file based on its path.

    Args:
        settings: Settings object with up_links configuration
        file_path: Path to the file to check

    Returns:
        UP link value if path matches a pattern, None otherwise
    """
    file_path_str = str(file_path)

    for folder_pattern, up_link in settings.up_links.items():
        if folder_pattern in file_path_str:
            return up_link

    return None


def should_exclude(settings: Settings, file_path: Path) -> bool:
    """Check if a file should be excluded from validation.

    Args:
        settings: Settings object with exclusion rules
        file_path: Path to check for exclusion

    Returns:
        True if the file should be excluded
    """
    file_path_str = str(file_path)

    # Check excluded paths
    for excluded_path in settings.exclude_paths:
        if excluded_path in file_path_str:
            return True

    # Check excluded files
    if file_path.name in settings.exclude_files:
        return True

    # Check excluded patterns (glob-style matching)
    for pattern in settings.exclude_patterns:
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

    # Always exclude system documentation files in vault root
    # These files use type: "system" and don't follow note type validation rules
    system_files = {"AGENTS.md", "CLAUDE.md", "README.md", "Home.md"}
    if file_path.name in system_files:
        # Only exclude if in vault root (check no subfolder in path)
        # If none of these methodology folders appear in path, file is in vault root
        methodology_folders = [
            "Atlas/",
            "Calendar/",
            "Efforts/",
            "Projects/",
            "Areas/",
            "Resources/",
            "Archives/",
            "Notes/",
            "Daily/",
            "Zettel/",
            "References/",
            "Literature/",
        ]
        if not any(folder in file_path_str for folder in methodology_folders):
            return True

    return False


def is_inbox_path(settings: Settings, file_path: Path) -> bool:
    """Check if a file is in the inbox (no frontmatter required).

    Args:
        settings: Settings object with folder structure configuration
        file_path: Path to check

    Returns:
        True if the file is in the inbox folder
    """
    inbox_path = settings.folder_structure.get("inbox", "+/")
    return inbox_path in str(file_path)
