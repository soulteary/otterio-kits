#!/usr/bin/env bash
# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0
# Check each module without allowing go.work to supply missing dependencies.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/check-modules.sh [layout|verify|test|short|race|race-short|noasm|cross|tools|architectures] [module ...]

  layout  Check all go.mod directories, go.work membership and license files.
  verify  Check module paths, dependency graphs and cached sums (including tools).
  test    Run the original tests on the host platform (default).
  short   Run upstream short tests (including native Linux/386 checks).
  race    Run the original tests with the race detector on the host platform.
  race-short  Preserve upstream -cpu=1,4 -short race tests for simdjson/CRC.
  noasm   Test portable implementations where supplied by upstream.
  cross   Build packages and test binaries for linux/arm64; do not run them.
  tools   Generate/compile MD5 assembly and smoke-test benchmark execution.
  architectures  Run SHA256 upstream build checks for all Go targets/tags.

With no module arguments, test all six release modules. verify also checks both
auxiliary modules; tools selects only those auxiliary modules. Every mode checks
that the complete module inventory and six-module workspace match the lists in
this script. Module files are read-only;
Go may download dependencies and write its normal module/build caches.
All selected modules are checked, then a summary and combined exit status are
reported. One failure does not suppress checks of the remaining modules.
Set CROSS_GOOS and CROSS_GOARCH to override the cross-compilation target.
Set TEST_TIMEOUT to override the per-package test timeout (default: 10m).
Set REQUIRE_SIMDJSON_CPU=1 to require AVX2/CLMUL support for native parser tests.
USAGE
}

