import os
import imaplib
import email
import smtplib
import logging
from email.parser import BytesParser
from email.policy import default
from tnefparse import TNEF
import re
import time

###############################
# ENVIRONMENT VARIABLES
###############################
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

###############################
# LOGGING
###############################
logging.basicConfig(
    filename="/opt/gophish-bridge/bridge.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

################################
# HELPERS
################################

def extract_rid(msg):
    try:
        if msg.is_multipart():
            for part in msg.walk():
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")
                    match = re.search(r"rid=([A-Za-z0-9]+)", body)
                    if match:
                        return match.group(1)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(errors="ignore")
                match = re.search(r"rid=([A-Za-z0-9]+)", body)
                if match:
                    return match.group(1)
    except Exception as e:
        logging.error(f"RID extraction error: {e}")

    return None


def extract_email(header):
    match = re.search(r"<(.+?)>", str(header))
    if match:
        return match.group(1)
    return header


################################
# SEND FUNCTION
################################

def send_to_gophish(msg):
    logging.info("Sending email to GoPhish mailbox")

    try:
        raw = msg.as_string()

        if "?rid=" not in raw:
            logging.warning("RID missing, skipping")
            return

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, SMTP_USER, raw)

        logging.info("Email successfully re-injected")

    except Exception as e:
        logging.error(f"SMTP send error: {e}")


################################
# MAIN PROCESSING
################################

def process_emails():
    logging.info("Connecting to IMAP mailbox")

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select("INBOX")

        status, messages = mail.search(None, "UNSEEN")
        message_ids = messages[0].split()

        logging.info(f"Found {len(message_ids)} unread messages")

        for num in message_ids:
            try:
                status, data = mail.fetch(num, "(RFC822)")
                raw_email = data[0][1]

                msg = email.message_from_bytes(raw_email)

                user = extract_email(msg.get("From", "unknown"))
                rid = extract_rid(msg)

                if rid:
                    logging.info(f"REPORT_EVENT | user={user} | rid={rid}")
                else:
                    logging.warning(f"User reported: {user} | RID NOT FOUND")

                found = False

                for part in msg.walk():
                    content_type = part.get_content_type()
                    filename = part.get_filename()

                    logging.info(f"Checking part: {content_type} / {filename}")

                    # EML attachment
                    if filename and filename.endswith(".eml"):
                        eml_data = part.get_payload(decode=True)
                        original_msg = BytesParser(policy=default).parsebytes(eml_data)

                        send_to_gophish(original_msg)
                        found = True

                    # TNEF
                    elif content_type == "application/ms-tnef":
                        try:
                            tnef = TNEF(part.get_payload(decode=True))

                            for attachment in tnef.attachments:
                                if attachment.name and attachment.name.endswith(".eml"):
                                    original_msg = BytesParser(policy=default).parsebytes(attachment.data)

                                    send_to_gophish(original_msg)
                                    found = True

                        except Exception as e:
                            logging.error(f"TNEF parsing error: {e}")

                    # message/rfc822
                    elif content_type == "message/rfc822":
                        payload = part.get_payload()

                        if isinstance(payload, list):
                            for sub_msg in payload:

                                # --- FIX ADDED HERE ---
                                if sub_msg.get("From"):
                                    sub_msg.replace_header("From", SMTP_USER)

                                send_to_gophish(sub_msg)
                                found = True

                        else:
                            if payload and hasattr(payload, "get"):
                                if payload.get("From"):
                                    payload.replace_header("From", SMTP_USER)

                            send_to_gophish(payload)
                            found = True

                if found:
                    logging.info("Message processed successfully")
                else:
                    logging.warning("No usable email found")

                mail.copy(num, "Processed")
                mail.store(num, '+FLAGS', '\\Deleted')
                mail.expunge()

            except Exception as e:
                logging.error(f"Error processing message: {e}")

        mail.logout()

    except Exception as e:
        logging.error(f"Mailbox connection error: {e}")


################################
# ENTRY POINT
################################

if __name__ == "__main__":
    while True:
        process_emails()
        time.sleep(30)
