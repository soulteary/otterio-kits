# otterio-kits

为 otterIO 和 OC 统一维护基础 Go 组件的单仓多模块项目。六个库各自保留 `go.mod`、测试和许可证，独立发布；本仓库由 OtterIO 独立维护。

当前为本地导入基线，尚未创建 OtterIO 发布 tag。`minio-go/v7` SDK 的 fork 单独维护，不放入本仓库。

- `highwayhash`：带密钥的 HighwayHash，来源 `minio/highwayhash v1.0.4`。
- `sha256-simd`：SHA-256 CPU 加速实现，来源 `minio/sha256-simd v1.0.1`。
- `simdjson-go`：SIMD JSON 解析，来源 `minio/simdjson-go v0.4.5`。
- `sio`：DARE 流式加密，来源 `minio/sio v0.5.1`。
- `crc64nvme`：CRC-64/NVME，来源 `minio/crc64nvme v1.1.1`。
- `md5-simd`：并行 MD5，来源 `minio/md5-simd v1.1.2`。

模块路径为 `github.com/soulteary/otterio-kits/<目录>`。保留原 package 名和公开 API；调用方需要显式迁移 import 路径。本次未修改 otterIO 或 OC 的依赖。

## 开发和验证

六个发行模块最低 Go 声明保持上游版本，整个工作区至少需要 Go 1.24.0；`sio` 原工具链提示为 Go 1.24.10。本仓库 CI 检查 Go 1.24 系列与产品工具链 Go 1.27.1。根 `go.work` 仅用于本地联合开发。

```sh
python3 scripts/verify-upstreams.py
bash scripts/check-modules.sh verify
bash scripts/check-modules.sh test
bash scripts/check-modules.sh noasm
bash scripts/check-modules.sh race
bash scripts/check-modules.sh cross
bash scripts/check-modules.sh tools
```

检查脚本逐个在 `GOWORK=off` 下运行，避免工作区掩盖缺失的模块依赖。可以在模式后指定单个发行模块。`cross` 只编译目标平台包和测试二进制；`tools` 检查保留的两个辅助模块：`md5-simd/_gen` 和 `simdjson-go/benchmarks`。

`simdjson-go` 的解析器需要 amd64 上的 AVX2/CLMUL；ARM64 或 `noasm` 路径只有不支持平台的实现。宿主平台测试会报告 CPU 支持情况，不能将跳过解析测试当成该解析器已验证。

## 历史、来源和发布

每个上游以不带 `--squash` 的 subtree 合并导入，保留固定版本及其所有祖先的原始提交 SHA、作者和合并关系。导入提交中的子树逐个与上游原树核对；后续模块路径和维护配置另行提交。

完整来源与导入 SHA 在 [UPSTREAMS.json](UPSTREAMS.json)。按当前子目录过滤日志不一定显示全部上游历史；查原始提交可使用 `git log <上游 SHA>` 或 `git show <上游 SHA>:<原文件路径>`。

独立发行 tag 使用 `<目录>/vX.Y.Z`，例如 `highwayhash/v1.0.5`；保存来源的 `upstream/<目录>/<上游版本>` tag 不作为 Go 模块发行 tag。版本号示例不表示已发行。

- [详细执行计划](docs/IMPLEMENTATION_PLAN.md)
- [更新、历史检查和发布流程](docs/MAINTENANCE.md)
- [本次验证记录](docs/VALIDATION.md)
- [许可证与来源清单](docs/LICENSES.md)

六模块主协议均为 Apache-2.0，另外保留适用的 Go Authors BSD 和 Igneous MIT 许可材料。各模块的 `LICENSE*`、`NOTICE` 与原源码署名随独立发行保留。
