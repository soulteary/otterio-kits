#!/usr/bin/env python3
"""Select independent CI matrices from the complete Git event diff."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


RUNTIME = ("highwayhash", "sha256-simd", "simdjson-go", "sio", "crc64nvme", "md5-simd")
AUXILIARY = ("md5-simd/_gen", "simdjson-go/benchmarks")
ALL_MODULES = RUNTIME + AUXILIARY
# Directed dependencies: consumers must be checked when their input changes.
DEPENDENTS = {"simdjson-go": ("simdjson-go/benchmarks",), "md5-simd/_gen": ("md5-simd",)}
AUXILIARY_ENTRIES = (
    {"module": "md5-simd/_gen", "entry": "generator"},
    {"module": "simdjson-go/benchmarks", "entry": "benchmark smoke"},
)
EXTENDED_ENTRIES = (
    {"module": "sha256-simd", "entry": "all Go targets and upstream build tags",
     "mode": "architectures", "arch": "amd64"},
    {"module": "simdjson-go", "entry": "Linux 386 short tests", "mode": "short", "arch": "386"},
    {"module": "crc64nvme", "entry": "Linux 386 short tests", "mode": "short", "arch": "386"},
)
FUZZ_ENTRIES = tuple(
    {"module": module, "target": target}
    for module, targets in (
        ("sio", ("FuzzEncryptDecrypt", "FuzzDecryptMalformed", "FuzzDecryptBuffer",
                 "FuzzReaderWriter", "FuzzPackageBoundaries")),
        ("simdjson-go", ("FuzzParse", "FuzzCorrect", "FuzzSerialize")),
    )
    for target in targets
)
SHA = re.compile(r"[0-9a-f]{40}")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def valid_sha(value):
    return isinstance(value, str) and SHA.fullmatch(value) and value != "0" * 40


def changed_paths(repo, event_name, event):
    """None means a conservative full run; [] is a genuinely empty diff."""
    if event_name in ("schedule", "workflow_dispatch"):
        return None, f"{event_name}: run every module"
    try:
        if event_name == "pull_request":
            pull = event["pull_request"]
            base, head = pull["base"]["sha"], pull["head"]["sha"]
            if not valid_sha(base) or not valid_sha(head):
                return None, "PR comparison is missing a valid base or head: full run"
            base = git(repo, "merge-base", base, head).decode("ascii").strip()
        elif event_name == "push":
            base, head = event["before"], event["after"]
            if not valid_sha(base) or not valid_sha(head):
                return None, "Push comparison is unavailable or a new branch: full run"
        else:
            return None, f"Unsupported event {event_name}: full run"
        # Renames become delete + add, selecting both source and destination.
        # NUL delimiters preserve spaces/newlines; no API pagination/file cap.
        data = git(repo, "diff", "--name-only", "--no-renames", "-z", base, head, "--")
        return [os.fsdecode(path) for path in data.split(b"\0") if path], f"{event_name}: complete Git diff"
    except (KeyError, TypeError, AttributeError, OSError, subprocess.CalledProcessError,
            UnicodeError) as error:
        return None, f"Comparison unavailable ({type(error).__name__}): full run"


def select_modules(paths):
    if paths is None:
        return set(ALL_MODULES), "full selection"
    selected = set()
    # Nested modules own their files; do not automatically select the parent.
    longest_first = sorted(ALL_MODULES, key=len, reverse=True)
    for path in paths:
        module = next((module for module in longest_first
                       if path.startswith(module + "/")), None)
        if module:
            selected.add(module)
        elif path.startswith((".github/", "scripts/")) or path in ("go.work", "go.work.sum", "UPSTREAMS.json"):
            return set(ALL_MODULES), "shared CI, workspace or source policy changed"
        elif path.endswith(".md") and ("/" not in path or path.startswith("docs/")):
            continue
        else:
            # New code/modules and unclassified configuration must not bypass CI.
            return set(ALL_MODULES), "unclassified path changed: full selection"
    pending = list(selected)
    while pending:
        for dependent in DEPENDENTS.get(pending.pop(), ()):
            if dependent not in selected:
                selected.add(dependent)
                pending.append(dependent)
    return selected, "selected modules and directed dependents" if selected else "documentation-only or empty diff"


def matrices(selected):
    return {
        "quality": [module for module in ALL_MODULES if module in selected],
        "runtime": [module for module in RUNTIME if module in selected],
        "auxiliary": [entry for entry in AUXILIARY_ENTRIES if entry["module"] in selected],
        "extended": [entry for entry in EXTENDED_ENTRIES if entry["module"] in selected],
        "fuzz": [entry for entry in FUZZ_ENTRIES if entry["module"] in selected],
        "trivy": ["sio"] if "sio" in selected else [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--event", type=Path, default=os.environ.get("GITHUB_EVENT_PATH"))
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME"))
    parser.add_argument("--output", type=Path, default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()
    if not args.event or not args.event_name:
        parser.error("--event and --event-name (or the GitHub environment) are required")
    try:
        event = json.loads(args.event.read_text(encoding="utf-8"))
        if not isinstance(event, dict):
            raise ValueError("The GitHub event must be an object")
        paths, comparison_reason = changed_paths(args.repo, args.event_name, event)
        selected, selection_reason = select_modules(paths)
        outputs = matrices(selected)
        print(f"{comparison_reason}; {selection_reason}")
        print(json.dumps(outputs, indent=2))
        if args.output:
            with args.output.open("a", encoding="utf-8") as stream:
                for name, entries in outputs.items():
                    stream.write(f"{name}={json.dumps(entries, separators=(',', ':'))}\n")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as stream:
                stream.write("### CI module selection\n\n")
                stream.write(f"{comparison_reason}; {selection_reason}.\n\n")
                stream.write("Selected: " + (", ".join(outputs["quality"]) or "none; repository policy still runs") + "\n")
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"CI selection failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
