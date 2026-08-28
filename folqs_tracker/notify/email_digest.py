"""Send the digest by SMTP.

Plain SMTP rather than the Gmail API on purpose: this runs unattended from cron,
and an interactive OAuth consent screen is exactly what a 7am scheduled job
cannot answer. Use a Google App Password with smtp.gmail.com.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage


def send_email(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    sender: str,
    recipients: str,
    subject: str,
    text: str,
    html: str = "",
    timeout: int = 30,
) -> list[str]:
    """Send the digest. Returns the recipient list actually addressed."""
    to = [addr.strip() for addr in str(recipients).split(",") if addr.strip()]
    if not to:
        raise ValueError("no recipients configured (REPORT_EMAIL_TO)")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(to)
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=timeout) as server:
            if username:
                server.login(username, password)
            server.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=timeout) as server:
            server.starttls()
            if username:
                server.login(username, password)
            server.send_message(message)
    return to
