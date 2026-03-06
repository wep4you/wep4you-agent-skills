---
name: obsidian:help
description: Show help for all Obsidian commands or get detailed help for a specific command
argument-hint: [command] [subcommand] [--json]
allowed-tools: Bash(uv run:*)
---

# obsidian:help - Central Help System

Display help for all Obsidian vault management commands or get detailed information about a specific command.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py"
```

## Usage

### List All Commands

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py"
```

Shows overview of all available commands with descriptions.

### Get Command Details

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" init
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" config
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" types
```

Shows detailed help for a specific command including subcommands and examples.

### Get Subcommand Details

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" types add
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" config show
```

Shows detailed help for a specific subcommand.

### JSON Output

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" --json
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" types --json
```

Returns machine-readable JSON with command metadata.

## Options

| Option | Description |
|--------|-------------|
| `[command]` | Command name (init, config, types, props, templates, validate) |
| `[subcommand]` | Subcommand name (e.g., add, show, list) |
| `--json` | Output in JSON format for programmatic use |

## Available Commands

| Command | Description |
|---------|-------------|
| `obsidian:init` | Initialize Obsidian vault with PKM methodology |
| `obsidian:config` | Configuration management (show, edit, validate) |
| `obsidian:types` | Note type management (list, show, add, edit, remove) |
| `obsidian:props` | Property management (core, type, add, remove) |
| `obsidian:templates` | Template management (list, show, create, apply) |
| `obsidian:validate` | Vault validation and auto-fix |
| `obsidian:help` | This help system |

## Examples

List all commands:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py"
```

Get help for init:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" init
```

Get help for types add:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" types add
```

Get all commands as JSON:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/obsidian_commands/help_command.py" --json
```

## JSON Output Format

```json
{
  "commands": [
    {
      "name": "obsidian:init",
      "description": "Initialize Obsidian vault",
      "subcommands": [],
      "examples": ["obsidian:init /path/to/vault"]
    },
    {
      "name": "obsidian:types",
      "description": "Note type management",
      "subcommands": ["list", "show", "add", "edit", "remove", "wizard"],
      "examples": ["obsidian:types list", "obsidian:types add meeting"]
    }
  ]
}
```
