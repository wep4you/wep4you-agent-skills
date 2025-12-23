---
description: Manage Obsidian note type definitions
argument-hint: [--list|--show|--add|--edit|--remove|--wizard] [name]
allowed-tools: Bash(uv run:*)
---

# Obsidian Note Types Manager

Manage note type definitions for your Obsidian vault. Define folders, required properties, and templates for different types of notes.

## Execution

Run the note types manager script:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --list
```

## Commands

### List All Note Types

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --list
```

Shows all defined note types with their folders and properties.

### Show Note Type Details

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --show <name>
```

Display detailed information about a specific note type.

Example:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --show map
```

### Interactive Wizard

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --wizard
```

Launch the interactive wizard to create a new note type. The wizard will guide you through:
1. Entering the note type name
2. Defining the folder location
3. Specifying required properties
4. Optionally assigning a template

### Add Note Type

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --add <name>
```

Add a new note type interactively. For non-interactive mode:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --add <name> --non-interactive
```

Example:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --add blog
```

### Edit Note Type

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --edit <name>
```

Edit an existing note type. Shows current values and prompts for changes.

Example:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --edit project
```

### Remove Note Type

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --remove <name>
```

Remove a note type after confirmation.

Example:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --remove custom
```

## Arguments

- `--config <path>` - Path to custom config file
- `--list` - List all note types
- `--show <name>` - Show details for a note type
- `--add <name>` - Add a new note type
- `--edit <name>` - Edit an existing note type
- `--remove <name>` - Remove a note type
- `--wizard` - Interactive wizard mode
- `--non-interactive` - Non-interactive mode for --add

## Default Note Types

| Type | Folder | Properties | Purpose |
|------|--------|------------|---------|
| **map** | Atlas/Maps/ | type, up, related | MOC notes |
| **dot** | Atlas/Dots/ | type, up | Atomic notes |
| **source** | Atlas/Sources/ | type, author, url | References |
| **project** | Efforts/Projects/ | type, status, due | Projects |
| **daily** | Calendar/Daily/ | type, daily | Daily notes |

## Configuration

Note types are stored in `.claude/config/note-types.yaml`:

```yaml
note_types:
  map:
    folder: Atlas/Maps/
    properties:
      - type
      - up
      - related

  blog:
    folder: Writing/Blog/
    properties:
      - type
      - up
      - published
      - tags
    template: templates/blog-post.md
```

## Common Workflows

### Create a Custom Note Type

Use the wizard for a guided experience:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --wizard
```

### Quick Add with Defaults

Add a note type with minimal configuration:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --add meeting --non-interactive
```

### Modify Existing Type

Update properties or template for an existing type:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --edit project
```

### View All Configurations

List all note types to see your vault's structure:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/note-types/scripts/note_types.py" --list
```

## Integration with Validator

Note types can be used by the vault validator for type inference:

```yaml
# .claude/config/validator.yaml
type_rules:
  'Atlas/Maps/': map
  'Writing/Blog/': blog
  'Efforts/Meetings/': meeting
```
