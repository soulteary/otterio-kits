# 逐模块发布

`otterio-kits` 维护六个独立的 Go 库。一个 Git 提交可以包含多个模块的改动，但每个模块有自己的版本、tag 和发行说明；修改 `simdjson-go` 不要求同时发布 CRC 或加密库。根目录没有用于发行的 `go.mod`，也不发布一个包含六库的根 Go 模块。

本文是维护者的操作指南。仓库已有主线和模块 CI，当前没有自动发布工作流，也没有正式发行 tag 的 CI 触发入口。下面的发布命令须由维护者在完成检查后执行；本文中的候选版本和命令不表示已经发布。

## 模块身份与首发候选

模块路径已迁移为 `github.com/soulteary/otterio-kits/<目录>`。Go 子目录模块的 tag 必须包含目录前缀，而消费者使用的版本号不含这个前缀。例如：

```text
module: github.com/soulteary/otterio-kits/crc64nvme
Git tag: crc64nvme/v1.1.2
go.mod: github.com/soulteary/otterio-kits/crc64nvme v1.1.2
```

以下候选沿用上游版本序列，递增一个补丁号，便于说明导入基线和 OtterIO 维护版的关系。它们是六个新模块路径的首发候选，不是已发行版本，也不表示与 MinIO 同名版本具有相同内容：

- `highwayhash/v1.0.5`：基于上游 `v1.0.4`。
- `sha256-simd/v1.0.2`：基于上游 `v1.0.1`。
- `simdjson-go/v0.4.6`：基于上游 `v0.4.5`。
- `sio/v0.5.2`：基于上游 `v0.5.1`。
- `crc64nvme/v1.1.2`：基于上游 `v1.1.1`。
- `md5-simd/v1.1.3`：基于上游 `v1.1.2`。

维护者可以另定独立版本序列，但需在首发前统一规则。保留 `simdjson-go`、`sio` 的 `v0` 成熟度声明；迁移仓库和模块路径不构成自动升级为 `v1` 的依据。发行说明应记录本仓库实际改动，不能只写“上游补丁版本”。之后各模块单独按语义版本管理：修复使用 patch，兼容的新 API 使用 minor，稳定模块不兼容的公开 API 或已承诺行为变更使用新的 major。`v2` 及以上还要迁移 module/import 路径为 `/v2` 等后缀，例如 `github.com/soulteary/otterio-kits/crc64nvme/v2`，对应 tag 为 `crc64nvme/v2.0.0`。

保留原 package 名，路径中的连字符不成为 Go 标识符。引用示意如下，实际程序只导入使用的包：

```go
import (
    highwayhash "github.com/soulteary/otterio-kits/highwayhash"
    sha256 "github.com/soulteary/otterio-kits/sha256-simd"
    simdjson "github.com/soulteary/otterio-kits/simdjson-go"
    sio "github.com/soulteary/otterio-kits/sio"
    crc64nvme "github.com/soulteary/otterio-kits/crc64nvme"
    md5simd "github.com/soulteary/otterio-kits/md5-simd"
)
```

六个发行库及两个辅助模块的 `go` 声明目前都是 `1.27.2`。这是消费者的最低 Go 要求，不只是 CI 使用的工具链版本；低于该版本的工具链无法在 `GOTOOLCHAIN=local` 下使用这些发行版。发行说明须写明最低版本。后续调整最低版本时，应按影响单独说明。

`md5-simd/_gen` 是汇编生成器，`simdjson-go/benchmarks` 是比较工具，不在本次发行清单中，不给它们创建库发行 tag。benchmarks 的本地 `replace => ../` 用于测量当前父模块；六个发行库不依赖这个替换。Go 的模块下载包排除带有嵌套 `go.mod` 的辅助目录。

## 准备一个候选提交

以 `crc64nvme` 为例，从已合并的 `main` 提交准备发布。先把代码、依赖、必要的生成文件和该模块的发行说明经 PR 合入主线。确认将使用的完整 SHA 在 `main` 上，不能根据一个通过检查的旧提交给更新后的 `HEAD` 打 tag。

