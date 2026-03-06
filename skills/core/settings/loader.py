"""
Settings loader for Obsidian vault configuration.

Provides functions to load, save, and manage settings from .claude/settings.yaml.
This is the core loading mechanism used across all skills.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from skills.core.models.note_type import NoteTypeConfig
from skills.core.models.settings import Settings, ValidationRules

if TYPE_CHECKING:
    pass

SETTINGS_FILE = ".claude/settings.yaml"
TEMPLATE_FILE = Path(__file__).parent.parent.parent / "config" / "templates" / "settings.yaml"


def load_settings(vault_path: Path, create_if_missing: bool = False) -> Settings:
    """Load settings from .claude/settings.yaml.

    Args:
        vault_path: Path to Obsidian vault root
        create_if_missing: If True, create default settings.yaml if not found

    Returns:
        Settings object with all configuration

    Raises:
        FileNotFoundError: If settings.yaml doesn't exist and create_if_missing is False
        ValueError: If settings.yaml is invalid or vault_path is not a directory
    """
    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")
    if not vault_path.is_dir():
        raise ValueError(f"Vault path is not a directory: {vault_path}")

    settings_path = vault_path / SETTINGS_FILE

    if not settings_path.exists():
        if create_if_missing:
            create_default_settings(vault_path)
        else:
            raise FileNotFoundError(
                f"Settings file not found: {settings_path}\n"
                "Run 'init' skill to create settings or use create_if_missing=True"
            )

    try:
        with settings_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in settings file: {e}") from e

    if not raw:
        raise ValueError(f"Empty settings file: {settings_path}")

    return _parse_settings(raw)


def _parse_settings(raw: dict[str, Any]) -> Settings:
    """Parse raw YAML dict into Settings object."""
    # Handle both formats:
    # - Old: core_properties: [type, up, created, tags]
    # - New: core_properties: {all: [type, up, ...], mandatory: [...], optional: [...]}
    core_props_raw = raw.get("core_properties", [])
    if isinstance(core_props_raw, dict):
        # New format: use the 'all' key
        core_properties = core_props_raw.get("all", [])
    else:
        # Old format: direct list
        core_properties = core_props_raw

    # Parse note types with inheritance support
    note_types: dict[str, NoteTypeConfig] = {}
    for name, config in raw.get("note_types", {}).items():
        note_types[name] = NoteTypeConfig.from_dict(name, config, core_properties)

    # Parse validation rules
    val_raw = raw.get("validation", {})
    validation = ValidationRules.from_dict(val_raw)

    # Parse exclusions
    exclude = raw.get("exclude", {})

    return Settings(
        version=raw.get("version", "1.0"),
        methodology=raw.get("methodology", "custom"),
        core_properties=core_properties,
        note_types=note_types,
        validation=validation,
        folder_structure=raw.get("folder_structure", {}),
        up_links=raw.get("up_links", {}),
        exclude_paths=exclude.get("paths", []),
        exclude_files=exclude.get("files", []),
        exclude_patterns=exclude.get("patterns", []),
        formats=raw.get("formats", {}),
        logging=raw.get("logging", {}),
        raw=raw,
    )


def save_settings(vault_path: Path, settings: Settings) -> Path:
    """Save settings to .claude/settings.yaml.

    Args:
        vault_path: Path to Obsidian vault root
        settings: Settings object to save

    Returns:
        Path to the saved settings file
    """
    settings_path = vault_path / SETTINGS_FILE
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    with settings_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(settings.raw, f, default_flow_style=False, sort_keys=False, indent=2)

    return settings_path


def create_default_settings(vault_path: Path, methodology: str = "lyt-ace") -> Path:
    """Create default settings.yaml in vault.

    Args:
        vault_path: Path to vault root
        methodology: Methodology template to use

    Returns:
        Path to created settings file
    """
    settings_dir = vault_path / ".claude"
    settings_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = settings_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    settings_path = settings_dir / "settings.yaml"

    if TEMPLATE_FILE.exists():
        shutil.copy(TEMPLATE_FILE, settings_path)
        # Update methodology if different from default
        if methodology != "lyt-ace":
            with settings_path.open("r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace('methodology: "lyt-ace"', f'methodology: "{methodology}"')
            with settings_path.open("w", encoding="utf-8") as f:
                f.write(content)
    else:
        # Fallback: create minimal settings
        minimal = {
            "version": "1.0",
            "methodology": methodology,
            "core_properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
            "note_types": {},
            "validation": {"require_core_properties": True},
            "exclude": {"paths": ["+/", "x/", ".obsidian/", ".claude/", ".git/"]},
        }
        with settings_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(minimal, f, default_flow_style=False, sort_keys=False)

    return settings_path


def settings_exist(vault_path: Path) -> bool:
    """Check if settings.yaml exists in vault."""
    return (vault_path / SETTINGS_FILE).exists()


def get_backup_dir(vault_path: Path) -> Path:
    """Get backup directory path."""
    return vault_path / ".claude" / "backups"


def create_backup(vault_path: Path) -> Path | None:
    """Create backup of current settings.yaml.

    Returns:
        Path to backup file, or None if no settings exist
    """
    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        return None

    backup_dir = get_backup_dir(vault_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"settings_{timestamp}.yaml"

    shutil.copy2(settings_path, backup_path)
    return backup_path


def set_setting(vault_path: Path, key: str, value: str, create_backup_file: bool = True) -> None:
    """Set a configuration value in settings.yaml.

    Args:
        vault_path: Path to vault root
        key: Dot-separated key path (e.g., "validation.strict_types")
        value: Value to set (auto-converted to bool/int if applicable)
        create_backup_file: Whether to create backup before modifying

    Raises:
        FileNotFoundError: If settings.yaml doesn't exist
        ValueError: If key path is invalid
    """
    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

    # Create backup before modifying
    if create_backup_file:
        create_backup(vault_path)

    # Load raw YAML
    with settings_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # Parse key path
    keys = key.split(".")
    if not keys:
        raise ValueError("Key cannot be empty")

    # Navigate to the right location
    current = config
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            raise ValueError(f"Cannot set nested key: {k} is not a dict")
        current = current[k]

    # Convert value to appropriate type
    final_key = keys[-1]
    if value.lower() in ("true", "false"):
        current[final_key] = value.lower() == "true"
    elif value.isdigit():
        current[final_key] = int(value)
    elif value.startswith("[") and value.endswith("]"):
        # Simple list parsing
        items = value[1:-1].split(",")
        current[final_key] = [item.strip().strip("'\"") for item in items if item.strip()]
    else:
        current[final_key] = value

    # Save
    with settings_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False, indent=2)


def get_default_settings_dict() -> dict[str, Any]:
    """Get default settings as a dictionary for comparison."""
    return {
        "version": "1.0",
        "methodology": "custom",
        "core_properties": ["type", "up", "created", "daily", "tags", "collection", "related"],
        "note_types": {},
        "validation": {
            "require_core_properties": True,
            "allow_empty_properties": ["tags", "collection", "related"],
            "strict_types": True,
            "check_templates": True,
            "check_up_links": True,
            "check_inbox_no_frontmatter": True,
        },
        "exclude": {
            "paths": ["+/", "x/", ".obsidian/", ".claude/", ".git/"],
            "files": ["Home.md", "README.md"],
            "patterns": ["_*_MOC.md"],
        },
    }


def diff_settings(vault_path: Path) -> list[str]:
    """Compare current settings with defaults.

    Returns:
        List of difference strings
    """
    settings_path = vault_path / SETTINGS_FILE
    if not settings_path.exists():
        return ["Settings file does not exist - using defaults"]

    with settings_path.open("r", encoding="utf-8") as f:
        current = yaml.safe_load(f) or {}

    default = get_default_settings_dict()
    return _diff_dicts(default, current, "")


def _diff_dicts(d1: dict[str, Any], d2: dict[str, Any], path: str = "") -> list[str]:
    """Recursively find differences between two dicts."""
    changes: list[str] = []

    all_keys = set(d1.keys()) | set(d2.keys())

    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key

        if key not in d2:
            changes.append(f"- {current_path}: REMOVED (was: {d1[key]})")
        elif key not in d1:
            changes.append(f"+ {current_path}: ADDED (value: {d2[key]})")
        else:
            v1, v2 = d1[key], d2[key]
            if isinstance(v1, dict) and isinstance(v2, dict):
                changes.extend(_diff_dicts(v1, v2, current_path))
            elif v1 != v2:
                changes.append(f"~ {current_path}: {v1} → {v2}")

    return changes
