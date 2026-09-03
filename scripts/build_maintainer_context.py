#!/usr/bin/env python3
"""Generate maintainer-facing agent context for the System repository."""

from __future__ import annotations

import argparse
from pathlib import Path

ADAPTERS = ("AGENTS.md", "CLAUDE.md")
NOTICE = "> This file is generated from `MAINTAINER_RULES.md`. Edit that source, then run `python3 scripts/build_maintainer_context.py`."


def render_context(source: str) -> str:
    body = source.strip()
    return f"# AI OS System authoring context\n\n{NOTICE}\n\n{body}\n"


def build(*, root: Path, check: bool) -> list[str]:
    source_path = root / "MAINTAINER_RULES.md"
    if not source_path.exists():
        raise FileNotFoundError(f"Missing canonical source: {source_path}")
    rendered = render_context(source_path.read_text(encoding="utf-8"))
    changed: list[str] = []
    for name in ADAPTERS:
        target = root / name
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current != rendered:
            changed.append(name)
            if not check:
                target.write_text(rendered, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    changed = build(root=root, check=args.check)
    if args.check:
        if changed:
            print("Maintainer context is out of date: " + ", ".join(changed))
            return 1
        print("Maintainer context is up to date")
        return 0
    if changed:
        print("Generated: " + ", ".join(changed))
    else:
        print("Maintainer context already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
