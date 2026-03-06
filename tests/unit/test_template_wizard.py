#!/usr/bin/env python3
"""Tests for Template Wizard - TDD First (must fail initially)."""

import json
import subprocess


def test_template_create_wizard_non_interactive():
    """Non-interactive mode returns JSON guidance."""
    result = subprocess.run(
        ["uv", "run", "skills/templates/scripts/template_wizard.py", "create", "test"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    # Should return JSON even on error
    data = json.loads(result.stdout)
    assert data["interactive_required"] is True
    assert "schema" in data


def test_template_delete_wizard_non_interactive():
    """Non-interactive mode returns JSON with available templates info."""
    result = subprocess.run(
        ["uv", "run", "skills/templates/scripts/template_wizard.py", "delete"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert data["interactive_required"] is True
    # Should have either available_templates or confirm_command
    assert "available_templates" in data or "confirm_command" in data


def test_template_create_schema_has_required_fields():
    """Schema should describe name and content fields."""
    result = subprocess.run(
        ["uv", "run", "skills/templates/scripts/template_wizard.py", "create", "mytemplate"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    schema = data.get("schema", {})
    assert "name" in schema or "content" in schema


def test_template_delete_has_action_field():
    """Delete action should have action field."""
    result = subprocess.run(
        ["uv", "run", "skills/templates/scripts/template_wizard.py", "delete"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert data.get("action") == "delete_template"
