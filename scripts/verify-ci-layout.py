#!/usr/bin/env python3
"""Reject workflows restored inside imported subtrees."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
from pathlib import Path
import sys


def verify(repo):
    manifest = json.loads((repo / "UPSTREAMS.json").read_text(encoding="utf-8"))
    failures = []
    for module in manifest["modules"]:
        directory = module["directory"]
        module_dir = repo / directory
        if not module_dir.is_dir():
            failures.append(f"Missing module directory: {directory}")
            continue
        # Include nested tooling modules and both spellings: an incorrectly
        # named workflow directory is also unwanted imported CI configuration.
        for github_dir in sorted(module_dir.rglob(".github")):
            for name in ("workflows", "workflow"):
                path = github_dir / name
                if path.exists() or path.is_symlink():
                    failures.append(str(path.relative_to(repo)))
    if failures:
        print("CI layout failed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print("Keep executable workflows in the root .github/workflows. "
              "Remove imported subtree workflows after an upstream merge; "
              "the original files remain available in the import history.", file=sys.stderr)
        return 1
    print("CI layout verified: no workflows inside imported modules.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        return verify(args.repo.resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"CI layout failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
