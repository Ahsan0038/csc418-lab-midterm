import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from portal import create_server


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.temp.name) / "test.db", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/api/submissions"
        self.valid = {"name": "Test Student", "registration_number": "FA23-BSE-038",
                      "assignment_title": "DevOps Lab", "submission_url": "https://example.com/project"}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def post(self, data):
        request = Request(self.url, data=json.dumps(data).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def submissions(self):
        with urlopen(self.url, timeout=5) as response:
            return json.load(response)

    def test_valid_submission_is_saved_and_listed(self):
        status, result = self.post(self.valid)
        self.assertEqual(status, 201)
        rows = self.submissions()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], result["id"])
        for key, value in self.valid.items():
            self.assertEqual(rows[0][key], value)

    def test_missing_registration_is_rejected(self):
        data = dict(self.valid)
        data.pop("registration_number")
        status, result = self.post(data)
        self.assertEqual(status, 400)
        self.assertIn("Registration number", result["error"])
        self.assertEqual(self.submissions(), [])

    def test_invalid_url_is_rejected_and_not_saved(self):
        status, result = self.post(dict(self.valid, submission_url="not-a-url"))
        self.assertEqual(status, 400)
        self.assertIn("URL", result["error"])
        self.assertEqual(self.submissions(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
