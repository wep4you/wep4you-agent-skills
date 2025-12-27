---
name: validate
license: MIT
version: 1.6.0
description: "Obsidian vault validation and auto-fix tool using settings.yaml as single source of truth. Detects missing frontmatter, validates required properties, and auto-fixes common issues. Use when the user wants to (1) validate vault frontmatter against standards, (2) check for missing required properties, (3) fix common issues like unquoted wikilinks or wrong date formats, (4) audit vault compliance with type-specific rules, (5) run maintenance checks on their Obsidian vault, or (6) log validation results for audit trails. Triggers on keywords like validate vault, check frontmatter, fix vault issues, vault audit, maintenance check, note-type validation, audit log."
---

# Obsidian Validator

Validates Obsidian vault notes against configurable standards and auto-fixes common issues. Version 1.6.0 uses settings.yaml as single source of truth and detects notes without frontmatter.

## CRITICAL: Claude Code Behavior

**NEVER output commands for the user to copy.** When issues are found:

1. Show brief summary of issues
2. Ask: "Should I fix these issues automatically?" OR fix automatically
3. Run `--mode auto` yourself
4. Report results

❌ WRONG: "To fix, run: uv run scripts/validator.py --mode auto"
✅ RIGHT: "Fixing issues..." [runs auto-fix] "✅ Fixed 2 issues."

## Quick Start

```bash
# Report mode (show issues without fixing)
# Audit log written to .claude/logs/validate.jsonl by default
uv run scripts/validator.py --vault /path/to/vault

# Auto-fix mode (fix issues automatically)
uv run scripts/validator.py --vault /path/to/vault --mode auto

# Disable JSONL audit logging
uv run scripts/validator.py --vault /path/to/vault --no-jsonl

# Custom JSONL log path
uv run scripts/validator.py --vault /path/to/vault --jsonl custom-audit.jsonl
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

## JSONL Audit Logging (v1.5.0)

Audit logging is **enabled by default**. Validation results are automatically logged to `.claude/logs/validate.jsonl`.

```bash
# Default: logs to .claude/logs/validate.jsonl
uv run scripts/validator.py --vault .

# Custom log path
uv run scripts/validator.py --vault . --jsonl my-audit.jsonl

# Disable logging
uv run scripts/validator.py --vault . --no-jsonl
```

Each line in the JSONL file is a complete JSON object:

```json
{
  "timestamp": "2025-12-27T10:30:00.123456",
  "vault_path": "/path/to/vault",
  "mode": "report",
  "methodology": "para",
  "total_issues": 5,
  "issues_by_type": {"empty_types": 2, "missing_properties": 3},
  "issues_detail": {"empty_types": ["file1.md", "file2.md"]},
  "fixes_applied": 0
}
```

The JSONL file is appended to, allowing you to track validation history over time. The `.claude/logs/` directory is created automatically if it doesn't exist.

## Exit Codes

- `0`: No issues found (or all fixed in auto mode)
- `1`: Issues found (or remaining after auto-fix)

## Integration with Claude Code

When user requests vault validation:

1. Run validator in report mode first
2. If issues are found:
   - Show summary to user
   - Ask if they want to auto-fix OR immediately run auto-fix mode
   - **DO NOT output the command** - just run it directly
3. After auto-fix, report results

**Important**: When issues are found, Claude should proactively offer to fix them or run auto-fix directly. Never just output a command for the user to copy - always execute it.

### Example Flow

```
User: validate my vault

Claude: [runs validator in report mode]
Claude: Found 2 issues. Fixing automatically...
Claude: [runs validator in auto mode]
Claude: ✅ Fixed 2 issues. Vault is now compliant.
```
