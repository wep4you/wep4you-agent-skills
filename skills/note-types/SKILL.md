---
name: note-types
version: "0.1.0"
license: MIT
description: "Manage Obsidian note type definitions including folders, properties, and templates. Use when the user wants to (1) define new note types, (2) manage note type configurations, (3) set up folder and property mappings, (4) create note type templates, or (5) view existing note types. Triggers on keywords like note types, note type config, manage note types, define note type, note type wizard."
---

# Obsidian Note Types Manager

Manage note type definitions for your Obsidian vault. Define folders, required properties, and templates for different types of notes.

## Slash Commands

| Command | Description |
|---------|-------------|
| `obsidian:note-types --list` | List all note types |
| `obsidian:note-types --show <name>` | Show details for a note type |
| `obsidian:note-types --add <name>` | Add a new note type |
| `obsidian:note-types --edit <name>` | Edit an existing note type |
| `obsidian:note-types --remove <name>` | Remove a note type |
| `obsidian:note-types --wizard` | Interactive wizard mode |

## Quick Start

```bash
# List all note types
uv run skills/note-types/scripts/note_types.py --list

# Show details for a specific type
uv run skills/note-types/scripts/note_types.py --show map

# Interactive wizard to create a new type
uv run skills/note-types/scripts/note_types.py --wizard

# Add a note type non-interactively
uv run skills/note-types/scripts/note_types.py --add blog --non-interactive
```

## Features

### CRUD Operations

- **List**: View all defined note types
- **Show**: Display details for a specific note type
- **Add**: Create a new note type (interactive or non-interactive)
- **Edit**: Modify an existing note type
- **Remove**: Delete a note type

### Interactive Wizard

The wizard mode guides you through creating a new note type:

1. Enter note type name
2. Define folder location
3. Specify required properties
4. Optional: assign a template

```bash
uv run skills/note-types/scripts/note_types.py --wizard
```

### Default Note Types

The following note types are included by default:

| Type | Folder | Properties |
|------|--------|------------|
| map | Atlas/Maps/ | type, up, related |
| dot | Atlas/Dots/ | type, up |
| source | Atlas/Sources/ | type, author, url |
| project | Efforts/Projects/ | type, status, due |
| daily | Calendar/Daily/ | type, daily |

## Configuration

### Config File Location

Note types are stored in: `.claude/config/note-types.yaml`

The manager will also check:
- `.obsidian/note-types.yaml`
- `~/.config/obsidian/note-types.yaml`

### Config Format

```yaml
note_types:
  map:
    folder: Atlas/Maps/
    properties:
      - type
      - up
      - related

  project:
    folder: Efforts/Projects/
    properties:
      - type
      - status
      - due
    template: templates/project.md

  custom:
    folder: Custom/Notes/
    properties:
      - type
      - up
      - category
      - tags
```

## Commands

### List All Note Types

```bash
uv run skills/note-types/scripts/note_types.py --list
```

Output:
```
📋 Note Types (5):

  daily
    Folder: Calendar/Daily/
    Properties: type, daily

  dot
    Folder: Atlas/Dots/
    Properties: type, up

  ...
```

### Show Note Type Details

```bash
uv run skills/note-types/scripts/note_types.py --show map
```

Output:
```
📄 Note Type: map

  Folder: Atlas/Maps/
  Properties: type, up, related
```

### Add Note Type (Interactive)

```bash
uv run skills/note-types/scripts/note_types.py --add blog
```

Prompts:
```
Define note type: blog
(Press Enter to keep current value or use default)

  Folder [Blog/]:
  Properties (comma-separated) [type, up]: type, up, author, published
  Template [none]: templates/blog-post.md
```

### Add Note Type (Non-Interactive)

```bash
uv run skills/note-types/scripts/note_types.py --add blog --non-interactive
```

Creates a note type with minimal defaults:
- Folder: `Blog/`
- Properties: `type, up`

### Edit Note Type

```bash
uv run skills/note-types/scripts/note_types.py --edit project
```

Shows current values and prompts for changes:
```
📝 Editing note type: project

📄 Note Type: project
  Folder: Efforts/Projects/
  Properties: type, status, due

Define note type: project
(Press Enter to keep current value or use default)

  Folder [Efforts/Projects/]:
  Properties (comma-separated) [type, status, due]: type, status, due, priority
  Template [none]: templates/project.md
```

### Remove Note Type

```bash
uv run skills/note-types/scripts/note_types.py --remove custom
```

Prompts for confirmation:
```
⚠️  Delete note type 'custom'? (y/N): y
✅ Removed note type 'custom'
```

### Wizard Mode

```bash
uv run skills/note-types/scripts/note_types.py --wizard
```

Interactive wizard:
```
🧙 Note Type Wizard

Let's create a new note type for your Obsidian vault.

Note type name: meeting
  Folder [Meeting/]: Efforts/Meetings/
  Properties (comma-separated) [type, up]: type, up, date, attendees
  Template [none]: templates/meeting-notes.md

📋 Summary:
  Name: meeting
  Folder: Efforts/Meetings/
  Properties: type, up, date, attendees
  Template: templates/meeting-notes.md

✅ Create this note type? (Y/n): y

✅ Created note type 'meeting'
```

## Integration with Vault Validator

Note types defined here can be used by the vault validator for type inference:

```yaml
# In .claude/config/validator.yaml
type_rules:
  'Atlas/Maps/': map
  'Efforts/Projects/': project
  'Efforts/Meetings/': meeting  # Custom type
```

## Use Cases

### Define Custom Content Types

Create note types for your specific workflow:
- Blog posts
- Meeting notes
- Book summaries
- Research papers
- Client projects

### Enforce Consistent Structure

Define required properties for each note type to maintain consistency:
```yaml
book:
  folder: Atlas/Books/
  properties:
    - type
    - author
    - isbn
    - rating
    - read_date
```

### Template Integration

Link note types to templates for quick note creation:
```yaml
client:
  folder: Efforts/Clients/
  properties:
    - type
    - up
    - status
    - contact
  template: templates/client-intake.md
```

## Exit Codes

- `0`: Success
- `1`: Error (note type not found, validation failed, etc.)

## Integration with Claude Code

When user requests note type management:

1. Determine the action (list, add, edit, remove)
2. Run the appropriate command
3. For complex setups, use wizard mode
4. Report results and next steps

Example workflow:
```
User: "I want to add a note type for meeting notes"
Claude: Uses wizard mode to interactively create the type
Result: New note type defined with proper folder and properties
```
