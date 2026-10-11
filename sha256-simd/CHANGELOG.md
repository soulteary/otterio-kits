# Changelog

## v1.0.3

- Use Go's public crypto/sha256 implementation for ARM64 New and Sum256; remove inherited ARM64 assembly and custom CPU detection. Public signatures and checksum results remain unchanged. The unexported concrete hash implementation and additional interfaces on ARM64 may differ.
- Preserve Intel AVX512 BSD terms in LICENSE.Intel, generated assembly attribution and NOTICE. Require LICENSE.Intel in the repository layout check. amd64 instruction and dispatch logic is unchanged.
- Add cross-implementation serialized-state and continuation regression tests. Compatibility is checked with Go 1.27.2; arbitrary future state formats and malformed-state errors are not guaranteed.
- Raise the minimum consumer Go version from 1.27.1 to 1.27.2 and refresh cpuid/x/sys dependencies.
- Document source provenance and remove obsolete ARM64 backend benchmarks. No cross-platform performance guarantee is made.

See PROVENANCE.md and UPSTREAMS.json for evidence and the retained upstream baseline (minio/sha256-simd v1.0.1). Historical tags remain intact.
