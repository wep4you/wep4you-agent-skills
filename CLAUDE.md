# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

> **Primary documentation**: See [AGENTS.md](AGENTS.md) for complete project instructions, commands, and workflows.

## Claude-Specific Notes

- Use `uv run` for all Python commands (not `python` directly)
- Prefer parallel tool calls when operations are independent
- Use the Task tool with `subagent_type=Explore` for codebase exploration
- Always run `bd sync` before ending a session

## Development Workflow: TDD + Beads + SubAgents

### 1. TDD - Test Driven Development (MANDATORY)

**JEDER Task MUSS diesem Zyklus folgen:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. RED:   Tests ZUERST schreiben → Tests MÜSSEN FEHLSCHLAGEN │
│  2. GREEN: Code implementieren → NUR bis Tests grün sind     │
│  3. REFACTOR: Code verbessern → Tests bleiben grün           │
└─────────────────────────────────────────────────────────────┘
```

**Regeln:**
- Tests ZUERST - kein Code ohne vorherige Tests
- Tests MÜSSEN initial fehlschlagen - grüne Tests bei Erstellung = falsche Tests
- Terminal UND Claude Code Modi müssen getestet werden
- Keine Shortcuts - TDD wird NICHT übersprungen

### 2. Beads - Task Planning & Tracking

**Verwende Beads für:**
- Multi-Session Tasks
- Tasks mit Dependencies
- Entdeckte Arbeit während Implementation

**Bead-Struktur für autonome SubAgents:**
```markdown
## Ziel
[Klares, messbares Ziel]

## TDD - Tests ZUERST
[Konkrete Test-Cases die zu erstellen sind]

## Zu erstellen / Zu ändern
[Tabelle mit Dateien und Änderungen]

## Erfolgskriterien
[Checkboxen mit verifizierbaren Kriterien]

## Ralph-Wiggum Start
[Vollständiger Befehl mit --max-iterations 20]
```

### 3. SubAgent-Steuerung

**Prinzip:** Main-Agent steuert nur, SubAgents arbeiten.

```
Main Agent (Orchestrierung)
├── bd ready → Nächsten Bead holen
├── bd show <id> → Details prüfen
├── /ralph-wiggum:ralph-loop "..." → SubAgent starten
│   └── SubAgent arbeitet autonom (max 20 Iterations)
│       └── Output: <promise>BEAD X DONE</promise>
├── bd close <id> → Bead abschliessen
└── Weiter zum nächsten Bead
```

**Regeln für Main-Agent:**
1. KEINE Code-Änderungen im Main-Agent - nur Steuerung
2. Beads müssen ALLE Infos für autonomen SubAgent enthalten
3. Nach jedem Bead: `bd close <id>` + kurze Zusammenfassung

## Quick Reference

```bash
# Essential commands
uv sync --all-extras        # Install dependencies
uv run pytest               # Run tests
uv run ruff check .         # Lint
bd ready                    # Find work
bd sync                     # Sync issues
```

For full documentation, architecture, and workflows, see [AGENTS.md](AGENTS.md).

## Ralph-Wiggum Usage (WICHTIG)

When using Ralph-Wiggum loops, **both** the `--completion-promise` flag AND the `<promise>` tag in the prompt are required:

```bash
# CORRECT - Promise flag matches promise tag text
/ralph-wiggum:ralph-loop "Do task X. When done, output <promise>TASK DONE</promise>" --completion-promise "TASK DONE" --max-iterations 20

# WRONG - Missing --completion-promise flag (runs infinitely!)
/ralph-wiggum:ralph-loop "Do task X. Output <promise>TASK DONE</promise> when done."

# WRONG - Promise text doesn't match flag
/ralph-wiggum:ralph-loop "Output <promise>COMPLETE</promise>" --completion-promise "DONE"
```

**Key rules:**
1. Always set `--completion-promise "TEXT"` flag
2. The TEXT must exactly match what's between `<promise>TEXT</promise>` in prompt
3. Always set `--max-iterations 20` (Standard für Feature-Tasks)
4. Use short, unique promise texts (e.g., "BEAD 1 DONE", "TESTS PASS")
