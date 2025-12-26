# Obsidian Vault Initializer

Initialize a new Obsidian vault with a chosen Personal Knowledge Management (PKM) methodology.

## Features

- **Multiple methodologies** - Choose from LYT-ACE, PARA, Zettelkasten, or Minimal
- **Complete setup** - Creates folders, config files, and documentation
- **Frontmatter standards** - Pre-configured validation rules
- **Dry-run mode** - Preview before creating
- **Interactive or CLI** - Choose methodology interactively or via flags

## Quick Start

```bash
# Interactive mode
uv run skills/init/scripts/init_vault.py --vault /path/to/vault

# Specify methodology
uv run skills/init/scripts/init_vault.py --vault /path/to/vault --methodology lyt-ace

# Preview only (dry-run)
uv run skills/init/scripts/init_vault.py --vault /path/to/vault --methodology para --dry-run
```

## Methodologies

### LYT-ACE (Linking Your Thinking + ACE Framework)

Combines Nick Milo's Linking Your Thinking with Atlas/Calendar/Efforts structure.

**Folders:**
- `Atlas/Maps` - Maps of Content (MOCs)
- `Atlas/Dots` - Atomic notes and concepts
- `Atlas/Sources` - Reference material
- `Calendar/Daily` - Daily notes
- `Efforts/Projects` - Active projects
- `Efforts/Areas` - Areas of responsibility

**Best for:** People who want a comprehensive, interconnected knowledge system with clear organizational layers.

### PARA (Projects, Areas, Resources, Archives)

Tiago Forte's productivity-focused organization method.

**Folders:**
- `Projects` - Active projects with deadlines
- `Areas` - Areas of responsibility
- `Resources` - Reference materials
- `Archives` - Inactive items

**Best for:** People focused on actionable work and GTD-style productivity.

### Zettelkasten

Traditional slip-box system focused on atomic notes and connections.

**Folders:**
- `Permanent` - Permanent notes (main knowledge)
- `Literature` - Literature notes from sources
- `Fleeting` - Fleeting notes (temporary thoughts)
- `References` - Reference materials

**Best for:** Researchers, academics, and people building a long-term knowledge base.

### Minimal

Simple starter structure for getting started quickly.

**Folders:**
- `Notes` - General notes
- `Daily` - Daily notes

**Best for:** Beginners or people who want to start simple and evolve their system.

## What Gets Created

### 1. Folder Structure
Complete folder hierarchy based on chosen methodology.

### 2. Configuration Files (`.claude/config/`)

#### `validator.yaml`
```yaml
exclude_paths:
  - "+/"          # Inbox
  - "x/"          # System files
  - ".obsidian/"
  - ".claude/"

type_rules:
  'Atlas/Maps/': map
  'Atlas/Dots/': dot
  # ... methodology-specific rules

auto_fix:
  empty_types: true
  daily_links: true
  wikilink_quotes: true
  title_properties: true
```

#### `frontmatter.yaml`
```yaml
properties:
  type:
    description: Note type classification
    type: text
    required: true
  up:
    description: Parent note link
    type: wikilink
    required: true
  # ... 6 standard properties
```

#### `note-types.yaml`
```yaml
note_types:
  dot:
    description: Dot note
    template: null
  map:
    description: Map note
    template: null
  # ... methodology-specific types
```

### 3. README.md
Vault documentation with methodology description and usage instructions.

### 4. System Folders
- `.obsidian/` - Obsidian configuration
- `.claude/config/` - Claude Code configuration

## Usage Examples

### Initialize new vault with LYT-ACE
```bash
uv run skills/init/scripts/init_vault.py \
  --vault ~/Documents/MyKnowledge \
  --methodology lyt-ace
```

**Output:**
```
Initializing vault at: /Users/you/Documents/MyKnowledge
Methodology: LYT + ACE Framework

Creating LYT + ACE Framework folder structure...
  Created: /Users/you/Documents/MyKnowledge/Atlas/Maps
  Created: /Users/you/Documents/MyKnowledge/Atlas/Dots
  ...

Creating configuration files...
  Created: /Users/you/Documents/MyKnowledge/.claude/config/validator.yaml
  Created: /Users/you/Documents/MyKnowledge/.claude/config/frontmatter.yaml
  Created: /Users/you/Documents/MyKnowledge/.claude/config/note-types.yaml

Created: /Users/you/Documents/MyKnowledge/README.md

✓ Vault initialization complete!
```

