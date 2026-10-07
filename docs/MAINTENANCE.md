# 日常维护、历史检查和发布

## 维护入口

根 `UPSTREAMS.json` 是六个发行模块的来源清单。新增组件时，同时更新来源清单、`go.work`、检查脚本的显式清单和 CI。脚本核对所有 `go.mod`，防止新模块被遗漏。

六个发行模块可以独立使用；没有用于发行的根 `go.mod`。两个辅助模块保留在 `md5-simd/_gen` 和 `simdjson-go/benchmarks`，不在六模块工作区内。基准工具通过原有的 `replace => ../` 比较当前解析器；发行模块不使用本地 replace。

修改算法前先运行原测试并保存基准；适配产品后另行运行存量数据回归。所有检查都将测试执行与交叉编译分开记录。

```sh
python3 scripts/verify-upstreams.py
bash scripts/check-modules.sh verify
bash scripts/check-modules.sh test
bash scripts/check-modules.sh tools
```

脚本默认使用普通 Go 缓存。如果环境限制写入默认缓存，可以显式指定可写目录：

```sh
GOMODCACHE=/tmp/otterio-kits-modcache GOCACHE=/tmp/otterio-kits-buildcache \
  bash scripts/check-modules.sh test
```

根工作区的联合检查使用明确的模块目录列表，而不是只运行根 `go test ./...`：

```sh
GOWORK="$PWD/go.work" go test ./highwayhash/... ./sha256-simd/... \
  ./simdjson-go/... ./sio/... ./crc64nvme/... ./md5-simd/...
```

## 原始历史怎么查

导入前仓库提交：`0855462506b24f78b77837ca004ee5043696bfc3`。每个非 squash subtree 导入提交和来源 tag 在 `UPSTREAMS.json` 中记录。

```sh
git log --first-parent --oneline main
git log upstream/highwayhash/v1.0.4
git show upstream/highwayhash/v1.0.4:highwayhash.go
python3 scripts/verify-upstreams.py
```

原始提交保留原仓库根目录路径。当前 `highwayhash/highwayhash.go` 的目录位置来自导入合并提交，因此 `git log -- highwayhash/` 不能代替对原 SHA 的查询。原提交的作者、消息、父提交和 SHA 完整保留；维护提交包含路径迁移和许可补充。

`git subtree` 不带 `--squash`，导入的是固定 tag 的全部可达祖先。未合并 PR、其他远端分支和 tag 之后的修改不属于初次导入范围。普通完整 clone 会获得主线可达的原提交；来源 tag 如未被 clone 带入，可单独获取。历史脚本在 tag 缺失时提示，在 tag 指错 SHA 时失败。

历史检查需要完整仓库；浅 clone 不适合验证原始历史。CI 的逐模块构建可用浅 clone，单独的历史验证应使用 `fetch-depth: 0`。

## 接收一个模块的整体上游更新

下面以 highwayhash 为例，目标版本和 SHA 由维护者核对后填写；不要直接跟随浮动分支发布。

```sh
git remote add upstream-highwayhash https://github.com/minio/highwayhash.git
# remote 已存在时跳过上一行。
git fetch --no-tags upstream-highwayhash \
  refs/tags/v1.0.4:refs/tags/upstream/highwayhash/v1.0.4
```

上述 fetch 演示重建原始来源引用。其他 remote 的 URL 可从清单恢复。接收更新时，将 fetch 的两个 `v1.0.4` 换成核实的新上游 tag，获取到该模块自己的 `upstream/<模块>/<版本>` 命名空间，核对原提交和差异，再运行：

```sh
git subtree merge --prefix=highwayhash <核实后的上游提交SHA>
```

这会保留新上游历史。解决模块路径、README、NOTICE 等维护差异的冲突后，确认本仓库模块身份没有被恢复为上游路径。

`UPSTREAMS.json` 中现有 `upstream` 和 `import` 是不可变的初次导入记录，不能用后续合并提交覆盖。后续合并子树包含本仓库维护改动，不会等于纯上游原树；原树一致性检查始终针对初次导入提交。将新上游 tag/SHA、原树、历史引用、merge SHA 和维护差异追加到该模块的 `updates`，再运行模块与相关产品检查。未来更新的检查应验证新 SHA 对 merge/HEAD 的祖先关系，并审查与新原树的维护差异，不要求该合并子树与原树相等。

## 选择性移植修复

`cherry-pick` 会在当前历史中重放更改，通常生成新 SHA；它不能把一段完整上游历史原样搬入模块目录。根路径的上游提交也不能直接盲目 cherry-pick 到子目录。

已 fetch 的普通非合并修复可以先生成补丁，再按目录应用：

```sh
git format-patch -1 --stdout <原始修复SHA> > /tmp/highwayhash-fix.patch
git am --directory=highwayhash -3 /tmp/highwayhash-fix.patch
```

先检查补丁范围，尤其是仓库根的 CI、模块路径、生成代码和第三方材料；需要适配的修复应单独审查。合并提交需要选择主线父提交并检查差异，不直接套用以上示例。维护提交说明应包含原 SHA、上游 PR、适配内容，清单中的 `upstream_patches` 同步记录；整体更新时检查是否重复引入。

## 独立发行

发布一个模块时按目录打 tag，例如 `highwayhash/v1.0.5`；这只是格式示例，版本号需按实际发行计划决定。不能用根 `v1.0.5` 同时表示六个模块。

发布前检查：该模块在 `GOWORK=off` 下通过、许可证与 NOTICE 随模块保留、适用平台完成运行、发行说明记录上游基线和本仓库改动。新模块路径的首次发行号独立决定，不把原 MinIO tag 称为 OtterIO 已发行版本。主版本升级遵循 Go 模块 `/v2` 等路径规则。

本次仅作本地导入，没有推送、没有创建正式发行 tag。后续批准发布时，先推送主线；主线祖先中的原始提交会一并传输。来源 tag 如需在远端保存，逐个显式推送：

```sh
git push origin main
git push origin refs/tags/upstream/highwayhash/v1.0.4
```

按清单对其他五个来源 tag 执行相同操作。正式发行 tag 另外创建并推送；不使用 `git push --tags` 混合所有来源与发布引用。远端可访问后，在仓库之外通过正式 tag 下载单模块，再次验证 import、Go 版本和许可包。

## 参考

- [Git subtree 官方文档](https://github.com/git/git/blob/master/contrib/subtree/git-subtree.adoc)：非 squash 导入、merge 与历史语义。
- [Git cherry-pick 官方文档](https://git-scm.com/docs/git-cherry-pick)：重放提交及来源记录。
- [Go 多模块仓库官方说明](https://go.dev/doc/modules/managing-source)：子目录模块与目录前缀版本 tag。
