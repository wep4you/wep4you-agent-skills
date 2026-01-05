"""
Note content generation utilities.

Provides functions for generating sample notes and note content
for Obsidian vaults.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from skills.core.generation.frontmatter import generate_frontmatter


def generate_note_content(
    note_type: str,
    type_config: dict[str, Any],
    *,
    title: str | None = None,
    up_link: str = "[[Home]]",
    created_date: date | None = None,
    methodology: str = "",
    core_properties: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
    body_content: str | None = None,
) -> str:
    """Generate complete note content with frontmatter and body.

    Args:
        note_type: Type of note (map, dot, source, etc.)
        type_config: Configuration for this note type
        title: Note title (defaults to type-based title)
        up_link: Parent note wikilink
        created_date: Creation date (defaults to today)
        methodology: Methodology name for tags
        core_properties: List of core properties to include
        custom_properties: List of custom properties to add
        per_type_properties: Dict of type -> list of additional properties
        body_content: Custom body content (overrides default)

    Returns:
        Complete markdown note content
    """
    if created_date is None:
        created_date = date.today()

    if title is None:
        title = f"Getting Started with {note_type.replace('_', ' ').title()}s"

    description = type_config.get("description", f"{note_type.title()} notes")

    # Default core properties
    default_core = ["type", "up", "created", "daily", "tags", "collection", "related"]
    active_properties = core_properties if core_properties is not None else default_core

    # Build additional properties for frontmatter
    additional_props: dict[str, Any] = {}

    # Add required properties with default values
    additional_required = type_config.get("properties", {}).get("additional_required", [])
    for prop in additional_required:
        if prop == "status":
            additional_props["status"] = "active"
        elif prop == "rank":
            additional_props["rank"] = 3
        elif prop == "priority":
            additional_props["priority"] = "medium"
        elif prop == "author":
            additional_props["author"] = "Unknown"
        elif prop == "url":
            additional_props["url"] = ""
        elif prop == "source":
            additional_props["source"] = ""
        else:
            additional_props[prop] = ""

    # Add per-type custom properties
    if per_type_properties and note_type in per_type_properties:
        for prop in per_type_properties[note_type]:
            if prop not in additional_props:
                additional_props[prop] = ""

    # Add custom global properties
    if custom_properties:
        for prop in custom_properties:
            if prop not in additional_props:
                additional_props[prop] = ""

    # Build optional commented properties
    optional_props = type_config.get("properties", {}).get("optional", [])
    per_type_props_list = per_type_properties.get(note_type, []) if per_type_properties else []
    optional_commented = [p for p in optional_props if p not in per_type_props_list]

    # Generate frontmatter
    tags = ["sample", methodology] if methodology else ["sample"]
    daily_link = f"[[{created_date.isoformat()}]]" if "daily" in active_properties else None

    frontmatter = generate_frontmatter(
        note_type,
        up_link=up_link,
        created_date=created_date,
        daily_link=daily_link,
        tags=tags if "tags" in active_properties else None,
        additional_properties=additional_props,
        optional_commented=optional_commented,
        core_properties=active_properties,
    )

    # Generate body content
    if body_content is None:
        body_content = _generate_default_body(note_type, title, description)

    return frontmatter + "\n" + body_content


def _generate_default_body(note_type: str, title: str, description: str) -> str:
    """Generate default body content for a note type.

    Args:
        note_type: Type of note
        title: Note title
        description: Note type description

    Returns:
        Body content as string
    """
    type_title = note_type.replace("_", " ").title()

    body = f"""
# {title}

Welcome to your first **{type_title}** note!

## What is a {type_title}?

{description}

## Recommended Structure

"""

    # Add type-specific structure suggestions
    if note_type == "map":
        body += """- **Overview**: Brief description of what this map covers
- **Contents**: Links to related notes organized by topic
- **Related Maps**: Links to other relevant maps
"""
    elif note_type == "dot":
        body += """- **Core Idea**: One atomic concept per note
- **Details**: Explanation and context
- **See Also**: Links to related concepts
"""
    elif note_type == "source":
        body += """- **Summary**: Key points from the source
