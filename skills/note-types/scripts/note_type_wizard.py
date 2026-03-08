#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Note Type Wizard - Interactive and vault operations for note types.

This module contains the interactive wizard functionality and vault structure
operations that were extracted from note_types.py to keep the main module
focused on CRUD operations.

It also contains CLI command handler functions to keep the main module slim.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add project root to path for imports
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

if TYPE_CHECKING:
    from note_types import NoteTypesManager

from skills.core.utils.paths import get_moc_filename, get_moc_link  # noqa: E402


def interactive_type_definition(
    name: str,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Interactively build a note type definition.

    Args:
        name: Name of the note type
        existing: Existing definition to use as defaults

    Returns:
        Note type definition dictionary
    """
    existing = existing or {}

    print(f"Define note type: {name}")
    print("(Press Enter to keep current value or use default)\n")

    # Description
    default_desc = existing.get("description", f"{name.capitalize()} notes")
    description = input(f"  Description [{default_desc}]: ").strip()
    description = description if description else default_desc

    # Folder hints
    default_folders = existing.get("folder_hints", [f"{name.capitalize()}/"])
    folders_str = ", ".join(default_folders)
    folders_input = input(f"  Folders (comma-separated) [{folders_str}]: ").strip()
    if folders_input:
        folder_hints = [f.strip() for f in folders_input.split(",")]
    else:
        folder_hints = default_folders

    # Properties
    existing_props = existing.get("properties", {})
    if isinstance(existing_props, dict):
        default_req = existing_props.get("additional_required", [])
        default_opt = existing_props.get("optional", [])
    else:
        default_req = existing_props if isinstance(existing_props, list) else []
        default_opt = []

    req_str = ", ".join(default_req) if default_req else "none"
    req_input = input(f"  Required properties [{req_str}]: ").strip()
    if req_input and req_input.lower() != "none":
        additional_required = [p.strip() for p in req_input.split(",")]
    elif req_input.lower() == "none":
        additional_required = []
    else:
        additional_required = default_req

    opt_str = ", ".join(default_opt) if default_opt else "none"
    opt_input = input(f"  Optional properties [{opt_str}]: ").strip()
    if opt_input and opt_input.lower() != "none":
        optional = [p.strip() for p in opt_input.split(",")]
    elif opt_input.lower() == "none":
        optional = []
    else:
        optional = default_opt

    # Icon
    default_icon = existing.get("icon", "file")
    icon = input(f"  Icon [{default_icon}]: ").strip()
    icon = icon if icon else default_icon

    config: dict[str, Any] = {
        "description": description,
        "folder_hints": folder_hints,
        "properties": {
            "additional_required": additional_required,
            "optional": optional,
        },
        "validation": existing.get("validation", {"allow_empty_up": False}),
        "icon": icon,
    }

    return config


def run_wizard(
    note_types: dict[str, dict[str, Any]],
    on_create: Callable[..., Any],
) -> None:
    """Interactive wizard to create a new note type.

    Args:
        note_types: Current note types dictionary
        on_create: Callback function to call when type is created (name, config)
    """
    print("Note Type Wizard\n")
    print("Let's create a new note type for your Obsidian vault.\n")

    while True:
        name = input("Note type name: ").strip().lower()
        if not name:
            print("Name cannot be empty")
            continue
        if name in note_types:
            print(f"Note type '{name}' already exists")
            continue
        break

    config = interactive_type_definition(name)

    print("\nSummary:")
    print(f"  Name: {name}")
    print(f"  Description: {config['description']}")
    print(f"  Folders: {', '.join(config['folder_hints'])}")
    req = config["properties"]["additional_required"]
    opt = config["properties"]["optional"]
    if req:
        print(f"  Required: {', '.join(req)}")
    if opt:
        print(f"  Optional: {', '.join(opt)}")
    print(f"  Icon: {config['icon']}")

    response = input("\nCreate this note type? (Y/n): ").strip().lower()
    if response and response != "y":
        print("Cancelled")
        return

    on_create(name, config)
    print(f"\nCreated note type '{name}'")


class VaultStructureManager:
    """Manages vault folder structure for note types."""

    def __init__(
        self,
        vault_path: Path,
        templates_folder: Path,
        bases_folder: Path,
        system_prefix: str,
        core_properties: list[str],
    ) -> None:
        """Initialize vault structure manager.

        Args:
            vault_path: Path to the vault root
            templates_folder: Path to the templates folder
            bases_folder: Path to the bases folder
            system_prefix: System folder prefix (e.g., "x")
            core_properties: List of core property names
        """
        self.vault_path = vault_path
        self.templates_folder = templates_folder
        self.bases_folder = bases_folder
        self.system_prefix = system_prefix
        self.core_properties = core_properties
        self.all_bases_file = self.bases_folder / "all_bases.base"

    def _get_additional_properties(self, config: dict[str, Any]) -> tuple[list[str], list[str]]:
        """Get additional required and optional properties from config.

        Args:
            config: Note type configuration

        Returns:
            Tuple of (required, optional) property lists
        """
        props = config.get("properties", {})
        if isinstance(props, dict):
            required = props.get("additional_required", [])
            optional = props.get("optional", [])
            return required, optional
        elif isinstance(props, list):
            return props, []
        return [], []

    def create_structure(self, name: str, config: dict[str, Any]) -> None:
        """Create vault folder structure for a new note type.

        Args:
            name: Name of the note type
            config: Note type configuration
        """
        folder_hints = config.get("folder_hints", [])
        if not folder_hints:
            folder_hints = [f"{name.capitalize()}/"]
            config["folder_hints"] = folder_hints

        folder = folder_hints[0].rstrip("/")
        folder_path = self.vault_path / folder

        # Create folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Created folder: {folder}/")

        # Create MOC file
        self._create_moc(name, config, folder_path)

        # Update all_bases.base with new view
        self._update_bases_file(name, folder)

        # Create template
        self._create_template(name, config)

        # Create sample note
        self._create_sample_note(name, config, folder_path)

    def _create_moc(self, name: str, config: dict[str, Any], folder_path: Path) -> None:
        """Create MOC (Map of Content) file in the folder.

        Args:
            name: Note type name
            config: Note type configuration
            folder_path: Path to the folder
        """
        display_name = folder_path.name
        moc_filename = get_moc_filename(display_name)
        moc_path = folder_path / moc_filename
        if moc_path.exists():
            print(f"{moc_filename} already exists in {display_name}/")
            return

        description = config.get("description", f"Notes and content for {name.capitalize()}.")

        moc_content = f"""---
type: map
created: "{{{{date}}}}"
---

# {display_name}

{description}

## Contents

![[all_bases.base#{display_name}]]
"""
        moc_path.write_text(moc_content, encoding="utf-8")
        print(f"Created {moc_filename} in {display_name}/")

    def _update_bases_file(self, name: str, folder: str) -> None:
        """Add a new YAML view to all_bases.base.

        Args:
            name: Name of the note type
            folder: Folder path for the note type
        """
        if not self.all_bases_file.exists():
            print(f"Base file not found: {self.all_bases_file}")
            print("Run 'obsidian:init' first to initialize your vault.")
            return

        content = self.all_bases_file.read_text(encoding="utf-8")

        # Check if view already exists
        view_name = folder.split("/")[-1] if "/" in folder else folder
        if f"name: {view_name}" in content:
            print(f"View '{view_name}' already exists in all_bases.base")
            return

        # Create new YAML view entry
        new_view_lines = [
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

        # Append to end of file
        lines = content.rstrip().split("\n")
        lines.extend(new_view_lines)
        self.all_bases_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Added view '{view_name}' to all_bases.base")

    def _create_template(self, name: str, config: dict[str, Any]) -> None:
        """Create a template file for the note type.

        Args:
            name: Name of the note type
            config: Note type configuration
        """
        self.templates_folder.mkdir(parents=True, exist_ok=True)

        template_path = self.templates_folder / f"{name}.md"
        if template_path.exists():
            print(f"Template already exists: {template_path.name}")
            return

        description = config.get("description", f"{name.capitalize()} notes")
        required, optional = self._get_additional_properties(config)

        # Build frontmatter
        lines = ["---"]
        lines.append(f'type: "{name}"')

        for prop in self.core_properties:
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

        # Add required properties
        for prop in required:
            if prop == "status":
                lines.append('status: "active"')
            else:
                lines.append(f"{prop}: ")

        # Add optional properties as empty
        for prop in optional:
            if prop not in required:
                lines.append(f"{prop}: ")

        lines.append("---")
        lines.append("")
        lines.append("# {{title}}")
        lines.append("")
        lines.append(f"> Template for **{name.capitalize()}** notes: {description}")
        lines.append("")
        lines.append("## Content")
        lines.append("")
        lines.append("<!-- Your content here -->")
        lines.append("")
        lines.append("## Related")
        lines.append("")
        lines.append("- [[]]")
        lines.append("")

        template_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Created template: {self.system_prefix}/templates/{name}.md")

        # Update config to reference the template
        config["template"] = f"{self.system_prefix}/templates/{name}.md"

    def _create_sample_note(self, name: str, config: dict[str, Any], folder_path: Path) -> None:
        """Create a sample note in the folder.

        Args:
            name: Name of the note type
            config: Note type configuration
            folder_path: Path to the folder
        """
        sample_name = f"Sample {name.capitalize()}"
        sample_path = folder_path / f"{sample_name}.md"

        if sample_path.exists():
            print(f"Sample note already exists: {sample_name}.md")
            return

        description = config.get("description", f"{name.capitalize()} notes")
        required, optional = self._get_additional_properties(config)
        today = datetime.now().strftime("%Y-%m-%d")
        folder_name = folder_path.name
        moc_link = get_moc_link(folder_name)

        # Build frontmatter
        lines = ["---"]
        lines.append(f'type: "{name}"')

        for prop in self.core_properties:
            if prop == "type":
                continue
            elif prop == "up":
                lines.append(f'up: "{moc_link}"')
            elif prop == "created":
                lines.append(f"created: {today}")
            elif prop == "tags":
                lines.append(f"tags: [{name}]")
            elif prop == "daily":
                lines.append(f"daily: {today}")
            elif prop == "collection":
                lines.append("collection: ")
            elif prop == "related":
                lines.append("related: []")
            else:
                lines.append(f"{prop}: ")

        # Add required properties with sample values
        for prop in required:
            if prop == "status":
                lines.append('status: "active"')
            else:
                lines.append(f"{prop}: ")

        # Add optional properties
        for prop in optional:
            if prop not in required:
                lines.append(f"{prop}: ")

        lines.append("---")
        lines.append("")
        lines.append(f"# {sample_name}")
        lines.append("")
        lines.append(f"> This is a sample **{name}** note: {description}")
        lines.append("")
        lines.append("## Content")
        lines.append("")
        lines.append("This is a sample note. You can delete it after reviewing the structure.")
        lines.append("")
        lines.append("## Related")
        lines.append("")
        lines.append(f"- {moc_link}")
        lines.append("")

        sample_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Created sample note: {sample_name}.md")

    def remove_structure(
        self, name: str, config: dict[str, Any], remove_folder: bool = False
    ) -> None:
        """Remove vault structure for a note type.

        Args:
            name: Name of the note type
            config: Note type configuration
            remove_folder: If True, also remove the folder (if empty)
        """
        folder_hints = config.get("folder_hints", [])
        folder = folder_hints[0].rstrip("/") if folder_hints else name.capitalize()
        folder_path = self.vault_path / folder

        # Remove view from all_bases.base
        self._remove_from_bases_file(name, folder)

        # Remove template
        template_path = self.templates_folder / f"{name}.md"
        if template_path.exists():
            template_path.unlink()
            print(f"Removed template: {name}.md")

        # Remove sample note
        sample_path = folder_path / f"Sample {name.capitalize()}.md"
        if sample_path.exists():
            sample_path.unlink()
            print(f"Removed sample note: Sample {name.capitalize()}.md")

        # Remove MOC file
        folder_name = folder_path.name
        moc_filename = get_moc_filename(folder_name)
        moc_path = folder_path / moc_filename
        if moc_path.exists():
            moc_path.unlink()
            print(f"Removed {moc_filename} from {folder}/")

        # Remove folder if empty and requested
        if remove_folder and folder_path.exists():
            remaining = list(folder_path.iterdir())
            if not remaining:
                folder_path.rmdir()
                print(f"Removed empty folder: {folder}/")
            else:
                print(f"Folder {folder}/ not empty ({len(remaining)} files), keeping it")

    def _remove_from_bases_file(self, name: str, folder: str | None = None) -> None:
        """Remove a YAML view from all_bases.base.

        Args:
            name: Name of the note type
            folder: Folder path (used as view name)
        """
        if not self.all_bases_file.exists():
            return

        content = self.all_bases_file.read_text(encoding="utf-8")

        # The view name is the folder name (or capitalized type name if no folder)
        view_name = folder.split("/")[-1] if folder else name.capitalize()

        # Check if view exists
        if f"name: {view_name}" not in content:
            return

        # Parse YAML-style view entries and remove the matching one
        lines = content.split("\n")
        new_lines = []
        skip_view = False
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for view entry start
            if line.strip() == "- type: table":
                # Look ahead for the name line
                found_target = False
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("- type:"):
                    if lines[j].strip() == f"name: {view_name}":
                        found_target = True
                        break
                    j += 1

                if found_target:
                    # Skip this entire view entry
                    skip_view = True
                    i += 1
                    continue

            # Check if we're done skipping (next view entry or end)
            if skip_view and line.strip().startswith("- type:"):
                skip_view = False

            if not skip_view:
                new_lines.append(line)

            i += 1

        # Ensure trailing newline
        content_out = "\n".join(new_lines)
        if not content_out.endswith("\n"):
            content_out += "\n"

        self.all_bases_file.write_text(content_out, encoding="utf-8")
        print(f"Removed view '{view_name}' from all_bases.base")

    def rename_folder(self, name: str, old_folder: str, new_folder: str) -> None:
        """Rename a note type's folder in the vault.

        Args:
            name: Name of the note type
            old_folder: Old folder path (without trailing /)
            new_folder: New folder path (without trailing /)
        """
        old_path = self.vault_path / old_folder
        new_path = self.vault_path / new_folder

        if not old_path.exists():
            print(f"Old folder {old_folder}/ not found, creating {new_folder}/")
            new_path.mkdir(parents=True, exist_ok=True)
            print(f"Created folder: {new_folder}/")
            self._update_bases_file(name, new_folder)
            return

        if new_path.exists():
            print(f"Target folder {new_folder}/ already exists, not renaming")
            return

        try:
            old_path.rename(new_path)
            print(f"Renamed folder: {old_folder}/ -> {new_folder}/")

            # Update all_bases.base: remove old view, add new view
            self._remove_from_bases_file(name, old_folder)
            self._update_bases_file(name, new_folder)

            # Update MOC file if it exists
            old_folder_name = old_folder.split("/")[-1] if "/" in old_folder else old_folder
            new_folder_name = new_folder.split("/")[-1] if "/" in new_folder else new_folder
            old_moc_filename = get_moc_filename(old_folder_name)
            new_moc_filename = get_moc_filename(new_folder_name)
            old_moc_path = new_path / old_moc_filename
            new_moc_path = new_path / new_moc_filename

            if old_moc_path.exists():
                old_moc_path.rename(new_moc_path)
                self._update_moc_content(new_moc_path, old_folder_name, new_folder_name)

        except OSError as e:
            print(f"Failed to rename folder: {e}")

    def _update_moc_content(self, moc_path: Path, old_folder: str, new_folder: str) -> None:
        """Update folder references in MOC file.

        Args:
            moc_path: Path to MOC file
            old_folder: Old folder name
            new_folder: New folder name
        """
        try:
            content = moc_path.read_text(encoding="utf-8")
            updated = content.replace(f"##{old_folder}]]", f"##{new_folder}]]")
            updated = updated.replace(f"#{old_folder}]]", f"#{new_folder}]]")
            updated = updated.replace(f"# {old_folder}", f"# {new_folder}")
            if updated != content:
                moc_path.write_text(updated, encoding="utf-8")
                print(f"Updated {moc_path.name} references")
        except OSError:
            pass

    def update_template(self, name: str, config: dict[str, Any]) -> None:
        """Update template file with new properties.

        Args:
            name: Name of the note type
            config: Note type configuration with new properties
        """
        template_path = self.templates_folder / f"{name}.md"
        if not template_path.exists():
            return

        try:
            content = template_path.read_text(encoding="utf-8")

            if not content.startswith("---"):
                return

            parts = content.split("---", 2)
            if len(parts) < 3:
                return

            required, optional = self._get_additional_properties(config)
            description = config.get("description", f"{name.capitalize()} notes")

            # Build new frontmatter
            lines = ["---"]
            lines.append(f'type: "{name}"')

            for prop in self.core_properties:
                if prop == "type":
                    continue
                elif prop == "up":
                    lines.append('up: "[[]]"')
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

            for prop in required:
                if prop not in self.core_properties:
                    if prop == "status":
                        lines.append('status: "active"')
                    else:
                        lines.append(f"{prop}: ")

            for prop in optional:
                if prop not in self.core_properties and prop not in required:
                    lines.append(f"{prop}: ")

            lines.append("---")

            # Rebuild template with new frontmatter and updated description
            body = parts[2].strip()
            body_lines = body.split("\n")
            for i, line in enumerate(body_lines):
                if line.startswith("> Template for"):
                    body_lines[i] = f"> Template for **{name.capitalize()}** notes: {description}"
                    break

            new_content = "\n".join(lines) + "\n\n" + "\n".join(body_lines) + "\n"
            template_path.write_text(new_content, encoding="utf-8")
            print(f"Updated template: {self.system_prefix}/templates/{name}.md")

        except OSError:
            pass

    def update_notes_frontmatter(
        self, name: str, config: dict[str, Any], folder_path: Path
    ) -> None:
        """Update frontmatter in existing notes to include new properties.

        Args:
            name: Name of the note type
            config: Note type configuration with new properties
            folder_path: Path to the folder containing notes
        """
        if not folder_path.exists():
            return

        required, optional = self._get_additional_properties(config)
        all_props = set(self.core_properties) | set(required) | set(optional)

        updated_count = 0
        for note_path in folder_path.glob("*.md"):
            # Skip MOC files
            if note_path.name.startswith("_") and note_path.name.endswith("_MOC.md"):
                continue

            try:
                content = note_path.read_text(encoding="utf-8")
                if not content.startswith("---"):
                    continue

                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue

                frontmatter = parts[1].strip()
                body = parts[2]

                # Parse existing properties
                existing_props = set()
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        prop_name = line.split(":")[0].strip()
                        if not prop_name.startswith("#"):
                            existing_props.add(prop_name)

                # Find missing properties
                missing = all_props - existing_props

                if not missing:
                    continue

                # Add missing properties to frontmatter
                new_lines = frontmatter.split("\n")
                for prop in sorted(missing):
                    if prop == "status":
                        new_lines.append('status: ""')
                    else:
                        new_lines.append(f'{prop}: ""')

                new_content = "---\n" + "\n".join(new_lines) + "\n---" + body
                note_path.write_text(new_content, encoding="utf-8")
                updated_count += 1

            except OSError:
                continue

        if updated_count > 0:
            print(f"Updated frontmatter in {updated_count} note(s)")


# =============================================================================
# CLI Command Handlers
# =============================================================================


def _create_vault_manager(manager: NoteTypesManager) -> VaultStructureManager:
    """Create a VaultStructureManager from a NoteTypesManager."""
    return VaultStructureManager(
        manager.vault_path,
        manager.templates_folder,
        manager.bases_folder,
        manager.system_prefix,
        manager.get_core_properties(),
    )


def handle_add(
    manager: NoteTypesManager, name: str, config_json: str | None, non_interactive: bool
) -> None:
    """Handle the --add command."""
    config: dict[str, Any] = {}
    if config_json:
        try:
            config = json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON config: {e}")
            sys.exit(1)
    elif not non_interactive:
        config = interactive_type_definition(name)

    try:
        manager.add_type(name, config)
        print(f"\nAdded note type '{name}'")

        if not non_interactive or config_json:
            vault_mgr = _create_vault_manager(manager)
            vault_mgr.create_structure(name, manager.get_type(name) or {})
            manager._save_settings()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def handle_edit(
    manager: NoteTypesManager,
    name: str,
    config_json: str | None,
    non_interactive: bool,
    args: argparse.Namespace,
) -> None:
    """Handle the --edit command."""
    if not manager.get_type(name):
        print(f"Note type '{name}' not found")
        sys.exit(1)

    old_config = manager.get_type(name) or {}
    old_folder_hints = old_config.get("folder_hints", [])
    old_folder = old_folder_hints[0].rstrip("/") if old_folder_hints else name.capitalize()

    update_config: dict[str, Any] = {}

    if config_json:
        try:
            update_config = json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON config: {e}")
            sys.exit(1)
    elif not non_interactive:
        update_config = interactive_type_definition(name, old_config)
    else:
        if args.description:
            update_config["description"] = args.description
        if args.folder:
            update_config["folder"] = args.folder
        if args.required_props:
            update_config["required_props"] = [p.strip() for p in args.required_props.split(",")]
        if args.optional_props:
            update_config["optional_props"] = [p.strip() for p in args.optional_props.split(",")]
        if args.icon:
            update_config["icon"] = args.icon

    try:
        new_config = manager.update_type(name, update_config)

        new_folder_hints = new_config.get("folder_hints", [])
        new_folder = new_folder_hints[0].rstrip("/") if new_folder_hints else name.capitalize()

        vault_mgr = _create_vault_manager(manager)

        if old_folder != new_folder:
            vault_mgr.rename_folder(name, old_folder, new_folder)

        vault_mgr.update_template(name, new_config)
        folder_path = manager.vault_path / new_folder
        vault_mgr.update_notes_frontmatter(name, new_config, folder_path)

        print(f"Updated note type '{name}'")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def handle_remove(manager: NoteTypesManager, name: str, skip_confirm: bool) -> None:
    """Handle the --remove command."""
    if not manager.get_type(name):
        print(f"Note type '{name}' not found")
        sys.exit(1)

    if not skip_confirm:
        response = input(f"Delete note type '{name}'? (y/N): ").strip().lower()
        if response != "y":
            print("Cancelled")
            return

    config = manager.get_type(name) or {}
    try:
        manager.delete_type(name)

        vault_mgr = _create_vault_manager(manager)
        vault_mgr.remove_structure(name, config, remove_folder=True)

        print(f"Removed note type '{name}'")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def handle_wizard(manager: NoteTypesManager) -> None:
    """Handle the --wizard command."""

    def on_create(name: str, config: dict[str, Any]) -> None:
        manager.add_type(name, config)
        vault_mgr = _create_vault_manager(manager)
        vault_mgr.create_structure(name, manager.get_type(name) or {})
        manager._save_settings()

    run_wizard(manager.list_types(), on_create)
