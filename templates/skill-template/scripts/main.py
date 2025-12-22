#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
Your Skill Name - Main Script

Description of what this script does.

Usage:
    uv run scripts/main.py [options] <vault_path>

Examples:
    uv run scripts/main.py ~/Documents/MyVault
    uv run scripts/main.py --verbose ~/Documents/MyVault
"""

import argparse
import sys
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Your skill description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "vault_path",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to the Obsidian vault (default: current directory)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    return parser.parse_args()


def load_config(config_path: Path | None, vault_path: Path) -> dict:
    """Load configuration from file or use defaults."""
    # Default configuration
    config = {
        "setting_name": "default_value",
    }

    # Try to load from specified path or default location
    if config_path and config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
            config.update(user_config)
    else:
        # Try default location in vault
        default_config = vault_path / ".claude" / "config" / "your-skill.yaml"
        if default_config.exists():
            with open(default_config) as f:
                user_config = yaml.safe_load(f) or {}
                config.update(user_config)

    return config


def main() -> int:
    """Main entry point."""
    args = parse_args()
    vault_path = args.vault_path.resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}", file=sys.stderr)
        return 1

    config = load_config(args.config, vault_path)

    if args.verbose:
        print(f"Processing vault: {vault_path}")
        print(f"Configuration: {config}")

    # TODO: Implement your skill logic here
    print("Skill executed successfully!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
