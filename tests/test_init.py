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
    build_settings_yaml,
    choose_methodology_interactive,
    create_folder_structure,
    create_home_note,
    create_readme,
    create_settings_yaml,
    init_vault,
    main,
    print_methodologies,
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

        assert "type" in settings["core_properties"]
        assert "up" in settings["core_properties"]
        assert "created" in settings["core_properties"]


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
    """Test Home.md creation"""

    def test_create_home_note(self, tmp_path: Path) -> None:
        """Test Home.md creation"""
        create_home_note(tmp_path, "lyt-ace", dry_run=False)

        home_path = tmp_path / "Home.md"
        assert home_path.exists()

        content = home_path.read_text()
        assert "LYT + ACE Framework" in content
        assert "type: home" in content

    def test_home_note_dry_run(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't create Home.md"""
        create_home_note(tmp_path, "minimal", dry_run=True)

        assert not (tmp_path / "Home.md").exists()


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

        # Check README and Home
        assert (vault_path / "README.md").exists()
        assert (vault_path / "Home.md").exists()

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
        """Test main function with methodology flag"""
        vault_path = tmp_path / "cli-vault"
        args = ["--vault", str(vault_path), "--methodology", "minimal"]

        with patch("sys.argv", ["init_vault.py", *args]):
            exit_code = main()

        assert exit_code == 0
        assert (vault_path / "Notes").exists()

    def test_main_list_methodologies(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Test --list flag"""
        args = ["--vault", str(tmp_path / "test"), "--list"]

        with patch("sys.argv", ["init_vault.py", *args]):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "lyt-ace" in captured.out
        assert "para" in captured.out

    def test_main_dry_run(self, tmp_path: Path) -> None:
        """Test --dry-run flag"""
        vault_path = tmp_path / "dry-cli-vault"
        args = ["--vault", str(vault_path), "--methodology", "para", "--dry-run"]

        with patch("sys.argv", ["init_vault.py", *args]):
            exit_code = main()

        assert exit_code == 0
        # Should not create folders in dry-run
        if vault_path.exists():
            assert not (vault_path / "Projects").exists()

    def test_main_interactive(self, tmp_path: Path) -> None:
        """Test interactive mode via CLI"""
        vault_path = tmp_path / "interactive-cli"
        args = ["--vault", str(vault_path)]

        with patch("sys.argv", ["init_vault.py", *args]):
            with patch("builtins.input", return_value="zettelkasten"):
                exit_code = main()

        assert exit_code == 0
        assert (vault_path / "Permanent").exists()

    def test_main_error_handling(self, tmp_path: Path) -> None:
        """Test error handling in main"""
        vault_path = tmp_path / "error-vault"
        args = ["--vault", str(vault_path), "--methodology", "invalid"]

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

        init_vault(vault_path, "minimal", dry_run=False)

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
        settings = yaml.safe_load(
            (vault_path / ".claude" / "settings.yaml").read_text()
        )
        assert settings["methodology"] == "lyt-ace"
        assert "map" in settings["note_types"]
        assert "type" in settings["core_properties"]

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
            settings = yaml.safe_load(
                (vault_path / ".claude" / "settings.yaml").read_text()
            )

            # Check required fields
            assert settings["version"] == "1.0"
            assert settings["methodology"] == methodology_key
            assert isinstance(settings["core_properties"], list)
            assert isinstance(settings["note_types"], dict)
            assert isinstance(settings["validation"], dict)
