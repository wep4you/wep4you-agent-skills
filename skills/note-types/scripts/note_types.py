#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Note Types Manager - CRUD operations for Obsidian note types

Manages note type definitions by reading from and writing to .claude/settings.yaml.
This integrates with the init skill and settings_loader for a unified configuration.

Usage:
    uv run scripts/note_types.py --list
    uv run scripts/note_types.py --show map
    uv run scripts/note_types.py --add blog
    uv run scripts/note_types.py --edit project
    uv run scripts/note_types.py --remove custom
    uv run scripts/note_types.py --wizard
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Settings file path (relative to vault root)
SETTINGS_FILE = ".claude/settings.yaml"


class NoteTypesManager:
    """Manages note type definitions in .claude/settings.yaml"""

    def __init__(self, vault_path: str | None = None) -> None:
        """Initialize the note types manager

        Args:
            vault_path: Path to vault root. If None, uses current directory.
        """
        self.vault_path = Path(vault_path) if vault_path else Path.cwd()
        self.settings_path = self.vault_path / SETTINGS_FILE
        self.settings: dict[str, Any] = {}
        self.note_types: dict[str, dict[str, Any]] = {}
        self._load_settings()

        # Read folder paths from folder_structure (single source of truth)
        folder_structure = self.settings.get("folder_structure", {})
        templates_path = folder_structure.get("templates", "x/templates/").rstrip("/")
        bases_path = folder_structure.get("bases", "x/bases/").rstrip("/")

        # Extract system prefix from templates path (e.g., "x" from "x/templates")
        self.system_prefix = templates_path.split("/")[0] if "/" in templates_path else "x"
        self.templates_folder = self.vault_path / templates_path
        self.bases_folder = self.vault_path / bases_path
        self.all_bases_file = self.bases_folder / "all_bases.base"

    def _load_settings(self) -> None:
        """Load settings from .claude/settings.yaml"""
        if not self.settings_path.exists():
            print(f"❌ Settings file not found: {self.settings_path}")
            print("   Run 'obsidian:init' first to initialize your vault.")
            sys.exit(1)

        try:
            with open(self.settings_path, encoding="utf-8") as f:
                self.settings = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"❌ Error parsing settings.yaml: {e}")
            sys.exit(1)

        # Extract note_types section
        self.note_types = self.settings.get("note_types", {})
        if not self.note_types:
            print("⚠️  No note types found in settings.yaml")
            print("   The vault may not be properly initialized.")
        else:
            methodology = self.settings.get("methodology", "unknown")
            print(f"✅ Loaded {len(self.note_types)} note types ({methodology} methodology)\n")

    def _save_settings(self) -> None:
        """Save settings back to .claude/settings.yaml"""
        self.settings["note_types"] = self.note_types

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    self.settings,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            print(f"✅ Saved settings to {self.settings_path}")
        except OSError as e:
            print(f"❌ Error saving settings: {e}")
            sys.exit(1)

    def _get_core_properties(self) -> list[str]:
        """Get list of core properties from settings

        Returns:
            List of core property names
        """
        core_props = self.settings.get("core_properties", {})
        if isinstance(core_props, dict):
            result = core_props.get("all", ["type", "up", "created"])
            return list(result) if result else ["type", "up", "created"]
        elif isinstance(core_props, list):
            return core_props
        return ["type", "up", "created"]

    def _get_additional_properties(self, config: dict[str, Any]) -> tuple[list[str], list[str]]:
        """Get additional required and optional properties from config

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

    def _build_frontmatter(
        self, name: str, config: dict[str, Any], use_placeholders: bool = False
    ) -> str:
        """Build frontmatter YAML for a note

        Args:
            name: Note type name
            config: Note type configuration
            use_placeholders: If True, use {{date}} etc. for templates

        Returns:
            Frontmatter string including --- delimiters
        """
        core_props = self._get_core_properties()
        required, optional = self._get_additional_properties(config)

        today = datetime.now().strftime("%Y-%m-%d")
        lines = ["---"]

        # Add all core properties
        for prop in core_props:
            if prop == "type":
                lines.append(f"type: {name}")
            elif prop == "created":
                lines.append(f"created: {'{{date}}' if use_placeholders else today}")
            elif prop == "up":
                lines.append('up: "[[_Readme]]"' if not use_placeholders else 'up: ""')
            elif prop == "daily":
                lines.append(f"daily: {'{{date}}' if use_placeholders else today}")
            elif prop == "tags":
                lines.append(f"tags: [{name}]" if not use_placeholders else "tags: []")
            else:
                lines.append(f'{prop}: ""')

        # Add additional required properties
        for prop in required:
            if prop not in core_props:
                lines.append(f'{prop}: ""')

        # Add optional properties as comments in templates, empty in samples
        for prop in optional:
            if prop not in core_props and prop not in required:
                if use_placeholders:
                    lines.append(f"# {prop}: ")
                else:
                    lines.append(f'{prop}: ""')

        lines.append("---")
        return "\n".join(lines)

    def _create_vault_structure(self, name: str, config: dict[str, Any]) -> None:
        """Create vault folder structure for a new note type

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
        print(f"📁 Created folder: {folder}/")

        # Create _Readme.md
        self._create_readme(name, config, folder_path)

        # Update all_bases.base with new view
        self._update_bases_file(name, folder)

        # Create template
        self._create_template(name, config)

        # Create sample note
        self._create_sample_note(name, config, folder_path)

    def _create_readme(self, name: str, config: dict[str, Any], folder_path: Path) -> None:
        """Create _Readme.md in the folder (matches init skill format)

        Args:
            name: Note type name
            config: Note type configuration
            folder_path: Path to the folder
        """
        readme_path = folder_path / "_Readme.md"
        if readme_path.exists():
            print(f"ℹ️  _Readme.md already exists in {folder_path.name}/")
            return

        description = config.get("description", f"Notes and content for {name.capitalize()}.")
        display_name = folder_path.name

        # Match init skill's simple _Readme format
        readme_content = f"""---
type: map
created: "{{{{date}}}}"
---

# {display_name}

{description}

## Contents

![[all_bases.base#{display_name}]]
"""
        readme_path.write_text(readme_content, encoding="utf-8")
        print(f"📄 Created _Readme.md in {folder_path.name}/")

    def _update_bases_file(self, name: str, folder: str) -> None:
        """Add a new YAML view to all_bases.base (matches init skill format)

        Args:
            name: Name of the note type
            folder: Folder path for the note type
        """
        if not self.all_bases_file.exists():
            print(f"⚠️  Base file not found: {self.all_bases_file}")
            print("   Run 'obsidian:init' first to initialize your vault.")
            return

        content = self.all_bases_file.read_text(encoding="utf-8")

        # Check if view already exists (look for "name: FolderName" in views)
        view_name = folder.split("/")[-1] if "/" in folder else folder
        if f"name: {view_name}" in content:
            print(f"ℹ️  View '{view_name}' already exists in all_bases.base")
            return

        # Create new YAML view entry (matches init skill format)
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
        print(f"📊 Added view '{view_name}' to all_bases.base")

    def _create_template(self, name: str, config: dict[str, Any]) -> None:
        """Create a template file for the note type (matches init skill format)

        Args:
            name: Name of the note type
            config: Note type configuration
        """
        self.templates_folder.mkdir(parents=True, exist_ok=True)

        template_path = self.templates_folder / f"{name}.md"
        if template_path.exists():
            print(f"ℹ️  Template already exists: {template_path.name}")
            return

        description = config.get("description", f"{name.capitalize()} notes")
        core_props = self._get_core_properties()
        required, optional = self._get_additional_properties(config)

        # Build frontmatter matching init skill format
        lines = ["---"]
        lines.append(f'type: "{name}"')

        for prop in core_props:
            if prop == "type":
                continue  # Already added above
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
        print(f"📝 Created template: {self.system_prefix}/templates/{name}.md")

        # Update config to reference the template
        config["template"] = f"{self.system_prefix}/templates/{name}.md"

    def _create_sample_note(self, name: str, config: dict[str, Any], folder_path: Path) -> None:
        """Create a sample note in the folder (matches template structure)

        Args:
            name: Name of the note type
            config: Note type configuration
            folder_path: Path to the folder
        """
        sample_name = f"Sample {name.capitalize()}"
        sample_path = folder_path / f"{sample_name}.md"

        if sample_path.exists():
            print(f"ℹ️  Sample note already exists: {sample_name}.md")
            return

        description = config.get("description", f"{name.capitalize()} notes")
        core_props = self._get_core_properties()
        required, optional = self._get_additional_properties(config)
        today = datetime.now().strftime("%Y-%m-%d")

        # Build frontmatter matching template format but with values filled in
        lines = ["---"]
        lines.append(f'type: "{name}"')

        for prop in core_props:
            if prop == "type":
                continue  # Already added above
            elif prop == "up":
                lines.append('up: "[[_Readme]]"')
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
        lines.append("- [[_Readme]]")
        lines.append("")

        sample_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"📄 Created sample note: {sample_name}.md")

    def _remove_vault_structure(
        self, name: str, config: dict[str, Any], remove_folder: bool = False
    ) -> None:
        """Remove vault structure for a note type

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
            print(f"🗑️  Removed template: {name}.md")

        # Remove sample note
        sample_path = folder_path / f"Sample {name.capitalize()}.md"
        if sample_path.exists():
            sample_path.unlink()
            print(f"🗑️  Removed sample note: Sample {name.capitalize()}.md")

        # Remove _Readme.md
        readme_path = folder_path / "_Readme.md"
        if readme_path.exists():
            readme_path.unlink()
            print(f"🗑️  Removed _Readme.md from {folder}/")

        # Remove folder if empty and requested
        if remove_folder and folder_path.exists():
            remaining = list(folder_path.iterdir())
            if not remaining:
                folder_path.rmdir()
                print(f"🗑️  Removed empty folder: {folder}/")
            else:
                print(f"ℹ️  Folder {folder}/ not empty ({len(remaining)} files), keeping it")

    def _remove_from_bases_file(self, name: str, folder: str | None = None) -> None:
        """Remove a YAML view from all_bases.base

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
        print(f"📊 Removed view '{view_name}' from all_bases.base")

    def _format_properties(self, nt_config: dict[str, Any]) -> list[str]:
        """Extract all properties from note type config

        Args:
            nt_config: Note type configuration dict

        Returns:
            List of all property names
        """
        props = nt_config.get("properties", {})
        if isinstance(props, list):
            return props

        all_props: list[str] = []
        if "additional_required" in props:
            all_props.extend(props.get("additional_required", []))
        if "optional" in props:
            all_props.extend(props.get("optional", []))
        return all_props

    def list_types(self) -> None:
        """List all note types"""
        if not self.note_types:
            print("No note types defined.")
            return

        core_props = self._get_core_properties()

        print(f"📋 Note Types ({len(self.note_types)}):\n")
        print(f"   Core properties: {', '.join(core_props)}\n")

        for name, config in sorted(self.note_types.items()):
            description = config.get("description", "")
            folder_hints = config.get("folder_hints", [])
            props = self._format_properties(config)
            icon = config.get("icon", "")

            print(f"  {icon} {name}")
            if description:
                print(f"    Description: {description}")
            print(f"    Folders: {', '.join(folder_hints)}")
            if props:
                print(f"    Additional properties: {', '.join(props)}")
            print()

    def show_type(self, name: str) -> None:
        """Show details for a specific note type

        Args:
            name: Name of the note type
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            print(f"   Available: {', '.join(self.note_types.keys())}")
            sys.exit(1)

        config = self.note_types[name]
        icon = config.get("icon", "📄")

        print(f"{icon} Note Type: {name}\n")
        print(f"  Description: {config.get('description', '-')}")
        print(f"  Folders: {', '.join(config.get('folder_hints', []))}")

        print(f"  Core properties: {', '.join(self._get_core_properties())}")

        props = config.get("properties", {})
        if isinstance(props, dict):
            req = props.get("additional_required", [])
            opt = props.get("optional", [])
            if req:
                print(f"  Required properties: {', '.join(req)}")
            if opt:
                print(f"  Optional properties: {', '.join(opt)}")
        elif isinstance(props, list):
            print(f"  Properties: {', '.join(props)}")

        validation = config.get("validation", {})
        if validation:
            print(f"  Validation: {validation}")

        if "template" in config:
            print(f"  Template: {config['template']}")
        print()

    def add_type(
        self,
        name: str,
        interactive: bool = True,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Add a new note type

        Args:
            name: Name of the note type
            interactive: Whether to prompt for details interactively
            config: Optional config dict (for non-interactive mode with full config)
        """
        if name in self.note_types:
            print(f"❌ Note type '{name}' already exists")
            print("   Use --edit to modify it")
            sys.exit(1)

        if config:
            # Use provided config, normalize structure
            final_config = self._normalize_config(name, config)
        elif interactive:
            final_config = self._interactive_type_definition(name)
        else:
            final_config = {
                "description": f"{name.capitalize()} notes",
                "folder_hints": [f"{name.capitalize()}/"],
                "properties": {
                    "additional_required": [],
                    "optional": [],
                },
                "validation": {
                    "allow_empty_up": False,
                },
                "icon": "file",
            }

        self.note_types[name] = final_config
        self._save_settings()
        self._create_vault_structure(name, final_config)
        # Save again to persist template path
        self._save_settings()
        print(f"\n✅ Added note type '{name}'")
        self.show_type(name)

    def _normalize_config(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Normalize a config dict to the expected structure

        Args:
            name: Note type name (for defaults)
            config: Input config dict

        Returns:
            Normalized config dict
        """
        # Start with defaults
        normalized: dict[str, Any] = {
            "description": config.get("description", f"{name.capitalize()} notes"),
            "folder_hints": [],
            "properties": {
                "additional_required": [],
                "optional": [],
            },
            "validation": {
                "allow_empty_up": config.get("allow_empty_up", False),
            },
            "icon": config.get("icon", "file"),
        }

        # Handle folder/folder_hints
        if "folder" in config:
            folder = config["folder"]
            normalized["folder_hints"] = [folder if folder.endswith("/") else f"{folder}/"]
        elif "folder_hints" in config:
            normalized["folder_hints"] = config["folder_hints"]
        else:
            normalized["folder_hints"] = [f"{name.capitalize()}/"]

        # Handle properties
        if "required_props" in config or "required" in config:
            props = config.get("required_props", config.get("required", []))
            if isinstance(props, str):
                props = [p.strip() for p in props.split(",")]
            normalized["properties"]["additional_required"] = props

        if "optional_props" in config or "optional" in config:
            props = config.get("optional_props", config.get("optional", []))
            if isinstance(props, str):
                props = [p.strip() for p in props.split(",")]
            normalized["properties"]["optional"] = props

        # Handle nested properties format
        if "properties" in config and isinstance(config["properties"], dict):
            if "additional_required" in config["properties"]:
                normalized["properties"]["additional_required"] = config["properties"][
                    "additional_required"
                ]
            if "optional" in config["properties"]:
                normalized["properties"]["optional"] = config["properties"]["optional"]

        return normalized

    def edit_type(
        self,
        name: str,
        interactive: bool = True,
        config: dict[str, Any] | None = None,
        description: str | None = None,
        folder: str | None = None,
        required_props: list[str] | None = None,
        optional_props: list[str] | None = None,
        icon: str | None = None,
    ) -> None:
        """Edit an existing note type

        Args:
            name: Name of the note type
            interactive: Whether to prompt for details interactively
            config: Full config dict (replaces all settings from JSON)
            description: New description (non-interactive mode)
            folder: New folder hint (non-interactive mode)
            required_props: New required properties (non-interactive mode)
            optional_props: New optional properties (non-interactive mode)
            icon: New icon (non-interactive mode)
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            sys.exit(1)

        # Capture old folder before changes
        old_config = self.note_types[name]
        old_folder_hints = old_config.get("folder_hints", [])
        old_folder = old_folder_hints[0].rstrip("/") if old_folder_hints else name.capitalize()

        print(f"📝 Editing note type: {name}\n")
        self.show_type(name)

        if config:
            # Full config provided - merge with existing, only update explicitly provided fields
            final_config = self.note_types[name].copy()

            # Only update fields that were explicitly provided in the config
            if "description" in config:
                final_config["description"] = config["description"]

            if "folder" in config or "folder_hints" in config:
                folder = config.get("folder", config.get("folder_hints", [None])[0])
                if folder:
                    final_config["folder_hints"] = [
                        folder if folder.endswith("/") else f"{folder}/"
                    ]

            if "icon" in config:
                final_config["icon"] = config["icon"]

            if "allow_empty_up" in config:
                final_config.setdefault("validation", {})["allow_empty_up"] = config[
                    "allow_empty_up"
                ]

            # Handle properties
            if (
                "required_props" in config
                or "required" in config
                or "optional_props" in config
                or "optional" in config
                or "properties" in config
            ):
                props = final_config.get("properties", {})
                if not isinstance(props, dict):
                    props = {"additional_required": [], "optional": []}

                if "required_props" in config or "required" in config:
                    req = config.get("required_props", config.get("required", []))
                    if isinstance(req, str):
                        req = [p.strip() for p in req.split(",")]
                    props["additional_required"] = req

                if "optional_props" in config or "optional" in config:
                    opt = config.get("optional_props", config.get("optional", []))
                    if isinstance(opt, str):
                        opt = [p.strip() for p in opt.split(",")]
                    props["optional"] = opt

                if "properties" in config and isinstance(config["properties"], dict):
                    if "additional_required" in config["properties"]:
                        props["additional_required"] = config["properties"]["additional_required"]
                    if "optional" in config["properties"]:
                        props["optional"] = config["properties"]["optional"]

                final_config["properties"] = props
        elif interactive:
            final_config = self._interactive_type_definition(name, self.note_types[name])
        else:
            # Non-interactive with individual parameters
            final_config = self.note_types[name].copy()

            if description is not None:
                final_config["description"] = description

            if folder is not None:
                final_config["folder_hints"] = [folder if folder.endswith("/") else f"{folder}/"]

            if required_props is not None or optional_props is not None:
                props = final_config.get("properties", {})
                if not isinstance(props, dict):
                    props = {"additional_required": [], "optional": []}
                if required_props is not None:
                    props["additional_required"] = required_props
                if optional_props is not None:
                    props["optional"] = optional_props
                final_config["properties"] = props

            if icon is not None:
                final_config["icon"] = icon

        # Check if folder changed
        new_folder_hints = final_config.get("folder_hints", [])
        new_folder = new_folder_hints[0].rstrip("/") if new_folder_hints else name.capitalize()

        self.note_types[name] = final_config
        self._save_settings()

        # Handle folder rename if folder changed
        if old_folder != new_folder:
            self._rename_folder(name, old_folder, new_folder)

        # Update template with new properties
        self._update_template_properties(name, final_config)

        # Update existing notes' frontmatter with new properties
        folder_path = self.vault_path / new_folder
        self._update_notes_frontmatter(name, final_config, folder_path)

        print(f"✅ Updated note type '{name}'")
        self.show_type(name)

    def _rename_folder(self, name: str, old_folder: str, new_folder: str) -> None:
        """Rename a note type's folder in the vault

        Args:
            name: Name of the note type
            old_folder: Old folder path (without trailing /)
            new_folder: New folder path (without trailing /)
        """
        old_path = self.vault_path / old_folder
        new_path = self.vault_path / new_folder

        if not old_path.exists():
            print(f"ℹ️  Old folder {old_folder}/ not found, creating {new_folder}/")
            new_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created folder: {new_folder}/")
            # Update all_bases.base with new folder
            self._update_bases_file(name, new_folder)
            return

        if new_path.exists():
            print(f"⚠️  Target folder {new_folder}/ already exists, not renaming")
            return

        # Rename the folder
        try:
            old_path.rename(new_path)
            print(f"📁 Renamed folder: {old_folder}/ → {new_folder}/")

            # Update all_bases.base: remove old view, add new view
            self._remove_from_bases_file(name, old_folder)
            self._update_bases_file(name, new_folder)

            # Update _Readme.md if it exists
            readme_path = new_path / "_Readme.md"
            if readme_path.exists():
                self._update_readme_folder(readme_path, old_folder, new_folder)

        except OSError as e:
            print(f"❌ Failed to rename folder: {e}")

    def _update_readme_folder(self, readme_path: Path, old_folder: str, new_folder: str) -> None:
        """Update folder references in _Readme.md

        Args:
            readme_path: Path to _Readme.md
            old_folder: Old folder name
            new_folder: New folder name
        """
        try:
            content = readme_path.read_text(encoding="utf-8")
            # Update the embed reference
            old_view_name = old_folder.split("/")[-1] if "/" in old_folder else old_folder
            new_view_name = new_folder.split("/")[-1] if "/" in new_folder else new_folder
            updated = content.replace(f"##{old_view_name}]]", f"##{new_view_name}]]")
            updated = updated.replace(f"#{old_view_name}]]", f"#{new_view_name}]]")
            if updated != content:
                readme_path.write_text(updated, encoding="utf-8")
                print("📝 Updated _Readme.md references")
        except OSError:
            pass  # Ignore errors updating readme

    def _update_template_properties(self, name: str, config: dict[str, Any]) -> None:
        """Update template file with new properties

        Args:
            name: Name of the note type
            config: Note type configuration with new properties
        """
        template_path = self.templates_folder / f"{name}.md"
        if not template_path.exists():
            return

        try:
            content = template_path.read_text(encoding="utf-8")

            # Parse existing frontmatter
            if not content.startswith("---"):
                return

            parts = content.split("---", 2)
            if len(parts) < 3:
                return

            # Get new properties
            core_props = self._get_core_properties()
            required, optional = self._get_additional_properties(config)
            description = config.get("description", f"{name.capitalize()} notes")

            # Build new frontmatter
            lines = ["---"]
            lines.append(f'type: "{name}"')

            for prop in core_props:
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
                if prop not in core_props:
                    if prop == "status":
                        lines.append('status: "active"')
                    else:
                        lines.append(f"{prop}: ")

            for prop in optional:
                if prop not in core_props and prop not in required:
                    lines.append(f"{prop}: ")

            lines.append("---")

            # Rebuild template with new frontmatter and updated description
            body = parts[2].strip()
            # Update description line if present
            body_lines = body.split("\n")
            for i, line in enumerate(body_lines):
                if line.startswith("> Template for"):
                    body_lines[i] = f"> Template for **{name.capitalize()}** notes: {description}"
                    break

            new_content = "\n".join(lines) + "\n\n" + "\n".join(body_lines) + "\n"
            template_path.write_text(new_content, encoding="utf-8")
            print(f"📝 Updated template: {self.system_prefix}/templates/{name}.md")

        except OSError:
            pass

    def _update_notes_frontmatter(
        self, name: str, config: dict[str, Any], folder_path: Path
    ) -> None:
        """Update frontmatter in existing notes to include new properties

        Args:
            name: Name of the note type
            config: Note type configuration with new properties
            folder_path: Path to the folder containing notes
        """
        if not folder_path.exists():
            return

        core_props = self._get_core_properties()
        required, optional = self._get_additional_properties(config)
        all_props = set(core_props) | set(required) | set(optional)

        updated_count = 0
        for note_path in folder_path.glob("*.md"):
            if note_path.name == "_Readme.md":
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
            print(f"📝 Updated frontmatter in {updated_count} note(s)")

    def remove_type(self, name: str, skip_confirm: bool = False) -> None:
        """Remove a note type

        Args:
            name: Name of the note type
            skip_confirm: Skip confirmation prompt (for non-interactive use)
        """
        if name not in self.note_types:
            print(f"❌ Note type '{name}' not found")
            sys.exit(1)

        if not skip_confirm:
            response = input(f"⚠️  Delete note type '{name}'? (y/N): ").strip().lower()
            if response != "y":
                print("Cancelled")
                return

        config = self.note_types[name]
        del self.note_types[name]
        self._save_settings()
        self._remove_vault_structure(name, config, remove_folder=True)
        print(f"✅ Removed note type '{name}'")

    def _interactive_type_definition(
        self, name: str, existing: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Interactively build a note type definition

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

    def wizard(self) -> None:
        """Interactive wizard to create a new note type"""
        print("🧙 Note Type Wizard\n")
        print("Let's create a new note type for your Obsidian vault.\n")

        while True:
            name = input("Note type name: ").strip().lower()
            if not name:
                print("❌ Name cannot be empty")
                continue
            if name in self.note_types:
                print(f"❌ Note type '{name}' already exists")
                continue
            break

        config = self._interactive_type_definition(name)

        print("\n📋 Summary:")
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

        response = input("\n✅ Create this note type? (Y/n): ").strip().lower()
        if response and response != "y":
            print("Cancelled")
            return

        self.note_types[name] = config
        self._save_settings()
        self._create_vault_structure(name, config)
        self._save_settings()  # Save again for template path
        print(f"\n✅ Created note type '{name}'")


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage Obsidian note types in settings.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

List & Show:
  %(prog)s --list                           # List all note types
  %(prog)s --show project                   # Show details for 'project'

Add with JSON config (RECOMMENDED):
  %(prog)s --add meeting --config '{
    "description": "Meeting notes",
    "folder": "Meetings/",
    "required_props": ["attendees", "date"],
    "optional_props": ["action_items"],
    "icon": "calendar"
  }'

Add with minimal defaults:
  %(prog)s --add blog --non-interactive     # Creates Blog/ with defaults

Edit with JSON config (RECOMMENDED):
  %(prog)s --edit meeting --config '{
    "description": "Updated description",
    "required_props": ["attendees", "date", "location"]
  }'

