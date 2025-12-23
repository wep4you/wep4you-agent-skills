---
description: Create or reset vault settings.yaml
argument-hint: [--reset methodology]
allowed-tools: Bash(uv run:*)
---

# Create Vault Configuration

Create a default `.claude/settings.yaml` if it doesn't exist, or reset to a different methodology.

## Execution

Create new settings (if none exist):
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --create --show
```

Reset to a different methodology:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --reset $1 --yes
```

**Note**: The `--yes` flag is required in non-interactive mode (Claude Code).
Before executing, always warn the user that this will overwrite existing settings.

## Arguments

- `--create` - Create default settings if missing (will NOT overwrite)
- `--reset <methodology>` - Reset settings to specified methodology (with confirmation)
- `--yes` - Skip confirmation prompt (use with caution!)

## Methodologies

Available methodologies for `--reset`:
- `lyt-ace` - Linking Your Thinking with ACE folder structure (default)
- `para` - Projects, Areas, Resources, Archives
- `zettelkasten` - Zettelkasten/slip-box method
- `minimal` - Minimal configuration
- `custom` - Empty custom configuration

## Examples

```bash
# Show available methodologies with descriptions
/obsidian:config-create --reset list

# Reset to PARA methodology
/obsidian:config-create --reset para

# Reset to Zettelkasten (skip confirmation)
/obsidian:config-create --reset zettelkasten --yes
```

## Created Files

- `.claude/settings.yaml` - Main configuration file
- `.claude/logs/` - Directory for JSONL validation logs

## Warning

Using `--reset` will **permanently overwrite** your existing settings.yaml!
A colored warning and confirmation prompt will appear before any changes are made.
