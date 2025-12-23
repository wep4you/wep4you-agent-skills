---
name: init
license: MIT
description: "Initialize a new Obsidian vault with a chosen PKM methodology (LYT-ACE, PARA, Zettelkasten, or Minimal). Creates folder structure, configuration files, and frontmatter standards. Use when the user wants to (1) create a new Obsidian vault, (2) set up a vault with a specific methodology, (3) initialize vault configuration, or (4) scaffold a new PKM system. Triggers on keywords like init vault, create vault, new obsidian vault, setup vault, scaffold vault."
---

# Obsidian Vault Initializer

Initialize a new Obsidian vault with a chosen Personal Knowledge Management (PKM) methodology.

## Quick Start

```bash
# Interactive mode (prompts for methodology)
uv run skills/init/scripts/init_vault.py --vault /path/to/vault

# Specify methodology directly
uv run skills/init/scripts/init_vault.py --vault /path/to/vault --methodology lyt-ace

# Dry-run mode (preview without creating)
uv run skills/init/scripts/init_vault.py --vault /path/to/vault --methodology para --dry-run

# List available methodologies
uv run skills/init/scripts/init_vault.py --list
```

## Available Methodologies

| Methodology | Description | Folders Created |
|-------------|-------------|-----------------|
| **lyt-ace** | Linking Your Thinking + ACE Framework | Atlas/Maps, Atlas/Dots, Atlas/Sources, Calendar/Daily, Efforts/Projects, Efforts/Areas |
| **para** | Tiago Forte's PARA Method | Projects, Areas, Resources, Archives |
| **zettelkasten** | Traditional slip-box system | Permanent, Literature, Fleeting, References |
| **minimal** | Simple starter structure | Notes, Daily |

## What Gets Created

When you initialize a vault, the following is created:

### 1. Folder Structure
Based on your chosen methodology, a complete folder hierarchy is created with the methodology's recommended organization.

### 2. Configuration Files (`.claude/config/`)

- **`validator.yaml`** - Frontmatter validation configuration
  - Exclude paths and files
  - Type inference rules (folder → note type mapping)
  - Auto-fix settings

- **`frontmatter.yaml`** - Property definitions
  - Required and optional properties
  - Property types (text, date, wikilink, etc.)
  - Property descriptions

- **`note-types.yaml`** - Note type definitions
  - Note type descriptions
  - Template associations (customizable)

### 3. README.md
A vault README with methodology description, folder structure, and validation commands.

### 4. System Folders
- `.obsidian/` - Obsidian settings directory
- `.claude/config/` - Claude Code configuration

## Frontmatter Standards

All initialized vaults use these 6 standard frontmatter properties:

```yaml
type: dot           # Note type (inferred from folder)
up: "[[Parent]]"    # Parent note link
created: 2025-01-15 # Creation date (YYYY-MM-DD)
daily: "[[2025-01-15]]"  # Daily note link
collection:         # Collection classification (optional)
related:            # Related notes (optional)
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--vault <path>` | Path to vault (required, created if doesn't exist) |
| `--methodology <name>` | Methodology to use (lyt-ace, para, zettelkasten, minimal) |
| `--dry-run` | Preview what would be created without creating files |
| `--list` | List all available methodologies and exit |

## Examples

### Initialize with LYT-ACE methodology
```bash
uv run skills/init/scripts/init_vault.py --vault ~/Documents/MyVault --methodology lyt-ace
```

### Preview PARA structure
```bash
uv run skills/init/scripts/init_vault.py --vault ~/test-vault --methodology para --dry-run
```

### Interactive mode (prompts for methodology)
```bash
uv run skills/init/scripts/init_vault.py --vault ~/NewVault
```

## Integration with Claude Code

When a user asks to initialize a vault:

1. **Determine vault path** - Ask user where to create the vault
2. **Choose methodology** - Use flag or interactive mode
3. **Run initialization** - Execute init_vault.py with appropriate args
4. **Confirm success** - Show created structure and next steps

### Suggested workflow
1. Run init to create vault structure
2. Open vault in Obsidian
3. Start creating notes
4. Run `/obsidian:validate` to check frontmatter compliance

## Customization

After initialization, users can customize:

- **Type rules** - Edit `.claude/config/validator.yaml` to adjust folder → type mappings
- **Properties** - Edit `.claude/config/frontmatter.yaml` to add custom properties
- **Note types** - Edit `.claude/config/note-types.yaml` to define new note types
- **Folder structure** - Add additional folders as needed

## Validation

Once initialized, validate the vault using the validate skill:

```bash
# Check for issues
uv run skills/validate/scripts/validator.py --vault /path/to/vault --mode report

# Auto-fix issues
uv run skills/validate/scripts/validator.py --vault /path/to/vault --mode auto
```

## Exit Codes

- `0` - Success
- `1` - Error (invalid methodology, file creation failed, etc.)

## See Also

- **validate skill** - Validate vault frontmatter against standards
- **Methodologies reference** - `skills/init/references/methodologies.md`
- **Configuration reference** - `skills/init/references/config.md`
