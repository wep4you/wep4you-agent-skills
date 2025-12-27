---
name: frontmatter
description: Manage frontmatter properties for Obsidian vault
---

# Frontmatter Property Management

Manage core and type-specific frontmatter properties for your Obsidian vault.

## Usage

```bash
# List all core properties
/frontmatter list-core

# List properties for a specific note type
/frontmatter list-type project

# Add a new core property
/frontmatter add-core priority string --description "Note priority"

# Add type-specific property
/frontmatter add-type-prop meeting attendees "list[string]"

# Get required properties for a type
/frontmatter get-required project

# List all configured types
/frontmatter list-types

# Save configuration
/frontmatter save
```

## Commands

- `list-core` - List all core properties
- `add-core <name> <type>` - Add/update core property
- `remove-core <name>` - Remove core property
- `list-type [TYPE]` - List type-specific properties
- `add-type-prop <type> <name> <prop_type>` - Add type-specific property
- `remove-type-prop <type> <name>` - Remove type-specific property
- `list-types` - List all note types
- `get-required [TYPE]` - Get required properties
- `save` - Save configuration

## Options

- `--vault PATH` - Vault path (default: current directory)
- `--format text|json|yaml` - Output format (default: text)
- `--required` - Mark property as required (for add commands)
- `--description DESC` - Property description
- `--format FORMAT` - Property format spec (e.g., YYYY-MM-DD)

## Examples

### View Core Properties

```bash
/frontmatter list-core
```

### Add Custom Core Property

```bash
/frontmatter add-core priority string --description "Note priority level"
/frontmatter save
```

### Configure Project Properties

```bash
/frontmatter add-type-prop project budget string --description "Project budget"
/frontmatter add-type-prop project team "list[string]" --description "Team members"
/frontmatter save
```

### Export Properties

```bash
# Export as JSON
/frontmatter list-core --format json > core-properties.json

# Export as YAML
/frontmatter list-type --format yaml > type-properties.yaml
```

## Integration

This command works with the vault validator to define:

- Which properties are required/optional
- Property types and formats
- Type-specific property rules
- Validation constraints

After modifying properties, run the validator to check your vault:

```bash
/validate
```
