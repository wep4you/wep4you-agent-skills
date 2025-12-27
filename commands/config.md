---
description: Manage Obsidian vault configuration (settings.yaml)
argument-hint: [set|edit|diff|reset] [key value]
allowed-tools: Bash(uv run:*)
---

# Config Management

Manage the Obsidian vault settings file (.claude/settings.yaml).

## Execution

Run the config management tool:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --show
```

## Commands

### Set Value
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --set <key> <value>
```
Set a specific configuration value. Supports nested keys with dot notation.
Creates a backup before modifying.

Examples:
- `--set validation.strict_types false`
- `--set methodology para`

### Edit Config
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --edit
```
Open the settings file in your default editor ($EDITOR).
Creates a backup before editing.

### Show Diff
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --diff
```
Show differences between current settings and defaults.

### Reset Settings
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --reset <methodology>
```
Reset settings to a specific methodology (lyt-ace, para, zettelkasten, minimal, custom).
Creates a backup before resetting.

Examples:
- `--reset para --yes` (reset to PARA without confirmation)
- `--reset list` (show available methodologies)

## Configuration File

Location: `.claude/settings.yaml` (in vault root)

The settings file controls:
- Methodology and folder structure
- Core properties required in all notes
- Note type definitions
- Validation rules
- Excluded paths and files

## Backups

All destructive operations (edit, set, reset) automatically create timestamped backups in:
`.claude/backups/`

## Examples

Set a validation rule:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --set validation.strict_types false
```

Compare your settings with defaults:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --diff
```

Reset to PARA methodology:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --reset para --yes
```
