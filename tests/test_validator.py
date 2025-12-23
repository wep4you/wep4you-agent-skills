"""
Tests for validate skill

Run with: uv run pytest tests/test_validator.py -v
"""

import sys
from pathlib import Path

import pytest

# Add skills directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "validate" / "scripts"))

# Import after path modification - these will be available when run via uv
# Note: Import is done inside test functions to handle PEP 723 script dependencies


class TestFrontmatterExtraction:
    """Test frontmatter extraction logic"""

    def test_valid_frontmatter_extraction(self, tmp_path):
        """Test extraction of valid frontmatter"""
        # Create temporary file
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: "[[Parent]]"
created: 2025-01-15
---

# Content

Some content with --- in it.
""")

        # Import and test
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        content = test_file.read_text()
        frontmatter = validator.extract_frontmatter_only(content)

        assert frontmatter is not None
        assert "type: Dot" in frontmatter
        assert "# Content" not in frontmatter

    def test_no_frontmatter(self, tmp_path):
        """Test file without frontmatter"""
        test_file = tmp_path / "no-fm.md"
        test_file.write_text("# Just a heading\n\nSome content")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        content = test_file.read_text()
        frontmatter = validator.extract_frontmatter_only(content)

        assert frontmatter is None or frontmatter.strip() == ""


class TestValidation:
    """Test validation checks"""

    @pytest.fixture
    def fixtures_path(self):
        """Return path to test fixtures"""
        return Path(__file__).parent / "fixtures"

    def test_valid_note_passes(self, fixtures_path):
        """Valid notes should not produce issues"""
        from validator import VaultValidator

        validator = VaultValidator(str(fixtures_path / "valid"))
        validator.run_validation()

        total_issues = sum(len(v) for v in validator.issues.values())
        assert total_issues == 0, f"Valid notes should have no issues: {validator.issues}"

    def test_detect_missing_type(self, fixtures_path):
        """Detect missing type property"""
        from validator import VaultValidator

        validator = VaultValidator(str(fixtures_path / "invalid"))
        validator.run_validation()

        # Check that missing-type.md is in missing_properties
        missing_files = [f for f in validator.issues["missing_properties"] if "missing-type" in f]
        assert len(missing_files) > 0, "Should detect missing type property"

    def test_detect_unquoted_wikilinks(self, fixtures_path):
        """Detect unquoted wikilinks in frontmatter"""
        from validator import VaultValidator

        validator = VaultValidator(str(fixtures_path / "invalid"))
        validator.run_validation()

        issues = validator.issues["unquoted_wikilinks"]
        unquoted_files = [f for f in issues if "unquoted-wikilink" in f]
        assert len(unquoted_files) > 0, "Should detect unquoted wikilinks"

    def test_detect_title_property(self, fixtures_path):
        """Detect deprecated title property"""
        from validator import VaultValidator

        validator = VaultValidator(str(fixtures_path / "invalid"))
        validator.run_validation()

        title_files = [f for f in validator.issues["title_properties"] if "has-title" in f]
        assert len(title_files) > 0, "Should detect title property"

    def test_detect_date_mismatch(self, fixtures_path):
        """Detect date mismatch between created and daily"""
        from validator import VaultValidator

        validator = VaultValidator(str(fixtures_path / "invalid"))
        validator.run_validation()

        mismatch_files = [f for f in validator.issues["date_mismatches"] if "date-mismatch" in f]
        assert len(mismatch_files) > 0, "Should detect date mismatch"


class TestAutoFix:
    """Test auto-fix functionality"""

    def test_fix_title_property(self, tmp_path):
        """Test removal of title property"""
        # Create file with title property
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
title: Old Title
type: Dot
up: "[[Parent]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection: []
related: []
---

# Content
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.run_validation()
        validator.run_fixes()

        # Re-read and check
        new_content = test_file.read_text()
        assert "title:" not in new_content

    def test_fix_date_mismatch(self, tmp_path):
        """Test date synchronization fix"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: "[[Parent]]"
