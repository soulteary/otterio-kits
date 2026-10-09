# otterio-kits multi-module implementation plan

Plan date: 2026-10-08 (Asia/Shanghai).

This document records the initial import plan. Current toolchain requirements and later dependency changes are in the root README and [UPGRADE.md](UPGRADE.md). Initial provenance and original-tree acceptance records remain preserved.

The initial scope was to establish one maintenance repository for six core libraries: preserve fixed upstream baselines and original history, migrate module paths, and define per-module validation, provenance, and independent releases. `minio-go/v7` remains a separate SDK project. otterIO / OC dependency migrations and unreleased upstream fixes are subsequent work.

This plan defines steps and acceptance criteria. Actual completion is established by provenance records, import commits, and validation results, not plan checkmarks alone.

## 1. Repository structure and module boundaries

Six components reside directly under the repository root, each retaining its own `go.mod`, `go.sum`, original source, tests, test data, and license materials:

```text
otterio-kits/
├── LICENSE
├── README.md
├── UPSTREAMS.json
├── docs/
├── go.work
├── scripts/
│   ├── check-modules.sh
│   └── verify-upstreams.py
├── .github/workflows/
├── highwayhash/
├── sha256-simd/
├── simdjson-go/
├── sio/
├── crc64nvme/
└── md5-simd/
```

Module paths:

- `github.com/soulteary/otterio-kits/highwayhash`
- `github.com/soulteary/otterio-kits/sha256-simd`
- `github.com/soulteary/otterio-kits/simdjson-go`
- `github.com/soulteary/otterio-kits/sio`
- `github.com/soulteary/otterio-kits/crc64nvme`
- `github.com/soulteary/otterio-kits/md5-simd`

Do not add a root release `go.mod` that binds all components to one version. `go.work` is for repository development and joint checks. Every module must build and test independently with `GOWORK=off` so it remains usable outside the workspace.

The initial migration retains package names, public APIs, algorithms, ciphertext formats, build tags, and the six runtime modules' dependency versions. Module-path changes are intentional; successful compilation does not establish comprehensive compatibility with existing data. Retain the two helper modules `md5-simd/_gen` and `simdjson-go/benchmarks`, check them separately, and do not release them as libraries. Benchmarks retain a local parent replace and align metadata with dependencies already selected by the parent.

## 2. Pinning six import baselines

Use the user's existing dependency versions as initial baselines. Before import, resolve each Git tag again and compare its commit with the full SHA below:

- **highwayhash**: upstream `https://github.com/minio/highwayhash.git`, tag `v1.0.4`, commit `070ab1a87a76ab3c81950392f2991dc0ba638585`.
- **sha256-simd**: upstream `https://github.com/minio/sha256-simd.git`, tag `v1.0.1`, commit `6096f891a77bfe490cbea7a424c821b5fdb92849`.
- **simdjson-go**: upstream `https://github.com/minio/simdjson-go.git`, tag `v0.4.5`, commit `d82c779820b28b701fc258ee32f5df4ffc368f2d`.
- **sio**: upstream `https://github.com/minio/sio.git`, tag `v0.5.1`, commit `e1fddaac73108d378e89df17f4c3e2b53e5122c8`.
- **crc64nvme**: upstream `https://github.com/minio/crc64nvme.git`, tag `v1.1.1`, commit `cc422c7b1355e33091486ab1e6d461aba6fcaf69`.
- **md5-simd**: upstream `https://github.com/minio/md5-simd.git`, tag `v1.1.2`, commit `776275e0c9a74ceebbd50fe5c1d61b0c80c608df`.

These baselines exclude unreleased post-tag changes. Record each upstream default branch separately in `UPSTREAMS.json` for future review; a moving branch cannot replace a fixed commit.

Acceptance: each tag, full SHA, and import directory has an unambiguous correspondence. If a tag target changes, stop that component's import and record the discrepancy; other verified components may proceed.

## 3. Preserving original history

Use **Git subtree imports without `--squash`**. Each component gets its own import merge, making the baseline an ancestor and placing files in the component directory. This retains original SHAs, authors, timestamps, messages, and merge relationships for the baseline and every reachable ancestor without rewriting upstream history.

Start with a clean working tree and verify the commit:

```sh
git remote add upstream-highwayhash https://github.com/minio/highwayhash.git
git fetch --no-tags upstream-highwayhash master
git fetch --no-tags upstream-highwayhash refs/tags/v1.0.4
git rev-parse FETCH_HEAD^{commit}
git subtree add --prefix=highwayhash 070ab1a87a76ab3c81950392f2991dc0ba638585
```

Do not fetch only shallow history. Complete baseline ancestry first; missing Git objects or incomplete history prevent a claim of full preservation.

`cherry-pick` is useful for later selected fixes but normally creates new SHAs. Retaining authors/messages does not preserve original commits and merge relationships as mainline ancestors. `cherry-pick -x` records provenance, but root paths still need adapting to the component directory.

