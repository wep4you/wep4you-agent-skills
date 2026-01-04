---
name: obsidian-commands
description: Unified command router and deprecation system for Obsidian CLI commands
version: "1.0.0"
author: Peter Weiss
license: MIT
---

# Obsidian Commands

Core infrastructure for the obsidian: command namespace. Provides:

- **Unified Command Router**: Routes all obsidian:* commands to their handlers
- **Deprecation Warnings**: Notifies users when using deprecated commands
- **Backward Compatibility**: Maps old commands to new equivalents

## Architecture

This module is the foundation for CLI restructuring in v1.0.0:

```
obsidian-commands/
├── __init__.py      # Package exports
├── deprecation.py   # Deprecation warning system
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

## Deprecated Commands

The following commands are deprecated and will be removed in v2.0.0:

| Old Command | Replacement |
|-------------|-------------|
| `/frontmatter` | `obsidian:props` |
| `/note-types` | `obsidian:types` |
| `/config-show` | `obsidian:config show` |
| `/config-create` | `obsidian:config create` |
| `/config-validate` | `obsidian:config validate` |
| `/config-methodologies` | `obsidian:config methodologies` |
| `--mode auto` | `--fix` |

## Usage

### Programmatic

```python
from obsidian_commands import route_command, check_deprecation

# Route a command
exit_code = route_command("obsidian:config", ["show", "--vault", "/path"])

# Check deprecation
if check_deprecation("frontmatter"):
    print("This command is deprecated!")
```

### CLI Testing

```bash
# List all commands
uv run skills/obsidian-commands/router.py --list

# Check if command is deprecated
uv run skills/obsidian-commands/deprecation.py --check frontmatter

# List deprecated commands
uv run skills/obsidian-commands/deprecation.py --list
```

## Integration

This module is imported by command handlers to ensure deprecation warnings
are shown consistently. It does not replace the individual skill scripts
but provides a unified entry point for command discovery and routing.