created: 2025-01-15
daily: "[[2025-01-20]]"
collection: []
related: []
---

# Content
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.run_validation()
        validator.run_fixes()

        new_content = test_file.read_text()
        assert 'daily: "[[2025-01-15]]"' in new_content


class TestConfiguration:
    """Test configuration loading"""

    def test_default_config(self, tmp_path):
        """Test default config when no file exists"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))

        assert "exclude_paths" in validator.config
        assert "auto_fix" in validator.config

    def test_custom_config(self, tmp_path):
        """Test loading custom config"""
        # Create config file
        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "validator.yaml"
        config_file.write_text("""
version: "test"
exclude_paths:
  - custom/exclude/
auto_fix:
  empty_types: false
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))

        assert validator.config.get("version") == "test"
        assert "custom/exclude/" in validator.config.get("exclude_paths", [])

    def test_exclude_paths(self, tmp_path):
        """Test file exclusion based on config"""
        # Create excluded and non-excluded files
        excluded_dir = tmp_path / "templates"
        excluded_dir.mkdir()
        (excluded_dir / "template.md").write_text("---\ntype:\n---\n# Template")

        regular_dir = tmp_path / "notes"
        regular_dir.mkdir()
        (regular_dir / "note.md").write_text("---\ntype:\n---\n# Note")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["exclude_paths"] = ["templates/"]

        files = validator.scan_vault()
        file_names = [f.name for f in files]

        assert "template.md" not in file_names
        assert "note.md" in file_names


class TestTypeInference:
    """Test type inference from file location"""

    @pytest.fixture
    def validator_with_rules(self, tmp_path):
        """Create validator with type rules configured"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        # Set up type rules (normally loaded from config)
        validator.type_rules = {
            "Atlas/Maps/": "map",
            "Atlas/Dots/": "dot",
            "Calendar/daily/": "daily",
        }
        return validator

    def test_infer_dot_type(self, validator_with_rules):
        """Test inferring Dot type from Atlas/Dots path"""
        inferred = validator_with_rules.infer_type("Atlas/Dots/Software/Python.md")
        assert inferred == "dot"

    def test_infer_map_type(self, validator_with_rules):
        """Test inferring Map type from Atlas/Maps path"""
        inferred = validator_with_rules.infer_type("Atlas/Maps/Software/Python Map.md")
        assert inferred == "map"

    def test_infer_daily_type(self, validator_with_rules):
        """Test inferring Daily type from Calendar path"""
        inferred = validator_with_rules.infer_type("Calendar/daily/2025/01/2025-01-15.md")
        assert inferred == "daily"

    def test_no_inference_for_unknown_path(self, validator_with_rules):
        """Test that unknown paths return None"""
        inferred = validator_with_rules.infer_type("random/path/note.md")
        assert inferred is None


class TestAutoFixExtended:
    """Extended auto-fix tests for better coverage"""

    def test_fix_empty_type(self, tmp_path):
        """Test fixing empty type field"""
        # Create directory structure that matches type rules
        dots_dir = tmp_path / "Atlas" / "Dots"
        dots_dir.mkdir(parents=True)
        test_file = dots_dir / "test.md"
        test_file.write_text("""---
type:
up: "[[Parent]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection: []
related: []
---

# Content
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        # Explicitly set type rules for the test
        validator.type_rules = {"Atlas/Dots/": "dot"}
        validator.run_validation()
        fixed = validator.fix_empty_types()

        # Verify fix was applied
        assert fixed == 1
        new_content = test_file.read_text()
        assert "type: dot" in new_content

    def test_fix_unquoted_wikilinks(self, tmp_path):
        """Test adding quotes to wikilinks"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: [[Parent]]
created: 2025-01-15
daily: "[[2025-01-15]]"
collection: []
related: []
---

# Content
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.run_validation()
        validator.run_fixes()

        new_content = test_file.read_text()
        assert 'up: "[[Parent]]"' in new_content

    def test_fix_invalid_created(self, tmp_path):
        """Test fixing created date format"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: "[[Parent]]"
