# otterio-kits

为 otterIO 和 OC 统一维护基础 Go 组件的单仓多模块项目。六个库各自保留 `go.mod`、测试和许可证，独立发布；本仓库由 OtterIO 独立维护。

项目以固定上游版本导入并持续维护，尚未创建 OtterIO 发布 tag。`minio-go/v7` SDK 的 fork 单独维护，不放入本仓库。

- `highwayhash`：带密钥的 HighwayHash，来源 `minio/highwayhash v1.0.4`。
- `sha256-simd`：SHA-256 CPU 加速实现，来源 `minio/sha256-simd v1.0.1`。
- `simdjson-go`：SIMD JSON 解析，来源 `minio/simdjson-go v0.4.5`。
- `sio`：DARE 流式加密，来源 `minio/sio v0.5.1`。
- `crc64nvme`：CRC-64/NVME，来源 `minio/crc64nvme v1.1.1`。
- `md5-simd`：并行 MD5，来源 `minio/md5-simd v1.1.2`。

模块路径为 `github.com/soulteary/otterio-kits/<目录>`。保留原 package 名和公开 API；调用方需要显式迁移 import 路径。本次未修改 otterIO 或 OC 的依赖。

## 开发和验证

六个发行模块、两个辅助模块和根工作区统一使用 **Go 1.27.1**，与 otterIO、OC 一致。CI 从 `go.work` 读取版本，每个发行模块分别运行 Linux amd64、macOS ARM64 和 Windows amd64；检查脚本同时防止任一模块的 Go 声明偏离工作区。根 `go.work` 用于本地联合开发。

```sh
python3 scripts/verify-upstreams.py
bash scripts/check-modules.sh verify
bash scripts/check-modules.sh test
bash scripts/check-modules.sh noasm
bash scripts/check-modules.sh race
bash scripts/check-modules.sh cross
bash scripts/check-modules.sh tools
```

检查脚本逐个在 `GOWORK=off` 下运行，避免工作区掩盖缺失的模块依赖；会收集所有选定模块的结果后返回总状态。可以在模式后指定单个发行模块。`cross` 只编译目标平台包和测试二进制；`tools` 实际运行 MD5 生成器并编译临时产物，执行保留 JSON 基准的烟测。扩展平台入口见 [CI_TESTS.md](docs/CI_TESTS.md)。

`simdjson-go` 的解析器需要 amd64 上的 AVX2/CLMUL；ARM64 或 `noasm` 路径只有不支持平台的实现。宿主平台测试会报告 CPU 支持情况，不能将跳过解析测试当成该解析器已验证。

## 历史、来源和发布

每个上游以不带 `--squash` 的 subtree 合并导入，保留固定版本及其所有祖先的原始提交 SHA、作者和合并关系。导入提交中的子树逐个与上游原树核对；后续模块路径和维护配置另行提交。

完整来源与导入 SHA 在 [UPSTREAMS.json](UPSTREAMS.json)。按当前子目录过滤日志不一定显示全部上游历史；查原始提交可使用 `git log <上游 SHA>` 或 `git show <上游 SHA>:<原文件路径>`。

独立发行 tag 使用 `<目录>/vX.Y.Z`，例如 `highwayhash/v1.0.5`；保存来源的 `upstream/<目录>/<上游版本>` tag 不作为 Go 模块发行 tag。版本号示例不表示已发行。

- [详细执行计划](docs/IMPLEMENTATION_PLAN.md)
- [更新、历史检查和发布流程](docs/MAINTENANCE.md)
- [本次验证记录](docs/VALIDATION.md)
- [Go、依赖升级与 CI 修复记录](docs/UPGRADE.md)
- [原 CI 检查迁移对应关系](docs/CI_MIGRATION.md)
- [格式、vet 与统一工具版本](docs/CI_QUALITY.md)
- [逐模块测试、生成器与扩展平台](docs/CI_TESTS.md)
- [覆盖率、fuzz 与性能比较](docs/CI_REPORTS.md)
- [许可证与来源清单](docs/LICENSES.md)

六模块主协议均为 Apache-2.0，另外保留适用的 Go Authors BSD 和 Igneous MIT 许可材料。各模块的 `LICENSE*`、`NOTICE` 与原源码署名随独立发行保留。
