"""
Settings and validation rules dataclasses.

Defines the Settings and ValidationRules classes used to represent
the user configuration loaded from settings.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skills.core.models.note_type import NoteTypeConfig


@dataclass
class ValidationRules:
    """Validation rules from settings.

    Configures how note validation should behave.

    Attributes:
        require_core_properties: Whether to enforce core properties on all notes
        allow_empty_properties: List of properties that can be empty
        strict_types: Whether to enforce strict type checking
        check_templates: Whether to validate templates
        check_up_links: Whether to validate up-links
        check_inbox_no_frontmatter: Whether inbox notes should have no frontmatter
    """

    require_core_properties: bool = True
    allow_empty_properties: list[str] = field(default_factory=list)
    strict_types: bool = True
    check_templates: bool = True
    check_up_links: bool = True
    check_inbox_no_frontmatter: bool = True

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ValidationRules:
        """Create ValidationRules from a settings dictionary.

        Args:
            raw: Raw validation dictionary from settings.yaml

        Returns:
            Configured ValidationRules instance
        """
        return cls(
            require_core_properties=raw.get("require_core_properties", True),
            allow_empty_properties=raw.get("allow_empty_properties", []),
            strict_types=raw.get("strict_types", True),
            check_templates=raw.get("check_templates", True),
            check_up_links=raw.get("check_up_links", True),
            check_inbox_no_frontmatter=raw.get("check_inbox_no_frontmatter", True),
        )


@dataclass
class Settings:
    """User settings loaded from settings.yaml.

    This is the primary configuration object containing all user settings
    for the Obsidian vault.

    Attributes:
        version: Settings file version
        methodology: PKM methodology name (e.g., "lyt-ace", "para")
        core_properties: List of properties required in all notes
        note_types: Dictionary of note type configurations
        validation: Validation rules configuration
        folder_structure: Folder path definitions
        up_links: Up-link mappings by folder
        exclude_paths: Paths to exclude from validation
        exclude_files: Files to exclude from validation
        exclude_patterns: Glob patterns to exclude
        formats: Format configurations
        logging: Logging configuration
        raw: Original YAML dict for access to custom fields
    """

    version: str
    methodology: str
    core_properties: list[str]
    note_types: dict[str, NoteTypeConfig]
    validation: ValidationRules
    folder_structure: dict[str, Any]
    up_links: dict[str, str]
    exclude_paths: list[str]
    exclude_files: list[str]
    exclude_patterns: list[str]
    formats: dict[str, Any]
    logging: dict[str, Any]
    raw: dict[str, Any]

    def get_note_type(self, type_name: str) -> NoteTypeConfig | None:
        """Get configuration for a specific note type.

        Args:
            type_name: Name of the note type

        Returns:
            NoteTypeConfig if found, None otherwise
        """
        return self.note_types.get(type_name)

    def get_all_properties_for_type(self, type_name: str) -> list[str]:
        """Get all properties (required + optional) for a note type.

        Args:
            type_name: Name of the note type

        Returns:
            List of all property names for the type
        """
        note_type = self.get_note_type(type_name)
        if not note_type:
            return self.core_properties.copy()
        return note_type.required_properties + note_type.optional_properties

    def is_excluded_path(self, path_str: str) -> bool:
        """Check if a path should be excluded from validation.

        Args:
            path_str: String representation of the path

        Returns:
            True if the path should be excluded
        """
        return any(excluded in path_str for excluded in self.exclude_paths)
