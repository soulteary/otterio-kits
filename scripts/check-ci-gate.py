#!/usr/bin/env python3
"""Fail a stable CI gate if selection or any selected job did not succeed."""

# Copyright 2026 otterIO contributors.
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import sys


def verify(needs, expected_jobs):
    errors = []
    changes = needs.get("changes", {})
    if changes.get("result") != "success":
        errors.append("Module selection did not succeed")
    outputs = changes.get("outputs", {})
    for job, selection in expected_jobs:
        if selection == "always":
            expected = "success"
        else:
            try:
                entries = json.loads(outputs[selection])
                if not isinstance(entries, list):
                    raise ValueError("selection must be an array")
            except (KeyError, TypeError, ValueError):
                errors.append(f"Missing or invalid selection for {job}: {selection}")
                continue
            expected = "success" if entries else "skipped"
        actual = needs.get(job, {}).get("result")
        if actual != expected:
            errors.append(f"{job}: expected {expected}, received {actual}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", action="append", required=True, metavar="JOB:SELECTION")
    parser.add_argument("--needs-json", default=os.environ.get("CI_NEEDS_JSON"))
    args = parser.parse_args()
    try:
        needs = json.loads(args.needs_json)
        if not isinstance(needs, dict):
            raise ValueError("needs must be an object")
        jobs = []
        for spec in args.job:
            job, selection = spec.split(":", 1)
            if not job or not selection:
                raise ValueError("expected JOB:SELECTION")
            jobs.append((job, selection))
        errors = verify(needs, jobs)
    except (TypeError, ValueError, AttributeError) as error:
        print(f"CI gate failed: {error}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("CI gate passed: selection and all selected checks succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
