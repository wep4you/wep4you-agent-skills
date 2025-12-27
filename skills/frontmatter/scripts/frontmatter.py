#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Frontmatter Property Management for Obsidian Vault

Manages core and type-specific frontmatter properties:
- List, add, and remove core properties
- Manage type-specific properties
- Configure validation rules and defaults
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

# Default core properties embedded in script
DEFAULT_CORE_PROPERTIES = {
    "type": {"required": True, "type": "string", "description": "Note type classification"},
    "up": {
        "required": False,
        "type": "wikilink",
        "description": "Parent note in hierarchy",
    },
    "created": {
        "required": True,
        "type": "date",
        "format": "YYYY-MM-DD",
        "description": "Creation date",
    },
    "daily": {
        "required": False,
        "type": "wikilink",
        "description": "Associated daily note",
    },
    "collection": {
        "required": False,
        "type": "wikilink",
        "description": "Collection classification",
    },
    "related": {
        "required": False,
        "type": "list[wikilink]",
        "description": "Related notes",
    },
}

# Default type-specific properties
DEFAULT_TYPE_PROPERTIES = {
    "dot": {
        "tags": {"required": False, "type": "list[string]", "description": "Topic tags"},
    },
    "map": {
        "tags": {"required": False, "type": "list[string]", "description": "Topic tags"},
        "summary": {
            "required": False,
            "type": "string",
            "description": "Map summary",
        },
    },
    "source": {
        "author": {"required": False, "type": "string", "description": "Source author"},
        "url": {"required": False, "type": "string", "description": "Source URL"},
        "published": {
            "required": False,
            "type": "date",
            "format": "YYYY-MM-DD",
            "description": "Publication date",
        },
    },
    "project": {
        "status": {
            "required": True,
            "type": "string",
            "values": ["active", "completed", "archived", "planning"],
            "description": "Project status",
        },
        "deadline": {
            "required": False,
            "type": "date",
            "format": "YYYY-MM-DD",
            "description": "Project deadline",
        },
    },
    "daily": {
        "mood": {
            "required": False,
            "type": "string",
            "values": ["great", "good", "neutral", "bad"],
            "description": "Daily mood",
        },
    },
}


