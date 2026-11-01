# November 2026 module maintenance

This maintenance change keeps Go 1.27.3, public APIs, algorithms, serialized JSON,
and DARE ciphertext formats unchanged.

## Dependency audit

All six runtime modules and both helper modules were checked independently with
`GOWORK=off`, `go get -u -t ./...`, and `go mod tidy`. Runtime requirements were
already current at the time of the audit. The JSON comparison helper now declares
`simdjson-go v0.4.8`, replacing its stale `v0.4.7` floor. Its intentional local
`replace => ../` remains for benchmarking the checked-out parser. It must also be
checked outside the workspace against the public module without that replacement.

CI pins are refreshed together with their manifest: Go Test Report v1.1.3,
Go Report Card v1.1.4, CodeQL Action v4.39.1, govulncheck v1.9.0,
golangci-lint v2.15.0, Trivy v0.76.1, and the pinned October benchstat revision.
No quality threshold or test selection is weakened.

## Quality fixes and patch candidates

- `md5-simd/v1.2.2`: separate client registration and lane input handling from
  scheduling. Preserve client-channel ordering, digest reset/sum handling, buffer
  ownership, and SIMD/scalar selection. Remove an unreachable debug block.
- `sio/v0.5.5`: separate initial input and partial-package handling from the DARE
  2.0 reader loops. Preserve byte counts, errors, finalization, and buffer recycling.
  Extract the ReaderAt round-trip assertion without removing test cases.
- `simdjson-go/v0.4.9`: separate root-document interface conversion from scalar
  dispatch and correct three misspelled comments. Iterator advancement and error
  behavior are unchanged.

These are candidates until verified formal tags and Releases exist. The other
three runtime modules have no dependency or runtime-code changes in this update;
corrected README release information alone does not require new versions.

Go Report Card was regenerated with its complete six-check set and no checker
errors. MD5 and SIO now report 100%. SIMD JSON retains its true 95.8% aggregate:
its spelling check is now 100% and `Iter.Interface` no longer exceeds the
complexity threshold, but 13 files still contain complexity findings. These
include the parser state machine, serializer, float conversion, examples, tests,
and benchmarks. This patch does not hide those files, raise thresholds, or
rewrite the remaining algorithms merely to change the score.

## Validation boundaries

Local macOS ARM64 validation covers all modules' native tests, module verification,
helper generation/compilation, and SIO race tests. SIMD JSON's ARM64 tests skip
native parsing because no ARM64 parser exists; this is not parser validation.
Linux AVX2/CLMUL tests, race/coverage, and the existing cross-platform CI are
required before merging and releasing the affected modules.

A local six-sample SIO benchmark comparison used the same Apple M5 and Go 1.27.3.
Reader allocation counts were unchanged. Timing samples varied substantially,
including unchanged writer controls, so they establish no throughput claim.
Use the same-runner Linux benchmark comparison and retain its hardware metadata
before releasing the scheduling/reader refactors. Cross-compilation, native tests,
and measured performance must be reported separately.
