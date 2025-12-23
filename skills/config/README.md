# Config Loader Skill

Configuration loader and manager for Obsidian vault settings with hierarchical configuration merging and vault-specific overrides.

## Overview

The Config Loader skill provides a robust configuration management system for Obsidian vaults. It supports:

- **Hierarchical Configuration**: Merge default, skill, and vault-specific settings
- **Note Type Management**: Define and customize note types with folder hints
- **Frontmatter Defaults**: Template-based frontmatter for different note types
- **Validation**: Verify configuration structure and required fields
- **Type Safety**: Full type hints with MyPy strict compliance

## Quick Start

```bash
# Load and display vault configuration
uv run skills/config/scripts/config_loader.py --vault /path/to/vault --show

# Validate configuration
uv run skills/config/scripts/config_loader.py --vault . --validate

# Load custom config
uv run skills/config/scripts/config_loader.py --vault . --config custom.yaml --show
```

## Use Cases

Use this skill when you need to:

1. **Load vault configuration** - Get merged configuration for a vault
2. **Customize note types** - Define custom note types with properties
3. **Manage frontmatter defaults** - Set default frontmatter templates
4. **Merge configurations** - Combine multiple config sources
5. **Validate config structure** - Ensure configuration is valid
6. **Save custom settings** - Persist vault-specific overrides

## Configuration Files

### default.yaml

Core vault configuration:

```yaml
core_properties:
  - type
  - up
  - created
  - daily
  - collection
  - related

note_types:
  map:
    description: "Map of Content - Overview and navigation notes"
    folder_hints:
      - "Atlas/Maps/"
    properties:
      - type
      - up
      - created
      - daily
      - collection
      - related
```

### frontmatter-defaults.yaml

Default frontmatter templates:

```yaml
map:
  type: "map"
  up: "[[Home]]"
  created: ""
  daily: ""
  collection: ""
  related: ""
  description: ""

project:
  type: "project"
  up: "[[Projects]]"
  created: ""
  daily: ""
  collection: ""
  related: ""
  status: "active"
  deadline: ""
```

### note-types-defaults.yaml

Extended note type definitions with validation rules, aliases, icons, and property type definitions.

## Usage Examples

### Python API

```python
from pathlib import Path
from config_loader import load_config, save_config, merge_configs

# Load configuration
config = load_config(Path("/path/to/vault"))

# Get note type config
map_config = config["note_types"]["map"]
print(map_config["description"])

# Save custom configuration
custom = {
    "note_types": {
        "blog": {
            "description": "Blog posts",
            "properties": ["type", "up", "created", "published"]
        }
    }
}
save_config(Path("/path/to/vault"), custom, "blog.yaml")

# Merge configurations
merged = merge_configs(base_config, override_config)
```

### CLI

```bash
# Show loaded configuration
uv run scripts/config_loader.py --vault . --show

# Validate configuration
uv run scripts/config_loader.py --vault . --validate

# Load specific config file
uv run scripts/config_loader.py --vault . --config custom.yaml --show
```

## Configuration Hierarchy

Configurations are merged in this order (later overrides earlier):

1. **Embedded defaults** - DEFAULT_CONFIG in config_loader.py
2. **Skill defaults** - skills/config/config/{name}.yaml
3. **Vault overrides** - {vault}/.claude/config/{name}.yaml

This allows global defaults with vault-specific customization.

## Vault-Specific Overrides

To customize a vault's configuration:

1. Create `.claude/config/` directory in vault root
2. Add YAML file with overrides (e.g., `custom.yaml`)
3. Define only properties you want to change

Example `.claude/config/custom.yaml`:

```yaml
# Add custom note type
note_types:
  meeting:
    description: "Meeting notes"
    folder_hints:
      - "Meetings/"
    properties:
      - type
      - up
      - created
      - daily
      - attendees
      - agenda

# Override auto-fix settings
auto_fix:
  empty_types: false
  daily_links: true
```

## Note Types

Default note types included:

| Type | Description | Icon | Folder Hints |
|------|-------------|------|--------------|
| **map** | Map of Content - Overviews | 🗺️ | Atlas/Maps/, Maps/ |
| **dot** | Atomic concepts | ⚫ | Atlas/Dots/, Dots/ |
| **source** | External references | 📚 | Atlas/Sources/, Sources/ |
| **effort** | Work and tasks | 💪 | Efforts/ |
| **project** | Defined outcomes | 🎯 | Efforts/Projects/, Projects/ |
| **area** | Ongoing responsibilities | 🏠 | Efforts/Areas/, Areas/ |
| **daily** | Journal entries | 📅 | Calendar/daily/, daily/ |

## Core Properties

All notes require these 6 properties:

```yaml
type: dot           # Note type (required, non-empty)
up: "[[Parent]]"    # Parent link (required, quoted wikilink)
created: 2025-01-15 # Creation date (required, YYYY-MM-DD)
daily: "[[2025-01-15]]"  # Daily link (required, quoted)
collection:         # Collection (required, can be empty)
related:            # Related notes (required, can be empty)
```

## API Reference

### load_config(vault_path, config_name="default.yaml")

Load configuration with hierarchical merging.

**Returns:** Merged configuration dictionary

### save_config(vault_path, config, config_name="custom.yaml")

Save configuration to vault-specific location.

### merge_configs(base, override)

Deep merge two configuration dictionaries.

**Returns:** Merged configuration

### get_note_type_config(config, note_type)

Get configuration for specific note type.

**Returns:** Note type config dict or None

### infer_note_type(file_path, config)

Infer note type from file path using folder hints.

**Returns:** Inferred note type string or None

### validate_config(config)

Validate configuration structure and required fields.

**Returns:** List of validation errors (empty if valid)

## Integration

This skill integrates with:

- **validate skill** - Use config for validation rules
- **Claude Code** - Load vault settings for automation
- **Custom tools** - Extend with vault-specific note types

## Quality Standards

- Python 3.10+
- Type hints everywhere (MyPy strict)
- Ruff-compliant (100 char line length)
- 90%+ test coverage
- PEP 723 inline dependencies

## License

MIT License - See LICENSE file

## Contributing

See CONTRIBUTING.md for development setup and guidelines.
