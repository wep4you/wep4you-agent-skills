#!/usr/bin/env python3
"""Tests for Config Wizard - TDD First (must fail initially)."""

import json
import subprocess
from pathlib import Path

import yaml


def test_config_edit_wizard_non_interactive(tmp_path: Path):
    """Non-interactive mode returns JSON with current config."""
    # Create test settings
    settings_path = tmp_path / ".claude" / "settings.yaml"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(yaml.dump({"methodology": "zettelkasten", "version": 1}))

    result = subprocess.run(
        ["uv", "run", "skills/config/scripts/config_wizard.py", str(settings_path)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert data["interactive_required"] is True
    assert "current_config" in data


def test_config_wizard_returns_editable_fields(tmp_path: Path):
    """Non-interactive mode returns list of editable fields."""
    settings_path = tmp_path / ".claude" / "settings.yaml"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        yaml.dump({"methodology": "zettelkasten", "version": 1, "system_prefix": "x"})
    )

    result = subprocess.run(
        ["uv", "run", "skills/config/scripts/config_wizard.py", str(settings_path)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "editable_fields" in data
    fields = data["editable_fields"]
    assert isinstance(fields, list)
    assert len(fields) >= 2


def test_config_wizard_action_field(tmp_path: Path):
    """Response should have correct action field."""
    settings_path = tmp_path / ".claude" / "settings.yaml"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(yaml.dump({"methodology": "para"}))

    result = subprocess.run(
        ["uv", "run", "skills/config/scripts/config_wizard.py", str(settings_path)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert data.get("action") == "edit_config"
