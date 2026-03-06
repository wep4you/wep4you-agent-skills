#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Templates Command - Template management for Obsidian notes

Provides unified template management with support for Templater plugin:
- obsidian:templates          List all templates
- obsidian:templates list     List all templates (explicit)
- obsidian:templates show     Show template content
- obsidian:templates create   Create new template
- obsidian:templates edit     Edit existing template
- obsidian:templates delete   Delete template
- obsidian:templates apply    Apply template to note

Usage:
    uv run templates_command.py --vault /path/to/vault
    uv run templates_command.py --vault /path/to/vault show map/basic
    uv run templates_command.py --vault /path/to/vault apply map/basic Atlas/Maps/NewNote.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Import from templates in same directory
sys.path.insert(0, str(Path(__file__).parent))
from templates import TemplateManager

# ANSI colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RED = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


def cmd_list(manager: TemplateManager, output_format: str = "text", source: str = "all") -> int:
    """List templates.

    Args:
        manager: TemplateManager instance
        output_format: Output format
        source: Filter by source (all, plugin, vault)

    Returns:
        Exit code
    """
    templates = manager.list_templates(source=source)

    if output_format == "json":
        print(json.dumps(templates, indent=2))
        return 0

    if not templates:
        print(f"{COLOR_YELLOW}No templates found.{COLOR_RESET}")
        return 0

    print(f"\n{COLOR_BOLD}Available Templates{COLOR_RESET}")
    print("=" * 60)
    print(f"\n{'Name':<30} {'Type':<15} {'Source':<10}")
    print("-" * 60)

    for template in templates:
        name = template["name"]
        ttype = template.get("type", "custom")
        source = template.get("source", "unknown")
        print(f"{name:<30} {ttype:<15} {source:<10}")

    print(f"\n{COLOR_DIM}Total: {len(templates)} templates{COLOR_RESET}")
    if manager.has_templater:
        templater = f"{COLOR_GREEN}installed{COLOR_RESET}"
    else:
        templater = f"{COLOR_DIM}not found{COLOR_RESET}"
    print(f"Templater: {templater}\n")

    return 0


def cmd_show(manager: TemplateManager, name: str) -> int:
    """Show template content.

    Args:
        manager: TemplateManager instance
        name: Template name

    Returns:
        Exit code
    """
    content = manager.show_template(name)

    if content is None:
        print(f"{COLOR_RED}Template not found: {name}{COLOR_RESET}")
        print(f"\nUse {COLOR_CYAN}obsidian:templates list{COLOR_RESET} to see available templates.")
        return 1

    print(f"\n{COLOR_BOLD}Template: {name}{COLOR_RESET}")
    print("-" * 50)
    print(content)
    return 0


def is_interactive() -> bool:
    """Check if running in an interactive terminal."""
    return sys.stdin.isatty()


def cmd_create(manager: TemplateManager, name: str, content: str | None = None) -> int:
    """Create a new template.

    Args:
        manager: TemplateManager instance
        name: Template name
        content: Optional template content

    Returns:
        Exit code
    """
    # If no content and not interactive, return JSON guidance
    if not content and not is_interactive():
        result = {
            "interactive_required": True,
            "action": "create",
            "name": name,
            "message": f"Provide --content to create template '{name}'",
            "config_schema": {
                "content": "Template content (Markdown with optional Templater syntax)",
            },
            "example": {
                "command": f"obsidian:templates create {name} --content '...'",
                "content_example": "---\ntype: {{type}}\ncreated: {{date}}\n---\n\n# {{title}}",
            },
        }
        print(json.dumps(result, indent=2))
        return 0

    if manager.create_template(name, content or ""):
        return 0
    return 1


def cmd_edit(manager: TemplateManager, name: str) -> int:
    """Edit a template.

    Args:
        manager: TemplateManager instance
        name: Template name

    Returns:
        Exit code
    """
    # If not interactive, return JSON guidance
    if not is_interactive():
        content = manager.show_template(name)
        result = {
            "interactive_required": True,
            "action": "edit",
            "name": name,
            "message": f"Cannot edit template '{name}' interactively. "
            "Use 'obsidian:templates show' to view, then create a new version.",
            "current_content": content,
            "hint": "In Claude Code mode, read the template file directly and edit it",
        }
        print(json.dumps(result, indent=2))
        return 0

    if manager.edit_template(name):
        return 0
    return 1


