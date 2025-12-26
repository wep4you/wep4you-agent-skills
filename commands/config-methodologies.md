---
description: List available vault methodologies (LYT-ACE, PARA, Zettelkasten, Minimal)
argument-hint: [methodology-name]
allowed-tools: Bash(uv run:*)
---

# Show Available Methodologies

Display available vault methodologies from YAML definitions.

## Execution

### List all methodologies

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/config/methodologies/loader.py"
```

### Show specific methodology details

If a methodology name is provided as argument:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/config/methodologies/loader.py" $1
```

## Available Methodologies

| Name | Description |
|------|-------------|
| `lyt-ace` | LYT + ACE Framework - Linking Your Thinking with Atlas/Calendar/Efforts |
| `para` | PARA Method - Projects, Areas, Resources, Archives |
| `zettelkasten` | Zettelkasten - Slip-box note-taking system |
| `minimal` | Minimal - Simple note organization |

## Output

Without argument - lists all methodologies with name and description.

With argument - shows detailed info:
- Name and description
- Folders to create
- Core properties
- Note types with their configurations

## Examples

```bash
# List all
obsidian:config-methodologies

# Show PARA details
obsidian:config-methodologies para

# Show LYT-ACE details
obsidian:config-methodologies lyt-ace
```
