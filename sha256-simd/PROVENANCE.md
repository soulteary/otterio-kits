# SHA implementation provenance and ARM64 maintenance

Research date: 2026-10-11. Observed source history is separated from inference and unresolved authorization evidence. This record does not change the immutable import baseline or claim that prior upstream distribution was unlawful.

## ARM64 source and replacement

- jocover's [sole commit `019832c0331c5b0ae05f6e673f8581347d911834`](https://github.com/jocover/sha256-armv8/tree/019832c0331c5b0ae05f6e673f8581347d911834), dated 2016-04-28, contains `sha256-armv8-aarch64.S`. Its five-file tree has no license file; the assembly and README contain no explicit redistribution grant.
- MinIO's [reference implementation `904acabdd2104aaf8bb3663783b5486ca8af75b7`](https://github.com/minio/sha256-simd/commit/904acabdd2104aaf8bb3663783b5486ca8af75b7), dated 2016-07-20, explicitly cites jocover. Of 98 whitespace-normalized WORD instruction comments, 97 occur in jocover's implementation. This supports adaptation, not a legal conclusion.
- MinIO added Apache-2.0 headers in [commit `86b43afcb78d8d1eae14caa63db98c49c0125d45`](https://github.com/minio/sha256-simd/commit/86b43afcb78d8d1eae14caa63db98c49c0125d45). That commit does not document authorization from jocover. No additional grant was found in the inspected public records; private agreements or other sources may exist.

This revision removes `sha256block_arm64.s`, its wrapper, custom ARM64 feature detection and the README's copied instruction excerpt. Merely disabling the backend would leave inherited code in distributed sources. New module archives exclude the removed files; historical commits and tags remain intact.

On ARM64, New uses its existing crypto/sha256.New fallback; Sum256 explicitly calls crypto/sha256.Sum256. Changing only New would miss the one-shot path, which previously constructed an internal digest. The test-only forced-generic selector remains available to test the retained portable algorithm. ARM64 uses the portable build's unavailable-assembly sentinel. amd64 Intel SHA and AVX512 dispatch are unchanged.

Go 1.27.2's [ARM64 implementation](https://github.com/golang/go/blob/go1.27.2/src/crypto/internal/fips140/sha256/sha256block_arm64.go) detects SHA2 support and supplies a generic fallback. Only the public package is called; no Go assembly or internal API is vendored. noasm controls this kit's assembly, not the standard library, as was already true for New's fallback.

Public hash signatures, bytes, sizes and block sizes are unchanged. ARM64 New's unexported concrete implementation changes; additional interfaces supplied by the standard library may become observable. Compatibility tests exercise the retained internal digest directly, standard-library states and New, including cross-restoration and continuation. They do not promise stable state formats for arbitrary future Go versions or identical errors for every malformed state.

## Intel AVX512

MinIO's [initial commit `d243e153a46c5d9a2af94836e9ba614b85508e7d`](https://github.com/minio/sha256-simd/commit/d243e153a46c5d9a2af94836e9ba614b85508e7d), dated 2017-12-05, was merged through [PR #30](https://github.com/minio/sha256-simd/pull/30) on 2017-12-08. Its asm names Intel's avx512/sha256_x16_avx512.asm, conversion through minio/asm2plan9s, and full Intel BSD-3-Clause terms.

Intel's [pre-import revision `97595930c8d1e462733186f0e9d3ad4c14e12722`](https://github.com/intel/intel-ipsec-mb/blob/97595930c8d1e462733186f0e9d3ad4c14e12722/avx512/sha256_x16_avx512.asm), dated 2017-10-24, confirms the 2017 Intel notice and terms. It is a historical reference, not proof that MinIO used exactly that revision; the precise Intel revision remains unconfirmed.

The maintained asm retains the full terms. This revision copies them verbatim into LICENSE.Intel, adds Intel/MinIO attribution and license pointers to generated assembly, and updates NOTICE and the inventory. Executable instruction bytes are unchanged. Source and binary distributions must preserve the applicable notices, conditions and disclaimer. Apache-2.0 does not replace Intel's BSD terms. Preserve the header when regenerating assembly.

## Compatibility and preliminary measurements

An independent pre-change comparison on Go 1.27.2 / macOS ARM64 / Apple M5 passed 12 input lengths and 36 split points, digest equivalence, state equivalence, bidirectional restoration, prefix handling and Reset under the race detector. Three short benchmark samples per size measured approximately 61 ns versus 43 ns for 64 bytes, 359 ns versus 341 ns for 1 KiB, and about 3.2 GB/s for both implementations at 64 KiB and 1 MiB. These are exploratory observations, not cross-platform performance guarantees.

The maintained test additionally exercises the retained internal digest to avoid a trivial stdlib-to-itself comparison after replacement. Native amd64/AVX512 execution requires suitable CI hardware; cross-compilation proves build compatibility only. Release readiness still requires current-commit CI, packaging and external consumer checks from the release runbook. This update does not certify the whole dependency graph.
