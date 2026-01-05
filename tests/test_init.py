"""
Tests for init skill

Run with: uv run pytest tests/test_init.py -v
Coverage: uv run pytest tests/test_init.py -v --cov=skills/init --cov-report=term-missing
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Add skills directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "init" / "scripts"))

# Import after path modification
from init_vault import (
    METHODOLOGIES,
    NoteTypeConfig,
    WizardConfig,
    apply_ranking_system,
    build_settings_yaml,
    choose_methodology_interactive,
    create_agent_docs,
    create_folder_structure,
    create_gitignore,
    create_home_note,
    create_readme,
    create_sample_notes,
    create_settings_yaml,
    detect_existing_vault,
    generate_agents_md,
    generate_claude_md,
    generate_sample_note,
    init_git_repo,
    init_vault,
    main,
    print_methodologies,
    reset_vault,
    show_migration_hint,
    wizard_step_confirm,
    wizard_step_custom_note_types,
    wizard_step_frontmatter,
    wizard_step_git_init,
    wizard_step_note_types,
    wizard_step_per_type_properties,
    wizard_step_quick_or_custom,
    wizard_step_ranking_system,
)


class TestMethodologies:
    """Test methodology definitions"""

    def test_all_methodologies_have_required_fields(self) -> None:
        """Test that all methodologies have required fields"""
        required_fields = ["name", "description", "folders", "core_properties", "note_types"]
        for key, method in METHODOLOGIES.items():
            for field in required_fields:
                assert field in method, f"Methodology {key} missing field: {field}"

    def test_methodologies_have_unique_names(self) -> None:
        """Test that all methodology names are unique"""
        names = [m["name"] for m in METHODOLOGIES.values()]
        assert len(names) == len(set(names)), "Duplicate methodology names found"

    def test_methodologies_have_folders(self) -> None:
        """Test that all methodologies define folders"""
        for key, method in METHODOLOGIES.items():
            assert len(method["folders"]) > 0, f"Methodology {key} has no folders"

    def test_methodologies_have_note_types(self) -> None:
        """Test that all methodologies define note types"""
        for key, method in METHODOLOGIES.items():
            assert len(method["note_types"]) > 0, f"Methodology {key} has no note types"

    def test_lyt_ace_structure(self) -> None:
        """Test LYT-ACE methodology structure"""
        lyt_ace = METHODOLOGIES["lyt-ace"]
        assert lyt_ace["name"] == "LYT + ACE Framework"
        assert "Atlas/Maps" in lyt_ace["folders"]
        assert "Atlas/Dots" in lyt_ace["folders"]
        assert "Calendar/daily" in lyt_ace["folders"]
        assert "Efforts/Projects" in lyt_ace["folders"]
        # Check note types
        assert "map" in lyt_ace["note_types"]
        assert "dot" in lyt_ace["note_types"]
        assert lyt_ace["note_types"]["map"]["folder_hints"] == ["Atlas/Maps/"]

    def test_para_structure(self) -> None:
        """Test PARA methodology structure"""
        para = METHODOLOGIES["para"]
        assert para["name"] == "PARA Method"
        assert "Projects" in para["folders"]
        assert "Areas" in para["folders"]
        assert "Resources" in para["folders"]
        assert "Archives" in para["folders"]
        assert "project" in para["note_types"]

    def test_zettelkasten_structure(self) -> None:
        """Test Zettelkasten methodology structure"""
        zettel = METHODOLOGIES["zettelkasten"]
        assert zettel["name"] == "Zettelkasten"
        assert "Permanent" in zettel["folders"]
        assert "Literature" in zettel["folders"]
        assert "Fleeting" in zettel["folders"]
        assert "permanent" in zettel["note_types"]

    def test_minimal_structure(self) -> None:
        """Test Minimal methodology structure"""
        minimal = METHODOLOGIES["minimal"]
        assert minimal["name"] == "Minimal"
        assert "Notes" in minimal["folders"]
        assert "Daily" in minimal["folders"]
        assert "note" in minimal["note_types"]


class TestPrintMethodologies:
    """Test methodology printing"""

    def test_print_methodologies_output(self, capsys: pytest.CaptureFixture) -> None:
        """Test that print_methodologies produces output"""
        print_methodologies()
        captured = capsys.readouterr()
        assert "Available methodologies" in captured.out
        assert "lyt-ace" in captured.out
        assert "para" in captured.out
        assert "zettelkasten" in captured.out
        assert "minimal" in captured.out


class TestChooseMethodologyInteractive:
    """Test interactive methodology selection"""

    def test_choose_valid_methodology(self) -> None:
        """Test choosing a valid methodology interactively"""
        with patch("builtins.input", return_value="para"):
            result = choose_methodology_interactive()
            assert result == "para"

    def test_choose_retry_on_invalid(self) -> None:
        """Test retry on invalid methodology choice"""
        with patch("builtins.input", side_effect=["invalid", "lyt-ace"]):
            result = choose_methodology_interactive()
            assert result == "lyt-ace"

    def test_choose_case_insensitive(self) -> None:
        """Test that methodology choice is case-insensitive"""
        with patch("builtins.input", return_value="LYT-ACE"):
            result = choose_methodology_interactive()
            assert result == "lyt-ace"

    def test_choose_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from input"""
        with patch("builtins.input", return_value="  para  "):
            result = choose_methodology_interactive()
            assert result == "para"


