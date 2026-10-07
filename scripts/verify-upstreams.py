#!/usr/bin/env python3
"""Verify retained upstream history and import trees without changing Git."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


MODULES = (
    "highwayhash",
    "sha256-simd",
    "simdjson-go",
    "sio",
    "crc64nvme",
    "md5-simd",
)
MODULE_PREFIX = "github.com/soulteary/otterio-kits/"
OBJECT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


class VerificationError(Exception):
    """An invalid manifest or unavailable Git object."""


def git(repo, *args, allow_missing=False):
    env = os.environ.copy()
    # Provenance must use the original objects, not local replacement objects.
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    if result.returncode:
        if allow_missing and result.returncode == 1:
            return None
        detail = result.stderr.strip() or f"exit status {result.returncode}"
        raise VerificationError(f"git {' '.join(args)}: {detail}")
    return result.stdout.strip()


def require_string(mapping, key, context):
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise VerificationError(f"{context}.{key} must be a non-empty string")
    return value


def require_object_id(mapping, key, context):
    value = require_string(mapping, key, context)
    if not OBJECT_ID.fullmatch(value):
        raise VerificationError(f"{context}.{key} must be a full Git object ID")
    return value


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("modules"), list):
        raise VerificationError("UPSTREAMS.json must contain a modules array")
    entries = manifest["modules"]
    if len(entries) != len(MODULES):
        raise VerificationError(f"Expected {len(MODULES)} published modules, found {len(entries)}")
    seen_names, seen_dirs, seen_paths = set(), set(), set()
    validated = []
    for index, entry in enumerate(entries):
        context = f"modules[{index}]"
        if not isinstance(entry, dict):
            raise VerificationError(f"{context} must be an object")
        name = require_string(entry, "name", context)
        directory = require_string(entry, "directory", context)
        module = require_string(entry, "module", context)
        if name not in MODULES:
            raise VerificationError(f"Unexpected published module: {name}")
        if directory != name or module != MODULE_PREFIX + name:
            raise VerificationError(f"{name}: directory or module path does not match the published module")
        if name in seen_names or directory in seen_dirs or module in seen_paths:
            raise VerificationError(f"Duplicate module name, directory or path: {name}")
        seen_names.add(name)
        seen_dirs.add(directory)
        seen_paths.add(module)
        upstream = entry.get("upstream")
        imported = entry.get("import")
        if not isinstance(upstream, dict) or not isinstance(imported, dict):
            raise VerificationError(f"{name}: upstream and import must be objects")
        for key in ("repository", "default_branch", "tag", "history_ref"):
            require_string(upstream, key, f"{name}.upstream")
        baseline = require_object_id(upstream, "commit", f"{name}.upstream")
        tree = require_object_id(upstream, "tree", f"{name}.upstream")
        import_commit = require_object_id(imported, "commit", f"{name}.import")
        count = upstream.get("commit_count")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise VerificationError(f"{name}.upstream.commit_count must be a positive integer")
        expected_ref = f"refs/tags/upstream/{name}/{upstream['tag']}"
        if upstream["history_ref"] != expected_ref:
            raise VerificationError(f"{name}: history_ref must be {expected_ref}")
        if not isinstance(entry.get("licenses"), list) or not entry["licenses"]:
            raise VerificationError(f"{name}.licenses must be a non-empty array")
        validated.append((entry, baseline, tree, import_commit))
    if seen_names != set(MODULES):
        raise VerificationError("The manifest does not contain exactly the six published modules")
    return validated


def read_module_path(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r'\s*module\s+(?:"([^"\n]+)"|(\S+))\s*(?://.*)?', line)
        if match:
            return match.group(1) or match.group(2)
    raise VerificationError(f"No module directive found in {path}")


def verify(repo):
    if Path(git(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise VerificationError(f"{repo} is not the Git repository root")
    if git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise VerificationError("History verification requires a non-shallow clone; fetch full history first")
    git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    manifest_path = repo / "UPSTREAMS.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VerificationError(f"Cannot read {manifest_path}: {error}") from error
    entries = validate_manifest(manifest)
    # Nested benchmark/generator modules are retained upstream tooling, not
    # additional first-level published modules.
    actual_dirs = {path.parent.name for path in repo.glob("*/go.mod")}
    if actual_dirs != set(MODULES) or (repo / "go.mod").exists():
        raise VerificationError(f"Published go.mod inventory mismatch: {sorted(actual_dirs)}")
    all_commits = set()
    total_count = 0
    failures = []
    warnings = []
    for entry, baseline, tree, imported in entries:
        name = entry["name"]
        upstream = entry["upstream"]
        errors = []
        try:
            actual_module = read_module_path(repo / entry["directory"] / "go.mod")
            if actual_module != entry["module"]:
                errors.append(f"go.mod declares {actual_module}, expected {entry['module']}")
            for revision, label in ((baseline, "baseline"), (imported, "import")):
                resolved = git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
                if resolved != revision:
                    errors.append(f"{label} object does not identify the recorded commit")
                if git(repo, "merge-base", "--is-ancestor", revision, "HEAD", allow_missing=True) is None:
                    errors.append(f"{label} commit is not an ancestor of HEAD")
            if git(repo, "merge-base", "--is-ancestor", baseline, imported, allow_missing=True) is None:
                errors.append("baseline commit is not an ancestor of the import commit")
            baseline_tree = git(repo, "rev-parse", "--verify", f"{baseline}^{{tree}}")
            import_tree = git(repo, "rev-parse", "--verify", f"{imported}:{entry['directory']}")
            if git(repo, "cat-file", "-t", tree) != "tree":
                errors.append("recorded upstream tree is not a Git tree object")
            if baseline_tree != tree:
                errors.append(f"baseline tree differs: {baseline_tree}, expected {tree}")
            if import_tree != tree:
                errors.append(f"import subtree differs: {import_tree}, expected {tree}")
            commits = set(git(repo, "rev-list", baseline).splitlines())
            count = int(git(repo, "rev-list", "--count", baseline))
            if count != upstream["commit_count"] or count != len(commits):
                errors.append(f"history count is {count}, expected {upstream['commit_count']}")
            all_commits.update(commits)
            total_count += count
            ref = upstream["history_ref"]
            # show-ref's exit 1 means absent; absence can be legitimate when a
            # consumer cloned without fetching every namespaced upstream tag.
            present = git(repo, "show-ref", "--verify", "--quiet", ref, allow_missing=True)
            if present is None:
                warnings.append(f"{name}: {ref} is absent; retained commit history was still checked")
            elif git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}") != baseline:
                errors.append(f"{ref} does not point to the recorded baseline")
            print(f"[{'FAIL' if errors else 'OK'}] {name}: {count} original upstream commits ({upstream['tag']})")
        except (VerificationError, OSError, UnicodeError, ValueError) as error:
            errors.append(str(error))
            print(f"[FAIL] {name}: history verification incomplete")
        failures.extend(f"{name}: {error}" for error in errors)
    for warning in warnings:
        print(f"[WARN] {warning}")
    print(f"Original history count sum: {total_count}; unique retained upstream commits: {len(all_commits)}")
    if failures:
        for failure in failures:
            print(f"[ERROR] {failure}", file=sys.stderr)
        print("Verification failed; the totals above may be partial.", file=sys.stderr)
        return 1
    print("All six upstream histories and original import trees verified.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1],
        help="repository root (default: parent of scripts/)",
    )
    args = parser.parse_args()
    try:
        return verify(args.repo.resolve())
    except (VerificationError, OSError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
