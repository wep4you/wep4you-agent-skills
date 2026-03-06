"""
Ranking system utilities for note types.

Provides functions to apply ranking systems (rank or priority)
to project-like notes in the vault configuration.
"""

from __future__ import annotations

import copy
from typing import Any

# Note types that support ranking (project-like notes)
RANKABLE_NOTE_TYPES = frozenset({"project", "area"})


def apply_ranking_system(
    note_types: dict[str, dict[str, Any]], ranking_system: str
) -> dict[str, dict[str, Any]]:
    """Apply ranking system choice to note types.

    Adds either 'rank' or 'priority' as a required property for project-like notes.
    This is used to configure how projects are prioritized in the vault.

    Args:
        note_types: Dictionary of note type configurations
        ranking_system: Either "rank" (1-5 numeric) or "priority" (text)

    Returns:
        Modified note_types with ranking property added (deep copy)

    Example:
        >>> types = {"project": {"properties": {"additional_required": [], "optional": []}}}
        >>> result = apply_ranking_system(types, "rank")
        >>> "rank" in result["project"]["properties"]["additional_required"]
        True
    """
    modified = copy.deepcopy(note_types)

    for type_name, type_config in modified.items():
        # Only apply to project-like notes
        if type_name not in RANKABLE_NOTE_TYPES:
            continue

        props = type_config.get("properties", {})
        additional_required = list(props.get("additional_required", []))
        optional = list(props.get("optional", []))

        if ranking_system == "rank":
            # Add rank as required (if not already there)
            if "rank" not in additional_required:
                additional_required.append("rank")
            # Remove priority from optional if present
            if "priority" in optional:
                optional.remove("priority")
        else:
            # Move priority from optional to required
            if "priority" not in additional_required:
                additional_required.append("priority")
            if "priority" in optional:
                optional.remove("priority")

        # Update the config
        if "properties" not in type_config:
            type_config["properties"] = {}
        type_config["properties"]["additional_required"] = additional_required
        type_config["properties"]["optional"] = optional

    return modified