在仓库根目录，使用一个干净的检出创建候选分支，冻结本次检查对象：

```sh
git fetch origin main
test -z "$(git status --porcelain)"

release_module=crc64nvme
release_version=v1.1.2
release_tag="$release_module/$release_version"
release_commit=$(git rev-parse origin/main)
candidate_branch="release-candidate-$release_module-$release_version"

git switch --create "$candidate_branch" "$release_commit"
git show --no-patch --format=fuller "$release_commit"
```

分支名和 tag 名中的版本号替换为本次确定的版本；分支已存在时先检查它的 SHA，不能强制覆盖。记录完整 `release_commit`，之后的本地检查、远端 CI、tag 以及发行说明都使用这一提交。候选检查发现问题时，先通过修复 PR 更新 `main`，再选择新的候选提交、创建新的候选分支并重新验证。

## 检查独立模块

根 `go.work` 仅供仓库内联合开发，消费者不会靠它补齐依赖。检查必须关闭工作区；脚本已经设置 `GOWORK=off` 和只读模块模式。对单个候选执行：

```sh
python3 scripts/verify-upstreams.py
python3 scripts/verify-ci-layout.py
python3 scripts/check-quality.py format "$release_module"
python3 scripts/check-quality.py vet "$release_module"
python3 scripts/check-quality.py tidy "$release_module"
bash scripts/check-modules.sh verify "$release_module"
bash scripts/check-modules.sh test "$release_module"
bash scripts/check-modules.sh noasm "$release_module"
bash scripts/check-modules.sh cross "$release_module"
```

使用与 `go.work` 一致的工具链。`tidy` 模式只检查元数据差异，不能忽略失败后直接发版。`cross` 只编译，不证明目标平台运行正确。`noasm` 只在提供有效便携实现的模块上有相应算法验证含义；`simdjson-go` 的不支持平台实现不能证明解析器正确。原生解析测试需要 Linux amd64 的 AVX2/CLMUL，专用汇编路径的验证应记录实际运行的硬件能力。

发布 MD5 生成器相关改动时，额外运行 `bash scripts/check-modules.sh tools md5-simd/_gen`；JSON 基准相关改动使用 `bash scripts/check-modules.sh tools simdjson-go/benchmarks`。选择对应模块的完整 CI 检查结果，包括质量、lint、govulncheck、CodeQL 和 Linux/macOS/Windows 原生测试。涉及平台或汇编变更时再检查扩展平台结果，参考 [CI_TESTS.md](CI_TESTS.md) 与 [CI_SECURITY.md](CI_SECURITY.md)。

当前六个发行库之间没有 `require` 依赖。如果今后引入模块间依赖，先发布被依赖的模块，再把依赖方的 `go.mod` 固定到公开版本并验证；不能依靠 `go.work` 或本地 `replace` 发布。

## 在相同 SHA 手动运行 CI

当前工作流没有正式 tag 的触发规则。发布前手动运行全量检查，不把推送 tag 当成已经运行测试。将候选分支推到指定远端分支，再从它触发检查：

```sh
git push origin "refs/heads/$candidate_branch:refs/heads/$candidate_branch"
gh workflow run quality.yml --ref "$candidate_branch"
gh workflow run ci.yml --ref "$candidate_branch"
gh workflow run lint.yml --ref "$candidate_branch"
gh workflow run security.yml --ref "$candidate_branch"
```

这些入口的 `workflow_dispatch` 检查全量模块。平台、汇编或生成器改动需要扩展检查时，再手动运行：

```sh
gh workflow run extended.yml --ref "$candidate_branch"
```

`workflow_dispatch` 的 `ref` 使用分支或 tag 名。候选分支让它固定到同一个已合入主线的提交，避免运行期间 `main` 前进导致验证对象改变。查看运行记录：

```sh
gh run list --branch "$candidate_branch" --event workflow_dispatch \
  --json databaseId,workflowName,headSha,status,conclusion,url
```

