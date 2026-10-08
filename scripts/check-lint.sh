#!/usr/bin/env bash
# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

if [[ $# != 1 ]]; then
  echo 'Usage: scripts/check-lint.sh module' >&2
  exit 2
fi
module=$1
case "$module" in
  highwayhash|sha256-simd|simdjson-go|sio|crc64nvme|md5-simd|md5-simd/_gen|simdjson-go/benchmarks) ;;
  *) echo "Unknown module: $module" >&2; exit 2 ;;
esac
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
config="$repo_dir/.golangci.yml"
case "$module" in
  highwayhash|sio) config="$repo_dir/$module/.golangci.yml" ;;
esac
export GOWORK=off GOTOOLCHAIN=local
export GOFLAGS="${GOFLAGS:-} -mod=readonly"
cd "$repo_dir/$module"
printf 'Linting %s with %s\n' "$module" "${config#"$repo_dir"/}"
golangci-lint config verify --config "$config"
golangci-lint run --config "$config" --timeout 5m ./...
if [[ "$module" == highwayhash ]]; then
  # goimports moved from a linter to a formatter in golangci-lint v2.
  # --diff prints the difference and exits nonzero, without modifying files.
  golangci-lint fmt --config "$config" --diff ./...
fi
