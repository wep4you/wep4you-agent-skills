"""
Core utility functions for Obsidian vault skills.

This module provides shared utility functions used across skills:
- Ranking system utilities (apply_ranking_system)
- Path utilities (get_moc_filename, get_moc_link, extract_folder_name)
"""

from skills.core.utils.paths import extract_folder_name, get_moc_filename, get_moc_link
from skills.core.utils.ranking import RANKABLE_NOTE_TYPES, apply_ranking_system

__all__ = [
    "RANKABLE_NOTE_TYPES",
    "apply_ranking_system",
    "extract_folder_name",
    "get_moc_filename",
    "get_moc_link",
]
