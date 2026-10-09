# Formatting, static checks, and CI versions

The root `quality.yml` contains repository policy checks and independent quality jobs for all eight Go modules. Each module checks formatting of all Go files, full `go vet ./...`, module paths/dependencies, and `go mod tidy -diff`. The tidy check does not rewrite committed go.mod/go.sum files. Steps use `always()` to collect subsequent results within a module so multiple issues can be fixed together.

Formatting includes generated Go files and files under different build tags. Nested go.mod files are checked by their corresponding helper-module jobs. Nine existing MD5 formatting issues were corrected with gofmt, including generated `md5block_amd64.go`.

Full vet on Linux AMD64 then found that old generated assembly wrote to BP as a general-purpose register. Regenerating `.s` and `.go` files with pinned Avo v0.6.0 avoids the frame pointer. Instructions and labels match the old output after fixed register renaming; the algorithm and stack-frame size are unchanged. Tests directly call scalar assembly across padding boundaries and multi-block inputs and compare against standard-library MD5. Generation commands now include gofmt.

Full vet also found two existing issues. simdjson's `AsInteger` used an argument-free append when converting a uint to int64, omitting the return value. A regression test requiring no SIMD covers 0, 42, maximum int64, and overflow rejection. SHA AVX512 test workers now use `Errorf` and defer `wg.Done`, avoiding `Fatalf` from a child goroutine.

On 2026-10-09, simdjson received two targeted upstream backports beyond its v0.4.5 import baseline: `cac9cd14dd098e3abde93f5056dab89c8690c932` (#92), which continues filtered `Object.ForEach` traversal after skipping an unselected value, and `1a32809` (#89), which corrects the expected-type error from `Iter.Array`. The upstream filtering regression tests were retained. Additional direct-tape tests verify skipped fields, missing keys, and the array error without requiring SIMD. These backports do not constitute a full master-branch update; the initial provenance in `UPSTREAMS.json` remains unchanged.

```sh
python3 scripts/check-quality.py format md5-simd
python3 scripts/check-quality.py vet sha256-simd
python3 scripts/check-quality.py tidy simdjson-go/benchmarks
python3 -m venv /tmp/otterio-ci-python
/tmp/otterio-ci-python/bin/python -m pip install "PyYAML==$(python3 scripts/ci-tool-version.py PyYAML)"
/tmp/otterio-ci-python/bin/python scripts/verify-ci-config.py
/tmp/otterio-ci-python/bin/python -m unittest discover -s scripts/tests -p 'test_*.py'
GOBIN=/tmp/otterio-ci-bin bash scripts/install-ci-tool.sh actionlint
/tmp/otterio-ci-bin/actionlint
```

`.github/ci-tools.json` pins Actions, govulncheck, golangci-lint, actionlint, benchstat, and Trivy. The product Go version comes from `go.work`. Action `uses` references require literal versions; `verify-ci-config.py` checks consistency with the manifest and requires one CodeQL version throughout. The installer installs pinned Go tools outside modules without adding CI dependencies to runtime modules.

`.github/actions/setup-ci-tool` caches executables separately per tool. Cache keys include the pinned tool version, Go version, runner platform/architecture, cgo and instruction-set settings, and manifest/installer contents, without fallback across versions. Before reuse, the installer reads Go build metadata and checks package path, version, compiler, and target settings. A mismatch causes reinstallation and another check. Cache misses install the pinned version; caching does not change module selection, check scope, or required gates.

When upgrading tools, update the manifest and literal workflow references together, then run actionlint and version validation. actionlint is pinned and uses its built-in shellcheck integration on Linux runners to check expressions, dependencies, matrices, action inputs, and shell commands.

Version validation uses pinned PyYAML's SafeLoader to inspect actual workflow job/step `uses` nodes and composite-action steps. It supports `uses :`, quoted keys, flow mappings, folded scalars, and anchors/aliases. It does not depend on line formatting or treat strings in `run` or environment variables as actions. Go/CLI tool queries must specify full versions; floating queries such as `v1` or `v1.2` are rejected. The Python parser version is also included in the shared manifest and checks.
