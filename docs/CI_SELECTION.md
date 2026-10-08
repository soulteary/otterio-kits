# 按模块选择 CI

仓库继续保留八个根 CI 入口及原有检查步骤。PR 和主线推送由共享
`.github/workflows/changes.yml` 运行 `scripts/select-ci.py`，只为受影响模块
创建检查任务。选择器使用 Python 标准库，不引入新的外部 Action。

## 选择规则

- 六个运行时模块独立选择：highwayhash、sha256-simd、simdjson-go、sio、crc64nvme、md5-simd。
- `simdjson-go` 修改同时选择 `simdjson-go/benchmarks`，因为 benchmark 模块通过
  `replace ../` 使用本地父模块。只修改 benchmarks 时仅检查这个辅助模块。
- `md5-simd/_gen` 修改同时选择 MD5 主模块，以覆盖生成代码的消费者。
  只修改 MD5 主模块时不重新运行生成器。
- 辅助模块优先按最长目录前缀匹配。模块内的测试、汇编、依赖、配置、说明文件
  都选择所属模块。
- 根 `.github/`、`scripts/`、`go.work`、`go.work.sum`、`UPSTREAMS.json` 修改运行全量。
  其他未分类路径也保守运行全量，包括新增模块、根 LICENSE/NOTICE、文档目录中的代码。
- 仅根 Markdown 文件及 `docs/` 下 Markdown 文件修改时，跳过模块检查，仍执行
  Quality 的仓库策略、工作流校验及原始历史检查。

Quality、lint、govulncheck 覆盖选中的运行时及辅助模块；三平台测试、覆盖率、
CodeQL、基准报告覆盖选中的运行时模块；Trivy 只在 SIO 被选中时运行。
生成器及 benchmark smoke 各自运行辅助入口。扩展平台只运行 SHA256 全平台、
simdjson Linux/386、CRC Linux/386 中受影响的入口；fuzz 只选择 SIO 或 simdjson
已有的目标。基准 PR 仍使用一次迭代烟测，手动运行保留同机基线比较。

模块源码修改现在也会触发相应扩展平台和基准烟测；此前这两个 PR 入口只匹配
工作流或公共脚本修改。

## 比较范围与定期检查

PR 比较 `merge-base(base.sha, head.sha)..head.sha`，包含该 PR 的全部提交；
push 比较事件中的 `before..after`，包含一次推送的全部提交。
完整 `git diff --name-only --no-renames -z` 保留删除路径，并把跨目录重命名
视为删除和新增，检查两端模块。不通过 GitHub 文件列表 API，避免文件数量截断。

比较提交缺失、新分支的全零 SHA、无法取得 merge-base 或 Git 比较失败时，
明确记录原因并运行全量，不把失败误判为空修改。无效事件 JSON 则使选择任务失败。
定时与手动运行始终全量，不依赖上一次提交的路径。每日 fuzz、每周安全扫描和
每周扩展平台检查保留当前周期。

## 必需检查应使用固定 gate

每个入口都有固定名称的汇总任务：`Quality gate`、`Modules gate`、`Lint gate`、
`Security gate`、`Coverage gate`、`Extended platforms gate`、`Fuzz gate`、`Benchmarks gate`。
将需要强制的这些固定名称设置为 GitHub ruleset 或分支保护的 required checks。
不要把动态出现的 `模块 / 平台`、`Quality / 模块` 或 `CodeQL / 模块` 名称设置为必需检查。

汇总任务始终运行，并要求选择任务成功。非空选择对应的检查必须实际成功；
只有空选择允许对应检查 skipped。检查失败、取消、意外跳过、缺失选择输出都使
gate 失败。Quality gate 还要求仓库策略任务成功，因此文档修改仍受到统一策略约束。

GitHub 的工作流级 `paths` 过滤可能让必需检查一直 Pending；job 级条件跳过则报告
成功。本仓库不使用 PR 工作流级路径过滤，改为始终启动轻量选择器和固定汇总任务。
动态矩阵为空时，通过在矩阵展开前求值的 job 条件跳过检查。
官方说明：[工作流语法及比较范围](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#git-diff-comparisons)、
[任务条件及跳过状态](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions)。

新增模块或模块间依赖时，同一个 PR 应更新选择器的模块清单、消费者关系、
专项矩阵与 `check-modules.sh` 的 inventory；公共脚本修改会自动运行全量验证。
`scripts/tests/test_ci_selection.py` 用临时真实 Git 仓库验证比较范围、重命名、
删除、大量文件、辅助依赖、失败回退及汇总门禁。Quality 的仓库任务执行这些回归。
