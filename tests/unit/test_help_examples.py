"""Tests for help_command.py examples - Bug fixes validation.

Tests for ACCURATE documentation:
- Bug 80w: types show should use <name> not methodology-specific types
- Bug 78b: props add/remove - NO wizard exists, document --yes flag
- Bug esw: templates create/delete - NO wizard exists, document --yes/--content
- Bug ouo: config edit/create - NO wizard exists, document actual behavior

IMPORTANT: props, templates, config do NOT have wizards!
Only types and init have actual interactive wizards.
"""

import sys
from pathlib import Path

# Add skills directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "obsidian_commands"))

from help_command import find_command, find_subcommand


class TestBug80wTypesShowExample:
    """Bug 80w: types show should use methodology-agnostic examples."""

    def test_types_show_does_not_use_methodology_specific_type(self):
        """types show example should not use 'map' which is LYT-ACE specific."""
        cmd = find_command("types")
        assert cmd is not None

        show_subcmd = find_subcommand(cmd, "show")
        assert show_subcmd is not None

        # Check that no example uses 'map' as it's methodology-specific
        for example in show_subcmd.examples:
            assert "map" not in example.lower(), (
                f"Example uses methodology-specific type 'map': {example}"
            )

    def test_types_show_uses_placeholder(self):
        """types show example should use <name> placeholder."""
        cmd = find_command("types")
        show_subcmd = find_subcommand(cmd, "show")

        # Should use <name> placeholder for generic examples
        has_placeholder = any("<name>" in example for example in show_subcmd.examples)

        assert has_placeholder, (
            f"No example uses <name> placeholder. Examples: {show_subcmd.examples}"
        )


class TestBug78bPropsNOWizard:
    """Bug 78b: props add/remove have NO wizard - document --yes flag instead."""

    def test_props_add_does_not_claim_wizard(self):
        """props add should NOT claim to have a wizard (none exists)."""
        cmd = find_command("props")
        assert cmd is not None

        add_subcmd = find_subcommand(cmd, "add")
        assert add_subcmd is not None

        # Should NOT claim wizard exists
        assert "wizard" not in add_subcmd.description.lower(), (
            f"props add falsely claims wizard: {add_subcmd.description}"
        )

    def test_props_add_documents_yes_flag(self):
        """props add should document --yes flag for non-interactive use."""
        cmd = find_command("props")
        add_subcmd = find_subcommand(cmd, "add")

        # Description or examples should mention --yes
        mentions_yes = "--yes" in add_subcmd.description.lower() or any(
            "--yes" in ex for ex in add_subcmd.examples
        )

        assert mentions_yes, f"props add should document --yes flag. Desc: {add_subcmd.description}"

    def test_props_remove_does_not_claim_wizard(self):
        """props remove should NOT claim to have a wizard (none exists)."""
        cmd = find_command("props")
        remove_subcmd = find_subcommand(cmd, "remove")
        assert remove_subcmd is not None

        assert "wizard" not in remove_subcmd.description.lower(), (
            f"props remove falsely claims wizard: {remove_subcmd.description}"
        )

    def test_props_remove_documents_yes_flag(self):
        """props remove should document --yes flag for non-interactive use."""
        cmd = find_command("props")
        remove_subcmd = find_subcommand(cmd, "remove")

        mentions_yes = "--yes" in remove_subcmd.description.lower() or any(
            "--yes" in ex for ex in remove_subcmd.examples
        )

        assert mentions_yes, (
            f"props remove should document --yes flag. Desc: {remove_subcmd.description}"
        )


