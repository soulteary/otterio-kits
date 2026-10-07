# otterio-kits 单仓多模块执行计划

计划日期：2026-10-08（北京时间）。

本次先建立六个基础库的统一维护仓库：保存上游基线及其原始提交历史，迁移模块路径，建立逐模块验证、来源记录和独立发布规则。`minio-go/v7` 继续作为独立 SDK 项目；otterIO、OC 的依赖切换以及上游未发布修复，分别安排后续工作。

本文描述执行步骤与验收标准。实际完成情况以仓库中的来源记录、导入提交和验证结果为准，不能仅凭计划中的勾选认定已通过。

## 1. 仓库结构和模块边界

六个组件直接位于仓库一级目录，各自保留 `go.mod`、`go.sum`、原始源码、测试、测试数据和许可材料：

```text
otterio-kits/
├── LICENSE
├── README.md
├── UPSTREAMS.json
├── docs/
├── go.work
├── scripts/
│   ├── check-modules.sh
│   └── verify-upstreams.py
├── .github/workflows/
├── highwayhash/
├── sha256-simd/
├── simdjson-go/
├── sio/
├── crc64nvme/
└── md5-simd/
```

模块路径分别为：

- `github.com/soulteary/otterio-kits/highwayhash`
- `github.com/soulteary/otterio-kits/sha256-simd`
- `github.com/soulteary/otterio-kits/simdjson-go`
- `github.com/soulteary/otterio-kits/sio`
- `github.com/soulteary/otterio-kits/crc64nvme`
- `github.com/soulteary/otterio-kits/md5-simd`

根目录不增加用于包发布的 `go.mod`，避免把六个组件绑定成同一个版本。`go.work` 仅用于仓库内开发和联合检查。每个模块必须在 `GOWORK=off` 条件下单独构建和测试，确保离开工作区后仍可独立使用。

初次迁移保留 package 名、公开 API、算法、密文格式、构建标签和六个发行模块的依赖版本。模块路径变化是本次迁移的有意变化；不能把成功编译当成存量数据兼容性已经全面验证。另保留 `md5-simd/_gen` 与 `simdjson-go/benchmarks` 两个辅助模块，单独检查且不发行；基准模块保留本地父目录 replace，并对齐父模块已有的依赖元数据。

## 2. 固定六个导入基线

以用户当前依赖版本作为初次基线，导入前从 Git 仓库再次解析 tag 指向的 commit，并与以下完整 SHA 比较：

- **highwayhash**：上游 `https://github.com/minio/highwayhash.git`，tag `v1.0.4`，commit `070ab1a87a76ab3c81950392f2991dc0ba638585`。
- **sha256-simd**：上游 `https://github.com/minio/sha256-simd.git`，tag `v1.0.1`，commit `6096f891a77bfe490cbea7a424c821b5fdb92849`。
- **simdjson-go**：上游 `https://github.com/minio/simdjson-go.git`，tag `v0.4.5`，commit `d82c779820b28b701fc258ee32f5df4ffc368f2d`。
- **sio**：上游 `https://github.com/minio/sio.git`，tag `v0.5.1`，commit `e1fddaac73108d378e89df17f4c3e2b53e5122c8`。
- **crc64nvme**：上游 `https://github.com/minio/crc64nvme.git`，tag `v1.1.1`，commit `cc422c7b1355e33091486ab1e6d461aba6fcaf69`。
- **md5-simd**：上游 `https://github.com/minio/md5-simd.git`，tag `v1.1.2`，commit `776275e0c9a74ceebbd50fe5c1d61b0c80c608df`。

这些基线不包含 tag 之后的未发布修改。`UPSTREAMS.json` 来源记录应另外注明上游默认分支，供后续审查更新时使用，但不能用变动中的分支名替代固定 commit。

验收要求：每个基线的 tag、完整 SHA 和导入目录一一对应；发现 tag 指向变化时停止该组件导入并记录差异，其他已核实组件可继续。

## 3. 保存原始历史的方法

采用 **不带 `--squash` 的 Git subtree 导入**。每个组件单独建立一个导入合并提交，上游基线 commit 成为合并历史的祖先，文件落入对应目录。这保留基线及其所有可达祖先的原始 commit SHA、作者、时间、消息和合并关系，不改写原始仓库历史。

