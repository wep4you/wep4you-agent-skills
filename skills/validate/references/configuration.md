# Vault Validator Configuration Guide

This document explains all configuration options for the vault-validator skill.

## Configuration Files

The skill includes two pre-built configuration templates:

| File | Description | Use Case |
|------|-------------|----------|
| `config/default.yaml` | Full configuration with ACE/LYT settings | Linking Your Thinking users |
| `config/minimal.yaml` | Minimal starter configuration | Any Obsidian vault |

## Using a Configuration

### Option 1: Copy to Your Vault (Recommended)

```bash
# Copy the config template to your vault
cp config/default.yaml ~/YourVault/.claude/config/validator.yaml

# Edit to customize for your vault
vim ~/YourVault/.claude/config/validator.yaml
```

### Option 2: Pass Config Path

```bash
uv run scripts/validator.py --config config/minimal.yaml ~/YourVault
```

## Configuration Options

### `required_properties`

List of frontmatter properties that must exist in every note.

```yaml
required_properties:
  - type
  - up
  - created
  - daily
  - collection
  - related
```

### `valid_types`

List of valid values for the `type` property.

```yaml
valid_types:
  - Dot          # Atomic notes
  - Map          # Maps of Content
  - Daily        # Daily notes
  - Monthly      # Monthly notes
  - Yearly       # Yearly notes
  - Project      # Active projects
  - Task         # Individual tasks
  - Person       # Contact notes
```

### `exclude_paths`

Directories to skip during validation. Uses glob patterns.

```yaml
exclude_paths:
  - +/                # Inbox folder
  - x/                # System files (templates, scripts)
  - .obsidian/        # Obsidian config
  - .claude/          # Claude Code config
```

### `auto_fix`

Enable/disable automatic fixes.

```yaml
auto_fix:
  title_removal: true      # Remove deprecated title: property
  date_mismatch: true      # Fix created/daily date mismatches
  empty_type: true         # Add type: property when missing
  quoted_wikilinks: true   # Quote wikilinks in YAML
```

### `folders`

Folder-to-type mappings for auto-detection.

```yaml
folders:
  Dots:
    path: "Atlas/Dots"
    default_type: "Dot"
  Maps:
    path: "Atlas/Maps"
    default_type: "Map"
```

## Customization Examples

### Minimal Configuration

For a basic vault without specific structure:

```yaml
required_properties:
  - type
  - created

valid_types:
  - note
  - reference
  - project

exclude_paths:
  - templates/
  - .obsidian/
```

### PARA System

For vaults using the PARA methodology:

```yaml
required_properties:
  - type
  - status
  - created

valid_types:
  - project
  - area
  - resource
  - archive

folders:
  projects:
    path: "Projects"
    default_type: "project"
  areas:
    path: "Areas"
    default_type: "area"
  resources:
    path: "Resources"
    default_type: "resource"
```

### Zettelkasten

For slip-box style vaults:

```yaml
required_properties:
  - type
  - created
  - keywords

valid_types:
  - permanent
  - literature
  - fleeting
  - index

auto_fix:
  title_removal: true
```

## See Also

- [SKILL.md](../SKILL.md) - Skill overview and usage
- [README.md](../README.md) - Installation and quick start
