#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Template Wizard - Interactive template management for Obsidian vaults.

Provides interactive wizards for creating and deleting templates.
In non-interactive mode (Claude Code), returns JSON guidance.

Usage:
    uv run template_wizard.py create <name> [--vault /path]
    uv run template_wizard.py delete [--vault /path] [--yes]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Import from templates.py in same directory (not the parent package)
sys.path.insert(0, str(Path(__file__).parent))

if TYPE_CHECKING:
    from skills.templates.scripts.templates import TemplateManager
else:
    from templates import TemplateManager


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


def handle_create(manager: TemplateManager, name: str | None = None) -> None:
    """Handle create template action.

    Args:
        manager: TemplateManager instance
        name: Optional template name
    """
    if not is_interactive():
        # Non-interactive: return JSON guidance
        result = {
            "interactive_required": True,
            "action": "create_template",
            "message": "Provide --content flag for non-interactive creation",
            "schema": {
                "name": "Template name (without .md extension)",
                "content": "Markdown content with optional Templater syntax",
            },
            "example": {
                "command": (
                    f"obsidian:templates create {name or '<name>'} "
                    "--content '---\\ntype: meeting\\n---'"
                ),
            },
            "templater_syntax": {
                "date": "{{date}}",
                "title": "{{title}}",
                "type": "{{type}}",
            },
        }
        print(json.dumps(result, indent=2))
        return

    # Interactive wizard with Box UI
    print()
    print("\u250c" + "\u2500" * 58 + "\u2510")
    print("\u2502" + " CREATE TEMPLATE".ljust(58) + "\u2502")
    print("\u2514" + "\u2500" * 58 + "\u2518")

    if not name:
        name = input("\n  Template name: ").strip()

    if not name:
        print("  \u2717 Name cannot be empty")
        return

    # Check if template already exists
    existing = manager.list_templates(source="vault")
    existing_names = [t["name"] for t in existing]
    if name in existing_names:
        print(f"  \u2717 Template '{name}' already exists")
        return

    print("\n  Enter content (end with empty line):")
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break

    content = "\n".join(lines)

    if not content.strip():
        print("  \u2717 Content cannot be empty")
        return

    print(f"\n  Preview ({len(lines)} lines):")
    preview_lines = content.split("\n")[:5]
    for line in preview_lines:
        print(f"    {line}")
    if len(lines) > 5:
        print("    ...")

    if input("\n  Create? [y/N]: ").strip().lower() != "y":
        print("  Cancelled")
        return

    if manager.create_template(name, content):
        print(f"  \u2713 Created: {name}")
    else:
        print("  \u2717 Failed to create template")


def handle_delete(manager: TemplateManager, name: str | None = None, yes: bool = False) -> None:
    """Handle delete template action.

    Args:
        manager: TemplateManager instance
        name: Optional template name
        yes: Skip confirmation if True
    """
    templates = manager.list_templates(source="vault")
    template_names = [t["name"] for t in templates]

    if not is_interactive():
        # Non-interactive: return JSON guidance
        result = {
            "interactive_required": True,
            "action": "delete_template",
            "message": "Select a template to delete",
            "available_templates": template_names,
            "confirm_command": "obsidian:templates delete <name> --yes",
        }
        print(json.dumps(result, indent=2))
        return

    # Interactive: show list with selection
    print()
    print("\u250c" + "\u2500" * 58 + "\u2510")
    print("\u2502" + " DELETE TEMPLATE".ljust(58) + "\u2502")
    print("\u251c" + "\u2500" * 58 + "\u2524")
    if template_names:
        for i, t in enumerate(template_names, 1):
            print("\u2502" + f" {i}. {t}".ljust(58) + "\u2502")
    else:
        print("\u2502" + " (no templates found)".ljust(58) + "\u2502")
    print("\u2514" + "\u2500" * 58 + "\u2518")

    if not template_names:
        print("\n  No templates to delete.")
        return

    if not name:
        choice = input("\n  Delete [number or name]: ").strip()

        # Try to parse as number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(template_names):
                name = template_names[idx]
            else:
                print(f"  \u2717 Invalid selection: {choice}")
                return
        except ValueError:
            name = choice

    if name not in template_names:
        print(f"  \u2717 Template '{name}' not found")
        return

    # Show content preview
    content = manager.show_template(name)
    if content:
        preview = content[:200] + "..." if len(content) > 200 else content
        print("\n  Content preview:")
        for line in preview.split("\n")[:5]:
            print(f"    {line}")

    if input(f"\n  Delete '{name}'? [y/N]: ").strip().lower() != "y":
        print("  Cancelled")
        return

    if manager.delete_template(name):
        print(f"  \u2713 Deleted: {name}")
    else:
        print("  \u2717 Failed to delete template")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Template Wizard - Interactive template management",
    )
    parser.add_argument(
        "action",
        choices=["create", "delete"],
        help="Action to perform",
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="Template name (optional for delete)",
    )
    parser.add_argument(
        "--vault",
        type=str,
        default=".",
        help="Path to vault (default: current directory)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation (for non-interactive use)",
    )

    args = parser.parse_args()

    manager = TemplateManager(vault_path=args.vault)

    if args.action == "create":
        handle_create(manager, args.name)
    elif args.action == "delete":
        handle_delete(manager, args.name, args.yes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
