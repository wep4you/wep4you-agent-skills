---
description: Validate vault settings.yaml structure
argument-hint: [--vault path]
allowed-tools: Bash(uv run:*)
---

# Validate Vault Configuration

Check that `.claude/settings.yaml` is valid and complete.

## Execution

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/config/scripts/settings_loader.py" --vault . --validate
```

## Validation Checks

- Settings file exists and is valid YAML
- Required fields present (version, methodology, core_properties)
- Note types have required properties defined
- Folder hints are valid paths

## Exit Codes

- `0`: Settings are valid
- `1`: Validation errors found