- **Quotes**: Important quotes with page references
- **My Thoughts**: Your own reflections
"""
    elif note_type == "project":
        body += """- **Outcome**: What does "done" look like?
- **Tasks**: Actionable next steps
- **Resources**: Links to relevant materials
"""
    elif note_type == "daily":
        body += """- **Tasks**: What to accomplish today
- **Notes**: Capture thoughts and ideas
- **Reflections**: End-of-day review
"""
    else:
        body += """- **Main Content**: Your notes and ideas
- **Related**: Links to connected topics
"""

    body += """
## Tips

1. Use the `up` link to navigate to parent notes
2. Add tags to make notes discoverable
3. Link liberally to other notes

---
*This is a sample note. Feel free to edit or delete it.*

[[Home]]
"""

    return body


def generate_sample_notes(
    vault_path: Path,
    methodology: str,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
    up_links: dict[str, str],
    *,
    dry_run: bool = False,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> list[Path]:
    """Create sample notes for each enabled note type.

    Args:
        vault_path: Path to the vault root
        methodology: Selected methodology name
        note_types: Dictionary of enabled note types
        core_properties: List of core properties
        up_links: Dict mapping folder paths to up-links
        dry_run: If True, only print what would be created
        custom_properties: List of custom global properties to add
        per_type_properties: Dict of type -> list of additional properties

    Returns:
        List of created file paths
    """
    created_files: list[Path] = []
    today = date.today()

    for note_type, type_config in note_types.items():
        folder_hints = type_config.get("folder_hints", [])
        if not folder_hints:
            continue

        folder = folder_hints[0].rstrip("/")
        type_title = note_type.replace("_", " ").title()

        # Special handling for daily notes
        if note_type == "daily":
            filename = f"{today.isoformat()}.md"
        else:
            filename = f"Getting Started with {type_title}s.md"

        file_path = vault_path / folder / filename

        # Determine up link
        up_link = up_links.get(folder_hints[0], "[[Home]]")

        content = generate_note_content(
            note_type,
            type_config,
            up_link=up_link,
            created_date=today,
            methodology=methodology,
            core_properties=core_properties,
            custom_properties=custom_properties,
            per_type_properties=per_type_properties,
        )

        if dry_run:
            print(f"  [DRY RUN] Would create: {file_path}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"  Created: {file_path}")
            created_files.append(file_path)

    return created_files


def generate_home_note(
    methodology: str,
    note_types: list[str],
    *,
    created_date: date | None = None,
) -> str:
    """Generate content for the Home note.

    Args:
        methodology: Methodology name
        note_types: List of enabled note types
        created_date: Creation date (defaults to today)

    Returns:
        Home note content
    """
    if created_date is None:
        created_date = date.today()

    content = f"""---
type: "map"
created: "{created_date.isoformat()}"
---

# Home

Welcome to your Obsidian vault using the **{methodology.upper()}** methodology!

## Quick Links

"""

    # Add links based on methodology
    if methodology == "lyt-ace":
        content += """- [[Atlas/_Atlas_MOC|Atlas]] - Your knowledge structures
- [[Calendar/_Calendar_MOC|Calendar]] - Time-based notes
- [[Efforts/_Efforts_MOC|Efforts]] - Active projects and areas
"""
    elif methodology == "para":
        content += """- [[Projects/_Projects_MOC|Projects]] - Active projects
- [[Areas/_Areas_MOC|Areas]] - Areas of responsibility
- [[Resources/_Resources_MOC|Resources]] - Reference materials
- [[Archive/_Archive_MOC|Archive]] - Completed items
"""
    elif methodology == "zettelkasten":
        content += """- [[Permanent/_Permanent_MOC|Permanent Notes]] - Refined ideas
- [[Literature/_Literature_MOC|Literature Notes]] - Source notes
- [[Fleeting/_Fleeting_MOC|Fleeting Notes]] - Quick captures
"""
    else:
        content += """- [[Notes/_Notes_MOC|Notes]] - Your notes
"""

    content += """
## Getting Started

1. Capture ideas in the **+** (Inbox) folder
2. Process and refine notes regularly
3. Use links to connect related ideas

---
*This is your home base. Customize it to fit your workflow.*
"""

    return content
