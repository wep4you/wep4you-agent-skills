#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
Your Skill Name - Obsidian Vault Tool

Description of what this skill does for Obsidian vaults.

Usage:
    uv run scripts/main.py --vault /path/to/vault
    uv run scripts/main.py --vault . --verbose

Examples:
    uv run scripts/main.py --vault ~/Documents/MyVault
    uv run scripts/main.py --vault . --config config/custom.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Your Obsidian skill description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--vault",
        type=Path,
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


def load_config(config_path: Path | None, vault_path: Path) -> dict[str, Any]:
    """Load configuration from file or use defaults."""
    # Obsidian-specific default configuration
    config: dict[str, Any] = {
        "vault": {
            "daily_notes_folder": "Daily Notes",
            "templates_folder": "Templates",
        },
        "settings": {},
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


def find_markdown_files(vault_path: Path) -> list[Path]:
    """Find all markdown files in the vault."""
    return list(vault_path.rglob("*.md"))


def process_vault(
    vault_path: Path, config: dict[str, Any], verbose: bool = False
) -> dict[str, Any]:
    """Process the Obsidian vault.

    Returns:
        Dictionary with processing results
    """
    results: dict[str, Any] = {
        "files_processed": 0,
        "issues_found": 0,
        "changes_made": 0,
    }

    md_files = find_markdown_files(vault_path)

    for md_file in md_files:
        if verbose:
            print(f"Processing: {md_file.relative_to(vault_path)}")

        # TODO: Implement your vault processing logic here
        results["files_processed"] += 1

    return results


def main() -> int:
    """Main entry point."""
    args = parse_args()
    vault_path = args.vault.resolve()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}", file=sys.stderr)
        return 1

    # Check for .obsidian folder to verify it's an Obsidian vault
    if not (vault_path / ".obsidian").exists():
        print("Warning: No .obsidian folder found. Is this an Obsidian vault?", file=sys.stderr)

    config = load_config(args.config, vault_path)

    if args.verbose:
        print(f"Processing vault: {vault_path}")
        print(f"Configuration: {config}")

    results = process_vault(vault_path, config, verbose=args.verbose)

    print("\nResults:")
    print(f"  Files processed: {results['files_processed']}")
    print(f"  Issues found: {results['issues_found']}")
    print(f"  Changes made: {results['changes_made']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