示例流程如下，执行前需确保工作树干净，并先核对 commit：

```sh
git remote add upstream-highwayhash https://github.com/minio/highwayhash.git
git fetch --no-tags upstream-highwayhash master
git fetch --no-tags upstream-highwayhash refs/tags/v1.0.4
git rev-parse FETCH_HEAD^{commit}
git subtree add --prefix=highwayhash 070ab1a87a76ab3c81950392f2991dc0ba638585
```

初次 fetch 不能只取浅历史。若环境只有浅克隆，先补全基线的祖先；Git 对象不存在或历史未完整取到时，不能声明已保留完整基线历史。

`cherry-pick` 适合后续选择某一修复，但通常生成新的 commit SHA，不能作为完整保留原历史的主要方法。即使保留作者和原始消息，它也不等同于把原提交及其原合并关系保存在当前主线中。`cherry-pick -x` 可以记录来源，但根目录路径仍需要适配组件目录。

导入后应明确区分两类提交：

1. **导入提交**：子目录内容与上游基线树完全一致。
2. **OtterIO 维护提交**：模块路径、内部 import、文档、许可补充和仓库治理修改；每项修改都可与基线比较。

原提交中的文件路径仍是上游仓库的根目录路径。查阅原历史可使用 `git log <基线 SHA>`、`git show <原 SHA>:<上游路径>`；直接按当前子目录过滤日志，不一定显示全部上游提交。后续 subtree 导入也应持续不使用 squash，不对已经共享的导入历史做 rebase。

保存原始历史的范围是“导入基线及其所有可达祖先”，不是所有远端分支、未合并 PR 和基线之后的提交。若后续需要这些对象，应另行 fetch、审查并记录。

## 4. 分阶段执行与验收

### 阶段 A：准备、清点和可恢复性

1. 确认目标仓库、当前分支、远端、工作树和现有提交；保留现有根 `LICENSE`。
2. 阅读仓库约定，清点六个上游 tag、commit、许可证、构建标签、依赖和测试数据。
3. 给每个上游使用独立 remote 名；避免把六个仓库的同名 `v1.0.0` 等 tag 混入根发布命名空间。
4. 记录操作前 commit。必要时创建恢复点；不使用硬重置或强制推送清理用户已有内容。

验收：目标正确，既有内容可恢复，六个基线 SHA 全部核实，来源清单可供其他维护者重做导入。

### 阶段 B：逐库导入，先验证原树

按 highwayhash、sha256-simd、simdjson-go、sio、crc64nvme、md5-simd 的顺序逐个导入。每次导入后，先完成以下检查再进行模块改名：

- 原始基线 SHA 是导入提交的祖先。
- 上游基线树与导入提交中的组件子树完全一致，包括 LICENSE、测试数据、汇编和 dotfiles。
- 原提交的作者、时间、消息和父提交仍可查询。
- `UPSTREAMS.json` 记录导入 SHA、基线 SHA、目录和导入时的祖先提交数量；用数量和可达性确认历史没有被 squash。

验收：六个组件均有独立导入提交，所有基线祖先可达，未混入 tag 之后的功能修改。导入中的上游 `.github` 文件作为来源保留，但不会自动成为本仓库根级 GitHub Actions 工作流。

执行 `python3 scripts/verify-upstreams.py` 可只读检查 `UPSTREAMS.json`、基线和导入提交的可达性、原树/导入子树一致性、六库原始祖先数量及去重总数。完整历史是硬性要求；缺少命名空间来源 tag 只提示警告，因为普通消费者 clone 可能未取全部 tag。历史基线仍须是当前 HEAD 祖先。`md5-simd/_gen`、`simdjson-go/benchmarks` 的嵌套 `go.mod` 是保留的上游工具模块，不能误计为第七、第八个发布模块。

### 阶段 C：迁移模块身份和补齐来源材料

1. 将各 `go.mod` 的 `module` 改为本仓库的子模块路径。
2. 迁移模块内部自引用 import、示例和安装说明；外部第三方依赖保持原版本。
3. 不批量改写原作者署名或原始 Git 历史。在修改文件中保留原头部，并明确记录本次维护改动。
4. 维护 `UPSTREAMS.json`：上游 URL、基线 tag/SHA、导入 SHA、原许可材料、路径迁移和后续补丁来源。
5. 保留组件 README 的技术说明；根 README 明确说明此仓库由 OtterIO 独立维护，列出六个上游来源和各模块用途。
6. 保存必要的第三方许可文本与 NOTICE。每个独立 Go 模块都应携带自身发行所需的材料，不能仅靠根目录汇总代替。

