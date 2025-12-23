#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Template Manager for Obsidian Vaults
Manage note templates with support for Templater plugin and simple variables
Version: 1.0.0

Usage:
    uv run scripts/templates.py --list
    uv run scripts/templates.py --show <name>
    uv run scripts/templates.py --create <name>
    uv run scripts/templates.py --edit <name>
    uv run scripts/templates.py --delete <name>
    uv run scripts/templates.py --apply <name> <file>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class TemplateManager:
    """Manages Obsidian note templates with Templater support"""

    def __init__(self, vault_path: str | None = None):
        """Initialize template manager

        Args:
            vault_path: Path to Obsidian vault (default: current directory)
        """
        self.vault_path = Path(vault_path or Path.cwd())
        self.plugin_templates_dir = self._find_plugin_templates_dir()
        self.vault_templates_dir = self._find_vault_templates_dir()
        self.has_templater = self._detect_templater()

    def _find_plugin_templates_dir(self) -> Path:
        """Find plugin templates directory"""
        # Look for skills/templates/templates or templates/ relative to vault
        candidates = [
            self.vault_path / "skills" / "templates" / "templates",
            self.vault_path / "templates",
            Path(__file__).parent.parent.parent.parent / "templates",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Default to templates directory in project root
        return Path(__file__).parent.parent.parent.parent / "templates"

    def _find_vault_templates_dir(self) -> Path | None:
        """Find vault-specific templates directory"""
        candidates = [
            self.vault_path / ".obsidian" / "templates",
            self.vault_path / "Templates",
            self.vault_path / "templates",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate

        return None

    def _detect_templater(self) -> bool:
        """Detect if Templater plugin is installed"""
        templater_dir = self.vault_path / ".obsidian" / "plugins" / "templater-obsidian"
        return templater_dir.exists() and templater_dir.is_dir()

    def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates

        Returns:
            List of template info dicts with name, path, source
        """
        templates = []

        # Plugin templates
        if self.plugin_templates_dir.exists():
            for template_dir in self.plugin_templates_dir.iterdir():
                if template_dir.is_dir():
                    for template_file in template_dir.glob("*.md"):
                        templates.append(
                            {
                                "name": f"{template_dir.name}/{template_file.stem}",
                                "path": str(template_file),
                                "source": "plugin",
                                "type": template_dir.name,
                            }
                        )

        # Vault templates
        if self.vault_templates_dir:
            for template_file in self.vault_templates_dir.glob("*.md"):
                templates.append(
                    {
                        "name": template_file.stem,
                        "path": str(template_file),
                        "source": "vault",
                        "type": "custom",
                    }
                )

        return sorted(templates, key=lambda x: x["name"])

    def show_template(self, name: str) -> str | None:
        """Show template content

        Args:
            name: Template name (e.g., 'map/basic' or 'my-template')

        Returns:
            Template content or None if not found
        """
        template_path = self._resolve_template_path(name)
        if not template_path:
            return None

        return template_path.read_text()

    def create_template(self, name: str, content: str = "") -> bool:
        """Create new template

        Args:
            name: Template name (e.g., 'map/new-template')
            content: Template content (default: basic template)

        Returns:
            True if created successfully
        """
        if not self.vault_templates_dir:
            print("❌ No vault templates directory found")
            print("   Create one at: .obsidian/templates/ or Templates/")
            return False

        # Use default content if not provided
        if not content:
            content = self._get_default_template()

        template_path = self.vault_templates_dir / f"{name}.md"
        template_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            template_path.write_text(content)
            print(f"✅ Created template: {template_path}")
            return True
        except Exception as e:
            print(f"❌ Error creating template: {e}")
            return False

    def edit_template(self, name: str) -> bool:
        """Open template in system editor

        Args:
            name: Template name

        Returns:
            True if editor launched successfully
        """
        template_path = self._resolve_template_path(name)
        if not template_path:
            print(f"❌ Template not found: {name}")
            return False

        # Open in system editor
        editor = os.environ.get("EDITOR", "vim")
        try:
            import subprocess

            subprocess.run([editor, str(template_path)], check=False)  # noqa: S603
            return True
        except Exception as e:
            print(f"❌ Error opening editor: {e}")
            return False

    def delete_template(self, name: str) -> bool:
        """Delete template (vault templates only)

        Args:
            name: Template name

        Returns:
            True if deleted successfully
        """
        template_path = self._resolve_template_path(name)
        if not template_path:
            print(f"❌ Template not found: {name}")
            return False

        # Only allow deleting vault templates
        if self.vault_templates_dir and not str(template_path).startswith(
            str(self.vault_templates_dir)
        ):
            print(f"❌ Cannot delete plugin template: {name}")
            print("   Only vault templates can be deleted")
            return False

        try:
            template_path.unlink()
            print(f"✅ Deleted template: {template_path}")
            return True
        except Exception as e:
            print(f"❌ Error deleting template: {e}")
            return False

    def apply_template(
        self, template_name: str, target_file: str, variables: dict[str, str] | None = None
    ) -> bool:
        """Apply template to file

        Args:
            template_name: Template name
            target_file: Target file path
            variables: Variable substitutions

        Returns:
            True if applied successfully
        """
        template_path = self._resolve_template_path(template_name)
        if not template_path:
            print(f"❌ Template not found: {template_name}")
            return False

        content = template_path.read_text()

        # Substitute variables
        if variables is None:
            variables = {}

        # Add default variables
        defaults = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": Path(target_file).stem,
        }
        variables = {**defaults, **variables}

        # Apply variable substitution
        content = self._substitute_variables(content, variables)

        # Write to target file
        target_path = Path(target_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            target_path.write_text(content)
            print(f"✅ Applied template to: {target_path}")
            return True
        except Exception as e:
            print(f"❌ Error applying template: {e}")
            return False

    def _resolve_template_path(self, name: str) -> Path | None:
        """Resolve template name to path

        Args:
            name: Template name (e.g., 'map/basic' or 'my-template')

        Returns:
            Path to template or None if not found
        """
        # Try vault templates first
        if self.vault_templates_dir:
            vault_template = self.vault_templates_dir / f"{name}.md"
            if vault_template.exists():
                return vault_template

        # Try plugin templates
        if "/" in name:
            # Type-specific template (e.g., 'map/basic')
            template_type, template_name = name.split("/", 1)
            plugin_template = self.plugin_templates_dir / template_type / f"{template_name}.md"
            if plugin_template.exists():
                return plugin_template
        else:
            # Search all plugin template directories
            for template_dir in self.plugin_templates_dir.iterdir():
                if template_dir.is_dir():
                    template_file = template_dir / f"{name}.md"
                    if template_file.exists():
                        return template_file

        return None

    def _substitute_variables(self, content: str, variables: dict[str, str]) -> str:
        """Substitute variables in template content

        Supports:
        - Simple syntax: {{variable}}
        - Templater syntax: <% tp.date.now() %> (if Templater installed)

        Args:
            content: Template content
            variables: Variable substitutions

        Returns:
            Content with variables substituted
        """
        # Simple variable substitution {{variable}}
        for var, value in variables.items():
            content = content.replace(f"{{{{{var}}}}}", value)

        # Templater syntax support (basic - just replace known patterns)
        if self.has_templater:
            # Replace common Templater patterns with actual values
            content = re.sub(
                r"<% tp\.date\.now\([^)]*\) %>",
                datetime.now().strftime("%Y-%m-%d"),
                content,
            )
            content = re.sub(
                r"<% tp\.date\.tomorrow\([^)]*\) %>",
                datetime.now().strftime("%Y-%m-%d"),
                content,
            )
            content = re.sub(
                r"<% tp\.file\.title %>",
                variables.get("title", ""),
                content,
            )

        return content

    def _get_default_template(self) -> str:
        """Get default template content"""
        return """---
type: {{type}}
up: "[[{{up}}]]"
created: {{date}}
daily: "[[{{date}}]]"
collection:
related: []
---

# {{title}}

## Overview


## Notes

"""


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage Obsidian note templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--vault", help="Path to Obsidian vault (default: current directory)")

    # Commands
    commands = parser.add_mutually_exclusive_group(required=True)
    commands.add_argument("--list", action="store_true", help="List all templates")
    commands.add_argument("--show", metavar="NAME", help="Show template content")
    commands.add_argument("--create", metavar="NAME", help="Create new template")
    commands.add_argument("--edit", metavar="NAME", help="Edit template")
    commands.add_argument("--delete", metavar="NAME", help="Delete template")
    commands.add_argument(
        "--apply",
        nargs=2,
        metavar=("TEMPLATE", "FILE"),
        help="Apply template to file",
    )

    # Additional options
    parser.add_argument("--content", help="Template content (for --create)")
    parser.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Variable for template substitution (for --apply)",
    )

    args = parser.parse_args()

    manager = TemplateManager(vault_path=args.vault)

    # Execute command
    if args.list:
        templates = manager.list_templates()
        if not templates:
            print("No templates found")
            return 0

        print(f"\n{'Name':<30} {'Type':<15} {'Source':<10}")
        print("=" * 60)
        for template in templates:
            print(f"{template['name']:<30} {template['type']:<15} {template['source']:<10}")
        print(f"\nTotal: {len(templates)} templates")
        print(f"Templater: {'✅ installed' if manager.has_templater else '❌ not found'}")
        return 0

    elif args.show:
        content = manager.show_template(args.show)
        if content is None:
            print(f"❌ Template not found: {args.show}")
            return 1
        print(content)
        return 0

    elif args.create:
        content = args.content or ""
        if manager.create_template(args.create, content):
            return 0
        return 1

    elif args.edit:
        if manager.edit_template(args.edit):
            return 0
        return 1

    elif args.delete:
        if manager.delete_template(args.delete):
            return 0
        return 1

    elif args.apply:
        template_name, target_file = args.apply

        # Parse variables
        variables = {}
        if args.var:
            for var_pair in args.var:
                if "=" in var_pair:
                    key, value = var_pair.split("=", 1)
                    variables[key] = value

        if manager.apply_template(template_name, target_file, variables):
            return 0
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
