# Module test entry points

`.github/workflows/ci.yml` is the normal test entry point. Every published module
has its own Linux amd64, macOS arm64 and Windows amd64 job. This keeps the original
repositories' Windows and macOS checks, uses the repository's single Go version,
and names failures with both the module and platform. The matrix does not cancel
other modules when one job fails.

Each job verifies its module metadata, executes native upstream tests, checks the
portable implementation where one exists, and runs race detection. Native Linux
requires AVX2/CLMUL for simdjson-go, so a successful parser job cannot consist only
of skipped parser tests. On unsupported architectures simdjson-go's upstream
unsupported-platform stubs are checked; there is no portable JSON parser fallback.
The simdjson-go and crc64nvme race jobs use upstream short suites, retaining
crc64nvme's `-cpu=1,4` concurrency checks for both modules.
The simdjson-go `noasm` job retains its upstream tests for unsupported-platform
stubs and does not claim parser fallback coverage. The other modules run their
full race suites. Linux also compiles packages and test binaries for Linux arm64; this is compilation coverage, not target execution.

Native tests, portable tests and race checks continue after an earlier check fails,
provided setup succeeded and the workflow was not cancelled. The earlier failure
still fails the job. Local serial invocations also continue through all selected
modules, print a per-module result summary, and fail if any module failed. Each
module runs in a fresh Bash process so a successful final command cannot mask an
earlier failure.

```sh
bash scripts/check-modules.sh test
bash scripts/check-modules.sh race-short simdjson-go crc64nvme
bash scripts/check-modules.sh noasm highwayhash sha256-simd simdjson-go crc64nvme md5-simd
bash scripts/check-modules.sh cross sio md5-simd
```

The two auxiliary modules have separate named CI jobs:

- `md5-simd/_gen`: compile its Go source, run the assembly generator into a temporary
  directory, then compile both generated assembly and Go declarations for amd64.
  Retained generated source is never overwritten by this check.
- `simdjson-go/benchmarks`: compile its tests and run the retained
  `BenchmarkJsoniterApache_builds` and `BenchmarkBugerJsonParserLarge` entry points
  with `-benchtime=1x`. This checks that benchmark fixtures and entry points work;
  it does not measure performance regressions.

```sh
bash scripts/check-modules.sh tools md5-simd/_gen
bash scripts/check-modules.sh tools simdjson-go/benchmarks
```

`.github/workflows/extended.yml` runs weekly, can be started manually, and runs
on pull requests that change its workflow, shared test runner, Go toolchain or
this entry-point documentation. It keeps
SHA256's upstream `test-architectures.sh`: every target reported by the current
`go tool dist list`, built with the original normal, `noasm`, `appengine`, and
combined tag modes. It also retains native Linux 386 short tests for simdjson-go
and crc64nvme by installing and running the 386 Go toolchain with `CGO_ENABLED=0`,
matching the original pure Go/assembly checks without requiring 32-bit C headers. The 386 simdjson-go
job exercises unsupported-platform behavior, not an AVX2 parser. These longer or
less common checks have explicit per-module job names and do not multiply every
normal pull request's platform matrix.

```sh
bash scripts/check-modules.sh architectures sha256-simd
# On a Linux host running a native 386 Go toolchain:
bash scripts/check-modules.sh short simdjson-go crc64nvme
```

All workflows use the same checkout and setup-go releases, `go.work` supplies the
Go version, and `GOTOOLCHAIN=local` / `GOWORK=off` keep module checks independent.
Module files are read-only during checks. Coverage, scheduled fuzzing and measured
performance comparison are maintained in a separate change with independent
workflow entry points and per-module results.
