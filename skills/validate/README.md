# Vault Validator

A Claude Code skill for validating and auto-fixing Obsidian vault frontmatter.

## Features

- **Frontmatter Validation**: Checks for required properties, proper formatting, and consistency
- **Auto-Fix**: Automatically fixes common issues like missing types, unquoted wikilinks, and date mismatches
- **Configurable**: YAML-based configuration for custom rules, exclusions, and type mappings
- **Progressive**: Report mode for review, auto mode for batch fixes

## Requirements

- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Python 3.10+

## Installation

### As a Claude Code Skill

1. Copy the `vault-validator/` directory to your `.claude/skills/` folder
2. The skill will be automatically detected by Claude Code

### Standalone Usage

```bash
# Clone or copy the skill
cp -r vault-validator /path/to/your/vault/.claude/skills/

# Run directly with uv
uv run /path/to/vault/.claude/skills/vault-validator/scripts/validator.py --vault .
```

## Usage

### Basic Validation

```bash
# Report mode - show issues without fixing
uv run scripts/validator.py --vault /path/to/vault

# Auto-fix mode - fix issues automatically
uv run scripts/validator.py --vault /path/to/vault --mode auto

# Generate markdown report
uv run scripts/validator.py --vault /path/to/vault --report report.md
```

### With Claude Code

Simply ask Claude to validate your vault:

- "Validate my vault frontmatter"
- "Check for missing properties in Atlas/"
- "Fix vault issues automatically"
- "Run a vault audit"

## Configuration

Create a `validator.yaml` in `.claude/config/` or use the `--config` flag.

### Example Configuration

```yaml
# Paths to exclude from validation
exclude_paths:
  - +/                    # Inbox - unprocessed content
  - x/                    # System files (templates, scripts)
  - .obsidian/
  - .claude/

# Type inference rules
type_rules:
  'Atlas/Maps/': map
  'Atlas/Dots/': dot
  'Atlas/Sources/': source
  'Efforts/Projects/': project
  'Calendar/daily/': daily

# Auto-fix settings
auto_fix:
  empty_types: true
  daily_links: true
  wikilink_quotes: true
  title_properties: true
```

See `config/default.yaml` for all options.

## Validation Checks

| Check | Description | Auto-Fix |
|-------|-------------|----------|
| Empty Types | `type:` exists but empty | Infers from folder location |
| Missing Properties | Required properties missing | Adds `type:` property |
| Invalid Daily Links | Full-path instead of basename | Converts to basename |
| Unquoted Wikilinks | `[[link]]` not quoted in YAML | Adds quotes |
| Invalid Created | `created:` as wikilink | Extracts date value |
| Title Properties | Redundant `title:` property | Removes property |
| Date Mismatches | `created:` ≠ `daily:` date | Syncs dates |

## Required Frontmatter

The validator expects these 6 properties (configurable):

```yaml
type: dot                    # Note classification
up: "[[Parent Note]]"        # Parent link (quoted wikilink)
created: 2025-01-15          # Creation date (YYYY-MM-DD)
daily: "[[2025-01-15]]"      # Daily note link (basename, quoted)
collection:                  # Collection tag (can be empty)
related:                     # Related notes (can be empty)
```

## Exit Codes

- `0`: No issues found (or all fixed in auto mode)
- `1`: Issues remain after validation

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Credits

Created for use with [Claude Code](https://claude.ai/code) by Anthropic.
