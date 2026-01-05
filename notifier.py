# server/notifier.py
import os
from time import time
from dotenv import load_dotenv

load_dotenv()  # loads server/.env

# Twilio
TW_SID = os.getenv("TWILIO_ACCOUNT_SID")
TW_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TW_FROM = os.getenv("TWILIO_FROM_NUMBER")  # must be in E.164 format, e.g. +1XXXXXXXXX
NOTIFY_PHONES = os.getenv("NOTIFY_PHONES", "")  # comma-separated E.164 numbers

# Optional email fallback (kept minimal here)
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
NOTIFY_EMAILS = os.getenv("NOTIFY_EMAILS", "")  # comma-separated emails

# Rate-limiter / cooldown
NOTIFICATION_COOLDOWN_SEC = int(os.getenv("NOTIFICATION_COOLDOWN_SEC", 10 * 60))  # default 10 minutes
_last_notification_time = 0

def _can_send():
    global _last_notification_time
    now = time()
    if now - _last_notification_time >= NOTIFICATION_COOLDOWN_SEC:
        _last_notification_time = now
        return True
    return False

def send_sms_notification(message: str):
    """
    Send SMS to all numbers in NOTIFY_PHONES via Twilio.
    Returns (ok: bool, details)
    """
    if not (TW_SID and TW_TOKEN and TW_FROM and NOTIFY_PHONES):
        return False, "twilio-not-configured"

    if not _can_send():
        return False, "rate-limited"

    # import here so module doesn't break if twilio not installed
    try:
        from twilio.rest import Client
    except Exception as e:
        return False, f"twilio-client-missing:{e}"

    client = Client(TW_SID, TW_TOKEN)
    phones = [p.strip() for p in NOTIFY_PHONES.split(",") if p.strip()]
    results = []
    for number in phones:
        try:
            msg = client.messages.create(body=message, from_=TW_FROM, to=number)
            results.append({"to": number, "status": "sent", "sid": msg.sid})
        except Exception as exc:
            results.append({"to": number, "status": "error", "error": str(exc)})
    return True, results

# Optional: email notification (fallback)
def send_email_notification(subject: str, body: str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and NOTIFY_EMAILS):
        return False, "email-not-configured"
    if not _can_send():
        return False, "rate-limited"
    try:
        import smtplib
        from email.mime.text import MIMEText
        recipients = [e.strip() for e in NOTIFY_EMAILS.split(",") if e.strip()]
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)

        s = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, recipients, msg.as_string())
        s.quit()
        return True, "email-sent"
    except Exception as e:
        return False, f"email-failed:{e}"

def send_notification(count: int = None):
    """
    Compose and send notification. Sends SMS (primary) and optionally email.
    Returns a dict describing results.
    """
    if count:
        body = f"ALERT: Driver had {count} drowsiness events in the configured time window. Please check immediately."
    else:
        body = "ALERT: Driver drowsiness detected. Please check immediately."

    out = {"sms": None, "email": None, "console": body}
    # always print to console
    print("[NOTIFIER] " + body)

    ok_sms, res_sms = send_sms_notification(body)
    out["sms"] = {"ok": ok_sms, "info": res_sms}

    # optionally send email too if configured
    ok_email, res_email = send_email_notification("Driver Drowsiness Alert", body)
    out["email"] = {"ok": ok_email, "info": res_email}

    return out
