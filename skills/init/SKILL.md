---
name: init
version: "0.37.0"
license: MIT
description: "Initialize a new Obsidian vault with a chosen PKM methodology (LYT-ACE, PARA, Zettelkasten, or Minimal). Creates folder structure, configuration files, and frontmatter standards. Use when the user wants to (1) create a new Obsidian vault, (2) set up a vault with a specific methodology, (3) initialize vault configuration, or (4) scaffold a new PKM system. Triggers on keywords like init vault, create vault, new obsidian vault, setup vault, scaffold vault."
---

# Obsidian Vault Initializer

Initialize a new Obsidian vault with a chosen Personal Knowledge Management (PKM) methodology.

## ⛔ FORBIDDEN - READ THIS FIRST ⛔

**NEVER call these scripts directly:**
- ❌ `skills/init/scripts/init_vault.py` - FORBIDDEN
- ❌ `skills/init/scripts/wizard.py` - FORBIDDEN
- ❌ `skills/init/scripts/content_generators.py` - FORBIDDEN
- ❌ Any script in `skills/init/scripts/` - FORBIDDEN

**ONLY call the wrapper:**
- ✅ `uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py"` - CORRECT

If you call the internal scripts directly, you will get an error:
`{"error": "Direct call not allowed", "message": "This script must be called through the wrapper."}`

## Available Methodologies

| Methodology | Description |
|-------------|-------------|
| **lyt-ace** | Linking Your Thinking + ACE Framework |
| **para** | Tiago Forte's PARA Method |
| **zettelkasten** | Traditional slip-box system |
| **minimal** | Simple starter structure |

## Integration with Claude Code

### ⚠️ CRITICAL RULES ⚠️

1. **ONLY use this command**: `uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> [options]`
2. **NEVER call any script in `skills/init/scripts/` directly** - they will reject the call!
3. **After EVERY user selection**, call the wrapper AGAIN with accumulated flags
4. **Parse JSON `next_step`** field to see the exact command to run next
5. **Use AskUserQuestion** for each `prompt_type` in JSON output

**The wrapper handles ALL execution internally. You NEVER need to call another script.**

### Workflow

The wrapper outputs JSON with `prompt_type`. Handle each type sequentially:

**⚠️ IMPORTANT: For ALL prompts with `multi_select: true` or `options` array, you MUST use the AskUserQuestion tool - NEVER ask as free text!**

#### Step 1: Start
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path>
```

#### Step 2: `prompt_type: "action_required"` (existing vault)
→ Use AskUserQuestion with options from JSON
→ Call wrapper again WITH `--action=<chosen>`:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue
```

#### Step 3: `prompt_type: "methodology_required"`
→ Use AskUserQuestion with methodology options
→ Call wrapper again WITH `-m <methodology>` AND keep `--action`:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para
```

#### Step 4: `prompt_type: "note_types_required"`
→ Use AskUserQuestion with "All (Recommended)" or "Custom" options
→ If user chooses "all": `--note-types=all`
→ If user chooses "custom": `--note-types=custom` (triggers Step 4b)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para --note-types=all
```

#### Step 4b: `prompt_type: "note_types_select"` (only if custom)
→ **MUST use AskUserQuestion tool** with multi-select from `options` array
→ Each option has `id`, `label`, `description` - use these for the question
→ Set `multiSelect: true` in AskUserQuestion
→ Join selected IDs with comma in `--note-types`
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para --note-types=project,area
```

**Example AskUserQuestion for note_types_select:**
```json
{
  "questions": [{
    "question": "Which note types do you want to include?",
    "header": "Note Types",
    "multiSelect": true,
    "options": [
      {"label": "Map", "description": "Map of Content - Overview and navigation notes"},
      {"label": "Dot", "description": "Atomic concepts and ideas"},
      ...
    ]
  }]
}
```

#### Step 5: `prompt_type: "properties_required"`
→ Use AskUserQuestion with "All (Recommended)" or "Custom" options
→ If user chooses "all": `--core-properties=all`
→ If user chooses "custom": `--core-properties=custom` (triggers Step 5b)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para --note-types=all --core-properties=all
```

