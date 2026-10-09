# Per-module releases

`otterio-kits` maintains six independent Go libraries. One Git commit may change multiple modules, but each module has its own version, tag, and release notes. Changing `simdjson-go` does not require releasing the CRC or encryption libraries. There is no root release `go.mod` or root Go module containing all six libraries.

This is a maintainer runbook. Mainline and module CI are available, but there is currently no automatic release workflow or CI trigger for formal release tags. Maintainers execute the release commands after completing checks. Candidate versions and commands below do not indicate published releases.

## Module identity and first-release candidates

Module paths have migrated to `github.com/soulteary/otterio-kits/<directory>`. Go subdirectory-module tags must include the directory prefix; consumer version numbers omit it. For example:

```text
module: github.com/soulteary/otterio-kits/crc64nvme
Git tag: crc64nvme/v1.1.2
go.mod: github.com/soulteary/otterio-kits/crc64nvme v1.1.2
```

These candidates continue the upstream version sequence with one patch increment to show the relationship between the import baseline and the OtterIO maintenance release. They are first-release candidates for six new module paths, not published versions or claims of identical content to similarly numbered MinIO releases:

- `highwayhash/v1.0.5`: based on upstream `v1.0.4`.
- `sha256-simd/v1.0.2`: based on upstream `v1.0.1`.
- `simdjson-go/v0.4.6`: based on upstream `v0.4.5`.
- `sio/v0.5.2`: based on upstream `v0.5.1`.
- `crc64nvme/v1.1.2`: based on upstream `v1.1.1`.
- `md5-simd/v1.1.3`: based on upstream `v1.1.2`.

Maintainers may choose independent version sequences, but should settle the convention before first release. Retain the `v0` maturity declaration for `simdjson-go` and `sio`; moving repositories and module paths does not justify an automatic `v1`. Release notes must describe actual repository changes rather than only saying “upstream patch version.” Thereafter each module follows semantic versioning independently: patch for fixes, minor for compatible new APIs, and a new major for incompatible public APIs or promised behavior in stable modules. For `v2` and later, migrate module/import paths to `/v2` or the corresponding suffix, for example `github.com/soulteary/otterio-kits/crc64nvme/v2` with tag `crc64nvme/v2.0.0`.

Original package names are retained; hyphens in paths are not Go identifiers. Example imports follow; actual programs should import only the packages they use:

```go
import (
    highwayhash "github.com/soulteary/otterio-kits/highwayhash"
    sha256 "github.com/soulteary/otterio-kits/sha256-simd"
    simdjson "github.com/soulteary/otterio-kits/simdjson-go"
    sio "github.com/soulteary/otterio-kits/sio"
    crc64nvme "github.com/soulteary/otterio-kits/crc64nvme"
    md5simd "github.com/soulteary/otterio-kits/md5-simd"
)
```

The six runtime libraries and two helper modules currently declare `go 1.27.2`. This is the minimum consumer Go requirement, not merely the CI compiler version. Older toolchains cannot use these releases with `GOTOOLCHAIN=local`. State the minimum in release notes and explain the impact of future changes separately.

`md5-simd/_gen` is an assembly generator and `simdjson-go/benchmarks` is a comparison tool. They are outside the runtime release list and receive no library release tags. The benchmarks' local `replace => ../` measures the current parent module; runtime libraries do not depend on it. Go module download archives exclude helper directories containing nested `go.mod` files.

## Preparing a candidate commit

This example prepares a `crc64nvme` release from a merged `main` commit. First merge code, dependencies, necessary generated files, and module release notes through a PR. Confirm that the full SHA is on `main`; a passing older commit does not justify tagging a newer `HEAD`.

From a clean checkout at the repository root, create a candidate branch to freeze the revision under validation:

```sh
git fetch origin main
test -z "$(git status --porcelain)"

release_module=crc64nvme
release_version=v1.1.2
release_tag="$release_module/$release_version"
release_commit=$(git rev-parse origin/main)
candidate_branch="release-candidate-$release_module-$release_version"

git switch --create "$candidate_branch" "$release_commit"
git show --no-patch --format=fuller "$release_commit"
```

Replace the branch/tag version with the selected release version. If the branch already exists, inspect its SHA rather than force-overwriting it. Record the full `release_commit`; local checks, remote CI, the tag, and release notes must all refer to that commit. If validation finds a problem, merge a fix PR into `main`, select a new candidate commit, create a new candidate branch, and repeat validation.

## Checking the independent module

Root `go.work` supports joint repository development; consumers cannot rely on it to fill missing dependencies. Checks must disable the workspace. Scripts already enforce `GOWORK=off` and readonly module metadata. For a single candidate, run:

```sh
python3 scripts/verify-upstreams.py
python3 scripts/verify-ci-layout.py
python3 scripts/check-quality.py format "$release_module"
python3 scripts/check-quality.py vet "$release_module"
python3 scripts/check-quality.py tidy "$release_module"
bash scripts/check-modules.sh verify "$release_module"
bash scripts/check-modules.sh test "$release_module"
bash scripts/check-modules.sh noasm "$release_module"
bash scripts/check-modules.sh cross "$release_module"
```

