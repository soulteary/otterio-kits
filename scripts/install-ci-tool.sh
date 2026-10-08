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
# Install the versioned tool outside the library modules and workspace.
(cd "$GOBIN" && GOWORK=off GOTOOLCHAIN=local GOFLAGS= go install "$package@$version")
printf '%s/%s\n' "$GOBIN" "$tool"
