#!/usr/bin/env python3
"""Tests for Props Wizard - TDD First (must fail initially)."""

import json
import subprocess


def test_props_add_wizard_non_interactive():
    """Non-interactive mode returns JSON guidance."""
    result = subprocess.run(
        ["uv", "run", "skills/frontmatter/scripts/props_wizard.py", "add"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    # Should return JSON even on error (file not found means test properly fails)
    data = json.loads(result.stdout)
    assert data["interactive_required"] is True
    assert "schema" in data


def test_props_remove_wizard_non_interactive():
    """Non-interactive mode returns JSON with current properties."""
    result = subprocess.run(
        ["uv", "run", "skills/frontmatter/scripts/props_wizard.py", "remove"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert data["interactive_required"] is True
    assert "current_properties" in data


def test_props_wizard_add_schema_has_required_fields():
    """Schema should describe name and type fields."""
    result = subprocess.run(
        ["uv", "run", "skills/frontmatter/scripts/props_wizard.py", "add"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    schema = data.get("schema", {})
    assert "name" in schema
    assert "type" in schema


def test_props_wizard_remove_lists_removable_properties():
    """Remove action should list properties that can be removed."""
    result = subprocess.run(
        ["uv", "run", "skills/frontmatter/scripts/props_wizard.py", "remove"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    props = data.get("current_properties", [])
    # Should be a list (even if empty)
    assert isinstance(props, list)