Keep two kinds of commits distinct:

1. **Import commits**: component content exactly matches the upstream baseline tree.
2. **OtterIO maintenance commits**: module paths, internal imports, documentation, license additions, and repository policy changes, each comparable to the baseline.

Original commits retain upstream root paths. Inspect them with `git log <baseline-sha>` or `git show <original-sha>:<upstream-path>`; filtering by today's subdirectory may omit upstream history. Continue later subtree imports without squash and do not rebase shared import history.

Preservation covers the baseline and its reachable ancestors, not every remote branch, unmerged PR, or post-baseline commit. Fetch, review, and record additional objects separately when needed.

## 4. Execution stages and acceptance

### Stage A: preparation, inventory, and recoverability

1. Confirm the target repository, branch, remotes, working tree, and existing commits; retain the root LICENSE.
2. Read repository conventions and inventory six upstream tags, commits, licenses, build tags, dependencies, and fixtures.
3. Use separate remote names and avoid importing colliding upstream tags such as `v1.0.0` into the root release namespace.
4. Record the starting commit and create a recovery point if needed. Do not hard-reset or force-push away existing user content.

Acceptance: correct target, recoverable existing content, six verified SHAs, and provenance sufficient for another maintainer to reproduce imports.

### Stage B: import each library and verify original trees first

Import highwayhash, sha256-simd, simdjson-go, sio, crc64nvme, and md5-simd in order. Before renaming module paths, check each import:

- The original baseline SHA is an ancestor of the import commit.
- The imported subtree exactly matches the upstream tree, including LICENSE, fixtures, assembly, and dotfiles.
- Original authors, dates, messages, and parents remain inspectable.
- `UPSTREAMS.json` records import SHA, baseline SHA, directory, and ancestor count. Reachability and counts confirm that history was not squashed.

Acceptance: six distinct import commits, all baseline ancestors reachable, and no post-tag feature changes mixed in. Imported `.github` files retain provenance but do not automatically become root GitHub Actions workflows.

`python3 scripts/verify-upstreams.py` checks the manifest, baseline/import reachability, tree/subtree equality, six ancestor counts, and deduplicated total without writing. Full history is mandatory. Missing namespaced provenance tags only warn because ordinary consumers may not fetch all tags; baseline history must still be an ancestor of HEAD. Nested `go.mod` files in the two helper modules are retained upstream tool modules, not seventh/eighth runtime releases.

### Stage C: migrate module identity and complete provenance materials

1. Change each `go.mod` module declaration to its repository submodule path.
2. Migrate internal self-imports, examples, and installation instructions while retaining external dependency versions at this stage.
3. Retain original source headers and Git history; clearly record maintenance changes in modified files.
4. Maintain upstream URLs, baseline tag/SHA, import SHA, original license materials, path migration, and later patch provenance in `UPSTREAMS.json`.
5. Keep component README technical content. Root README states independent OtterIO maintenance, six upstream sources, and library purposes.
6. Preserve required third-party license text and NOTICE materials per independent module; a root summary cannot substitute for distribution materials.

Acceptance: no obsolete self-imports, independently resolvable dependencies, traceable provenance, and differences limited to declared migration/governance changes.

### Stage D: common maintenance entry points and per-module CI

1. List six modules in root `go.work` and choose a Go toolchain satisfying all module declarations.
2. Maintain an explicit script module inventory and compare it with actual `go.mod` files and `go.work`; new modules must not silently escape checks.
3. Test and statically check six modules separately in root CI. Root `go test ./...` alone does not cover the repository.
4. Validate workspace and independent `GOWORK=off` modes. CI must not depend on runtime-module local replaces or user-specific caches.
5. Run host tests, applicable race/noasm tests, and Linux amd64/arm64 cross-builds. Respect component platforms/build tags and mark unsupported paths as not applicable.
6. Place active workflows at root `.github/workflows`; historical nested workflows do not run current CI.

Acceptance: all six modules covered, independent checks pass, toolchain requirements explicit, and loop scripts propagate failures. Record compilation separately from real-hardware execution.

### Stage E: complete the initial local delivery

1. Save import history, provenance, plan, validation results, and known limits.
2. Review the diff for unintended algorithm, API, ciphertext-format, or dependency changes.
3. Create reviewable maintenance commits while retaining six import commits and original history.
4. Finish local organization and validation. Execute pushes, formal tags, and product dependency upgrades as explicit release steps; do not call draft versions published.

Acceptance: another maintainer can reproduce provenance and module checks and identify unexecuted compatibility checks.

## 5. License and provenance maintenance

All six upstream root LICENSE files are Apache-2.0. Preserve additional source copyright/license declarations; a root summary cannot replace them.

