"""
Note type configuration dataclass.

Defines the NoteTypeConfig class used to represent note type definitions
loaded from settings.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NoteTypeConfig:
    """Configuration for a single note type.

    This class represents the configuration of a note type as defined in
    settings.yaml. It includes folder hints for detection, property
    definitions, and validation rules.

    Attributes:
        name: The unique identifier/name of the note type (e.g., "project", "map")
        description: Human-readable description of this note type
        folder_hints: List of folder patterns used to detect this note type
        required_properties: Properties that must be present in notes of this type
        optional_properties: Properties that may optionally be present
        validation: Custom validation rules for this note type
        icon: Icon identifier for UI display
        is_custom: Whether this is a user-defined custom type
        inherit_core: Whether this type inherits core_properties
    """

    name: str
    description: str
    folder_hints: list[str]
    required_properties: list[str] = field(default_factory=list)
    optional_properties: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    icon: str = "file"
    is_custom: bool = False
    inherit_core: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for settings.yaml.

        Returns:
            Dictionary representation suitable for YAML serialization.
        """
        return {
            "description": self.description,
            "folder_hints": self.folder_hints,
            "properties": {
                "additional_required": self.required_properties,
                "optional": self.optional_properties,
            },
            "validation": self.validation,
            "icon": self.icon,
        }

    @classmethod
    def from_dict(
        cls,
        name: str,
        config: dict[str, Any],
        core_properties: list[str] | None = None,
    ) -> NoteTypeConfig:
        """Create NoteTypeConfig from a settings dictionary.

        Args:
            name: The note type name/key
            config: Configuration dictionary from settings.yaml
            core_properties: List of core properties for inheritance

        Returns:
            Configured NoteTypeConfig instance
        """
        core_properties = core_properties or []
        props = config.get("properties", {})
        inherit_core = config.get("inherit_core", True)

        # Compute required properties based on inheritance
        if inherit_core:
            additional_required = props.get("additional_required", [])
            explicit_required = props.get("required", [])

            if explicit_required and not additional_required:
                # Old format: required contains everything
                required_properties = explicit_required
            else:
                # New format: core + additional
                required_properties = list(core_properties) + additional_required
        else:
            # No inheritance: use explicit required list only
            required_properties = props.get("required", [])

        return cls(
            name=name,
            description=config.get("description", ""),
            folder_hints=config.get("folder_hints", []),
            required_properties=required_properties,
            optional_properties=props.get("optional", []),
            validation=config.get("validation", {}),
            icon=config.get("icon", "file"),
            is_custom=config.get("is_custom", False),
            inherit_core=inherit_core,
        )

    def get_all_properties(self) -> list[str]:
        """Get all properties (required + optional).

        Returns:
            Combined list of required and optional properties.
        """
        return self.required_properties + self.optional_properties
