#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Reporter module for vault validation.

This module handles validation reporting:
- Summary generation
- Detailed markdown reports
- JSONL audit logging
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ValidationReporter:
    """Handles validation report generation and logging."""

    def __init__(
        self,
        vault_path: Path,
        mode: str,
        methodology: str = "default",
    ):
        """Initialize reporter.

        Args:
            vault_path: Path to the vault root
            mode: Validation mode (report/auto/interactive)
            methodology: Methodology name from settings
        """
        self.vault_path = vault_path
        self.mode = mode
        self.methodology = methodology

    def generate_summary(self, issues: dict[str, list[str]]) -> dict[str, Any]:
        """Generate and print validation summary.

        Args:
            issues: Dictionary mapping issue type to list of affected files

        Returns:
            Summary dictionary with total_issues and issues_by_type
        """
        total_issues = sum(len(v) for v in issues.values())

        summary = {
            "total_issues": total_issues,
            "issues_by_type": {k: len(v) for k, v in issues.items() if v},
        }

        print("\n" + "=" * 60)
        print("  VALIDATION SUMMARY")
        print("=" * 60 + "\n")

        if total_issues == 0:
            print("  No issues found! Vault is compliant with standards.\n")
        else:
            print(f"  Found {total_issues} issues:\n")
            for issue_type, files in issues.items():
                if files:
                    count = len(files)
                    print(f"  - {issue_type.replace('_', ' ').title()}: {count}")

        print("\n" + "=" * 60 + "\n")

        return summary

    def generate_report(
        self,
        issues: dict[str, list[str]],
        output_path: str | None = None,
    ) -> str:
        """Generate detailed markdown report.

        Args:
            issues: Dictionary mapping issue type to list of affected files
            output_path: Optional path to save the report

        Returns:
            Markdown report content
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_issues = sum(len(v) for v in issues.values())

        report = f"""# Vault Validation Report

**Date**: {timestamp}
**Mode**: {self.mode}
**Methodology**: {self.methodology}
**Total Issues**: {total_issues}

---

## Summary

"""

        for issue_type, files in issues.items():
            if files:
                report += f"\n### {issue_type.replace('_', ' ').title()} ({len(files)} files)\n\n"
                for file_path in files[:10]:  # Limit to first 10
                    report += f"- `{file_path}`\n"
                if len(files) > 10:
                    report += f"\n... and {len(files) - 10} more\n"

        if output_path:
            Path(output_path).write_text(report)
            print(f"  Report saved to: {output_path}")

        return report

    def get_default_jsonl_path(self) -> Path:
        """Get default JSONL log path: .claude/logs/validate.jsonl"""
        return self.vault_path / ".claude" / "logs" / "validate.jsonl"

    def log_to_jsonl(
        self,
        issues: dict[str, list[str]],
        output_path: str | Path | None = None,
        fixes_applied: int = 0,
    ) -> None:
        """Append validation result as JSON line to JSONL file for audit trail.

        Each line is a complete JSON object with:
        - timestamp: ISO format datetime
        - vault_path: Absolute path to vault
        - mode: Validation mode (report/auto/interactive)
        - total_issues: Count of all issues found
        - issues_by_type: Dict of issue type -> count
        - issues_detail: Dict of issue type -> list of affected files
        - fixes_applied: Number of auto-fixes applied (if mode=auto)
        - methodology: Methodology from settings

        Args:
            issues: Dictionary mapping issue type to list of affected files
            output_path: Path to JSONL file. If None, uses default .claude/logs/validate.jsonl
            fixes_applied: Number of fixes applied in auto mode
        """
        timestamp = datetime.now().isoformat()
        total_issues = sum(len(v) for v in issues.values())

        log_entry = {
            "timestamp": timestamp,
            "vault_path": str(self.vault_path.absolute()),
            "mode": self.mode,
            "methodology": self.methodology,
            "total_issues": total_issues,
            "issues_by_type": {k: len(v) for k, v in issues.items() if v},
            "issues_detail": {k: v for k, v in issues.items() if v},
            "fixes_applied": fixes_applied,
        }

        # Use default path if not specified
        jsonl_path = Path(output_path) if output_path else self.get_default_jsonl_path()

        # Create parent directories if they don't exist
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to JSONL file (create if doesn't exist)
        with open(jsonl_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"  Logged to JSONL: {jsonl_path}")
