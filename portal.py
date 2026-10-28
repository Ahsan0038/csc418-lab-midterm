"""Assignment portal: Python standard library only."""
import json
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED_FIELDS = ("name", "registration_number", "assignment_title", "submission_url")

def validate_submission(data):
    if not isinstance(data, dict):
        return "A JSON object is required."
    for field in REQUIRED_FIELDS:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return field.replace("_", " ").capitalize() + " is required."
    try:
        url = data.get("submission_url", "").strip()
        parts = urlsplit(url)
        valid = (parts.scheme in ("http", "https") and parts.hostname
                 and not any(c.isspace() for c in url)
                 and not parts.username and not parts.password)
        _ = parts.port
    except ValueError:
        valid = False
    if not valid:
        return "Submission URL must be a valid http:// or https:// URL."
    return None


def create_server(db_path="submissions.db", port=5000):
    with closing(sqlite3.connect(str(db_path))) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY, name TEXT, registration_number TEXT,
            assignment_title TEXT, submission_url TEXT)""")

    class Handler(BaseHTTPRequestHandler):
        def send_json(self, status, data):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                body = Path(__file__).with_name("index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/submissions":
                with closing(sqlite3.connect(str(db_path))) as db, db:
                    db.row_factory = sqlite3.Row
                    rows = db.execute("SELECT * FROM submissions ORDER BY id DESC").fetchall()
                self.send_json(200, [dict(row) for row in rows])
            else:
                self.send_json(404, {"error": "Not found"})

        def do_POST(self):
            if self.path != "/api/submissions":
                return self.send_json(404, {"error": "Not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    raise ValueError("Invalid request size")
                data = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                return self.send_json(400, {"error": "Invalid JSON request"})
            error = validate_submission(data)
            if error:
                return self.send_json(400, {"error": error})
            fields = ("name", "registration_number", "assignment_title", "submission_url")
            with closing(sqlite3.connect(str(db_path))) as db, db:
                cursor = db.execute(
                    "INSERT INTO submissions (name, registration_number, assignment_title, submission_url) VALUES (?, ?, ?, ?)",
                    [data.get(key, "").strip() for key in fields])
                submission_id = cursor.lastrowid
            self.send_json(201, {"id": submission_id, "message": "Submission saved."})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    server = create_server()
    print("Portal: http://127.0.0.1:5000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
