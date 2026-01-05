#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Content generation functions for Obsidian vault initialization.

This module provides functions for generating sample notes, templates,
MOCs, agent docs, and settings files during vault initialization.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Add repository root to path for importing methodology loader
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config.methodologies.loader import METHODOLOGIES  # noqa: E402
from skills.core.models import WizardConfig  # noqa: E402
from skills.core.utils.paths import get_moc_filename  # noqa: E402
from skills.init.scripts.vault_utils import get_all_content_folders  # noqa: E402

# =============================================================================
# Sample Note Generation
# =============================================================================


def generate_sample_note(
    note_type: str,
    note_type_config: dict[str, Any],
    core_properties: list[str],
    methodology: str,
    up_links: dict[str, str],
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> str:
    """Generate sample note content dynamically."""
    today = date.today().isoformat()
    folder_hint = note_type_config.get("folder_hints", [""])[0]
    description = note_type_config.get("description", f"{note_type.title()} notes")
    up_link = up_links.get(folder_hint, "[[Home]]")

    # Filter core properties
    active_properties = list(core_properties)
    if core_properties_filter:
        mandatory = {"type", "created"}
        active_properties = [
            p for p in core_properties if p in core_properties_filter or p in mandatory
        ]

    if custom_properties:
        active_properties = list(active_properties) + custom_properties

    # Build frontmatter
    lines = ["---", f'type: "{note_type}"']

    if "up" in active_properties:
        lines.append(f'up: "{up_link}"')
    lines.append(f'created: "{today}"')
    if "daily" in active_properties:
        lines.append(f'daily: "[[{today}]]"')
    if "tags" in active_properties:
        lines.append(f"tags: [sample, {methodology}]")
    if "collection" in active_properties:
        lines.append('collection: ""')
    if "related" in active_properties:
        lines.append("related: []")

    # Add additional_required properties
    additional_required = note_type_config.get("properties", {}).get("additional_required", [])
    for prop in additional_required:
        if prop == "status":
            lines.append('status: "active"')
        elif prop == "rank":
            lines.append("rank: 3")
        elif prop == "priority":
            lines.append('priority: "medium"')
        elif prop == "author":
            lines.append('author: "Unknown"')
        elif prop in ("url", "source"):
            lines.append(f'{prop}: ""')
        else:
            lines.append(f'{prop}: ""')

    # Add per-type properties
    if per_type_properties and note_type in per_type_properties:
        for prop in per_type_properties[note_type]:
            if prop not in additional_required:
                lines.append(f'{prop}: ""')

    # Add custom global properties
    if custom_properties:
        written = {"type", "up", "created", "daily", "tags", "collection", "related"}
        written.update(additional_required)
        if per_type_properties and note_type in per_type_properties:
            written.update(per_type_properties[note_type])
        for prop in custom_properties:
            if prop not in written:
                lines.append(f'{prop}: ""')

    # Add optional properties as comments
    optional_props = note_type_config.get("properties", {}).get("optional", [])
    per_type_for_type = per_type_properties.get(note_type, []) if per_type_properties else []
    for prop in optional_props:
        if prop not in per_type_for_type:
            lines.append(f"# {prop}: ")

    lines.append("---")

    # Build body
    type_title = note_type.replace("_", " ").title()
    body = f"""
# Getting Started with {type_title}s

Welcome to your first **{type_title}** note!

## What is a {type_title}?

{description}

## Recommended Structure

"""
    if note_type == "map":
        body += "- **Overview**: Brief description of what this map covers\n"
        body += "- **Contents**: Links to related notes organized by topic\n"
        body += "- **Related Maps**: Links to other relevant maps\n"
    elif note_type == "dot":
        body += "- **Core Idea**: One atomic concept per note\n"
        body += "- **Details**: Explanation and context\n"
        body += "- **See Also**: Links to related concepts\n"
    elif note_type == "source":
        body += "- **Summary**: Key points from the source\n"
        body += "- **Quotes**: Important quotes with page references\n"
        body += "- **My Thoughts**: Your own reflections\n"
    elif note_type == "project":
        body += '- **Outcome**: What does "done" look like?\n'
        body += "- **Tasks**: Actionable next steps\n"
        body += "- **Resources**: Links to relevant materials\n"
    elif note_type == "daily":
        body += "- **Tasks**: What to accomplish today\n"
        body += "- **Notes**: Capture thoughts and ideas\n"
        body += "- **Reflections**: End-of-day review\n"
    else:
        body += "- **Main Content**: Your notes and ideas\n"
        body += "- **Related**: Links to connected topics\n"

    body += """
## Tips

1. Use the `up` link to navigate to parent notes
2. Add tags to make notes discoverable
3. Link liberally to other notes

---
*This is a sample note. Feel free to edit or delete it.*

[[Home]]
"""
    return "\n".join(lines) + body


def create_sample_notes(
    vault_path: Path,
    methodology: str,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
    dry_run: bool = False,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> list[Path]:
    """Create sample notes for each enabled note type."""
    method_config = METHODOLOGIES[methodology]
    up_links = method_config.get("up_links", {})
    created_files: list[Path] = []

    print("\nCreating sample notes...")

    for note_type, type_config in note_types.items():
        folder_hints = type_config.get("folder_hints", [])
        if not folder_hints:
            continue

        folder = folder_hints[0].rstrip("/")
        type_title = note_type.replace("_", " ").title()

        if note_type == "daily":
            filename = f"{date.today().isoformat()}.md"
        else:
            filename = f"Getting Started with {type_title}s.md"

        file_path = vault_path / folder / filename
        content = generate_sample_note(
            note_type,
            type_config,
            core_properties,
            methodology,
            up_links,
            core_properties_filter,
            custom_properties,
            per_type_properties,
        )

        if dry_run:
            print(f"  [DRY RUN] Would create: {file_path}")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"  Created: {file_path}")
            created_files.append(file_path)

    return created_files


# =============================================================================
# Template Generation
# =============================================================================


def generate_template_note(
    note_type: str,
    type_config: dict[str, Any],
    core_properties: list[str],
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> str:
    """Generate a template note for a specific note type."""
    active_properties = list(core_properties)
    if core_properties_filter:
        mandatory = {"type", "created"}
        active_properties = [
            p for p in core_properties if p in core_properties_filter or p in mandatory
        ]

    if custom_properties:
        active_properties = list(active_properties) + custom_properties

    lines = ["---", f'type: "{note_type}"']

    for prop in active_properties:
        if prop == "type":
            continue
        elif prop == "up":
            lines.append('up: "[[{{up}}]]"')
        elif prop == "created":
            lines.append("created: {{date}}")
        elif prop == "tags":
            lines.append("tags: []")
        elif prop in ("daily", "collection"):
            lines.append(f"{prop}: ")
        elif prop == "related":
            lines.append("related: []")
        else:
            lines.append(f"{prop}: ")

    props = type_config.get("properties", {})
    for prop in props.get("additional_required", []):
        if prop == "status":
            lines.append('status: "active"')
        elif prop in ("author", "url"):
            lines.append(f"{prop}: ")
        else:
            lines.append(f"{prop}: ")

    if per_type_properties and note_type in per_type_properties:
        for prop in per_type_properties[note_type]:
            if prop not in props.get("additional_required", []):
                lines.append(f"{prop}: ")

    per_type_for_type = per_type_properties.get(note_type, []) if per_type_properties else []
    for prop in props.get("optional", []):
        if prop not in per_type_for_type:
            lines.append(f"# {prop}: ")

    lines.extend(["---", ""])

    description = type_config.get("description", f"{note_type.title()} note")
    type_title = note_type.replace("_", " ").title()

    lines.extend(
        [
            "# {{title}}",
            "",
            f"> Template for **{type_title}** notes: {description}",
            "",
            "## Content",
            "",
            "<!-- Your content here -->",
            "",
            "## Related",
            "",
            "- [[]]",
            "",
        ]
    )

    return "\n".join(lines)


def create_template_notes(
    vault_path: Path,
    methodology: str,
    note_types: dict[str, dict[str, Any]],
    core_properties: list[str],
    dry_run: bool = False,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> list[Path]:
    """Create template notes for each note type."""
    method_config = METHODOLOGIES[methodology]
    folder_structure = method_config.get("folder_structure", {})
    templates_folder = folder_structure.get("templates", "x/templates/")
    templates_path = vault_path / templates_folder
    created_files: list[Path] = []

    print("\nCreating template notes...")

    for note_type, type_config in note_types.items():
        if note_type == "daily":
            continue

        template_file = templates_path / f"{note_type}.md"
        content = generate_template_note(
            note_type,
            type_config,
            core_properties,
            core_properties_filter,
            custom_properties,
            per_type_properties,
        )

        if dry_run:
            print(f"  [DRY RUN] Would create: {template_file}")
        else:
            template_file.parent.mkdir(parents=True, exist_ok=True)
            template_file.write_text(content)
            print(f"  Created: {template_file}")
            created_files.append(template_file)

    return created_files


# =============================================================================
# MOC and Bases Generation
# =============================================================================


def generate_all_bases_content(methodology: str) -> str:
    """Generate the all_bases.base file content."""
    content_folders = get_all_content_folders(methodology)

    lines = [
        "filters:",
        "  and:",
        "    - '!file.inFolder(\"+\")'",
        "    - '!file.inFolder(\"x\")'",
        '    - file.folder != "/"',
        '    - \'!file.name.startsWith("_") || !file.name.endsWith("_MOC")\'',
        "views:",
        "  - type: table",
        "    name: All",
        "    groupBy:",
        "      property: file.folder",
        "      direction: ASC",
        "    order:",
        "      - file.name",
        "      - type",
        "      - up",
    ]

    for folder in content_folders:
        view_name = folder.split("/")[-1] if "/" in folder else folder
        lines.extend(
            [
                "  - type: table",
                f"    name: {view_name}",
                "    filters:",
                "      and:",
                f'        - file.inFolder("{folder}")',
                "    order:",
                "      - file.name",
                "      - type",
                "      - up",
            ]
        )

    return "\n".join(lines) + "\n"


def create_all_bases_file(vault_path: Path, methodology: str, dry_run: bool = False) -> Path | None:
    """Create the all_bases.base file."""
    bases_folder = vault_path / "x" / "bases"
    base_file = bases_folder / "all_bases.base"
    content = generate_all_bases_content(methodology)

    print("\nCreating all_bases.base (Obsidian Bases views)...")

    if dry_run:
        print(f"  [DRY RUN] Would create: {base_file}")
        return None
    else:
        bases_folder.mkdir(parents=True, exist_ok=True)
        base_file.write_text(content)
        print(f"  Created: {base_file}")
        return base_file


# Folder descriptions for MOC files
FOLDER_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "lyt-ace": {
        "Atlas": "Knowledge repository containing Maps of Content, atomic concepts, and sources.",
        "Atlas/Maps": "Maps of Content - Overview and navigation notes.",
        "Atlas/Dots": "Atomic concepts and ideas - one idea per note.",
        "Atlas/Sources": "External references, citations, and source materials.",
        "Calendar": "Time-based notes including daily journals and periodic reviews.",
        "Calendar/daily": "Daily journal entries and reflections.",
        "Efforts": "Active work including projects and ongoing areas of responsibility.",
        "Efforts/Projects": "Projects with defined outcomes and deadlines.",
        "Efforts/Areas": "Ongoing areas of responsibility.",
    },
    "para": {
        "Projects": "Active projects with defined outcomes and deadlines.",
        "Areas": "Ongoing areas of responsibility that require maintenance.",
        "Resources": "Reference materials and resources for future use.",
        "Archives": "Completed or inactive items preserved for reference.",
    },
    "zettelkasten": {
        "Permanent": "Your own ideas and insights - the core of your knowledge base.",
        "Literature": "Notes from reading and external sources.",
        "Fleeting": "Quick captures and ideas to process later.",
        "References": "External sources and citations.",
    },
    "minimal": {
        "Notes": "General notes and ideas.",
        "Daily": "Daily journal entries and reflections.",
    },
}


def generate_folder_moc_content(folder_path: str, methodology: str) -> str:
    """Generate MOC file content for a folder."""
    descriptions = FOLDER_DESCRIPTIONS.get(methodology, {})
    description = descriptions.get(folder_path, f"Notes and content for {folder_path}.")
    display_name = folder_path.split("/")[-1] if "/" in folder_path else folder_path
    today = date.today().isoformat()

    return f"""---
type: map
created: "{today}"
---

# {display_name}

{description}

## Contents

![[all_bases.base#{display_name}]]
"""


def create_folder_mocs(
    vault_path: Path,
    methodology: str,
    dry_run: bool = False,
    note_types_filter: list[str] | None = None,
) -> list[Path]:
    """Create MOC files in each content folder."""
    from skills.init.scripts.vault_utils import get_folders_for_note_types

    selected_folders = set(get_folders_for_note_types(methodology, note_types_filter))
    content_folders = get_all_content_folders(methodology)
    created_files: list[Path] = []

    print("\nCreating folder MOC files...")

    for folder in content_folders:
        folder_created = folder in selected_folders
        if "/" in folder and not folder_created:
            parent = folder.split("/")[0]
            folder_created = any(
                sf.startswith(parent + "/") or sf == parent for sf in selected_folders
            )

        if not folder_created and note_types_filter is not None:
            continue

        folder_path = vault_path / folder
        if not dry_run and not folder_path.exists():
            continue

        moc_filename = get_moc_filename(folder)
        moc_path = folder_path / moc_filename
        content = generate_folder_moc_content(folder, methodology)

        if dry_run:
            print(f"  [DRY RUN] Would create: {moc_path}")
        else:
            moc_path.parent.mkdir(parents=True, exist_ok=True)
            moc_path.write_text(content)
            print(f"  Created: {moc_path}")
            created_files.append(moc_path)

    return created_files


# =============================================================================
# Settings and Documentation
# =============================================================================


def build_settings_yaml(
    methodology: str,
    config: WizardConfig | None = None,
    note_types_filter: list[str] | None = None,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Build settings.yaml content for a methodology."""
    method_config = METHODOLOGIES[methodology]
    note_types = dict(method_config["note_types"])

    # Apply per-type property customizations
    if per_type_properties:
        for type_name, props_list in per_type_properties.items():
            if type_name in note_types:
                note_types[type_name] = dict(note_types[type_name])
                existing_props = note_types[type_name].get("properties", {})
                existing_required = existing_props.get("additional_required", [])
                existing_optional = existing_props.get("optional", [])
                new_required = list(set(existing_required + props_list))
                note_types[type_name]["properties"] = {
                    "additional_required": new_required,
                    "optional": existing_optional,
                }

    if config and config.per_type_properties:
        for type_name, props in config.per_type_properties.items():
            if type_name in note_types:
                note_types[type_name] = dict(note_types[type_name])
                note_types[type_name]["properties"] = {
                    "additional_required": props.get("required", []),
                    "optional": props.get("optional", []),
                }

    if config and config.custom_note_types:
        for type_name, type_config in config.custom_note_types.items():
            note_types[type_name] = type_config.to_dict()

    if config and config.note_types:
        filtered_types = {}
        for type_name in config.note_types:
            if type_name in note_types:
                filtered_types[type_name] = note_types[type_name]
        if config.custom_note_types:
            for type_name, type_config in config.custom_note_types.items():
                filtered_types[type_name] = type_config.to_dict()
        note_types = filtered_types

    if note_types_filter:
        note_types = {k: v for k, v in note_types.items() if k in note_types_filter}

    # Build core properties
    all_core_properties = list(method_config["core_properties"])

    if core_properties_filter:
        mandatory = {"type", "created"}
        all_core_properties = [
            p for p in all_core_properties if p in core_properties_filter or p in mandatory
        ]

    core_properties_config: dict[str, Any] = {"all": all_core_properties}

    if custom_properties:
        core_properties_config["custom"] = custom_properties
        all_core_properties = list(all_core_properties) + custom_properties
        core_properties_config["all"] = all_core_properties

    if config:
        if config.mandatory_properties:
            core_properties_config["mandatory"] = config.mandatory_properties
        if config.optional_properties:
            core_properties_config["optional"] = config.optional_properties
        if config.custom_properties:
            existing_custom = core_properties_config.get("custom", [])
            all_custom = list(set(existing_custom + config.custom_properties))
            core_properties_config["custom"] = all_custom
            base_props = list(method_config["core_properties"])
            if core_properties_filter:
                mandatory = {"type", "created"}
                base_props = [
                    p for p in base_props if p in core_properties_filter or p in mandatory
                ]
            core_properties_config["all"] = base_props + all_custom

    return {
        "version": "1.0",
        "methodology": methodology,
        "core_properties": core_properties_config,
        "note_types": note_types,
        "validation": {
            "require_core_properties": True,
            "allow_empty_properties": ["tags", "collection", "related"],
            "strict_types": True,
            "check_templates": True,
            "check_up_links": True,
            "check_inbox_no_frontmatter": True,
        },
        "folder_structure": method_config.get("folder_structure", {}),
        "up_links": method_config.get("up_links", {}),
        "exclude": {
            "paths": ["+/", "x/", ".obsidian/", ".claude/", ".git/"],
            "files": ["HOME.md", "README.md"],
            "patterns": ["_*_MOC.md"],
        },
        "formats": {
            "date": "YYYY-MM-DD",
            "daily_link": "[[{date}]]",
            "wikilink_quoted": True,
        },
        "logging": {
            "enabled": True,
            "format": "jsonl",
            "directory": ".claude/logs/",
            "retention_days": 30,
        },
    }


def create_settings_yaml(
    vault_path: Path,
    methodology: str,
    dry_run: bool = False,
    config: WizardConfig | None = None,
    note_types_filter: list[str] | None = None,
    core_properties_filter: list[str] | None = None,
    custom_properties: list[str] | None = None,
    per_type_properties: dict[str, list[str]] | None = None,
) -> None:
    """Create settings.yaml for the vault."""
    settings = build_settings_yaml(
        methodology,
        config,
        note_types_filter,
        core_properties_filter,
        custom_properties,
        per_type_properties,
    )
    settings_path = vault_path / ".claude" / "settings.yaml"

    header = """# .claude/settings.yaml - Obsidian Vault Settings
# This is the PRIMARY source of truth for all validation and configuration.
# Generated by init-skill. Manual editing supported.

"""

    yaml_content = yaml.dump(
        settings, default_flow_style=False, sort_keys=False, allow_unicode=True
    )

    print("\nCreating settings.yaml (primary configuration)...")

    if dry_run:
        print(f"  [DRY RUN] Would create: {settings_path}")
    else:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(header + yaml_content)
        print(f"  Created: {settings_path}")


def create_readme(vault_path: Path, methodology: str, dry_run: bool = False) -> None:
    """Create README.md in the vault root."""
    method_config = METHODOLOGIES[methodology]
    readme_path = vault_path / "README.md"

    content = f"""# {vault_path.name}

This Obsidian vault uses the **{method_config["name"]}** methodology.

## Methodology

{method_config["description"]}

## Folder Structure

"""
    for folder in method_config["folders"]:
        content += f"- `{folder}/`\n"

    content += """
## Configuration

Vault configuration is stored in `.claude/settings.yaml`.

---

For slash command reference and more details, see AGENTS.md.
"""

    if dry_run:
        print(f"\n[DRY RUN] Would create: {readme_path}")
    else:
        readme_path.write_text(content)
        print(f"\nCreated: {readme_path}")


def create_home_note(vault_path: Path, methodology: str, dry_run: bool = False) -> None:
    """Create HOME.md in the vault root."""
    method_config = METHODOLOGIES[methodology]
    home_path = vault_path / "HOME.md"
    today = date.today().isoformat()

    content = f"""---
type: map
created: "{today}"
---

# Home

Welcome to your **{method_config["name"]}** vault!

## All Notes

![[all_bases.base#All]]

## Getting Started

1. Start capturing ideas in the `+/` inbox
2. Process inbox items into appropriate folders
3. Run `/obsidian:validate` to check your notes

## Configuration

Your vault settings are in `.claude/settings.yaml`.
"""

    if dry_run:
        print(f"[DRY RUN] Would create: {home_path}")
    else:
        home_path.write_text(content)
        print(f"Created: {home_path}")


def generate_agents_md(methodology: str) -> str:
    """Generate AGENTS.md content."""
    method_config = METHODOLOGIES[methodology]
    folders = method_config.get("folders", [])
    folder_list = "\n".join(f"- `{f}/`" for f in folders[:6])
    today = date.today().isoformat()

    return f"""---
type: "system"
created: "{today}"
tags: [system, agents]
---

# AGENTS.md

Instructions for AI coding agents working with this Obsidian vault.

## Project Overview

This is an Obsidian vault using the **{method_config["name"]}** methodology.

- **Config**: `.claude/settings.yaml` (single source of truth)
- **Templates**: `x/templates/`
- **Validation**: Run after any note changes

## Commands

```bash
/obsidian:validate
/obsidian:validate --fix
/obsidian:config show
/obsidian:types
```

## Project Structure

{folder_list}
- `x/templates/` - Note templates
- `.claude/` - Configuration

## Code Style (Frontmatter)

**Required properties (ALL notes):**
```yaml
---
type: "project"
created: "{today}"
up: "[[Parent Note]]"
---
```

## Boundaries

### Always Do
- Read `settings.yaml` before creating notes
- Use templates from `x/templates/`
- Validate after changes

### Never Do
- Create notes without frontmatter
- Place notes outside designated folders
- Modify `.obsidian/` folder
"""


def create_agent_docs(
    vault_path: Path,
    methodology: str,
    dry_run: bool = False,
) -> None:
    """Create AGENTS.md and CLAUDE.md."""
    agents_content = generate_agents_md(methodology)
    agents_path = vault_path / "AGENTS.md"

    if dry_run:
        print(f"[DRY RUN] Would create: {agents_path}")
    else:
        agents_path.write_text(agents_content)
        print(f"Created: {agents_path}")

    today = date.today().isoformat()
    claude_content = f"""---
type: "system"
created: "{today}"
tags: [system]
---

# CLAUDE.md

See @AGENTS.md for complete agent instructions.

## Obsidian Plugin

```bash
/obsidian:validate --fix
/obsidian:config show
/obsidian:types
```
"""
    claude_path = vault_path / "CLAUDE.md"

    if dry_run:
        print(f"[DRY RUN] Would create: {claude_path}")
    else:
        claude_path.write_text(claude_content)
        print(f"Created: {claude_path}")
