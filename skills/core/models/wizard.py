"""
Wizard configuration dataclass.

Defines the WizardConfig class used to collect configuration
from interactive wizard flows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skills.core.models.note_type import NoteTypeConfig


@dataclass
class WizardConfig:
    """Configuration collected from the wizard flow.

    This class collects and stores all the configuration options
    gathered during an interactive setup wizard.

    Attributes:
        methodology: Selected PKM methodology name
        note_types: Dictionary of note type configurations
        core_properties: List of core properties for all notes
        mandatory_properties: Properties that are always required
        optional_properties: Properties that are optional
        custom_properties: User-defined custom properties
        custom_note_types: User-defined custom note types
        per_type_properties: Per-type property overrides
        create_samples: Whether to create sample notes
        reset_vault: Whether to reset existing vault content
        ranking_system: Ranking system choice ("rank" or "priority")
        init_git: Whether to initialize a git repository
    """

    methodology: str
    note_types: dict[str, dict[str, Any]]
    core_properties: list[str]
    mandatory_properties: list[str] = field(default_factory=list)
    optional_properties: list[str] = field(default_factory=list)
    custom_properties: list[str] = field(default_factory=list)
    custom_note_types: dict[str, NoteTypeConfig] = field(default_factory=dict)
    per_type_properties: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    create_samples: bool = True
    reset_vault: bool = False
    ranking_system: str = "rank"  # "rank" (1-5) or "priority" (text)
    init_git: bool = False

    def get_all_properties(self) -> list[str]:
        """Get all unique properties (core + mandatory + optional + custom).

        Returns:
            Deduplicated list of all property names
        """
        all_props = set(self.core_properties)
        all_props.update(self.mandatory_properties)
        all_props.update(self.optional_properties)
        all_props.update(self.custom_properties)
        return list(all_props)

    def get_properties_for_type(self, type_name: str) -> dict[str, list[str]]:
        """Get property configuration for a specific note type.

        Args:
            type_name: Name of the note type

        Returns:
            Dictionary with 'required' and 'optional' property lists
        """
        if type_name in self.per_type_properties:
            return self.per_type_properties[type_name]

        # Default: return core + mandatory as required
        return {
            "required": self.core_properties + self.mandatory_properties,
            "optional": self.optional_properties,
        }
