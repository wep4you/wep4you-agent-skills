# Note Types Manager

Manage Obsidian note type definitions for your vault. Define folders, required properties, and templates for different types of notes.

## Overview

The Note Types Manager helps you organize your Obsidian vault by defining structured note types. Each note type specifies:

- **Folder**: Where notes of this type should be stored
- **Properties**: Required frontmatter properties
- **Template**: (Optional) Template file for new notes

This ensures consistency across your vault and integrates with validation tools.

## Installation

This skill is part of the wep4you-agent-skills plugin. No additional installation needed.

## Quick Start

```bash
# View all note types
uv run skills/note-types/scripts/note_types.py --list

# Create a new note type using the wizard
uv run skills/note-types/scripts/note_types.py --wizard

# Show details for a specific type
uv run skills/note-types/scripts/note_types.py --show project
```

## Default Note Types

The manager comes with 5 built-in note types:

| Type | Folder | Properties | Purpose |
|------|--------|------------|---------|
| **map** | Atlas/Maps/ | type, up, related | MOC (Map of Content) notes |
| **dot** | Atlas/Dots/ | type, up | Atomic notes (Zettelkasten) |
| **source** | Atlas/Sources/ | type, author, url | External references |
| **project** | Efforts/Projects/ | type, status, due | Project management |
| **daily** | Calendar/Daily/ | type, daily | Daily journal notes |

## Usage

### List All Note Types

```bash
uv run skills/note-types/scripts/note_types.py --list
```

### Add New Note Type

Interactive mode (recommended):
```bash
uv run skills/note-types/scripts/note_types.py --wizard
```

Quick add with defaults:
```bash
uv run skills/note-types/scripts/note_types.py --add blog --non-interactive
```

### Edit Existing Type

```bash
uv run skills/note-types/scripts/note_types.py --edit project
```

### Remove Note Type

```bash
uv run skills/note-types/scripts/note_types.py --remove custom
```

### Show Type Details

```bash
uv run skills/note-types/scripts/note_types.py --show map
```

## Configuration

Note types are stored in `.claude/config/note-types.yaml`:

```yaml
note_types:
  blog:
    folder: Writing/Blog/
    properties:
      - type
      - up
      - published
      - tags
    template: templates/blog-post.md

  meeting:
    folder: Efforts/Meetings/
    properties:
      - type
      - up
      - date
      - attendees
```

## Examples

### Define a Book Notes Type

```bash
$ uv run skills/note-types/scripts/note_types.py --wizard

🧙 Note Type Wizard

Note type name: book
  Folder [Book/]: Atlas/Books/
  Properties (comma-separated) [type, up]: type, up, author, isbn, rating
  Template [none]: templates/book-review.md

✅ Create this note type? (Y/n): y
✅ Created note type 'book'
```

### Define a Client Project Type

```yaml
client:
  folder: Efforts/Clients/
  properties:
    - type
    - up
    - status
    - contact_name
    - contract_value
    - start_date
  template: templates/client-intake.md
```

## Integration

### With Vault Validator

Use note types for type inference in validation:

```yaml
# .claude/config/validator.yaml
type_rules:
  'Atlas/Books/': book
  'Writing/Blog/': blog
  'Efforts/Clients/': client
```

### With Templates

Reference templates in note type definitions:

```yaml
blog:
  folder: Writing/Blog/
  properties: [type, up, published]
  template: templates/blog-post.md
```

Template file (`templates/blog-post.md`):
```markdown
---
type: blog
up: "[[Blog Index]]"
published: false
tags: []
---

# {{title}}

## Summary

## Content
```

## CLI Reference

```
usage: note_types.py [-h] [--config CONFIG] [--list] [--show NAME]
                     [--add NAME] [--edit NAME] [--remove NAME]
                     [--wizard] [--non-interactive]

Manage Obsidian note types

options:
  -h, --help           Show help message
  --config CONFIG      Path to config file
  --list               List all note types
  --show NAME          Show details for a note type
  --add NAME           Add a new note type
  --edit NAME          Edit an existing note type
  --remove NAME        Remove a note type
  --wizard             Interactive wizard mode
  --non-interactive    Non-interactive mode for --add
```

## Best Practices

1. **Use Descriptive Names**: Choose clear, lowercase names (e.g., `meeting`, `book`, `client`)

2. **Consistent Folder Structure**: Use clear folder hierarchies
   - `Atlas/` for knowledge (maps, dots, sources)
   - `Efforts/` for work (projects, areas, clients)
   - `Calendar/` for time-based notes (daily, weekly)

3. **Minimal Required Properties**: Start with essential properties
   - Always include: `type`, `up`
   - Add specific properties as needed

4. **Template Integration**: Create templates for complex note types

5. **Version Control**: Commit `.claude/config/note-types.yaml` to git

## Troubleshooting

### Config Not Found

If no config file exists, default note types are used. Create one:

```bash
mkdir -p .claude/config
uv run skills/note-types/scripts/note_types.py --wizard
```

### Note Type Already Exists

Use `--edit` instead of `--add`:

```bash
uv run skills/note-types/scripts/note_types.py --edit project
```

### Custom Config Location

Specify a custom config path:

```bash
uv run skills/note-types/scripts/note_types.py --config my-config.yaml --list
```

## License

MIT - See LICENSE file for details

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## Support

- Issues: https://github.com/wep4you/wep4you-agent-skills/issues
- Documentation: [SKILL.md](SKILL.md)
