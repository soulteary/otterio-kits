#!/usr/bin/env bash
# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tool=${1:?Usage: scripts/install-ci-tool.sh tool}
package=$(python3 "$repo_dir/scripts/ci-tool-version.py" "$tool" --field package)
version=$(python3 "$repo_dir/scripts/ci-tool-version.py" "$tool")
export GOBIN=${GOBIN:-${RUNNER_TEMP:-${TMPDIR:-/tmp}}/otterio-ci-bin}
mkdir -p "$GOBIN"
if [[ -x "$GOBIN/$tool" ]] && python3 "$repo_dir/scripts/check-ci-tool-cache.py" "$tool" "$GOBIN/$tool"; then
  printf 'Reusing verified %s %s (%s)\n' "$tool" "$version" "$(go env GOVERSION)" >&2
  printf '%s/%s\n' "$GOBIN" "$tool"
  exit 0
fi
# Install the versioned tool outside the library modules and workspace.
(cd "$GOBIN" && GOWORK=off GOTOOLCHAIN=local GOFLAGS= go install "$package@$version")
python3 "$repo_dir/scripts/check-ci-tool-cache.py" "$tool" "$GOBIN/$tool"
printf '%s/%s\n' "$GOBIN" "$tool"
