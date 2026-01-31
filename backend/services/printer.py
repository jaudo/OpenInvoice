"""Thermal printer service using ESC/POS protocol."""

import base64
from io import BytesIO
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from escpos.printer import Usb
    from escpos.exceptions import USBNotFoundError
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False
    USBNotFoundError = Exception

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class PrinterStatus:
    """Printer connection status."""
    connected: bool
    printer_name: str = ""
    error_message: str = ""


class PrinterNotConnectedError(Exception):
    """Raised when printer is not connected."""
    pass


class ThermalPrinter:
    """
    Thermal printer service for 58mm receipt printers.

    Supports ESC/POS compatible printers like Bisofice.
    """

    # Common USB Vendor/Product IDs for thermal printers
    KNOWN_PRINTERS = [
        (0x0416, 0x5011),  # Bisofice / Generic
        (0x04B8, 0x0E15),  # Epson TM-T20II
        (0x0519, 0x0001),  # Star TSP100
        (0x0DD4, 0x0200),  # Custom printers
    ]

    # Receipt formatting
    LINE_WIDTH = 32  # Characters for 58mm paper

    def __init__(self, vendor_id: int = None, product_id: int = None):
        """
        Initialize printer connection.

        Args:
            vendor_id: USB vendor ID (auto-detect if not specified)
            product_id: USB product ID (auto-detect if not specified)
        """
        self.printer = None
        self.vendor_id = vendor_id
        self.product_id = product_id

        if ESCPOS_AVAILABLE:
            self._connect()

    def _connect(self) -> bool:
        """Attempt to connect to printer."""
        if not ESCPOS_AVAILABLE:
            return False

        # Try specified IDs first
        if self.vendor_id and self.product_id:
            try:
                self.printer = Usb(self.vendor_id, self.product_id)
                return True
            except USBNotFoundError:
                pass

        # Auto-detect from known printers
        for vid, pid in self.KNOWN_PRINTERS:
            try:
                self.printer = Usb(vid, pid)
                self.vendor_id = vid
                self.product_id = pid
                return True
            except USBNotFoundError:
                continue

        return False

    def get_status(self) -> PrinterStatus:
        """Get current printer status."""
        if not ESCPOS_AVAILABLE:
            return PrinterStatus(
                connected=False,
                error_message="ESC/POS library not installed"
            )

        if self.printer:
            return PrinterStatus(
                connected=True,
                printer_name=f"USB:{self.vendor_id:04X}:{self.product_id:04X}"
            )

        return PrinterStatus(
            connected=False,
            error_message="No printer found"
        )

    def is_connected(self) -> bool:
        """Check if printer is connected."""
        return self.printer is not None

    def reconnect(self) -> bool:
        """Attempt to reconnect to printer."""
        self.printer = None
        return self._connect()

    def print_receipt(
        self,
        store_name: str,
        invoice_number: str,
        items: list[dict],
        subtotal: float,
        vat_amount: float,
        total: float,
        payment_method: str,
        qr_base64: str,
        currency_symbol: str = "€",
        seller_id: str = "",
        timestamp: str = None
    ) -> bool:
        """
        Print a formatted receipt.

        Args:
            store_name: Name of the store
            invoice_number: Invoice number
            items: List of invoice items
            subtotal: Subtotal before VAT
            vat_amount: Total VAT amount
            total: Grand total
            payment_method: Payment method used
            qr_base64: QR code image as base64 PNG
            currency_symbol: Currency symbol to use
            seller_id: Seller ID for the receipt
            timestamp: Invoice timestamp

        Returns:
            True if print successful
        """
        if not self.printer:
            raise PrinterNotConnectedError("Printer not connected")

        timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            p = self.printer

            # Header
            p.set(align='center', text_type='B')
            p.text(f"{store_name}\n")
            p.set(align='center', text_type='NORMAL')
            p.text("=" * self.LINE_WIDTH + "\n")

            # Invoice info
            p.set(align='left')
            p.text(f"Invoice: {invoice_number}\n")
            p.text(f"Date: {timestamp}\n")
            if seller_id:
                p.text(f"Seller: {seller_id}\n")
            p.text("-" * self.LINE_WIDTH + "\n")

            # Items
            for item in items:
                name = item.get('product_name', item.get('name', 'Item'))
                qty = item.get('quantity', 1)
                price = item.get('unit_price', 0)
                line_total = item.get('line_total', qty * price)

                # Truncate name if too long
                max_name_len = self.LINE_WIDTH - 15
                if len(name) > max_name_len:
                    name = name[:max_name_len-2] + ".."

                # Format: Name          Qty x Price
                #                          Total
                p.text(f"{name}\n")
                p.text(f"  {qty} x {currency_symbol}{price:.2f}")
                total_str = f"{currency_symbol}{line_total:.2f}"
                padding = self.LINE_WIDTH - 4 - len(f"{qty} x {currency_symbol}{price:.2f}") - len(total_str)
                p.text(" " * max(1, padding) + total_str + "\n")

            p.text("-" * self.LINE_WIDTH + "\n")

            # Totals
            p.set(align='right')
            p.text(f"Subtotal: {currency_symbol}{subtotal:.2f}\n")
            p.text(f"VAT: {currency_symbol}{vat_amount:.2f}\n")
            p.set(text_type='B')
            p.text(f"TOTAL: {currency_symbol}{total:.2f}\n")
            p.set(text_type='NORMAL')

            p.text("-" * self.LINE_WIDTH + "\n")

            # Payment method
            p.set(align='center')
            p.text(f"Paid by: {payment_method.upper()}\n")

            # QR Code
            if qr_base64 and PIL_AVAILABLE:
                p.text("\n")
                try:
                    qr_bytes = base64.b64decode(qr_base64)
                    qr_image = Image.open(BytesIO(qr_bytes))
                    p.image(qr_image)
                except Exception:
                    p.text("[QR Code]\n")
            p.text("\n")

            # Footer
            p.text("Thank you for your purchase!\n")
            p.text("Verify receipt at:\n")
            p.text("openinvoice.app/verify\n")
            p.text("\n\n\n")

            # Cut paper
            p.cut()

            return True

        except Exception as e:
            raise PrinterNotConnectedError(f"Print failed: {str(e)}")

    def print_test_page(self) -> bool:
        """Print a test page to verify printer connection."""
        if not self.printer:
            raise PrinterNotConnectedError("Printer not connected")

        try:
            p = self.printer

            p.set(align='center', text_type='B')
            p.text("PRINTER TEST\n")
            p.set(text_type='NORMAL')
            p.text("=" * self.LINE_WIDTH + "\n")
            p.text("Open Invoice POS\n")
            p.text(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            p.text("-" * self.LINE_WIDTH + "\n")
            p.text("Characters: ABCDEFGHIJKLMNOP\n")
            p.text("Numbers: 0123456789\n")
            p.text("Symbols: !@#$%^&*()+-=\n")
            p.text("=" * self.LINE_WIDTH + "\n")
            p.text("If you can read this,\n")
            p.text("your printer is working!\n")
            p.text("\n\n\n")
            p.cut()

            return True

        except Exception as e:
            raise PrinterNotConnectedError(f"Test print failed: {str(e)}")

    def close(self):
        """Close printer connection."""
        if self.printer:
            try:
                self.printer.close()
            except Exception:
                pass
            self.printer = None
