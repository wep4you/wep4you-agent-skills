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
    choose_methodology_interactive,
    create_config_files,
    create_folder_structure,
    create_readme,
    init_vault,
    main,
    print_methodologies,
)


class TestMethodologies:
    """Test methodology definitions"""

    def test_all_methodologies_have_required_fields(self):
        """Test that all methodologies have required fields"""
        required_fields = ["name", "description", "folders", "default_type_rules"]
        for key, method in METHODOLOGIES.items():
            for field in required_fields:
                assert field in method, f"Methodology {key} missing field: {field}"

    def test_methodologies_have_unique_names(self):
        """Test that all methodology names are unique"""
        names = [m["name"] for m in METHODOLOGIES.values()]
        assert len(names) == len(set(names)), "Duplicate methodology names found"

    def test_methodologies_have_folders(self):
        """Test that all methodologies define folders"""
        for key, method in METHODOLOGIES.items():
            assert len(method["folders"]) > 0, f"Methodology {key} has no folders"

    def test_methodologies_have_type_rules(self):
        """Test that all methodologies define type rules"""
        for key, method in METHODOLOGIES.items():
            assert len(method["default_type_rules"]) > 0, f"Methodology {key} has no type rules"

    def test_lyt_ace_structure(self):
        """Test LYT-ACE methodology structure"""
        lyt_ace = METHODOLOGIES["lyt-ace"]
        assert lyt_ace["name"] == "LYT + ACE Framework"
        assert "Atlas/Maps" in lyt_ace["folders"]
        assert "Atlas/Dots" in lyt_ace["folders"]
        assert "Calendar/Daily" in lyt_ace["folders"]
        assert "Efforts/Projects" in lyt_ace["folders"]
        assert lyt_ace["default_type_rules"]["Atlas/Maps/"] == "map"
        assert lyt_ace["default_type_rules"]["Atlas/Dots/"] == "dot"

    def test_para_structure(self):
        """Test PARA methodology structure"""
        para = METHODOLOGIES["para"]
        assert para["name"] == "PARA Method"
        assert "Projects" in para["folders"]
        assert "Areas" in para["folders"]
        assert "Resources" in para["folders"]
        assert "Archives" in para["folders"]
        assert para["default_type_rules"]["Projects/"] == "project"

    def test_zettelkasten_structure(self):
        """Test Zettelkasten methodology structure"""
        zettel = METHODOLOGIES["zettelkasten"]
        assert zettel["name"] == "Zettelkasten"
        assert "Permanent" in zettel["folders"]
        assert "Literature" in zettel["folders"]
        assert "Fleeting" in zettel["folders"]
        assert zettel["default_type_rules"]["Permanent/"] == "permanent"

    def test_minimal_structure(self):
        """Test Minimal methodology structure"""
        minimal = METHODOLOGIES["minimal"]
        assert minimal["name"] == "Minimal"
        assert "Notes" in minimal["folders"]
        assert "Daily" in minimal["folders"]
        assert minimal["default_type_rules"]["Notes/"] == "note"


class TestPrintMethodologies:
    """Test methodology printing"""

    def test_print_methodologies_output(self, capsys):
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

    def test_choose_valid_methodology(self):
        """Test choosing a valid methodology interactively"""
        with patch("builtins.input", return_value="para"):
            result = choose_methodology_interactive()
            assert result == "para"

    def test_choose_retry_on_invalid(self):
        """Test retry on invalid methodology choice"""
        with patch("builtins.input", side_effect=["invalid", "lyt-ace"]):
            result = choose_methodology_interactive()
            assert result == "lyt-ace"

    def test_choose_case_insensitive(self):
        """Test that methodology choice is case-insensitive"""
        with patch("builtins.input", return_value="LYT-ACE"):
            result = choose_methodology_interactive()
            assert result == "lyt-ace"

    def test_choose_strips_whitespace(self):
        """Test that whitespace is stripped from input"""
        with patch("builtins.input", return_value="  para  "):
            result = choose_methodology_interactive()
            assert result == "para"