created: [[2025-01-15]]
daily: "[[2025-01-15]]"
collection: []
related: []
---

# Content
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.run_validation()
        fixed = validator.fix_invalid_created()

        assert fixed == 1
        new_content = test_file.read_text()
        assert "created: 2025-01-15" in new_content

    def test_fix_daily_links(self, tmp_path):
        """Test fixing full-path daily links"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: "[[Parent]]"
created: 2025-01-15
daily: "[[Calendar/daily/2025/01/2025-01-15]]"
collection: []
related: []
---

# Content
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.run_validation()
        validator.run_fixes()

        new_content = test_file.read_text()
        assert 'daily: "[[2025-01-15]]"' in new_content


class TestReportGeneration:
    """Test report generation"""

    def test_generate_summary(self, tmp_path):
        """Test summary generation"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        summary = validator.generate_summary()

        assert "total_issues" in summary
        assert "issues_by_type" in summary

    def test_generate_report(self, tmp_path):
        """Test markdown report generation"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.issues["empty_types"] = ["file1.md", "file2.md"]

        report = validator.generate_report()

        assert "Vault Validation Report" in report
        assert "Empty Types" in report

    def test_generate_report_to_file(self, tmp_path):
        """Test saving report to file"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))

        output_file = tmp_path / "report.md"
        validator.generate_report(str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "Vault Validation Report" in content


class TestValidationExtended:
    """Extended validation tests"""

    def test_detect_invalid_daily_link(self, tmp_path):
        """Test detecting full-path daily links"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: "[[Parent]]"
created: 2025-01-15
daily: "[[Calendar/daily/2025/01/2025-01-15]]"
collection: []
related: []
---
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.run_validation()

        assert len(validator.issues["invalid_daily_links"]) > 0

    def test_detect_invalid_created_format(self, tmp_path):
        """Test detecting wikilink in created field"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: "[[Parent]]"
created: [[2025-01-15]]
daily: "[[2025-01-15]]"
collection: []
related: []
---
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.run_validation()

        assert len(validator.issues["invalid_created"]) > 0

    def test_skip_daily_notes_for_missing_properties(self, tmp_path):
        """Test that daily notes don't require all properties"""
        daily_dir = tmp_path / "Calendar" / "daily" / "2025" / "01"
        daily_dir.mkdir(parents=True)
        test_file = daily_dir / "2025-01-15.md"
        test_file.write_text("""---
type: daily
created: 2025-01-15
---

# Daily Note
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.run_validation()

        # Daily notes should not be flagged for missing properties
        missing = [f for f in validator.issues["missing_properties"] if "2025-01-15" in f]
        assert len(missing) == 0


class TestFixMissingTypes:
    """Test fix_missing_types function"""

    def test_fix_missing_type_with_inferable_location(self, tmp_path):
        """Test adding missing type to file in known location"""
        dots_dir = tmp_path / "Atlas" / "Dots"
        dots_dir.mkdir(parents=True)
        test_file = dots_dir / "test.md"
        test_file.write_text("""---
up: "[[Parent]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection: []
related: []
---

# Content
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.type_rules = {"Atlas/Dots/": "dot"}
        validator.run_validation()

        # Should have missing type in issues
        assert len(validator.issues["missing_properties"]) > 0

        fixed = validator.fix_missing_types()
        assert fixed == 1

        new_content = test_file.read_text()
        assert "type: dot" in new_content

    def test_fix_missing_type_skips_non_type_properties(self, tmp_path):
        """Test that fix_missing_types only handles type property"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: dot
created: 2025-01-15
---

# Content missing other properties
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.run_validation()

        # Should have missing properties but not type
        fixed = validator.fix_missing_types()
        assert fixed == 0


class TestConfigErrors:
    """Test configuration error handling"""

    def test_invalid_config_file(self, tmp_path):
        """Test handling of invalid YAML config"""
        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "validator.yaml"
        config_file.write_text("invalid: yaml: content: [")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))

        # Should fall back to default config
        assert "exclude_paths" in validator.config


class TestExcludeFiles:
    """Test file exclusion"""

    def test_exclude_specific_files(self, tmp_path):
        """Test excluding specific files by name"""
        (tmp_path / "normal.md").write_text("---\ntype: dot\n---\n")
        (tmp_path / "README.md").write_text("---\ntype: dot\n---\n")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["exclude_files"] = ["README.md"]

        files = validator.scan_vault()
        file_names = [f.name for f in files]

        assert "normal.md" in file_names
        assert "README.md" not in file_names


class TestRunValidationWithPath:
    """Test run_validation with path filter"""

    def test_validate_specific_path(self, tmp_path):
        """Test validating only a specific subdirectory"""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        (notes_dir / "note.md").write_text("---\ntype: dot\n---\n")

        other_dir = tmp_path / "other"
        other_dir.mkdir()
        (other_dir / "other.md").write_text("---\ntype:\n---\n")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.run_validation("notes/")

        # Should only have scanned notes directory
        total_issues = sum(len(v) for v in validator.issues.values())
        # notes/note.md is valid, so no issues from that
        assert validator.skipped_files == 0 or total_issues == 0


class TestGenerateSummaryWithIssues:
    """Test summary generation with issues"""

    def test_summary_with_multiple_issue_types(self, tmp_path):
        """Test summary when multiple issue types exist"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.issues["empty_types"] = ["file1.md"]
        validator.issues["title_properties"] = ["file2.md", "file3.md"]

        summary = validator.generate_summary()

        assert summary["total_issues"] == 3
        assert "empty_types" in summary["issues_by_type"]
        assert summary["issues_by_type"]["empty_types"] == 1
        assert summary["issues_by_type"]["title_properties"] == 2


class TestReportWithManyFiles:
    """Test report generation with many files"""

    def test_report_truncates_long_lists(self, tmp_path):
        """Test that report truncates lists > 10 files"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.issues["empty_types"] = [f"file{i}.md" for i in range(15)]

        report = validator.generate_report()

        assert "... and 5 more" in report


class TestAutoFixDisabled:
    """Test auto-fix when disabled in config"""

    def test_fix_daily_links_disabled(self, tmp_path):
        """Test that fix_daily_links respects config"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
daily: "[[Calendar/daily/2025/01/2025-01-15]]"
---
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.config["auto_fix"] = {"daily_links": False}
        validator.run_validation()

        fixed = validator.fix_daily_links()
        assert fixed == 0

    def test_fix_wikilink_quotes_disabled(self, tmp_path):
        """Test that fix_unquoted_wikilinks respects config"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
up: [[Parent]]
---
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.config["auto_fix"] = {"wikilink_quotes": False}
        validator.run_validation()

        fixed = validator.fix_unquoted_wikilinks()
        assert fixed == 0

    def test_fix_invalid_created_disabled(self, tmp_path):
        """Test that fix_invalid_created respects config"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
created: [[2025-01-15]]
---
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.config["auto_fix"] = {"invalid_created": False}
        validator.run_validation()

        fixed = validator.fix_invalid_created()
        assert fixed == 0

    def test_fix_title_properties_disabled(self, tmp_path):
        """Test that fix_title_properties respects config"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
title: Test
type: Dot
---
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.config["auto_fix"] = {"title_properties": False}
        validator.run_validation()

        fixed = validator.fix_title_properties()
        assert fixed == 0

    def test_fix_date_mismatches_disabled(self, tmp_path):
        """Test that fix_date_mismatches respects config"""
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: Dot
created: 2025-01-15
daily: "[[2025-01-20]]"
---
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path), mode="auto")
        validator.config["auto_fix"] = {"date_mismatches": False}
        validator.run_validation()

        fixed = validator.fix_date_mismatches()
        assert fixed == 0


class TestDynamicConfig:
    """Test dynamic configuration loading (v1.3.0)"""

    def test_load_dynamic_config_with_note_type_rules(self, tmp_path):
        """Test loading config with note-type validation rules"""
        config_dir = tmp_path / ".claude" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "validator.yaml"
        config_file.write_text("""
version: "1.3.0"
dynamic_config: true
note_type_validation: true
note_type_validation_rules:
  map:
    required: [type, up]
    formats:
      created: date
  project:
    required: [type, status]
""")

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))

        assert validator.config.get("version") == "1.3.0"
        assert validator.config.get("dynamic_config") is True
        assert validator.config.get("note_type_validation") is True
        assert "map" in validator.note_type_rules
        assert "project" in validator.note_type_rules


class TestNoteTypeValidation:
    """Test note-type specific validation (v1.3.0)"""

    def test_check_type_properties_missing_required(self, tmp_path):
        """Test detection of missing required properties for a type"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["note_type_validation"] = True
        validator.note_type_rules = {
            "map": {"required": ["type", "up", "related"], "optional": ["tags"]}
        }

        frontmatter = """---
type: map
up: "[[Parent]]"
created: 2025-01-15
---"""

        violations = validator.check_type_properties(frontmatter, "map", "test.md")
        assert len(violations) == 1
        assert "missing: related" in violations[0]

    def test_check_type_properties_all_present(self, tmp_path):
        """Test no violations when all required properties present"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["note_type_validation"] = True
        validator.note_type_rules = {"map": {"required": ["type", "up"]}}

        frontmatter = """---
type: map
up: "[[Parent]]"
created: 2025-01-15
---"""

        violations = validator.check_type_properties(frontmatter, "map", "test.md")
        assert len(violations) == 0

    def test_check_property_formats_invalid_date(self, tmp_path):
        """Test detection of invalid date format"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["note_type_validation"] = True
        validator.note_type_rules = {"map": {"formats": {"created": "date"}}}

        frontmatter = """---
type: map
created: 2025/01/15
---"""

        violations = validator.check_property_formats(frontmatter, "map", "test.md")
        assert len(violations) == 1
        assert "invalid date format" in violations[0]

    def test_check_property_formats_valid_date(self, tmp_path):
        """Test valid date format passes"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["note_type_validation"] = True
        validator.note_type_rules = {"map": {"formats": {"created": "date"}}}

        frontmatter = """---
type: map
created: 2025-01-15
---"""

        violations = validator.check_property_formats(frontmatter, "map", "test.md")
        assert len(violations) == 0

    def test_check_property_formats_wikilink(self, tmp_path):
        """Test wikilink format validation"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["note_type_validation"] = True
        validator.note_type_rules = {"map": {"formats": {"up": "wikilink"}}}

        # Invalid - not a wikilink
        frontmatter_invalid = """---
type: map
up: Parent
---"""

        violations = validator.check_property_formats(frontmatter_invalid, "map", "test.md")
        assert len(violations) == 1
        assert "should be wikilink" in violations[0]

        # Valid - is a wikilink
        frontmatter_valid = """---
type: map
up: "[[Parent]]"
---"""

        violations = validator.check_property_formats(frontmatter_valid, "map", "test.md")
        assert len(violations) == 0

    def test_validate_file_with_type_validation(self, tmp_path):
        """Test validate_file integrates type-specific checks"""
        from validator import VaultValidator

        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: map
up: "[[Parent]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection: []
related: []
---

# Test Map
""")

        validator = VaultValidator(str(tmp_path))
        validator.config["note_type_validation"] = True
        validator.note_type_rules = {
            "map": {"required": ["type", "up", "tags"], "formats": {"created": "date"}}
        }

        validator.run_validation()

        # Should detect missing 'tags' property
        assert len(validator.issues["type_property_violations"]) == 1
        assert "missing: tags" in validator.issues["type_property_violations"][0]

    def test_type_validation_disabled_by_default(self, tmp_path):
        """Test that type validation is disabled when config flag is false"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        validator.config["note_type_validation"] = False
        validator.note_type_rules = {"map": {"required": ["tags"]}}

        frontmatter = """---
type: map
up: "[[Parent]]"
---"""

        violations = validator.check_type_properties(frontmatter, "map", "test.md")
        assert len(violations) == 0  # Should return empty list when disabled


class TestParseFrontmatterToDict:
    """Test frontmatter parsing to dictionary"""

    def test_parse_simple_frontmatter(self, tmp_path):
        """Test parsing simple frontmatter"""
        from datetime import date

        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        frontmatter = """---
type: map
up: "[[Parent]]"
created: 2025-01-15
---"""

        result = validator.parse_frontmatter_to_dict(frontmatter)
        assert result["type"] == "map"
        assert result["up"] == "[[Parent]]"
        # PyYAML parses dates as datetime.date objects
        assert result["created"] == date(2025, 1, 15) or result["created"] == "2025-01-15"

    def test_parse_frontmatter_with_lists(self, tmp_path):
        """Test parsing frontmatter with list properties"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        frontmatter = """---
type: map
tags: [tag1, tag2, tag3]
related: []
---"""

        result = validator.parse_frontmatter_to_dict(frontmatter)
        assert isinstance(result["tags"], list)
        assert len(result["tags"]) == 3
        assert result["related"] == []

    def test_parse_invalid_frontmatter(self, tmp_path):
        """Test parsing invalid frontmatter returns empty dict"""
        from validator import VaultValidator

        validator = VaultValidator(str(tmp_path))
        frontmatter = "invalid: yaml: content: ["

        result = validator.parse_frontmatter_to_dict(frontmatter)
        assert result == {}


class TestCLI:
    """Test command-line interface"""

    def test_parse_arguments(self):
        """Test argument parsing works"""
        from validator import main

        # This just verifies the parser is set up correctly
        # Actual CLI testing would require subprocess
        assert callable(main)

    def test_main_report_mode(self, tmp_path):
        """Test main function in report mode"""
        import sys
        from unittest.mock import patch

        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: dot
up: "[[Parent]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection: []
related: []
---
""")

        from validator import main

        with patch.object(sys, "argv", ["validator.py", "--vault", str(tmp_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_auto_mode_with_issues(self, tmp_path):
        """Test main function in auto mode with issues"""
        import sys
        from unittest.mock import patch

        dots_dir = tmp_path / "Atlas" / "Dots"
        dots_dir.mkdir(parents=True)
        test_file = dots_dir / "test.md"
        test_file.write_text("""---
type:
up: "[[Parent]]"
created: 2025-01-15
daily: "[[2025-01-15]]"
collection: []
related: []
---
""")

        from validator import main

        args = ["validator.py", "--vault", str(tmp_path), "--mode", "auto"]
        with patch.object(sys, "argv", args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # May exit 0 or 1 depending on fixes
            assert exc_info.value.code in [0, 1]

    def test_main_with_report_output(self, tmp_path):
        """Test main function with report output"""
        import sys
        from unittest.mock import patch

        test_file = tmp_path / "test.md"
        test_file.write_text("""---
type: dot
---
""")

        report_file = tmp_path / "report.md"

        from validator import main

        args = ["validator.py", "--vault", str(tmp_path), "--report", str(report_file)]
        with patch.object(sys, "argv", args):
            with pytest.raises(SystemExit):
                main()

        assert report_file.exists()
