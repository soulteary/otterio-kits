#!/usr/bin/env bash
# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

if [[ $# != 1 ]]; then
  echo 'Usage: scripts/check-security.sh module' >&2
  exit 2
fi
module=$1
case "$module" in
  highwayhash|sha256-simd|simdjson-go|sio|crc64nvme|md5-simd|md5-simd/_gen|simdjson-go/benchmarks) ;;
  *) echo "Unknown module: $module" >&2; exit 2 ;;
esac
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export GOWORK=off GOTOOLCHAIN=local
export GOFLAGS="${GOFLAGS:-} -mod=readonly"
cd "$repo_dir/$module"
printf 'Scanning %s (including tests) with fixed-version govulncheck\n' "$module"
# Text mode intentionally keeps govulncheck's nonzero exit on reachable
# vulnerabilities. JSON/SARIF output alone always exits zero.
exec govulncheck -test ./...
