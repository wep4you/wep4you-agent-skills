---
name: init
version: "0.25.0"
license: MIT
description: "Initialize a new Obsidian vault with a chosen PKM methodology (LYT-ACE, PARA, Zettelkasten, or Minimal). Creates folder structure, configuration files, and frontmatter standards. Use when the user wants to (1) create a new Obsidian vault, (2) set up a vault with a specific methodology, (3) initialize vault configuration, or (4) scaffold a new PKM system. Triggers on keywords like init vault, create vault, new obsidian vault, setup vault, scaffold vault."
---

# Obsidian Vault Initializer

Initialize a new Obsidian vault with a chosen Personal Knowledge Management (PKM) methodology.

## Available Methodologies

| Methodology | Description |
|-------------|-------------|
| **lyt-ace** | Linking Your Thinking + ACE Framework |
| **para** | Tiago Forte's PARA Method |
| **zettelkasten** | Traditional slip-box system |
| **minimal** | Simple starter structure |

## Integration with Claude Code

**This skill uses a wrapper script that enforces correct workflow order.**

### Workflow: Use the Wrapper Script

Run the wrapper script which outputs structured JSON prompts:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path>
```

### Parse JSON Output

The wrapper outputs JSON with a `prompt_type` field. Handle each type:

**`prompt_type: "action_required"`** (Existing vault detected)

Use AskUserQuestion with these options:
- **Abort** (Default) - Cancel initialization
- **Continue** - Add methodology structure to existing content
- **Reset** - Delete all content and start fresh (DESTRUCTIVE)
- **Migrate** - Migration feature (coming soon)

Then call wrapper with chosen action:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=<chosen>
```

**`prompt_type: "methodology_required"`** (Ready for methodology)

Use AskUserQuestion with methodology options:
- lyt-ace (LYT + ACE Framework)
- para (PARA Method)
- zettelkasten (Traditional Zettelkasten)
- minimal (Simple starter)

Then call wrapper with chosen methodology (preserving the previous action if any):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=<previous_action> -m <methodology>
```

**IMPORTANT:** If the previous step was `--action=reset`, you MUST include it again!

**`prompt_type: "note_types_required"`** (Select note types)

Use AskUserQuestion with multi-select for note types. The JSON includes:
- `multi_select: true` - Allow multiple selections
- `options` - List of note types with `id`, `label`, `description`, `selected`

Then call wrapper with selected note types:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=<action> -m <methodology> --note-types=<type1,type2,...>
```

To skip note type selection and use all defaults, add `--defaults`:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> -m <methodology> --defaults
```

### Example Flow

```
1. User: /obsidian:init

2. Run wrapper:
   python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /path/to/vault

3. If JSON shows "action_required":
   → AskUserQuestion: "What to do with existing vault?"
   → User selects "reset"
   → Run: python3 ... --action=reset
   → This returns "methodology_required"

4. If JSON shows "methodology_required":
   → AskUserQuestion: "Which methodology?"
   → User selects "para"
   → Run: python3 ... --action=reset -m para
   → This returns "note_types_required"

5. If JSON shows "note_types_required":
   → AskUserQuestion: "Which note types?" (multi-select)
   → User selects "project, area"
   → Run: python3 ... --action=reset -m para --note-types=project,area
   → (IMPORTANT: Keep --action AND -m from previous steps!)

6. Show results and next steps
```

**Quick initialization** (skip note type selection):
```
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /path/to/vault -m para --defaults
```

### After Initialization

Show what was created and suggest next steps:
1. Open the vault in Obsidian
2. Explore the sample notes in each folder
3. Run `/obsidian:validate` to check frontmatter
4. Run `/obsidian:config-show` to view settings

---

## CLI Reference

### Wrapper (commands/init.py)

| Option | Description |
|--------|-------------|
| `<path>` | Path to vault (positional, required) |
| `-m, --methodology` | Methodology: lyt-ace, para, zettelkasten, minimal |
| `--action` | Action for existing vault: abort, continue, reset, migrate |
| `--note-types` | Comma-separated list of note types to include |
| `--defaults` | Skip note type selection (use all defaults) |
| `--check` | Output vault status as JSON (no changes) |
| `--list` | List methodologies and exit |

### Direct Script (init_vault.py)

| Option | Description |
|--------|-------------|
| `<path>` | Path to vault (positional, required) |
| `-m, --methodology` | Methodology: lyt-ace, para, zettelkasten, minimal |
| `--note-types` | Comma-separated list of note types to include |
| `--defaults` | Use default settings without prompts |
| `--check` | Output vault status as JSON (no changes) |
| `--reset` | Delete existing content before init |
| `--dry-run` | Preview without creating files |
| `--list` | List methodologies and exit |
| `--list-note-types` | List note types for a methodology as JSON |
| `--wizard` | Full interactive wizard (terminal only) |

## Examples

```bash
# Check vault status (JSON output)
uv run init_vault.py /path/to/vault --check

# Initialize with PARA methodology (all note types)
uv run init_vault.py /path/to/vault -m para --defaults

# Initialize with specific note types only
uv run init_vault.py /path/to/vault -m para --note-types=project,area --defaults

# Reset and reinitialize
uv run init_vault.py /path/to/vault -m lyt-ace --defaults --reset

# Preview what would be created
uv run init_vault.py /path/to/vault -m zettelkasten --dry-run

# List available methodologies
uv run init_vault.py --list

# List note types for a methodology
uv run init_vault.py --list-note-types para
```

## What Gets Created

1. **Folder Structure** - Based on chosen methodology
2. **Configuration** - `.claude/settings.yaml` with validation rules
3. **Sample Notes** - Getting started notes for each note type
4. **Template Notes** - Templates for each note type in `x/templates/`
5. **all_bases.base** - Obsidian Bases views in `x/bases/` for folder navigation
6. **Home.md** - Vault home page with navigation
7. **README.md** - Vault documentation

## Exit Codes

- `0` - Success (including `--check` output)
- `1` - Error (invalid methodology, file creation failed)