class FrontmatterManager:
    """Manages frontmatter property definitions and validation rules"""

    def __init__(self, vault_path: Optional[str] = None) -> None:  # noqa: UP007
        """
        Initialize frontmatter manager

        Args:
            vault_path: Path to vault (default: current directory)
        """
        self.vault_path = Path(vault_path) if vault_path else Path.cwd()
        self.config_dir = self.vault_path / ".claude" / "config"
        self.config_file = self.config_dir / "frontmatter.yaml"

        self.core_properties = DEFAULT_CORE_PROPERTIES.copy()
        self.type_properties = DEFAULT_TYPE_PROPERTIES.copy()

        self.load_config()

    def load_config(self) -> None:
        """Load frontmatter configuration from file"""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)

            if not config:
                return

            # Merge with defaults
            if "core_properties" in config:
                self.core_properties.update(config["core_properties"])

            if "type_properties" in config:
                self.type_properties.update(config["type_properties"])

        except yaml.YAMLError as e:
            print(f"Warning: Invalid config file: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}", file=sys.stderr)

    def save_config(self) -> None:
        """Save current configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "core_properties": self.core_properties,
            "type_properties": self.type_properties,
        }

        with open(self.config_file, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"Configuration saved to {self.config_file}")

    def list_core_properties(self, output_format: str = "text") -> None:
        """
        List all core properties

        Args:
            output_format: Output format (text, json, yaml)
        """
        if output_format == "json":
            print(json.dumps(self.core_properties, indent=2))
        elif output_format == "yaml":
            print(yaml.dump(self.core_properties, default_flow_style=False, sort_keys=False))
        else:
            print("\nCore Properties:")
            print("=" * 80)
            for name, spec in self.core_properties.items():
                required = "Required" if spec.get("required", False) else "Optional"
                prop_type = spec.get("type", "unknown")
                desc = spec.get("description", "")

                print(f"\n{name}:")
                print(f"  Type: {prop_type}")
                print(f"  Required: {required}")
                if "format" in spec:
                    print(f"  Format: {spec['format']}")
                if desc:
                    print(f"  Description: {desc}")

    def add_core_property(
        self,
        name: str,
        prop_type: str,
        required: bool = False,
        description: str = "",
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Add or update a core property

        Args:
            name: Property name
            prop_type: Property type (string, date, wikilink, list[wikilink], etc.)
            required: Whether property is required
            description: Property description
            **kwargs: Additional property specifications (format, values, etc.)
        """
        self.core_properties[name] = {
            "required": required,
            "type": prop_type,
            "description": description,
            **kwargs,
        }

        print(f"Added/updated core property: {name}")

    def remove_core_property(self, name: str) -> None:
        """
        Remove a core property

        Args:
            name: Property name to remove
        """
        if name not in self.core_properties:
            print(f"Error: Property '{name}' not found", file=sys.stderr)
            sys.exit(1)

        del self.core_properties[name]
        print(f"Removed core property: {name}")

    def list_type_properties(
        self, note_type: Optional[str] = None, output_format: str = "text"  # noqa: UP007
    ) -> None:
        """
        List type-specific properties

        Args:
            note_type: Specific type to show (None for all)
            output_format: Output format (text, json, yaml)
        """
        if note_type:
            if note_type not in self.type_properties:
                print(f"Error: Type '{note_type}' not found", file=sys.stderr)
                sys.exit(1)

            data = {note_type: self.type_properties[note_type]}
        else:
            data = self.type_properties

        if output_format == "json":
            print(json.dumps(data, indent=2))
        elif output_format == "yaml":
            print(yaml.dump(data, default_flow_style=False, sort_keys=False))
        else:
            print("\nType-Specific Properties:")
            print("=" * 80)

            for type_name, properties in data.items():
                print(f"\n{type_name}:")
                if not properties:
                    print("  (no additional properties)")
                    continue

                for prop_name, spec in properties.items():
                    required = "Required" if spec.get("required", False) else "Optional"
                    prop_type = spec.get("type", "unknown")
                    desc = spec.get("description", "")

                    print(f"\n  {prop_name}:")
                    print(f"    Type: {prop_type}")
                    print(f"    Required: {required}")
                    if "format" in spec:
                        print(f"    Format: {spec['format']}")
                    if "values" in spec:
                        print(f"    Values: {', '.join(spec['values'])}")
                    if desc:
                        print(f"    Description: {desc}")

    def add_type_property(
        self,
        note_type: str,
        name: str,
        prop_type: str,
        required: bool = False,
        description: str = "",
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Add or update a type-specific property

        Args:
            note_type: Note type (dot, map, source, etc.)
            name: Property name
            prop_type: Property type
            required: Whether property is required
            description: Property description
            **kwargs: Additional specifications
        """
        if note_type not in self.type_properties:
            self.type_properties[note_type] = {}

        self.type_properties[note_type][name] = {
            "required": required,
            "type": prop_type,
            "description": description,
            **kwargs,
        }

        print(f"Added/updated property '{name}' for type '{note_type}'")

    def remove_type_property(self, note_type: str, name: str) -> None:
        """
        Remove a type-specific property

        Args:
            note_type: Note type
            name: Property name to remove
        """
        if note_type not in self.type_properties:
            print(f"Error: Type '{note_type}' not found", file=sys.stderr)
            sys.exit(1)

        if name not in self.type_properties[note_type]:
            print(f"Error: Property '{name}' not found for type '{note_type}'", file=sys.stderr)
            sys.exit(1)

        del self.type_properties[note_type][name]
        print(f"Removed property '{name}' from type '{note_type}'")

    def list_types(self) -> None:
        """List all configured note types"""
        print("\nConfigured Note Types:")
        print("=" * 80)

        for type_name in sorted(self.type_properties.keys()):
            prop_count = len(self.type_properties[type_name])
            print(f"  {type_name}: {prop_count} additional properties")

    def get_required_properties(self, note_type: Optional[str] = None) -> dict[str, Any]:  # noqa: UP007
        """
        Get all required properties for a note type

        Args:
            note_type: Note type (None for core only)

        Returns:
            Dictionary of required properties
        """
        required = {
            name: spec for name, spec in self.core_properties.items() if spec.get("required", False)
        }

        if note_type and note_type in self.type_properties:
            type_required = {
                name: spec
                for name, spec in self.type_properties[note_type].items()
                if spec.get("required", False)
            }
            required.update(type_required)

        return required


def main() -> None:
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Frontmatter Property Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--vault",
        default=".",
        help="Path to vault (default: current directory)",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        help="Output format (default: text)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Core properties commands
    subparsers.add_parser("list-core", help="List core properties")

    add_core = subparsers.add_parser("add-core", help="Add core property")
    add_core.add_argument("name", help="Property name")
    add_core.add_argument("type", help="Property type")
    add_core.add_argument("--required", action="store_true", help="Mark as required")
    add_core.add_argument("--description", default="", help="Property description")
    add_core.add_argument("--format", dest="prop_format", help="Property format (e.g., YYYY-MM-DD)")

    remove_core = subparsers.add_parser("remove-core", help="Remove core property")
    remove_core.add_argument("name", help="Property name")

    # Type properties commands
    list_type = subparsers.add_parser("list-type", help="List type properties")
    list_type.add_argument("type", nargs="?", help="Note type (optional)")

    add_type = subparsers.add_parser("add-type-prop", help="Add type-specific property")
    add_type.add_argument("note_type", help="Note type")
    add_type.add_argument("name", help="Property name")
    add_type.add_argument("prop_type", help="Property type")
    add_type.add_argument("--required", action="store_true", help="Mark as required")
    add_type.add_argument("--description", default="", help="Property description")

    remove_type = subparsers.add_parser("remove-type-prop", help="Remove type-specific property")
    remove_type.add_argument("note_type", help="Note type")
    remove_type.add_argument("name", help="Property name")

    # Utility commands
    subparsers.add_parser("list-types", help="List all note types")

    get_required = subparsers.add_parser("get-required", help="Get required properties")
    get_required.add_argument("type", nargs="?", help="Note type (optional)")

    # Save command
    subparsers.add_parser("save", help="Save configuration to file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    manager = FrontmatterManager(args.vault)

    try:
        if args.command == "list-core":
            manager.list_core_properties(args.format)

        elif args.command == "add-core":
            kwargs = {}
            if args.prop_format:
                kwargs["format"] = args.prop_format

            manager.add_core_property(
                args.name,
                args.type,
                required=args.required,
                description=args.description,
                **kwargs,
            )
            manager.save_config()

        elif args.command == "remove-core":
            manager.remove_core_property(args.name)
            manager.save_config()

        elif args.command == "list-type":
            manager.list_type_properties(args.type, args.format)

        elif args.command == "add-type-prop":
            manager.add_type_property(
                args.note_type,
                args.name,
                args.prop_type,
                required=args.required,
                description=args.description,
            )
            manager.save_config()

        elif args.command == "remove-type-prop":
            manager.remove_type_property(args.note_type, args.name)
            manager.save_config()

        elif args.command == "list-types":
            manager.list_types()

        elif args.command == "get-required":
            required = manager.get_required_properties(args.type)
            if args.format == "json":
                print(json.dumps(required, indent=2))
            elif args.format == "yaml":
                print(yaml.dump(required, default_flow_style=False, sort_keys=False))
            else:
                type_label = f" for type '{args.type}'" if args.type else ""
                print(f"\nRequired Properties{type_label}:")
                print("=" * 80)
                for name, spec in required.items():
                    print(f"  {name}: {spec.get('type', 'unknown')}")

        elif args.command == "save":
            manager.save_config()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
