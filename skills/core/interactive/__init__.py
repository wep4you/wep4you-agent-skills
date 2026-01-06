"""
Interactive mode utilities for terminal vs Claude Code detection.

Provides functions to detect whether commands are running in an interactive
terminal or in Claude Code (non-interactive) mode, and format appropriate
responses for each case.
"""

from __future__ import annotations

import sys
from typing import Any


def is_interactive() -> bool:
    """Check if running in an interactive terminal.

    Returns True if stdin is connected to a TTY (terminal).
    Returns False in Claude Code mode (piped input, subprocess, etc.)

    Returns:
        True if interactive (terminal), False otherwise (Claude Code)
    """
    return sys.stdin.isatty()


def prompt_yes_no(message: str, default: bool = False) -> bool:
    """Prompt user for yes/no confirmation.

    Only works in interactive mode. In non-interactive mode,
    use is_interactive() to check and return JSON instead.

    Args:
        message: Prompt message to display
        default: Default value if user presses Enter

    Returns:
        True for yes, False for no
    """
    suffix = " [Y/n] " if default else " [y/N] "
    response = input(message + suffix).strip().lower()

    if not response:
        return default

    return response in ("y", "yes", "j", "ja")


def prompt_choice(message: str, choices: list[str], default: str | None = None) -> str:
    """Prompt user to select from choices.

    Only works in interactive mode. In non-interactive mode,
    use is_interactive() to check and return JSON instead.

    Args:
        message: Prompt message to display
        choices: List of valid choices
        default: Default choice if user presses Enter

    Returns:
        Selected choice
    """
    print(message)
    for i, choice in enumerate(choices, 1):
        marker = "*" if choice == default else " "
        print(f"  {marker}{i}. {choice}")

    while True:
        prompt = f"Select [1-{len(choices)}]"
        if default:
            prompt += f" (default: {default})"
        prompt += ": "

        response = input(prompt).strip()

        if not response and default:
            return default

        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            # Check if they typed the choice name
            if response in choices:
                return response

        print(f"Please enter a number between 1 and {len(choices)}")


def format_non_interactive_response(
    action: str,
    name: str | None = None,
    message: str | None = None,
    schema: dict[str, Any] | None = None,
    example: dict[str, Any] | None = None,
    current_config: dict[str, Any] | None = None,
    confirm_command: str | None = None,
    warning: str | None = None,
    **extra: dict[str, Any],
) -> dict[str, Any]:
    """Format a response for non-interactive (Claude Code) mode.

    Creates a structured JSON response that tells Claude Code what
    information is needed to complete the action.

    Args:
        action: The action being performed (add, edit, remove, create, delete)
        name: Name of the item being acted upon
        message: Human-readable message explaining what's needed
        schema: Schema describing required configuration fields
        example: Example of how to use the command non-interactively
        current_config: Current configuration (for edit actions)
        confirm_command: Command to run to confirm (for remove/delete)
        warning: Warning message about the action
        **extra: Additional fields to include in response

    Returns:
        Dict with interactive_required=True and provided fields
    """
    result: dict[str, Any] = {
        "interactive_required": True,
        "action": action,
    }

    if name is not None:
        result["name"] = name

    if message is not None:
        result["message"] = message

    if schema is not None:
        result["config_schema"] = schema

    if example is not None:
        result["example"] = example

    if current_config is not None:
        result["current_config"] = current_config

    if confirm_command is not None:
        result["confirm_command"] = confirm_command

    if warning is not None:
        result["warning"] = warning

    # Add any extra fields
    result.update(extra)

    return result
