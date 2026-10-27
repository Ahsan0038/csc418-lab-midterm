"""Generate JSON from executed tests; optionally deliver it over HTTP."""
import argparse
import json
import os
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


class ReportResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"name": test.id(), "result": "passed", "failure_message": None})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"name": test.id(), "result": "failed",
                             "failure_message": self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"name": test.id(), "result": "failed",
                             "failure_message": self._exc_info_to_string(err, test)})


def git_value(*args):
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "local"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="POST the report to the receiver")
    parser.add_argument("--receiver", default="http://127.0.0.1:8765/report")
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parent)
    suite = unittest.defaultTestLoader.discover(".", pattern="test_portal.py")
    result = unittest.TextTestRunner(verbosity=2, resultclass=ReportResult).run(suite)
    failed = len(result.failures) + len(result.errors)
    report = {
        "repository": os.getenv("GITHUB_REPOSITORY", "local/assignment-portal"),
        "branch": os.getenv("GITHUB_REF_NAME") or git_value("branch", "--show-current"),
        "commit_sha": os.getenv("GITHUB_SHA") or git_value("rev-parse", "HEAD"),
        "pipeline_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "1"),
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": result.records,
        "total": result.testsRun,
        "passed": len([r for r in result.records if r["result"] == "passed"]),
        "failed": failed,
        "overall_status": "passed" if result.wasSuccessful() and result.testsRun else "failed"
    }
    payload = json.dumps(report, indent=2).encode()
    Path("ci-report.json").write_bytes(payload)
    print(f"Report: {report['overall_status']} | {report['passed']} passed | {failed} failed", flush=True)
    delivered = not args.send
    if args.send:
        # This runs even when assertions fail. Test failure is returned AFTER delivery.
        for attempt in range(3):
            try:
                request = Request(args.receiver, data=payload,
                                  headers={"Content-Type": "application/json"}, method="POST")
                with urlopen(request, timeout=10) as response:
                    if response.status != 200:
                        raise RuntimeError("Receiver did not acknowledge the report")
                    print(response.read().decode(), flush=True)
                delivered = True
                break
            except Exception as error:
                print(f"Delivery attempt {attempt + 1} failed: {error}", file=sys.stderr)
                if attempt < 2:
                    time.sleep(1)
    return 0 if report["overall_status"] == "passed" and delivered else 1


if __name__ == "__main__":
    sys.exit(main())
