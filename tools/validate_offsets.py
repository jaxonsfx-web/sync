#!/usr/bin/env python3
"""Offline sanity checks for offset data files. Does not inspect or modify processes.

Supported inputs:
  - JSON objects/arrays containing numeric offset fields
  - C/C++ headers with numeric #define / constexpr / const declarations

This checks formatting and suspicious values only; it cannot prove an offset is
correct for a particular application build.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MAX_OFFSET = (1 << 64) - 1
OFFSET_WORDS = re.compile(r"(?:offset|address|addr|size|stride|rva|va|base)", re.I)
DECL = re.compile(
    r"^\s*(?:#\s*define\s+([A-Za-z_]\w*)\s+([^\s/]+)"
    r"|(?:inline\s+)?(?:static\s+)?(?:constexpr|const)\s+"
    r"(?:unsigned\s+)?(?:char|short|int|long|size_t|uintptr_t|uint(?:8|16|32|64)_t)"
    r"\s+([A-Za-z_]\w*)\s*=\s*([^;]+);)",
    re.M,
)
NUMERIC = re.compile(r"^(?:0[xX][0-9a-fA-F]+|0[bB][01]+|[0-9]+)[uUlL]*$")


def parse_number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        s = value.strip().replace("_", "")
        s = re.sub(r"[uUlL]+$", "", s)
        if NUMERIC.fullmatch(s):
            try:
                return int(s, 0) if s.startswith(("0x", "0X", "0b", "0B")) else int(s, 10)
            except ValueError:
                return None
    return None


def walk_json(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, item in value.items():
            here = f"{path}.{key}"
            number = parse_number(item)
            if OFFSET_WORDS.search(str(key)) and number is not None:
                yield here, number
            yield from walk_json(item, here)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from walk_json(item, f"{path}[{i}]")


def validate_json(path: Path) -> tuple[int, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return 0, [f"ERROR: cannot parse JSON: {exc}"]
    entries = list(walk_json(data))
    return len(entries), check_entries(entries)


def validate_header(path: Path) -> tuple[int, list[str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return 0, [f"ERROR: cannot read file: {exc}"]
    entries = []
    names: dict[str, int] = {}
    issues = []
    for match in DECL.finditer(source):
        name = match.group(1) or match.group(3)
        raw = (match.group(2) or match.group(4)).strip()
        if not OFFSET_WORDS.search(name):
            continue
        # Remove simple C++ integer casts and parentheses around a literal.
        raw = re.sub(r"^\([^()]+\)\s*", "", raw).strip("() ")
        number = parse_number(raw)
        if number is None:
            issues.append(f"INFO: {name}: non-literal value skipped ({raw[:50]})")
            continue
        if name in names:
            issues.append(f"WARNING: duplicate identifier {name} (also {names[name]})")
        names[name] = source.count("\n", 0, match.start()) + 1
        entries.append((name, number))
    return len(entries), issues + check_entries(entries)


def check_entries(entries) -> list[str]:
    issues = []
    seen: dict[str, int] = {}
    for name, value in entries:
        if value < 0:
            issues.append(f"WARNING: {name}: negative value {value}")
        elif value > MAX_OFFSET:
            issues.append(f"WARNING: {name}: exceeds unsigned 64-bit range")
        if isinstance(name, str):
            if name in seen and seen[name] != value:
                issues.append(f"WARNING: duplicate path/name {name} has differing values")
            seen[name] = value
    if not issues:
        issues.append("OK: no obvious formatting or range issues found")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="JSON offset dump or C/C++ header")
    args = parser.parse_args()
    path = args.file
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    if path.suffix.lower() == ".json":
        count, issues = validate_json(path)
    elif path.suffix.lower() in {".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc"}:
        count, issues = validate_header(path)
    else:
        print("ERROR: supported file types are .json, .h, .hpp, .hh, .hxx, .cpp, .cc", file=sys.stderr)
        return 2
    print(f"Sync Offset Validator — {path}")
    print(f"Numeric offset-like values checked: {count}")
    for issue in issues:
        print(issue)
    print("Note: a clean report does not confirm that offsets match any live build.")
    return 1 if any(line.startswith("ERROR:") for line in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
