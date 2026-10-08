#!/usr/bin/env bash
# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0
# Independent per-module reports. The normal module gate remains check-modules.sh.
set -euo pipefail

usage() {
  echo "Usage: $0 coverage|benchmark MODULE OUTPUT_DIR [REPO_DIR]" >&2
  echo "       $0 fuzz MODULE FUZZ_TARGET OUTPUT_DIR [REPO_DIR]" >&2
  exit 2
}

[[ $# -ge 3 ]] || usage
mode=$1
module=$2
shift 2
target=
if [[ "$mode" == fuzz ]]; then
  [[ $# -ge 2 ]] || usage
  target=$1
  shift
fi
output_dir=$1
shift
repo_dir=${1:-$(cd "$(dirname "$0")/.." && pwd)}
[[ $# -le 1 ]] || usage
case "$mode" in coverage|fuzz|benchmark) ;; *) usage ;; esac
case "$module" in
  highwayhash|sha256-simd|simdjson-go|sio|crc64nvme|md5-simd) ;;
  *) echo "Unknown report module: $module" >&2; exit 2 ;;
esac
mkdir -p "$output_dir"
output_dir=$(cd "$output_dir" && pwd)
repo_dir=$(cd "$repo_dir" && pwd)
cd "$repo_dir/$module"

export GOWORK=off GOTOOLCHAIN=local
export GOFLAGS="${GOFLAGS:-} -mod=readonly"
export CGO_ENABLED=1

{
  printf 'module: %s\nmode: %s\nrevision: %s\n' "$module" "$mode" "$(git -C "$repo_dir" rev-parse HEAD)"
  go version
  go env -json GOOS GOARCH GOHOSTOS GOHOSTARCH GOAMD64 CGO_ENABLED GOWORK
  printf 'gomaxprocs: %s\n' "${GOMAXPROCS:-default}"
  uname -a
  if command -v lscpu >/dev/null 2>&1; then lscpu; fi
} > "$output_dir/environment.txt"

# Parser fuzzing and benchmarks otherwise skip successfully on unsupported CPUs.
# Require a real parser before reporting coverage, fuzzing, or parser performance.
if [[ "$module" == simdjson-go ]]; then
  cat > "$output_dir/cpu-probe.go" <<'GO'
package main

import (
    "fmt"
    "os"
    simdjson "github.com/soulteary/otterio-kits/simdjson-go"
)

func main() {
    supported := simdjson.SupportedCPU()
    fmt.Printf("simdjson AVX2/CLMUL parser support: %t\n", supported)
    if !supported {
        fmt.Fprintln(os.Stderr, "this report requires a supported native parser CPU")
        os.Exit(1)
    }
}
GO
  go run "$output_dir/cpu-probe.go" 2>&1 | tee -a "$output_dir/environment.txt"
fi

if [[ "$module" == md5-simd && "$mode" == benchmark ]]; then
  cat > "$output_dir/cpu-probe.go" <<'GO'
package main

import (
    "fmt"
    "os"
    "runtime"
    "github.com/klauspost/cpuid/v2"
)

func main() {
    supported := runtime.GOARCH == "amd64" && cpuid.CPU.Supports(cpuid.AVX2)
    fmt.Printf("MD5 AVX2 benchmark support: %t\n", supported)
    if !supported {
        fmt.Fprintln(os.Stderr, "this benchmark requires AVX2 to measure the labelled SIMD implementation")
        os.Exit(1)
    }
}
GO
  go run "$output_dir/cpu-probe.go" 2>&1 | tee -a "$output_dir/environment.txt"
fi

case "$mode" in
  coverage)
    # Preserve sio's upstream Linux race + atomic coverage job and give every
    # runtime module a separate profile. Do not merge incompatible module paths.
    go test -race -count=1 -timeout=10m -covermode=atomic \
      -coverprofile="$output_dir/coverage.out" ./... 2>&1 | tee "$output_dir/tests.txt"
    go tool cover -func="$output_dir/coverage.out" | tee "$output_dir/coverage.txt"
    if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
      {
        printf '### %s coverage\n\n```text\n' "$module"
        tail -n 1 "$output_dir/coverage.txt"
        printf '```\n'
      } >> "$GITHUB_STEP_SUMMARY"
    fi
    ;;
  fuzz)
    case "$module/$target" in
      sio/FuzzEncryptDecrypt|sio/FuzzDecryptMalformed|sio/FuzzDecryptBuffer|sio/FuzzReaderWriter|sio/FuzzPackageBoundaries|simdjson-go/FuzzParse|simdjson-go/FuzzCorrect|simdjson-go/FuzzSerialize) ;;
      *) echo "Unknown fuzz target: $module/$target" >&2; exit 2 ;;
    esac
    # An obsolete selector must fail instead of yielding a successful empty run.
    go test -list "^${target}$" . > "$output_dir/targets.txt"
    if ! grep -Fx "$target" "$output_dir/targets.txt" >/dev/null; then
      echo "Fuzz target is missing on this platform: $module/$target" >&2
      exit 1
    fi
    printf 'target: %s\nfuzztime: %s\nparallel: %s\n' "$target" "${FUZZTIME:-1m}" "${FUZZ_PARALLEL:-2}" >> "$output_dir/environment.txt"
    # Each job has one target and a bounded run. Keep the exit status while
    # collecting newly discovered inputs even after a failing fuzz invocation.
    set +e
    go test -run '^$' -fuzz "^${target}$" -fuzztime="${FUZZTIME:-1m}" \
      -parallel="${FUZZ_PARALLEL:-2}" -timeout=8m . 2>&1 | tee "$output_dir/fuzz.txt"
    result=${PIPESTATUS[0]}
    set -e
    mkdir -p "$output_dir/corpus"
    if [[ -d "testdata/fuzz/$target" ]]; then
      cp -R "testdata/fuzz/$target" "$output_dir/corpus/regressions"
    fi
    module_path=$(go list -m -f '{{.Path}}')
    fuzz_cache="$(go env GOCACHE)/fuzz/$module_path/$target"
    if [[ -d "$fuzz_cache" ]]; then
      cp -R "$fuzz_cache" "$output_dir/corpus/discovered"
    fi
    exit "$result"
    ;;
  benchmark)
    # Fixed, checked-in workloads, avoiding network fixtures and very large
    # upstream stress benchmarks. Both revisions use this same selector.
    case "$module" in
      highwayhash) selector='^Benchmark(Sum64_1K|Sum256_1K|Sum256_1M)$' ;;
      sha256-simd) selector='^BenchmarkHash$/.*/^(1K|1M)$' ;;
      simdjson-go) selector='^BenchmarkParse(Small|Medium)$' ;;
      sio) selector='^Benchmark(EncryptReader|DecryptReader|EncryptWriter|DecryptWriter)_(64KB|1MB)$' ;;
      crc64nvme) selector='^BenchmarkCrc64$/^(1024|1048576)-(asm512|asm|go|stdlib)$' ;;
      md5-simd) selector='^Benchmark(Avx2|CryptoMd5)$/^(32KB|1MB)$' ;;
    esac
    printf 'selector: %s\nbenchtime: %s\ncount: %s\ncpu: 1\n' "$selector" "${BENCHTIME:-200ms}" "${BENCH_COUNT:-10}" >> "$output_dir/environment.txt"
    go test -run '^$' -bench "$selector" -benchmem -benchtime="${BENCHTIME:-200ms}" \
      -count="${BENCH_COUNT:-10}" -cpu=1 -timeout=10m . 2>&1 | tee "$output_dir/benchmarks.txt"
    if ! grep -E '^Benchmark[^[:space:]]+[[:space:]]+[0-9]+[[:space:]]' "$output_dir/benchmarks.txt" >/dev/null; then
      echo "No benchmark measurements were produced for $module; selector or CPU support changed." >&2
      exit 1
    fi
    ;;
esac
