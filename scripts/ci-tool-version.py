#!/usr/bin/env python3
"""Read a fixed tool version from the shared CI manifest."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tool")
parser.add_argument("--field", choices=("version", "package"), default="version")
args = parser.parse_args()
manifest = json.loads((Path(__file__).resolve().parents[1] / ".github/ci-tools.json").read_text())
if args.tool in manifest["go_tools"]:
    print(manifest["go_tools"][args.tool][args.field])
elif args.field == "version" and args.tool in manifest["cli_versions"]:
    print(manifest["cli_versions"][args.tool])
else:
    parser.error(f"Unknown tool or field: {args.tool}/{args.field}")
