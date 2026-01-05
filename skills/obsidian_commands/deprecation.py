#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Deprecation Warning System for Obsidian Commands

Provides consistent deprecation warnings when users invoke deprecated commands.
Supports both CLI output and structured JSON for programmatic handling.

Usage:
    from deprecation import check_deprecation, format_deprecation_warning

    # Check if command is deprecated
    if check_deprecation("frontmatter"):
        warning = format_deprecation_warning("frontmatter")
        print(warning)

    # Get replacement command
    replacement = get_replacement_command("note-types")
    # Returns: "obsidian:types"
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import TextIO

# ANSI color codes
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"


@dataclass
class DeprecatedCommand:
    """Represents a deprecated command with its replacement info."""

    old_name: str
    replacement: str
    removed_in: str
    reason: str = ""


# Deprecated commands mapping
# Old command name -> DeprecatedCommand info
DEPRECATED_COMMANDS: dict[str, DeprecatedCommand] = {
    # Frontmatter -> Props
    "frontmatter": DeprecatedCommand(
        old_name="frontmatter",
        replacement="obsidian:props",
        removed_in="2.0.0",
        reason="Consolidated into unified property management",
    ),
    "/frontmatter": DeprecatedCommand(
        old_name="/frontmatter",
        replacement="obsidian:props",
        removed_in="2.0.0",
        reason="Consolidated into unified property management",
    ),
    # Note-types -> Types
    "note-types": DeprecatedCommand(
        old_name="note-types",
        replacement="obsidian:types",
        removed_in="2.0.0",
        reason="Simplified command name",
    ),
    "/note-types": DeprecatedCommand(
        old_name="/note-types",
        replacement="obsidian:types",
        removed_in="2.0.0",
        reason="Simplified command name",
    ),
    "obsidian:note-types": DeprecatedCommand(
        old_name="obsidian:note-types",
        replacement="obsidian:types",
        removed_in="2.0.0",
        reason="Simplified command name",
    ),
    # Config subcommands -> config <subcommand>
    "config-show": DeprecatedCommand(
        old_name="config-show",
        replacement="obsidian:config show",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    "/config-show": DeprecatedCommand(
        old_name="/config-show",
        replacement="obsidian:config show",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    "config-create": DeprecatedCommand(
        old_name="config-create",
        replacement="obsidian:config create",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    "/config-create": DeprecatedCommand(
        old_name="/config-create",
        replacement="obsidian:config create",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    "config-validate": DeprecatedCommand(
        old_name="config-validate",
        replacement="obsidian:config validate",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    "/config-validate": DeprecatedCommand(
        old_name="/config-validate",
        replacement="obsidian:config validate",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    "config-methodologies": DeprecatedCommand(
        old_name="config-methodologies",
        replacement="obsidian:config methodologies",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    "/config-methodologies": DeprecatedCommand(
        old_name="/config-methodologies",
        replacement="obsidian:config methodologies",
        removed_in="2.0.0",
        reason="Unified under obsidian:config",
    ),
    # Validate mode flag
    "--mode auto": DeprecatedCommand(
        old_name="--mode auto",
        replacement="--fix",
        removed_in="2.0.0",
        reason="Simplified flag name",
    ),
}


def check_deprecation(command: str) -> bool:
    """Check if a command is deprecated.

    Args:
        command: Command name to check (with or without leading /)

    Returns:
        True if command is deprecated, False otherwise
    """
    # Normalize command name
    normalized = command.strip()
    return normalized in DEPRECATED_COMMANDS


def get_replacement_command(command: str) -> str | None:
    """Get the replacement for a deprecated command.

    Args:
        command: Deprecated command name

    Returns:
        Replacement command name, or None if not deprecated
    """
    normalized = command.strip()
    if normalized in DEPRECATED_COMMANDS:
        return DEPRECATED_COMMANDS[normalized].replacement
    return None


def get_deprecation_info(command: str) -> DeprecatedCommand | None:
    """Get full deprecation info for a command.

    Args:
        command: Command name to check

    Returns:
        DeprecatedCommand dataclass or None
    """
    normalized = command.strip()
    return DEPRECATED_COMMANDS.get(normalized)


def format_deprecation_warning(
    command: str,
    use_color: bool = True,
    include_reason: bool = True,
) -> str:
    """Format a deprecation warning message.

    Args:
        command: Deprecated command name
        use_color: Whether to use ANSI colors
        include_reason: Whether to include the deprecation reason

    Returns:
        Formatted warning string
    """
    info = get_deprecation_info(command)
    if not info:
        return ""

    if use_color:
        yellow = COLOR_YELLOW
        cyan = COLOR_CYAN
        bold = COLOR_BOLD
        dim = COLOR_DIM
        reset = COLOR_RESET
    else:
        yellow = cyan = bold = dim = reset = ""

    msg = f"Command '{info.old_name}' is deprecated and will be removed in v{info.removed_in}."
    lines = [
        f"{yellow}{bold}DEPRECATION WARNING{reset}",
        f"{yellow}{msg}{reset}",
        f"{cyan}Use '{info.replacement}' instead.{reset}",
    ]

    if include_reason and info.reason:
        lines.append(f"{dim}Reason: {info.reason}{reset}")

    return "\n".join(lines)


def format_deprecation_json(command: str) -> str:
    """Format deprecation info as JSON for programmatic handling.

    Args:
        command: Deprecated command name

    Returns:
        JSON string with deprecation info
    """
    info = get_deprecation_info(command)
    if not info:
        return json.dumps({"deprecated": False})

    return json.dumps(
        {
            "deprecated": True,
            "old_command": info.old_name,
            "replacement": info.replacement,
            "removed_in": info.removed_in,
            "reason": info.reason,
        },
        indent=2,
    )


def show_deprecation_warning(
    command: str,
    file: TextIO | None = None,
    json_output: bool = False,
) -> None:
    """Print deprecation warning to stderr.

    Args:
        command: Command name to check
        file: Output file (default: stderr)
        json_output: Output as JSON instead of formatted text
    """
    if file is None:
        file = sys.stderr

    if not check_deprecation(command):
        return

    if json_output:
        print(format_deprecation_json(command), file=file)
    else:
        # Check if output supports color
        use_color = hasattr(file, "isatty") and file.isatty()
        print(format_deprecation_warning(command, use_color=use_color), file=file)
        print(file=file)  # Extra newline for readability


def list_deprecated_commands() -> list[dict[str, str]]:
    """List all deprecated commands.

    Returns:
        List of dicts with old_name, replacement, removed_in, reason
    """
    seen: set[str] = set()
    result: list[dict[str, str]] = []

    for info in DEPRECATED_COMMANDS.values():
        # Skip duplicates (with/without /)
        key = f"{info.old_name}|{info.replacement}"
        if key in seen:
            continue
        seen.add(key)

        result.append(
            {
                "old_name": info.old_name,
                "replacement": info.replacement,
                "removed_in": info.removed_in,
                "reason": info.reason,
            }
        )

    return sorted(result, key=lambda x: x["old_name"])


def main() -> int:
    """CLI for testing deprecation system."""
    import argparse

    parser = argparse.ArgumentParser(description="Deprecation Warning System")
    parser.add_argument("--check", metavar="CMD", help="Check if command is deprecated")
    parser.add_argument("--list", action="store_true", help="List all deprecated commands")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.list:
        deprecated = list_deprecated_commands()
        if args.json:
            print(json.dumps(deprecated, indent=2))
        else:
            print("\nDeprecated Commands:")
            print("=" * 70)
            for item in deprecated:
                print(f"\n  {item['old_name']}")
                print(f"    -> {item['replacement']}")
                print(f"    Removed in: v{item['removed_in']}")
                if item["reason"]:
                    print(f"    Reason: {item['reason']}")
            print()
        return 0

    if args.check:
        if check_deprecation(args.check):
            if args.json:
                print(format_deprecation_json(args.check))
            else:
                show_deprecation_warning(args.check, file=sys.stdout)
            return 1
        else:
            if args.json:
                print(json.dumps({"deprecated": False}))
            else:
                print(f"Command '{args.check}' is not deprecated.")
            return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
