# Migration Guide: v0.x → v1.0.0

This guide covers migrating from the v0.x command structure to the new v1.0.0 unified `obsidian:` namespace.

## Overview

Version 1.0.0 introduces a cleaner, more consistent command structure:

- All commands use the `obsidian:` prefix
- Related functionality is grouped under unified commands
- Simplified flags (e.g., `--fix` instead of `--mode auto`)

## Command Migration

### Configuration Commands

| Old Command | New Command |
|-------------|-------------|
| `/config-show` | `obsidian:config show` |
| `/config-create` | `obsidian:config create` |
| `/config-validate` | `obsidian:config validate` |
| `/config-methodologies` | `obsidian:config methodologies` |
| `/config` | `obsidian:config` |

**Example:**
```bash
# Old
uv run settings_loader.py --vault . --show

# New
uv run config_command.py --vault . show
```

### Note Type Commands

| Old Command | New Command |
|-------------|-------------|
| `/note-types --list` | `obsidian:types list` |
| `/note-types --show <name>` | `obsidian:types show <name>` |
| `/note-types --add <name>` | `obsidian:types add <name>` |
| `/note-types --edit <name>` | `obsidian:types edit <name>` |
| `/note-types --remove <name>` | `obsidian:types remove <name>` |
| `/note-types --wizard` | `obsidian:types wizard` |

**Example:**
```bash
# Old
uv run note_types.py --add meeting --config '{...}'

# New
uv run types_command.py --vault . add meeting --config '{...}'
```

### Property Commands

| Old Command | New Command |
|-------------|-------------|
| `/frontmatter list-core` | `obsidian:props core` |
| `/frontmatter add-core <name>` | `obsidian:props core add <name>` |
| `/frontmatter remove-core <name>` | `obsidian:props core remove <name>` |
| `/frontmatter list-type <type>` | `obsidian:props type <name>` |
| `/frontmatter get-required` | `obsidian:props required` |

**Example:**
```bash
# Old
uv run frontmatter.py list-core --format json

# New
uv run props_command.py --vault . core --format json
```

### Validation Commands

| Old Flag | New Flag |
|----------|----------|
| `--mode auto` | `--fix` |
| `--mode report` | (default, no flag) |

**Example:**
```bash
# Old
uv run validator.py --vault . --mode auto

# New
uv run validate_command.py --vault . --fix
```

**New feature - filter by type:**
```bash
uv run validate_command.py --vault . --type project --fix
```

### Template Commands

| Old Command | New Command |
|-------------|-------------|
| `--list` | `list` |
| `--show <name>` | `show <name>` |
| `--create <name>` | `create <name>` |
| `--edit <name>` | `edit <name>` |
| `--delete <name>` | `delete <name>` |
| `--apply <tpl> <file>` | `apply <tpl> <file>` |

**Example:**
```bash
# Old
uv run templates.py --list

# New
uv run templates_command.py --vault . list
```

## Deprecation Timeline

| Version | Status |
|---------|--------|
| v1.0.0 | Old commands work with deprecation warnings |
| v1.x | Both old and new commands supported |
| v2.0.0 | Old commands removed |

## Automatic Migration

When you use a deprecated command, you'll see a warning:

```
DEPRECATION WARNING
Command '/frontmatter' is deprecated and will be removed in v2.0.0.
Use 'obsidian:props' instead.
```

The command will still work during the deprecation period.

## Script Updates

If you have scripts using the old commands, update them:

```bash
# Before
#!/bin/bash
cd "$VAULT_PATH"
uv run skills/validate/scripts/validator.py --mode auto
uv run skills/note-types/scripts/note_types.py --list

# After
#!/bin/bash
cd "$VAULT_PATH"
uv run skills/validate/scripts/validate_command.py --fix
uv run skills/note-types/scripts/types_command.py list
```

## New Features in v1.0.0

### Type-filtered Validation
```bash
obsidian:validate --type project --fix
```

### Unified Config Management
```bash
obsidian:config show --verbose --format json
obsidian:config diff
```

### Improved Property Management
```bash
obsidian:props required --type project
obsidian:props types --format json
```

## Getting Help

List all available commands:
```bash
uv run skills/obsidian_commands/router.py --list
```

Check if a command is deprecated:
```bash
uv run skills/obsidian_commands/deprecation.py --check frontmatter
```

List all deprecated commands:
```bash
uv run skills/obsidian_commands/deprecation.py --list
```