Use the toolchain declared in `go.work`. `tidy` only checks metadata differences; do not release while ignoring its failures. `cross` only compiles and does not prove runtime correctness on the target. `noasm` validates algorithms only where a usable portable implementation exists; simdjson's unsupported-platform stubs do not validate its parser. Native parser tests require AVX2/CLMUL on Linux amd64. Record the hardware capabilities actually exercised for specialized assembly paths.

For MD5 generator changes, also run `bash scripts/check-modules.sh tools md5-simd/_gen`; for JSON benchmark changes, run `bash scripts/check-modules.sh tools simdjson-go/benchmarks`. Review the selected module's complete CI results: quality, lint, govulncheck, CodeQL, and native Linux/macOS/Windows tests. Platform or assembly changes also require relevant extended-platform results. See [CI_TESTS.md](CI_TESTS.md) and [CI_SECURITY.md](CI_SECURITY.md).

The six runtime libraries currently have no `require` dependencies on one another. If such dependencies are introduced, release the dependency first, pin its public version in the dependent module's `go.mod`, and validate it. Do not publish relying on `go.work` or a local `replace`.

## Manually running CI at the same SHA

Current workflows have no formal-tag triggers. Run all checks manually before release; pushing a tag does not imply that tests ran. Push the candidate branch to its explicit remote branch and dispatch checks from it:

```sh
git push origin "refs/heads/$candidate_branch:refs/heads/$candidate_branch"
gh workflow run quality.yml --ref "$candidate_branch"
gh workflow run ci.yml --ref "$candidate_branch"
gh workflow run lint.yml --ref "$candidate_branch"
gh workflow run security.yml --ref "$candidate_branch"
```

These `workflow_dispatch` entry points check all modules. When platform, assembly, or generator changes need extended checks, also dispatch:

```sh
gh workflow run extended.yml --ref "$candidate_branch"
```

The `workflow_dispatch` `ref` is a branch or tag name. A candidate branch pins the same merged commit, avoiding a moving `main` during validation. Inspect runs with:

```sh
gh run list --branch "$candidate_branch" --event workflow_dispatch \
  --json databaseId,workflowName,headSha,status,conclusion,url
```

For every required workflow, confirm that `headSha` equals the full `release_commit` and wait for success. Passing checks at another SHA do not count, and success for selected modules must not be reported as complete validation. Record each run URL and actual platform. Create the formal tag only after the candidate's required checks finish. Select coverage, fuzzing, and performance reports based on changes, and distinguish smoke tests from performance comparisons.

## Creating and pushing one formal tag

Complete release notes and license/provenance follow-ups, confirm candidate checks pass, then check whether the version name is occupied:

```sh
git ls-remote origin "refs/tags/$release_tag" "refs/tags/$release_tag^{}"
git show --no-patch "$release_commit"
```

If the remote tag exists, inspect its release record and choose a new version; do not overwrite it. Create an annotated tag at the explicit verified SHA and push exactly that tag:

```sh
git tag -a "$release_tag" "$release_commit" \
  -m "$release_module $release_version"
git push origin "refs/tags/$release_tag:refs/tags/$release_tag"
git ls-remote origin "refs/tags/$release_tag" "refs/tags/$release_tag^{}"
```

The dereferenced `^{}` SHA in the second query must equal `release_commit`. Avoid `git push --tags`, which may publish other modules or mix in `upstream/*` provenance tags. Manage provenance tags separately; they are not Go module versions. One commit may have several module tags, but verify, push, and record each version independently.

## Verifying a consumer outside the repository

After the formal tag becomes public, create a temporary Go module outside the workspace and download that version through the public proxy. The following installs and compiles one CRC consumer; it does not run the dependency library's tests. Native library validation comes from the earlier exact-commit checks and CI.

```sh
consumer_dir=$(mktemp -d "${TMPDIR:-/tmp}/otterio-kits-consumer.XXXXXX")
(
  cd "$consumer_dir"
  export GOWORK=off GOTOOLCHAIN=local GOPROXY=https://proxy.golang.org
  go mod init example.com/otterio-kits-consumer
  go get github.com/soulteary/otterio-kits/crc64nvme@v1.1.2
  cat > main.go <<'EOF'
package main

import (
    "fmt"
    "github.com/soulteary/otterio-kits/crc64nvme"
)

func main() {
    fmt.Printf("%016x\n", crc64nvme.Checksum([]byte("otterIO")))
}
EOF
  go build ./...
  go list -m github.com/soulteary/otterio-kits/crc64nvme
  go mod download -json github.com/soulteary/otterio-kits/crc64nvme@v1.1.2
)
```

Use Go 1.27.2 or later. `GOTOOLCHAIN=local` exposes minimum-version problems directly. Check the path/version from `go list -m`, provenance in download output, and the module's `LICENSE*` and `NOTICE` inside `Dir`/`Zip`. Successful public-proxy resolution also puts the version in the module index. If synchronization is pending, verify the remote tag, path, and full SHA, then wait or retry without moving the tag.

