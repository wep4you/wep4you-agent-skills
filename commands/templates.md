---
name: templates
description: Manage Obsidian note templates with Templater support
---

# Template Management

Manage note templates for your Obsidian vault.

## Usage

```bash
# List all templates
uv run skills/templates/scripts/templates.py --list

# Show template
uv run skills/templates/scripts/templates.py --show <name>

# Create template
uv run skills/templates/scripts/templates.py --create <name>

# Edit template
uv run skills/templates/scripts/templates.py --edit <name>

# Delete template
uv run skills/templates/scripts/templates.py --delete <name>

# Apply template
uv run skills/templates/scripts/templates.py --apply <template> <file> [--var key=value ...]
```

## Examples

### List Templates

```bash
uv run skills/templates/scripts/templates.py --list
```

### Show Template Content

```bash
uv run skills/templates/scripts/templates.py --show map/basic
```

### Apply Template

```bash
# Basic application
uv run skills/templates/scripts/templates.py --apply map/basic "New Map.md"

# With variables
uv run skills/templates/scripts/templates.py --apply map/basic "Atlas/Maps/PKM.md" \
  --var up="Home" \
  --var title="PKM System"
```

### Create Custom Template

```bash
uv run skills/templates/scripts/templates.py --create meeting-notes
```

## Available Templates

- `map/basic` - Map of Content template
- `dot/basic` - Atomic note template
- `source/basic` - Source note template
- `map/templater` - Templater syntax example

## Variable Substitution

### Built-in Variables

- `{{date}}` - Current date (YYYY-MM-DD)
- `{{time}}` - Current time (HH:MM)
- `{{datetime}}` - Date and time
- `{{title}}` - File name (without extension)

### Custom Variables

Pass with `--var key=value`:

```bash
--var up="Parent Note" \
--var collection="My Collection" \
--var author="Jane Smith"
```

## Templater Support

If Templater plugin is installed, supports:

- `<% tp.date.now() %>` - Current date
- `<% tp.file.title %>` - File name
- Other Templater syntax

## See Also

- `skills/templates/SKILL.md` - Complete documentation
- `skills/templates/README.md` - Overview and examples
