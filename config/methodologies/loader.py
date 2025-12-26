#!/usr/bin/env python3
"""
Methodology Loader for Obsidian Vault Initialization

Loads methodology configurations from YAML files in the config/methodologies/ directory.
This module serves as the single source of truth for methodology definitions,
replacing hardcoded dictionaries in init_vault.py.

Usage:
    from config.methodologies.loader import (
        load_methodology,
        load_all_methodologies,
        get_methodology_names,
        METHODOLOGIES_DIR,
    )

    # Load a single methodology
    lyt_ace = load_methodology("lyt-ace")

    # Get all available methodology names
    names = get_methodology_names()  # ["lyt-ace", "para", "zettelkasten", "minimal"]

    # Load all methodologies at once
    all_methods = load_all_methodologies()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Directory containing methodology YAML files
METHODOLOGIES_DIR = Path(__file__).parent

# Cache for loaded methodologies
_methodology_cache: dict[str, dict[str, Any]] = {}


class MethodologyNotFoundError(Exception):
    """Raised when a requested methodology YAML file is not found."""

    pass


class MethodologyParseError(Exception):
    """Raised when a methodology YAML file cannot be parsed."""

    pass


def get_methodology_names() -> list[str]:
    """
    Get list of available methodology names.

    Returns:
        List of methodology names (without .yaml extension)

    Example:
        >>> names = get_methodology_names()
        >>> print(names)
        ['lyt-ace', 'minimal', 'para', 'zettelkasten']
    """
    yaml_files = METHODOLOGIES_DIR.glob("*.yaml")
    return sorted([f.stem for f in yaml_files if f.stem != "README"])


def load_methodology(name: str, use_cache: bool = True) -> dict[str, Any]:
    """
    Load a methodology configuration from its YAML file.

    Args:
        name: Methodology name (e.g., "lyt-ace", "para")
        use_cache: Whether to use cached result if available

    Returns:
        Dictionary with methodology configuration in init_vault.py format

    Raises:
        MethodologyNotFoundError: If YAML file doesn't exist
        MethodologyParseError: If YAML is invalid or missing required fields

    Example:
        >>> method = load_methodology("para")
        >>> print(method["name"])
        'PARA'
        >>> print(method["folders"])
        ['Projects', 'Areas', 'Resources', 'Archives', '+', 'x/templates', 'x/bases']
    """
    # Check cache first
    if use_cache and name in _methodology_cache:
        return _methodology_cache[name]

    # Find and load YAML file
    yaml_path = METHODOLOGIES_DIR / f"{name}.yaml"
    if not yaml_path.exists():
        available = get_methodology_names()
        raise MethodologyNotFoundError(
            f"Methodology '{name}' not found. Available: {', '.join(available)}"
        )

    try:
        with yaml_path.open("r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise MethodologyParseError(f"Invalid YAML in {yaml_path}: {e}") from e

    if not raw_data:
        raise MethodologyParseError(f"Empty YAML file: {yaml_path}")

    # Validate required fields
    methodology = _validate_and_transform(raw_data, name)

    # Cache the result
    _methodology_cache[name] = methodology

    return methodology


def _validate_and_transform(raw: dict[str, Any], name: str) -> dict[str, Any]:
    """
    Validate and transform raw YAML data to init_vault.py format.

    Args:
        raw: Raw YAML data
        name: Methodology name (for error messages)

    Returns:
        Validated and transformed methodology dict

    Raises:
        MethodologyParseError: If required fields are missing or invalid
    """
    required_fields = [
        "name",
        "description",
        "folders",
        "core_properties",
        "note_types",
    ]

    missing = [f for f in required_fields if f not in raw]
    if missing:
        raise MethodologyParseError(f"Methodology '{name}' missing required fields: {missing}")

    # Validate folders is a list
    if not isinstance(raw["folders"], list):
        raise MethodologyParseError(f"Methodology '{name}': 'folders' must be a list")

    # Validate core_properties is a list
    if not isinstance(raw["core_properties"], list):
        raise MethodologyParseError(f"Methodology '{name}': 'core_properties' must be a list")

    # Validate and transform note_types
    note_types = {}
    for nt_name, nt_config in raw.get("note_types", {}).items():
        note_types[nt_name] = _validate_note_type(nt_name, nt_config, name)

    # Build the methodology dict in init_vault.py format
    methodology = {
        "name": raw["name"],
        "description": raw["description"],
        "folders": raw["folders"],
        "core_properties": raw["core_properties"],
        "note_types": note_types,
        "folder_structure": raw.get("folder_structure", {}),
        "up_links": raw.get("up_links", {}),
    }

    return methodology


def _validate_note_type(
    nt_name: str, config: dict[str, Any], methodology_name: str
) -> dict[str, Any]:
    """
    Validate and transform a note type configuration.

    Args:
        nt_name: Note type name
        config: Note type configuration from YAML
        methodology_name: Parent methodology name (for error messages)

    Returns:
        Validated note type dict in init_vault.py format

    Raises:
        MethodologyParseError: If required fields are missing
    """
    required_fields = ["description", "folder_hints", "properties", "validation", "icon"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise MethodologyParseError(
            f"Note type '{nt_name}' in '{methodology_name}' missing: {missing}"
        )

    # Validate properties structure
    props = config.get("properties", {})
    if "additional_required" not in props:
        raise MethodologyParseError(
            f"Note type '{nt_name}' in '{methodology_name}' missing properties.additional_required"
        )
    if "optional" not in props:
        raise MethodologyParseError(
            f"Note type '{nt_name}' in '{methodology_name}' missing properties.optional"
        )

    return {
        "description": config["description"],
        "folder_hints": config["folder_hints"],
        "properties": {
            "additional_required": props.get("additional_required", []),
            "optional": props.get("optional", []),
        },
        "validation": config.get("validation", {}),
        "icon": config.get("icon", "file"),
    }


def load_all_methodologies(use_cache: bool = True) -> dict[str, dict[str, Any]]:
    """
    Load all available methodology configurations.

    Args:
        use_cache: Whether to use cached results if available

    Returns:
        Dictionary mapping methodology names to their configurations

    Example:
        >>> all_methods = load_all_methodologies()
        >>> print(list(all_methods.keys()))
        ['lyt-ace', 'minimal', 'para', 'zettelkasten']
    """
    result = {}
    for name in get_methodology_names():
        try:
            result[name] = load_methodology(name, use_cache=use_cache)
        except (MethodologyNotFoundError, MethodologyParseError) as e:
            # Log warning but continue loading others
            print(f"Warning: Could not load methodology '{name}': {e}")
    return result


def clear_cache() -> None:
    """Clear the methodology cache."""
    _methodology_cache.clear()


def reload_methodology(name: str) -> dict[str, Any]:
    """
    Force reload a methodology from disk, bypassing cache.

    Args:
        name: Methodology name

    Returns:
        Reloaded methodology configuration
    """
    _methodology_cache.pop(name, None)
    return load_methodology(name, use_cache=False)


# Provide METHODOLOGIES as a lazy-loaded dict-like interface
class _MethodologiesProxy:
    """
    Proxy class that provides dict-like access to methodologies.

    This allows using `METHODOLOGIES["para"]` syntax while loading
    methodologies on demand from YAML files.
    """

    def __getitem__(self, key: str) -> dict[str, Any]:
        return load_methodology(key)

    def __contains__(self, key: str) -> bool:
        return key in get_methodology_names()

    def __iter__(self):
        return iter(get_methodology_names())

    def keys(self) -> list[str]:
        return get_methodology_names()

    def values(self) -> list[dict[str, Any]]:
        return [load_methodology(n) for n in get_methodology_names()]

    def items(self) -> list[tuple[str, dict[str, Any]]]:
        return [(n, load_methodology(n)) for n in get_methodology_names()]

    def get(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any] | None:
        try:
            return load_methodology(key)
        except MethodologyNotFoundError:
            return default


# Export a METHODOLOGIES object that can be used as drop-in replacement
METHODOLOGIES = _MethodologiesProxy()


if __name__ == "__main__":  # pragma: no cover
    # CLI for testing
    import sys

    if len(sys.argv) > 1:
        name = sys.argv[1]
        try:
            method = load_methodology(name)
            print(f"Methodology: {method['name']}")
            print(f"Description: {method['description']}")
            print(f"Folders: {method['folders']}")
            print(f"Core properties: {method['core_properties']}")
            print(f"Note types: {list(method['note_types'].keys())}")
        except (MethodologyNotFoundError, MethodologyParseError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Available methodologies:")
        for name in get_methodology_names():
            method = load_methodology(name)
            print(f"  {name}: {method['name']} - {method['description']}")
