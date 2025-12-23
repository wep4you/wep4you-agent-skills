---
name: config
license: MIT
description: "Configuration loader and manager for Obsidian vault settings. Use when the user wants to (1) load vault configuration, (2) customize note type definitions, (3) manage frontmatter defaults, (4) merge configuration files, (5) validate configuration structure, or (6) save custom vault settings. Triggers on keywords like load config, vault settings, note type config, frontmatter defaults, merge configs, validate configuration."
---

# Config Loader

Loads, manages, and merges YAML configuration files for Obsidian vault management with support for vault-specific overrides.

## Quick Start

```bash
# Load and show vault configuration
uv run scripts/config_loader.py --vault /path/to/vault --show

# Validate configuration structure
uv run scripts/config_loader.py --vault /path/to/vault --validate

# Load custom config file
uv run scripts/config_loader.py --vault /path/to/vault --config custom.yaml --show
```

## Features

- **Hierarchical Config Loading**: Merge default, skill, and vault-specific configurations
- **Type-Safe Operations**: Full type hints with MyPy strict compliance
- **Note Type Inference**: Automatically infer note types from folder paths
- **Configuration Validation**: Validate config structure and required fields
- **Vault Overrides**: Support for `.claude/config/` vault-specific settings

## Configuration Hierarchy

The config loader merges configurations in this order (later overrides earlier):

1. **DEFAULT_CONFIG** (embedded in script)
2. **Skill defaults** (`skills/config/config/{name}.yaml`)
3. **Vault overrides** (`.claude/config/{name}.yaml` in vault)

## Usage Examples

### Load Configuration

```python
from pathlib import Path
from config_loader import load_config

# Load default configuration
config = load_config(Path("/path/to/vault"))

# Load custom configuration
config = load_config(Path("/path/to/vault"), "custom.yaml")
```

### Save Custom Configuration

```python
from pathlib import Path
from config_loader import save_config

custom_config = {
    "core_properties": ["type", "up", "created"],
    "note_types": {
        "custom": {
            "description": "Custom note type",
            "properties": ["type", "up"]
        }
    }
}

save_config(Path("/path/to/vault"), custom_config, "custom.yaml")
```

### Merge Configurations

```python
from config_loader import merge_configs

base = {
    "core_properties": ["type", "up"],
    "validation": {"strict": true}
}

override = {
    "core_properties": ["type", "up", "created"],
    "auto_fix": {"enabled": true}
}

merged = merge_configs(base, override)
# Result: All keys from both, override takes precedence for conflicts
```

### Get Note Type Configuration

```python
from config_loader import load_config, get_note_type_config

config = load_config(Path("/path/to/vault"))
map_config = get_note_type_config(config, "map")

print(map_config["description"])  # "Map of Content - Overview and navigation notes"
print(map_config["properties"])   # ["type", "up", "created", "daily", ...]
```

### Infer Note Type from Path

```python
from pathlib import Path
from config_loader import load_config, infer_note_type

config = load_config(Path("/vault"))
file_path = Path("/vault/Atlas/Maps/My Map.md")

note_type = infer_note_type(file_path, config)
print(note_type)  # "map"
```

### Validate Configuration

```python
from config_loader import load_config, validate_config

config = load_config(Path("/path/to/vault"))
errors = validate_config(config)

if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Configuration is valid")
```

## Configuration Files

### default.yaml

Core configuration with:
- `core_properties`: Required frontmatter properties for all notes
- `note_types`: Note type definitions with folder hints and properties
- `validation`: Validation rules
- `auto_fix`: Auto-fix toggles
- `exclude_paths`: Paths to exclude from processing
- `exclude_files`: Files to exclude from processing

### frontmatter-defaults.yaml

Default frontmatter templates for:
- New notes (minimal template)
- Each note type (map, dot, source, project, area, daily, effort)
- Date formats and link formats
- Default parent links by note type

### note-types-defaults.yaml

