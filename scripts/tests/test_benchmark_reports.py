"""Preserve benchmark measurements, diagnostics, and failed command status."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "check-reports.sh"


class BenchmarkReportTests(unittest.TestCase):
    def run_report(self, exit_code, tee_exit=0):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "sio").mkdir()
        tools = root / "bin"
        tools.mkdir()
        go = tools / "go"
        go.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "if sys.argv[1] == 'version': print('go version test')\n"
            "elif sys.argv[1] == 'env': print('{}')\n"
            "elif sys.argv[1] == 'test':\n"
            " print('go: downloading example.com/test v1.0.0', file=sys.stderr)\n"
            " print('BenchmarkEncryptReader_64KB 1 123 ns/op 0 B/op 0 allocs/op')\n"
            " sys.exit(int(os.environ['BENCHMARK_TEST_EXIT']))\n"
        )
        go.chmod(0o755)
        git = tools / "git"
        git.write_text("#!/bin/sh\nprintf '%040d\\n' 0\n")
        git.chmod(0o755)
        tee = tools / "tee"
        tee.write_text('#!/bin/sh\n/usr/bin/tee "$@"\nexit "$BENCHMARK_TEE_EXIT"\n')
        tee.chmod(0o755)
        output = root / "output"
        result = subprocess.run(
            ["bash", str(SCRIPT), "benchmark", "sio", str(output), str(root)],
            env={**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"],
                 "BENCHMARK_TEST_EXIT": str(exit_code), "BENCHMARK_TEE_EXIT": str(tee_exit)},
            capture_output=True, text=True,
        )
        return result, output

    def test_download_diagnostics_do_not_split_measurements(self):
        result, output = self.run_report(0)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BenchmarkEncryptReader_64KB", (output / "benchmarks.txt").read_text())
        self.assertNotIn("go:", (output / "benchmarks.txt").read_text())
        self.assertIn("go: downloading", (output / "diagnostics.txt").read_text())
        self.assertIn("go: downloading", result.stderr)

    def test_failed_go_test_is_not_hidden_by_tee(self):
        result, output = self.run_report(17)
        self.assertEqual(result.returncode, 17)
        self.assertIn("go: downloading", (output / "diagnostics.txt").read_text())

    def test_failed_measurement_write_is_not_hidden_by_successful_test(self):
        result, output = self.run_report(0, tee_exit=23)
        self.assertEqual(result.returncode, 23)
        self.assertIn("go: downloading", (output / "diagnostics.txt").read_text())


if __name__ == "__main__":
    unittest.main()
