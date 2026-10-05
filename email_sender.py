import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email import encoders
from dotenv import load_dotenv

load_dotenv()

SIGNATURE_HTML = """
<p>Regards,</p>
<img src="cid:logo" alt="Logo">
<p>
906 W. Medical Center Blvd<br>
Webster, TX 77598<br>
&#9993; Email: Intake10@ombcs.com<br>
&#127760; <a href="https://www.omegarcmsolutions.com">www.omegarcmsolutions.com</a>
</p>
<br>
<small><i>This email and any files transmitted with it may contain PRIVILEGED or
CONFIDENTIAL information and may be read or used only by the intended recipient.
If you are not the intended recipient of the email or any of its attachments,
please be advised that you have received this email in error and that any use,
dissemination, distribution, forwarding, printing or copying of this email or
any attached files is strictly prohibited. If you have received this email in
error, please immediately purge it and all attachments and notify the sender
by reply email or contact the sender at the number listed.</i></small>
"""


def _build_html_body(name):
    return f"""<html><body>
<p>Hello Dr. {name},</p>
<p>Please find the attached report containing all billing issues
assigned to your office. Please review the report and let us know
if you have any questions or require additional information.</p>
<br>
{SIGNATURE_HTML}
</body></html>"""


def send_emails(file_map):
    server = os.getenv("SMTP_SERVER")
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    email_map_raw = os.getenv("EMAIL_MAP", "{}")
    email_map = json.loads(email_map_raw)
    cc_mail = os.getenv("CC_mail", "")
    bcc_mail = os.getenv("BCC_mail", "")
    cc_map_raw = os.getenv("CC_MAP", "{}")
    try:
        cc_map = json.loads(cc_map_raw)
    except Exception:
        cc_map = {}
    cc_list = [a.strip() for a in cc_mail.split(",") if a.strip()]
    bcc_list = [a.strip() for a in bcc_mail.split(",") if a.strip()]

    if not all([server, user, password]):
        print("    SMTP config incomplete (SMTP_SERVER, SMTP_USER, SMTP_PASS required)")
        return

    logo_path = os.path.join(os.getcwd(), "logo.png")

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
                msg = MIMEMultipart("related")
                msg["From"] = user
                msg["To"] = recipient
                # Combine global CCs with provider-specific CCs
                provider_cc_raw = cc_map.get(name, [])
                if isinstance(provider_cc_raw, str):
                    provider_cc = [a.strip() for a in provider_cc_raw.split(",") if a.strip()]
                elif isinstance(provider_cc_raw, list):
                    provider_cc = [str(a).strip() for a in provider_cc_raw if str(a).strip()]
                else:
                    provider_cc = []

                combined_cc = list(dict.fromkeys(cc_list + provider_cc))
                if combined_cc:
                    msg["Cc"] = ", ".join(combined_cc)
                if bcc_list:
                    msg["Bcc"] = ", ".join(bcc_list)
                msg["Subject"] = "Weekly Actions Report"

                alt = MIMEMultipart("alternative")
                html_part = MIMEText(_build_html_body(name), "html")
                alt.attach(html_part)
                msg.attach(alt)

                if os.path.isfile(logo_path):
                    with open(logo_path, "rb") as f:
                        logo = MIMEImage(f.read())
                        logo.add_header("Content-ID", "<logo>")
                        logo.add_header("Content-Disposition", "inline; filename=logo.png")
                        msg.attach(logo)

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
