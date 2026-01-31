"""Email service for sending receipts via SMTP."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailConfig:
    """SMTP email configuration."""
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    from_name: str = "Open Invoice"
    from_email: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> 'EmailConfig':
        """Create config from dictionary."""
        return cls(
            host=data.get('host', ''),
            port=data.get('port', 587),
            username=data.get('username', ''),
            password=data.get('password', ''),
            use_tls=data.get('use_tls', True),
            from_name=data.get('from_name', 'Open Invoice'),
            from_email=data.get('from_email', data.get('username', ''))
        )


@dataclass
class EmailResult:
    """Result of email sending operation."""
    success: bool
    message: str = ""
    error: str = ""


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self, config: EmailConfig = None):
        """
        Initialize email service.

        Args:
            config: SMTP configuration
        """
        self.config = config

    def set_config(self, config: EmailConfig):
        """Update email configuration."""
        self.config = config

    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        if not self.config:
            return False
        return bool(
            self.config.host and
            self.config.username and
            self.config.password
        )

    def send_receipt(
        self,
        to_email: str,
        invoice_number: str,
        store_name: str,
        total: float,
        pdf_bytes: bytes,
        currency_symbol: str = "€"
    ) -> EmailResult:
        """
        Send receipt email with PDF attachment.

        Args:
            to_email: Recipient email address
            invoice_number: Invoice number
            store_name: Store name for email
            total: Invoice total
            pdf_bytes: PDF file as bytes
            currency_symbol: Currency symbol

        Returns:
            EmailResult with success status
        """
        if not self.is_configured():
            return EmailResult(
                success=False,
                error="Email not configured"
            )

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = f"Your Receipt from {store_name} - {invoice_number}"

            # HTML body
            html_body = self._generate_email_body(
                store_name=store_name,
                invoice_number=invoice_number,
                total=total,
                currency_symbol=currency_symbol
            )
            msg.attach(MIMEText(html_body, 'html'))

            # PDF attachment
            pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=f'receipt_{invoice_number}.pdf'
            )
            msg.attach(pdf_attachment)

            # Send email
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.username, self.config.password)
                server.send_message(msg)

            return EmailResult(
                success=True,
                message=f"Receipt sent to {to_email}"
            )

        except smtplib.SMTPAuthenticationError:
            return EmailResult(
                success=False,
                error="SMTP authentication failed. Check username and password."
            )
        except smtplib.SMTPConnectError:
            return EmailResult(
                success=False,
                error=f"Could not connect to SMTP server {self.config.host}"
            )
        except Exception as e:
            return EmailResult(
                success=False,
                error=str(e)
            )

    def _generate_email_body(
        self,
        store_name: str,
        invoice_number: str,
        total: float,
        currency_symbol: str
    ) -> str:
        """Generate HTML email body."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #4CAF50;
                    padding-bottom: 20px;
                    margin-bottom: 20px;
                }}
                .store-name {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #4CAF50;
                }}
                .invoice-info {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .total {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #4CAF50;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="store-name">{store_name}</div>
                <p>Thank you for your purchase!</p>
            </div>

            <div class="invoice-info">
                <p><strong>Invoice Number:</strong> {invoice_number}</p>
                <p class="total"><strong>Total:</strong> {currency_symbol}{total:.2f}</p>
            </div>

            <p>Your receipt is attached to this email as a PDF file.</p>

            <p>You can verify the authenticity of this receipt by scanning the QR code
            on the attached PDF or by visiting our verification page.</p>

            <div class="footer">
                <p>This is an automated email from Open Invoice POS.</p>
                <p>Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

    def test_connection(self) -> EmailResult:
        """
        Test SMTP connection without sending email.

        Returns:
            EmailResult with connection status
        """
        if not self.is_configured():
            return EmailResult(
                success=False,
                error="Email not configured"
            )

        try:
            with smtplib.SMTP(self.config.host, self.config.port, timeout=10) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.username, self.config.password)
                server.noop()

            return EmailResult(
                success=True,
                message="Connection successful"
            )

        except smtplib.SMTPAuthenticationError:
            return EmailResult(
                success=False,
                error="Authentication failed"
            )
        except smtplib.SMTPConnectError:
            return EmailResult(
                success=False,
                error="Could not connect to server"
            )
        except Exception as e:
            return EmailResult(
                success=False,
                error=str(e)
            )
