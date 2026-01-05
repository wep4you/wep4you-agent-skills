#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Command Router for Obsidian Commands

Routes commands to their appropriate handlers while maintaining
backward compatibility with deprecated command names.

Usage:
    from router import CommandRouter, route_command

    # Route a command
    result = route_command("obsidian:config", ["show", "--vault", "/path"])

    # Or use the class directly
    router = CommandRouter()
    handler = router.get_handler("obsidian:types")
    handler(["list"])
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .deprecation import check_deprecation, get_replacement_command, show_deprecation_warning

# Type alias for command handlers
CommandHandler = Callable[[list[str]], int]


@dataclass
class CommandInfo:
    """Information about a registered command."""

    name: str
    handler: CommandHandler
    description: str = ""
    subcommands: list[str] = field(default_factory=list)


class CommandRouter:
    """Routes commands to their handlers with deprecation support."""

    def __init__(self) -> None:
        """Initialize the command router."""
        self._commands: dict[str, CommandInfo] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register all built-in obsidian commands."""
        # Register commands - handlers are lazy-loaded from skill scripts
        self.register(
            "obsidian:init",
            self._handler_init,
            "Initialize Obsidian vault",
        )
        self.register(
            "obsidian:config",
            self._handler_config,
            "Configuration management",
            subcommands=["show", "edit", "validate", "methodologies", "create"],
        )
        self.register(
            "obsidian:types",
            self._handler_types,
            "Note type management",
            subcommands=["list", "show", "add", "edit", "remove", "wizard"],
        )
        self.register(
            "obsidian:props",
            self._handler_props,
            "Property management",
            subcommands=["core", "type", "required", "add", "remove"],
        )
        self.register(
            "obsidian:templates",
            self._handler_templates,
            "Template management",
            subcommands=["list", "show", "create", "edit", "delete", "apply"],
        )
        self.register(
            "obsidian:validate",
            self._handler_validate,
            "Vault validation",
        )

    def register(
        self,
        name: str,
        handler: CommandHandler,
        description: str = "",
        subcommands: list[str] | None = None,
    ) -> None:
        """Register a command handler.

        Args:
            name: Command name (e.g., "obsidian:config")
            handler: Function to handle the command
            description: Human-readable description
            subcommands: List of available subcommands
        """
        self._commands[name] = CommandInfo(
            name=name,
            handler=handler,
            description=description,
            subcommands=subcommands or [],
        )

    def get_handler(self, command: str) -> CommandHandler | None:
        """Get handler for a command, checking deprecation.

        Args:
            command: Command name (with or without obsidian: prefix)

        Returns:
            Command handler function or None
        """
        # Check for deprecation and show warning
        if check_deprecation(command):
            show_deprecation_warning(command)
            replacement = get_replacement_command(command)
            if replacement:
                command = replacement

        # Normalize command name
        normalized = self._normalize_command(command)
        info = self._commands.get(normalized)
        return info.handler if info else None

    def _normalize_command(self, command: str) -> str:
        """Normalize command name to canonical form.

        Args:
            command: Input command name

        Returns:
            Normalized command name
        """
        # Strip leading /
        cmd = command.lstrip("/").strip()

        # Add obsidian: prefix if missing
        if not cmd.startswith("obsidian:"):
            cmd = f"obsidian:{cmd}"

        return cmd

    def list_commands(self) -> list[CommandInfo]:
        """List all registered commands.

        Returns:
            List of CommandInfo objects
        """
        return list(self._commands.values())

    def route(self, command: str, args: list[str]) -> int:
        """Route a command to its handler.

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Exit code from handler (0 = success)
        """
        handler = self.get_handler(command)
        if handler is None:
            print(f"Unknown command: {command}", file=sys.stderr)
            print("Available commands:", file=sys.stderr)
            for cmd_info in self.list_commands():
                print(f"  {cmd_info.name}: {cmd_info.description}", file=sys.stderr)
            return 1

        return handler(args)

    # Command handlers - these invoke the actual skill scripts

    def _handler_init(self, args: list[str]) -> int:
        """Handle obsidian:init command."""
        return self._run_skill_script("init", "init_vault.py", args)

    def _handler_config(self, args: list[str]) -> int:
        """Handle obsidian:config command."""
        return self._run_skill_script("config", "settings_loader.py", args)

    def _handler_types(self, args: list[str]) -> int:
        """Handle obsidian:types command."""
        return self._run_skill_script("note-types", "note_types.py", args)

    def _handler_props(self, args: list[str]) -> int:
        """Handle obsidian:props command."""
        return self._run_skill_script("frontmatter", "frontmatter.py", args)

    def _handler_templates(self, args: list[str]) -> int:
        """Handle obsidian:templates command."""
        return self._run_skill_script("templates", "templates.py", args)

    def _handler_validate(self, args: list[str]) -> int:
        """Handle obsidian:validate command."""
        # Transform --fix to --mode auto for backward compatibility
        transformed_args = []
        for arg in args:
            if arg == "--fix":
                transformed_args.extend(["--mode", "auto"])
            else:
                transformed_args.append(arg)

        return self._run_skill_script("validate", "validator.py", transformed_args)

    def _run_skill_script(
        self,
        skill_name: str,
        script_name: str,
        args: list[str],
    ) -> int:
        """Run a skill script with arguments.

        Args:
            skill_name: Name of the skill (directory name)
            script_name: Script filename
            args: Arguments to pass

        Returns:
            Exit code from script
        """
        import subprocess

        # Find script path
        skills_dir = Path(__file__).parent.parent
        script_path = skills_dir / skill_name / "scripts" / script_name

        if not script_path.exists():
            print(f"Script not found: {script_path}", file=sys.stderr)
            return 1

        try:
            # Using uv run to execute skill scripts (trusted internal paths)
            result = subprocess.run(  # noqa: S603
                ["/usr/bin/env", "uv", "run", str(script_path), *args],
                check=False,
            )
            return result.returncode
        except FileNotFoundError:
            # Fallback if uv not available
            try:
                result = subprocess.run(  # noqa: S603
                    [sys.executable, str(script_path), *args],
                    check=False,
                )
                return result.returncode
            except Exception as e:
                print(f"Error running script: {e}", file=sys.stderr)
                return 1


# Global router instance
_router: CommandRouter | None = None


def get_router() -> CommandRouter:
    """Get or create the global command router.

    Returns:
        CommandRouter instance
    """
    global _router
    if _router is None:
        _router = CommandRouter()
    return _router


def route_command(command: str, args: list[str] | None = None) -> int:
    """Route a command to its handler.

    Convenience function for the global router.

    Args:
        command: Command name (e.g., "obsidian:config")
        args: Command arguments

    Returns:
        Exit code (0 = success)
    """
    router = get_router()
    return router.route(command, args or [])


def main() -> int:
    """CLI entry point for command router."""
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian Command Router")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--list", action="store_true", help="List available commands")

    args = parser.parse_args()

    if args.list:
        router = get_router()
        print("\nObsidian Commands:")
        print("=" * 60)
        for cmd in router.list_commands():
            print(f"\n  {cmd.name}")
            print(f"    {cmd.description}")
            if cmd.subcommands:
                print(f"    Subcommands: {', '.join(cmd.subcommands)}")
        print()
        return 0

    if not args.command:
        parser.print_help()
        return 0

    return route_command(args.command, args.args)


if __name__ == "__main__":
    sys.exit(main())