- **highwayhash, sio, crc64nvme**: retain original LICENSE files, source headers, and notices; inspect new materials with every patch.
- **sha256-simd**: retain Go Authors BSD terms in tests, Kristofer Peterson's Apache attribution, ARM64 source comments, and README attribution to Intel. Intel/jocover historical provenance still requires verification; do not claim a complete audit.
- **simdjson-go**: retain Go Authors headers in `appendfloat_f.go` and `ftoaryu.go`; add complete distributable Go BSD text and record its source.
- **md5-simd**: retain `LICENSE.Golang`, full Igneous Systems MIT text in assembly, and MinIO attribution; include them in distribution notices.

Distinguish preserved original text, license materials added for independent distribution, and unverified history. Check applicable notices for binaries, containers, and source archives. This inventory does not replace comprehensive review of dependencies, test assets, or brand names.

## 6. Existing-data compatibility validation

Initial import acceptance uses original tests, tree equality, and a minimal migration diff. Before later algorithm/parser/encryption changes, add product-specific regressions:

- **highwayhash**: fixed key/input vectors for 64/128/256-bit outputs, chunked writes, and CPU-implementation equality; representative existing otterIO disk-checksum vectors.
- **sha256-simd**: compare with `crypto/sha256` for empty input, block boundaries, large input, Reset, and chunked writes; restore old serialized states when relevant. Assess the AVX512 service path separately.
- **simdjson-go**: Unicode escapes, floating-point/integer boundaries, filtered traversal, deletion, and build paths. Reproduce upstream issue reports before deciding on patches.
- **sio**: publicly distributable fixed key/nonce/version/ciphertext fixtures; old-ciphertext decryption, truncation/tamper detection, chunking, and protocol-version compatibility. Specify compatibility boundaries for key-derivation changes.
- **crc64nvme**: fixed NVMe CRC vectors, alignment, chunked Update, portable/SIMD equality, and matching CPU environments for illegal-instruction reports.
- **md5-simd**: compare with `crypto/md5` for concurrent clients, chunking, Reset/Close, and reuse. Pooling and register-preservation fixes require concrete regressions.

Race checks and cross-compilation do not prove all SIMD hardware paths. Arrange actual Linux amd64/arm64 execution before first release. Report AVX2/AVX512 or other specialized paths as validated only after running on supporting hardware.

## 7. Subsequent upstream updates

Update one component at a time to a fixed commit:

1. Fetch upstream and compare the recorded baseline to the target SHA for code, dependencies, APIs, licenses, and build requirements.
2. Choose a full update or a selected fix. An open upstream issue is not automatically a current product defect.
3. Prefer subtree pull/merge without squash for full updates. Resolve module-path, maintenance-notice, and license conflicts while retaining repository identity.
4. For selected fixes, apply a provenance-recorded patch or cherry-pick adapted to the subdirectory. Record original SHA/PR, adaptation reasons, and new maintenance commit; check duplication during later full updates.
5. Append to `UPSTREAMS.json` `updates` and change records, then run independent module tests, relevant cross-module checks, and product regressions. Do not overwrite initial `upstream` / `import` records. Later merged trees include local changes: verify ancestry and maintenance differences rather than initial tree equality.
6. Record Go version, CPU, input size, and concurrency for benchmarks. A single performance measurement is insufficient justification for merging.

Retain recorded original Git objects and `refs/tags/upstream/<module>/<baseline-version>` references. Remote reconstruction must be possible from `UPSTREAMS.json`, since `.git/config` is not distributed by ordinary clones.

## 8. Independent versions and release rules

Go submodule tags use directory prefixes such as `highwayhash/v1.0.5` and `simdjson-go/v0.4.6`. These examples define format and do not create releases.

- Distinguish original upstream versions from published OtterIO versions in release notes.
- Preserve upstream tags under `upstream/<component>/<tag>` to avoid collisions; these are not Go module release tags.
- Release each module according to its own changes; a single-library fix does not require tagging all six.
- Do not casually withdraw or move public tags. Evaluate `/v2` paths under Go major-version rules for incompatible APIs.
- Before release, resolve each module in a temporary external consumer with `GOWORK=off`; verify tags, module paths, license materials, and public provenance.
- Record baseline, OtterIO patches, minimum Go version, validation hardware, and known limitations per release.

## 9. Subsequent scope and priorities

After the initial import:

1. Review merged but unreleased md5-simd/simdjson-go fixes and decide scope using reproductions.
2. Evaluate standard-library substitution for actual product SHA256 usage; preserving the library baseline does not promise continued use of every implementation.
3. Establish an independent `otterio-go` SDK fork, then coordinate otterIO / OC dependency paths and API types.
4. Run product regressions for HighwayHash disk checksums, SIO historical ciphertext, and SIMD hardware paths.
5. Select first independent releases, push remotely, verify module downloads, and publish formal versions.

Record completion only after actual acceptance evidence exists. Keep unexecuted product compatibility checks, hardware validation, and license-history verification on the maintenance list.