Extended note type configuration with:
- Detailed descriptions and aliases
- Icon assignments
- Required vs optional properties
- Type-specific validation rules
- Property type definitions with data types

## Note Types

The default configuration includes these note types:

| Type | Description | Folder Hints |
|------|-------------|--------------|
| **map** | Map of Content - Overview and navigation notes | `Atlas/Maps/`, `Maps/` |
| **dot** | Dot notes - Atomic concepts and ideas | `Atlas/Dots/`, `Dots/` |
| **source** | Source notes - External references | `Atlas/Sources/`, `Sources/` |
| **effort** | Effort notes - Work and tasks | `Efforts/` |
| **project** | Project notes - Defined outcomes | `Efforts/Projects/`, `Projects/` |
| **area** | Area notes - Ongoing responsibilities | `Efforts/Areas/`, `Areas/` |
| **daily** | Daily notes - Date-based journal entries | `Calendar/daily/`, `daily/` |

## Core Properties

All notes require these 6 properties (per vault standards):

```yaml
type: dot           # Note type
up: "[[Parent]]"    # Parent note link (quoted)
created: 2025-01-15 # Creation date (YYYY-MM-DD)
daily: "[[2025-01-15]]"  # Daily note link (quoted)
collection:         # Collection classification (can be empty)
related:            # Related notes (can be empty)
```

## Vault-Specific Overrides

To customize configuration for a specific vault:

1. Create `.claude/config/` directory in vault root
2. Add YAML file (e.g., `custom.yaml`)
3. Define only the properties you want to override

Example `.claude/config/custom.yaml`:

```yaml
# Override just the note types
note_types:
  blog:
    description: "Blog post notes"
    folder_hints:
      - "Blog/"
    properties:
      - type
      - up
      - created
      - daily
      - published
      - tags

# Keep all other defaults from skill config
```

## API Reference

### load_config(vault_path, config_name)

Load configuration with hierarchical merging.

**Parameters:**
- `vault_path` (Path): Path to Obsidian vault root
- `config_name` (str): Config file name (default: "default.yaml")

**Returns:** dict[str, Any] - Merged configuration

**Raises:**
- ValueError: If vault path invalid
- yaml.YAMLError: If YAML parsing fails

### save_config(vault_path, config, config_name)

Save configuration to vault-specific location.

**Parameters:**
- `vault_path` (Path): Path to vault root
- `config` (dict): Configuration to save
- `config_name` (str): Config file name (default: "custom.yaml")

**Raises:**
- ValueError: If vault path invalid
- OSError: If file cannot be written

### merge_configs(base, override)

Deep merge two configuration dictionaries.

**Parameters:**
- `base` (dict): Base configuration
- `override` (dict): Override configuration

**Returns:** dict[str, Any] - Merged configuration

### get_note_type_config(config, note_type)

Get configuration for specific note type.

**Parameters:**
- `config` (dict): Configuration dictionary
- `note_type` (str): Note type identifier

**Returns:** dict[str, Any] | None - Note type config or None

### infer_note_type(file_path, config)

Infer note type from file path using folder hints.

**Parameters:**
- `file_path` (Path): Path to markdown file
- `config` (dict): Configuration dictionary

**Returns:** str | None - Inferred note type or None

### validate_config(config)

Validate configuration structure.

**Parameters:**
- `config` (dict): Configuration to validate

**Returns:** list[str] - Validation errors (empty if valid)

## Integration with Claude Code

When user requests configuration management:

1. Determine vault path (usually current directory or user-specified)
2. Load configuration with appropriate hierarchy
3. Perform requested operation (load, save, merge, validate)
4. Report results and configuration details

## Exit Codes

- `0`: Success
- `1`: Error (invalid vault, YAML error, validation failed)

## Dependencies

- Python 3.10+
- PyYAML >= 6.0 (via PEP 723 inline dependencies)

## Quality Standards

- Type hints on all functions (MyPy strict)
- Ruff-compliant (100 char line length)
- Full docstrings with examples
- Error handling with descriptive messages
