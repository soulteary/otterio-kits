#!/usr/bin/env python3
"""Require fixed, consistent Actions versions in all root CI configuration."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path
import re
import sys

repo = Path(__file__).resolve().parents[1]
manifest = json.loads((repo / ".github/ci-tools.json").read_text(encoding="utf-8"))
expected = manifest["actions"]
uses = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)")
fixed_ref = re.compile(r"v\d+\.\d+\.\d+|[0-9a-f]{40}")
errors = []
seen = set()
for path in sorted((repo / ".github").rglob("*")):
    if path.suffix not in (".yml", ".yaml"):
        continue
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = uses.match(line)
        if not match:
            continue
        value = match.group(1)
        if value.startswith("./"):
            continue
        location = f"{path.relative_to(repo)}:{number}"
        if "@" not in value:
            errors.append(f"{location}: unversioned action {value}")
            continue
        action, ref = value.rsplit("@", 1)
        seen.add(action)
        if action not in expected:
            errors.append(f"{location}: {action} is missing from .github/ci-tools.json")
        elif ref != expected[action]:
            errors.append(f"{location}: {value}; expected {action}@{expected[action]}")
        if not fixed_ref.fullmatch(ref):
            errors.append(f"{location}: action ref must be an exact release or full SHA: {ref}")
codeql = {ref for action, ref in expected.items() if action.startswith("github/codeql-action/")}
if len(codeql) != 1:
    errors.append("All CodeQL actions must use the same version in the manifest")
for action, ref in expected.items():
    if not fixed_ref.fullmatch(ref):
        errors.append(f"Manifest contains a floating action ref: {action}@{ref}")
for name, entry in manifest["go_tools"].items():
    if entry["version"] in ("latest", "main", "master") or not entry["version"].startswith("v"):
        errors.append(f"Manifest contains a floating Go tool version: {name}")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"CI action versions verified: {len(seen)} action types; one CodeQL version.")
