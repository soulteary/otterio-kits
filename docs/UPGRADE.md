# Go and dependency upgrades and CI fixes

Record date: 2026-10-08. The initial upstream SHAs, original trees, 796 original commits, and `upstream` / `import` records in `UPSTREAMS.json` remain unchanged. These are independent maintenance changes after import.

This is a historical record. Current toolchain requirements are in the root README and `go.work`.

## Toolchain and dependencies

At this upgrade stage, the six runtime modules, two helper modules, and `go.work` all declared `go 1.27.1`, matching otterIO and OC. [Official Go download metadata](https://go.dev/dl/?mode=json) was checked at the time and identified it as the latest stable version. The old sio `toolchain go1.24.10` suggestion was removed.

Direct and explicitly declared indirect dependencies were upgraded to the latest versions available from the official Go module proxy at the time, then tidied per module. Main versions were:

- x/sys `v0.48.0`, x/crypto `v0.57.0`, x/term `v0.46.0`.
- cpuid/v2 `v2.4.0`, compress `v1.20.1`.
- Assembly generator: avo `v0.6.0`, x/mod `v0.41.0`, x/sync `v0.23.0`, x/tools `v0.51.0`.
- Benchmark tools: jsonparser `v1.6.1`, modern-go/concurrent `v0.0.0-20180306012644-bacd9c7ef1dd`.
- json-iterator/go `v1.1.12` and modern-go/reflect2 `v1.0.2` remained the latest stable versions at that check and were retained.

`go list -mod=readonly -m -u -json` was run against each module's `require` entries, including indirect dependencies, for all eight modules; none reported `Update`. The benchmark module's local replace to its parent was retained rather than treated as an external upgrade. Tidy manages unused entries in third-party graphs; no extra dependency was introduced solely to change an unused version.

The complete per-module version inventory is in `UPSTREAMS.json` under `maintenance_updates`. Original `local_changes` describe initial maintenance commit `31f7ef5`, not a claim that all dependencies still match upstream after this upgrade.

## CI failures and fixes

Both Linux amd64 jobs in the [original failing run](https://github.com/soulteary/otterio-kits/actions/runs/37703368849) failed in `TestNdjsonCountWhere2`. The test implicitly downloaded untracked `RC_2009-01.json.zst`; for a non-200 response, `err` was nil, and calling `err.Error()` panicked. Both jobs detected SIMDJSON CPU support, so the failure came from external corpus loading.

The fixed test uses 12 inline NDJSON rows, retains both `countWhere` and `FindElement` query paths, and covers seven conditions: ordinary matches, case sensitivity, empty strings, no match, another field, and missing-field cases. Samples include non-string and nested fields. Leading/trailing blank lines are passed to the parser. The test needs no network and is not skipped under `-short`.

The shared fixture helper now reads local files only, reports paths in errors, and supports `errors.Is`. Callers fail explicitly through `testing.TB`. Implicit HTTP downloads and retry loops were removed. Checked-in large-corpus tests remain; benchmarks needing additional large data require local fixtures prepared at the expected paths. Regression checks for missing ordinary and zstd files passed.

At this stage, root CI retained only Go 1.27.1 Linux amd64 and macOS ARM64 jobs. setup-go read from `go.work`; old Go 1.24 compatibility jobs were removed. Recursive cache globs covered both helper modules. Layout checks enforced matching Go directives across all eight modules and the workspace.

ARM64 `noasm` validation after the cpuid/v2 upgrade found a dispatch bug: SHA2 detection selected an assembly backend that was not compiled, causing `TestGolden` to panic. Dispatch now requires both a CPU feature and build-time backend availability. Without assembly backends, Intel SHA, AVX512, and ARM SHA2 are all disabled. Hash algorithms and assembly bodies were unchanged. Both CI platforms at that stage ran `noasm` checks.

A portable-build regression temporarily enables all relevant CPU features, confirms dispatch remains disabled and `New` uses the standard library, then restores CPU information. After the SHA256 fix, ARM64 native, noasm, race, noasm + race, and appengine checks passed. amd64 native/noasm checks passed again, and both Linux architectures cross-compiled.

## Validation scope

Completed at this stage: dependency verification for eight modules; original host ARM64 tests, race, and applicable noasm checks; Linux amd64/ARM64 package and test-binary cross-compilation; joint six-module workspace tests; Bash/YAML checks; and original-history verification.

The official Go 1.27.1 darwin-amd64 toolchain was also used through Rosetta for six-module tests and four-module noasm checks; all passed. That environment lacked AVX2, so SIMDJSON parser tests still skipped and did not count as AVX2 parser execution.

Go 1.27.1 with avo 0.6.0 generated assembly and stubs in a temporary directory without overwriting repository assembly. JsoniterApache_builds and BugerJsonParserLarge each ran one benchmark iteration, exercising upgraded parser dependencies and zstd decompression. These smoke tests support no performance conclusion.

Remote Linux amd64 CI still needed to run after pushing this update to validate the actual AVX2 parser and new NDJSON cases. This stage changed SHA256 backend-selection conditions while retaining algorithms and assembly bodies. Product compatibility regressions for otterIO / OC remained scheduled according to the maintenance plan.
