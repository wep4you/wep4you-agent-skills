#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Prompts module for vault initialization.

This module provides JSON prompt generation for Claude Code's
interactive vault initialization workflow.
"""

from __future__ import annotations

from skills.core.prompts.init_prompts import (
    build_next_step_command,
    output_abort,
    output_action_prompt,
    output_custom_properties_prompt,
    output_git_init_prompt,
    output_methodology_prompt,
    output_migrate_hint,
    output_note_types_prompt,
    output_note_types_select_prompt,
    output_per_type_properties_prompt,
    output_properties_prompt,
    output_properties_select_prompt,
    output_ranking_system_prompt,
)

__all__ = [
    "build_next_step_command",
    "output_abort",
    "output_action_prompt",
    "output_custom_properties_prompt",
    "output_git_init_prompt",
    "output_methodology_prompt",
    "output_migrate_hint",
    "output_note_types_prompt",
    "output_note_types_select_prompt",
    "output_per_type_properties_prompt",
    "output_properties_prompt",
    "output_properties_select_prompt",
    "output_ranking_system_prompt",
]
