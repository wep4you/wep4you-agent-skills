"""
Core settings loading and validation for Obsidian vault skills.

This module provides shared settings operations used across all skills.
"""

from skills.core.settings.loader import (
    SETTINGS_FILE,
    create_backup,
    create_default_settings,
    diff_settings,
    get_backup_dir,
    get_default_settings_dict,
    load_settings,
    save_settings,
    set_setting,
    settings_exist,
)
from skills.core.settings.validation import (
    get_up_link_for_path,
    infer_note_type_from_path,
    is_inbox_path,
    should_exclude,
    validate_settings,
)

__all__ = [
    "SETTINGS_FILE",
    "create_backup",
    "create_default_settings",
    "diff_settings",
    "get_backup_dir",
    "get_default_settings_dict",
    "get_up_link_for_path",
    "infer_note_type_from_path",
    "is_inbox_path",
    "load_settings",
    "save_settings",
    "set_setting",
    "settings_exist",
    "should_exclude",
    "validate_settings",
]
