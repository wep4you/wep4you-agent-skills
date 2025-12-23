---
description: Initialize a new Obsidian vault with a PKM methodology
argument-hint: [--methodology lyt-ace|para|zettelkasten|minimal] [--vault path] [--dry-run]
allowed-tools: Bash(uv run:*)
---

# Initialize Obsidian Vault

Initialize a new Obsidian vault with a chosen Personal Knowledge Management methodology.

## Execution

Run the init script to create a new vault:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" --vault /path/to/vault --methodology lyt-ace
```

## Arguments

- `--vault <path>` - Path to vault (required, created if doesn't exist)
- `--methodology <name>` - Methodology: lyt-ace, para, zettelkasten, minimal (optional, prompts if omitted)
- `--dry-run` - Preview what would be created without creating files
- `--list` - List available methodologies and exit

## Available Methodologies

| Methodology | Description | Best For |
|-------------|-------------|----------|
| **lyt-ace** | Linking Your Thinking + ACE Framework | Comprehensive interconnected knowledge systems |
| **para** | Projects, Areas, Resources, Archives | Productivity and GTD-focused workflows |
| **zettelkasten** | Traditional slip-box system | Research and long-term knowledge building |
| **minimal** | Simple starter structure | Beginners wanting to start simple |

## What Gets Created

1. **Folder structure** - Methodology-specific folders (e.g., Atlas/Maps, Projects, etc.)
2. **Configuration files** - `.claude/config/` with validator.yaml, frontmatter.yaml, note-types.yaml
3. **README.md** - Vault documentation
4. **System folders** - `.obsidian/`, `.claude/config/`

## Examples

### Interactive mode (prompts for methodology)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" --vault ~/Documents/MyVault
```

### Specify methodology
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" \
  --vault ~/Documents/MyVault \
  --methodology para
```

### Preview (dry-run)
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" \
  --vault ~/test \
  --methodology zettelkasten \
  --dry-run
```

### List methodologies
```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" --list
```

## Workflow

When a user requests vault initialization:

1. **Determine vault path**
   - Ask user where to create the vault
   - Default to current directory if appropriate

2. **Choose methodology**
   - If user specified: use that methodology
   - If not specified: run in interactive mode or ask for preference

3. **Confirm before creation**
   - Show what will be created
   - Suggest using --dry-run to preview

4. **Run initialization**
   - Execute init_vault.py with chosen options
   - Show progress and results

5. **Post-initialization**
   - Suggest opening vault in Obsidian
   - Mention validation command: `/obsidian:validate`
   - Explain next steps for customization

## Common Scenarios

### User: "Create a new Obsidian vault with PARA method"
```bash
# Ask for vault path, then run:
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" \
  --vault /path/from/user \
  --methodology para
```

### User: "Initialize a vault with LYT structure"
```bash
# LYT = lyt-ace methodology
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" \
  --vault /path/from/user \
  --methodology lyt-ace
```

### User: "Set up a new vault for me"
```bash
# Interactive - let script prompt for methodology
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" \
  --vault /path/from/user
```

### User: "Show me what folders would be created with Zettelkasten"
```bash
# Use dry-run to preview
uv run "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_vault.py" \
  --vault /path/from/user \
  --methodology zettelkasten \
  --dry-run
```

## Frontmatter Standards

All initialized vaults include these 6 standard frontmatter properties:

```yaml
type: dot                    # Note type (auto-inferred from folder)
up: "[[Parent Note]]"        # Parent note link
created: 2025-01-15          # Creation date (YYYY-MM-DD)
daily: "[[2025-01-15]]"      # Daily note link
collection:                  # Collection classification
related:                     # Related notes
```

## Configuration Files

### validator.yaml
- Exclude paths and files
- Type inference rules (folder → note type)
- Auto-fix settings

### frontmatter.yaml
- Property definitions
- Required/optional flags
- Property types and descriptions

### note-types.yaml
- Note type definitions
- Template associations

## Next Steps After Initialization

1. **Open vault in Obsidian**
   ```bash
   open /path/to/vault
   ```

2. **Start creating notes** following methodology structure

3. **Validate frontmatter** (optional)
   ```bash
   /obsidian:validate
   ```

4. **Customize configuration** (optional)
   - Edit `.claude/config/*.yaml` files as needed

## Exit Codes

- `0` - Success
- `1` - Error (invalid methodology, permission denied, etc.)

## Error Handling

Common errors and solutions:

- **Invalid methodology** - Use `--list` to see available options
- **Permission denied** - Check directory permissions
- **Path already exists** - Script will create in existing directory (safe)

## See Also

- **Skill documentation**: `skills/init/SKILL.md`
- **Detailed README**: `skills/init/README.md`
- **Validate skill**: `/obsidian:validate`