The other modules can be installed at their corresponding candidate versions. These are separate commands; consumers need not depend on all six:

```sh
go get github.com/soulteary/otterio-kits/highwayhash@v1.0.5
go get github.com/soulteary/otterio-kits/sha256-simd@v1.0.2
go get github.com/soulteary/otterio-kits/simdjson-go@v0.4.6
go get github.com/soulteary/otterio-kits/sio@v0.5.2
go get github.com/soulteary/otterio-kits/md5-simd@v1.1.3
```

For each release, write an external consumer example using that module's package/API. The CRC example is not evidence that the other five libraries were verified. Successful JSON compilation does not establish that SIMD parsing ran on the current CPU.

An earlier release-path check was performed on 2026-10-08: outside the repository with the workspace disabled, all six modules at commit `0284a7beecea3819a4965c781ccffdf3d0bb0ba5` were downloaded through the public proxy as `v0.0.0-20261008011013-0284a7beecea`. A consumer with six blank imports compiled successfully. All six archives retained `go.mod`, `LICENSE`, `NOTICE`, and applicable BSD/MIT files; the two helper modules were excluded from runtime archives. This validates module resolution, consumer compilation, and license packaging at that commit. It did not run dependency tests or verify future formal tags; repeat these checks for every actual release.

## Release notes, provenance, and subsequent fixes

A Go version is determined by its module path, directory-prefixed tag, and tagged code. GitHub Releases describe that version. Verify the public tag before creating its Release; do not let a Release command implicitly create an unverified tag. GitHub's automatic source archives are full repository snapshots at the Git commit; Go download archives are scoped to individual module directories.

Each module's release notes should include its module path, version, and full SHA; upstream baseline and adapted patches; minimum Go version; actual successful CI and hardware/platform coverage; behavior, API, performance, and dependency changes; and applicable license materials. Refer to immutable initial provenance and subsequent maintenance records in [UPSTREAMS.json](../UPSTREAMS.json). Do not overwrite the upstream baseline with the new release version.

Save reviewed release notes in a separate file, substitute its actual path below, and create the corresponding Release:

```sh
release_notes_file=/absolute/path/to/crc64nvme-v1.1.2.md
gh release create "$release_tag" --verify-tag --latest=false \
  --title "$release_module $release_version" \
  --notes-file "$release_notes_file"
```

`--verify-tag` requires the tag to exist remotely. `--latest=false` prevents one component's version from appearing as a repository-wide Latest release; Go still selects versions by each module's tags. Create only the selected module's Release and do not use a repository-wide autogenerated changelog as its complete release notes.

Each module retains its LICENSE, applicable `LICENSE.Golang` / `LICENSE.Igneous`, NOTICE, and original source attribution. First-release preparation must address [outstanding provenance checks](LICENSES.md#outstanding-provenance-checks): the precise historical authorization chain for SHA's Intel AVX512 and jocover ARM64 implementations still needs verification. Handle this follow-up for the SHA module; decide other modules' readiness from their own materials and validation.

Never delete, force-move, or overwrite public tags. Publish a new patch version for corrections. If an older version should no longer be selected, explain it with `retract` in a new module version and publish that version. Retain old tags/source for reproducibility. `retract` neither deletes downloaded versions nor substitutes for a fixed release.

After recording CI links, the formal tag, and the Release, retain candidate branches or remove them when maintainers confirm they are no longer needed. Removing a candidate branch does not affect its published tag.

Finally, prepare separate dependency-migration PRs for otterIO / OC that explicitly change import paths and versions. Migrate SDK transitive dependencies in the independent `otterio-go` fork. Publishing kits tags does not automatically replace product `github.com/minio/*` dependencies. Run product regressions separately for disk checksums, existing ciphertext, and JSON data compatibility.

## Official rules

- [Go multi-module repositories](https://go.dev/doc/modules/managing-source): subdirectory modules, tag prefixes, and consumer versions.
- [Go version numbers](https://go.dev/doc/modules/version-numbers): stability declarations and semantic versions.
- [Publishing Go modules](https://go.dev/doc/modules/publishing): public tags, proxy indexing, and immutable versions.
- [Go workspaces](https://go.dev/ref/mod#workspaces): avoiding hidden independent-dependency problems.
- [Go minimum-version directives](https://go.dev/ref/mod#go-mod-file-go): minimum toolchain requirements.
- [Go module archives](https://go.dev/ref/mod#zip-files): subdirectory scope and nested-module exclusion.
- [Go retract directives](https://go.dev/ref/mod#go-mod-file-retract): withdrawing recommendations while retaining versions.
- [Manually running GitHub workflows](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow): `workflow_dispatch` and branch selection.
- [GitHub CLI release creation](https://cli.github.com/manual/gh_release_create): `--verify-tag`, release-note files, and Latest flags.