class TestBugEswTemplatesNOWizard:
    """Bug esw: templates create/delete have NO wizard - document flags instead."""

    def test_templates_create_does_not_claim_wizard(self):
        """templates create should NOT claim to have a wizard (none exists)."""
        cmd = find_command("templates")
        assert cmd is not None

        create_subcmd = find_subcommand(cmd, "create")
        assert create_subcmd is not None

        assert "wizard" not in create_subcmd.description.lower(), (
            f"templates create falsely claims wizard: {create_subcmd.description}"
        )

    def test_templates_create_documents_content_flag(self):
        """templates create should document --content for non-interactive use."""
        cmd = find_command("templates")
        create_subcmd = find_subcommand(cmd, "create")

        mentions_content = "--content" in create_subcmd.description.lower() or any(
            "--content" in ex for ex in create_subcmd.examples
        )

        assert mentions_content, (
            f"templates create should document --content. Desc: {create_subcmd.description}"
        )

    def test_templates_edit_documents_editor(self):
        """templates edit should document that it opens system editor."""
        cmd = find_command("templates")
        edit_subcmd = find_subcommand(cmd, "edit")
        assert edit_subcmd is not None

        # Should mention "editor" not "wizard"
        mentions_editor = "editor" in edit_subcmd.description.lower()
        has_wizard = "wizard" in edit_subcmd.description.lower()

        assert mentions_editor and not has_wizard, (
            f"templates edit should say 'editor' not 'wizard'. Desc: {edit_subcmd.description}"
        )

    def test_templates_delete_does_not_claim_wizard(self):
        """templates delete should NOT claim to have a wizard (none exists)."""
        cmd = find_command("templates")
        delete_subcmd = find_subcommand(cmd, "delete")
        assert delete_subcmd is not None

        assert "wizard" not in delete_subcmd.description.lower(), (
            f"templates delete falsely claims wizard: {delete_subcmd.description}"
        )

    def test_templates_delete_documents_yes_flag(self):
        """templates delete should document --yes for non-interactive use."""
        cmd = find_command("templates")
        delete_subcmd = find_subcommand(cmd, "delete")

        mentions_yes = "--yes" in delete_subcmd.description.lower() or any(
            "--yes" in ex for ex in delete_subcmd.examples
        )

        assert mentions_yes, (
            f"templates delete should document --yes. Desc: {delete_subcmd.description}"
        )


class TestBugOuoConfigNOWizard:
    """Bug ouo: config edit/create have NO wizard - document actual behavior."""

    def test_config_edit_does_not_claim_wizard(self):
        """config edit should NOT claim to have a wizard (none exists)."""
        cmd = find_command("config")
        assert cmd is not None

        edit_subcmd = find_subcommand(cmd, "edit")
        assert edit_subcmd is not None

        assert "wizard" not in edit_subcmd.description.lower(), (
            f"config edit falsely claims wizard: {edit_subcmd.description}"
        )

    def test_config_edit_documents_editor(self):
        """config edit should document that it opens system editor."""
        cmd = find_command("config")
        edit_subcmd = find_subcommand(cmd, "edit")

        mentions_editor = "editor" in edit_subcmd.description.lower()

        assert mentions_editor, (
            f"config edit should mention editor. Desc: {edit_subcmd.description}"
        )

    def test_config_create_does_not_claim_wizard(self):
        """config create should NOT claim to have a wizard (none exists)."""
        cmd = find_command("config")
        create_subcmd = find_subcommand(cmd, "create")
        assert create_subcmd is not None

        assert "wizard" not in create_subcmd.description.lower(), (
            f"config create falsely claims wizard: {create_subcmd.description}"
        )

    def test_config_create_documents_methodology_flag(self):
        """config create should document --methodology flag."""
        cmd = find_command("config")
        create_subcmd = find_subcommand(cmd, "create")

        mentions_methodology = any("--methodology" in ex for ex in create_subcmd.examples)

        assert mentions_methodology, (
            f"config create should show --methodology. Examples: {create_subcmd.examples}"
        )


class TestTypesHasRealWizard:
    """Verify that types command correctly documents its REAL wizard."""

    def test_types_wizard_subcommand_exists(self):
        """types should have a wizard subcommand (it's a real wizard)."""
        cmd = find_command("types")
        assert cmd is not None

        wizard_subcmd = find_subcommand(cmd, "wizard")
        assert wizard_subcmd is not None, "types wizard subcommand should exist"

    def test_types_add_mentions_wizard_option(self):
        """types add should mention wizard as an option (bare command)."""
        cmd = find_command("types")
        add_subcmd = find_subcommand(cmd, "add")
        assert add_subcmd is not None

        # types add without args runs wizard - this should be documented
        has_bare_example = any(
            ex.strip().endswith("obsidian:types add") for ex in add_subcmd.examples
        )

        assert has_bare_example, (
            f"types add should show bare command example. Examples: {add_subcmd.examples}"
        )
