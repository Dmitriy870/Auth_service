import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPException
from typing import List, Union

from fastapi import HTTPException, status

from config import EmailConfig

email_config = EmailConfig()


def send_email(
    subject: str,
    body: str,
    recipients: Union[List[str], str],
) -> None:
    if isinstance(recipients, str):
        recipients = [recipients]
    elif not isinstance(recipients, list) or not all(isinstance(r, str) for r in recipients):
        raise ValueError("Recipients must be a list of strings or a single string.")

    sender_email = email_config.HOST_USER
    sender_password = email_config.HOST_PASSWORD
    smtp_server = email_config.HOST
    smtp_port = email_config.PORT

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, message.as_string())
    except SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SMTP Authentication failed. Check email credentials.",
        )
    except SMTPConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to the SMTP server.",
        )
    except SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP error occurred: {e}",
        )
