# Module security and lint checks

The root `Security` and `Lint` workflows replace the imported security/lint
entries without assuming a single root Go module. Every matrix entry identifies
one module in its check name, uses `GOWORK=off`, and reads Go from `go.work`.
Both workflows run on PRs, main pushes, and manual dispatch. Security also retains
a weekly schedule from the original CodeQL workflows.

## Tool versions

`.github/ci-tools.json` is the common version manifest. The installer reads fixed
Go tool versions from it; `scripts/ci-tool-version.py` supplies the Trivy CLI
version. Workflow validation enforces the same action reference everywhere.

Initial versions are govulncheck `v1.8.0`, golangci-lint `v2.14.0`, CodeQL Action
`v4.38.2`, Trivy CLI `v0.75.0`, and Trivy Action `v0.36.0` pinned to its full SHA.
CodeQL uses the action release's linked bundle so all module jobs use the same
extractor and query packs. When updating CodeQL, change all init/analyze/SARIF
references and the manifest together, and verify its Go version support.

Primary references:

- [govulncheck command and exit-code documentation](https://github.com/golang/vuln/blob/v1.8.0/cmd/govulncheck/doc.go)
- [golangci-lint v2.14.0 release](https://github.com/golangci/golangci-lint/releases/tag/v2.14.0)
- [CodeQL manual builds](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/manage-your-configuration/codeql-for-compiled-languages)
- [CodeQL init source-root input](https://github.com/github/codeql-action/blob/v4.38.2/init/action.yml)
- [Trivy Action v0.36.0](https://github.com/aquasecurity/trivy-action/tree/a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8)

## govulncheck

The eight Go modules, including `md5-simd/_gen` and `simdjson-go/benchmarks`, run
`govulncheck -test ./...` separately on Linux/amd64. This preserves the original
simdjson-go vulnerability scan and extends it to every module and test dependency.
Text output intentionally gates reachable vulnerabilities: govulncheck's JSON
and SARIF output modes return zero even when they contain findings. Module-only
findings that are unreachable remain visible in the console report.

The tool is pinned; the official vulnerability database updates continuously.
These scans cover the selected Linux/amd64 Go build. They do not establish the
absence of vulnerabilities in native assembly or inactive build-tag paths.

Local reproduction:

```sh
GOBIN=/tmp/otterio-ci-bin bash scripts/install-ci-tool.sh govulncheck
PATH=/tmp/otterio-ci-bin:$PATH bash scripts/check-security.sh sio
```

## CodeQL

The two imported CodeQL entries are consolidated into six runtime-module jobs.
`source-root` identifies the selected module, `build-mode: manual` avoids
standalone-repository autobuild assumptions, and `go build -a ./...` extracts the
selected module with its own dependency metadata. Code scanning categories include
both language and module, so one module's SARIF does not overwrite another's.

Only the CodeQL and SARIF upload jobs receive `security-events: write`; checkouts
do not persist credentials. The database build and upload need verification in
GitHub Actions because the action's extractor and GitHub code-scanning service
are not exercised by a local Go build.

## SIO Trivy compatibility

The original SIO filesystem vulnerability/secret scan and SARIF upload are retained.
The scan root is `sio`, rather than the monorepo root. The Trivy action and its CLI
both have fixed versions; the action's setup-trivy and cache dependencies are
also pinned to commit SHAs. Findings retain upstream's report-only policy;
scanner failures still fail the job. Reachable Go findings are gated by
`govulncheck` independently.

## Lint policy migration

All eight Go modules use one pinned golangci-lint v2 version:

- `highwayhash/.golangci.yml` retains misspell, govet, revive, ineffassign,
  unparam, and unused. The former gosimple checks map to staticcheck's `S*` rules;
  goimports moves to the v2 formatter and runs with `--diff`. Type checking is
  intrinsic to golangci-lint v2. Existing comment/error-string exceptions remain.
- `sio/.golangci.yml` retains its twelve enabled linters and exclusions.
  `gomodguard` migrates to its replacement `gomodguard_v2`.
- Modules without an imported lint configuration use the root vet baseline.
  Additional unused or style gates need their own module policy and cleanup,
  particularly for assembly references and retained upstream helpers.

The SIO package documentation is reattached to the package declaration: the
import-time modification notice had separated it with a blank line. This fixes
the staticcheck package-comment finding without suppressing the rule.

```sh
GOBIN=/tmp/otterio-ci-bin bash scripts/install-ci-tool.sh golangci-lint
PATH=/tmp/otterio-ci-bin:$PATH bash scripts/check-lint.sh highwayhash
```

## Initial local verification (2026-10-08)

- govulncheck `v1.8.0` scanned all eight modules with Linux/amd64 build settings,
  including tests: no reachable vulnerabilities.
- Trivy `v0.75.0` successfully scanned SIO and produced a valid SARIF report.
  It reported [GO-2026-5932](https://pkg.go.dev/vuln/GO-2026-5932) for
  `golang.org/x/crypto`: that advisory concerns the unmaintained OpenPGP packages.
  SIO does not import those packages; govulncheck also reports zero vulnerable
  imported packages. The module-level result is retained in SARIF rather than
  hidden by an ignore entry.
- The migrated Highwayhash/SIO lint policies pass on Linux/amd64 build settings,
  including Highwayhash's goimports formatter check. The common vet baseline
  uses the append/testinggoroutine fixes in the preceding quality PR and the
  three equivalent ioutil.ReadFile-to-os.ReadFile updates in this PR.
- actionlint and shell syntax checks pass for the new entries. SIO tests pass.
  The CodeQL extraction/upload still requires GitHub Actions validation.
