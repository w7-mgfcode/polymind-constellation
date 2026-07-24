#!/usr/bin/env python3
"""Provider-SDK-free reference harness for discovery and activation only."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from polymind.catalog import (
    CatalogError,
    activate_skill,
    catalog_document,
    read_resource,
    render_activation,
    render_catalog,
    render_resource_json,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=Path("skills"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="return compact session-start metadata")
    activate = commands.add_parser("activate", help="return one SKILL.md and its manifest")
    activate.add_argument("name")
    resource = commands.add_parser("resource", help="return one bounded package resource")
    resource.add_argument("name")
    resource.add_argument("path")
    resource.add_argument("--max-bytes", type=int, default=256 * 1024)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "list":
            print(render_catalog(catalog_document(args.skills_root), "json"), end="")
        elif args.command == "activate":
            document = activate_skill(args.skills_root, args.name)
            print(render_activation(document, "json"), end="")
        elif args.command == "resource":
            record, content = read_resource(
                args.skills_root, args.name, args.path, max_bytes=args.max_bytes
            )
            print(render_resource_json(record, content), end="")
        else:  # pragma: no cover - argparse owns the command choices
            raise AssertionError(f"unhandled command: {args.command}")
    except CatalogError as error:
        print(f"harness error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
