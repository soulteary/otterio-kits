# CI module selection

The repository retains eight root CI entry points and their existing checks. For PRs and mainline pushes, shared `.github/workflows/changes.yml` runs `scripts/select-ci.py` to create check jobs only for affected modules. The selector uses the Python standard library and adds no external Action.

## Selection rules

- Select six runtime modules independently: highwayhash, sha256-simd, simdjson-go, sio, crc64nvme, and md5-simd.
- A `simdjson-go` change also selects `simdjson-go/benchmarks`, which uses its local parent through `replace ../`. A benchmarks-only change selects only that helper module.
- A `md5-simd/_gen` change also selects the MD5 runtime module to cover consumers of generated code. A runtime-only MD5 change does not rerun the generator.
- Match helper modules by longest directory prefix first. Tests, assembly, dependencies, configuration, and documentation within a module all select that module.
- Changes to root `.github/`, `scripts/`, `go.work`, `go.work.sum`, or `UPSTREAMS.json` select everything. Unclassified paths also conservatively select everything, including new modules, root LICENSE/NOTICE, and code under docs.
- Changes limited to root Markdown files and Markdown under `docs/` skip module checks. Quality still runs repository policy, workflow validation, and original-history checks.

Quality, lint, and govulncheck cover selected runtime and helper modules. Three-platform tests, coverage, CodeQL, and benchmark reports cover selected runtime modules. Trivy runs only when SIO is selected. Generator and benchmark smoke tests use their own helper entry points. Extended checks select affected entries from SHA256's architecture matrix, simdjson Linux/386, and CRC Linux/386. Fuzzing selects existing SIO or simdjson targets. PR benchmarks remain single-iteration smoke tests; manual runs retain same-runner baseline comparisons.

Module source changes now also trigger the relevant extended-platform and benchmark smoke checks. Previously, those PR entry points matched only workflow or shared-script changes.

## Comparison scope and scheduled checks

PRs compare `merge-base(base.sha, head.sha)..head.sha`, covering all PR commits. Pushes compare event `before..after`, covering every commit in the push. Full `git diff --name-only --no-renames -z` output retains deleted paths and treats cross-directory renames as deletion/addition so both modules are checked. The selector does not use GitHub's file-list API, avoiding file-count truncation.

Missing comparison commits, all-zero SHAs for new branches, unavailable merge bases, and Git diff failures explicitly log a reason and select everything rather than treating failure as an empty change. Invalid event JSON fails the selection job. Scheduled and manual runs always select everything and do not depend on the previous commit's paths. Daily fuzzing, weekly security scans, and weekly extended-platform checks retain their schedules.

## Use fixed gates as required checks

Each entry point has a fixed aggregate job name: `Quality gate`, `Modules gate`, `Lint gate`, `Security gate`, `Coverage gate`, `Extended platforms gate`, `Fuzz gate`, and `Benchmarks gate`. Configure the gates you want to enforce as required checks in GitHub rulesets or branch protection. Avoid dynamic names such as `module / platform`, `Quality / module`, or `CodeQL / module` as required checks.

Aggregate jobs always run and require successful selection. Checks for nonempty selections must actually succeed; only empty selections permit the corresponding checks to be skipped. Failures, cancellations, unexpected skips, and missing selection outputs fail the gate. Quality gate additionally requires repository policy success, so documentation changes remain subject to common policy checks.

Workflow-level `paths` filters can leave required checks Pending, while job-condition skips report success. This repository avoids PR workflow-level path filtering and always starts the lightweight selector and fixed gates. Empty dynamic matrices skip through job conditions evaluated before matrix expansion. See [workflow syntax and comparison scope](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#git-diff-comparisons) and [job conditions and skipped status](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions).

When adding modules or inter-module dependencies, update the selector inventory, consumer relationships, specialized matrices, and `check-modules.sh` inventory in the same PR. Shared-script changes automatically trigger full validation. `scripts/tests/test_ci_selection.py` uses temporary real Git repositories to cover comparison scope, renames, deletions, large file sets, helper dependencies, failure fallback, and aggregate gates. Quality's repository job runs these regressions.