class TestCreateFolderStructure:
    """Test folder structure creation"""

    def test_create_lyt_ace_folders(self, tmp_path):
        """Test creating LYT-ACE folder structure"""
        create_folder_structure(tmp_path, "lyt-ace", dry_run=False)

        assert (tmp_path / "Atlas" / "Maps").exists()
        assert (tmp_path / "Atlas" / "Dots").exists()
        assert (tmp_path / "Atlas" / "Sources").exists()
        assert (tmp_path / "Calendar" / "Daily").exists()
        assert (tmp_path / "Efforts" / "Projects").exists()
        assert (tmp_path / "Efforts" / "Areas").exists()
        assert (tmp_path / ".obsidian").exists()
        assert (tmp_path / ".claude" / "config").exists()

    def test_create_para_folders(self, tmp_path):
        """Test creating PARA folder structure"""
        create_folder_structure(tmp_path, "para", dry_run=False)

        assert (tmp_path / "Projects").exists()
        assert (tmp_path / "Areas").exists()
        assert (tmp_path / "Resources").exists()
        assert (tmp_path / "Archives").exists()
        assert (tmp_path / ".obsidian").exists()

    def test_create_zettelkasten_folders(self, tmp_path):
        """Test creating Zettelkasten folder structure"""
        create_folder_structure(tmp_path, "zettelkasten", dry_run=False)

        assert (tmp_path / "Permanent").exists()
        assert (tmp_path / "Literature").exists()
        assert (tmp_path / "Fleeting").exists()
        assert (tmp_path / "References").exists()

    def test_create_minimal_folders(self, tmp_path):
        """Test creating minimal folder structure"""
        create_folder_structure(tmp_path, "minimal", dry_run=False)

        assert (tmp_path / "Notes").exists()
        assert (tmp_path / "Daily").exists()

    def test_create_folders_dry_run(self, tmp_path):
        """Test dry-run mode doesn't create folders"""
        create_folder_structure(tmp_path, "para", dry_run=True)

        assert not (tmp_path / "Projects").exists()
        assert not (tmp_path / "Areas").exists()

    def test_create_folders_invalid_methodology(self, tmp_path):
        """Test error on invalid methodology"""
        with pytest.raises(ValueError, match="Unknown methodology"):
            create_folder_structure(tmp_path, "invalid", dry_run=False)

    def test_create_folders_idempotent(self, tmp_path):
        """Test that creating folders twice is safe"""
        create_folder_structure(tmp_path, "minimal", dry_run=False)
        create_folder_structure(tmp_path, "minimal", dry_run=False)  # Should not error

        assert (tmp_path / "Notes").exists()


class TestCreateConfigFiles:
    """Test configuration file creation"""

    def test_create_validator_config(self, tmp_path):
        """Test validator.yaml creation"""
        create_config_files(tmp_path, "lyt-ace", dry_run=False)

        config_path = tmp_path / ".claude" / "config" / "validator.yaml"
        assert config_path.exists()

        config = yaml.safe_load(config_path.read_text())
        assert "exclude_paths" in config
        assert "type_rules" in config
        assert "auto_fix" in config
        assert config["type_rules"]["Atlas/Maps/"] == "map"

    def test_create_frontmatter_config(self, tmp_path):
        """Test frontmatter.yaml creation"""
        create_config_files(tmp_path, "para", dry_run=False)

        config_path = tmp_path / ".claude" / "config" / "frontmatter.yaml"
        assert config_path.exists()

        config = yaml.safe_load(config_path.read_text())
        assert "properties" in config
        assert "type" in config["properties"]
        assert "up" in config["properties"]
        assert "created" in config["properties"]
        assert "daily" in config["properties"]
        assert "collection" in config["properties"]
        assert "related" in config["properties"]

    def test_create_note_types_config(self, tmp_path):
        """Test note-types.yaml creation"""
        create_config_files(tmp_path, "zettelkasten", dry_run=False)

        config_path = tmp_path / ".claude" / "config" / "note-types.yaml"
        assert config_path.exists()

        config = yaml.safe_load(config_path.read_text())
        assert "note_types" in config
        assert "permanent" in config["note_types"]
        assert "literature" in config["note_types"]

    def test_config_files_dry_run(self, tmp_path):
        """Test dry-run mode doesn't create config files"""
        create_config_files(tmp_path, "para", dry_run=True)

        config_dir = tmp_path / ".claude" / "config"
        if config_dir.exists():
            assert not (config_dir / "validator.yaml").exists()

    def test_config_exclude_paths(self, tmp_path):
        """Test that validator config has exclude paths"""
        create_config_files(tmp_path, "minimal", dry_run=False)

        config_path = tmp_path / ".claude" / "config" / "validator.yaml"
        config = yaml.safe_load(config_path.read_text())

        assert "+/" in config["exclude_paths"]
        assert "x/" in config["exclude_paths"]
        assert ".obsidian/" in config["exclude_paths"]

    def test_config_auto_fix_settings(self, tmp_path):
        """Test that validator config has auto-fix settings"""
        create_config_files(tmp_path, "para", dry_run=False)

        config_path = tmp_path / ".claude" / "config" / "validator.yaml"
        config = yaml.safe_load(config_path.read_text())

        assert config["auto_fix"]["empty_types"] is True
        assert config["auto_fix"]["daily_links"] is True
        assert config["auto_fix"]["wikilink_quotes"] is True

    def test_frontmatter_required_properties(self, tmp_path):
        """Test that frontmatter config has required properties"""
        create_config_files(tmp_path, "lyt-ace", dry_run=False)

        config_path = tmp_path / ".claude" / "config" / "frontmatter.yaml"
        config = yaml.safe_load(config_path.read_text())

        # Check required properties
        assert config["properties"]["type"]["required"] is True
        assert config["properties"]["up"]["required"] is True
        assert config["properties"]["created"]["required"] is True
        assert config["properties"]["daily"]["required"] is True

        # Check optional properties
        assert config["properties"]["collection"]["required"] is False
        assert config["properties"]["related"]["required"] is False


