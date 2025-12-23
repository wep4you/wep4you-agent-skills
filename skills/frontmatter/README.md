# Frontmatter Property Management

Manage core and type-specific frontmatter properties for Obsidian vault validation.

## Overview

This skill provides tools to:

- Define and manage core frontmatter properties (available to all notes)
- Configure type-specific properties (per note type)
- Export property definitions in multiple formats
- Integrate with vault validation workflows

## Installation

This skill is part of the `wep4you-agent-skills` package:

```bash
# Install package
uv sync --all-extras

# Or run directly with uv
uv run skills/frontmatter/scripts/frontmatter.py --help
```

## Quick Start

```bash
# List all core properties
uv run skills/frontmatter/scripts/frontmatter.py list-core

# List properties for a specific note type
uv run skills/frontmatter/scripts/frontmatter.py list-type project

# Add a custom core property
uv run skills/frontmatter/scripts/frontmatter.py add-core priority string --description "Note priority"

# Add type-specific property
uv run skills/frontmatter/scripts/frontmatter.py add-type-prop project budget string

# Save configuration
uv run skills/frontmatter/scripts/frontmatter.py save
```

## Default Properties

### Core Properties

Every note should have these properties:

```yaml
type: string          # Required - Note type (dot, map, source, etc.)
up: "[[Parent]]"      # Optional - Parent note
created: 2025-01-15   # Required - Creation date
daily: "[[2025-01-15]]"  # Optional - Daily note link
collection: null      # Optional - Collection
related: []           # Optional - Related notes
```

### Type-Specific Properties

Additional properties by note type:

**Dot** (atomic notes):
- `tags`: List of topic tags

**Map** (structure notes):
- `tags`: Topic tags
- `summary`: Map summary

**Source** (references):
- `author`: Source author
- `url`: Source URL
- `published`: Publication date

**Project**:
- `status`: Project status (required: active/completed/archived/planning)
- `deadline`: Project deadline

**Daily**:
- `mood`: Daily mood (great/good/neutral/bad)

## Commands

### Core Properties

```bash
# List
frontmatter.py list-core [--format text|json|yaml]

# Add/Update
frontmatter.py add-core NAME TYPE [--required] [--description DESC]

# Remove
frontmatter.py remove-core NAME
```

### Type Properties

```bash
# List all types
frontmatter.py list-types

# List type properties
frontmatter.py list-type [TYPE] [--format text|json|yaml]

# Add/Update
frontmatter.py add-type-prop TYPE NAME PROP_TYPE [--required] [--description DESC]

# Remove
frontmatter.py remove-type-prop TYPE NAME
```

### Utility

```bash
# Get required properties
frontmatter.py get-required [TYPE] [--format text|json|yaml]

# Save configuration
frontmatter.py save
```

## Configuration File

Properties are stored at `.claude/config/frontmatter.yaml`:

```yaml
core_properties:
  type:
    required: true
    type: string
    description: Note type classification
  created:
    required: true
    type: date
    format: YYYY-MM-DD
    description: Creation date
  # ... more core properties

type_properties:
  project:
    status:
      required: true
      type: string
      values: [active, completed, archived, planning]
      description: Project status
  # ... more types
```

## Property Specification

Each property supports:

- **required**: Boolean - is this property mandatory?
- **type**: string, date, wikilink, list[string], list[wikilink]
- **description**: Human-readable description
- **format**: Format spec (e.g., YYYY-MM-DD for dates)
- **values**: Allowed values for enum types

## Output Formats

All commands support:

- `--format text`: Human-readable (default)
- `--format json`: Machine-readable JSON
- `--format yaml`: YAML for configs/exports

## Examples

### Customize Core Properties

```bash
# Add priority to all notes
uv run scripts/frontmatter.py add-core priority string \
  --description "Note priority level"

# Save changes
uv run scripts/frontmatter.py save
```

### Configure Meeting Note Type

```bash
# Add meeting-specific properties
uv run scripts/frontmatter.py add-type-prop meeting attendees "list[string]" \
  --description "Meeting attendees"

uv run scripts/frontmatter.py add-type-prop meeting date date \
  --required --description "Meeting date"

# Save
uv run scripts/frontmatter.py save
```

### Export for Documentation

```bash
# Export all properties as YAML
uv run scripts/frontmatter.py list-core --format yaml > docs/core-properties.yaml
uv run scripts/frontmatter.py list-type --format yaml > docs/type-properties.yaml
```

## Integration

### With Validator

The validator skill uses these property definitions:

1. Load core + type properties
2. Validate each note against required properties
3. Check property formats (dates, enums, etc.)
4. Report missing or invalid properties

### With Custom Scripts

```python
from frontmatter import FrontmatterManager

manager = FrontmatterManager("/path/to/vault")

# Get required properties for a note type
required = manager.get_required_properties("project")

# Check if property exists
if "status" in required:
    print(f"Status is required: {required['status']}")
```

## Development

Run tests:

```bash
uv run pytest tests/test_frontmatter.py -v
```

Lint:

```bash
uv run ruff check skills/frontmatter/
uv run ruff format skills/frontmatter/
```

## License

MIT License - See LICENSE file for details.
