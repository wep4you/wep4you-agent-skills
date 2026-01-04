---
name: obsidian:templates
description: Manage Obsidian note templates with Templater support
argument-hint: [list|show|create|edit|delete|apply] [name]
allowed-tools: Bash(uv run:*)
---

# obsidian:templates - Template Management

Manage note templates with support for Templater plugin.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . [subcommand]
```

## Subcommands

### List Templates (default)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault .
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . list
```
Display all available templates from both plugin and vault.

Output formats: `--format text|json`

### Show Template Content
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . show <name>
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . show map/basic
```
Display template content for review.

### Create Template
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . create <name>
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . create meeting --content "---\ntype: meeting\n---"
```
Create a new template in the vault's templates directory.

### Edit Template
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . edit <name>
```
Open template in system editor ($EDITOR).

### Delete Template
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . delete <name>
```
Delete a vault template. Plugin templates cannot be deleted.

### Apply Template
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . apply <template> <file>
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . apply map/basic Atlas/Maps/NewNote.md --var title=MyNote
```
Apply template to create a new note with variable substitution.

## Built-in Templates

| Name | Type | Description |
|------|------|-------------|
| `map/basic` | map | Map of Content template |
| `map/templater` | map | Map with Templater syntax |
| `dot/basic` | dot | Atomic note template |
| `source/basic` | source | Reference note template |

## Variable Substitution

### Built-in Variables
- `{{date}}` - Current date (YYYY-MM-DD)
- `{{time}}` - Current time (HH:MM)
- `{{datetime}}` - Date and time
- `{{title}}` - File name (without extension)

### Custom Variables
Pass with `--var key=value`:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . apply map/basic Note.md \
  --var up="Parent Note" \
  --var collection="My Collection"
```

## Templater Support

If Templater plugin is installed, these patterns are processed:
- `<% tp.date.now() %>` - Current date
- `<% tp.date.tomorrow() %>` - Tomorrow's date
- `<% tp.file.title %>` - File title

## Template Locations

Templates are loaded from:
1. **Plugin templates**: `skills/templates/templates/` (read-only)
2. **Vault templates**: `.obsidian/templates/`, `Templates/`, or `templates/` (editable)

## Examples

List all templates as JSON:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . list --format json
```

Create a new meeting template:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . create meeting
```

Apply template with variables:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/templates/scripts/templates_command.py" --vault . apply dot/basic Atlas/Dots/Concept.md --var title="New Concept" --var up="Index"
```
