"""
Frontmatter generation and parsing utilities.

Provides functions for creating, parsing, and updating YAML frontmatter
in Obsidian markdown notes.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import yaml

# Default core properties with their specifications
DEFAULT_CORE_PROPERTIES = {
    "type": {"required": True, "type": "string", "description": "Note type classification"},
    "up": {
        "required": False,
        "type": "wikilink",
        "description": "Parent note in hierarchy",
    },
    "created": {
        "required": True,
        "type": "date",
        "format": "YYYY-MM-DD",
        "description": "Creation date",
    },
    "daily": {
        "required": False,
        "type": "wikilink",
        "description": "Associated daily note",
    },
    "collection": {
        "required": False,
        "type": "wikilink",
        "description": "Collection classification",
    },
    "related": {
        "required": False,
        "type": "list[wikilink]",
        "description": "Related notes",
    },
}

# Default type-specific properties
DEFAULT_TYPE_PROPERTIES = {
    "dot": {
        "tags": {"required": False, "type": "list[string]", "description": "Topic tags"},
    },
    "map": {
        "tags": {"required": False, "type": "list[string]", "description": "Topic tags"},
        "summary": {
            "required": False,
            "type": "string",
            "description": "Map summary",
        },
    },
    "source": {
        "author": {"required": False, "type": "string", "description": "Source author"},
        "url": {"required": False, "type": "string", "description": "Source URL"},
        "published": {
            "required": False,
            "type": "date",
            "format": "YYYY-MM-DD",
            "description": "Publication date",
        },
    },
    "project": {
        "status": {
            "required": True,
            "type": "string",
            "values": ["active", "completed", "archived", "planning"],
            "description": "Project status",
        },
        "deadline": {
            "required": False,
            "type": "date",
            "format": "YYYY-MM-DD",
            "description": "Project deadline",
        },
    },
    "daily": {
        "mood": {
            "required": False,
            "type": "string",
            "values": ["great", "good", "neutral", "bad"],
            "description": "Daily mood",
        },
    },
}


def generate_frontmatter(
    note_type: str,
    *,
    up_link: str | None = None,
    created_date: date | None = None,
    daily_link: str | None = None,
    tags: list[str] | None = None,
    collection: str | None = None,
    related: list[str] | None = None,
    additional_properties: dict[str, Any] | None = None,
    optional_commented: list[str] | None = None,
    core_properties: list[str] | None = None,
) -> str:
    """Generate YAML frontmatter for a note.

    Args:
        note_type: The type of note (map, dot, source, etc.)
        up_link: Parent note wikilink
        created_date: Creation date (defaults to today)
        daily_link: Associated daily note wikilink
        tags: List of tags
        collection: Collection wikilink
        related: List of related note wikilinks
        additional_properties: Dict of additional properties to include
        optional_commented: List of property names to add as commented placeholders
        core_properties: List of core property names to include (defaults to all)

    Returns:
        YAML frontmatter string with --- delimiters
    """
    if created_date is None:
        created_date = date.today()

    # Default core properties if not specified
    default_core = ["type", "up", "created", "daily", "tags", "collection", "related"]
    active_props = core_properties if core_properties is not None else default_core

    lines = ["---"]

    # Type is always first
    lines.append(f'type: "{note_type}"')

    # Add up link
    if "up" in active_props and up_link:
        lines.append(f'up: "{up_link}"')

    # Add created date
    if "created" in active_props:
        lines.append(f'created: "{created_date.isoformat()}"')

    # Add daily link
    if "daily" in active_props and daily_link:
        lines.append(f'daily: "{daily_link}"')

    # Add tags
    if "tags" in active_props:
        if tags:
            tag_str = ", ".join(tags)
            lines.append(f"tags: [{tag_str}]")
        else:
            lines.append("tags: []")

    # Add collection
    if "collection" in active_props:
        if collection:
            lines.append(f'collection: "{collection}"')
        else:
            lines.append('collection: ""')

    # Add related
    if "related" in active_props:
        if related:
            related_str = ", ".join(f'"{r}"' for r in related)
            lines.append(f"related: [{related_str}]")
        else:
            lines.append("related: []")

    # Add additional properties
    if additional_properties:
        for prop, value in additional_properties.items():
            if isinstance(value, str):
                lines.append(f'{prop}: "{value}"')
            elif isinstance(value, bool):
                lines.append(f"{prop}: {str(value).lower()}")
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{prop}: []")
                else:
                    items = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                    lines.append(f"{prop}: [{items}]")
            elif value is None:
                lines.append(f'{prop}: ""')
            else:
                lines.append(f"{prop}: {value}")

    # Add optional properties as comments
    if optional_commented:
        for prop in optional_commented:
            lines.append(f"# {prop}: ")

    lines.append("---")

    return "\n".join(lines)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse frontmatter from markdown content.

    Args:
        content: Full markdown content with frontmatter

    Returns:
        Tuple of (frontmatter dict, remaining content)

    Raises:
        ValueError: If frontmatter is malformed
    """
    content = content.strip()

    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    end_match = content.find("\n---", 3)
    if end_match == -1:
        raise ValueError("Malformed frontmatter: missing closing ---")

    frontmatter_str = content[4:end_match]
    remaining = content[end_match + 4 :].lstrip("\n")

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}") from e

    return frontmatter, remaining


def update_frontmatter(
    content: str,
    updates: dict[str, Any],
    *,
    remove_keys: list[str] | None = None,
) -> str:
    """Update frontmatter in markdown content.

    Args:
        content: Full markdown content with frontmatter
        updates: Dictionary of property updates
        remove_keys: List of keys to remove from frontmatter

    Returns:
        Updated markdown content

    Raises:
        ValueError: If frontmatter is malformed
    """
    frontmatter, body = parse_frontmatter(content)

    # Apply updates
    for key, value in updates.items():
        frontmatter[key] = value

    # Remove specified keys
    if remove_keys:
        for key in remove_keys:
            frontmatter.pop(key, None)

    # Regenerate frontmatter
    if not frontmatter:
        return body

    # Use yaml.dump with specific formatting
    frontmatter_str = yaml.dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    return f"---\n{frontmatter_str}---\n\n{body}"


def get_property_default(prop_name: str, note_type: str | None = None) -> Any:  # noqa: ANN401
    """Get the default value for a frontmatter property.

    Args:
        prop_name: Property name
        note_type: Optional note type for type-specific defaults

    Returns:
        Default value for the property
    """
    # Check type-specific properties first
    if note_type and note_type in DEFAULT_TYPE_PROPERTIES:
        type_props = DEFAULT_TYPE_PROPERTIES[note_type]
        if prop_name in type_props:
            spec: dict[str, Any] = type_props[prop_name]
            if "values" in spec:
                return spec["values"][0]  # Return first allowed value
            prop_type = spec.get("type", "string")
            if prop_type == "list[string]":
                return []
            return ""

    # Check core properties
    if prop_name in DEFAULT_CORE_PROPERTIES:
        spec = DEFAULT_CORE_PROPERTIES[prop_name]
        prop_type = spec.get("type", "string")
        if prop_type == "list[wikilink]":
            return []
        if prop_type == "date":
            return date.today().isoformat()
        return ""

    # Special cases for known properties
    defaults = {
        "status": "active",
        "rank": 3,
        "priority": "medium",
        "author": "",
        "url": "",
        "source": "",
    }

    return defaults.get(prop_name, "")
