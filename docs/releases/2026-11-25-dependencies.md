# November 25, 2026 dependency maintenance

This update raises the minimum Go version from 1.27.3 to 1.27.4 in the six runtime
modules, both helper modules, and the root workspace. Consumers must use Go
1.27.4 or later. CI continues to read its toolchain version from `go.work`.

## Dependency changes

| Dependency | Previous | Updated | Modules |
| --- | --- | --- | --- |
| `github.com/klauspost/cpuid/v2` | `v2.4.1` | `v2.4.2` | CRC, MD5, SHA256, SIMD JSON, JSON benchmarks |
| `github.com/klauspost/compress` | `v1.20.3` | `v1.20.5` | SIMD JSON and JSON benchmarks |
| `golang.org/x/sys` | `v0.49.0` | `v0.50.0` | All six runtime modules and JSON benchmarks |
| `golang.org/x/crypto` | `v0.58.0` | `v0.59.0` | SIO |
| `golang.org/x/term` | `v0.47.0` | `v0.48.0` | SIO |
| `golang.org/x/mod` | `v0.42.0` | `v0.43.0` | MD5 assembly generator |
| `golang.org/x/sync` | `v0.24.0` | `v0.25.0` | MD5 assembly generator |
| `golang.org/x/tools` | `v0.52.0` | `v0.53.0` | MD5 assembly generator |

The dependency versions were checked against the public Go module proxy on
November 25, 2026. Other declared external dependencies were already current.
Each module's checksums are regenerated independently with `GOWORK=off`.

The JSON benchmark helper now declares the parser release candidate `v0.4.10`.
Its existing `replace => ../` intentionally measures the checked-out parser.
The helper is not independently released; after publishing the parser tag,
verify it again with the replacement removed in a temporary checkout and the
public `v0.4.10` module downloaded from the Go proxy.

## Independent patch candidates

| Module | Previous release | Candidate tag |
| --- | --- | --- |
| `crc64nvme` | `v1.1.4` | `crc64nvme/v1.1.5` |
| `highwayhash` | `v1.0.7` | `highwayhash/v1.0.8` |
| `md5-simd` | `v1.2.2` | `md5-simd/v1.2.3` |
| `sha256-simd` | `v1.0.4` | `sha256-simd/v1.0.5` |
| `simdjson-go` | `v0.4.9` | `simdjson-go/v0.4.10` |
| `sio` | `v0.5.5` | `sio/v0.5.6` |

These names are candidates until exact-commit checks, formal tags, public module
downloads, and GitHub Releases have been verified. Each Release must identify its
own module path, final commit, successful CI runs, and applicable platform checks.

Library sources, public API declarations, assembly, and retained license materials
are unchanged. No performance improvement is claimed. The original import
baselines and historical validation records remain in `UPSTREAMS.json` and the
existing maintenance documents.

## Validation

Local Go 1.27.4 Linux/amd64 checks passed for all eight modules' metadata,
formatting, vet, and tidy checks; all six runtime native suites; and both helper
entry points. SIMD JSON reported CPU support with `REQUIRE_SIMDJSON_CPU=1`.
Upstream history, CI layout, and centralized action-version checks passed.
The Python policy suite passed 76 of 79 tests locally; three benchmark-report
tests stopped during CPU metadata collection because this container's `lscpu`
cannot read `/sys/devices/system/cpu/possible`. The unchanged full suite remains
required in the remote Quality workflow.

Follow the [release procedure](../RELEASING.md) for the final merged commit.
Required checks include all eight modules' quality, lint, and vulnerability
checks; the six runtime modules' native Linux, macOS, and Windows tests; CodeQL;
the helper generator and benchmark entry points; and the extended platform
workflow. Linux SIMD JSON tests must require AVX2/CLMUL support. Cross-compilation
and unsupported-platform stub tests do not establish native parser correctness.

Create each directory-prefixed tag only after its required checks pass at the
final commit. Verify every module through the public proxy outside this workspace,
including its license files, before recording the corresponding release result.
