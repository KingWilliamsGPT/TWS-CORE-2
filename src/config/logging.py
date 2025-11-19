# src/config/logging.py
import logging
import html
from django.conf import settings
from django.core.mail import mail_admins
from django.utils.log import AdminEmailHandler
from src.common.clients import zeptomail


class CustomAdminEmailHandler(AdminEmailHandler):
    """
    A custom version of Django's AdminEmailHandler.
    Allows customizing subject, recipients, or formatting.
    """

    def emit(self, record):
        try:
            # Get the original message
            if record.levelno >= logging.ERROR:
                message = self.format(record)
                _ = (
                    html.escape
                )  # for record.module actually coz of stuf like <ipython-input-3-e1...>

                # Customize subject line
                subject = f"[{settings.SITE_NAME} ERROR] {record.levelname} in {record.module}"

                # Optionally, override recipients (instead of settings.ADMINS)
                recipients = settings.DEVELOPER_EMAILS

                # Send email
                zeptomail._send(
                    to=recipients,
                    subject=subject,
                    html_body=f"""
                    An error occurred in the application {settings.SITE_NAME} APP:<br><br>
                    
                    <strong>Level:</strong> {_(record.levelname)}<br>
                    <strong>Module:</strong> {_(record.module)}<br>
                    <strong>Message:</strong><br>
                    <pre>{_(message)}</pre>
                    <br><br>
                    <small>This is an automated message. Please do not reply.</small>
                    <small> You are seeing this because you are listed in DEVELOPER_EMAILS in settings.</small>
                    """,
                )
        except Exception:
            self.handleError(record)
