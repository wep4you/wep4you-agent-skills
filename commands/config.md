---
description: Manage Obsidian vault configuration (settings.yaml)
argument-hint: [show|edit|validate|methodologies|create|diff]
allowed-tools: Bash(uv run:*)
---

# obsidian:config - Configuration Management

Unified configuration management for Obsidian vaults.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . [subcommand]
```

## Subcommands

### Show Configuration (default)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault .
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . show --verbose
```
Display current vault configuration. Use `--verbose` for full details.

Output formats: `--format text|json|yaml`

### Edit Settings
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . edit
```
Open settings.yaml in your default editor ($EDITOR).
Creates automatic backup before editing.

### Validate Configuration
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . validate
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . validate --format json
```
Check configuration structure for errors. Returns exit code 0 if valid.

### List Methodologies
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . methodologies
```
Show available PKM methodologies with descriptions:
- **lyt-ace**: Linking Your Thinking + ACE Framework
- **para**: Projects, Areas, Resources, Archives
- **zettelkasten**: Traditional slip-box method
- **minimal**: Simple starter configuration
- **custom**: Empty configuration

### Create Settings
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . create --methodology para
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . create --methodology lyt-ace --force
```
Create default settings.yaml with chosen methodology.
Use `--force` to overwrite existing settings (creates backup first).

### Show Diff
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . diff
```
Compare current settings with default values.

## Configuration File

**Location**: `.claude/settings.yaml` (in vault root)

The settings file controls:
- Methodology and folder structure
- Core properties required in all notes
- Note type definitions with folder hints
- Validation rules
- Excluded paths and files

## Backups

All destructive operations create timestamped backups in:
`.claude/backups/settings_YYYYMMDD_HHMMSS.yaml`

## Examples

Show configuration as JSON:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . show --format json
```

Validate and check for errors:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault . validate
```

Create new PARA vault:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/config_command.py" --vault ~/notes create --methodology para
```

## Deprecated Commands

The following commands are deprecated (use subcommands instead):
- `/config-show` -> `obsidian:config show`
- `/config-create` -> `obsidian:config create`
- `/config-validate` -> `obsidian:config validate`
- `/config-methodologies` -> `obsidian:config methodologies`
