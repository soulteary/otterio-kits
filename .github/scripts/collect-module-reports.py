import datetime
import io
import json
import os
import pathlib
import re
import subprocess
import zipfile

MODULES = ("highwayhash", "sha256-simd", "simdjson-go", "sio", "crc64nvme", "md5-simd")
FILES = ("go-test-report.md", "go-test-report.json", "coverage.svg", "goreportcard.svg", "goreportcard-report.md")
repository = os.environ["GITHUB_REPOSITORY"]
run_id = os.environ["GITHUB_RUN_ID"]
current_attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
expected_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

def api(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint, "--paginate", "--slurp"], text=True))

artifacts = [item for page in api(f"repos/{repository}/actions/runs/{run_id}/artifacts") for item in page["artifacts"]]
jobs = {}
now = datetime.datetime.now(datetime.timezone.utc)
for module in MODULES:
    candidates = []
    for artifact in artifacts:
        match = re.fullmatch(rf"go-quality-module-{run_id}-(\d+)-{re.escape(module)}", artifact["name"])
        if not match or artifact["expired"]:
            continue
        attempt = int(match[1])
        if attempt > current_attempt or datetime.datetime.fromisoformat(artifact["expires_at"].replace("Z", "+00:00")) <= now:
            continue
        if attempt not in jobs:
            jobs[attempt] = [item for page in api(f"repos/{repository}/actions/runs/{run_id}/attempts/{attempt}/jobs") for item in page["jobs"]]
        if any(job["name"] == f"Report module {module}" and job["status"] == "completed" and job["conclusion"] == "success" for job in jobs[attempt]):
            candidates.append((attempt, artifact))
    if not candidates:
        raise SystemExit(f"No unexpired successful producer artifact for {module}")
    artifact = max(candidates, key=lambda candidate: candidate[0])[1]
    payload = subprocess.check_output(["gh", "api", f"repos/{repository}/actions/artifacts/{artifact['id']}/zip"])
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.read("source-sha.txt").decode().strip() != expected_sha:
            raise SystemExit(f"Producer source SHA does not match for {module}")
        output = pathlib.Path(".github/reports") / module
        if output.is_symlink():
            raise SystemExit("Refusing a symlink report directory")
        output.mkdir(parents=True, exist_ok=True)
        for filename in FILES:
            entry = archive.getinfo(filename)
            if entry.is_dir() or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit("Refusing non-file report evidence")
            target = output / filename
            if target.is_symlink():
                raise SystemExit("Refusing a symlink report target")
            target.write_bytes(archive.read(entry))
    print(f"Collected {module} from successful producer attempt {artifact['name']}")
