"""
Core content generation modules for Obsidian vault skills.

This module provides shared generation functions for creating frontmatter,
templates, MOC files, and note content.
"""

from skills.core.generation.content import (
    generate_home_note,
    generate_note_content,
    generate_sample_notes,
)
from skills.core.generation.frontmatter import (
    DEFAULT_CORE_PROPERTIES,
    DEFAULT_TYPE_PROPERTIES,
    generate_frontmatter,
    get_property_default,
    parse_frontmatter,
    update_frontmatter,
)
from skills.core.generation.moc import (
    FOLDER_DESCRIPTIONS,
    create_folder_mocs,
    generate_moc_content,
    get_moc_filename,
    update_moc,
)
from skills.core.generation.templates import (
    create_template_notes,
    generate_template_note,
    load_template,
    render_template,
)

__all__ = [
    "DEFAULT_CORE_PROPERTIES",
    "DEFAULT_TYPE_PROPERTIES",
    "FOLDER_DESCRIPTIONS",
    "create_folder_mocs",
    "create_template_notes",
    "generate_frontmatter",
    "generate_home_note",
    "generate_moc_content",
    "generate_note_content",
    "generate_sample_notes",
    "generate_template_note",
    "get_moc_filename",
    "get_property_default",
    "load_template",
    "parse_frontmatter",
    "render_template",
    "update_frontmatter",
    "update_moc",
]
