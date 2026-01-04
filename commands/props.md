---
name: obsidian:props
description: Manage frontmatter properties for Obsidian notes
argument-hint: [core|type|required|types] [name]
allowed-tools: Bash(uv run:*)
---

# obsidian:props - Property Management

Manage core and type-specific frontmatter properties.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . [subcommand]
```

## Subcommands

### List Core Properties (default)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault .
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . core
```
Display all core properties with their types and requirements.

Output formats: `--format text|json`

### Add Core Property
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . core add <name>
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . core add author --type string
```
Add a new core property that will be included in all notes.

### Remove Core Property
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . core remove <name>
```
Remove a core property. Essential properties (`type`, `created`) cannot be removed.

### Type-Specific Properties
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . type <name>
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . type project --format json
```
Show all properties for a specific note type (core + type-specific).

### Required Properties
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . required
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . required --type project
```
List all required properties. Use `--type` to filter by note type.

### All Types Properties
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . types
```
List all note types with their additional properties.

## Default Core Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | Note type classification |
| `up` | wikilink | No | Parent note in hierarchy |
| `created` | date | Yes | Creation date (YYYY-MM-DD) |
| `daily` | wikilink | No | Associated daily note |
| `tags` | list | No | Topic tags |
| `collection` | wikilink | No | Collection link |
| `related` | list[wikilink] | No | Related notes |

## Property Types

- `string` - Text value
- `date` - Date in YYYY-MM-DD format
- `wikilink` - Obsidian link `[[Note]]`
- `list[string]` - List of text values
- `list[wikilink]` - List of links

## Examples

Get core properties as JSON:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . core --format json
```

Check what's required for a project note:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . type project
```

Add a custom core property:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/frontmatter/scripts/props_command.py" --vault . core add source --type wikilink
```

## Deprecated Command

This command replaces `/frontmatter` which is deprecated.

Old -> New mapping:
- `list-core` -> `core`
- `add-core` -> `core add`
- `remove-core` -> `core remove`
- `list-type <type>` -> `type <name>`
- `get-required` -> `required`
