# Provenance and licenses

This repository maintains six independent Go modules imported from the upstream versions used by otterIO / OC at the initial import. `minio-go/v7` is outside its scope. Original source, copyright notices, and primary LICENSE files are retained; module-path changes do not replace existing licenses.

Each module has an added `NOTICE` containing its upstream URL, fixed baseline, and applicable license inventory for independent distribution. These are otterio-kits attribution additions, not claims that upstream provided files with the same name.

Inventory date: 2026-10-08 (Asia/Shanghai). This inventory describes fixed-baseline materials; it does not claim a complete audit of historical provenance, test data, or transitive dependencies.

## Module license materials

- **`highwayhash`, baseline `v1.0.4`**: primary license Apache-2.0; original Minio Inc. source notices are retained. Sources: [upstream version](https://github.com/minio/highwayhash/tree/v1.0.4), [upstream LICENSE](https://github.com/minio/highwayhash/blob/v1.0.4/LICENSE). Local: [LICENSE](../highwayhash/LICENSE).
- **`sha256-simd`, baseline `v1.0.1`**: primary license Apache-2.0. `sha256_test.go` contains full Go Authors BSD-3-Clause terms, copied into `LICENSE.Golang` with original headers retained. `sha256block_amd64.s` contains Kristofer Peterson's Apache-2.0 notice. Sources: [upstream version](https://github.com/minio/sha256-simd/tree/v1.0.1), [upstream LICENSE](https://github.com/minio/sha256-simd/blob/v1.0.1/LICENSE), [Go BSD source notice](https://github.com/minio/sha256-simd/blob/v1.0.1/sha256_test.go), [Kristofer Peterson notice](https://github.com/minio/sha256-simd/blob/v1.0.1/sha256block_amd64.s). Local: [LICENSE](../sha256-simd/LICENSE), [LICENSE.Golang](../sha256-simd/LICENSE.Golang).
- **`simdjson-go`, baseline `v0.4.5`**: primary license Apache-2.0. `appendfloat_f.go` and `ftoaryu.go` retain Go Authors BSD attribution; the full Go BSD-3-Clause text was added as `LICENSE.Golang`. Sources: [upstream version](https://github.com/minio/simdjson-go/tree/v0.4.5), [upstream LICENSE](https://github.com/minio/simdjson-go/blob/v0.4.5/LICENSE), [appendfloat_f.go](https://github.com/minio/simdjson-go/blob/v0.4.5/appendfloat_f.go), [ftoaryu.go](https://github.com/minio/simdjson-go/blob/v0.4.5/ftoaryu.go). Local: [LICENSE](../simdjson-go/LICENSE), [LICENSE.Golang](../simdjson-go/LICENSE.Golang).
- **`sio`, baseline `v0.5.1`**: primary license Apache-2.0; original Minio Inc. source notices are retained. Sources: [upstream version](https://github.com/minio/sio/tree/v0.5.1), [upstream LICENSE](https://github.com/minio/sio/blob/v0.5.1/LICENSE). Local: [LICENSE](../sio/LICENSE).
- **`crc64nvme`, baseline `v1.1.1`**: primary license Apache-2.0; original Minio Inc. source notices are retained. Sources: [upstream version](https://github.com/minio/crc64nvme/tree/v1.1.1), [upstream LICENSE](https://github.com/minio/crc64nvme/blob/v1.1.1/LICENSE). Local: [LICENSE](../crc64nvme/LICENSE).
- **`md5-simd`, baseline `v1.1.2`**: primary license Apache-2.0; upstream `LICENSE.Golang` is retained. `block8_amd64.s` contains the 2018 Igneous Systems copyright and full MIT terms, copied into `LICENSE.Igneous` with the original header retained. Sources: [upstream version](https://github.com/minio/md5-simd/tree/v1.1.2), [upstream LICENSE](https://github.com/minio/md5-simd/blob/v1.1.2/LICENSE), [upstream LICENSE.Golang](https://github.com/minio/md5-simd/blob/v1.1.2/LICENSE.Golang), [Igneous source notice](https://github.com/minio/md5-simd/blob/v1.1.2/block8_amd64.s). Local: [LICENSE](../md5-simd/LICENSE), [LICENSE.Golang](../md5-simd/LICENSE.Golang), [LICENSE.Igneous](../md5-simd/LICENSE.Igneous).

Added `LICENSE.Golang` files contain the full Go Authors BSD-3-Clause text. SHA's text was extracted from its complete test-source notice by removing comment prefixes. simdjson uses the same Go Authors license text and retains its original `Copyright 2009 The Go Authors. All rights reserved.` source headers. These additions do not relicense BSD code as Apache or change ownership.

## Import and modification records

Git history traces code provenance; license files and source headers carry notices in distributions. Preserve both. Repository maintenance records track imports and subsequent patches.

When modifying upstream files, retain original copyright headers and add a clear modification notice, for example:

```text
Modified by otterio-kits maintainers on 2026-10-08:
updated module imports for the otterio-kits multi-module repository.
```

The notice describes an actual change and does not replace copyright. Use the relevant date and description for future changes; do not copy it into unmodified files.

## Distribution materials

Each independent Go module distribution should include its LICENSE, applicable `LICENSE.Golang` / `LICENSE.Igneous`, original copyright headers, and module attribution. Root LICENSE and NOTICE files cannot replace module-specific materials.

otterIO, OC, and other binary/container distributions should provide applicable Apache, BSD, and MIT copyright/license notices in release notes or accompanying materials. Preserve any new upstream NOTICE or license materials when accepting patches and update this inventory. References: [Apache-2.0 section 4](https://www.apache.org/licenses/LICENSE-2.0.txt), [BSD-3-Clause](https://opensource.org/license/bsd-3-clause), [MIT](https://opensource.org/license/mit).

## Outstanding provenance checks

The upstream SHA [README](https://github.com/minio/sha256-simd/blob/v1.0.1/README.md) attributes AVX512 to Intel `intel-ipsec-mb`; its [ARM64 assembly](https://github.com/minio/sha256-simd/blob/v1.0.1/sha256block_arm64.s) identifies `jocover/sha256-armv8` as a source. These original attributions are retained, but the precise historical import commits and complete authorization chain have not been located. Complete this provenance check before releasing a further maintained SHA version.

This inventory does not cover all external Go modules/build tools, trademarks, name registrations, test data, or every historical commit. When upgrading dependencies or adding files, supplement materials based on actual content rather than relying solely on the repository's primary license.