逐一核对上述入口的 `headSha` 等于完整 `release_commit`，等待对应运行成功。不能使用别的 SHA 的绿灯，也不能把部分模块检查成功写成全量检查通过。记录各运行 URL 和实际平台；只有当前候选需要的检查完成后才创建正式 tag。覆盖率、fuzz 与性能报告按实际改动选择运行，报告中区分烟测和性能比较。

## 创建并推送一个正式 tag

先确认发行说明和许可待办已经完成，候选提交的检查通过，再检查版本名是否已被占用：

```sh
git ls-remote origin "refs/tags/$release_tag" "refs/tags/$release_tag^{}"
git show --no-patch "$release_commit"
```

如该远端 tag 已存在，核对已有发行记录并选择新的版本，不能覆盖。创建 annotated tag，明确指定已验证 SHA，精确推送这一个 tag：

```sh
git tag -a "$release_tag" "$release_commit" \
  -m "$release_module $release_version"
git push origin "refs/tags/$release_tag:refs/tags/$release_tag"
git ls-remote origin "refs/tags/$release_tag" "refs/tags/$release_tag^{}"
```

第二次查询中 `^{}` 的解引用 SHA 必须等于 `release_commit`。不要使用 `git push --tags`，避免一次发布其他模块或混入 `upstream/*` 来源 tag。来源 tag 单独管理，不作为 Go 模块版本。一个提交可以有几个模块 tag，但每个版本仍需分别核实、推送和记录。

## 从仓库外验证消费者

正式 tag 公开后，在工作区之外创建临时 Go 模块，从公共 proxy 下载这一版本。以下只安装和编译单个 CRC 消费者，不运行依赖库自己的测试；库的原生测试结果来自前面的精确提交验证和 CI。

```sh
consumer_dir=$(mktemp -d "${TMPDIR:-/tmp}/otterio-kits-consumer.XXXXXX")
(
  cd "$consumer_dir"
  export GOWORK=off GOTOOLCHAIN=local GOPROXY=https://proxy.golang.org
  go mod init example.com/otterio-kits-consumer
  go get github.com/soulteary/otterio-kits/crc64nvme@v1.1.2
  cat > main.go <<'EOF'
package main

import (
    "fmt"
    "github.com/soulteary/otterio-kits/crc64nvme"
)

func main() {
    fmt.Printf("%016x\n", crc64nvme.Checksum([]byte("otterIO")))
}
EOF
  go build ./...
  go list -m github.com/soulteary/otterio-kits/crc64nvme
  go mod download -json github.com/soulteary/otterio-kits/crc64nvme@v1.1.2
)
```

使用 Go 1.27.2 或更高工具链；`GOTOOLCHAIN=local` 让最低版本问题直接显现。核对 `go list -m` 的路径与版本、下载输出的来源信息，以及 `Dir`/`Zip` 中该模块的 `LICENSE*` 和 `NOTICE`。公共 proxy 的解析成功也会使版本进入模块索引；如果尚未同步，检查远端 tag、路径和完整 SHA，等待或重试，不要移动 tag。

其他五个模块可按对应候选版本安装；以下仅列出独立命令，不要求消费者同时依赖六库：

```sh
go get github.com/soulteary/otterio-kits/highwayhash@v1.0.5
go get github.com/soulteary/otterio-kits/sha256-simd@v1.0.2
go get github.com/soulteary/otterio-kits/simdjson-go@v0.4.6
go get github.com/soulteary/otterio-kits/sio@v0.5.2
go get github.com/soulteary/otterio-kits/md5-simd@v1.1.3
```

各模块发行时为外部消费者编写使用对应 package/API 的编译示例，不能把 CRC 的示例当作其他五库已经验证的证据。JSON 的编译成功不等于 SIMD 解析已在当前 CPU 上运行。

已有一次发布路径验证记录：2026-10-08，在仓库外关闭工作区，通过公共 proxy 下载提交 `0284a7beecea3819a4965c781ccffdf3d0bb0ba5` 的六个模块，解析为 `v0.0.0-20261008011013-0284a7beecea`，使用六个空白 import 的消费者编译通过。六份下载包均保留 `go.mod`、`LICENSE`、`NOTICE` 及适用的 BSD/MIT 许可文件，两个辅助模块不在 runtime 模块下载包中。这证明该提交的模块路径、消费者编译和许可文件打包可用，没有运行依赖库测试，也没有验证未来正式 tag；每次发行仍需按本节对实际版本重新检查。

