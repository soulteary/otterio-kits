#!/usr/bin/env python3
"""Regression tests for semantic CI version checks, independent of YAML spelling."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest


REPO = Path(__file__).resolve().parents[2]
CHECKER_PATH = REPO / "scripts" / "verify-ci-config.py"


class CIConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        specification = importlib.util.spec_from_file_location("verify_ci_config", CHECKER_PATH)
        cls.checker = importlib.util.module_from_spec(specification)
        sys.modules[specification.name] = cls.checker
        specification.loader.exec_module(cls.checker)
        cls.original_manifest = json.loads((REPO / ".github/ci-tools.json").read_text())

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="otterio-ci-config-test-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.github = self.repo / ".github"
        (self.github / "workflows").mkdir(parents=True)
        self.manifest = copy.deepcopy(self.original_manifest)
        self.manifest["python_tools"] = {"PyYAML": "6.0.3"}
        self.write_manifest()

    def write_manifest(self):
        (self.github / "ci-tools.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def write_yaml(self, source, name="workflows/ci.yml"):
        path = self.github / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
        return path

    def workflow_with_step(self, step):
        # Build a valid step sequence while retaining each fixture's key spelling.
        self.write_yaml("name: Test\non: push\njobs:\n  test:\n    runs-on: ubuntu-24.04\n"
                        "    steps:\n" + textwrap.indent(textwrap.dedent(step).strip(), "      ") + "\n")

    def assert_valid(self, expected_seen=None):
        errors, seen = self.checker.verify(self.repo)
        self.assertEqual(errors, [], "\n".join(errors))
        if expected_seen is not None:
            self.assertEqual(seen, set(expected_seen))

    def assert_invalid(self, diagnostic=None):
        errors, _ = self.checker.verify(self.repo)
        self.assertTrue(errors, "CI configuration incorrectly passed")
        if diagnostic is not None:
            self.assertIn(diagnostic, "\n".join(errors))

    def test_existing_manifest_and_fixed_block_step_pass(self):
        self.workflow_with_step("- uses: actions/checkout@v7.0.1")
        self.assert_valid({"actions/checkout"})

    def test_whitespace_before_colon_does_not_hide_floating_ref(self):
        self.workflow_with_step("- uses : actions/checkout@main")
        self.assert_invalid("actions/checkout")

    def test_flow_mapping_does_not_hide_floating_ref(self):
        self.workflow_with_step("- { uses: actions/checkout@main }")
        self.assert_invalid("actions/checkout")

    def test_flow_workflow_and_fixed_ref_pass(self):
        self.write_yaml('jobs: {test: {runs-on: ubuntu-24.04, steps: [{uses: "actions/checkout@v7.0.1"}]}}\n')
        self.assert_valid({"actions/checkout"})

    def test_quoted_keys_and_values_are_checked(self):
        for step in ('- "uses": "actions/checkout@main"', "- 'uses': 'actions/checkout@main'"):
            with self.subTest(step=step):
                self.workflow_with_step(step)
                self.assert_invalid("actions/checkout")

    def test_explicit_yaml_key_is_checked(self):
        self.workflow_with_step('''
            - ? "uses"
              : actions/checkout@main
        ''')
        self.assert_invalid("actions/checkout")

    def test_folded_scalar_is_checked(self):
        self.workflow_with_step('''
            - uses: >-
                actions/checkout@main
        ''')
        self.assert_invalid("actions/checkout")

    def test_fixed_folded_scalar_passes(self):
        self.workflow_with_step('''
            - uses: >-
                actions/checkout@v7.0.1
        ''')
        self.assert_valid({"actions/checkout"})

    def test_scalar_alias_is_checked_at_real_uses_field(self):
        self.write_yaml('''
            x-action: &action actions/checkout@main
            jobs:
              test:
                runs-on: ubuntu-24.04
                steps:
                  - uses: *action
        ''')
        self.assert_invalid("actions/checkout")

    def test_step_mapping_alias_is_checked(self):
        self.write_yaml('''
            x-step: &action-step {uses: actions/checkout@main}
            jobs:
              test:
                runs-on: ubuntu-24.04
                steps:
                  - *action-step
        ''')
        self.assert_invalid("actions/checkout")

    def test_fixed_aliases_pass(self):
        self.write_yaml('''
            x-action: &action actions/checkout@v7.0.1
            x-step: &action-step {uses: *action}
            jobs:
              test:
                runs-on: ubuntu-24.04
                steps:
                  - *action-step
                  - uses: *action
        ''')
        self.assert_valid({"actions/checkout"})

    def test_reusable_job_floating_ref_is_checked(self):
        self.write_yaml('''
            jobs:
              shared:
                uses : example/shared/.github/workflows/ci.yml@main
        ''')
        self.assert_invalid("example/shared/.github/workflows/ci.yml")

    def test_listed_fixed_reusable_job_passes(self):
        action = "example/shared/.github/workflows/ci.yml"
        self.manifest["actions"][action] = "v1.2.3"
        self.write_manifest()
        self.write_yaml(f"jobs: {{shared: {{uses: {action}@v1.2.3}}}}\n")
        self.assert_valid({action})

    def test_composite_action_floating_ref_is_checked(self):
        self.write_yaml('''
            name: Composite
            runs:
              using: composite
              steps:
                - { uses : actions/checkout@main }
        ''', "actions/example/action.yml")
        self.assert_invalid("actions/checkout")

    def test_composite_action_alias_and_yaml_suffix_are_checked(self):
        self.write_yaml('''
            name: Composite
            x-action: &action actions/checkout@main
            runs:
              using: composite
              steps:
                - uses: *action
        ''', "actions/example/action.yaml")
        self.assert_invalid("actions/checkout")

    def test_fixed_composite_action_passes(self):
        self.write_yaml('''
            name: Composite
            runs:
              using: composite
              steps:
                - uses : actions/checkout@v7.0.1
                - shell: bash
                  run: |
                    echo 'uses: actions/checkout@main'
        ''', "actions/example/action.yml")
        self.assert_valid({"actions/checkout"})

    def test_local_steps_and_local_reusable_job_pass(self):
        self.write_yaml('''
            jobs:
              shared:
                uses: ./.github/workflows/shared.yml
              test:
                runs-on: ubuntu-24.04
                steps:
                  - uses: ./.github/actions/example
        ''')
        self.write_yaml('''
            runs:
              using: composite
              steps:
                - uses: ./another-action
        ''', "actions/example/action.yml")
        self.assert_valid(set())

    def test_run_and_env_text_are_not_actions(self):
        self.write_yaml('''
            env:
              uses: actions/checkout@main
            jobs:
              test:
                runs-on: ubuntu-24.04
                env:
                  uses: actions/setup-go@main
                steps:
                  - name: Text containing uses
                    env:
                      uses: actions/checkout@main
                    run: |
                      uses: actions/checkout@main
                      printf 'uses: actions/setup-go@latest'
        ''')
        self.assert_valid(set())

    def test_unused_anchor_text_is_not_an_action(self):
        self.write_yaml('''
            x-text: &unused {uses: actions/checkout@main}
            jobs:
              test:
                runs-on: ubuntu-24.04
                steps:
                  - run: echo test
        ''')
        self.assert_valid(set())

    def test_malformed_workflow_fails(self):
        self.write_yaml("jobs: [\n")
        self.assert_invalid()

    def test_malformed_composite_action_fails(self):
        self.write_yaml("runs: [\n", "actions/example/action.yml")
        self.assert_invalid()

    def test_non_scalar_uses_is_rejected(self):
        for value in ("[actions/checkout@v7.0.1]", "{action: actions/checkout@v7.0.1}", "null", "42"):
            with self.subTest(value=value):
                self.workflow_with_step(f"- uses: {value}")
                self.assert_invalid()

    def test_floating_action_versions_are_rejected(self):
        for version in ("main", "master", "latest", "v7", "v7.0"):
            with self.subTest(version=version):
                self.workflow_with_step(f"- uses: actions/checkout@{version}")
                self.assert_invalid("actions/checkout")

    def test_unversioned_remote_action_is_rejected(self):
        self.workflow_with_step("- uses: actions/checkout")
        self.assert_invalid("actions/checkout")

    def test_unlisted_fixed_action_is_rejected(self):
        self.workflow_with_step("- uses: example/unlisted@v1.2.3")
        self.assert_invalid("example/unlisted")

    def test_fixed_but_inconsistent_action_version_is_rejected(self):
        self.workflow_with_step("- uses: actions/checkout@v7.0.0")
        self.assert_invalid("actions/checkout")

    def test_full_commit_pin_passes(self):
        self.workflow_with_step("- uses: aquasecurity/trivy-action@" + self.manifest["actions"]["aquasecurity/trivy-action"])
        self.assert_valid({"aquasecurity/trivy-action"})

    def test_short_commit_pin_is_rejected(self):
        action = "example/action"
        self.manifest["actions"][action] = "abcdef123456"
        self.write_manifest()
        self.workflow_with_step(f"- uses: {action}@abcdef123456")
        self.assert_invalid()

    def test_floating_manifest_action_version_is_rejected(self):
        self.manifest["actions"]["actions/checkout"] = "main"
        self.write_manifest()
        self.assert_invalid("actions/checkout")

    def test_codeql_manifest_versions_must_match(self):
        self.manifest["actions"]["github/codeql-action/analyze"] = "v4.38.1"
        self.write_manifest()
        self.assert_invalid("CodeQL")

    def test_floating_go_queries_are_rejected(self):
        for version in ("v1", "v1.2", "v1.2.x", "latest", "main", "master"):
            with self.subTest(version=version):
                self.manifest["go_tools"]["govulncheck"]["version"] = version
                self.write_manifest()
                self.assert_invalid("govulncheck")

    def test_exact_go_semver_and_pseudoversions_pass(self):
        for version in ("v1.2.3", "v1.2.3-rc.1", "v0.0.0-20260929162123-406019bb8b68"):
            with self.subTest(version=version):
                self.manifest["go_tools"]["govulncheck"]["version"] = version
                self.write_manifest()
                self.assert_valid(set())

    def test_floating_cli_versions_are_rejected(self):
        for version in ("latest", "main", "v0", "v0.75"):
            with self.subTest(version=version):
                self.manifest["cli_versions"]["trivy"] = version
                self.write_manifest()
                self.assert_invalid("trivy")

    def test_exact_cli_version_passes(self):
        self.manifest["cli_versions"]["trivy"] = "v0.75.0"
        self.write_manifest()
        self.assert_valid(set())

    def test_pyyaml_exact_version_is_required(self):
        for version in ("latest", "6", "6.0", "~=6.0.3", "6.0.3.*"):
            with self.subTest(version=version):
                self.manifest["python_tools"]["PyYAML"] = version
                self.write_manifest()
                self.assert_invalid("PyYAML")

    def test_fixed_pyyaml_version_passes(self):
        self.manifest["python_tools"]["PyYAML"] = "6.0.3"
        self.write_manifest()
        self.assert_valid(set())


if __name__ == "__main__":
    unittest.main()