#### Step 5b: `prompt_type: "properties_select"` (only if custom)
→ **MUST use AskUserQuestion tool** with multi-select from `options` array
→ Options with `disabled: true` (type, created) are mandatory - pre-select them
→ Set `multiSelect: true` in AskUserQuestion
→ Join selected IDs with comma in `--core-properties`
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para --note-types=all --core-properties=type,created,up,tags
```

#### Step 6: `prompt_type: "custom_properties_input"`

**⚠️ CRITICAL: This is a FREE TEXT input - do NOT add options like "None", "Custom", etc!**

→ Simply ask the user to type property names (comma-separated)
→ If user types property names: use them in `--custom-properties=<names>`
→ If user says "none", "skip", or similar: use `--custom-properties=none`

**Correct approach:**
```
Claude: "Enter custom property names for ALL note types (comma-separated), or 'none' to skip:"
User types: "myProp1, myProp2"
```

**WRONG approach (do NOT do this):**
```
Claude shows options: [None] [Custom] [Type something]  ← NEVER DO THIS
```

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para --note-types=all --core-properties=all --custom-properties=myProp1,myProp2
```

#### Step 7: `prompt_type: "per_type_properties_combined"`

**⚠️ CRITICAL: Pass user input EXACTLY as typed - do NOT map to existing properties!**

For each note type in `type_sections`:
1. Show checkboxes for existing `optional` properties (from methodology)
2. Allow free text input for custom properties specific to this type
3. Combine both into the result

**Format:** `--per-type-props=type1:selected1,selected2,custom1;type2:none;type3:customOnly`

**Example flow:**
```
Daily notes - optional properties available: [mood] [weather]
User selects: (none)
User types custom: "motto"
Result for daily: "motto" (NOT "mood"!)

Project notes - optional properties available: [deadline] [priority]
User selects: [deadline] ✓
User types custom: (empty)
Result for project: "deadline"
```

**CRITICAL:** If user types "motto", pass "motto" - do NOT change it to "mood" because it looks similar!

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=continue -m para --note-types=all --core-properties=all --custom-properties=priority --per-type-props=project:deadline,budget;daily:motto;area:none
```

#### Step 8: Execution
The wrapper automatically executes when all parameters are provided.

### Complete Example (with Custom selection)

```
1. User: /obsidian:init

2. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault
   → JSON: {"prompt_type": "action_required", ...}
   → AskUserQuestion → User: "continue"

3. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue
   → JSON: {"prompt_type": "methodology_required", ...}
   → AskUserQuestion → User: "para"

4. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue -m para
   → JSON: {"prompt_type": "note_types_required", ...}
   → AskUserQuestion (All/Custom) → User: "custom"

5. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue -m para --note-types=custom
   → JSON: {"prompt_type": "note_types_select", ...}
   → AskUserQuestion (multi-select) → User: "project,area"

6. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue -m para --note-types=project,area
   → JSON: {"prompt_type": "properties_required", ...}
   → AskUserQuestion (All/Custom) → User: "all"

7. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue -m para --note-types=project,area --core-properties=all
   → Initialization runs! Show results.
```

### Quick Example (All defaults)

```
1. User: /obsidian:init

2-4. (action, methodology selection as above)

5. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue -m para
   → JSON: {"prompt_type": "note_types_required", ...}
   → AskUserQuestion → User: "all"

6. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue -m para --note-types=all
   → JSON: {"prompt_type": "properties_required", ...}
   → AskUserQuestion → User: "all"

7. Run: uv run "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /vault --action=continue -m para --note-types=all --core-properties=all
   → Initialization runs! Show results.
```

### After Initialization

Show what was created and suggest:
1. Open the vault in Obsidian
2. Run `/obsidian:validate` to check frontmatter
3. Run `/obsidian:config-show` to view settings

---

## CLI Reference (commands/init.py)

| Option | Description |
|--------|-------------|
| `<path>` | Path to vault (positional, required) |
| `--action` | Action for existing vault: abort, continue, reset, migrate |
| `-m, --methodology` | Methodology: lyt-ace, para, zettelkasten, minimal |
| `--note-types` | Comma-separated list of note types to include |
| `--core-properties` | Comma-separated list of core properties to include |
| `--custom-properties` | Comma-separated list of custom global properties |
| `--per-type-props` | Per-type properties: `type1:prop1,prop2;type2:prop3` |
| `--defaults` | Skip note type and property selection (use all) |
| `--check` | Output vault status as JSON (no changes) |
| `--list` | List methodologies and exit |

⚠️ **DO NOT use init_vault.py directly** - it is an internal script called by the wrapper.

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
