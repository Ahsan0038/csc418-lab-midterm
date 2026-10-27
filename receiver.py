"""Keep running on your PC; writes received actual test results automatically."""
import argparse
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def make_receiver(directory, port=8765):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)

    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/report":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000:
                    raise ValueError("Invalid size")
                report = json.loads(self.rfile.read(length))
                required = {"repository", "branch", "commit_sha", "pipeline_run_id",
                            "execution_timestamp", "tests", "total", "passed", "failed", "overall_status"}
                if not isinstance(report, dict) or not required.issubset(report):
                    raise ValueError("Missing report fields")
                if not isinstance(report["tests"], list):
                    raise ValueError("Invalid test list")
                body = json.dumps(report, indent=2).encode()
            except (ValueError, UnicodeDecodeError):
                self.send_error(400, "Invalid test report")
                return
            # An atomic replacement avoids a partially written latest report.
            pending = directory / "test-report.json.tmp"
            pending.write_bytes(body)
            os.replace(pending, directory / "test-report.json")
            history = directory / "report-history"
            history.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            (history / f"{stamp}-{report['overall_status']}.json").write_bytes(body)
            message = f"Saved {directory / 'test-report.json'} ({report['overall_status']})".encode()
            print(message.decode(), flush=True)
            self.send_response(200)
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

    return HTTPServer(("127.0.0.1", port), Receiver)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()
    server = make_receiver(args.output_dir)
    print(f"Receiver: http://127.0.0.1:8765/report -> {Path(args.output_dir).resolve()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