class TestCreateFolderStructure:
    """Test folder structure creation"""

    def test_create_lyt_ace_folders(self, tmp_path: Path) -> None:
        """Test creating LYT-ACE folder structure"""
        create_folder_structure(tmp_path, "lyt-ace", dry_run=False)

        assert (tmp_path / "Atlas" / "Maps").exists()
        assert (tmp_path / "Atlas" / "Dots").exists()
        assert (tmp_path / "Atlas" / "Sources").exists()
        assert (tmp_path / "Calendar" / "daily").exists()
        assert (tmp_path / "Efforts" / "Projects").exists()
        assert (tmp_path / "Efforts" / "Areas").exists()
        assert (tmp_path / ".obsidian").exists()
        assert (tmp_path / ".claude").exists()

    def test_create_para_folders(self, tmp_path: Path) -> None:
        """Test creating PARA folder structure"""
        create_folder_structure(tmp_path, "para", dry_run=False)

        assert (tmp_path / "Projects").exists()
        assert (tmp_path / "Areas").exists()
        assert (tmp_path / "Resources").exists()
        assert (tmp_path / "Archives").exists()
        assert (tmp_path / ".obsidian").exists()

    def test_create_zettelkasten_folders(self, tmp_path: Path) -> None:
        """Test creating Zettelkasten folder structure"""
        create_folder_structure(tmp_path, "zettelkasten", dry_run=False)

        assert (tmp_path / "Permanent").exists()
        assert (tmp_path / "Literature").exists()
        assert (tmp_path / "Fleeting").exists()
        assert (tmp_path / "References").exists()

    def test_create_minimal_folders(self, tmp_path: Path) -> None:
        """Test creating minimal folder structure"""
        create_folder_structure(tmp_path, "minimal", dry_run=False)

        assert (tmp_path / "Notes").exists()
        assert (tmp_path / "Daily").exists()

    def test_create_folders_dry_run(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't create folders"""
        create_folder_structure(tmp_path, "para", dry_run=True)

        assert not (tmp_path / "Projects").exists()
        assert not (tmp_path / "Areas").exists()

    def test_create_folders_invalid_methodology(self, tmp_path: Path) -> None:
        """Test error on invalid methodology"""
        with pytest.raises(ValueError, match="Unknown methodology"):
            create_folder_structure(tmp_path, "invalid", dry_run=False)

    def test_create_folders_idempotent(self, tmp_path: Path) -> None:
        """Test that creating folders twice is safe"""
        create_folder_structure(tmp_path, "minimal", dry_run=False)
        create_folder_structure(tmp_path, "minimal", dry_run=False)  # Should not error

        assert (tmp_path / "Notes").exists()


class TestBuildSettingsYaml:
    """Test settings.yaml content building"""

    def test_build_settings_has_required_keys(self) -> None:
        """Test that built settings has all required keys"""
        settings = build_settings_yaml("lyt-ace")

        assert "version" in settings
        assert "methodology" in settings
        assert "core_properties" in settings
        assert "note_types" in settings
        assert "validation" in settings
        assert "exclude" in settings

    def test_build_settings_methodology_specific(self) -> None:
        """Test that settings are methodology-specific"""
        lyt_settings = build_settings_yaml("lyt-ace")
        para_settings = build_settings_yaml("para")

        assert lyt_settings["methodology"] == "lyt-ace"
        assert para_settings["methodology"] == "para"
        assert "map" in lyt_settings["note_types"]
        assert "project" in para_settings["note_types"]

    def test_build_settings_core_properties(self) -> None:
        """Test that core_properties are set correctly"""
        settings = build_settings_yaml("lyt-ace")

        # core_properties is now a dict with 'all' key containing the list
        assert "all" in settings["core_properties"]
        assert "type" in settings["core_properties"]["all"]
        assert "up" in settings["core_properties"]["all"]
        assert "created" in settings["core_properties"]["all"]


class TestCreateSettingsYaml:
    """Test settings.yaml file creation"""

    def test_create_settings_yaml(self, tmp_path: Path) -> None:
        """Test settings.yaml creation"""
        create_settings_yaml(tmp_path, "lyt-ace", dry_run=False)

        settings_path = tmp_path / ".claude" / "settings.yaml"
        assert settings_path.exists()

        config = yaml.safe_load(settings_path.read_text())
        assert config["version"] == "1.0"
        assert config["methodology"] == "lyt-ace"
        assert "note_types" in config
        assert "map" in config["note_types"]

    def test_create_settings_dry_run(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't create settings file"""
        create_settings_yaml(tmp_path, "para", dry_run=True)

        settings_path = tmp_path / ".claude" / "settings.yaml"
        assert not settings_path.exists()

    def test_settings_has_header(self, tmp_path: Path) -> None:
        """Test that settings.yaml has header comments"""
        create_settings_yaml(tmp_path, "minimal", dry_run=False)

        content = (tmp_path / ".claude" / "settings.yaml").read_text()
        assert "PRIMARY source of truth" in content

    def test_settings_exclude_paths(self, tmp_path: Path) -> None:
        """Test that settings has exclude paths"""
        create_settings_yaml(tmp_path, "minimal", dry_run=False)

        config = yaml.safe_load((tmp_path / ".claude" / "settings.yaml").read_text())
        assert "+/" in config["exclude"]["paths"]
        assert ".obsidian/" in config["exclude"]["paths"]

    def test_settings_validation_config(self, tmp_path: Path) -> None:
        """Test that settings has validation configuration"""
        create_settings_yaml(tmp_path, "para", dry_run=False)

        config = yaml.safe_load((tmp_path / ".claude" / "settings.yaml").read_text())
        assert config["validation"]["require_core_properties"] is True
        assert "allow_empty_properties" in config["validation"]


class TestCreateReadme:
    """Test README creation"""

    def test_create_readme(self, tmp_path: Path) -> None:
        """Test README.md creation"""
        create_readme(tmp_path, "para", dry_run=False)

        readme_path = tmp_path / "README.md"
        assert readme_path.exists()

        content = readme_path.read_text()
        assert "PARA Method" in content
        assert "Projects" in content
        assert "Areas" in content
        assert "settings.yaml" in content

    def test_readme_dry_run(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't create README"""
        create_readme(tmp_path, "minimal", dry_run=True)

        assert not (tmp_path / "README.md").exists()

    def test_readme_has_methodology_info(self, tmp_path: Path) -> None:
        """Test README contains methodology information"""
        create_readme(tmp_path, "lyt-ace", dry_run=False)

        content = (tmp_path / "README.md").read_text()
        assert "LYT + ACE Framework" in content
        assert "Atlas/Maps" in content

    def test_readme_has_validation_commands(self, tmp_path: Path) -> None:
        """Test README contains validation commands"""
        create_readme(tmp_path, "zettelkasten", dry_run=False)

        content = (tmp_path / "README.md").read_text()
        assert "/obsidian:validate" in content


class TestCreateHomeNote:
    """Test HOME.md creation"""

    def test_create_home_note(self, tmp_path: Path) -> None:
        """Test HOME.md creation"""
        create_home_note(tmp_path, "lyt-ace", dry_run=False)

        home_path = tmp_path / "HOME.md"
        assert home_path.exists()

        content = home_path.read_text()
        assert "LYT + ACE Framework" in content
        assert "type: map" in content
        # Verify date is properly substituted (not {{date}})
        assert "{{date}}" not in content
        assert "created:" in content

    def test_home_note_dry_run(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't create HOME.md"""
        create_home_note(tmp_path, "minimal", dry_run=True)

        assert not (tmp_path / "HOME.md").exists()


class TestInitVault:
    """Test complete vault initialization"""

    def test_init_vault_lyt_ace(self, tmp_path: Path) -> None:
        """Test complete LYT-ACE vault initialization"""
        vault_path = tmp_path / "test-vault"
        init_vault(vault_path, "lyt-ace", dry_run=False)

        # Check folders
        assert (vault_path / "Atlas" / "Maps").exists()
        assert (vault_path / ".obsidian").exists()

        # Check settings.yaml (PRIMARY config)
        assert (vault_path / ".claude" / "settings.yaml").exists()

        # Check README and HOME
        assert (vault_path / "README.md").exists()
        assert (vault_path / "HOME.md").exists()

    def test_init_vault_para(self, tmp_path: Path) -> None:
        """Test complete PARA vault initialization"""
        vault_path = tmp_path / "para-vault"
        init_vault(vault_path, "para", dry_run=False)

        assert (vault_path / "Projects").exists()
        assert (vault_path / "README.md").exists()
        assert (vault_path / ".claude" / "settings.yaml").exists()

    def test_init_vault_dry_run(self, tmp_path: Path) -> None:
        """Test dry-run doesn't create vault"""
        vault_path = tmp_path / "dry-vault"
        init_vault(vault_path, "minimal", dry_run=True)

        # Vault directory itself shouldn't be created in dry-run
        if vault_path.exists():
            # If it exists, it should be empty
            assert not (vault_path / "Notes").exists()

    def test_init_vault_creates_directory(self, tmp_path: Path) -> None:
        """Test that init creates vault directory if it doesn't exist"""
        vault_path = tmp_path / "new-vault"
        assert not vault_path.exists()

        init_vault(vault_path, "minimal", dry_run=False)

        assert vault_path.exists()
        assert (vault_path / "Notes").exists()

    def test_init_vault_interactive_mode(self, tmp_path: Path) -> None:
        """Test interactive mode (methodology=None)"""
        vault_path = tmp_path / "interactive-vault"

        with patch("builtins.input", return_value="para"):
            init_vault(vault_path, methodology=None, dry_run=False)

        assert (vault_path / "Projects").exists()


class TestMainCLI:
    """Test CLI main function"""

    def test_main_with_methodology(self, tmp_path: Path) -> None:
        """Test main function with methodology flag (simulating wrapper call)"""
        vault_path = tmp_path / "cli-vault"
        args = [str(vault_path), "-m", "minimal", "--defaults"]

        # Set env to simulate wrapper call
        with patch.dict("os.environ", {"INIT_FROM_WRAPPER": "1"}):
            with patch("sys.argv", ["init_vault.py", *args]):
                exit_code = main()

        assert exit_code == 0
        assert (vault_path / "Notes").exists()

    def test_main_list_methodologies(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --list flag"""
        args = ["--list"]

        with patch("sys.argv", ["init_vault.py", *args]):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "lyt-ace" in captured.out
        assert "para" in captured.out

    def test_main_dry_run(self, tmp_path: Path) -> None:
        """Test --dry-run flag (simulating wrapper call)"""
        vault_path = tmp_path / "dry-cli-vault"
        args = [str(vault_path), "-m", "para", "--dry-run", "--defaults"]

        # Set env to simulate wrapper call
        with patch.dict("os.environ", {"INIT_FROM_WRAPPER": "1"}):
            with patch("sys.argv", ["init_vault.py", *args]):
                exit_code = main()

        assert exit_code == 0
        # Should not create folders in dry-run
        if vault_path.exists():
            assert not (vault_path / "Projects").exists()

    def test_main_interactive(self, tmp_path: Path) -> None:
        """Test interactive mode via CLI (wizard mode)"""
        vault_path = tmp_path / "interactive-cli"
        args = [str(vault_path), "--wizard"]

        # Mock is_interactive to return True and the full wizard flow
        # Input sequence: methodology, setup mode, ranking system, git init, confirm
        with patch("sys.argv", ["init_vault.py", *args]):
            with patch("init_vault.is_interactive", return_value=True):
                with patch("builtins.input", side_effect=["zettelkasten", "q", "r", "n", "y"]):
                    exit_code = main()

        assert exit_code == 0
        assert (vault_path / "Permanent").exists()

    def test_main_error_handling(self, tmp_path: Path) -> None:
        """Test error handling in main"""
        vault_path = tmp_path / "error-vault"
        args = [str(vault_path), "-m", "invalid"]

        # Set env to simulate wrapper call, so we get to argparse validation
        with patch.dict("os.environ", {"INIT_FROM_WRAPPER": "1"}):
            # argparse calls sys.exit(2) on invalid choice
            with patch("sys.argv", ["init_vault.py", *args]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 2  # argparse error exit code


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_existing_vault_safe(self, tmp_path: Path) -> None:
        """Test initializing into existing directory is safe"""
        vault_path = tmp_path / "existing"
        vault_path.mkdir()
        (vault_path / "existing-file.md").write_text("# Existing")

        # Use defaults to skip the interactive prompt for existing vault
        init_vault(vault_path, "minimal", dry_run=False, use_defaults=True)

        # Should create new folders without destroying existing file
        assert (vault_path / "existing-file.md").exists()
        assert (vault_path / "Notes").exists()

    def test_unicode_vault_path(self, tmp_path: Path) -> None:
        """Test vault path with unicode characters"""
        vault_path = tmp_path / "テスト-vault"
        init_vault(vault_path, "minimal", dry_run=False)

        assert (vault_path / "Notes").exists()

    def test_spaces_in_path(self, tmp_path: Path) -> None:
        """Test vault path with spaces"""
        vault_path = tmp_path / "My Vault"
        init_vault(vault_path, "minimal", dry_run=False)

        assert (vault_path / "Notes").exists()


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_lyt_ace_workflow(self, tmp_path: Path) -> None:
        """Test complete LYT-ACE vault setup and verification"""
        vault_path = tmp_path / "lyt-integration"

        # Initialize vault
        init_vault(vault_path, "lyt-ace", dry_run=False)

        # Verify all components
        assert (vault_path / "Atlas" / "Maps").exists()
        assert (vault_path / "Atlas" / "Dots").exists()
        assert (vault_path / "Calendar" / "daily").exists()
        assert (vault_path / "Efforts" / "Projects").exists()

        # Verify settings.yaml is valid YAML with correct structure
        settings = yaml.safe_load((vault_path / ".claude" / "settings.yaml").read_text())
        assert settings["methodology"] == "lyt-ace"
        assert "map" in settings["note_types"]
        # core_properties is now a dict with 'all' key containing the list
        assert "type" in settings["core_properties"]["all"]

        # Verify README
        readme = (vault_path / "README.md").read_text()
        assert "Atlas/Maps" in readme

    def test_all_methodologies_initialize(self, tmp_path: Path) -> None:
        """Test that all methodologies can be initialized"""
        for methodology_key in METHODOLOGIES.keys():
            vault_path = tmp_path / f"test-{methodology_key}"
            init_vault(vault_path, methodology_key, dry_run=False)

            # Verify at least basic structure exists
            assert vault_path.exists()
            assert (vault_path / ".claude" / "settings.yaml").exists()
            assert (vault_path / "README.md").exists()

    def test_settings_yaml_is_valid(self, tmp_path: Path) -> None:
        """Test that generated settings.yaml is valid and parseable"""
        for methodology_key in METHODOLOGIES.keys():
            vault_path = tmp_path / f"yaml-test-{methodology_key}"
            init_vault(vault_path, methodology_key, dry_run=False)

            # Parse and validate settings
            settings = yaml.safe_load((vault_path / ".claude" / "settings.yaml").read_text())

            # Check required fields
            assert settings["version"] == "1.0"
            assert settings["methodology"] == methodology_key
            # core_properties is now a dict with 'all' key containing the list
            assert isinstance(settings["core_properties"], dict)
            assert "all" in settings["core_properties"]
            assert isinstance(settings["core_properties"]["all"], list)
            assert isinstance(settings["note_types"], dict)
            assert isinstance(settings["validation"], dict)


class TestDetectExistingVault:
    """Tests for vault detection"""

    def test_detect_nonexistent_vault(self, tmp_path: Path) -> None:
        """Test detection of non-existent vault"""
        vault_path = tmp_path / "nonexistent"
        result = detect_existing_vault(vault_path)

        assert result["exists"] is False
        assert result["has_obsidian"] is False
        assert result["has_content"] is False

    def test_detect_empty_vault(self, tmp_path: Path) -> None:
        """Test detection of empty vault"""
        vault_path = tmp_path / "empty"
        vault_path.mkdir()
        result = detect_existing_vault(vault_path)

        assert result["exists"] is True
        assert result["has_content"] is False
        assert result["folder_count"] == 0

    def test_detect_obsidian_vault(self, tmp_path: Path) -> None:
        """Test detection of Obsidian vault"""
        vault_path = tmp_path / "obsidian"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        result = detect_existing_vault(vault_path)

        assert result["has_obsidian"] is True

    def test_detect_claude_config(self, tmp_path: Path) -> None:
        """Test detection of Claude configuration"""
        vault_path = tmp_path / "claude"
        vault_path.mkdir()
        (vault_path / ".claude").mkdir()
        result = detect_existing_vault(vault_path)

        assert result["has_claude_config"] is True

    def test_detect_content(self, tmp_path: Path) -> None:
        """Test detection of existing content"""
        vault_path = tmp_path / "content"
        vault_path.mkdir()
        (vault_path / "Notes").mkdir()
        (vault_path / "test.md").write_text("# Test")
        result = detect_existing_vault(vault_path)

        assert result["has_content"] is True
        assert result["folder_count"] == 1
        assert result["file_count"] == 1


class TestResetVault:
    """Tests for vault reset functionality"""

    def test_reset_removes_content(self, tmp_path: Path) -> None:
        """Test that reset removes all content except protected folders"""
        vault_path = tmp_path / "reset"
        vault_path.mkdir()
        (vault_path / "Notes").mkdir()
        (vault_path / "test.md").write_text("# Test")

        reset_vault(vault_path)

        assert not (vault_path / "Notes").exists()
        assert not (vault_path / "test.md").exists()

    def test_reset_keeps_protected_folders(self, tmp_path: Path) -> None:
        """Test that reset keeps all protected folders (.obsidian, .git, .github, .vscode)"""
        vault_path = tmp_path / "keep-protected"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / ".git").mkdir()
        (vault_path / ".github").mkdir()
        (vault_path / ".vscode").mkdir()
        (vault_path / "Notes").mkdir()

        reset_vault(vault_path)

        # All protected folders are preserved (including .git)
        assert (vault_path / ".obsidian").exists()
        assert (vault_path / ".git").exists()
        assert (vault_path / ".github").exists()
        assert (vault_path / ".vscode").exists()
        # Regular content is removed
        assert not (vault_path / "Notes").exists()


class TestWizardSteps:
    """Tests for wizard step functions"""

    def test_wizard_step_quick_or_custom_quick(self) -> None:
        """Test quick setup selection"""
        with patch("builtins.input", return_value="q"):
            result = wizard_step_quick_or_custom()
        assert result is True

    def test_wizard_step_quick_or_custom_custom(self) -> None:
        """Test custom setup selection"""
        with patch("builtins.input", return_value="c"):
            result = wizard_step_quick_or_custom()
        assert result is False

    def test_wizard_step_note_types_default(self) -> None:
        """Test note types with default selection"""
        with patch("builtins.input", return_value=""):
            result = wizard_step_note_types("lyt-ace")

        # Should return all note types
        assert "map" in result
        assert "dot" in result
        assert len(result) == len(METHODOLOGIES["lyt-ace"]["note_types"])

    def test_wizard_step_frontmatter_default(self) -> None:
        """Test frontmatter with default selection"""
        core = ["type", "up", "created"]
        with patch("builtins.input", side_effect=["", ""]):
            mandatory, optional, custom = wizard_step_frontmatter(core)

        assert mandatory == core
        assert optional == []
        assert custom == []

    def test_wizard_step_frontmatter_with_optional(self) -> None:
        """Test frontmatter with optional selection"""
        core = ["type", "up", "created"]
        with patch("builtins.input", side_effect=["3", ""]):
            mandatory, optional, custom = wizard_step_frontmatter(core)

        assert "created" in optional
        assert "created" not in mandatory
        assert custom == []  # No custom properties added

    def test_wizard_step_confirm_yes(self) -> None:
        """Test confirmation with yes"""
        config = WizardConfig(
            methodology="minimal",
            note_types={"note": {}},
            core_properties=["type"],
            mandatory_properties=["type"],
        )
        with patch("builtins.input", return_value="y"):
            result = wizard_step_confirm(config)
        assert result is True

    def test_wizard_step_confirm_no(self) -> None:
        """Test confirmation with no"""
        config = WizardConfig(
            methodology="minimal",
            note_types={"note": {}},
            core_properties=["type"],
            mandatory_properties=["type"],
        )
        with patch("builtins.input", return_value="n"):
            result = wizard_step_confirm(config)
        assert result is False

    def test_wizard_step_ranking_system_rank(self) -> None:
        """Test ranking system selection - rank"""
        with patch("builtins.input", return_value="r"):
            result = wizard_step_ranking_system()
        assert result == "rank"

    def test_wizard_step_ranking_system_default(self) -> None:
        """Test ranking system selection - default (empty = rank)"""
        with patch("builtins.input", return_value=""):
            result = wizard_step_ranking_system()
        assert result == "rank"

    def test_wizard_step_ranking_system_priority(self) -> None:
        """Test ranking system selection - priority"""
        with patch("builtins.input", return_value="p"):
            result = wizard_step_ranking_system()
        assert result == "priority"

    def test_wizard_step_git_init_yes(self) -> None:
        """Test git init selection - yes"""
        with patch("builtins.input", return_value="y"):
            result = wizard_step_git_init()
        assert result is True

    def test_wizard_step_git_init_no(self) -> None:
        """Test git init selection - no"""
        with patch("builtins.input", return_value="n"):
            result = wizard_step_git_init()
        assert result is False

    def test_wizard_step_git_init_default(self) -> None:
        """Test git init selection - default (empty = no)"""
        with patch("builtins.input", return_value=""):
            result = wizard_step_git_init()
        assert result is False


class TestGitInit:
    """Tests for git initialization functions"""

    def test_create_gitignore(self, tmp_path: Path) -> None:
        """Test .gitignore file creation"""
        vault_path = tmp_path / "git-test"
        vault_path.mkdir()

        create_gitignore(vault_path)

        gitignore = vault_path / ".gitignore"
        assert gitignore.exists()

        content = gitignore.read_text()
        assert ".obsidian/workspace.json" in content
        assert ".DS_Store" in content
        assert ".claude/logs/" in content
        assert ".claude/backups/" in content

    def test_init_git_repo_already_exists(self, tmp_path: Path) -> None:
        """Test git init skips if .git already exists"""
        vault_path = tmp_path / "existing-git"
        vault_path.mkdir()
        (vault_path / ".git").mkdir()

        result = init_git_repo(vault_path, "minimal")
        assert result is True  # Returns True (already initialized)

    def test_init_git_repo_dry_run(self, tmp_path: Path) -> None:
        """Test git init dry run mode"""
        vault_path = tmp_path / "git-dry-run"
        vault_path.mkdir()

        result = init_git_repo(vault_path, "minimal", dry_run=True)
        assert result is True
        # .git should not be created in dry run
        assert not (vault_path / ".git").exists()


class TestApplyRankingSystem:
    """Tests for apply_ranking_system function"""

    def test_apply_rank_to_project(self) -> None:
        """Test applying rank system adds rank as required"""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": ["status"],
                    "optional": ["deadline", "priority"],
                }
            },
            "note": {"properties": {"additional_required": [], "optional": []}},
        }
        result = apply_ranking_system(note_types, "rank")

        # Project should have rank added, priority removed from optional
        assert "rank" in result["project"]["properties"]["additional_required"]
        assert "priority" not in result["project"]["properties"]["optional"]
        # Note type should be unchanged
        assert result["note"]["properties"]["additional_required"] == []

    def test_apply_priority_to_project(self) -> None:
        """Test applying priority system moves priority to required"""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": ["status"],
                    "optional": ["deadline", "priority"],
                }
            },
        }
        result = apply_ranking_system(note_types, "priority")

        # Priority should be in required, not optional
        assert "priority" in result["project"]["properties"]["additional_required"]
        assert "priority" not in result["project"]["properties"]["optional"]

    def test_apply_rank_to_area(self) -> None:
        """Test that area type also gets ranking applied"""
        note_types = {
            "area": {
                "properties": {
                    "additional_required": [],
                    "optional": [],
                }
            },
        }
        result = apply_ranking_system(note_types, "rank")
        assert "rank" in result["area"]["properties"]["additional_required"]

    def test_original_not_modified(self) -> None:
        """Test that original note_types is not modified"""
        note_types = {
            "project": {
                "properties": {
                    "additional_required": ["status"],
                    "optional": ["priority"],
                }
            },
        }
        apply_ranking_system(note_types, "rank")
        # Original should still have priority in optional
        assert "priority" in note_types["project"]["properties"]["optional"]
        assert "rank" not in note_types["project"]["properties"]["additional_required"]


class TestAgentDocs:
    """Tests for AGENTS.md and CLAUDE.md generation"""

    def test_generate_agents_md_content(self) -> None:
        """Test AGENTS.md content generation - agent-focused instructions"""
        note_types = {
            "project": {
                "description": "Active projects",
                "folder_hints": ["Projects/"],
                "properties": {
                    "additional_required": ["status", "rank"],
                    "optional": ["deadline"],
                },
                "validation": {"allow_empty_up": False},
            }
        }
        # Note: note_types and core_properties are kept for API compat but not used
        content = generate_agents_md("para", note_types, ["type", "up", "created"])

        # Core structure (following AGENTS.md standard)
        assert "# AGENTS.md" in content
        assert "PARA" in content  # Methodology name
        assert "## Project Overview" in content
        assert "settings.yaml" in content  # References settings.yaml
        # Commands section
        assert "## Commands" in content
        assert "/obsidian:validate" in content
        # Project structure
        assert "## Project Structure" in content
        # Code style (frontmatter)
        assert "## Code Style" in content
        assert "type:" in content
        assert "created:" in content
        # Testing section
        assert "## Testing" in content
        # Boundaries section (three-tier)
        assert "## Boundaries" in content
        assert "Always Do" in content
        assert "Ask First" in content
        assert "Never Do" in content
        # UP-Links
        assert "## UP-Links" in content
        assert "logical parent" in content
        assert "MOC" in content
        # Git workflow
        assert "## Git Workflow" in content

    def test_generate_claude_md_content(self) -> None:
        """Test CLAUDE.md content generation - minimal with @AGENTS.md include"""
        content = generate_claude_md()

        # Minimal structure with AGENTS.md reference
        assert "# CLAUDE.md" in content
        assert "@AGENTS.md" in content  # Include directive for AGENTS.md
        # Claude-specific section
        assert "## Claude-Specific" in content
        assert "/memory" in content
        # Obsidian plugin commands
        assert "## Obsidian Plugin" in content
        assert "/obsidian:validate" in content

    def test_create_agent_docs(self, tmp_path: Path) -> None:
        """Test creating agent docs files"""
        vault_path = tmp_path / "agent-docs-test"
        vault_path.mkdir()

        note_types = METHODOLOGIES["minimal"]["note_types"]
        core_properties = METHODOLOGIES["minimal"]["core_properties"]

        create_agent_docs(vault_path, "minimal", note_types, core_properties)

        assert (vault_path / "AGENTS.md").exists()
        assert (vault_path / "CLAUDE.md").exists()

        agents_content = (vault_path / "AGENTS.md").read_text()
        assert "Minimal" in agents_content

    def test_create_agent_docs_dry_run(self, tmp_path: Path) -> None:
        """Test agent docs dry run"""
        vault_path = tmp_path / "agent-docs-dry"
        vault_path.mkdir()

        note_types = METHODOLOGIES["minimal"]["note_types"]
        core_properties = METHODOLOGIES["minimal"]["core_properties"]

        create_agent_docs(vault_path, "minimal", note_types, core_properties, dry_run=True)

        # Files should not be created in dry run
        assert not (vault_path / "AGENTS.md").exists()
        assert not (vault_path / "CLAUDE.md").exists()


class TestSampleNotes:
    """Tests for sample note generation"""

    def test_generate_sample_note_content(self) -> None:
        """Test sample note content generation"""
        note_type_config = {
            "description": "Test note type",
            "folder_hints": ["Notes/"],
            "properties": {"additional_required": [], "optional": []},
        }
        content = generate_sample_note(
            "test",
            note_type_config,
            ["type", "created"],
            "minimal",
            {},
        )

        assert "---" in content
        assert 'type: "test"' in content
        assert "Getting Started with Tests" in content

    def test_generate_sample_note_with_additional_props(self) -> None:
        """Test sample note with additional required properties"""
        note_type_config = {
            "description": "Source note",
            "folder_hints": ["Sources/"],
            "properties": {"additional_required": ["author", "url"], "optional": []},
        }
        content = generate_sample_note(
            "source",
            note_type_config,
            ["type", "created"],
            "lyt-ace",
            {},
        )

        assert 'author: "Unknown"' in content
        assert 'url: ""' in content

    def test_generate_sample_note_with_rank(self) -> None:
        """Test sample note with rank property"""
        note_type_config = {
            "description": "Project note",
            "folder_hints": ["Projects/"],
            "properties": {"additional_required": ["status", "rank"], "optional": []},
        }
        content = generate_sample_note(
            "project",
            note_type_config,
            ["type", "created"],
            "para",
            {},
        )

        assert 'status: "active"' in content
        assert "rank: 3" in content  # Default middle rank

    def test_generate_sample_note_with_priority(self) -> None:
        """Test sample note with priority property"""
        note_type_config = {
            "description": "Project note",
            "folder_hints": ["Projects/"],
            "properties": {"additional_required": ["status", "priority"], "optional": []},
        }
        content = generate_sample_note(
            "project",
            note_type_config,
            ["type", "created"],
            "para",
            {},
        )

        assert 'status: "active"' in content
        assert 'priority: "medium"' in content

    def test_create_sample_notes(self, tmp_path: Path) -> None:
        """Test creating sample notes"""
        vault_path = tmp_path / "samples"
        vault_path.mkdir()
        (vault_path / "Notes").mkdir()

        note_types = {
            "note": {
                "description": "General notes",
                "folder_hints": ["Notes/"],
                "properties": {"additional_required": [], "optional": []},
            }
        }

        files = create_sample_notes(
            vault_path, "minimal", note_types, ["type", "created"], dry_run=False
        )

        assert len(files) == 1
        assert files[0].exists()
        assert "Getting Started with Notes.md" in str(files[0])

    def test_create_sample_notes_dry_run(self, tmp_path: Path) -> None:
        """Test sample notes dry run"""
        vault_path = tmp_path / "dry-samples"
        vault_path.mkdir()

        note_types = {
            "note": {
                "description": "General notes",
                "folder_hints": ["Notes/"],
                "properties": {"additional_required": [], "optional": []},
            }
        }

        files = create_sample_notes(
            vault_path, "minimal", note_types, ["type", "created"], dry_run=True
        )

        assert len(files) == 0


class TestMigrationHint:
    """Tests for migration hint"""

    def test_migration_hint_with_existing(self, capsys: pytest.CaptureFixture) -> None:
        """Test migration hint is shown for existing content"""
        show_migration_hint(has_existing_content=True)
        captured = capsys.readouterr()
        assert "Migration" in captured.out

    def test_migration_hint_without_existing(self, capsys: pytest.CaptureFixture) -> None:
        """Test migration hint is not shown for new vault"""
        show_migration_hint(has_existing_content=False)
        captured = capsys.readouterr()
        assert captured.out == ""


class TestWizardConfig:
    """Tests for WizardConfig dataclass"""

    def test_wizard_config_defaults(self) -> None:
        """Test WizardConfig default values"""
        config = WizardConfig(
            methodology="minimal",
            note_types={"note": {}},
            core_properties=["type"],
        )

        assert config.mandatory_properties == []
        assert config.optional_properties == []
        assert config.custom_properties == []
        assert config.custom_note_types == {}
        assert config.per_type_properties == {}
        assert config.create_samples is True
        assert config.reset_vault is False


class TestNoteTypeConfig:
    """Tests for NoteTypeConfig dataclass"""

    def test_note_type_config_defaults(self) -> None:
        """Test NoteTypeConfig default values"""
        config = NoteTypeConfig(
            name="meeting",
            description="Meeting notes",
            folder_hints=["Meetings/"],
        )

        assert config.required_properties == []
        assert config.optional_properties == []
        assert config.validation == {}
        assert config.icon == "file"
        assert config.is_custom is False

    def test_note_type_config_to_dict(self) -> None:
        """Test NoteTypeConfig conversion to dictionary"""
        config = NoteTypeConfig(
            name="recipe",
            description="Recipe notes",
            folder_hints=["Recipes/"],
            required_properties=["ingredients", "time"],
            optional_properties=["rating"],
            validation={"allow_empty_up": True},
            icon="book",
            is_custom=True,
        )

        result = config.to_dict()

        assert result["description"] == "Recipe notes"
        assert result["folder_hints"] == ["Recipes/"]
        assert result["properties"]["additional_required"] == ["ingredients", "time"]
        assert result["properties"]["optional"] == ["rating"]
        assert result["validation"]["allow_empty_up"] is True
        assert result["icon"] == "book"


class TestWizardStepPerTypeProperties:
    """Tests for per-type property wizard step"""

    def test_per_type_properties_accept_defaults(self) -> None:
        """Test accepting defaults for per-type properties"""
        note_types = METHODOLOGIES["minimal"]["note_types"]
        with patch("builtins.input", return_value=""):
            result = wizard_step_per_type_properties(note_types)
        assert result == {}

    def test_per_type_properties_accept_with_a(self) -> None:
        """Test accepting defaults with 'a' input"""
        note_types = METHODOLOGIES["minimal"]["note_types"]
        with patch("builtins.input", return_value="a"):
            result = wizard_step_per_type_properties(note_types)
        assert result == {}

    def test_per_type_properties_customize(self) -> None:
        """Test customizing per-type properties"""
        note_types = {"note": {"properties": {"additional_required": [], "optional": []}}}
        # c to customize, e to edit, enter new required, enter new optional
        with patch("builtins.input", side_effect=["c", "e", "priority, status", "due_date"]):
            result = wizard_step_per_type_properties(note_types)
        assert "note" in result
        assert "priority" in result["note"]["required"]
        assert "due_date" in result["note"]["optional"]

    def test_per_type_properties_clear_with_dash(self) -> None:
        """Test clearing properties with '-' input"""
        note_types = {
            "note": {"properties": {"additional_required": ["old"], "optional": ["legacy"]}}
        }
        # c to customize, e to edit, - to clear required, - to clear optional
        with patch("builtins.input", side_effect=["c", "e", "-", "-"]):
            result = wizard_step_per_type_properties(note_types)
        assert "note" in result
        assert result["note"]["required"] == []
        assert result["note"]["optional"] == []

    def test_per_type_properties_skip_editing(self) -> None:
        """Test skipping editing a type"""
        note_types = {"note": {"properties": {"additional_required": [], "optional": []}}}
        # c to customize, n to skip editing
        with patch("builtins.input", side_effect=["c", "n"]):
            result = wizard_step_per_type_properties(note_types)
        assert result == {}

    def test_per_type_properties_keep_existing(self) -> None:
        """Test keeping existing properties with empty input"""
        note_types = {
            "note": {"properties": {"additional_required": ["status"], "optional": ["rating"]}}
        }
        # c to customize, e to edit, enter to keep required, enter to keep optional
        with patch("builtins.input", side_effect=["c", "y", "", ""]):
            result = wizard_step_per_type_properties(note_types)
        assert "note" in result
        assert result["note"]["required"] == ["status"]
        assert result["note"]["optional"] == ["rating"]


class TestWizardStepCustomNoteTypes:
    """Tests for custom note type wizard step"""

    def test_custom_note_types_none(self) -> None:
        """Test declining to add custom note types"""
        with patch("builtins.input", return_value=""):
            result = wizard_step_custom_note_types("minimal", {})
        assert result == {}

    def test_custom_note_types_none_with_n(self) -> None:
        """Test declining to add custom note types with 'n'"""
        with patch("builtins.input", return_value="n"):
            result = wizard_step_custom_note_types("minimal", {})
        assert result == {}

    def test_custom_note_types_add_one(self) -> None:
        """Test adding one custom note type"""
        # a to add, meeting, description, 1 for first folder, required, optional, n for no more
        with patch(
            "builtins.input",
            side_effect=[
                "a",  # add custom types
                "meeting",  # type name
                "Meeting notes",  # description
                "1",  # folder choice
                "attendees",  # required properties
                "location",  # optional properties
                "n",  # no more types
            ],
        ):
            result = wizard_step_custom_note_types("minimal", {})

        assert "meeting" in result
        assert result["meeting"].name == "meeting"
        assert result["meeting"].description == "Meeting notes"
        assert "attendees" in result["meeting"].required_properties
        assert "location" in result["meeting"].optional_properties
        assert result["meeting"].is_custom is True

    def test_custom_note_types_empty_name_exits(self) -> None:
        """Test empty name exits the wizard"""
        with patch(
            "builtins.input",
            side_effect=[
                "a",  # add custom types
                "",  # empty name exits
            ],
        ):
            result = wizard_step_custom_note_types("minimal", {})
        assert result == {}

    def test_custom_note_types_default_description(self) -> None:
        """Test default description when empty"""
        with patch(
            "builtins.input",
            side_effect=[
                "a",  # add custom types
                "recipe",  # type name
                "",  # empty description -> default
                "1",  # folder choice
                "",  # no required properties
                "",  # no optional properties
                "n",  # no more types
            ],
        ):
            result = wizard_step_custom_note_types("minimal", {})

        assert "recipe" in result
        assert result["recipe"].description == "Custom recipe notes"

    def test_custom_note_types_new_folder(self) -> None:
        """Test creating a new folder for custom type"""
        with patch(
            "builtins.input",
            side_effect=[
                "a",  # add custom types
                "recipe",  # type name
                "Recipe notes",  # description
                "99",  # invalid -> create new folder
                "Recipes",  # new folder name
                "",  # no required properties
                "",  # no optional properties
                "n",  # no more types
            ],
        ):
            result = wizard_step_custom_note_types("minimal", {})

        assert "recipe" in result
        assert result["recipe"].folder_hints == ["Recipes/"]

    def test_custom_note_types_duplicate_name_rejected(self) -> None:
        """Test duplicate name is rejected"""
        existing = {"note": {}}
        with patch(
            "builtins.input",
            side_effect=[
                "a",  # add custom types
                "note",  # duplicate name
                "unique",  # valid name
                "Unique notes",  # description
                "1",  # folder choice
                "",  # no required properties
                "",  # no optional properties
                "n",  # no more types
            ],
        ):
            result = wizard_step_custom_note_types("minimal", existing)

        assert "note" not in result  # Rejected
        assert "unique" in result

    def test_custom_note_types_add_multiple(self) -> None:
        """Test adding multiple custom note types"""
        with patch(
            "builtins.input",
            side_effect=[
                "a",  # add custom types
                "recipe",  # first type
                "Recipe notes",  # description
                "1",  # folder
                "",  # no required
                "",  # no optional
                "y",  # add more
                "meeting",  # second type
                "Meeting notes",  # description
                "1",  # folder
                "attendees",  # required
                "",  # no optional
                "n",  # no more types
            ],
        ):
            result = wizard_step_custom_note_types("minimal", {})

        assert "recipe" in result
        assert "meeting" in result


class TestBuildSettingsYamlWithConfig:
    """Tests for build_settings_yaml with WizardConfig"""

    def test_build_with_per_type_customizations(self) -> None:
        """Test building settings with per-type property customizations"""
        config = WizardConfig(
            methodology="minimal",
            note_types=METHODOLOGIES["minimal"]["note_types"],
            core_properties=["type", "created"],
            per_type_properties={"note": {"required": ["priority"], "optional": ["rating"]}},
        )

        settings = build_settings_yaml("minimal", config)

        assert settings["note_types"]["note"]["properties"]["additional_required"] == ["priority"]
        assert settings["note_types"]["note"]["properties"]["optional"] == ["rating"]

    def test_build_with_custom_note_types(self) -> None:
        """Test building settings with custom note types"""
        custom_type = NoteTypeConfig(
            name="recipe",
            description="Recipe notes",
            folder_hints=["Recipes/"],
            required_properties=["ingredients"],
            optional_properties=[],
            is_custom=True,
        )
        config = WizardConfig(
            methodology="minimal",
            note_types=METHODOLOGIES["minimal"]["note_types"],
            core_properties=["type", "created"],
            custom_note_types={"recipe": custom_type},
        )

        settings = build_settings_yaml("minimal", config)

        assert "recipe" in settings["note_types"]
        assert settings["note_types"]["recipe"]["description"] == "Recipe notes"
        recipe_props = settings["note_types"]["recipe"]["properties"]
        assert recipe_props["additional_required"] == ["ingredients"]

    def test_build_with_mandatory_optional_classification(self) -> None:
        """Test building settings with mandatory/optional property classification"""
        config = WizardConfig(
            methodology="minimal",
            note_types=METHODOLOGIES["minimal"]["note_types"],
            core_properties=["type", "created", "tags"],
            mandatory_properties=["type", "created"],
            optional_properties=["tags"],
            custom_properties=["priority"],
        )

        settings = build_settings_yaml("minimal", config)

        assert settings["core_properties"]["mandatory"] == ["type", "created"]
        assert settings["core_properties"]["optional"] == ["tags"]
        assert settings["core_properties"]["custom"] == ["priority"]
        assert "priority" in settings["core_properties"]["all"]


class TestManualTestingBugfixesIntegration:
    """Integration tests for bugs found during manual testing.

    These tests ensure regressions don't occur for fixes made during manual testing.
    """

    # HOME.md integration tests

    def test_home_md_filename_is_uppercase(self, tmp_path: Path) -> None:
        """Bug: HOME.md should be uppercase, not Home.md"""
        vault_path = tmp_path / "home-test"
        init_vault(vault_path, "lyt-ace", dry_run=False)

        # Check actual filenames in directory (macOS is case-insensitive for exists())
        md_files = [f.name for f in vault_path.iterdir() if f.suffix == ".md"]
        # Should be HOME.md (uppercase)
        assert "HOME.md" in md_files
        # Should NOT contain Home.md (lowercase)
        assert "Home.md" not in md_files

    def test_home_md_date_substituted_not_placeholder(self, tmp_path: Path) -> None:
        """Bug: HOME.md date was {{date}} placeholder instead of actual date"""
        vault_path = tmp_path / "home-date-test"
        init_vault(vault_path, "para", dry_run=False)

        content = (vault_path / "HOME.md").read_text()

        # Should NOT contain {{date}} placeholder
        assert "{{date}}" not in content
        # Should contain a properly formatted date (YYYY-MM-DD pattern)
        import re

        assert re.search(r"created: \"?\d{4}-\d{2}-\d{2}\"?", content)

    def test_home_md_has_correct_frontmatter(self, tmp_path: Path) -> None:
        """Test HOME.md has proper frontmatter structure"""
        vault_path = tmp_path / "home-frontmatter-test"
        init_vault(vault_path, "zettelkasten", dry_run=False)

        content = (vault_path / "HOME.md").read_text()

        # Should have type: map
        assert "type: map" in content
        # Should have created date
        assert "created:" in content

    def test_moc_notes_date_substituted_not_placeholder(self, tmp_path: Path) -> None:
        """Bug: MOC notes had {{date}} placeholder instead of actual date"""
        vault_path = tmp_path / "moc-date-test"
        init_vault(vault_path, "lyt-ace", dry_run=False)

        # Check a MOC file (e.g., _Maps_MOC.md)
        moc_path = vault_path / "Atlas" / "Maps" / "_Maps_MOC.md"
        assert moc_path.exists()

        content = moc_path.read_text()

        # Should NOT contain {{date}} placeholder
        assert "{{date}}" not in content
        # Should contain a properly formatted date (YYYY-MM-DD pattern)
        import re

        assert re.search(r"created: \"?\d{4}-\d{2}-\d{2}\"?", content)

    # .gitignore integration tests

    def test_gitignore_created_during_init(self, tmp_path: Path) -> None:
        """Bug: .gitignore was not created during init"""
        vault_path = tmp_path / "gitignore-init-test"
        init_vault(vault_path, "minimal", dry_run=False)

        gitignore = vault_path / ".gitignore"
        assert gitignore.exists()

    def test_gitignore_created_before_git_init(self, tmp_path: Path) -> None:
        """Test .gitignore is created even without git init"""
        vault_path = tmp_path / "gitignore-no-git-test"
        # Don't pass git=True - just check .gitignore is created
        init_vault(vault_path, "para", dry_run=False)

        gitignore = vault_path / ".gitignore"
        assert gitignore.exists()
        # Should have standard entries
        content = gitignore.read_text()
        assert ".obsidian/workspace.json" in content

    def test_gitignore_idempotent(self, tmp_path: Path) -> None:
        """Test .gitignore creation is idempotent (doesn't duplicate content)"""
        vault_path = tmp_path / "gitignore-idempotent-test"
        vault_path.mkdir()

        # Create first time
        create_gitignore(vault_path)
        first_content = (vault_path / ".gitignore").read_text()

        # Create second time (should not duplicate)
        create_gitignore(vault_path)
        second_content = (vault_path / ".gitignore").read_text()

        assert first_content == second_content

    def test_gitignore_preserved_during_reset(self, tmp_path: Path) -> None:
        """Bug: .gitignore should be preserved during reset"""
        vault_path = tmp_path / "gitignore-reset-test"
        vault_path.mkdir()

        # Create .gitignore with custom content
        gitignore = vault_path / ".gitignore"
        gitignore.write_text("# Custom content\n*.log\n")

        # Add some content to reset
        (vault_path / "Notes").mkdir()
        (vault_path / "test.md").write_text("# Test")

        # Reset vault (should preserve .gitignore)
        reset_vault(vault_path)

        # .gitignore should still exist
        assert gitignore.exists()
        # Content could be updated but file should exist
        assert gitignore.read_text()

    # Git behavior integration tests

    def test_git_protected_during_reset_by_default(self, tmp_path: Path) -> None:
        """Bug: .git should be protected by default during reset"""
        vault_path = tmp_path / "git-protected-test"
        vault_path.mkdir()
        (vault_path / ".git").mkdir()
        (vault_path / ".git" / "config").write_text("[core]\n")
        (vault_path / "Notes").mkdir()

        # Reset vault without specifying git behavior
        reset_vault(vault_path)

        # .git should be preserved
        assert (vault_path / ".git").exists()
        assert (vault_path / ".git" / "config").exists()
        # Regular content should be removed
        assert not (vault_path / "Notes").exists()

    def test_init_with_git_creates_repository(self, tmp_path: Path) -> None:
        """Test init_git_repo creates .git directory"""
        vault_path = tmp_path / "git-init-test"
        vault_path.mkdir()

        # First create .gitignore (required before git init)
        create_gitignore(vault_path)

        # Then initialize git
        result = init_git_repo(vault_path, "minimal")

        assert result is True
        assert (vault_path / ".git").exists()
        assert (vault_path / ".gitignore").exists()

    def test_protected_files_preserved_during_reset(self, tmp_path: Path) -> None:
        """Test PROTECTED_FILES are preserved during reset"""
        vault_path = tmp_path / "protected-files-test"
        vault_path.mkdir()

        # Create protected files
        (vault_path / "README.md").write_text("# Custom README")
        (vault_path / "AGENTS.md").write_text("# Custom AGENTS")
        (vault_path / "CLAUDE.md").write_text("# Custom CLAUDE")
        (vault_path / "HOME.md").write_text("# Custom HOME")
        (vault_path / ".gitignore").write_text("# Custom gitignore")

        # Create non-protected content
        (vault_path / "Notes").mkdir()
        (vault_path / "random.md").write_text("# Random")

        # Reset
        reset_vault(vault_path)

        # Protected files should still exist
        assert (vault_path / "README.md").exists()
        assert (vault_path / "AGENTS.md").exists()
        assert (vault_path / "CLAUDE.md").exists()
        assert (vault_path / "HOME.md").exists()
        assert (vault_path / ".gitignore").exists()

        # Non-protected content should be removed
        assert not (vault_path / "Notes").exists()
        assert not (vault_path / "random.md").exists()

    def test_protected_folders_preserved_during_reset(self, tmp_path: Path) -> None:
        """Test PROTECTED_FOLDERS (.obsidian, .git, .github, .vscode) are preserved"""
        vault_path = tmp_path / "protected-folders-test"
        vault_path.mkdir()

        # Create protected folders with content
        (vault_path / ".obsidian").mkdir()
        (vault_path / ".obsidian" / "app.json").write_text("{}")
        (vault_path / ".git").mkdir()
        (vault_path / ".git" / "config").write_text("[core]")
        (vault_path / ".github").mkdir()
        (vault_path / ".github" / "workflows").mkdir()
        (vault_path / ".vscode").mkdir()
        (vault_path / ".vscode" / "settings.json").write_text("{}")

        # Create non-protected content
        (vault_path / "Notes").mkdir()

        # Reset
        reset_vault(vault_path)

        # All protected folders should exist
        assert (vault_path / ".obsidian").exists()
        assert (vault_path / ".obsidian" / "app.json").exists()
        assert (vault_path / ".git").exists()
        assert (vault_path / ".git" / "config").exists()
        assert (vault_path / ".github").exists()
        assert (vault_path / ".vscode").exists()

        # Non-protected content removed
        assert not (vault_path / "Notes").exists()