验收：没有遗留的本模块旧自引用；六模块能独立解析依赖；来源可溯；与基线的差异限于已声明的迁移及治理内容。

### 阶段 D：统一维护入口和逐模块 CI

1. 根 `go.work` 列出六模块，选择能覆盖全部模块声明的 Go 工具链版本。
2. `scripts/check-modules.sh` 维护显式模块清单，并核对清单与实际 `go.mod`、`go.work` 一致；新增模块时不能静默漏测。
3. 根 CI 对六模块分别执行测试和静态检查。仅在根运行 `go test ./...` 不能覆盖多模块仓库，不能作为验收依据。
4. 在工作区模式与 `GOWORK=off` 独立模式分别验证；CI 不依赖本地 `replace` 或用户目录缓存才能成功。
5. 执行宿主平台测试、适用的 race/noasm 测试、Linux amd64/arm64 交叉构建。执行范围受组件支持平台和构建标签约束；不支持的平台记录为不适用。
6. 独立 CI 文件放在根 `.github/workflows`；模块中的历史工作流不承担现行 CI。

验收：六模块全部被入口覆盖，独立模式通过，工具链要求明确，失败不会被循环脚本忽略。交叉构建结果与真实硬件执行结果分开记录。

### 阶段 E：完成本次本地交付

1. 保存导入历史、来源清单、执行计划、验证结果和已知限制。
2. 审查最终 diff，确认未无意改动算法、API、密文格式或第三方依赖。
3. 将治理改动形成便于审查的独立提交，保留六个导入提交和原始历史。
4. 本次完成本地仓库整理与验证。推送、正式 tag 和产品依赖升级作为明确的发布步骤执行，不把草案版本称作已发布版本。

验收：另一个维护者可以从仓库文档复现来源检查和逐模块验证，并判断哪些兼容性检查尚未执行。

## 5. 许可与来源维护

六个组件的上游根 LICENSE 均为 Apache-2.0。本仓库同时保留源码中的其他版权和许可声明；根协议汇总不能覆盖或替换这些材料。

- **highwayhash、sio、crc64nvme**：保留各组件原 LICENSE、头部署名及已有通知；每次接收补丁重新检查新增材料。
- **sha256-simd**：保留测试源码内 Go Authors BSD 条款、Kristofer Peterson 的 Apache 署名、ARM64 来源注释，以及 README 中 Intel 实现的来源说明。Intel/jocover 相关历史来源仍需进一步核实，不能据本次导入声称已完成全部许可溯源。
- **simdjson-go**：保留 `appendfloat_f.go`、`ftoaryu.go` 的 Go Authors 声明，补齐可随模块发行的对应 Go BSD 许可全文，并记录补充材料的来源。
- **md5-simd**：保留 `LICENSE.Golang`；保留汇编中 Igneous Systems 的 MIT 全文与 MinIO 署名，发行通知中同时列明。

来源文档应区分“完整原文保存”“为独立发行补充的许可材料”和“待核实历史来源”，不能把待核实项写成已经结案。二进制、镜像和源码压缩包发布时，检查适用通知是否随对应发行物提供。此次许可清点不代替所有第三方依赖、测试资产和品牌名称的完整审查。

## 6. 与存量数据兼容相关的验证

本次以原测试、树一致性和最小迁移 diff 验证导入；后续修改算法、解析器或加密逻辑前，必须增加与实际产品路径对应的回归检查：

