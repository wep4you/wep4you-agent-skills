---
description: Show vault settings from .claude/settings.yaml
argument-hint: [--type note-type]
allowed-tools: Bash(uv run:*)
---

# Show Vault Configuration

Display the current vault configuration from `.claude/settings.yaml`.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --show
```

If a specific note type is requested, add `--type <type>`:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --type $1
```

## Output

Shows:
- Version and methodology
- Core properties required in all notes
- Defined note types
- Validation rules

## Note Types

Available types: map, dot, source, effort, project, area, daily

Use `--type <name>` to show detailed configuration for a specific type.