def cmd_delete(manager: TemplateManager, name: str, yes: bool = False) -> int:
    """Delete a template.

    Args:
        manager: TemplateManager instance
        name: Template name
        yes: Skip confirmation (--yes flag)

    Returns:
        Exit code
    """
    # If not interactive and no --yes flag, return JSON guidance
    if not yes and not is_interactive():
        content = manager.show_template(name)
        result = {
            "interactive_required": True,
            "action": "delete",
            "name": name,
            "message": f"Add --yes flag to confirm deletion of template '{name}'",
            "template_to_delete": {
                "name": name,
                "content_preview": (
                    content[:200] + "..." if content and len(content) > 200 else content
                ),
            },
            "warning": "This will permanently delete the template file.",
            "confirm_command": f"obsidian:templates delete {name} --yes",
        }
        print(json.dumps(result, indent=2))
        return 0

    if manager.delete_template(name):
        return 0
    return 1


def cmd_apply(
    manager: TemplateManager,
    template: str,
    target: str,
    variables: list[str] | None = None,
) -> int:
    """Apply template to a file.

    Args:
        manager: TemplateManager instance
        template: Template name
        target: Target file path
        variables: Variable substitutions

    Returns:
        Exit code
    """
    # Parse variables
    var_dict = {}
    if variables:
        for var in variables:
            if "=" in var:
                key, value = var.split("=", 1)
                var_dict[key] = value

    if manager.apply_template(template, target, var_dict):
        return 0
    return 1


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian Template Management (obsidian:templates)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  (none)           List all templates (same as 'list')
  list             List all templates
  show <name>      Show template content
  create <name>    Create new template
  edit <name>      Edit template in editor
  delete <name>    Delete template
  apply <template> <file>  Apply template to file

Examples:
  %(prog)s --vault .
  %(prog)s --vault . show map/basic
  %(prog)s --vault . create meeting
  %(prog)s --vault . apply map/basic Atlas/Maps/NewNote.md --var title=MyNote
        """,
    )

    parser.add_argument(
        "--vault",
        type=str,
        default=".",
        help="Path to vault (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--source",
        "-s",
        choices=["vault", "plugin", "all"],
        default="vault",
        help="Filter by source (default: vault)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # list
    list_parser = subparsers.add_parser("list", help="List templates")
    list_parser.add_argument(
        "--source",
        "-s",
        choices=["vault", "plugin", "all"],
        default="vault",
        help="Filter by source (default: vault)",
    )

    # show
    show_parser = subparsers.add_parser("show", help="Show template content")
    show_parser.add_argument("name", help="Template name (e.g., map/basic)")

    # create
    create_parser = subparsers.add_parser("create", help="Create new template")
    create_parser.add_argument("name", help="Template name")
    create_parser.add_argument("--content", help="Template content")

    # edit
    edit_parser = subparsers.add_parser("edit", help="Edit template")
    edit_parser.add_argument("name", help="Template name")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete template")
    delete_parser.add_argument("name", help="Template name")
    delete_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (required for non-interactive)",
    )

    # apply
    apply_parser = subparsers.add_parser("apply", help="Apply template to file")
    apply_parser.add_argument("template", help="Template name")
    apply_parser.add_argument("target", help="Target file path")
    apply_parser.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Variable substitution",
    )

    args = parser.parse_args()

    # Initialize manager
    manager = TemplateManager(vault_path=args.vault)

    # Route to handler
    if args.command is None or args.command == "list":
        source = getattr(args, "source", "all")
        return cmd_list(manager, args.format, source)
    elif args.command == "show":
        return cmd_show(manager, args.name)
    elif args.command == "create":
        return cmd_create(manager, args.name, getattr(args, "content", None))
    elif args.command == "edit":
        return cmd_edit(manager, args.name)
    elif args.command == "delete":
        return cmd_delete(manager, args.name, getattr(args, "yes", False))
    elif args.command == "apply":
        return cmd_apply(manager, args.template, args.target, args.var)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
