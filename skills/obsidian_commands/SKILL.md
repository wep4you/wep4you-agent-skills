---
name: obsidian-commands
description: Unified command router for Obsidian CLI commands
version: "1.2.0"
author: Peter Weiss
license: MIT
---

# Obsidian Commands

Core infrastructure for the obsidian: command namespace. Provides:

- **Unified Command Router**: Routes all obsidian:* commands to their handlers
- **Backward Compatibility**: Normalizes command names

## Architecture

This module is the foundation for CLI restructuring in v1.0.0:

```
obsidian_commands/
├── __init__.py      # Package exports
├── router.py        # Command routing logic
└── SKILL.md         # This file
```

## Command Namespace

All commands use the `obsidian:` prefix:

| Command | Description | Subcommands |
|---------|-------------|-------------|
| `obsidian:init` | Initialize vault | - |
| `obsidian:config` | Configuration management | show, edit, validate, methodologies |
| `obsidian:types` | Note type management | list, show, add, edit, remove, wizard |
| `obsidian:props` | Property management | core, type, required, add, remove |
| `obsidian:templates` | Template management | list, show, create, edit, delete, apply |
| `obsidian:validate` | Vault validation | - |

## Usage

### Programmatic

```python
from obsidian_commands import route_command

# Route a command
exit_code = route_command("obsidian:config", ["show", "--vault", "/path"])
```

### CLI Testing

```bash
# List all commands
uv run skills/obsidian_commands/router.py --list
```

## Interactive Mode

### Terminal
Im Terminal werden Sie interaktiv durch die Optionen geführt.

### Claude Code / Non-Interactive
Bei Aufruf ohne Terminal (z.B. in Claude Code) wird JSON zurückgegeben:
```json
{
  "interactive_required": true,
  "action": "route",
  "config_schema": {...}
}
```

Verwenden Sie `--config='...'` oder `--yes` um direkt Werte zu übergeben.

## Integration

This module provides a unified entry point for command discovery and routing.
It does not replace the individual skill scripts but normalizes command handling.
