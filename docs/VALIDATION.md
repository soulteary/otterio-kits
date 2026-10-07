# 初次导入与验证记录

日期：2026-10-08（Asia/Shanghai）。本机工具链 `go1.27.1 darwin/arm64`。

## 已完成的维护基线

六库以不带 `--squash` 的 `git subtree add` 导入；每个导入合并提交的第二父提交就是对应上游版本 SHA，导入时子目录树与上游原树完全一致。

- highwayhash `v1.0.4`：74 个原提交；导入 `64a6c5bc32d33e94c9e80ef5a2d52de013db292c`。
- sha256-simd `v1.0.1`：92 个原提交；导入 `62753cf46186b1345981718538304fe061cfe03d`。
- simdjson-go `v0.4.5`：451 个原提交；导入 `c55169ea6c677816e320faeaa435c6a9b795eeef`。
- sio `v0.5.1`：44 个原提交；导入 `f59beba80d0adab7f6e83074c4e107e8aa328355`。
- crc64nvme `v1.1.1`：20 个原提交；导入 `e6616cbb3a6c4cbc20709fcb38c598e943888d6a`。
- md5-simd `v1.1.2`：115 个原提交；导入 `0d5cd410f1c037d85999fa73aae99cb2f3e15f7e`。

总计与去重后均为 **796 个原始提交**。完整上游 SHA、原树、来源引用及后续改动记录在 `UPSTREAMS.json`。初次来源字段不变，今后更新追加到 `updates`。

模块路径、示例、自引用和维护配置在六次导入之后另行提交。六个发行模块的依赖版本、原 `go.sum`、公开 API、算法和原 Apache `LICENSE` 保持基线。100 个上游 Go / 汇编文件逐字反向比对：移除本次修改通知并还原声明的自引用路径后与原始文件一致。

辅助模块 `md5-simd/_gen` 和 `simdjson-go/benchmarks` 的路径同步迁移。基准模块保留本地父目录 replace；`go mod tidy -go=1.17` 对齐父库原本就选中的 compress `v1.15.15`、cpuid/v2 `v2.2.3` 和 x/sys 依赖，更新它自己的 `go.sum`。这项变动不改变六个发行库的依赖。

补充了六模块各自 NOTICE、两份 Go BSD 全文和 MD5 的 Igneous MIT 全文；原始头部署名和已有许可证未替换。

## 实际执行的验证

以下命令均已通过。Go 缓存使用 `/private/tmp/otterio-compat-modcache` 和 `/private/tmp/otterio-kits-gocache`，下载的依赖版本由各模块既有声明约束；检查使用只读模块模式。

- `python3 scripts/verify-upstreams.py`：非浅历史、祖先关系、六个原树、导入子树、原提交数和来源 tag 全部通过。
- `bash scripts/check-modules.sh layout`：发现全部八个 go.mod，工作区恰含六个发行库，逐模块许可材料齐全。临时副本验证了“新增未登记模块”和“工作区漏模块”会失败。
- `bash scripts/check-modules.sh verify`：八个模块在 `GOWORK=off` 下的依赖图、测试依赖和缓存校验通过。
- `bash scripts/check-modules.sh test`：六个库的宿主平台原测试通过；附带命令和示例包可编译。
- `bash scripts/check-modules.sh noasm`：highwayhash、sha256-simd、crc64nvme、md5-simd 四库通过。sio 没有该构建标签；simdjson 不提供可用的无汇编解析器，按脚本说明跳过。
- `bash scripts/check-modules.sh race`：六库的宿主平台 race 检查通过，SIMDJSON 仍受下面的平台限制。
- `bash scripts/check-modules.sh tools`：汇编生成器与基准工具编译通过；未运行生成器、未执行性能基准。
- `bash scripts/check-modules.sh cross`：六库的 Linux ARM64 包和测试二进制编译通过。
- `CROSS_GOARCH=amd64 bash scripts/check-modules.sh cross`：六库的 Linux amd64 包和测试二进制编译通过；最后一个模块补齐固定依赖后单独重跑通过。
- `GOWORK="$PWD/go.work" go test ./highwayhash/... ./sha256-simd/... ./simdjson-go/... ./sio/... ./crc64nvme/... ./md5-simd/...`：联合工作区测试通过。
- Bash 语法、CI YAML 解析和 `git diff --check`：通过。

交叉编译明确只生成目标平台程序，不运行 Linux 测试。

## 尚未执行的范围

本机 `simdjson.SupportedCPU()` 返回 false：ARM64 没有 SIMDJSON 解析器实现，实际解析测试会跳过。其测试命令成功只能说明当前可编译路径通过，不能证明 amd64 解析器或 SIMD 汇编路径正确。

根 CI 已设置完整历史校验、Go 1.27.1 Linux amd64 / macOS ARM64 和 Go 1.24 系列兼容检查。Linux amd64 测试强制核对 AVX2/CLMUL 能力，以免解析测试全跳过。远端 CI、本机以外的 CPU 运行以及 Go 1.24 系列检查尚待推送后执行，不能写成已通过。

未执行 otterIO / OC 依赖切换、旧磁盘校验和历史密文产品回归；未接收 tag 之后的未发布补丁。许可历史的剩余核查范围见 [LICENSES.md](LICENSES.md)。

本次没有推送远端，没有创建正式发行版本。下一阶段按执行计划审查未发布修复与数据兼容性，再安排独立发行和产品迁移。
