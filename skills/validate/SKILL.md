---
name: validate
license: MIT
version: 1.3.0
description: "Obsidian vault validation and auto-fix tool with dynamic configuration and note-type specific validation. Use when the user wants to (1) validate vault frontmatter against standards, (2) check for missing required properties, (3) fix common issues like unquoted wikilinks or wrong date formats, (4) audit vault compliance with type-specific rules, or (5) run maintenance checks on their Obsidian vault. Triggers on keywords like validate vault, check frontmatter, fix vault issues, vault audit, maintenance check, note-type validation."
---

# Obsidian Validator

Validates Obsidian vault notes against configurable standards and auto-fixes common issues. Version 1.3.0 adds dynamic configuration and note-type specific validation.

## Quick Start

```bash
# Report mode (show issues without fixing)
uv run scripts/validator.py --vault /path/to/vault

# Auto-fix mode (fix issues automatically)
uv run scripts/validator.py --vault /path/to/vault --mode auto

# With custom config
uv run scripts/validator.py --vault /path/to/vault --config config/custom.yaml
```

## Validation Checks

The validator performs these checks:

| Check | Description | Auto-Fix |
|-------|-------------|----------|
| Empty Types | `type:` property exists but is empty | Yes - infers from folder |
| Missing Properties | Required frontmatter properties missing | Yes - adds `type:` |
| Invalid Daily Links | Full-path daily links instead of basename | Yes |
| Unquoted Wikilinks | `[[link]]` in YAML without quotes | Yes |
| Invalid Created | `created:` as wikilink instead of date | Yes |
| Title Properties | Redundant `title:` in frontmatter | Yes - removes |
| Date Mismatches | `created:` and `daily:` dates don't match | Yes - syncs |
| Type Property Violations | Type-specific required properties missing (v1.3.0) | No |
| Type Format Violations | Type-specific property format errors (v1.3.0) | No |

## Required Frontmatter Properties

Per vault standards, notes must have 6 properties:

```yaml
type: dot           # Note type (dot, map, source, project, etc.)
up: "[[Parent]]"    # Parent note link (quoted)
created: 2025-01-15 # Creation date (YYYY-MM-DD)
daily: "[[2025-01-15]]"  # Daily note link (basename, quoted)
collection:         # Collection classification (can be empty)
related:            # Related notes (can be empty)
```

## Configuration

### Default Config Location

The validator looks for config at: `.claude/config/validator.yaml`

### Key Configuration Options

```yaml
version: 1.3.0
dynamic_config: true          # Enable dynamic config loading (v1.3.0)
note_type_validation: true    # Enable type-specific validation (v1.3.0)

# Paths to exclude from validation
exclude_paths:
  - +/                    # Inbox
  - x/                    # System files
  - .obsidian/
  - .claude/

# Files to exclude
exclude_files:
  - Home.md
  - README.md

# Type inference rules (folder → type mapping)
type_rules:
  'Atlas/Maps/': map
  'Atlas/Dots/': dot
  'Atlas/Sources/': source
  'Efforts/Projects/': project
  'Calendar/daily/': daily

# Note-type specific validation rules (v1.3.0)
note_type_validation_rules:
  map:
    required: [type, up]           # Required properties for maps
    optional: [related, tags]      # Optional properties
    formats:
      created: date                # created must be YYYY-MM-DD
      up: wikilink                 # up must be [[link]]
  project:
    required: [type, status]
    optional: [due, priority]
    formats:
      status: string
      due: date

# Auto-fix toggles
auto_fix:
  empty_types: true
  daily_links: true
  wikilink_quotes: true
  title_properties: true
```

See `config/default.yaml` for complete configuration options.

## Modes

- **report** (default): Show issues without making changes
- **auto**: Fix issues automatically, re-validate after fixes
- **interactive**: Prompt before each fix (future)

## Exit Codes

- `0`: No issues found (or all fixed in auto mode)
- `1`: Issues found (or remaining after auto-fix)

## Integration with Claude Code

When user requests vault validation:

1. Determine vault path (usually current directory)
2. Check if custom config exists
3. Run validator in appropriate mode
4. Report results and suggest next steps
