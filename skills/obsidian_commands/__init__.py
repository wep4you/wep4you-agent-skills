#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Commands - Unified Command Router

Provides a unified entry point for all obsidian: namespace commands.
Handles command routing, deprecation warnings, and backward compatibility.

Usage:
    from obsidian_commands import route_command, show_deprecation_warning

Commands:
    obsidian:init       - Initialize vault
    obsidian:config     - Configuration management
    obsidian:types      - Note type management
    obsidian:props      - Property management (replaces frontmatter)
    obsidian:templates  - Template management
    obsidian:validate   - Vault validation
"""

from __future__ import annotations

from .deprecation import (
    DEPRECATED_COMMANDS,
    check_deprecation,
    format_deprecation_warning,
    get_replacement_command,
)
from .router import CommandRouter, route_command

__all__ = [
    "DEPRECATED_COMMANDS",
    "CommandRouter",
    "check_deprecation",
    "format_deprecation_warning",
    "get_replacement_command",
    "route_command",
]

__version__ = "1.0.0"
