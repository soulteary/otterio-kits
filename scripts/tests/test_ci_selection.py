"""Exercise selection on real Git histories and stable gate failure propagation."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


REPO = Path(__file__).resolve().parents[2]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


selector = load("ci_selector", "select-ci.py")
gate = load("ci_gate", "check-ci-gate.py")


class GitSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "CI selection test")
        self.git("config", "user.email", "ci@example.invalid")
        # Fixture commits must not inherit personal signing/hooks configuration.
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", "/dev/null")
        self.write("highwayhash/seed.go")
        self.write("sio/seed.go")
        self.base = self.commit()

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.repo), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def write(self, name, content="fixture\n"):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "-m", "fixture")
        return self.git("rev-parse", "HEAD")

    def selected(self, event_name, event):
        paths, _ = selector.changed_paths(self.repo, event_name, event)
        return selector.select_modules(paths)[0]

    def push(self, head, before=None):
        return self.selected("push", {"before": before or self.base, "after": head})

    def test_one_module_push(self):
        self.write("crc64nvme/check.go")
        self.assertEqual(self.push(self.commit()), {"crc64nvme"})

    def test_push_includes_every_commit(self):
        self.write("sha256-simd/check.go")
        self.commit()
        self.write("sio/check.go")
        self.assertEqual(self.push(self.commit()), {"sha256-simd", "sio"})

    def test_pr_includes_every_branch_commit(self):
        self.git("switch", "-c", "feature")
        self.write("sha256-simd/check.go")
        self.commit()
        self.write("sio/check.go")
        head = self.commit()
        event = {"pull_request": {"base": {"sha": self.base}, "head": {"sha": head}}}
        self.assertEqual(self.selected("pull_request", event), {"sha256-simd", "sio"})

    def test_pr_merge_base_excludes_unrelated_main_changes(self):
        self.git("switch", "-c", "feature")
        self.write("crc64nvme/check.go")
        head = self.commit()
        self.git("switch", "main")
        self.write("sio/only-on-main.go")
        latest_base = self.commit()
        event = {"pull_request": {"base": {"sha": latest_base}, "head": {"sha": head}}}
        self.assertEqual(self.selected("pull_request", event), {"crc64nvme"})

    def test_cross_module_rename_checks_both_sides(self):
        (self.repo / "highwayhash/seed.go").rename(self.repo / "sio/moved.go")
        self.assertEqual(self.push(self.commit()), {"highwayhash", "sio"})

    def test_deleted_file_selects_original_module(self):
        (self.repo / "highwayhash/seed.go").unlink()
        self.assertEqual(self.push(self.commit()), {"highwayhash"})

    def test_nul_delimiter_preserves_unusual_filenames(self):
        self.write("crc64nvme/spaces and\nnewlines.go")
        self.assertEqual(self.push(self.commit()), {"crc64nvme"})

    def test_complete_diff_has_no_file_limit(self):
        for index in range(3101):
            self.write(f"docs/fixture-{index:04}.md")
        self.write("sio/after-documents.go")
        self.assertEqual(self.push(self.commit()), {"sio"})

    def test_empty_diff_selects_nothing(self):
        self.assertEqual(self.push(self.base), set())

    def test_documentation_only_selects_nothing(self):
        self.write("README.md")
        self.write("docs/maintenance/plan.md")
        self.assertEqual(self.push(self.commit()), set())

    def test_auxiliary_has_longest_prefix_and_directed_dependency(self):
        self.write("simdjson-go/benchmarks/fixture.go")
        self.assertEqual(self.push(self.commit()), {"simdjson-go/benchmarks"})

    def test_parent_parser_checks_local_consumer(self):
        self.write("simdjson-go/fixture.go")
        self.assertEqual(self.push(self.commit()), {"simdjson-go", "simdjson-go/benchmarks"})

    def test_generator_checks_generated_runtime(self):
        self.write("md5-simd/_gen/fixture.go")
        self.assertEqual(self.push(self.commit()), {"md5-simd/_gen", "md5-simd"})

    def test_md5_runtime_does_not_check_generator(self):
        self.write("md5-simd/fixture.go")
        self.assertEqual(self.push(self.commit()), {"md5-simd"})

    def test_shared_configuration_selects_every_module(self):
        for path in ("scripts/check.sh", ".github/workflows/ci.yml", ".github/ci-tools.json",
                     "go.work", "go.work.sum", "UPSTREAMS.json", "LICENSE", "NOTICE"):
            with self.subTest(path=path):
                self.assertEqual(selector.select_modules([path])[0], set(selector.ALL_MODULES))

    def test_unknown_code_and_module_are_conservative(self):
        for path in ("future/go.mod", "docs/future/go.mod", "docs/example.go", "root.go"):
            with self.subTest(path=path):
                self.assertEqual(selector.select_modules([path])[0], set(selector.ALL_MODULES))

    def test_zero_or_missing_push_sha_runs_every_module(self):
        for event in ({"before": "0" * 40, "after": self.base}, {"after": self.base},
                      {"before": self.base, "after": "0" * 40}):
            with self.subTest(event=event):
                self.assertEqual(self.selected("push", event), set(selector.ALL_MODULES))

    def test_missing_object_runs_every_module(self):
        self.assertEqual(self.selected("push", {"before": "1" * 40, "after": self.base}),
                         set(selector.ALL_MODULES))

    def test_missing_merge_base_runs_every_module(self):
        self.git("switch", "--orphan", "unrelated")
        self.write("sio/unrelated.go")
        head = self.commit()
        event = {"pull_request": {"base": {"sha": self.base}, "head": {"sha": head}}}
        self.assertEqual(self.selected("pull_request", event), set(selector.ALL_MODULES))

    def test_non_repository_git_failure_runs_every_module(self):
        paths, reason = selector.changed_paths(self.repo / "absent", "push",
                                              {"before": self.base, "after": self.base})
        self.assertIsNone(paths)
        self.assertIn("Comparison unavailable", reason)

    def test_schedule_dispatch_and_unknown_events_run_every_module(self):
        for event in ("schedule", "workflow_dispatch", "merge_group"):
            with self.subTest(event=event):
                self.assertEqual(self.selected(event, {}), set(selector.ALL_MODULES))

    def test_invalid_event_structure_falls_back(self):
        self.assertEqual(self.selected("pull_request", {"pull_request": None}), set(selector.ALL_MODULES))

    def test_cli_emits_valid_empty_matrices(self):
        self.write("README.md")
        head = self.commit()
        event_path, output_path = self.repo / "event.json", self.repo / "output.txt"
        event_path.write_text(json.dumps({"before": self.base, "after": head}))
        result = subprocess.run([sys.executable, str(REPO / "scripts/select-ci.py"),
                                 "--repo", str(self.repo), "--event", str(event_path),
                                 "--event-name", "push", "--output", str(output_path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        emitted = dict(line.split("=", 1) for line in output_path.read_text().splitlines())
        self.assertEqual(set(emitted), set(selector.matrices(set())))
        self.assertTrue(all(json.loads(value) == [] for value in emitted.values()))

    def test_cli_rejects_malformed_event_without_emitting_selection(self):
        event_path, output_path = self.repo / "event.json", self.repo / "output.txt"
        event_path.write_text("not valid JSON")
        result = subprocess.run([sys.executable, str(REPO / "scripts/select-ci.py"),
                                 "--repo", str(self.repo), "--event", str(event_path),
                                 "--event-name", "push", "--output", str(output_path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(output_path.exists())

    def test_runtime_selection_routes_only_its_specialized_jobs(self):
        output = selector.matrices({"crc64nvme"})
        self.assertEqual(output["quality"], ["crc64nvme"])
        self.assertEqual(output["runtime"], ["crc64nvme"])
        self.assertEqual([entry["module"] for entry in output["extended"]], ["crc64nvme"])
        self.assertEqual(output["auxiliary"], [])
        self.assertEqual(output["fuzz"], [])
        self.assertEqual(output["trivy"], [])

    def test_full_selection_preserves_all_existing_specialized_entries(self):
        output = selector.matrices(set(selector.ALL_MODULES))
        self.assertEqual(len(output["quality"]), 8)
        self.assertEqual(len(output["runtime"]), 6)
        self.assertEqual(len(output["auxiliary"]), 2)
        self.assertEqual(len(output["extended"]), 3)
        self.assertEqual(len(output["fuzz"]), 8)
        self.assertEqual(output["trivy"], ["sio"])


class GateTests(unittest.TestCase):
    def needs(self, selected, result, changes="success"):
        return {"changes": {"result": changes, "outputs": {"runtime": json.dumps(selected)}},
                "modules": {"result": result}, "repository": {"result": "success"}}

    def test_selected_matrix_success_passes(self):
        self.assertEqual(gate.verify(self.needs(["sio"], "success"), [("modules", "runtime")]), [])

    def test_empty_matrix_is_deliberately_skipped(self):
        self.assertEqual(gate.verify(self.needs([], "skipped"), [("modules", "runtime")]), [])

    def test_selected_matrix_must_actually_succeed(self):
        for result in ("failure", "cancelled", "skipped", None):
            with self.subTest(result=result):
                self.assertTrue(gate.verify(self.needs(["sio"], result), [("modules", "runtime")]))

    def test_selection_failure_cannot_pass_as_skipped(self):
        for result in ("failure", "cancelled", "skipped", None):
            with self.subTest(result=result):
                self.assertTrue(gate.verify(self.needs([], "skipped", result), [("modules", "runtime")]))

    def test_missing_or_invalid_output_cannot_pass(self):
        for outputs in ({}, {"runtime": "invalid"}, {"runtime": "null"}, {"runtime": "{}"}):
            with self.subTest(outputs=outputs):
                needs = self.needs([], "skipped")
                needs["changes"]["outputs"] = outputs
                self.assertTrue(gate.verify(needs, [("modules", "runtime")]))

    def test_policy_failure_is_preserved_on_documentation_only_changes(self):
        needs = self.needs([], "skipped")
        needs["repository"]["result"] = "failure"
        self.assertTrue(gate.verify(needs, [("modules", "runtime"), ("repository", "always")]))

    def test_gate_cli_returns_nonzero_on_selected_job_skip(self):
        env = {**os.environ, "CI_NEEDS_JSON": json.dumps(self.needs(["sio"], "skipped"))}
        result = subprocess.run([sys.executable, str(REPO / "scripts/check-ci-gate.py"),
                                 "--job", "modules:runtime"], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected success, received skipped", result.stderr)


class WorkflowSelectionTests(unittest.TestCase):
    def test_workflows_keep_stable_unfiltered_gates_and_guard_empty_matrices(self):
        files = ("quality", "ci", "lint", "security", "coverage", "extended", "fuzz", "benchmarks")
        for filename in files:
            with self.subTest(filename=filename):
                document = yaml.load((REPO / f".github/workflows/{filename}.yml").read_text(), Loader=yaml.BaseLoader)
                self.assertNotIn("paths", document["on"]["pull_request"] or {})
                self.assertEqual(document["jobs"]["changes"]["uses"], "./.github/workflows/changes.yml")
                aggregate = document["jobs"]["gate"]
                self.assertIn("always()", aggregate["if"])
                self.assertIn("changes", aggregate["needs"])
                for job in document["jobs"].values():
                    if "strategy" in job:
                        self.assertEqual(job["needs"], "changes")
                        self.assertIn("!= '[]'", job["if"])

    def test_native_platform_include_cannot_reintroduce_unselected_module(self):
        document = yaml.load((REPO / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
        matrix = document["jobs"]["modules"]["strategy"]["matrix"]
        self.assertIn("fromJSON(needs.changes.outputs.runtime)", matrix["module"])
        self.assertTrue(all("module" not in entry for entry in matrix["include"]))
        coverage = yaml.load((REPO / ".github/workflows/coverage.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertNotIn("include", coverage["jobs"]["coverage"]["strategy"]["matrix"])


if __name__ == "__main__":
    unittest.main()
