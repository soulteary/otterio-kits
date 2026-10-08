# Independent module reports

Coverage, fuzzing, and performance have separate root workflows. A failing
module or fuzz target does not cancel the other matrix entries. Each entry
uploads its own logs, environment, and result files, including failed jobs.
The normal module test workflow remains the required correctness entry point.

## Coverage

`coverage.yml` runs the six runtime modules on Linux with `-race`, a fresh test
run, and `-covermode=atomic`. This preserves sio's original Linux coverage job.
Profiles and human-readable totals are uploaded under `coverage-MODULE` and a
module total is added to the run summary. Assembly instructions are not counted
by Go's source coverage; a percentage describes instrumented Go statements.

The original Codecov upload is retained with separate module flags. Set the
repository's `CODECOV_TOKEN` secret to enable it. Upload errors retain the
upstream nonblocking behavior. The profiles do not depend on Codecov being
configured and are always available from Actions artifacts. These profiles
belong to separate module paths and should not be concatenated into one total.

## Fuzzing

`fuzz.yml` runs nightly at 02:23 UTC, on manual dispatch, and on pull requests
affecting its configuration or the two fuzzable modules. Each of sio's five and
simdjson-go's three existing fuzz functions has a separate matrix entry. Every
entry validates that the exact target still exists, then fuzzes for one minute
with two workers. Go's eight-minute timeout and the 15-minute job timeout bound
initial corpus loading, execution, and minimization.

simdjson-go entries require native AVX2/CLMUL support before starting. Unsupported
hardware fails visibly instead of yielding a successful skipped parser run.
No new network fixtures are downloaded. Existing checked-in corpora are used.
New regressions in `testdata/fuzz/FuzzTARGET` and discovered inputs in Go's fuzz
cache are copied into the target's artifact, along with its log. Recover a
failing input, put it back under the corresponding module's
`testdata/fuzz/FuzzTARGET`, and replay the printed `go test -run` command locally.

Nightly fuzzing is recurring bounded exploration. Promote useful failures into
committed regression cases; artifacts expire after 14 days.

## Performance

`benchmarks.yml` runs manually, with a small pull-request smoke run when the
workflow or helper changes. Reports are separate for all six runtime modules.
The selectors use existing upstream benchmarks: highway hash 1 KiB / 1 MiB,
SHA-256 1 KiB / 1 MiB, small / medium JSON fixtures, sio 64 KiB / 1 MiB streams,
CRC64 1 KiB / 1 MiB, and MD5 32 KiB / 1 MiB. CPU-specific variants run when
available. simdjson-go requires a supported parser CPU; the MD5 comparison
requires AVX2 so a benchmark labelled AVX2 cannot report fallback performance.
No benchmark silently
succeeds with zero measurements.

Manual runs collect ten samples with 200 ms per benchmark, memory statistics,
and one Go CPU worker. Results include the exact revision, Go version, build
environment, selected workloads, and runner hardware. These defaults measure
bounded representative workloads instead of all upstream stress benchmarks.

The optional `baseline_ref` dispatch input defaults to `main`. Baseline and head
are measured consecutively on the same runner using the head's helper,
selectors, and Go compiler. Exact-version benchstat compares the raw result
files and writes the comparison to the run summary. An empty input disables
comparison. Ref inputs go through checkout's structured argument, not a shell
command. Pull-request smoke runs use one iteration and one sample; they do not
claim a performance comparison.

GitHub-hosted hardware and scheduling vary. Interpret within-run comparisons
with the reported uncertainty; cross-run results are not a regression threshold.
Stable performance gating should use a controlled runner and more samples.

## Local entries

From the repository root, with the matching Go toolchain installed:

```sh
bash scripts/check-reports.sh coverage sio /tmp/otterio-reports/sio
FUZZTIME=10s bash scripts/check-reports.sh fuzz sio FuzzDecryptMalformed /tmp/otterio-fuzz
BENCHTIME=1x BENCH_COUNT=1 bash scripts/check-reports.sh benchmark highwayhash /tmp/otterio-bench
```

`GOWORK=off`, the local Go toolchain, and readonly module metadata are enforced.
The SIMD parser reports require a supported amd64 host; cross-compilation does
not count as parser fuzz or performance validation.
