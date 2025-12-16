"""Inspect firebase.json for syntax or schema errors."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from biome_desktop.transport.config import FirebaseConfig


def _format_context(lines: list[str], lineno: int, colno: int, *, radius: int = 2) -> str:
    start = max(0, lineno - 1 - radius)
    end = min(len(lines), lineno + radius)
    snippet: list[str] = []
    for idx in range(start, end):
        prefix = ">" if idx == lineno - 1 else " "
        line_text = lines[idx]
        snippet.append(f"{prefix} {idx + 1:4d} | {line_text}")
        if idx == lineno - 1:
            marker_padding = " " * (colno - 1)
            gutter = "      "  # aligns with line numbers above
            snippet.append(f"  {gutter}{marker_padding}^")
    return "\n".join(snippet)


def _inspect_file(path: Path) -> int:
    if not path.exists():
        print(f"Config file not found at: {path}")
        return 1

    raw_text = path.read_text(encoding="utf-8")
    try:
        json.loads(raw_text)
    except json.JSONDecodeError as exc:
        lines = raw_text.splitlines()
        context = _format_context(lines, exc.lineno, exc.colno)
        print("JSON syntax error:")
        print(f"  {exc.msg} (line {exc.lineno}, column {exc.colno})")
        print(context)
        return 1

    try:
        FirebaseConfig.load(path)
    except ValueError as exc:
        print("Config structure error:")
        print(f"  {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print("Unexpected error while validating config:")
        print(f"  {exc}")
        return 1

    print("firebase.json looks valid.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check firebase.json for syntax issues.")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.home() / ".biome" / "firebase.json",
        help="Path to firebase.json (defaults to ~/.biome/firebase.json).",
    )
    args = parser.parse_args()
    return _inspect_file(args.path.expanduser().resolve())


if __name__ == "__main__":
    raise SystemExit(main())
