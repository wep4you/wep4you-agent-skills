# Configuration Reference

Complete reference documentation for the Config Loader skill configuration files and structure.

## Table of Contents

- [Configuration Files](#configuration-files)
- [Configuration Structure](#configuration-structure)
- [Note Type Definitions](#note-type-definitions)
- [Property Definitions](#property-definitions)
- [Validation Rules](#validation-rules)
- [Examples](#examples)

## Configuration Files

### default.yaml

The primary configuration file defining core vault settings.

**Location:**
- Skill: `skills/config/config/default.yaml`
- Vault override: `{vault}/.claude/config/default.yaml`

**Sections:**
- `core_properties` - Required frontmatter properties
- `note_types` - Note type definitions
- `validation` - Validation rules
- `auto_fix` - Auto-fix toggles
- `exclude_paths` - Paths to exclude
- `exclude_files` - Files to exclude

### frontmatter-defaults.yaml

Default frontmatter templates for each note type.

**Location:**
- Skill: `skills/config/config/frontmatter-defaults.yaml`
- Vault override: `{vault}/.claude/config/frontmatter-defaults.yaml`

**Sections:**
- Template for each note type
- `date_format` - Date formatting string
- `daily_link_format` - Daily note link format
- `default_parents` - Default parent links by type

### note-types-defaults.yaml

Extended note type definitions with validation and metadata.

**Location:**
- Skill: `skills/config/config/note-types-defaults.yaml`
- Vault override: `{vault}/.claude/config/note-types-defaults.yaml`

**Sections:**
- `note_types` - Extended type definitions
- `global_validation` - Global validation settings
- `property_types` - Property type definitions

## Configuration Structure

### Core Properties

List of properties required in all notes:

```yaml
core_properties:
  - type          # Note type identifier
  - up            # Parent note wikilink
  - created       # Creation date (YYYY-MM-DD)
  - daily         # Daily note wikilink
  - collection    # Collection classification
  - related       # Related notes list
```

### Note Types

Each note type definition includes:

```yaml
note_types:
  {type_name}:
    description: "Human-readable description"
    folder_hints:
      - "Folder/Path/"      # List of path patterns
    properties:
      - type                # List of required properties
      - up
      - created
```

**Fields:**
- `description` (string, required) - Human-readable description
- `folder_hints` (list, required) - Folder path patterns for type inference
- `properties` (list, required) - Required frontmatter properties

### Validation Settings

```yaml
validation:
  require_core_properties: true    # Enforce core properties
  allow_empty_properties:          # Properties that can be empty
    - collection
    - related
  strict_types: true               # Restrict to defined types only
```

### Auto-Fix Settings

```yaml
auto_fix:
  empty_types: true              # Infer and fill empty types
  daily_links: true              # Fix daily note link format
  wikilink_quotes: true          # Add quotes to wikilinks
  title_properties: true         # Remove redundant titles
  missing_properties: true       # Add missing properties
```

### Exclusion Rules

```yaml
exclude_paths:
  - "+/"              # Inbox folder
  - "x/"              # System files
  - ".obsidian/"      # Obsidian settings
  - ".claude/"        # Claude configuration

exclude_files:
  - "Home.md"
  - "README.md"
  - "CHANGELOG.md"
```

## Note Type Definitions

### Standard Note Types

#### map - Map of Content

Overview and navigation notes that provide structure.

```yaml
map:
  description: "Map of Content - Overview and navigation notes"
  folder_hints:
    - "Atlas/Maps/"
    - "Maps/"
  properties:
    - type
    - up
    - created
    - daily
    - collection
    - related
```

**Use cases:** Index pages, topic overviews, navigation hubs

#### dot - Atomic Notes

Atomic concepts and ideas following Zettelkasten principles.

```yaml
dot:
  description: "Dot notes - Atomic concepts and ideas"
  folder_hints:
    - "Atlas/Dots/"
    - "Dots/"
  properties:
    - type
    - up
    - created
    - daily
    - collection
    - related
```

**Use cases:** Concepts, ideas, definitions, atomic notes

#### source - Reference Notes

External references, citations, and source material.

```yaml
source:
  description: "Source notes - External references and citations"
  folder_hints:
    - "Atlas/Sources/"
    - "Sources/"
  properties:
    - type
    - up
    - created
    - daily
    - collection
    - related
    - author
    - url
```

**Use cases:** Books, articles, papers, external resources

#### project - Project Notes

Defined outcomes with deadlines and deliverables.

```yaml
project:
  description: "Project notes - Defined outcomes with deadlines"
  folder_hints:
    - "Efforts/Projects/"
    - "Projects/"
  properties:
    - type
    - up
    - created
    - daily
    - collection
    - related
    - status
    - deadline
```

**Use cases:** Projects with end dates, defined outcomes

**Status values:** `active`, `planning`, `on-hold`, `completed`, `cancelled`

#### area - Area Notes

Ongoing responsibilities without end dates.

```yaml
area:
  description: "Area notes - Ongoing responsibilities"
  folder_hints:
    - "Efforts/Areas/"
    - "Areas/"
  properties:
    - type
    - up
    - created
    - daily
    - collection
    - related
```

**Use cases:** Ongoing responsibilities, life areas, maintenance

#### daily - Daily Notes

Date-based journal entries and daily logs.

```yaml
daily:
  description: "Daily notes - Date-based journal entries"
  folder_hints:
    - "Calendar/daily/"
    - "daily/"
  properties:
    - type
    - up
    - created
    - daily
    - collection
    - related
```

**Use cases:** Daily journals, logs, time-based entries

#### effort - Effort Notes

General work and task notes.

```yaml
effort:
  description: "Effort notes - Work and tasks"
  folder_hints:
    - "Efforts/"
  properties:
    - type
    - up
    - created
    - daily
    - collection
    - related
```

**Use cases:** Tasks, work items, general efforts

## Property Definitions

### Standard Properties

#### type

```yaml
type:
  data_type: "string"
  required: true
  allowed_values: ["map", "dot", "source", "effort", "project", "area", "daily"]
```

**Format:** Single word, lowercase
**Required:** Yes
**Allowed empty:** No

#### up

```yaml
up:
  data_type: "wikilink"
  required: true
  must_be_quoted: true
```

**Format:** `"[[Parent Note]]"`
**Required:** Yes
**Allowed empty:** No

#### created

```yaml
created:
  data_type: "date"
  required: true
  format: "YYYY-MM-DD"
```

**Format:** `2025-01-15`
**Required:** Yes
**Allowed empty:** No

#### daily

```yaml
daily:
  data_type: "wikilink"
  required: true
  must_be_quoted: true
  format: "[[YYYY-MM-DD]]"
```

**Format:** `"[[2025-01-15]]"`
**Required:** Yes
**Allowed empty:** No

#### collection

```yaml
collection:
  data_type: "string"
  required: true
  allow_empty: true
```

**Format:** String or empty
**Required:** Yes (property must exist)
**Allowed empty:** Yes

#### related

```yaml
related:
  data_type: "list"
  required: true
  allow_empty: true
```

**Format:** List of wikilinks or empty
**Required:** Yes (property must exist)
**Allowed empty:** Yes

### Type-Specific Properties

#### author (source notes)

```yaml
author:
  data_type: "string"
  required_for: ["source"]
```

**Format:** Author name(s)
**Required for:** source notes

#### url (source notes)

```yaml
url:
  data_type: "string"
  required_for: ["source"]
  validation: "url_format"
```

**Format:** Valid URL
**Required for:** source notes

#### status (project notes)

```yaml
status:
  data_type: "string"
  required_for: ["project"]
  allowed_values: ["active", "planning", "on-hold", "completed", "cancelled"]
```

**Format:** One of allowed values
**Required for:** project notes

#### deadline (project notes)

```yaml
deadline:
  data_type: "date"
  format: "YYYY-MM-DD"
```

**Format:** `2025-12-31`
**Required for:** project notes (recommended)

## Validation Rules

### Global Validation

```yaml
global_validation:
  require_core_properties: true   # All notes need core properties
  strict_mode: true               # Enforce all rules strictly
  allow_custom_types: false       # Only allow defined types
  max_properties: 20              # Maximum properties per note
```

### Type-Specific Validation

Each note type can define:

```yaml
validation:
  allow_empty_up: false           # Parent link required
  require_daily_link: true        # Daily link required
  require_author: true            # Author required (sources)
  require_status: true            # Status required (projects)
  require_date_match: true        # Created matches filename (daily)
  valid_statuses:                 # Allowed status values
    - active
    - planning
    - completed
```

## Examples

### Basic Vault Configuration

```yaml
# .claude/config/default.yaml

core_properties:
  - type
  - up
  - created
  - daily
  - collection
  - related

note_types:
  map:
    description: "Overview notes"
    folder_hints: ["Maps/"]
    properties: ["type", "up", "created", "daily", "collection", "related"]

  dot:
    description: "Atomic notes"
    folder_hints: ["Notes/"]
    properties: ["type", "up", "created", "daily", "collection", "related"]

validation:
  require_core_properties: true
  strict_types: true

auto_fix:
  empty_types: true
  daily_links: true
```

### Custom Note Type

```yaml
# .claude/config/custom.yaml

note_types:
  meeting:
    description: "Meeting notes"
    folder_hints:
      - "Meetings/"
      - "Work/Meetings/"
    properties:
      - type
      - up
      - created
      - daily
      - collection
      - related
      - attendees
      - agenda
      - action_items
```

### Minimal Configuration

```yaml
# .claude/config/minimal.yaml

core_properties:
  - type
  - created

note_types:
  note:
    description: "Simple note"
    folder_hints: ["/"]
    properties: ["type", "created"]

validation:
  require_core_properties: true
  strict_types: false
  allow_empty_properties: []

auto_fix:
  empty_types: false
  missing_properties: false
```

### Extended Validation

```yaml
# .claude/config/strict.yaml

validation:
  require_core_properties: true
  allow_empty_properties: []    # No empty properties allowed
  strict_types: true

note_types:
  source:
    properties:
      - type
      - up
      - created
      - daily
      - collection
      - related
      - author
      - url
      - published
    validation:
      require_author: true
      require_url: true
      url_format_validation: true
```

## Configuration Merging

Configurations are merged in order:

1. Embedded DEFAULT_CONFIG
2. Skill default.yaml
3. Vault override

**Merge behavior:**
- Dictionaries: Deep merge (nested keys combined)
- Lists: Replace (override completely replaces base)
- Values: Replace (override takes precedence)

**Example:**

```yaml
# Base
note_types:
  map:
    description: "Maps"
    properties: ["type", "up"]

# Override
note_types:
  map:
    properties: ["type", "up", "created"]
  dot:
    description: "Dots"
    properties: ["type", "up"]

# Result
note_types:
  map:
    description: "Maps"        # Kept from base
    properties: ["type", "up", "created"]  # Replaced by override
  dot:
    description: "Dots"        # Added from override
    properties: ["type", "up"]
```

## Best Practices

1. **Start with defaults** - Use skill defaults, override only what's needed
2. **Vault-specific overrides** - Keep custom configs in `.claude/config/`
3. **Document changes** - Comment custom configuration files
4. **Validate configs** - Run `--validate` after changes
5. **Test incrementally** - Test configs with small changes
6. **Version control** - Track vault configs in git
7. **Share configs** - Document team/project-specific configs

## Troubleshooting

### Configuration not loading

- Check file path: `.claude/config/{name}.yaml`
- Verify YAML syntax with `--validate`
- Check file permissions

### Validation errors

- Run `--validate` to see specific errors
- Check required fields exist
- Verify data types match definitions

### Merge issues

- Remember: lists replace, dicts merge
- Check merge order (embedded → skill → vault)
- Use `--show` to see final merged config

### Type inference fails

- Check `folder_hints` patterns
- Verify file path contains hint substring
- Add custom folder hints to config
