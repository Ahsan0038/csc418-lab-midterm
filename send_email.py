"""Optional bonus: send real report using SMTP STARTTLS and CI secrets."""
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

raw = Path("ci-report.json").read_bytes()
report = json.loads(raw)
message = EmailMessage()
message["From"] = os.environ["SMTP_USER"]
message["To"] = os.environ["REPORT_TO"]
message["Subject"] = f"Portal CI: {report['overall_status']} - {report['commit_sha'][:12]}"
message.set_content(json.dumps(report, indent=2))
message.add_attachment(raw, maintype="application", subtype="json", filename="test-report.json")
with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT") or "587"), timeout=30) as smtp:
    smtp.starttls(context=ssl.create_default_context())
    smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    smtp.send_message(message)
print("Report email sent.")