Edit with individual parameters:
  %(prog)s --edit project --non-interactive --description "New desc" --icon "rocket"
  %(prog)s --edit project --non-interactive --required-props "status,priority"
  %(prog)s --edit project --non-interactive --folder "NewFolder/"

Remove:
  %(prog)s --remove meeting --yes           # Remove without confirmation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIG JSON FIELDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  description     : Note type description (string)
  folder          : Folder path, e.g. "Meetings/" (string)
  required_props  : Required properties (array or comma-separated string)
  optional_props  : Optional properties (array or comma-separated string)
  icon            : Lucide icon name, e.g. "calendar" (string)
  allow_empty_up  : Allow empty up links (boolean, default: false)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """,
    )

    parser.add_argument("--vault", help="Path to vault root (default: current directory)")
    parser.add_argument("--list", action="store_true", help="List all note types")
    parser.add_argument("--show", metavar="NAME", help="Show details for a note type")
    parser.add_argument("--add", metavar="NAME", help="Add a new note type")
    parser.add_argument("--edit", metavar="NAME", help="Edit an existing note type")
    parser.add_argument("--remove", metavar="NAME", help="Remove a note type")
    parser.add_argument("--wizard", action="store_true", help="Interactive wizard (terminal only)")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use minimal defaults (for --add) or individual params (for --edit)",
    )
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation (for --remove)")
    parser.add_argument(
        "--config",
        metavar="JSON",
        help="Full JSON config for --add/--edit (RECOMMENDED)",
    )
    # Individual edit parameters (alternative to --config)
    parser.add_argument("--description", help="Note type description")
    parser.add_argument("--folder", help="Folder path (e.g., Meetings/)")
    parser.add_argument(
        "--required-props", metavar="PROPS", help="Comma-separated required properties"
    )
    parser.add_argument(
        "--optional-props", metavar="PROPS", help="Comma-separated optional properties"
    )
    parser.add_argument("--icon", help="Lucide icon name (e.g., calendar, file, target)")

    args = parser.parse_args()

    actions = [args.list, args.show, args.add, args.edit, args.remove, args.wizard]
    if not any(actions):
        parser.print_help()
        sys.exit(1)

    manager = NoteTypesManager(args.vault)

    if args.list:
        manager.list_types()
    elif args.show:
        manager.show_type(args.show)
    elif args.add:
        # Parse JSON config if provided
        config = None
        if args.config:
            try:
                config = json.loads(args.config)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON config: {e}")
                sys.exit(1)
        manager.add_type(args.add, interactive=not args.non_interactive, config=config)
    elif args.edit:
        # Parse JSON config if provided
        config = None
        if args.config:
            try:
                config = json.loads(args.config)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON config: {e}")
                sys.exit(1)

        # Parse comma-separated properties if provided
        required_props = None
        optional_props = None
        if args.required_props:
            required_props = [p.strip() for p in args.required_props.split(",")]
        if args.optional_props:
            optional_props = [p.strip() for p in args.optional_props.split(",")]

        manager.edit_type(
            args.edit,
            interactive=not args.non_interactive and not config,
            config=config,
            description=args.description,
            folder=args.folder,
            required_props=required_props,
            optional_props=optional_props,
            icon=args.icon,
        )
    elif args.remove:
        manager.remove_type(args.remove, skip_confirm=args.yes)
    elif args.wizard:
        manager.wizard()


if __name__ == "__main__":
    main()
