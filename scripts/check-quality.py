#!/usr/bin/env python3
"""Check one Go module's complete formatting, vet or tidy metadata."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
from pathlib import Path
import subprocess
import sys

MODULES = ("highwayhash", "sha256-simd", "simdjson-go", "sio", "crc64nvme", "md5-simd",
           "md5-simd/_gen", "simdjson-go/benchmarks")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("mode", choices=("format", "vet", "tidy"))
parser.add_argument("module", choices=MODULES)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
directory = repo / args.module
env = {**os.environ, "GOWORK": "off", "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly"}
print(f"[{args.mode}] {args.module}", flush=True)
if args.mode == "format":
    files = []
    for current, children, names in os.walk(directory):
        # A nested go.mod is checked by that module's own quality job.
        children[:] = [name for name in children if name not in (".git", "vendor")
                       and not (Path(current) / name / "go.mod").is_file()]
        files.extend(str(Path(current) / name) for name in sorted(names) if name.endswith(".go"))
    result = subprocess.run(["gofmt", "-l", *files], text=True, capture_output=True, env=env)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.stdout:
        print(result.stdout, end="")
        print("Run gofmt on these files, including generated Go declarations.", file=sys.stderr)
    sys.exit(1 if result.stdout else result.returncode)
command = ["go", "vet", "./..."] if args.mode == "vet" else ["go", "mod", "tidy", "-diff"]
sys.exit(subprocess.run(command, cwd=directory, env=env).returncode)
