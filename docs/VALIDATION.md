# Initial import and validation record

Date: 2026-10-08 (Asia/Shanghai). Local toolchain: `go1.27.1 darwin/arm64`.

This historical record preserves acceptance results for initial maintenance commit `31f7ef5`. See [UPGRADE.md](UPGRADE.md) for later toolchain/dependency upgrades and CI fixes. Current requirements come from the root README, `go.work`, and CI.

## Completed maintenance baseline

The six libraries were imported with `git subtree add` without `--squash`. Each import merge's second parent is the upstream version SHA, and its component subtree exactly matches the original upstream tree.

- highwayhash `v1.0.4`: 74 original commits; import `64a6c5bc32d33e94c9e80ef5a2d52de013db292c`.
- sha256-simd `v1.0.1`: 92 original commits; import `62753cf46186b1345981718538304fe061cfe03d`.
- simdjson-go `v0.4.5`: 451 original commits; import `c55169ea6c677816e320faeaa435c6a9b795eeef`.
- sio `v0.5.1`: 44 original commits; import `f59beba80d0adab7f6e83074c4e107e8aa328355`.
- crc64nvme `v1.1.1`: 20 original commits; import `e6616cbb3a6c4cbc20709fcb38c598e943888d6a`.
- md5-simd `v1.1.2`: 115 original commits; import `0d5cd410f1c037d85999fa73aae99cb2f3e15f7e`.

Both the summed and deduplicated total are **796 original commits**. Full upstream SHAs, original trees, provenance references, and later maintenance records are in `UPSTREAMS.json`. Initial provenance fields remain immutable; future upstream updates are appended to `updates`.

Module paths, examples, self-imports, and maintenance configuration were committed separately after the six imports. The six runtime modules initially retained baseline dependencies, original `go.sum`, public APIs, algorithms, and Apache LICENSE files. Reverse comparison of 100 upstream Go/assembly files found byte-for-byte equality after removing added modification notices and restoring declared self-import paths.

The helper paths `md5-simd/_gen` and `simdjson-go/benchmarks` also migrated. Benchmarks retained their local parent replace. `go mod tidy -go=1.17` aligned the benchmark module with the parent's already-selected compress `v1.15.15`, cpuid/v2 `v2.2.3`, and x/sys dependency and updated its own `go.sum`. This did not change dependencies of the six runtime libraries.

Six module NOTICE files, two full Go BSD texts, and MD5's full Igneous MIT text were added. Original source attribution and existing licenses were retained.

## Checks actually performed

The following checks passed at this stage. Go caches were `/private/tmp/otterio-compat-modcache` and `/private/tmp/otterio-kits-gocache`; existing module declarations constrained downloads, and checks used readonly metadata.

- `python3 scripts/verify-upstreams.py`: full history, ancestry, six original trees, imported subtrees, original commit counts, and provenance tags.
- `bash scripts/check-modules.sh layout`: all eight go.mod files discovered; the workspace contained exactly six runtime modules; per-module license materials complete. Temporary copies confirmed failure for an unregistered new module and an omitted workspace module.
- `bash scripts/check-modules.sh verify`: independent `GOWORK=off` dependency graphs, test dependencies, and cache verification for eight modules.
- `bash scripts/check-modules.sh test`: original host tests for six libraries; included commands and examples compiled.
- `bash scripts/check-modules.sh noasm`: highwayhash, sha256-simd, crc64nvme, and md5-simd passed. sio has no such tag; simdjson has no usable noasm parser and was skipped as documented by the script.
- `bash scripts/check-modules.sh race`: host race checks for six libraries, with the SIMDJSON platform limitation below.
- `bash scripts/check-modules.sh tools`: assembly generator and benchmark tools compiled. The generator and performance benchmarks were not executed at this stage.
- `bash scripts/check-modules.sh cross`: six libraries' Linux ARM64 packages and test binaries compiled.
- `CROSS_GOARCH=amd64 bash scripts/check-modules.sh cross`: six libraries' Linux amd64 packages and test binaries compiled. The final module passed a separate rerun after its pinned dependencies were available.
- `GOWORK="$PWD/go.work" go test ./highwayhash/... ./sha256-simd/... ./simdjson-go/... ./sio/... ./crc64nvme/... ./md5-simd/...`: joint workspace tests.
- Bash syntax, CI YAML parsing, and `git diff --check`.

Cross-compilation only generated target-platform programs; it did not run Linux tests.

## Scope not executed at this stage

Local `simdjson.SupportedCPU()` returned false. ARM64 has no SIMDJSON parser implementation, so actual parsing tests skipped. A passing command established only the current compilable path, not amd64 parser or SIMD assembly correctness.

At initial acceptance, root CI was configured for full-history verification, Go 1.27.1 Linux amd64/macOS ARM64, and Go 1.24 compatibility checks. Linux amd64 required AVX2/CLMUL to avoid all parser tests skipping. Remote CI, CPUs beyond the local host, and Go 1.24 checks had not run and could not be reported as passed. This describes the initial configuration, not the current workflows.

No otterIO / OC dependency switch, existing-disk checksum regression, historical-ciphertext product regression, or post-tag unreleased patches were included. Remaining license-history checks are documented in [LICENSES.md](LICENSES.md).

This initial stage did not push remotely or create formal releases. The next stage was to review unreleased fixes and data compatibility, then arrange independent releases and product migrations.
