# 格式、静态检查与 CI 版本

根 `quality.yml` 包含仓库策略任务与八个 Go 模块的独立质量任务。每个模块分别检查全部 Go 文件的格式、完整 `go vet ./...`、模块路径/依赖校验和 `go mod tidy -diff`；后一个检查不改写提交内的 go.mod/go.sum。步骤使用 `always()` 收集同一模块的后续检查结果，便于一次修复多个问题。

格式检查包含生成的 Go 文件和不同 build tag 的文件。模块内的嵌套 go.mod 由对应辅助模块任务负责。MD5 的九个旧格式问题先执行 gofmt，包括生成的 `md5block_amd64.go`。

Linux AMD64 的完整 vet 随后发现旧生成汇编把 BP 当作普通寄存器写入。使用已固定的 Avo v0.6.0 重新生成 `.s` 和 `.go`，避开帧指针；所有指令与标签在固定寄存器重命名后与旧结果一致，算法和栈帧大小未变。新增直接调用标量汇编的测试，覆盖 padding 边界和多块输入，与标准库 MD5 比较。生成指令补充 gofmt，保证生成的 Go 文件满足格式门禁。

完整 vet 还发现两个旧问题：simdjson 的 `AsInteger` 在 uint 值可转为 int64 时执行了无参数 append，遗漏返回值；新增无需 SIMD 的回归测试覆盖 0、42、最大 int64 和溢出拒绝。SHA AVX512 测试的 worker 改用 `Errorf` 并 defer `wg.Done`，避免在子 goroutine 中调用 `Fatalf`。

```sh
python3 scripts/check-quality.py format md5-simd
python3 scripts/check-quality.py vet sha256-simd
python3 scripts/check-quality.py tidy simdjson-go/benchmarks
python3 -m venv /tmp/otterio-ci-python
/tmp/otterio-ci-python/bin/python -m pip install "PyYAML==$(python3 scripts/ci-tool-version.py PyYAML)"
/tmp/otterio-ci-python/bin/python scripts/verify-ci-config.py
/tmp/otterio-ci-python/bin/python -m unittest discover -s scripts/tests -p 'test_*.py'
GOBIN=/tmp/otterio-ci-bin bash scripts/install-ci-tool.sh actionlint
/tmp/otterio-ci-bin/actionlint
```

`.github/ci-tools.json` 是 Actions、govulncheck、golangci-lint、actionlint、benchstat 和 Trivy 的固定版本清单。Go 产品版本仍以 `go.work` 为准。Actions 的 `uses` 需要写字面量版本；`verify-ci-config.py` 校验它们与清单一致，并要求所有 CodeQL 步骤统一版本。工具安装器在模块之外安装固定 Go 工具版本，不向发行模块增加 CI 工具依赖。

Go 工具通过 `.github/actions/setup-ci-tool` 按工具分别缓存可执行文件，避免每个模块重复编译同一工具。缓存键包含固定工具版本、Go 版本、runner 平台与架构、cgo 和指令集设置，以及清单和安装器内容；不使用跨版本的回退键。安装器在复用前读取 Go 构建元数据，核对包路径、版本、编译器和目标设置，失配时重新安装并再次核对。首次缓存未命中仍执行固定版本安装；检查范围、模块选择和必需门禁不受缓存命中影响。

更新工具时同时更新清单和 workflow 字面量，运行 actionlint 和版本检查。actionlint 本身固定版本；使用其内置 shellcheck 集成（Linux runner 自带 shellcheck），检查表达式、任务依赖、矩阵、Actions 参数和 shell 命令。

版本校验使用固定 PyYAML 的 SafeLoader 解析 YAML 节点，检查 workflow 的实际 job/step `uses` 和 composite action 的步骤。支持 `uses :`、引号键、flow mapping、折叠 scalar 和锚点/别名，不依赖文本行形状，也不会把 `run` 或环境变量中的字符串当成 action。Go/CLI 必须使用完整版本，拒绝 `v1`、`v1.2` 等浮动查询；Python 解析器版本也纳入公共清单和检查。
