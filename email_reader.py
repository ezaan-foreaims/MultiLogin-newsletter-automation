# email_reader.py
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
from config import EMAIL_MAIL, APP_PASSWORD, IMAP_SERVER, IMAP_PORT


def _decode_header_value(value: Optional[str]) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, encoding in parts:
        if isinstance(text, bytes):
            decoded += text.decode(encoding or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded


def read_emails(limit: int = 10) -> List[Dict[str, str]]:
    emails = []

    print(f"📬 Connecting to Gmail IMAP server {IMAP_SERVER}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_MAIL, APP_PASSWORD)
    mail.select("inbox")

    status, data = mail.search(None, "ALL")
    if status != "OK":
        print("❌ No messages found.")
        return emails

    email_ids = data[0].split()
    print(f"✅ Found {len(email_ids)} emails. Fetching latest {limit}...\n")

    for num in email_ids[-limit:]:
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue

        msg = email.message_from_bytes(msg_data[0][1])

        from_ = _decode_header_value(msg.get("From"))
        subject = _decode_header_value(msg.get("Subject"))

        # Extract plain text body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                    try:
                        body = part.get_payload(decode=True).decode(errors="ignore")
                    except Exception:
                        pass
                    break
        else:
            try:
                body = msg.get_payload(decode=True).decode(errors="ignore")
            except Exception:
                body = ""

        emails.append({
            "from": from_,
            "subject": subject,
            "body": body.strip(),
        })

    mail.logout()
    return emails

