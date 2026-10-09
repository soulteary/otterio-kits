# CI migration and original check mapping

Executable workflows are retained only in the root `.github/workflows`. The eight removed module workflows remain readable at the original import commits recorded in `UPSTREAMS.json`; upstream history has not been rewritten or trimmed.

`python3 scripts/verify-ci-layout.py` checks all six imported directories and nested tool directories. It fails for `.github/workflows` or the misspelled `.github/workflow`, including empty directories. After a subtree update, review restored CI files, migrate useful checks to the root, then remove nested workflows.

## Migrated checks

The following work was implemented across five CI PRs. Commands run per module, and Go is read from `go.work` instead of retaining an obsolete Go version matrix.

- `highwayhash/go.yml`: three-platform tests, noasm, vet, and original golangci-lint rules moved to module test, quality, and lint workflows.
- `highwayhash/codeql.yml`: CodeQL and weekly scans moved to the root security workflow, using the same pinned version as CRC64.
- `sha256-simd/go.yml`: three-platform race tests, formatting, assembly-declaration vet, and `test-architectures.sh` moved to module tests, full vet, formatting, and extended-platform checks. Full vet includes asmdecl.
- `simdjson-go/go.yml`: three-platform tests, short race tests, formatting/vet, and Linux 386 checks were retained. Its noasm path only provides unsupported-platform stubs; skipped parser tests do not count as parser validation.
- `simdjson-go/vulncheck.yml`: govulncheck now uses a pinned tool version and scans the six runtime modules and two helper modules separately.
- `sio/go.yml`: three-platform race tests, vet/formatting, original lint rules, atomic coverage/Codecov, and Trivy SARIF moved to test, quality, lint, security, and coverage workflows.
- `crc64nvme/go.yml`: three-platform tests, noasm, `-cpu=1,4 -short -race`, formatting/vet, and Linux 386 moved to the corresponding module jobs.
- `crc64nvme/codeql-analysis.yml`: CodeQL and weekly scans moved to the unified security workflow.

MD5 had no upstream GitHub workflow. Root workflows add module tests, formatting, vet, lint, and security checks. Its generator runs as the separate `md5-simd/_gen` task. `simdjson-go/benchmarks` remains a separate module; benchmark smoke tests and longer performance comparisons run separately.

## Checks after an update

```sh
python3 scripts/verify-ci-layout.py
python3 scripts/verify-upstreams.py
bash scripts/check-modules.sh verify
```

For example, read an original workflow with `git show <highwayhash-import-commit>:highwayhash/.github/workflows/go.yml`. Obtain the actual import SHA from `UPSTREAMS.json`. Deleting a file in a later maintenance commit does not change the import commit's tree.
