"""
Path utilities for Obsidian vault operations.

Provides functions for generating consistent filenames and links
for MOC (Map of Content) files and other vault structures.
"""

from __future__ import annotations


def get_moc_filename(folder_path: str) -> str:
    """Get the MOC (Map of Content) filename for a folder.

    MOC files use a consistent naming convention with an underscore prefix
    and _MOC suffix to distinguish them from regular notes.

    Handles both simple folder names and full paths - extracts the last
    component of the path to use as the folder name.

    Args:
        folder_path: A folder path like "Efforts/Projects" or just "Projects"

    Returns:
        MOC filename like '_Projects_MOC.md'

    Example:
        >>> get_moc_filename("Projects")
        '_Projects_MOC.md'
        >>> get_moc_filename("Atlas/Dots")
        '_Dots_MOC.md'
    """
    folder_name = extract_folder_name(folder_path)
    return f"_{folder_name}_MOC.md"


def get_moc_link(folder_name: str) -> str:
    """Get the wikilink to a folder's MOC file (without path).

    Returns an Obsidian-style wikilink that can be used in frontmatter
    or as a reference in note content.

    Args:
        folder_name: The folder name (last component of path)

    Returns:
        Wikilink like '[[_Projects_MOC]]'

    Example:
        >>> get_moc_link("Projects")
        '[[_Projects_MOC]]'
        >>> get_moc_link("Areas")
        '[[_Areas_MOC]]'
    """
    return f"[[_{folder_name}_MOC]]"


def extract_folder_name(folder_path: str) -> str:
    """Extract the folder name from a path string.

    Handles both simple folder names and paths with slashes.

    Args:
        folder_path: A folder path like "Efforts/Projects" or just "Projects"

    Returns:
        The last component of the path (folder name)

    Example:
        >>> extract_folder_name("Efforts/Projects")
        'Projects'
        >>> extract_folder_name("Projects")
        'Projects'
    """
    return folder_path.split("/")[-1] if "/" in folder_path else folder_path
