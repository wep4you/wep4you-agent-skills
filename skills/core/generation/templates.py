"""
Template loading and rendering utilities.

Provides functions for loading note templates and rendering them
with placeholder values for Obsidian notes.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any


def load_template(
    template_path: Path,
    *,
    encoding: str = "utf-8",
) -> str:
    """Load a template file from disk.

    Args:
        template_path: Path to the template file
        encoding: File encoding (default utf-8)

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template file doesn't exist
        IOError: If template can't be read
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return template_path.read_text(encoding=encoding)


def render_template(
    template: str,
    *,
    title: str = "",
    note_type: str = "",
    up_link: str = "",
    created_date: date | None = None,
    custom_values: dict[str, str] | None = None,
) -> str:
    """Render a template with placeholder values.

    Supports the following placeholders:
    - {{title}}: Note title
    - {{type}}: Note type
    - {{up}}: Up-link value
    - {{date}}: Creation date in ISO format
    - Any custom key-value pairs

    Args:
        template: Template string with placeholders
        title: Note title
        note_type: Note type
        up_link: Parent note link
        created_date: Creation date (defaults to today)
        custom_values: Dict of additional placeholder values

    Returns:
        Rendered template string
    """
    if created_date is None:
        created_date = date.today()

    # Build replacements dict
    replacements = {
        "{{title}}": title,
        "{{type}}": note_type,
        "{{up}}": up_link,
        "{{date}}": created_date.isoformat(),
    }

    # Add custom values
    if custom_values:
        for key, value in custom_values.items():
            placeholder = f"{{{{{key}}}}}"  # Double braces for {{key}}
            replacements[placeholder] = value

    # Apply replacements
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    return result


def generate_template_note(
    note_type: str,
    type_config: dict[str, Any],
    core_properties: list[str],
    *,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> str:
    """Generate a template note for a specific note type.

    Creates a template with placeholders that can be filled in when
    creating new notes.

    Args:
        note_type: The type of note (e.g., 'map', 'dot', 'project')
        type_config: Configuration for this note type
        core_properties: List of core properties
        core_properties_filter: Optional filter for which properties to include
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

    Returns:
        Template content as string
    """
    # Filter core properties if filter is provided
    # Always include 'type' and 'created' as mandatory
    active_properties = list(core_properties)
    if core_properties_filter:
        mandatory = {"type", "created"}
        active_properties = [
            p for p in core_properties if p in core_properties_filter or p in mandatory
        ]

    # Add custom properties
    if custom_properties:
        active_properties = list(active_properties) + custom_properties

    # Build frontmatter with all properties as placeholders
    lines = ["---"]
    lines.append(f'type: "{note_type}"')

    # Add core properties (except type which is already added)
    for prop in active_properties:
        if prop == "type":
            continue
        elif prop == "up":
            lines.append('up: "[[{{up}}]]"')
        elif prop == "created":
            lines.append("created: {{date}}")
        elif prop == "tags":
            lines.append("tags: []")
        elif prop == "daily":
            lines.append("daily: ")
        elif prop == "collection":
            lines.append("collection: ")
        elif prop == "related":
            lines.append("related: []")
        else:
            lines.append(f"{prop}: ")

    # Add type-specific required properties
    props = type_config.get("properties", {})
    additional_required = props.get("additional_required", [])
    for prop in additional_required:
        if prop == "status":
            lines.append('status: "active"')
        elif prop == "author":
            lines.append("author: ")
        elif prop == "url":
            lines.append("url: ")
        else:
            lines.append(f"{prop}: ")

    # Add per-type custom properties (if any)
    if per_type_properties and note_type in per_type_properties:
        for prop in per_type_properties[note_type]:
            if prop not in additional_required:  # Avoid duplicates
                lines.append(f"{prop}: ")

    # Add optional properties as comments - skip if already added via per-type
    optional = props.get("optional", [])
    per_type_props_for_this_type = (
        per_type_properties.get(note_type, []) if per_type_properties else []
    )
    for prop in optional:
        # Skip if already added as per-type property
        if prop not in per_type_props_for_this_type:
            lines.append(f"# {prop}: ")

    lines.append("---")
    lines.append("")

    # Add template body
    description = type_config.get("description", f"{note_type.title()} note")
    type_title = note_type.replace("_", " ").title()

    lines.append("# {{title}}")
    lines.append("")
    lines.append(f"> Template for **{type_title}** notes: {description}")
    lines.append("")
    lines.append("## Content")
    lines.append("")
    lines.append("<!-- Your content here -->")
    lines.append("")
    lines.append("## Related")
    lines.append("")
    lines.append("- [[]]")
    lines.append("")

    return "\n".join(lines)


def create_template_notes(
    vault_path: Path,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
    templates_folder: str = "x/templates/",
    *,
    dry_run: bool = False,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> list[Path]:
    """Create template notes for each note type.

    Args:
        vault_path: Path to the vault root
        note_types: Dictionary of enabled note types
        core_properties: List of core properties
        templates_folder: Folder for templates (default: x/templates/)
        dry_run: If True, only print what would be created
        core_properties_filter: Optional filter for which properties to include
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

    Returns:
        List of created file paths
    """
    templates_path = vault_path / templates_folder
    created_files: list[Path] = []

    for note_type, type_config in note_types.items():
        # Skip daily notes - they use a different template system
        if note_type == "daily":
            continue

        template_file = templates_path / f"{note_type}.md"
        content = generate_template_note(
            note_type,
            type_config,
            core_properties,
            core_properties_filter=core_properties_filter,
            custom_properties=custom_properties,
            per_type_properties=per_type_properties,
        )

        if dry_run:
            print(f"  [DRY RUN] Would create: {template_file}")
        else:
            template_file.parent.mkdir(parents=True, exist_ok=True)
            template_file.write_text(content)
            print(f"  Created: {template_file}")
            created_files.append(template_file)

    return created_files
