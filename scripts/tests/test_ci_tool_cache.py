"""Reject stale tool binaries instead of silently weakening the CI tool pin."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import copy
import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ci_tool_cache", REPO / "scripts/check-ci-tool-cache.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ToolCacheTests(unittest.TestCase):
    def setUp(self):
        self.environment = dict(GOVERSION="go1.27.1", GOOS="linux", GOARCH="amd64",
                                CGO_ENABLED="1", GOAMD64="v1", GOARM64="")
        self.package = "example.invalid/tool/cmd/tool"
        self.version = "v1.2.3"
        self.info = {"GoVersion": "go1.27.1", "Path": self.package,
                     "Main": {"Version": self.version},
                     "Settings": [{"Key": key, "Value": value}
                                  for key, value in self.environment.items() if key != "GOVERSION" and value]}

    def accepted(self, info):
        return checker.matches(info, self.package, self.version, self.environment)

    def test_matching_binary_is_reusable(self):
        self.assertTrue(self.accepted(self.info))

    def test_empty_build_setting_omits_value_in_go_json(self):
        self.info["Settings"].append({"Key": "CGO_CFLAGS"})
        self.assertTrue(self.accepted(self.info))

    def test_wrong_tool_version_or_compiler_is_rebuilt(self):
        for field, value in (("Path", "example.invalid/other"), ("GoVersion", "go1.26.0")):
            with self.subTest(field=field):
                info = copy.deepcopy(self.info)
                info[field] = value
                self.assertFalse(self.accepted(info))
        info = copy.deepcopy(self.info)
        info["Main"]["Version"] = "v1.2.2"
        self.assertFalse(self.accepted(info))

    def test_wrong_target_cgo_or_instruction_level_is_rebuilt(self):
        for key, value in (("GOOS", "darwin"), ("GOARCH", "arm64"),
                           ("CGO_ENABLED", "0"), ("GOAMD64", "v3")):
            with self.subTest(key=key):
                info = copy.deepcopy(self.info)
                next(item for item in info["Settings"] if item["Key"] == key)["Value"] = value
                self.assertFalse(self.accepted(info))

    def test_missing_build_info_is_not_reusable(self):
        for info in ({}, {"Path": self.package}, {"Main": {"Version": self.version}}):
            self.assertFalse(self.accepted(info))


if __name__ == "__main__":
    unittest.main()
