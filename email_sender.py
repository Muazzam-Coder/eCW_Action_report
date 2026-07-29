import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv

load_dotenv()


def send_emails(file_map):
    server = os.getenv("SMTP_SERVER")
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    email_map_raw = os.getenv("EMAIL_MAP", "{}")
    email_map = json.loads(email_map_raw)

    if not all([server, user, password]):
        print("    SMTP config incomplete (SMTP_SERVER, SMTP_USER, SMTP_PASS required)")
        return

    with smtplib.SMTP_SSL(server, port) as smtp:
        smtp.login(user, password)
        for name, filepath in file_map.items():
            recipient = email_map.get(name)
            if not recipient:
                print(f"    No email found for '{name}', skipping")
                continue
            if not os.path.isfile(filepath):
                print(f"    File not found '{filepath}', skipping {name}")
                continue
            try:
                msg = MIMEMultipart()
                msg["From"] = user
                msg["To"] = recipient
                msg["Subject"] = f"Filtered Report - {name}"

                body = MIMEText(f"Please find the filtered report for {name} attached.", "plain")
                msg.attach(body)

                with open(filepath, "rb") as f:
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(f.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(filepath)}",
                    )
                    msg.attach(attachment)

                smtp.send_message(msg)
                print(f"    Email sent to {recipient} for '{name}'")
            except Exception as e:
                print(f"    Failed to send email for '{name}': {e}")
