"""
Core shared modules for Obsidian vault skills.

This package provides shared dataclasses, utilities, and configuration
that are used across multiple skills to avoid code duplication.
"""

from skills.core.models import NoteTypeConfig, Settings, ValidationRules, WizardConfig

__all__ = [
    "NoteTypeConfig",
    "Settings",
    "ValidationRules",
    "WizardConfig",
]
