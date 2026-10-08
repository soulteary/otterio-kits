# CI 迁移与原始检查对应关系

当前工作树只保留根 `.github/workflows` 中的可执行工作流。删除的八份子工作流仍可在 `UPSTREAMS.json` 记录的原始导入提交中读取；没有重写、裁剪上游历史。

`python3 scripts/verify-ci-layout.py` 检查六个导入目录及其嵌套工具目录。出现 `.github/workflows` 或误拼的 `.github/workflow` 时失败，即使目录为空也会提示。subtree 更新后先检查恢复的 CI 内容，将有价值的检查迁移到根入口，再移除子工作流。

## 原检查的迁移范围

以下范围分别由五个 CI PR 实现。检查命令按模块运行；Go 从 `go.work` 读取版本，不再保留过期 Go 版本矩阵。

- `highwayhash/go.yml`：三平台测试、noasm、vet、原 golangci-lint 规则；迁入根模块测试、质量和 lint 入口。
- `highwayhash/codeql.yml`：CodeQL 和每周扫描；迁入根安全入口，与 CRC64 使用同一固定版本。
- `sha256-simd/go.yml`：三平台 race、格式、汇编声明 vet、`test-architectures.sh`；迁入根模块测试、完整 vet、格式和扩展平台入口。完整 vet 包含 asmdecl。
- `simdjson-go/go.yml`：三平台测试、短 race、格式/vet、Linux 386；保留 noasm 只有不支持平台桩实现的事实，不把跳过解析器测试当作成功验证。
- `simdjson-go/vulncheck.yml`：govulncheck；改为固定工具版本，逐模块扫描发行模块与两个辅助模块。
- `sio/go.yml`：三平台 race、vet/格式、原 lint 规则、atomic 覆盖率/Codecov、Trivy SARIF；分别迁入测试、质量、lint、安全、覆盖率入口。
- `crc64nvme/go.yml`：三平台测试、noasm、`-cpu=1,4 -short -race`、格式/vet、Linux 386；迁入对应模块任务。
- `crc64nvme/codeql-analysis.yml`：CodeQL 和每周扫描；迁入统一安全入口。

MD5 原来没有 GitHub 工作流。新入口为它补齐逐模块测试、格式、vet、lint 和安全检查；生成器作为 `md5-simd/_gen` 独立任务。`simdjson-go/benchmarks` 同样保留独立模块，基准烟测与长期性能比较分别运行。

## 更新时的检查

```sh
python3 scripts/verify-ci-layout.py
python3 scripts/verify-upstreams.py
bash scripts/check-modules.sh verify
```

原始文件示例：`git show <highwayhash 的 import.commit>:highwayhash/.github/workflows/go.yml`。从 `UPSTREAMS.json` 取实际导入 SHA；后续维护提交删除文件不改变该提交的树对象。