### Preview PARA structure (dry-run)
```bash
uv run skills/init/scripts/init_vault.py \
  --vault ~/test-vault \
  --methodology para \
  --dry-run
```

**Output:**
```
*** DRY RUN MODE - No files will be created ***

Creating PARA Method folder structure...
  [DRY RUN] Would create: /Users/you/test-vault/Projects
  [DRY RUN] Would create: /Users/you/test-vault/Areas
  ...
```

### List available methodologies
```bash
uv run skills/init/scripts/init_vault.py --list
```

**Output:**
```
Available methodologies:

  lyt-ace         - LYT + ACE Framework
                    Linking Your Thinking combined with Atlas/Calendar/Efforts structure
                    Folders: Atlas/Maps, Atlas/Dots, Atlas/Sources, Calendar/Daily, Efforts/Projects, Efforts/Areas

  para            - PARA Method
                    Tiago Forte's Projects, Areas, Resources, Archives system
                    Folders: Projects, Areas, Resources, Archives
  ...
```

## Command Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--vault` | Path | Yes | Path to vault (created if doesn't exist) |
| `--methodology` | Choice | No | Methodology: lyt-ace, para, zettelkasten, minimal |
| `--dry-run` | Flag | No | Preview without creating files |
| `--list` | Flag | No | List available methodologies and exit |

## Frontmatter Standards

All vaults are initialized with 6 standard frontmatter properties:

```yaml
type: dot                    # Note type (auto-inferred from folder)
up: "[[Parent Note]]"        # Parent note link
created: 2025-01-15          # Creation date (YYYY-MM-DD)
daily: "[[2025-01-15]]"      # Daily note link (basename)
collection:                  # Collection classification (optional)
related:                     # Related notes (optional)
```

These properties are validated by the `validate` skill.

## Post-Initialization

After initializing your vault:

1. **Open in Obsidian**
   ```bash
   open ~/Documents/MyVault
   ```

2. **Start creating notes** following your methodology's structure

3. **Validate frontmatter** (optional)
   ```bash
   uv run skills/validate/scripts/validator.py --vault ~/Documents/MyVault --mode report
   ```

4. **Customize configuration** (optional)
   - Edit `.claude/config/validator.yaml` for type rules
   - Edit `.claude/config/frontmatter.yaml` for properties
   - Edit `.claude/config/note-types.yaml` for note types

## Integration with Claude Code

Use the `/obsidian:init` command:

```
/obsidian:init
```

Claude will:
1. Ask for vault path
2. Offer methodology choices with descriptions
3. Initialize the vault
4. Confirm success and suggest next steps

## Error Handling

The script handles common errors:

- **Invalid methodology** - Shows available options
- **Permission errors** - Reports filesystem issues
- **Invalid paths** - Validates vault path

Exit codes:
- `0` - Success
- `1` - Error occurred

## Advanced Usage

### Custom methodology selection in scripts
```python
from pathlib import Path
from init_vault import init_vault

vault_path = Path("/path/to/vault")
init_vault(vault_path, methodology="lyt-ace", dry_run=False)
```

### Programmatic access to methodologies
```python
from init_vault import METHODOLOGIES, print_methodologies

# List all methodologies
print_methodologies()

# Get methodology details
lyt_ace = METHODOLOGIES["lyt-ace"]
print(lyt_ace["folders"])  # ['Atlas/Maps', 'Atlas/Dots', ...]
```

## Testing

Run tests:
```bash
uv run pytest tests/test_init.py -v
```

With coverage:
```bash
uv run pytest tests/test_init.py -v --cov=skills/init --cov-report=term-missing
```

## See Also

- **SKILL.md** - Skill documentation for Claude Code
- **validate skill** - Validate vault frontmatter
- **references/methodologies.md** - Detailed methodology comparison
- **references/config.md** - Configuration reference

## License

MIT License - See LICENSE file for details.
