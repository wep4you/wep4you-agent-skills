#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Configuration Loader for Obsidian Vault
Loads, saves, and merges YAML configuration files with vault-specific overrides

Usage:
    from config_loader import load_config, save_config, merge_configs

    # Load config with vault overrides
    config = load_config(Path("/path/to/vault"))

    # Save custom config
    save_config(Path("/path/to/vault"), custom_config)

    # Merge configs
    merged = merge_configs(base_config, override_config)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

# Default configuration embedded in script
DEFAULT_CONFIG: dict[str, Any] = {
    "core_properties": [
        "type",
        "up",
        "created",
        "daily",
        "tags",
        "collection",
        "related",
    ],
    "note_types": {
        "map": {
            "description": "Map of Content - Overview and navigation notes",
            "folder_hints": ["Atlas/Maps/", "Maps/"],
            "properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        },
        "dot": {
            "description": "Dot notes - Atomic concepts and ideas",
            "folder_hints": ["Atlas/Dots/", "Dots/"],
            "properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        },
        "source": {
            "description": "Source notes - External references and citations",
            "folder_hints": ["Atlas/Sources/", "Sources/"],
            "properties": [
                "type",
                "up",
                "created",
                "daily",
                "tags",
                "collection",
                "related",
                "author",
                "url",
            ],
        },
        "project": {
            "description": "Project notes - Defined outcomes with deadlines",
            "folder_hints": ["Efforts/Projects/", "Projects/"],
            "properties": [
                "type",
                "up",
                "created",
                "daily",
                "tags",
                "collection",
                "related",
                "status",
                "deadline",
            ],
        },
        "area": {
            "description": "Area notes - Ongoing responsibilities",
            "folder_hints": ["Efforts/Areas/", "Areas/"],
            "properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        },
        "effort": {
            "description": "Effort notes - Work and tasks",
            "folder_hints": ["Efforts/"],
            "properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        },
        "daily": {
            "description": "Daily notes - Date-based journal entries",
            "folder_hints": ["Calendar/daily/", "daily/"],
            "properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        },
    },
    "validation": {
        "require_core_properties": True,
        "allow_empty_properties": ["tags", "collection", "related"],
        "strict_types": True,
    },
    "auto_fix": {
        "empty_types": True,
        "daily_links": True,
        "wikilink_quotes": True,
        "title_properties": True,
        "missing_properties": True,
    },
    "exclude_paths": [
        "+/",  # Inbox
        "x/",  # System files
        ".obsidian/",
        ".claude/",
        ".git/",
    ],
    "exclude_files": [
        "Home.md",
        "README.md",
        "CHANGELOG.md",
    ],
}


def load_config(vault_path: Path, config_name: str = "default.yaml") -> dict[str, Any]:
    """
    Load configuration with vault-specific overrides.

    Lookup order:
    1. .claude/config/{config_name} in vault (user override)
    2. skills/config/config/{config_name} (skill default)
    3. DEFAULT_CONFIG (embedded fallback)

    Args:
        vault_path: Path to Obsidian vault root
        config_name: Name of config file to load (default: "default.yaml")

    Returns:
        Merged configuration dictionary

    Raises:
        ValueError: If vault_path doesn't exist or isn't a directory
    """
    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise ValueError(f"Vault path is not a directory: {vault_path}")

    # Start with default config
    config = DEFAULT_CONFIG.copy()

    # Try to load skill default config
    skill_config_path = Path(__file__).parent.parent / "config" / config_name
    if skill_config_path.exists():
        try:
            with skill_config_path.open("r", encoding="utf-8") as f:
                skill_config = yaml.safe_load(f)
                if skill_config:
                    config = merge_configs(config, skill_config)
        except yaml.YAMLError as e:
            print(f"Warning: Failed to load skill config {skill_config_path}: {e}", file=sys.stderr)

    # Try to load vault-specific override
    vault_config_path = vault_path / ".claude" / "config" / config_name
    if vault_config_path.exists():
        try:
            with vault_config_path.open("r", encoding="utf-8") as f:
                vault_config = yaml.safe_load(f)
                if vault_config:
                    config = merge_configs(config, vault_config)
        except yaml.YAMLError as e:
            print(f"Warning: Failed to load vault config {vault_config_path}: {e}", file=sys.stderr)

    return config


def save_config(vault_path: Path, config: dict[str, Any], config_name: str = "custom.yaml") -> None:
    """
    Save configuration to vault-specific location.

    Saves to: {vault_path}/.claude/config/{config_name}

    Args:
        vault_path: Path to Obsidian vault root
        config: Configuration dictionary to save
        config_name: Name of config file (default: "custom.yaml")

    Raises:
        ValueError: If vault_path doesn't exist or isn't a directory
        OSError: If config directory cannot be created or file cannot be written
    """
    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise ValueError(f"Vault path is not a directory: {vault_path}")

    config_dir = vault_path / ".claude" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / config_name
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two configuration dictionaries.

    Override values take precedence over base values.
    Nested dictionaries are merged recursively.
    Lists are replaced (not merged).

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary

    Examples:
        >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> override = {"b": {"c": 4}, "e": 5}
        >>> merge_configs(base, override)
        {'a': 1, 'b': {'c': 4, 'd': 3}, 'e': 5}
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_configs(result[key], value)
        else:
            # Replace value (including lists)
            result[key] = value

    return result


def get_note_type_config(config: dict[str, Any], note_type: str) -> dict[str, Any] | None:
    """
    Get configuration for a specific note type.

    Args:
        config: Configuration dictionary
        note_type: Note type identifier (e.g., "map", "dot", "source")

    Returns:
        Note type configuration dictionary or None if not found
    """
    note_types = config.get("note_types", {})
    return note_types.get(note_type)


def infer_note_type(file_path: Path, config: dict[str, Any]) -> str | None:
    """
    Infer note type from file path based on folder hints.

    Args:
        file_path: Path to markdown file
        config: Configuration dictionary

    Returns:
        Inferred note type or None if no match
    """
    note_types = config.get("note_types", {})
    file_path_str = str(file_path)

    for note_type, type_config in note_types.items():
        folder_hints = type_config.get("folder_hints", [])
        for hint in folder_hints:
            if hint in file_path_str:
                return note_type

    return None


def validate_config(config: dict[str, Any]) -> list[str]:
    """
    Validate configuration structure and required fields.

    Args:
        config: Configuration dictionary to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Check core_properties
    if "core_properties" not in config:
        errors.append("Missing 'core_properties' in configuration")
    elif not isinstance(config["core_properties"], list):
        errors.append("'core_properties' must be a list")
    elif not config["core_properties"]:
        errors.append("'core_properties' cannot be empty")

    # Check note_types
    if "note_types" not in config:
        errors.append("Missing 'note_types' in configuration")
    elif not isinstance(config["note_types"], dict):
        errors.append("'note_types' must be a dictionary")
    elif not config["note_types"]:
        errors.append("'note_types' cannot be empty")
    else:
        # Validate each note type
        for note_type, type_config in config["note_types"].items():
            if not isinstance(type_config, dict):
                errors.append(f"Note type '{note_type}' must be a dictionary")
                continue

            if "properties" not in type_config:
                errors.append(f"Note type '{note_type}' missing 'properties'")
            elif not isinstance(type_config["properties"], list):
                errors.append(f"Note type '{note_type}' 'properties' must be a list")

    return errors


def main() -> int:
    """CLI entry point for testing config loader."""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration Loader for Obsidian Vault")
    parser.add_argument("--vault", type=Path, required=True, help="Path to vault")
    parser.add_argument("--config", default="default.yaml", help="Config file name")
    parser.add_argument("--validate", action="store_true", help="Validate config structure")
    parser.add_argument("--show", action="store_true", help="Show loaded configuration")

    args = parser.parse_args()

    try:
        config = load_config(args.vault, args.config)

        if args.validate:
            errors = validate_config(config)
            if errors:
                print("Configuration validation errors:", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
                return 1
            print("Configuration is valid")

        if args.show:
            print(yaml.safe_dump(config, default_flow_style=False, sort_keys=False))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