- **highwayhash**：固定 key/input 的 64、128、256 位输出，分块写入和不同 CPU 实现一致；从 otterIO 提取代表性的已有磁盘校验向量。
- **sha256-simd**：与 `crypto/sha256` 对照空输入、块边界、大输入、Reset 和分块写入；涉及状态序列化时验证旧状态的恢复。AVX512 服务路径单独评估。
- **simdjson-go**：覆盖 Unicode 转义、JSON 浮点与整数边界、过滤遍历、删除元素、不同构建路径；上游 issue 的失败报告先复现，再决定补丁。
- **sio**：保留可公开分发的固定密钥、nonce、版本和密文夹具；验证旧密文可解密、截断/篡改可识别、读写分块和协议版本兼容。任何密钥派生修改必须明确兼容边界。
- **crc64nvme**：固定 NVMe CRC 向量、不同 alignment、分块 Update、无 SIMD 路径和可运行的 SIMD 路径一致；非法指令问题需要对应 CPU 环境验证。
- **md5-simd**：与 `crypto/md5` 对照并发客户端、分块输入、Reset/Close 和复用路径；池化、寄存器保存修复需要具体回归案例。

race 检查和交叉编译不能证明 SIMD 汇编所有硬件路径均正确。首次发布前安排真实 Linux amd64/arm64 运行；AVX2/AVX512 等专用路径只有在支持硬件上执行过，才能记录为已验证。

## 7. 后续接收上游更新

每次只更新一个组件，以固定 commit 为目标：

1. fetch 对应上游，比较当前记录基线到目标 SHA 的代码、依赖、API、许可证和构建要求。
2. 明确选择整个上游更新，还是仅接收某个修复；上游未关闭 issue 不能直接认定为产品当前缺陷。
3. 整体更新优先继续使用非 squash subtree pull/merge。模块路径、维护说明和许可补充可能冲突，解决后必须保留本仓库模块身份。
4. 单独修复采用带来源的补丁应用或 cherry-pick，并适配子目录。记录原 SHA、PR、适配原因和新维护提交；以后整体更新时核对是否重复引入。
5. 将更新追加到 `UPSTREAMS.json` 的 `updates` 和变更记录，再运行该模块独立测试、相关跨模块检查和对应产品兼容回归。初次导入的 `upstream` / `import` 记录不可覆盖；后续合并子树包含本地维护改动，应检查新上游的祖先关系和维护差异，而不是套用初次原树相等条件。
6. 基准测试需记录 Go 版本、CPU、输入大小及并发度；仅有一次性能结果不能作为改动合入的全部依据。

应保留已记录的原始 Git 对象和 `refs/tags/upstream/<模块>/<基线版本>` 来源引用。恢复上游 remotes 的命令应可由 `UPSTREAMS.json` 重建，因为 `.git/config` 不会随普通 clone 分发。

## 8. 独立版本与发布规则

Go 子模块 tag 使用目录前缀，例如 `highwayhash/v1.0.5`、`simdjson-go/v0.4.6`。示例仅说明格式，本次不据此创建正式 tag。

- 原上游版本是导入来源，不是 OtterIO 已发布版本；发行说明明确区分二者。
- 原上游 tag 如需永久保存，使用 `upstream/<组件>/<tag>` 命名空间，避免六库同名 tag 冲突；这些来源 tag 不作为本仓库 Go 模块发布 tag。
- 各模块按自己的变更独立发版；无需为了一个组件修复同时给六个模块打 tag。
- 不随意撤回或移动公开 tag。新增不兼容 API 时按 Go 主版本规则评估 `/v2` 模块路径。
- 发布前在仓库外的临时消费者中使用 `GOWORK=off` 解析模块，核对 tag、module 路径、许可材料及可公开访问的来源。
- 每个版本记录基线、OtterIO 维护补丁、Go 最低版本、验证硬件和已知限制。

## 9. 后续范围与优先顺序

本次导入结束后，再安排以下独立工作，避免把建立维护基线与功能修复混在一起：

1. 审查 `md5-simd`、`simdjson-go` 的已合并未发布修复，并用复现用例决定接收范围。
2. 对 `sha256-simd` 的产品实际调用进行标准库替换评估；保留库基线不等于承诺继续使用其所有实现。
3. 独立建立 `otterio-go` SDK fork，再共同迁移 otterIO、OC 的依赖路径和 API 类型。
4. 对 HighwayHash 磁盘校验、SIO 历史密文和 SIMD 实机路径执行产品回归。
5. 确定首批独立发布版本，执行远端推送、模块下载验证和正式发布。

只有各阶段验收证据实际产生后，才将其记录为完成；未执行的产品兼容性检查、真实硬件验证及许可历史核实持续列入维护清单。
