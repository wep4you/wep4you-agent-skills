---
description: Manage Obsidian vault validator configuration
argument-hint: [show|edit|set|reset|validate|diff] [key value]
allowed-tools: Bash(uv run:*)
---

# Config Management

Manage the Obsidian vault validator configuration file.

## Execution

Run the config management tool:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --show
```

## Commands

### Show Current Config
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --show
```
Display the current configuration in YAML format.

### Show Defaults
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --show-defaults
```
Display the default configuration template.

### Edit Config
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --edit
```
Open the configuration file in your default editor ($EDITOR).
Creates a backup before editing.

### Set Value
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --set <key> <value>
```
Set a specific configuration value. Supports nested keys with dot notation.

Examples:
- `--set auto_fix.empty_types false`
- `--set default_mode auto`
- `--set performance.max_workers 8`

### Reset to Defaults
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --reset
```
Reset configuration to default values. Creates a backup before resetting.

### Validate Config
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --validate
```
Validate the configuration file structure and required keys.

### Show Diff
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --diff
```
Show differences between current configuration and defaults.

## Configuration File

Location: `.claude/config/validator.yaml` (in vault root)

The configuration file controls validator behavior including:
- Auto-fix settings
- Excluded paths and files
- Type inference rules
- Report formatting
- Performance settings

## Backups

All destructive operations (edit, set, reset) automatically create timestamped backups in:
`.claude/config/backups/`

## Examples

Check current auto-fix settings:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --show | grep auto_fix
```

Disable auto-fixing of folder renames:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --set auto_fix.folder_renames false
```

Compare your config with defaults:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_cli.py" --diff
```