mode=${1:-test}
if [[ $# -gt 0 ]]; then
  shift
fi
case "$mode" in
  layout|verify|test|short|race|race-short|noasm|cross|tools|architectures) ;;
  -h|--help|help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
release_modules=(highwayhash sha256-simd simdjson-go sio crc64nvme md5-simd)
# Retain upstream tooling as nested modules, but do not publish it as libraries
# or include it in go.work. The benchmark module intentionally replaces its
# parent with ../ so it measures this checkout with GOWORK=off.
auxiliary_modules=(md5-simd/_gen simdjson-go/benchmarks)
modules=("${release_modules[@]}")
if [[ "$mode" == verify ]]; then
  modules+=("${auxiliary_modules[@]}")
elif [[ "$mode" == tools ]]; then
  modules=("${auxiliary_modules[@]}")
fi
if [[ $# -gt 0 ]]; then
  modules=("$@")
fi

export GOWORK=off
export GOTOOLCHAIN=local
export GOFLAGS="${GOFLAGS:-} -mod=readonly"
test_timeout=${TEST_TIMEOUT:-10m}
host_os=$(go env GOHOSTOS)
host_arch=$(go env GOHOSTARCH)

if [[ "$mode" == test || "$mode" == short || "$mode" == race || "$mode" == race-short || "$mode" == noasm || "$mode" == tools ]]; then
  if [[ $(go env GOOS) != "$host_os" || $(go env GOARCH) != "$host_arch" ]]; then
    echo "Native test modes require GOOS/GOARCH to match the host. Use cross for compilation." >&2
    exit 2
  fi
fi

scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/otterio-kits-check.XXXXXX")
trap 'rm -rf "$scratch_dir"' EXIT

require_file() {
  if [[ ! -s "$1" ]]; then
    echo "Required file is missing or empty: $1" >&2
    exit 1
  fi
}

check_layout() {
  local expected_modules actual_modules expected_workspace actual_workspace
  local module module_file module_dir workspace_path workspace_go module_go
  expected_modules=$(printf '%s\n' "${release_modules[@]}" "${auxiliary_modules[@]}" | LC_ALL=C sort)
  actual_modules=$(
    find "$repo_dir" -type d \( -name .git -o -name .agents -o -name .codex \) -prune -o -type f -name go.mod -print |
      while IFS= read -r module_file; do
        module_dir=${module_file%/go.mod}
        printf '%s\n' "${module_dir#"$repo_dir"/}"
      done | LC_ALL=C sort
  )
  if [[ "$actual_modules" != "$expected_modules" ]]; then
    echo "go.mod inventory differs from the explicit release + auxiliary module lists." >&2
    printf 'Expected:\n%s\nDiscovered:\n%s\n' "$expected_modules" "$actual_modules" >&2
    exit 1
  fi
  require_file "$repo_dir/go.work"
  workspace_go=$(go work edit -json "$repo_dir/go.work" | awk -F '"' '/"Go":/ {print $4}')
  for module in "${release_modules[@]}" "${auxiliary_modules[@]}"; do
    module_go=$(cd "$repo_dir/$module" && go mod edit -json | awk -F '"' '/"Go":/ {print $4}')
    if [[ "$module_go" != "$workspace_go" ]]; then
      echo "$module/go.mod uses Go $module_go; expected workspace version $workspace_go." >&2
      exit 1
    fi
  done
  expected_workspace=$(
    for module in "${release_modules[@]}"; do
      (cd "$repo_dir/$module" && pwd)
    done | LC_ALL=C sort
  )
  actual_workspace=$(
    # go work edit only parses the file: the compatibility job may use a Go
    # version older than go.work while independently testing each go.mod.
    go work edit -json "$repo_dir/go.work" |
      awk -F '"' '/"DiskPath":/ {print $4}' |
      while IFS= read -r workspace_path; do
        if [[ "$workspace_path" == /* ]]; then
          (cd "$workspace_path" && pwd)
        else
          (cd "$repo_dir/$workspace_path" && pwd)
        fi
      done | LC_ALL=C sort
  )
  if [[ "$actual_workspace" != "$expected_workspace" ]]; then
    echo "go.work must contain exactly the six release modules, without duplicates or auxiliary tools." >&2
    printf 'Expected:\n%s\nWorkspace:\n%s\n' "$expected_workspace" "$actual_workspace" >&2
    exit 1
  fi
  for module in "${release_modules[@]}"; do
    require_file "$repo_dir/$module/LICENSE"
    require_file "$repo_dir/$module/NOTICE"
    case "$module" in
      sha256-simd|simdjson-go|md5-simd)
        require_file "$repo_dir/$module/LICENSE.Golang"
        ;;
    esac
  done
  require_file "$repo_dir/md5-simd/LICENSE.Igneous"
  echo "Layout verified: six release modules, two auxiliary modules, Go $workspace_go and per-module license materials."
}

probe_simdjson_cpu() {
  # This probes platform support; the implementation's existing tests validate
  # parsing. It also prevents a green amd64 CI run in which parser tests skip.
  cat > "$scratch_dir/simdjson-cpu.go" <<'GO'
package main

import (
    "fmt"
    "os"
    simdjson "github.com/soulteary/otterio-kits/simdjson-go"
)

func main() {
    supported := simdjson.SupportedCPU()
    fmt.Printf("simdjson parser CPU support: %t\n", supported)
    if os.Getenv("REQUIRE_SIMDJSON_CPU") == "1" && !supported {
        fmt.Fprintln(os.Stderr, "AVX2/CLMUL support is required for this native parser test job")
        os.Exit(1)
    }
}
GO
  go run "$scratch_dir/simdjson-cpu.go"
}

validate_module() {
  local module=$1
  case "$module" in
    highwayhash|sha256-simd|simdjson-go|sio|crc64nvme|md5-simd) ;;
    md5-simd/_gen|simdjson-go/benchmarks)
      if [[ "$mode" != verify && "$mode" != tools ]]; then
        echo "Auxiliary module $module is available only in verify/tools modes." >&2
        exit 2
      fi
      ;;
    *) echo "Unknown module: $module" >&2; exit 2 ;;
  esac
}

run_module() {
    local module=$1
    cd "$repo_dir/$module"
    echo "[$mode] $module ($host_os/$host_arch, $(go env GOVERSION), GOWORK=off)"
    case "$mode" in
      verify)
        expected_path="github.com/soulteary/otterio-kits/$module"
        actual_path=$(go list -m -f '{{.Path}}')
        if [[ "$actual_path" != "$expected_path" ]]; then
          echo "Expected module $expected_path, found $actual_path" >&2
          exit 1
        fi
        go list -deps -test ./... > /dev/null
        go mod verify
        ;;
      tools)
        go test -count=1 -timeout="$test_timeout" ./...
        case "$module" in
          md5-simd/_gen)
            generated_dir="$scratch_dir/generated-md5"
            mkdir -p "$generated_dir"
            go run gen.go -out "$generated_dir/md5block_amd64.s" \
              -stubs "$generated_dir/md5block_amd64.go" -pkg md5simd
            # Compile the actual output in isolation: generating files alone
            # would not prove that Go accepts both stubs and assembly.
            printf 'module otterio-generated-md5\n\ngo %s\n' "$(go env GOVERSION | sed 's/^go//')" > "$generated_dir/go.mod"
            (cd "$generated_dir" && GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go test ./...)
            ;;
          simdjson-go/benchmarks)
            # Both upstream benchmarks use fixtures retained in this module.
            # One iteration checks the entry points; it is not a performance comparison.
            go test -run '^$' -bench '^(BenchmarkJsoniterApache_builds|BenchmarkBugerJsonParserLarge)$' \
              -benchtime=1x -count=1 -timeout="$test_timeout" ./...
            ;;
        esac
        ;;
      test)
        if [[ "$module" == simdjson-go ]]; then
          probe_simdjson_cpu
          if [[ "$host_arch" != amd64 ]]; then
            echo "simdjson-go has no parser fallback on this architecture; upstream parser tests skip."
          fi
        fi
        go test -count=1 -timeout="$test_timeout" ./...
        ;;
      short)
        if [[ "$module" == simdjson-go ]]; then
          probe_simdjson_cpu
        fi
        go test -short -count=1 -timeout="$test_timeout" ./...
        ;;
      race)
        if [[ "$module" == simdjson-go ]]; then
          probe_simdjson_cpu
        fi
        CGO_ENABLED=1 go test -race -count=1 -timeout="$test_timeout" ./...
        ;;
      race-short)
        case "$module" in
          simdjson-go|crc64nvme) ;;
          *) echo "race-short is reserved for upstream simdjson-go and crc64nvme checks." >&2; exit 2 ;;
        esac
        if [[ "$module" == simdjson-go ]]; then
          probe_simdjson_cpu
        fi
        CGO_ENABLED=1 go test -cpu=1,4 -short -race -count=1 -timeout="$test_timeout" ./...
        ;;
      noasm)
        case "$module" in
          highwayhash|sha256-simd|crc64nvme|md5-simd)
            go test -tags=noasm -count=1 -timeout="$test_timeout" ./...
            ;;
          simdjson-go)
            echo "Upstream noasm tests validate unsupported-platform stubs, not a parser fallback."
            go test -tags=noasm -count=1 -timeout="$test_timeout" ./...
            ;;
          sio)
            echo "Skipping noasm: upstream does not define this build tag; covered by native tests."
            ;;
        esac
        ;;
      architectures)
        if [[ "$module" != sha256-simd ]]; then
          echo "architectures uses sha256-simd's upstream platform/tag build script." >&2
          exit 2
        fi
        CGO_ENABLED=0 sh ./test-architectures.sh
        ;;
      cross)
        target_os=${CROSS_GOOS:-linux}
        target_arch=${CROSS_GOARCH:-arm64}
        echo "Compile only: $target_os/$target_arch. No target tests are executed."
        export GOOS="$target_os" GOARCH="$target_arch" CGO_ENABLED=0
        go build ./...
        packages=$(go list ./...)
        mkdir -p "$scratch_dir/$module"
        index=0
        for package in $packages; do
          index=$((index + 1))
          go test -c -o "$scratch_dir/$module/$index.test" "$package"
        done
        ;;
    esac
}

# A fresh Bash process keeps errexit active inside every module. Calling a
# function/subshell from an if/! condition would disable errexit in its body,
# potentially hiding failed commands followed by successful commands.
if [[ "${OTTERIO_CHECK_MODULE_CHILD:-0}" == 1 ]]; then
  if [[ "${#modules[@]}" != 1 ]]; then
    echo "Internal module runner requires exactly one module." >&2
    exit 2
  fi
  validate_module "${modules[0]}"
  run_module "${modules[0]}"
  exit 0
fi

check_layout
if [[ "$mode" == layout ]]; then
  exit 0
fi
for module in "${modules[@]}"; do
  validate_module "$module"
done

failed_modules=()
results=()
for module in "${modules[@]}"; do
  set +e
  OTTERIO_CHECK_MODULE_CHILD=1 bash "$repo_dir/scripts/check-modules.sh" "$mode" "$module"
  status=$?
  set -e
  if [[ "$status" == 0 ]]; then
    results+=("$module: PASS")
  else
    results+=("$module: FAIL (exit $status)")
    failed_modules+=("$module")
  fi
done
printf '\n[%s] module results:\n' "$mode"
printf '  %s\n' "${results[@]}"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  summary_path=$GITHUB_STEP_SUMMARY
  if command -v cygpath >/dev/null 2>&1; then
    summary_path=$(cygpath -u "$summary_path")
  fi
  {
    printf '### %s (%s/%s)\n\n' "$mode" "$host_os" "$host_arch"
    printf -- '- %s\n' "${results[@]}"
    printf '\n'
  } >> "$summary_path"
fi
if [[ "${#failed_modules[@]}" != 0 ]]; then
  printf 'Failed modules: %s\n' "${failed_modules[*]}" >&2
  exit 1
fi
