# Documentation

English is the primary language for repository documentation. Keep new and updated guides in English, preserve commands and identifiers exactly, and distinguish current requirements from historical validation results.

## Maintenance and releases

- [Maintenance](MAINTENANCE.md): daily checks, original history, upstream updates, and selective patches.
- [Releasing](RELEASING.md): independent module versions, candidate commits, CI, tags, and external consumer checks.
- [Licenses and provenance](LICENSES.md): retained license materials and outstanding source-history checks.

## Continuous integration

- [CI migration](CI_MIGRATION.md): mapping imported workflows to root checks.
- [Module selection](CI_SELECTION.md): change detection and module selection.
- [Quality checks](CI_QUALITY.md): formatting, vet, module metadata, and pinned tools.
- [Module tests](CI_TESTS.md): native tests, generators, and extended platforms.
- [Security and lint](CI_SECURITY.md): vulnerability scans, CodeQL, Trivy, and lint checks.
- [Reports](CI_REPORTS.md): coverage, fuzzing, and performance comparisons.

## Historical records

These records describe work performed on 2026-10-08. Their toolchain versions, CI configuration, and pending items reflect that stage of development. Use the root [README](../README.md), `go.work`, module metadata, and current workflows for today's requirements.

- [Implementation plan](IMPLEMENTATION_PLAN.md): initial import scope and acceptance criteria.
- [Initial validation](VALIDATION.md): evidence and limitations for maintenance commit `31f7ef5`.
- [Dependency upgrade](UPGRADE.md): subsequent Go/dependency changes and CI fixes.

The immutable initial provenance and subsequent maintenance records are in [UPSTREAMS.json](../UPSTREAMS.json).