class TestCreateReadme:
    """Test README creation"""

    def test_create_readme(self, tmp_path):
        """Test README.md creation"""
        create_readme(tmp_path, "para", dry_run=False)

        readme_path = tmp_path / "README.md"
        assert readme_path.exists()

        content = readme_path.read_text()
        assert "PARA Method" in content
        assert "Projects" in content
        assert "Areas" in content
        assert "validator.yaml" in content

    def test_readme_dry_run(self, tmp_path):
        """Test dry-run mode doesn't create README"""
        create_readme(tmp_path, "minimal", dry_run=True)

        assert not (tmp_path / "README.md").exists()

    def test_readme_has_methodology_info(self, tmp_path):
        """Test README contains methodology information"""
        create_readme(tmp_path, "lyt-ace", dry_run=False)

        content = (tmp_path / "README.md").read_text()
        assert "LYT + ACE Framework" in content
        assert "Atlas/Maps" in content

    def test_readme_has_validation_commands(self, tmp_path):
        """Test README contains validation commands"""
        create_readme(tmp_path, "zettelkasten", dry_run=False)

        content = (tmp_path / "README.md").read_text()
        assert "validator.py" in content
        assert "--mode report" in content
        assert "--mode auto" in content


class TestInitVault:
    """Test complete vault initialization"""

    def test_init_vault_lyt_ace(self, tmp_path):
        """Test complete LYT-ACE vault initialization"""
        vault_path = tmp_path / "test-vault"
        init_vault(vault_path, "lyt-ace", dry_run=False)

        # Check folders
        assert (vault_path / "Atlas" / "Maps").exists()
        assert (vault_path / ".obsidian").exists()

        # Check config files
        assert (vault_path / ".claude" / "config" / "validator.yaml").exists()
        assert (vault_path / ".claude" / "config" / "frontmatter.yaml").exists()
        assert (vault_path / ".claude" / "config" / "note-types.yaml").exists()

        # Check README
        assert (vault_path / "README.md").exists()

    def test_init_vault_para(self, tmp_path):
        """Test complete PARA vault initialization"""
        vault_path = tmp_path / "para-vault"
        init_vault(vault_path, "para", dry_run=False)

        assert (vault_path / "Projects").exists()
        assert (vault_path / "README.md").exists()

    def test_init_vault_dry_run(self, tmp_path):
        """Test dry-run doesn't create vault"""
        vault_path = tmp_path / "dry-vault"
        init_vault(vault_path, "minimal", dry_run=True)

        # Vault directory itself shouldn't be created in dry-run
        if vault_path.exists():
            # If it exists, it should be empty
            assert not (vault_path / "Notes").exists()

    def test_init_vault_creates_directory(self, tmp_path):
        """Test that init creates vault directory if it doesn't exist"""
        vault_path = tmp_path / "new-vault"
        assert not vault_path.exists()

        init_vault(vault_path, "minimal", dry_run=False)

        assert vault_path.exists()
        assert (vault_path / "Notes").exists()

    def test_init_vault_interactive_mode(self, tmp_path):
        """Test interactive mode (methodology=None)"""
        vault_path = tmp_path / "interactive-vault"

        with patch("builtins.input", return_value="para"):
            init_vault(vault_path, methodology=None, dry_run=False)

        assert (vault_path / "Projects").exists()


