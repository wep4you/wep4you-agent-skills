"""
Pytest configuration and shared fixtures
"""

import sys
from pathlib import Path

import pytest


def pytest_configure(config):
    """Add skills scripts and scripts to Python path for imports"""
    base = Path(__file__).parent.parent

    # Add validate scripts
    skills_path = base / "skills" / "validate" / "scripts"
    if str(skills_path) not in sys.path:
        sys.path.insert(0, str(skills_path))

    # Add main scripts directory
    scripts_path = base / "scripts"
    if str(scripts_path) not in sys.path:
        sys.path.insert(0, str(scripts_path))


@pytest.fixture
def sample_vault(tmp_path):
    """Create a sample vault structure for testing"""
    # Create vault directories
    (tmp_path / "Atlas" / "Dots").mkdir(parents=True)
    (tmp_path / "Atlas" / "Maps").mkdir(parents=True)
    (tmp_path / "Calendar" / "daily" / "2025" / "01").mkdir(parents=True)
    (tmp_path / ".claude" / "config").mkdir(parents=True)

    return tmp_path


@pytest.fixture
def valid_note_content():
    """Return valid note frontmatter content"""
    return """---
type: Dot
up: "[[Home]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection:
  - "[[Software]]"
related:
  - "[[Python]]"
---

# Valid Note

This note has all required properties.
"""


@pytest.fixture
def invalid_note_content():
    """Return invalid note frontmatter content"""
    return """---
title: Should Not Exist
type:
up: [[Unquoted Link]]
created: [[2025-01-15]]
daily: "[[2025-01-20]]"
---

# Invalid Note

This note has multiple issues.
"""
