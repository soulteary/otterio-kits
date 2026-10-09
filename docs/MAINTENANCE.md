# Maintenance, history checks, and releases

## Maintenance entry points

The root `UPSTREAMS.json` records provenance for all six runtime modules. When adding a component, update it together with `go.work`, the check script's explicit module list, and CI. Scripts inspect every `go.mod` to prevent silent omissions.

The six runtime modules are independently usable; there is no root release `go.mod`. The helper modules `md5-simd/_gen` and `simdjson-go/benchmarks` are outside the six-module workspace. Benchmarks retain `replace => ../` to measure the current parser; runtime modules use no local replaces.

Before changing an algorithm, run the original tests and save benchmarks. After product integration, run separate regressions against existing data. Record native execution and cross-compilation separately.

```sh
python3 scripts/verify-upstreams.py
bash scripts/check-modules.sh verify
bash scripts/check-modules.sh test
bash scripts/check-modules.sh tools
```

Scripts use ordinary Go caches by default. If these are not writable, specify writable locations:

```sh
GOMODCACHE=/tmp/otterio-kits-modcache GOCACHE=/tmp/otterio-kits-buildcache \
  bash scripts/check-modules.sh test
```

Use explicit module directories for joint workspace tests; root `go test ./...` alone does not cover this repository:

```sh
GOWORK="$PWD/go.work" go test ./highwayhash/... ./sha256-simd/... \
  ./simdjson-go/... ./sio/... ./crc64nvme/... ./md5-simd/...
```

## Inspecting original history

The pre-import repository commit is `0855462506b24f78b77837ca004ee5043696bfc3`. `UPSTREAMS.json` records each subtree import commit and provenance tag.

```sh
git log --first-parent --oneline main
git log upstream/highwayhash/v1.0.4
git show upstream/highwayhash/v1.0.4:highwayhash.go
python3 scripts/verify-upstreams.py
```

Original commits retain upstream root paths. The current `highwayhash/highwayhash.go` location comes from the import merge, so `git log -- highwayhash/` cannot replace inspection by original SHA. Authors, messages, parents, and SHAs are preserved; maintenance commits contain path migrations and license additions.

Subtree imports without `--squash` preserve all reachable ancestors of the fixed tag. Unmerged PRs, other remote branches, and post-tag changes are outside the initial import. A full clone obtains original commits reachable from main; fetch provenance tags separately if needed. The history script warns about missing tags and fails when a tag points at the wrong SHA.

History verification requires a full repository. Module builds may use shallow clones, but the separate history job should use `fetch-depth: 0`.

## Accepting a complete upstream update

For highwayhash, first verify the target version and SHA. Do not release directly from a moving branch.

```sh
git remote add upstream-highwayhash https://github.com/minio/highwayhash.git
# Skip the previous line if the remote already exists.
git fetch --no-tags upstream-highwayhash \
  refs/tags/v1.0.4:refs/tags/upstream/highwayhash/v1.0.4
```

This fetch reconstructs the original provenance reference. Recover other remote URLs from the manifest. For an update, replace both `v1.0.4` values with the verified upstream tag, fetch it into `upstream/<module>/<version>`, inspect the original commit and diff, then run:

```sh
git subtree merge --prefix=highwayhash <verified-upstream-commit-sha>
```

This preserves new upstream history. Resolve conflicts in module paths, README, NOTICE, and other maintenance changes, ensuring the module identity remains the otterio-kits path.

Existing `upstream` and `import` records are immutable initial provenance. Never replace them with later merge records. A later merged subtree includes local maintenance changes and need not equal the upstream tree; exact tree equality applies to initial imports. Append the new tag/SHA, original tree, history reference, merge SHA, and maintenance differences to the module's `updates`. Run module and relevant product checks. Verify that the new upstream SHA is an ancestor of the merge/HEAD and review differences from the new upstream tree.

## Selectively porting fixes

`cherry-pick` replays changes and normally produces a new SHA. It does not preserve an entire upstream history or automatically relocate root paths into a module directory.

For a fetched, ordinary non-merge fix, generate and apply a directory-prefixed patch:

```sh
git format-patch -1 --stdout <original-fix-sha> > /tmp/highwayhash-fix.patch
git am --directory=highwayhash -3 /tmp/highwayhash-fix.patch
```

Inspect patch scope first, especially root CI, module paths, generated code, and third-party materials. Review adaptations separately. Merge commits require selecting a mainline parent and inspecting the diff; the example does not apply directly. Maintenance commit messages should include the original SHA, upstream PR, and adaptations; update `upstream_patches` too. Check for duplicate patches during later full updates.

## Independent releases

Use directory-prefixed tags such as `highwayhash/v1.0.5`. This is a format example; choose versions according to the release plan. A root `v1.0.5` cannot represent all six modules.

Before release, check the module with `GOWORK=off`, retain its LICENSE/NOTICE materials, execute tests on applicable platforms, and document the upstream baseline and local changes. First versions under new module paths are chosen independently; original MinIO tags are not OtterIO releases. Major upgrades follow Go's `/v2` module-path rules.

The repository mainline and module CI have been pushed to GitHub; releases remain independent. Merge candidate changes through a PR and verify the exact SHA to be tagged. See [Releasing](RELEASING.md). Original commits reachable from main travel with it. Push provenance tags explicitly when needed:

```sh
git push origin refs/tags/upstream/highwayhash/v1.0.4
```

Repeat for the other five provenance tags. Create and push release tags separately; avoid mixing provenance and releases with `git push --tags`. There is currently no automatic tag test/release entry point. Complete exact-SHA checks before publishing a tag, then download that module by its public tag outside the repository and verify imports, Go requirements, and license packaging.

## References

- [Git subtree documentation](https://github.com/git/git/blob/master/contrib/subtree/git-subtree.adoc): imports without squash, merges, and history semantics.
- [Git cherry-pick documentation](https://git-scm.com/docs/git-cherry-pick): replaying commits and recording provenance.
- [Go multi-module repositories](https://go.dev/doc/modules/managing-source): subdirectory modules and prefixed tags.
