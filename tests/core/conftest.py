"""
Pytest configuration and shared fixtures for core module tests.
"""

import pytest

from skills.core.models.settings import Settings, ValidationRules
from skills.core.models.note_type import NoteTypeConfig


@pytest.fixture
def sample_validation_rules():
    """Create sample ValidationRules for testing."""
    return ValidationRules(
        require_core_properties=True,
        allow_empty_properties=["related"],
        strict_types=True,
        check_templates=True,
        check_up_links=True,
        check_inbox_no_frontmatter=True,
    )


@pytest.fixture
def sample_note_type_config():
    """Create a sample NoteTypeConfig for testing."""
    return NoteTypeConfig(
        name="Dot",
        folder="Atlas/Dots",
        required_properties=["type", "up", "created"],
        optional_properties=["related", "collection"],
        template="dot-template",
    )


@pytest.fixture
def sample_settings(sample_validation_rules, sample_note_type_config):
    """Create sample Settings for testing."""
    return Settings(
        version="1.0",
        methodology="lyt-ace",
        core_properties=["type", "up", "created"],
        note_types={"Dot": sample_note_type_config},
        validation=sample_validation_rules,
        folder_structure={
            "atlas": "Atlas",
            "dots": "Atlas/Dots",
            "maps": "Atlas/Maps",
        },
        up_links={"Atlas/Dots": "[[Home]]"},
        exclude_paths=["templates/", ".obsidian/"],
        exclude_files=[".DS_Store"],
        exclude_patterns=["*.excalidraw.md"],
        formats={"date": "YYYY-MM-DD"},
        logging={"level": "INFO"},
        raw={},
    )


@pytest.fixture
def sample_frontmatter():
    """Return sample frontmatter dictionary for testing."""
    return {
        "type": "Dot",
        "up": "[[Home]]",
        "created": "2025-01-15",
        "daily": "[[2025-01-15]]",
        "collection": ["[[Software]]"],
        "related": ["[[Python]]"],
    }


@pytest.fixture
def sample_frontmatter_yaml():
    """Return sample frontmatter as YAML string."""
    return """---
type: Dot
up: "[[Home]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection:
  - "[[Software]]"
related:
  - "[[Python]]"
---"""
