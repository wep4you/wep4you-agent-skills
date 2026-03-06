"""
Core data models for Obsidian vault skills.

This module provides the shared dataclasses used across skills:
- NoteTypeConfig: Configuration for a single note type
- Settings: User settings loaded from settings.yaml
- ValidationRules: Validation rules from settings
- WizardConfig: Configuration collected from wizard flows
"""

from skills.core.models.note_type import NoteTypeConfig
from skills.core.models.settings import Settings, ValidationRules
from skills.core.models.wizard import WizardConfig

__all__ = [
    "NoteTypeConfig",
    "Settings",
    "ValidationRules",
    "WizardConfig",
]