## 发行说明、来源与后续修复

Go 版本由 module path、目录前缀 tag 和 tag 指向的代码确定，GitHub Release 用于说明这一版本。先验证已公开 tag，再创建对应 Release；不要让 Release 命令在缺少 tag 时隐式创建一个未验证的 tag。GitHub 自动提供的源码压缩包是该 Git 提交的仓库快照；Go 下载包则按模块目录划分，两者不应混称。

每个模块的发行说明至少记录：模块路径、版本和完整提交 SHA；上游基线与适配补丁；最低 Go 版本；实际通过的 CI 与硬件/平台范围；行为、API、性能和依赖变化；对应的许可材料。参考 [UPSTREAMS.json](../UPSTREAMS.json) 的不可变初次来源与后续维护记录，不用新发行版本覆盖上游基线。

将已审查的发行说明保存为独立文件，把下面的路径替换为该文件的实际路径，再创建对应 Release：

```sh
release_notes_file=/absolute/path/to/crc64nvme-v1.1.2.md
gh release create "$release_tag" --verify-tag --latest=false \
  --title "$release_module $release_version" \
  --notes-file "$release_notes_file"
```

`--verify-tag` 要求 tag 已在远端存在。`--latest=false` 避免把某个组件的版本显示为整仓统一的 Latest；Go 选择模块版本仍依据该模块自己的 tag。发布一个模块只创建它的 Release，不使用整仓自动生成的变更列表作为该模块的完整发行说明。

六个模块的 `LICENSE`、适用的 `LICENSE.Golang` / `LICENSE.Igneous`、`NOTICE` 和原源码署名随各自发行保留。首发准备需处理 [LICENSES.md 的已记录来源待办](LICENSES.md#尚需进一步追溯的来源)：`sha256-simd` 的 Intel AVX512 和 jocover ARM64 实现尚待追溯精确历史授权链。该待办按 SHA 模块处理，其他模块按各自材料和验证状态决定发行。

公开 tag 不再删除、强制移动或覆盖。发现错误时创建新的 patch 版本；若旧版本不应再被选择，在该模块新的版本中用 `retract` 指令说明原因并发布。旧 tag 与源码继续保留，使已有依赖可复现。`retract` 不会删除已下载版本，也不能替代修复版本。

候选分支在记录 CI 链接、正式 tag 与 Release 后可保留，或由维护者确认不再需要时清理。清理候选分支不改变已发布 tag。

最后在 otterIO / OC 另开依赖迁移 PR：显式引用需要切换 import 路径和版本；SDK 的转递依赖需在独立 `otterio-go` fork 中迁移。只发布 kits tag 不会自动替换产品里的 `github.com/minio/*`。产品的磁盘校验、存量密文和 JSON 数据兼容性应在产品回归中另行验证。

## 官方规则

- [Go 多模块仓库](https://go.dev/doc/modules/managing-source)：子目录模块、tag 前缀和消费者版本。
- [Go 模块版本号](https://go.dev/doc/modules/version-numbers)：稳定性声明与语义版本。
- [Go 发布步骤](https://go.dev/doc/modules/publishing)：公开 tag、proxy 索引与不可变版本。
- [Go 工作区](https://go.dev/ref/mod#workspaces)：避免工作区掩盖独立依赖的问题。
- [Go 最低版本声明](https://go.dev/ref/mod#go-mod-file-go)：`go` 指令的最低工具链要求。
- [Go 模块下载包](https://go.dev/ref/mod#zip-files)：子目录范围、嵌套模块排除等规则。
- [Go retract 指令](https://go.dev/ref/mod#go-mod-file-retract)：保留旧版本同时撤回推荐。
- [GitHub 手动运行工作流](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow)：`workflow_dispatch` 与分支选择。
- [GitHub CLI 创建 Release](https://cli.github.com/manual/gh_release_create)：`--verify-tag`、发行说明文件与 Latest 标记。