class TestMainCLI:
    """Test CLI main function"""

    def test_main_with_methodology(self, tmp_path):
        """Test main function with methodology flag"""
        vault_path = tmp_path / "cli-vault"
        args = ["--vault", str(vault_path), "--methodology", "minimal"]

        with patch("sys.argv", ["init_vault.py", *args]):
            exit_code = main()

        assert exit_code == 0
        assert (vault_path / "Notes").exists()

    def test_main_list_methodologies(self, tmp_path, capsys):
        """Test --list flag"""
        args = ["--vault", str(tmp_path / "test"), "--list"]

        with patch("sys.argv", ["init_vault.py", *args]):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "lyt-ace" in captured.out
        assert "para" in captured.out

    def test_main_dry_run(self, tmp_path):
        """Test --dry-run flag"""
        vault_path = tmp_path / "dry-cli-vault"
        args = ["--vault", str(vault_path), "--methodology", "para", "--dry-run"]

        with patch("sys.argv", ["init_vault.py", *args]):
            exit_code = main()

        assert exit_code == 0
        # Should not create folders in dry-run
        if vault_path.exists():
            assert not (vault_path / "Projects").exists()

    def test_main_interactive(self, tmp_path):
        """Test interactive mode via CLI"""
        vault_path = tmp_path / "interactive-cli"
        args = ["--vault", str(vault_path)]

        with patch("sys.argv", ["init_vault.py", *args]):
            with patch("builtins.input", return_value="zettelkasten"):
                exit_code = main()

        assert exit_code == 0
        assert (vault_path / "Permanent").exists()

    def test_main_error_handling(self, tmp_path):
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

    def test_existing_vault_safe(self, tmp_path):
        """Test initializing into existing directory is safe"""
        vault_path = tmp_path / "existing"
        vault_path.mkdir()
        (vault_path / "existing-file.md").write_text("# Existing")

        init_vault(vault_path, "minimal", dry_run=False)

        # Should create new folders without destroying existing file
        assert (vault_path / "existing-file.md").exists()
        assert (vault_path / "Notes").exists()

    def test_unicode_vault_path(self, tmp_path):
        """Test vault path with unicode characters"""
        vault_path = tmp_path / "テスト-vault"
        init_vault(vault_path, "minimal", dry_run=False)

        assert (vault_path / "Notes").exists()

    def test_spaces_in_path(self, tmp_path):
        """Test vault path with spaces"""
        vault_path = tmp_path / "My Vault"
        init_vault(vault_path, "minimal", dry_run=False)

        assert (vault_path / "Notes").exists()


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_lyt_ace_workflow(self, tmp_path):
        """Test complete LYT-ACE vault setup and verification"""
        vault_path = tmp_path / "lyt-integration"

        # Initialize vault
        init_vault(vault_path, "lyt-ace", dry_run=False)

        # Verify all components
        assert (vault_path / "Atlas" / "Maps").exists()
        assert (vault_path / "Atlas" / "Dots").exists()
        assert (vault_path / "Calendar" / "Daily").exists()
        assert (vault_path / "Efforts" / "Projects").exists()

        # Verify config files are valid YAML
        validator_config = yaml.safe_load(
            (vault_path / ".claude" / "config" / "validator.yaml").read_text()
        )
        assert "Atlas/Maps/" in validator_config["type_rules"]

        frontmatter_config = yaml.safe_load(
            (vault_path / ".claude" / "config" / "frontmatter.yaml").read_text()
        )
        assert len(frontmatter_config["properties"]) == 6  # 6 standard properties

        # Verify README
        readme = (vault_path / "README.md").read_text()
        assert "Atlas/Maps" in readme

    def test_all_methodologies_initialize(self, tmp_path):
        """Test that all methodologies can be initialized"""
        for methodology_key in METHODOLOGIES.keys():
            vault_path = tmp_path / f"test-{methodology_key}"
            init_vault(vault_path, methodology_key, dry_run=False)

            # Verify at least basic structure exists
            assert vault_path.exists()
            assert (vault_path / ".claude" / "config" / "validator.yaml").exists()
            assert (vault_path / "README.md").exists()
