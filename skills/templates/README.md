# Templates Skill

Template management system for Obsidian vaults with Templater plugin support.

## Overview

This skill provides comprehensive template management for Obsidian notes:

- **CRUD Operations**: Create, read, update, delete templates
- **Template Discovery**: Automatically finds plugin and vault templates
- **Templater Support**: Auto-detects Templater plugin and supports its syntax
- **Variable Substitution**: Simple `{{variable}}` or Templater `<% tp.* %>` syntax
- **Multiple Sources**: Plugin defaults + vault-specific templates

## Quick Start

```bash
# List all templates
uv run skills/templates/scripts/templates.py --list

# Apply template
uv run skills/templates/scripts/templates.py --apply map/basic "New Note.md"

# Create custom template
uv run skills/templates/scripts/templates.py --create my-template
```

## Features

### Template Locations

1. **Plugin Templates** (`templates/<type>/`):
   - `map/basic.md` - Map of Content
   - `dot/basic.md` - Atomic notes
   - `source/basic.md` - Source notes
   - `map/templater.md` - Templater syntax example

2. **Vault Templates**:
   - `.obsidian/templates/`
   - `Templates/`
   - Auto-discovered

### Templater Detection

Automatically detects if Templater plugin is installed:

```
.obsidian/plugins/templater-obsidian/ → ✅ Templater installed
```

### Variable Syntax

**Simple Variables:**
```markdown
{{date}}      → 2025-01-15
{{time}}      → 14:30
{{title}}     → Note Title
{{up}}        → Parent (custom)
```

**Templater Syntax (if installed):**
```markdown
<% tp.date.now("YYYY-MM-DD") %>  → 2025-01-15
<% tp.file.title %>              → Note Title
```

## Commands

| Command | Description |
|---------|-------------|
| `--list` | List all available templates |
| `--show <name>` | Display template content |
| `--create <name>` | Create new template |
| `--edit <name>` | Edit template in $EDITOR |
| `--delete <name>` | Delete template (vault only) |
| `--apply <name> <file>` | Apply template with variables |

## Example Usage

### List Templates

```bash
$ uv run skills/templates/scripts/templates.py --list

Name                           Type            Source
============================================================
dot/basic                      dot             plugin
map/basic                      map             plugin
map/templater                  map             plugin
source/basic                   source          plugin

Total: 4 templates
Templater: ❌ not found
```

### Apply Template with Variables

```bash
uv run skills/templates/scripts/templates.py --apply map/basic "Atlas/Maps/PKM.md" \
  --var up="Home" \
  --var title="PKM System"
```

Creates:
```markdown
---
type: map
up: "[[Home]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection:
related: []
---

# PKM System

## Overview
...
```

### Create Custom Template

```bash
uv run skills/templates/scripts/templates.py --create meeting-notes \
  --content "# Meeting {{title}}

Date: {{date}}
Attendees: {{attendees}}

## Notes
"
```

## Template Structure

Templates should include proper frontmatter and variable placeholders:

```markdown
---
type: {{type}}
up: "[[{{up}}]]"
created: {{date}}
daily: "[[{{date}}]]"
collection:
related: []
---

# {{title}}

Your content here...
```

## Integration with Claude Code

The skill integrates seamlessly with Claude Code workflows:

1. **Note Creation**: "Create a new map note from template"
2. **Template Management**: "Show me all available templates"
3. **Custom Templates**: "Create a template for meeting notes"
4. **Variable Substitution**: Automatically prompts for required variables

## Built-in Templates

### Map of Content (map/basic.md)

For high-level topic organization with links to related notes.

### Atomic Note (dot/basic.md)

For single-concept notes with context and connections.

### Source Note (source/basic.md)

For capturing information from external sources (articles, books, etc.).

### Templater Example (map/templater.md)

Demonstrates Templater plugin syntax for dynamic content.

## Requirements

- Python 3.10+
- PyYAML 6.0+
- uv (for script execution)

## Optional

- Templater plugin (for advanced templating features)

## See Also

- [SKILL.md](SKILL.md) - Complete skill documentation
- [validate skill](../validate/) - Vault validation and auto-fix
- [Templater Plugin](https://github.com/SilentVoid13/Templater) - Advanced templating

## License

MIT
