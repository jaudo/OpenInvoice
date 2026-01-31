"""PDF receipt generator using ReportLab."""

import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class PDFGenerator:
    """Generate PDF receipts for invoices."""

    # Page sizes
    A4_SIZE = A4
    RECEIPT_SIZE = (80 * mm, 200 * mm)  # 80mm thermal receipt size

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize PDF generator.

        Args:
            output_dir: Directory for saving PDF files (temp dir if not specified)
        """
        self.output_dir = output_dir or Path.cwd() / "temp"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_receipt_pdf(
        self,
        store_name: str,
        invoice_number: str,
        seller_id: str,
        items: list[dict],
        subtotal: float,
        vat_amount: float,
        total: float,
        payment_method: str,
        qr_base64: str,
        currency_symbol: str = "€",
        timestamp: str = None,
        customer_email: str = None
    ) -> bytes:
        """
        Generate a PDF receipt.

        Returns:
            PDF file as bytes
        """
        timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.A4_SIZE,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10
        )

        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )

        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10
        )

        right_style = ParagraphStyle(
            'Right',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        )

        total_style = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=14,
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold'
        )

        elements = []

        # Store header
        elements.append(Paragraph(store_name, title_style))
        elements.append(Paragraph(f"Seller ID: {seller_id}", header_style))
        elements.append(Spacer(1, 10 * mm))

        # Invoice info
        info_data = [
            ["Invoice:", invoice_number],
            ["Date:", timestamp],
            ["Payment:", payment_method.upper()],
        ]
        if customer_email:
            info_data.append(["Email:", customer_email])

        info_table = Table(info_data, colWidths=[30 * mm, 80 * mm])
        info_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10 * mm))

        # Items table
        items_data = [["Product", "Qty", "Price", "Total"]]
        for item in items:
            name = item.get('product_name', item.get('name', 'Item'))
            qty = item.get('quantity', 1)
            price = item.get('unit_price', 0)
            line_total = item.get('line_total', qty * price)

            # Truncate long names
            if len(name) > 30:
                name = name[:28] + ".."

            items_data.append([
                name,
                str(qty),
                f"{currency_symbol}{price:.2f}",
                f"{currency_symbol}{line_total:.2f}"
            ])

        items_table = Table(
            items_data,
            colWidths=[80 * mm, 20 * mm, 30 * mm, 30 * mm]
        )
        items_table.setStyle(TableStyle([
            # Header
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),

            # Alignment
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),

            # Grid
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 5 * mm))

        # Totals
        totals_data = [
            ["Subtotal:", f"{currency_symbol}{subtotal:.2f}"],
            ["VAT:", f"{currency_symbol}{vat_amount:.2f}"],
            ["TOTAL:", f"{currency_symbol}{total:.2f}"],
        ]
        totals_table = Table(totals_data, colWidths=[130 * mm, 30 * mm])
        totals_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
            ('TOPPADDING', (0, 2), (-1, 2), 8),
        ]))
        elements.append(totals_table)
        elements.append(Spacer(1, 15 * mm))

        # QR Code
        if qr_base64:
            try:
                qr_bytes = base64.b64decode(qr_base64)
                qr_image = Image(BytesIO(qr_bytes), width=40 * mm, height=40 * mm)
                qr_table = Table([[qr_image]], colWidths=[170 * mm])
                qr_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ]))
                elements.append(qr_table)
                elements.append(Spacer(1, 5 * mm))
            except Exception:
                pass

        # Footer
        elements.append(Paragraph(
            "Scan QR code to verify receipt authenticity",
            header_style
        ))
        elements.append(Paragraph(
            "Thank you for your purchase!",
            header_style
        ))

        doc.build(elements)

        return buffer.getvalue()

    def save_receipt_pdf(
        self,
        invoice_number: str,
        **kwargs
    ) -> Path:
        """
        Generate and save PDF receipt to file.

        Args:
            invoice_number: Invoice number (used for filename)
            **kwargs: Arguments passed to generate_receipt_pdf

        Returns:
            Path to saved PDF file
        """
        pdf_bytes = self.generate_receipt_pdf(invoice_number=invoice_number, **kwargs)

        filename = f"receipt_{invoice_number.replace('-', '_')}.pdf"
        filepath = self.output_dir / filename

        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)

        return filepath

    def generate_from_invoice(self, invoice: dict, settings: dict = None) -> bytes:
        """
        Generate PDF from invoice dictionary.

        Args:
            invoice: Invoice data dictionary
            settings: Application settings (for currency, store name, etc.)

        Returns:
            PDF file as bytes
        """
        settings = settings or {}

        return self.generate_receipt_pdf(
            store_name=invoice.get('store_name', settings.get('store_name', 'Store')),
            invoice_number=invoice.get('invoice_number'),
            seller_id=invoice.get('seller_id', settings.get('seller_id', '')),
            items=invoice.get('items', []),
            subtotal=invoice.get('subtotal', 0),
            vat_amount=invoice.get('vat_amount', 0),
            total=invoice.get('total', 0),
            payment_method=invoice.get('payment_method', 'cash'),
            qr_base64=invoice.get('qr_image', ''),
            currency_symbol=settings.get('currency_symbol', '€'),
            timestamp=invoice.get('created_at'),
            customer_email=invoice.get('customer_email')
        )
