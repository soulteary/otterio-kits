# 来源与许可证

本仓库集中维护以下六个独立 Go 模块。导入基线为当前 otterIO / OC 使用的上游版本；`minio-go/v7` 不在本仓库范围内。每个模块的上游源码、版权声明和主 `LICENSE` 均保留，模块路径变更不替代原有许可。

每个模块新增独立的 `NOTICE`，用于在单独发布模块时携带上游地址、固定基线和适用许可材料索引。它们是 otterio-kits 新增的集中归属说明，不是声称上游原有同名文件。

核对日期：2026-10-08（Asia/Shanghai）。本清单描述固定基线中的许可材料，不宣称完成所有历史来源、测试数据和传递依赖的许可审计。

## 各模块的许可材料

- **`highwayhash`，基线 `v1.0.4`**：主协议 Apache-2.0。保留源码中的 Minio Inc. 版权声明。来源：[上游仓库及版本](https://github.com/minio/highwayhash/tree/v1.0.4)、[上游 LICENSE](https://github.com/minio/highwayhash/blob/v1.0.4/LICENSE)；本地材料：[LICENSE](../highwayhash/LICENSE)。
- **`sha256-simd`，基线 `v1.0.1`**：主协议 Apache-2.0；`sha256_test.go` 另含 The Go Authors 的完整 BSD-3-Clause 条款，集中复制到 `LICENSE.Golang`，原页头仍保留。`sha256block_amd64.s` 含 Kristofer Peterson 的 Apache-2.0 版权声明。来源：[上游仓库及版本](https://github.com/minio/sha256-simd/tree/v1.0.1)、[上游 LICENSE](https://github.com/minio/sha256-simd/blob/v1.0.1/LICENSE)、[Go BSD 源声明](https://github.com/minio/sha256-simd/blob/v1.0.1/sha256_test.go)、[Kristofer Peterson 源声明](https://github.com/minio/sha256-simd/blob/v1.0.1/sha256block_amd64.s)；本地材料：[LICENSE](../sha256-simd/LICENSE)、[LICENSE.Golang](../sha256-simd/LICENSE.Golang)。
- **`simdjson-go`，基线 `v0.4.5`**：主协议 Apache-2.0；`appendfloat_f.go` 和 `ftoaryu.go` 带 The Go Authors 的 BSD 来源声明。保留这些声明，并补充 Go 项目的完整 BSD-3-Clause 文本至 `LICENSE.Golang`。来源：[上游仓库及版本](https://github.com/minio/simdjson-go/tree/v0.4.5)、[上游 LICENSE](https://github.com/minio/simdjson-go/blob/v0.4.5/LICENSE)、[appendfloat_f.go](https://github.com/minio/simdjson-go/blob/v0.4.5/appendfloat_f.go)、[ftoaryu.go](https://github.com/minio/simdjson-go/blob/v0.4.5/ftoaryu.go)；本地材料：[LICENSE](../simdjson-go/LICENSE)、[LICENSE.Golang](../simdjson-go/LICENSE.Golang)。
- **`sio`，基线 `v0.5.1`**：主协议 Apache-2.0。保留源码中的 Minio Inc. 版权声明。来源：[上游仓库及版本](https://github.com/minio/sio/tree/v0.5.1)、[上游 LICENSE](https://github.com/minio/sio/blob/v0.5.1/LICENSE)；本地材料：[LICENSE](../sio/LICENSE)。
- **`crc64nvme`，基线 `v1.1.1`**：主协议 Apache-2.0。保留源码中的 Minio Inc. 版权声明。来源：[上游仓库及版本](https://github.com/minio/crc64nvme/tree/v1.1.1)、[上游 LICENSE](https://github.com/minio/crc64nvme/blob/v1.1.1/LICENSE)；本地材料：[LICENSE](../crc64nvme/LICENSE)。
- **`md5-simd`，基线 `v1.1.2`**：主协议 Apache-2.0；保留上游已有 `LICENSE.Golang`。`block8_amd64.s` 含 Copyright (c) 2018 Igneous Systems 及完整 MIT 条款，集中复制到 `LICENSE.Igneous`，原页头仍保留。来源：[上游仓库及版本](https://github.com/minio/md5-simd/tree/v1.1.2)、[上游 LICENSE](https://github.com/minio/md5-simd/blob/v1.1.2/LICENSE)、[上游 LICENSE.Golang](https://github.com/minio/md5-simd/blob/v1.1.2/LICENSE.Golang)、[Igneous Systems 源声明](https://github.com/minio/md5-simd/blob/v1.1.2/block8_amd64.s)；本地材料：[LICENSE](../md5-simd/LICENSE)、[LICENSE.Golang](../md5-simd/LICENSE.Golang)、[LICENSE.Igneous](../md5-simd/LICENSE.Igneous)。

新增的 `LICENSE.Golang` 使用 The Go Authors 的完整 BSD-3-Clause 文本。`sha256-simd` 的文本由其测试源码中完整通知去掉注释前缀提取；`simdjson-go` 使用同一份 Go Authors 许可文本，保留其源码中原有的 `Copyright 2009 The Go Authors. All rights reserved.` 页头。补充文件不把 BSD 代码改授为 Apache，也不改变原版权归属。

## 导入及修改的记录

原始 Git 提交记录用于追溯代码来源；许可证文件和源码页头用于随发行物保留许可通知。两者均应保存。源码导入记录和后续补丁记录由仓库维护文档单独维护。

修改上游文件时，应保留原版权页头，并在文件中加入明确的变更通知。例如：

```text
Modified by otterio-kits maintainers on 2026-10-08:
updated module imports for the otterio-kits multi-module repository.
```

这条通知描述实际变更，不表示取代原版权。后续修改使用对应的日期和内容，不能机械复制这个示例到未修改的文件。

## 发布时保留的材料

独立 Go 模块发布包应包含该模块的 `LICENSE`、适用的 `LICENSE.Golang` / `LICENSE.Igneous`、原版权页头及模块归属说明。仓库根 `LICENSE` 和 `NOTICE` 不能替代子模块发布包中的通知；只发布单个子模块时，仍应携带它的适用许可材料。

otterIO、OC 或其他二进制、容器发行物应在发行说明或随附材料中提供所用组件的 Apache、BSD、MIT 版权和许可通知。原上游若增加 `NOTICE` 或其他许可证材料，接收补丁时一并保留并更新清单。可直接参考 [Apache-2.0 原文第 4 条](https://www.apache.org/licenses/LICENSE-2.0.txt)、[BSD-3-Clause 原文](https://opensource.org/license/bsd-3-clause)和 [MIT 原文](https://opensource.org/license/mit)。

## 尚需进一步追溯的来源

`sha256-simd` 的上游 [README](https://github.com/minio/sha256-simd/blob/v1.0.1/README.md) 说明 AVX512 实现来自 Intel `intel-ipsec-mb`；[ARM64 汇编](https://github.com/minio/sha256-simd/blob/v1.0.1/sha256block_arm64.s) 说明实现基于 `jocover/sha256-armv8`。本轮保留这些原始来源声明，但未定位历史导入时的精确提交和完整授权链；进一步发布维护版前，应完成这一来源核查。

本清单不覆盖外部 Go 模块和构建工具的完整许可清单，也不覆盖商标、名称注册、测试数据或全部历史提交的来源。升级外部依赖或引入新文件时，应根据其实际内容补充许可材料，不能只依据仓库主协议作判断。
