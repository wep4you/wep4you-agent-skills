---
name: templates
version: "1.0.0"
license: MIT
description: "Template management system for Obsidian vaults. Use when the user wants to (1) list available note templates, (2) create new templates, (3) apply templates to notes, (4) manage template variables, or (5) work with Templater plugin syntax. Triggers on keywords like template, create note from template, list templates, apply template, template variables."
---

# Obsidian Templates

Manage note templates with support for Templater plugin and simple variable substitution.

## Slash Commands (v1.0.0)

| Command | Description |
|---------|-------------|
| `obsidian:templates` | List all templates |
| `obsidian:templates list` | List all templates (explicit) |
| `obsidian:templates show <name>` | Show template content |
| `obsidian:templates create <name>` | Create new template |
| `obsidian:templates edit <name>` | Edit template in editor |
| `obsidian:templates delete <name>` | Delete template |
| `obsidian:templates apply <template> <file>` | Apply template to file |

## Quick Start

```bash
# List all available templates
uv run templates_command.py --vault .

# Show template content
uv run templates_command.py --vault . show map/basic

# Create new template
uv run templates_command.py --vault . create my-template

# Apply template to file
uv run templates_command.py --vault . apply map/basic "Atlas/Maps/New Map.md" --var up="Home" --var title="New Map"
```

## Features

### Template Discovery

The skill automatically discovers templates from multiple locations:

1. **Plugin Templates**: Pre-built templates in `templates/<type>/`
   - `map/basic.md` - Map of Content template
   - `dot/basic.md` - Atomic note template
   - `source/basic.md` - Source note template
   - `map/templater.md` - Map with Templater syntax

2. **Vault Templates**: Custom templates in your vault
   - `.obsidian/templates/`
   - `Templates/`
   - `templates/`

### Templater Support

The skill automatically detects if Templater plugin is installed:

```markdown
✅ Detects: .obsidian/plugins/templater-obsidian/
```

**Templater Syntax Supported:**
- `<% tp.date.now("YYYY-MM-DD") %>` - Current date
- `<% tp.date.tomorrow() %>` - Tomorrow's date
- `<% tp.file.title %>` - File name

**Fallback Syntax:**
- `{{date}}` - Current date (YYYY-MM-DD)
- `{{time}}` - Current time (HH:MM)
- `{{datetime}}` - Date and time
- `{{title}}` - File name
- `{{up}}` - Parent note (custom variable)
- Any custom variable via `--var key=value`

## Commands

### List Templates

```bash
uv run skills/templates/scripts/templates.py --list
```

Output:
```
Name                           Type            Source
============================================================
dot/basic                      dot             plugin
map/basic                      map             plugin
map/templater                  map             plugin
source/basic                   source          plugin
my-custom                      custom          vault

Total: 5 templates
Templater: ✅ installed
```

### Show Template

```bash
uv run skills/templates/scripts/templates.py --show map/basic
```

### Create Template

```bash
# Create with default content
uv run skills/templates/scripts/templates.py --create my-template

# Create with custom content
uv run skills/templates/scripts/templates.py --create my-template --content "# {{title}}"
```

### Edit Template

```bash
uv run skills/templates/scripts/templates.py --edit my-template
```

Opens template in `$EDITOR` (default: vim)

### Delete Template

```bash
uv run skills/templates/scripts/templates.py --delete my-template
```

**Note:** Only vault templates can be deleted (not plugin templates)

### Apply Template

```bash
# Basic usage
uv run skills/templates/scripts/templates.py --apply map/basic "New Map.md"

# With variables
uv run skills/templates/scripts/templates.py --apply map/basic "Atlas/Maps/PKM.md" \
  --var up="Home" \
  --var title="PKM System"

# Source template with metadata
uv run skills/templates/scripts/templates.py --apply source/basic "Sources/Article.md" \
  --var up="Sources" \
  --var author="John Doe" \
  --var url="https://example.com"
```

## Template Variables

### Built-in Variables

| Variable | Value | Example |
|----------|-------|---------|
| `{{date}}` | Current date | 2025-01-15 |
| `{{time}}` | Current time | 14:30 |
| `{{datetime}}` | Date and time | 2025-01-15 14:30 |
| `{{title}}` | File name (without .md) | My Note |

### Custom Variables

Pass custom variables with `--var`:

```bash
--var up="Parent Note" \
--var collection="My Collection" \
--var author="Jane Smith"
```

## Example Templates

### Map of Content (map/basic.md)

```markdown
---
type: map
up: "[[{{up}}]]"
created: {{date}}
daily: "[[{{date}}]]"
collection:
related: []
---

# {{title}}

## Overview


## Links


## Notes
```

### Atomic Note (dot/basic.md)

```markdown
---
type: dot
up: "[[{{up}}]]"
created: {{date}}
daily: "[[{{date}}]]"
collection:
related: []
---

# {{title}}

## Context


## Key Points


## Connections
```

### Source Note (source/basic.md)

```markdown
---
type: source
up: "[[{{up}}]]"
created: {{date}}
daily: "[[{{date}}]]"
collection:
related: []
author: {{author}}
url: {{url}}
---

# {{title}}

## Summary


## Key Takeaways


## Quotes


## Notes
```

## Integration with Claude Code

When user requests template operations:

1. **List templates**: Show available templates from plugin and vault
2. **Apply template**: Substitute variables and create note
3. **Create template**: Add to vault templates directory
4. **Detect Templater**: Check plugin status and use appropriate syntax

### Example Workflow

```
User: "Create a new map note called 'PKM System' under Home"

1. Check available templates (--list)
2. Apply map/basic template
3. Substitute variables: up="Home", title="PKM System"
4. Create file in appropriate location
```

## Configuration

Templates are discovered automatically. No configuration needed.

### Custom Template Location

To use custom vault templates:

1. Create directory: `.obsidian/templates/` or `Templates/`
2. Add `.md` files
3. Templates appear in `--list` with source="vault"

## Templater Plugin Integration

If Templater is installed (`.obsidian/plugins/templater-obsidian/`):

- Skill shows "✅ Templater installed" in `--list`
- Supports Templater syntax in templates
- Falls back to simple `{{variable}}` syntax if not installed

### Supported Templater Functions

- `tp.date.now()` - Current date
- `tp.date.tomorrow()` - Tomorrow
- `tp.file.title` - File name

Other Templater functions will be passed through as-is.

## Exit Codes

- `0`: Success
- `1`: Error (template not found, creation failed, etc.)
