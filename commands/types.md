---
name: obsidian:types
description: "Manage Obsidian note type definitions. CRITICAL: When user provides --config, pass it EXACTLY to the script."
argument-hint: [list|show|add|edit|remove|wizard] [name] [--config '{...}']
allowed-tools: Bash(uv run:*)
---

# obsidian:types - Note Type Management

Manage note type definitions for your Obsidian vault.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . [subcommand]
```

## Subcommands

### List Note Types (default)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault .
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . list
```
Display all configured note types with their properties.

Output formats: `--format text|json`

### Show Note Type Details
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . show <name>
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . show map --format json
```
Show detailed configuration for a specific note type.

### Add Note Type
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . add <name> --config '{"folder": "Folder/", "description": "..."}'
```

**CRITICAL**: Pass `--config` EXACTLY as provided by the user!

Example:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . add meeting --config '{"description": "Meeting notes", "folder": "Meetings/", "required_props": ["attendees", "date"], "icon": "calendar"}'
```

### Edit Note Type
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . edit <name> --config '{"description": "Updated"}'
```

Only the fields in the config JSON will be updated.

### Remove Note Type
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . remove <name> --yes
```
Use `--yes` to skip confirmation.

### Interactive Wizard
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . wizard
```
Guided experience for creating a new note type.

## Config JSON Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Note type description |
| `folder` | string | Folder path (e.g., "Meetings/") |
| `required_props` | array | Additional required properties |
| `optional_props` | array | Optional properties |
| `icon` | string | Lucide icon name (e.g., "calendar") |
| `allow_empty_up` | boolean | Allow empty up links |

## Note Type Structure

Note types are stored in `.claude/settings.yaml`:

```yaml
note_types:
  project:
    description: Active projects
    folder_hints: [Efforts/Projects/, Projects/]
    properties:
      additional_required: [status]
      optional: [deadline]
    validation:
      allow_empty_up: false
    icon: target
    template: x/templates/project.md
```

## Methodology-Based Defaults

Default note types depend on your chosen methodology:

| Methodology | Note Types |
|-------------|-----------|
| **LYT-ACE** | map, dot, source, project, area, daily |
| **PARA** | project, area, resource, archive |
| **Zettelkasten** | fleeting, literature, permanent, hub |
| **Minimal** | note |

## Examples

List all types as JSON:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . list --format json
```

Add a meeting type:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . add meeting --config '{"folder": "Meetings/", "required_props": ["attendees"], "icon": "users"}'
```

Update project description:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/types_command.py" --vault . edit project --config '{"description": "Currently active projects"}'
```

## Deprecated Command

This command replaces `/note-types` which is deprecated.

Old -> New mapping:
- `--list` -> `list`
- `--show <name>` -> `show <name>`
- `--add <name>` -> `add <name>`
- `--edit <name>` -> `edit <name>`
- `--remove <name>` -> `remove <name>`
- `--wizard` -> `wizard`
