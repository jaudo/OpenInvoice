"""QR code generation for receipts."""

import qrcode
import base64
from io import BytesIO
from datetime import datetime
from typing import Optional


class QRGenerator:
    """Generate QR codes for invoice verification."""

    VERSION = "v1"
    PREFIX = "OPENINVOICE"

    def __init__(self, box_size: int = 4, border: int = 2):
        """
        Initialize QR generator.

        Args:
            box_size: Size of each QR code box in pixels
            border: Border size in boxes
        """
        self.box_size = box_size
        self.border = border

    def generate_qr_data(
        self,
        invoice_number: str,
        total: float,
        hash_value: str,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Generate the QR code data string.

        Format: OPENINVOICE|v1|{invoice_number}|{total}|{hash_first_8}|{timestamp}
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        # Use Unix timestamp for compactness
        if 'T' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            unix_ts = int(dt.timestamp())
        else:
            unix_ts = int(datetime.now().timestamp())

        hash_prefix = hash_value[:8] if hash_value else "00000000"

        return f"{self.PREFIX}|{self.VERSION}|{invoice_number}|{total:.2f}|{hash_prefix}|{unix_ts}"

    def generate_qr_image(self, data: str) -> bytes:
        """
        Generate QR code image as PNG bytes.

        Args:
            data: The data string to encode

        Returns:
            PNG image as bytes
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=self.box_size,
            border=self.border
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def generate_qr_base64(self, data: str) -> str:
        """
        Generate QR code as base64-encoded PNG string.

        Args:
            data: The data string to encode

        Returns:
            Base64 encoded PNG string (without data: prefix)
        """
        image_bytes = self.generate_qr_image(data)
        return base64.b64encode(image_bytes).decode('utf-8')

    def generate_for_invoice(
        self,
        invoice_number: str,
        total: float,
        hash_value: str,
        timestamp: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Generate QR code data and image for an invoice.

        Args:
            invoice_number: The invoice number
            total: Invoice total amount
            hash_value: Full SHA-256 hash of the invoice
            timestamp: Invoice creation timestamp

        Returns:
            Tuple of (qr_data_string, base64_image)
        """
        qr_data = self.generate_qr_data(invoice_number, total, hash_value, timestamp)
        qr_image = self.generate_qr_base64(qr_data)
        return qr_data, qr_image

    @staticmethod
    def parse_qr_data(qr_string: str) -> Optional[dict]:
        """
        Parse QR code data string back into components.

        Args:
            qr_string: The QR data string

        Returns:
            Dictionary with parsed components or None if invalid
        """
        try:
            parts = qr_string.split('|')
            if len(parts) != 6:
                return None

            prefix, version, invoice_number, total, hash_prefix, timestamp = parts

            if prefix != QRGenerator.PREFIX:
                return None

            return {
                'version': version,
                'invoice_number': invoice_number,
                'total': float(total),
                'hash_prefix': hash_prefix,
                'timestamp': int(timestamp)
            }
        except (ValueError, IndexError):
            return None
