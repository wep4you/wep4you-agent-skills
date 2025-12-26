---
name: init
version: "0.26.0"
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

### CRITICAL RULES

1. **ALWAYS use the wrapper**: `python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py"`
2. **NEVER call init_vault.py directly** - the wrapper handles execution internally
3. **Parse JSON output** and use AskUserQuestion for each `prompt_type`
4. **Keep ALL previous flags** when calling the wrapper again

### Workflow

The wrapper outputs JSON with `prompt_type`. Handle each type sequentially:

#### Step 1: Start
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path>
```

#### Step 2: `prompt_type: "action_required"` (existing vault)
→ Use AskUserQuestion with options from JSON
→ Call wrapper again WITH `--action=<chosen>`:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue
```

#### Step 3: `prompt_type: "methodology_required"`
→ Use AskUserQuestion with methodology options
→ Call wrapper again WITH `-m <methodology>` AND keep `--action`:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para
```

#### Step 4: `prompt_type: "note_types_required"`
→ Use AskUserQuestion with multi-select (all types selected by default)
→ Join selected IDs with comma
→ Call wrapper again WITH `--note-types=<types>` AND keep ALL previous flags:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para --note-types=project,area
```

#### Step 5: Execution
The wrapper automatically executes when all parameters are provided.

### Complete Example

```
1. User: /obsidian:init

2. Run: python3 .../commands/init.py /vault
   → JSON: {"prompt_type": "action_required", ...}
   → AskUserQuestion → User: "continue"

3. Run: python3 .../commands/init.py /vault --action=continue
   → JSON: {"prompt_type": "methodology_required", ...}
   → AskUserQuestion → User: "para"

4. Run: python3 .../commands/init.py /vault --action=continue -m para
   → JSON: {"prompt_type": "note_types_required", "options": [...], ...}
   → AskUserQuestion (multi-select) → User: "project,area,resource"

5. Run: python3 .../commands/init.py /vault --action=continue -m para --note-types=project,area,resource
   → Initialization runs! Show results.
```

### After Initialization

Show what was created and suggest:
1. Open the vault in Obsidian
2. Run `/obsidian:validate` to check frontmatter
3. Run `/obsidian:config-show` to view settings

---

## CLI Reference

### Wrapper (commands/init.py) - USE THIS!

| Option | Description |
|--------|-------------|
| `<path>` | Path to vault (positional, required) |
| `--action` | Action for existing vault: abort, continue, reset, migrate |
| `-m, --methodology` | Methodology: lyt-ace, para, zettelkasten, minimal |
| `--note-types` | Comma-separated list of note types to include |
| `--check` | Output vault status as JSON (no changes) |
| `--list` | List methodologies and exit |

### Direct Script (init_vault.py) - FOR TESTING ONLY

| Option | Description |
|--------|-------------|
| `<path>` | Path to vault (positional, required) |
| `-m, --methodology` | Methodology: lyt-ace, para, zettelkasten, minimal |
| `--note-types` | Comma-separated list of note types to include |
| `--defaults` | Use default settings without prompts |
| `--reset` | Delete existing content before init |
| `--dry-run` | Preview without creating files |
| `--list-note-types` | List note types for a methodology as JSON |

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
