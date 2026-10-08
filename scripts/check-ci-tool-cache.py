#!/usr/bin/env python3
"""Accept only a pinned Go tool built for the current compiler and target."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
import subprocess
import sys


TARGET_KEYS = ("GOOS", "GOARCH", "CGO_ENABLED", "GOAMD64", "GOARM64")


def matches(info, package, version, environment):
    settings = {item["Key"]: item.get("Value", "") for item in info.get("Settings", [])}
    return (
        info.get("Path") == package
        and info.get("Main", {}).get("Version") == version
        and info.get("GoVersion") == environment["GOVERSION"]
        and all(settings.get(key, "") == environment.get(key, "") for key in TARGET_KEYS)
    )


def main():
    tool, binary = sys.argv[1:]
    repo = Path(__file__).resolve().parents[1]
    entry = json.loads((repo / ".github/ci-tools.json").read_text())["go_tools"][tool]
    # Use the installer's environment rather than the caller's module flags.
    environment = dict(os.environ, GOWORK="off", GOTOOLCHAIN="local", GOFLAGS="")
    try:
        current = json.loads(subprocess.check_output(
            ["go", "env", "-json", "GOVERSION", *TARGET_KEYS], env=environment))
        info = json.loads(subprocess.check_output(
            ["go", "version", "-m", "-json", binary], env=environment,
            stderr=subprocess.DEVNULL))
        return 0 if matches(info, entry["package"], entry["version"], current) else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        return 1


if __name__ == "__main__":
    sys.exit(main())
