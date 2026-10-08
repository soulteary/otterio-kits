# Go、依赖升级与 CI 修复

更新日期：2026-10-08。初次导入的上游 SHA、原树、796 个原始提交与 `UPSTREAMS.json` 的 `upstream` / `import` 记录不变。本次是导入后的独立维护改动。

## 工具链与依赖

六个发行模块、两个辅助模块和 `go.work` 全部声明 `go 1.27.1`，与 otterIO、OC 一致。[Go 官方下载元数据](https://go.dev/dl/?mode=json)核实该版本是本次查询时的最新稳定版。移除 sio 旧的 `toolchain go1.24.10` 提示。

所有模块的直接及实际声明的间接依赖按官方 Go 模块代理的最新可用版本更新，分别执行 tidy。主要版本为：

- x/sys `v0.48.0`、x/crypto `v0.57.0`、x/term `v0.46.0`。
- cpuid/v2 `v2.4.0`、compress `v1.20.1`。
- 辅助汇编生成器：avo `v0.6.0`、x/mod `v0.41.0`、x/sync `v0.23.0`、x/tools `v0.51.0`。
- 辅助基准工具：jsonparser `v1.6.1`、modern-go/concurrent `v0.0.0-20180306012644-bacd9c7ef1dd`。
- json-iterator/go `v1.1.12`、modern-go/reflect2 `v1.0.2` 仍是最新稳定版本，继续保留。

八个模块分别对 `go.mod` 的 `require`（含间接）执行 `go list -mod=readonly -m -u -json`，全部没有 `Update`。基准模块指向父目录的本地 replace 继续保留，不作为外部模块升级。第三方模块图中没有被项目使用的模块由 tidy 管理，不额外引入依赖仅为了改变未使用的版本。

完整逐模块版本清单在 `UPSTREAMS.json` 的 `maintenance_updates`。原 `local_changes` 对应初次维护提交 `31f7ef5`，不代表本次升级后所有依赖仍是上游基线版本。

## CI 失败原因与修复

[原失败运行](https://github.com/soulteary/otterio-kits/actions/runs/37703368849)的两个 Linux amd64 作业都在 `TestNdjsonCountWhere2` 失败：测试隐式下载未入库的 `RC_2009-01.json.zst`；HTTP 非 200 时 `err` 为 nil，错误处理调用 `err.Error()` 导致 panic。两个作业均检测到 SIMDJSON CPU 支持，因此失败来自外部语料加载。

修复后该测试使用 12 行内联 NDJSON，保留 `countWhere` 和 `FindElement` 两条查询方式，并覆盖七个条件：普通匹配、大小写、空字符串、无匹配、另一字段、缺字段，样本包含非字符串与嵌套字段。前后空行也实际交给解析器。测试无需网络，也不会因 `-short` 被跳过。

共享 fixture helper 改为只读本地文件，错误包含文件路径且可用 `errors.Is` 判断；调用方通过 `testing.TB` 明确失败。删除隐式 HTTP 下载和循环重试。保留已入库的大语料测试；需要额外大数据的性能基准先在指定路径准备本地 fixture。缺失普通文件和 zstd 文件的回归检查通过。

根 CI 只保留 Go 1.27.1 的 Linux amd64 与 macOS ARM64 作业；setup-go 从 `go.work` 读取版本，移除旧 Go 1.24 兼容作业。缓存 glob 改为递归路径，覆盖两个辅助模块。布局检查新增八个 `go.mod` 与工作区 Go 声明一致性，避免后续升级漏改模块。

升级 cpuid/v2 后的 ARM64 `noasm` 验证还发现了 CPU 分派缺陷：检测到 SHA2 能力时选择了没有编译的汇编后端，导致 `TestGolden` panic。修复将 CPU 特征检测与构建时后端可用性共同作为启用条件；没有汇编后端时 Intel SHA、AVX512、ARM SHA2 均不启用。哈希算法和汇编正文不变。两个 CI 平台现在都执行 `noasm` 检查。

新增 portable 构建回归临时启用全部相关 CPU 特征，再确认分派仍关闭且 `New` 使用标准库，随后恢复 CPU 信息。SHA256 修复后的 ARM64 原生、noasm、race、noasm + race、appengine 检查均通过；amd64 原生与 noasm 也再次通过，两个 Linux 架构重新编译通过。

## 验证范围

已完成：八模块依赖校验、宿主 ARM64 原测试、race、适用 noasm 检查，Linux amd64 / ARM64 包及测试二进制交叉编译，六模块工作区联合测试，Bash / YAML 检查与原始历史验证。

另用官方 Go 1.27.1 darwin-amd64 工具链通过 Rosetta 执行六模块测试与四模块 noasm 检查，均通过。该环境没有 AVX2，SIMDJSON 解析相关测试仍跳过，不能视为 AVX2 解析器运行验证。

Go 1.27.1 与 avo 0.6.0 实际生成汇编及 stub 成功，输出保存在临时目录，未覆盖仓库原汇编。JsoniterApache_builds 与 BugerJsonParserLarge 两项 benchmark 各运行一次通过，实际检查升级后的解析依赖与 zstd 解压组合；这次烟测不用于性能结论。

远端 Linux amd64 CI 需要在更新推送后运行，验证实际 AVX2 解析路径及新增 NDJSON 条件。本次调整了 SHA256 的后端选择条件，算法及汇编正文保持原样；依赖升级后的 otterIO / OC 数据兼容回归仍按维护计划安排。
