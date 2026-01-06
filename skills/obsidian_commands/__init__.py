#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Obsidian Commands - Unified Command Router

Provides a unified entry point for all obsidian: namespace commands.
Handles command routing and backward compatibility.

Usage:
    from obsidian_commands import route_command

Commands:
    obsidian:init       - Initialize vault
    obsidian:config     - Configuration management
    obsidian:types      - Note type management
    obsidian:props      - Property management
    obsidian:templates  - Template management
    obsidian:validate   - Vault validation
"""

from __future__ import annotations

from .router import CommandRouter, route_command

__all__ = [
    "CommandRouter",
    "route_command",
]

__version__ = "1.0.0"
