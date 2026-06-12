"""Email Service for sending documents via SMTP."""
from typing import Optional, list


class EmailService:
    """Handle email sending for invoices, quotations, and reports.

    In production, this integrates with an SMTP server or transactional email API.
    Currently logs to console.
    """

    def __init__(self):
        self.enabled = False
        self.smtp_host = ""
        self.smtp_port = 587
        self.smtp_user = ""
        self.smtp_pass = ""
        self.from_address = "noreply@incentivehouse.me"

    async def send_invoice(
        self,
        to_email: str,
        invoice_number: str,
        pdf_bytes: bytes,
        cc: Optional[list[str]] = None,
    ) -> dict:
        """Send an invoice email with PDF attachment."""
        if not self.enabled:
            print(f"[EMAIL] Would send invoice {invoice_number} to {to_email}")
            return {"status": "logged", "to": to_email, "invoice": invoice_number}

        # TODO: Implement real SMTP sending
        return {"status": "sent", "to": to_email, "invoice": invoice_number}

    async def send_quotation(
        self,
        to_email: str,
        quote_number: str,
        pdf_bytes: bytes,
        cc: Optional[list[str]] = None,
    ) -> dict:
        """Send a quotation email with PDF attachment."""
        if not self.enabled:
            print(f"[EMAIL] Would send quotation {quote_number} to {to_email}")
            return {"status": "logged", "to": to_email, "quote": quote_number}
        return {"status": "sent", "to": to_email, "quote": quote_number}

    async def send_pnl_report(
        self,
        to_email: str,
        job_code: str,
        pdf_bytes: bytes,
    ) -> dict:
        """Send a P&L report email."""
        if not self.enabled:
            print(f"[EMAIL] Would send P&L report for {job_code} to {to_email}")
            return {"status": "logged", "to": to_email, "job": job_code}
        return {"status": "sent", "to": to_email, "job": job_code}


email_service = EmailService()
