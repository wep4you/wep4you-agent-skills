---
description: Initialize a new Obsidian vault with a PKM methodology
argument-hint: [vault_path]
allowed-tools: Bash(uv run:*), Bash(python3:*)
---

# Initialize Obsidian Vault

Initialize a new Obsidian vault with a chosen Personal Knowledge Management methodology.

## CRITICAL: Workflow Order

**This command uses a wrapper script that enforces correct workflow order.**

The wrapper outputs JSON prompts that you MUST parse and use to ask the user questions in the correct order.

## Execution Flow

### Step 1: Run the Wrapper

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path>
```

The wrapper will output JSON with `prompt_type` field.

### Step 2: Parse JSON Output

**If `prompt_type` = `"action_required"`:**

The vault already has content. You MUST ask the user using AskUserQuestion:

```json
{
  "prompt_type": "action_required",
  "question": "What would you like to do with the existing vault?",
  "options": [
    {"id": "abort", "label": "Abort", "description": "Cancel (default)"},
    {"id": "continue", "label": "Continue", "description": "Add to existing"},
    {"id": "reset", "label": "Reset", "description": "Delete and start fresh"},
    {"id": "migrate", "label": "Migrate", "description": "Coming soon"}
  ]
}
```

Then call wrapper again with action:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" <vault_path> --action=<chosen>
```

**If `prompt_type` = `"methodology_required"`:**

Ask the user which methodology to use:

```json
{
  "prompt_type": "methodology_required",
  "question": "Which methodology would you like to use?",
  "options": [
    {"id": "lyt-ace", "label": "LYT-ACE"},
    {"id": "para", "label": "PARA"},
    {"id": "zettelkasten", "label": "Zettelkasten"},
    {"id": "minimal", "label": "Minimal"}
  ]
}
```

Then execute initialization:
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" <vault_path> -m <methodology> --defaults
```

### Step 3: Show Results

After successful initialization:
1. Show what was created
2. Suggest next steps:
   - Open vault in Obsidian
   - Run `/obsidian:validate` to check frontmatter
   - Run `/obsidian:config-show` to view settings

## Complete Example Flow

```
User: /obsidian:init

You: Run wrapper
→ python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /path/to/vault

Wrapper outputs:
{
  "prompt_type": "action_required",
  "message": "Existing vault: 9 folders, 3 files",
  ...
}

You: Use AskUserQuestion with the options from JSON
→ User selects "Continue"

You: Run wrapper with action
→ python3 "${CLAUDE_PLUGIN_ROOT}/commands/init.py" /path/to/vault --action=continue

Wrapper outputs:
{
  "prompt_type": "methodology_required",
  ...
}

You: Use AskUserQuestion with methodology options
→ User selects "para"

You: Execute init
→ uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" /path/to/vault -m para --defaults

Done!
```

## Wrapper CLI Reference

| Option | Description |
|--------|-------------|
| `vault_path` | Path to vault (positional, default: current dir) |
| `--action` | Action for existing vault: abort, continue, reset, migrate |
| `-m, --methodology` | Methodology: lyt-ace, para, zettelkasten, minimal |
| `--check` | Output vault status as JSON |
| `--list` | List methodologies and exit |

## Available Methodologies

| Methodology | Description |
|-------------|-------------|
| **lyt-ace** | Linking Your Thinking + ACE Framework |
| **para** | Projects, Areas, Resources, Archives |
| **zettelkasten** | Traditional slip-box system |
| **minimal** | Simple starter structure |

## Exit Codes

- `0` - Success or JSON prompt output
- `1` - Error

## See Also

- **Skill documentation**: `skills/init/SKILL.md`
- **Validate skill**: `/obsidian:validate`
- **Config skill**: `/obsidian:config-show`
