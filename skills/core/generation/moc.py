"""
MOC (Map of Content) generation utilities.

Provides functions for creating and updating Map of Content files
in Obsidian vaults.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from skills.core.utils.paths import extract_folder_name, get_moc_filename

# Default folder descriptions by methodology
FOLDER_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "lyt-ace": {
        "Atlas": "The Atlas contains your maps and interconnected knowledge structures.",
        "Atlas/Maps": "Maps of Content (MOCs) that organize and navigate your notes.",
        "Atlas/Dots": "Atomic notes - single ideas developed and refined.",
        "Atlas/Sources": "Reference materials and citations.",
        "Calendar": "Time-based notes including daily, weekly, and periodic reviews.",
        "Calendar/Daily": "Daily notes and journals.",
        "Efforts": "Active projects and ongoing work.",
        "Efforts/Projects": "Active projects with defined outcomes.",
        "Efforts/Areas": "Areas of responsibility to maintain.",
    },
    "para": {
        "Projects": "Active projects with defined outcomes and deadlines.",
        "Areas": "Areas of responsibility requiring ongoing attention.",
        "Resources": "Reference materials and topics of interest.",
        "Archive": "Completed or inactive items for reference.",
    },
    "zettelkasten": {
        "Permanent": "Permanent notes - refined and interconnected ideas.",
        "Literature": "Literature notes from sources you've read.",
        "Fleeting": "Quick captures and temporary notes.",
    },
    "minimal": {
        "Notes": "Your notes and ideas.",
    },
}


def generate_moc_content(
    folder_path: str,
    methodology: str | None = None,
    *,
    description: str | None = None,
    created_date: date | None = None,
    include_base_view: bool = True,
) -> str:
    """Generate MOC (Map of Content) file content for a folder.

    Args:
        folder_path: Path of the folder (e.g., "Projects", "Atlas/Dots")
        methodology: Methodology key for default descriptions
        description: Custom description (overrides default)
        created_date: Creation date (defaults to today)
        include_base_view: Whether to include the base view embed

    Returns:
        Markdown content for the MOC file
    """
    if created_date is None:
        created_date = date.today()

    # Get description from defaults or use provided/fallback
    if description is None:
        descriptions = FOLDER_DESCRIPTIONS.get(methodology or "", {})
        description = descriptions.get(folder_path, f"Notes and content for {folder_path}.")

    # Get display name (last part of path)
    display_name = extract_folder_name(folder_path)

    lines = [
        "---",
        'type: "map"',
        f'created: "{created_date.isoformat()}"',
        "---",
        "",
        f"# {display_name}",
        "",
        description,
        "",
        "## Contents",
        "",
    ]

    if include_base_view:
        lines.append(f"![[all_bases.base#{display_name}]]")
    else:
        lines.append("<!-- Add your content links here -->")

    lines.append("")

    return "\n".join(lines)


def update_moc(
    moc_path: Path,
    *,
    new_links: list[str] | None = None,
    description: str | None = None,
    append_section: tuple[str, str] | None = None,
) -> bool:
    """Update an existing MOC file.

    Args:
        moc_path: Path to the MOC file
        new_links: List of wikilinks to add to the Contents section
        description: New description to replace the existing one
        append_section: Tuple of (section_title, content) to append

    Returns:
        True if update succeeded, False otherwise
    """
    if not moc_path.exists():
        return False

    content = moc_path.read_text()
    lines = content.split("\n")
    updated_lines: list[str] = []

    in_contents = False
    description_replaced = False

    for i, line in enumerate(lines):
        # Handle description update
        if description and not description_replaced:
            # Description is typically after the # title line
            if i > 0 and lines[i - 1].startswith("# ") and line.strip() == "":
                updated_lines.append(line)
                # Skip existing description (non-empty lines until next ##)
                j = i + 1
                while j < len(lines) and not lines[j].startswith("##") and lines[j].strip():
                    j += 1
                updated_lines.append(description)
                updated_lines.append("")
                description_replaced = True
                continue

        # Detect Contents section
        if line.strip() == "## Contents":
            in_contents = True
            updated_lines.append(line)
            continue

        # Add new links before end of Contents section
        if in_contents and new_links:
            if line.startswith("##") or (line.strip() == "" and not any(lines[i + 1 :]).strip()):
                # Add links before next section or end
                for link in new_links:
                    updated_lines.append(f"- [[{link}]]")
                in_contents = False
                new_links = None  # Clear to prevent re-adding

        updated_lines.append(line)

    # Append new section if requested
    if append_section:
        section_title, section_content = append_section
        updated_lines.extend(["", f"## {section_title}", "", section_content, ""])

    moc_path.write_text("\n".join(updated_lines))
    return True


def create_folder_mocs(
    vault_path: Path,
    methodology: str,
    content_folders: list[str],
    *,
    dry_run: bool = False,
    note_types_filter: list[str] | None = None,
    selected_folders: set[str] | None = None,
) -> list[Path]:
    """Create MOC (Map of Content) files in each content folder.

    Args:
        vault_path: Path to the vault root
        methodology: Methodology key
        content_folders: List of content folder paths
        dry_run: If True, only print what would be created
        note_types_filter: List of note type names to include (None = all)
        selected_folders: Set of folders that should have MOCs (None = all)

    Returns:
        List of created file paths
    """
    created_files: list[Path] = []

    for folder in content_folders:
        # Skip folders that weren't created due to filtering
        if selected_folders is not None:
            folder_created = folder in selected_folders
            # For subfolders, check if parent is in selected folders
            if "/" in folder and not folder_created:
                parent = folder.split("/")[0]
                folder_created = any(
                    sf.startswith(parent + "/") or sf == parent for sf in selected_folders
                )

            if not folder_created and note_types_filter is not None:
                continue

        folder_path = vault_path / folder

        # Skip if folder doesn't exist
        if not dry_run and not folder_path.exists():
            continue

        moc_filename = get_moc_filename(folder)
        moc_path = folder_path / moc_filename
        content = generate_moc_content(folder, methodology)

        if dry_run:
            print(f"  [DRY RUN] Would create: {moc_path}")
        else:
            moc_path.parent.mkdir(parents=True, exist_ok=True)
            moc_path.write_text(content)
            print(f"  Created: {moc_path}")
            created_files.append(moc_path)

    return created_files
