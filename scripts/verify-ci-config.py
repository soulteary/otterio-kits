#!/usr/bin/env python3
"""Require fixed, consistent Actions versions in parsed CI configuration."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
from pathlib import Path
import re
import sys

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode


FIXED_REF = re.compile(r"v\d+\.\d+\.\d+|[0-9a-f]{40}")
EXACT_GO_VERSION = re.compile(r"v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")
EXACT_PYTHON_VERSION = re.compile(r"\d+\.\d+\.\d+")


def values(node, key):
    """Read mapping keys semantically, retaining duplicates and source marks."""
    if isinstance(node, MappingNode):
        for name, value in node.value:
            if isinstance(name, ScalarNode) and name.value == key:
                yield value


def action_references(document):
    """Inspect workflow jobs/steps and composite steps, not run/env text."""
    for jobs in values(document, "jobs"):
        if not isinstance(jobs, MappingNode):
            continue
        for _, job in jobs.value:
            yield from values(job, "uses")
            for steps in values(job, "steps"):
                if isinstance(steps, SequenceNode):
                    for step in steps.value:
                        yield from values(step, "uses")
    for runs in values(document, "runs"):
        for steps in values(runs, "steps"):
            if isinstance(steps, SequenceNode):
                for step in steps.value:
                    yield from values(step, "uses")


def verify(repo):
    manifest = json.loads((repo / ".github/ci-tools.json").read_text(encoding="utf-8"))
    expected = manifest["actions"]
    errors, seen = [], set()
    paths = list((repo / ".github/workflows").glob("*.y*ml"))
    paths.extend(path for path in (repo / ".github/actions").rglob("*")
                 if path.name in ("action.yml", "action.yaml"))
    for path in sorted(paths):
        if path.suffix not in (".yml", ".yaml"):
            continue
        try:
            # Aliases resolve to nodes; no YAML object constructors execute.
            document = yaml.compose(path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader)
        except yaml.YAMLError as error:
            errors.append(f"{path.relative_to(repo)}: invalid YAML: {error}")
            continue
        for node in action_references(document):
            location = f"{path.relative_to(repo)}:{node.start_mark.line + 1}"
            if not isinstance(node, ScalarNode) or node.tag != "tag:yaml.org,2002:str":
                errors.append(f"{location}: uses must be a string")
                continue
            value = node.value.strip()
            if value.startswith("./"):
                continue
            if "@" not in value:
                errors.append(f"{location}: unversioned action {value}")
                continue
            action, ref = value.rsplit("@", 1)
            seen.add(action)
            if action not in expected:
                errors.append(f"{location}: {action} is missing from .github/ci-tools.json")
            elif ref != expected[action]:
                errors.append(f"{location}: {value}; expected {action}@{expected[action]}")
            if not FIXED_REF.fullmatch(ref):
                errors.append(f"{location}: action ref must be an exact release or full SHA: {ref}")
    codeql = {ref for action, ref in expected.items() if action.startswith("github/codeql-action/")}
    if len(codeql) != 1:
        errors.append("All CodeQL actions must use the same version in the manifest")
    for action, ref in expected.items():
        if not isinstance(ref, str) or not FIXED_REF.fullmatch(ref):
            errors.append(f"Manifest contains a floating action ref: {action}@{ref}")
    for name, entry in manifest["go_tools"].items():
        version = entry["version"]
        if not isinstance(version, str) or not EXACT_GO_VERSION.fullmatch(version):
            errors.append(f"Manifest contains a floating Go tool version: {name}")
    for name, version in manifest.get("cli_versions", {}).items():
        if not isinstance(version, str) or not EXACT_GO_VERSION.fullmatch(version):
            errors.append(f"Manifest contains a floating CLI version: {name}")
    for name, version in manifest.get("python_tools", {}).items():
        if not isinstance(version, str) or not EXACT_PYTHON_VERSION.fullmatch(version):
            errors.append(f"Manifest contains a floating Python tool version: {name}")
    return errors, seen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        errors, seen = verify(args.repo.resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"CI configuration failed: {error}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"CI action versions verified: {len(seen)} action types; one CodeQL version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
