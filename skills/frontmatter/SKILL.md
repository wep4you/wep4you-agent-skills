---
name: frontmatter
license: MIT
description: "Frontmatter property management for Obsidian vaults. Use when the user wants to (1) manage core frontmatter properties, (2) configure type-specific properties, (3) list property definitions, (4) add or remove properties, (5) get required properties for validation. Triggers on keywords like frontmatter properties, manage properties, configure frontmatter, list properties, add property."
---

# Frontmatter Property Management

Manages core and type-specific frontmatter properties for Obsidian vault notes with configurable validation rules.

## Quick Start

```bash
# List core properties
uv run skills/frontmatter/scripts/frontmatter.py list-core

# List type-specific properties
uv run skills/frontmatter/scripts/frontmatter.py list-type dot

# Add a new core property
uv run skills/frontmatter/scripts/frontmatter.py add-core tags "list[string]" --description "Note tags"

# Add type-specific property
uv run skills/frontmatter/scripts/frontmatter.py add-type-prop project status string --required

# Get required properties for a type
uv run skills/frontmatter/scripts/frontmatter.py get-required project
```

## Core Properties

Default core properties available to all notes:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| type | string | Yes | Note type classification |
| up | wikilink | No | Parent note in hierarchy |
| created | date | Yes | Creation date (YYYY-MM-DD) |
| daily | wikilink | No | Associated daily note |
| collection | wikilink | No | Collection classification |
| related | list[wikilink] | No | Related notes |

## Type-Specific Properties

Additional properties defined per note type:

### Dot (Atomic Notes)
- **tags**: `list[string]` - Topic tags

### Map (Structure Notes)
- **tags**: `list[string]` - Topic tags
- **summary**: `string` - Map summary

### Source (Reference Notes)
- **author**: `string` - Source author
- **url**: `string` - Source URL
- **published**: `date` - Publication date (YYYY-MM-DD)

### Project (Project Notes)
- **status**: `string` (required) - Project status (active, completed, archived, planning)
- **deadline**: `date` - Project deadline (YYYY-MM-DD)

### Daily (Daily Notes)
- **mood**: `string` - Daily mood (great, good, neutral, bad)

## Commands

### Core Properties

```bash
# List all core properties
frontmatter.py list-core [--format text|json|yaml]

# Add or update core property
frontmatter.py add-core <name> <type> [--required] [--description DESC] [--format FORMAT]

# Remove core property
frontmatter.py remove-core <name>
```

### Type Properties

```bash
# List all types
frontmatter.py list-types

# List properties for a specific type (or all types)
frontmatter.py list-type [TYPE] [--format text|json|yaml]

# Add type-specific property
frontmatter.py add-type-prop <type> <name> <prop_type> [--required] [--description DESC]

# Remove type-specific property
frontmatter.py remove-type-prop <type> <name>
```

### Utility

```bash
# Get required properties for a note type
frontmatter.py get-required [TYPE] [--format text|json|yaml]

# Save current configuration
frontmatter.py save
```

## Property Types

Supported property types:

- `string` - Text value
- `date` - Date in YYYY-MM-DD format
- `wikilink` - Obsidian wikilink `[[Note]]`
- `list[string]` - List of text values
- `list[wikilink]` - List of wikilinks
- Custom types as needed

## Configuration

Configuration is stored at `.claude/config/frontmatter.yaml` in the vault:

```yaml
core_properties:
  type:
    required: true
    type: string
    description: Note type classification
  # ... other core properties

type_properties:
  dot:
    tags:
      required: false
      type: list[string]
      description: Topic tags
  # ... other types
```

## Property Specifications

Each property can have:

- **required**: `true|false` - Whether property is mandatory
- **type**: Property data type
- **description**: Human-readable description
- **format**: Format specification (e.g., `YYYY-MM-DD` for dates)
- **values**: Allowed values (for enums)

## Integration with Validator

The frontmatter manager provides property definitions used by the validator:

1. Validator uses core properties to check required fields
2. Type-specific properties validated based on note type
3. Format specifications enforce date formats, enums, etc.
4. Custom properties can be added per vault needs

## Output Formats

All list commands support multiple output formats:

- **text**: Human-readable formatted output (default)
- **json**: Machine-readable JSON
- **yaml**: YAML format for configs

## Examples

### Add Custom Core Property

```bash
# Add a priority property
uv run scripts/frontmatter.py add-core priority string \
  --description "Note priority" --save
```

### Configure Project Type

```bash
# Add budget field to projects
uv run scripts/frontmatter.py add-type-prop project budget string \
  --description "Project budget"

# Make it required
uv run scripts/frontmatter.py add-type-prop project budget string \
  --required --description "Project budget"
```

### Export Properties as YAML

```bash
# Export all core properties
uv run scripts/frontmatter.py list-core --format yaml > core-properties.yaml

# Export type properties
uv run scripts/frontmatter.py list-type --format yaml > type-properties.yaml
```

## Workflow

1. **Define Properties**: Use frontmatter manager to define required/optional properties
2. **Configure Types**: Add type-specific properties for different note types
3. **Validate**: Validator uses definitions to check notes
4. **Iterate**: Adjust properties based on vault needs

## Best Practices

- Keep core properties minimal and universal
- Use type-specific properties for specialized fields
- Mark properties `required` only when truly mandatory
- Provide clear descriptions for all properties
- Use appropriate types (wikilink for links, date for dates)
- Test validation after property changes
