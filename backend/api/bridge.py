"""API bridge for pywebview - exposes backend functionality to frontend."""

from datetime import datetime
from typing import Any, Optional

from ..database.connection import Database
from ..database.migrations import initialize_database
from ..database.repositories.products import ProductRepository, Product
from ..database.repositories.invoices import InvoiceRepository, Invoice, InvoiceItem
from ..database.repositories.settings import SettingsRepository
from ..database.repositories.audit import AuditRepository
from ..core.hash_chain import HashChain
from ..core.qr_generator import QRGenerator
from ..core.qr_validator import QRValidator
from ..core.keyboard_mapper import KeyboardMapper
from ..services.printer import ThermalPrinter, PrinterNotConnectedError
from ..services.pdf_generator import PDFGenerator
from ..services.email_service import EmailService, EmailConfig
from ..services.csv_importer import CSVImporter
from ..services.reports import ReportsService


class API:
    """
    API class exposed to frontend via pywebview.

    All methods return: {success: bool, data?: any, error?: string}
    """

    def __init__(self):
        """Initialize API with all services."""
        self.db = Database()
        initialize_database(self.db)

        # Repositories
        self.products = ProductRepository(self.db)
        self.invoices = InvoiceRepository(self.db)
        self.settings = SettingsRepository(self.db)
        self.audit = AuditRepository(self.db)

        # Services
        self.qr_generator = QRGenerator()
        self.qr_validator = QRValidator(self.invoices)
        self.printer = ThermalPrinter()
        self.pdf_generator = PDFGenerator()
        self.email_service = EmailService()
        self.csv_importer = CSVImporter(self.products)
        self.reports = ReportsService(self.db)

    def _response(self, success: bool, data: Any = None, error: str = None) -> dict:
        """Create standardized API response."""
        return {'success': success, 'data': data, 'error': error}

    # ============ Products ============

    def products_get_all(self) -> dict:
        """Get all active products."""
        try:
            products = self.products.get_all()
            return self._response(True, [p.to_dict() for p in products])
        except Exception as e:
            return self._response(False, error=str(e))

    def products_search(self, query: str) -> dict:
        """Search products by name or barcode."""
        try:
            products = self.products.search(query)
            return self._response(True, [p.to_dict() for p in products])
        except Exception as e:
            return self._response(False, error=str(e))

    def products_get_by_barcode(self, barcode: str) -> dict:
        """Get product by barcode."""
        try:
            product = self.products.get_by_barcode(barcode)
            if product:
                return self._response(True, product.to_dict())
            return self._response(False, error="Product not found")
        except Exception as e:
            return self._response(False, error=str(e))

    def products_create(self, data: dict) -> dict:
        """Create a new product."""
        try:
            product = Product(
                id=data.get('id') or f"PROD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                name=data['name'],
                description=data.get('description', ''),
                price=float(data['price']),
                vat_rate=float(data.get('vat_rate', 21.0)),
                barcode=data.get('barcode'),
                stock=int(data.get('stock', 0)),
                status=data.get('status', 'active')
            )
            created = self.products.create(product)
            return self._response(True, created.to_dict())
        except Exception as e:
            return self._response(False, error=str(e))

    def products_update(self, data: dict) -> dict:
        """Update an existing product."""
        try:
            product = Product(
                id=data['id'],
                name=data['name'],
                description=data.get('description', ''),
                price=float(data['price']),
                vat_rate=float(data.get('vat_rate', 21.0)),
                barcode=data.get('barcode'),
                stock=int(data.get('stock', 0)),
                status=data.get('status', 'active')
            )
            updated = self.products.update(product)
            return self._response(True, updated.to_dict())
        except Exception as e:
            return self._response(False, error=str(e))

    def products_delete(self, product_id: str) -> dict:
        """Delete (deactivate) a product."""
        try:
            self.products.delete(product_id)
            return self._response(True)
        except Exception as e:
            return self._response(False, error=str(e))

    def products_import_csv(self, file_path: str) -> dict:
        """Import products from CSV file."""
        try:
            result = self.csv_importer.import_csv(file_path)
            self.audit.log_product_imported(result.imported, file_path)
            return self._response(result.success, result.to_dict())
        except Exception as e:
            return self._response(False, error=str(e))

    # ============ Invoices ============

    def invoices_create(
        self,
        items: list[dict],
        payment_method: str,
        customer_email: str = None
    ) -> dict:
        """
        Create a new invoice.

        Args:
            items: List of {product_id, quantity}
            payment_method: 'cash' or 'card'
            customer_email: Optional customer email
        """
        try:
            # Get settings
            store_name = self.settings.store_name
            seller_id = self.settings.seller_id
            currency_symbol = self.settings.currency_symbol

            # Calculate totals and build invoice items
            invoice_items = []
            subtotal = 0
            vat_total = 0

            for item_data in items:
                product = self.products.get_by_id(item_data['product_id'])
                if not product:
                    return self._response(False, error=f"Product {item_data['product_id']} not found")

                quantity = int(item_data['quantity'])
                line_total = product.price * quantity
                vat_amount = line_total * (product.vat_rate / 100)

                subtotal += line_total
                vat_total += vat_amount

                invoice_items.append(InvoiceItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=product.price,
                    vat_rate=product.vat_rate,
                    line_total=line_total
                ))

            total = subtotal + vat_total

            # Get previous hash for chain
            previous_hash = self.invoices.get_latest_hash()

            # Generate invoice number
            invoice_number = self.invoices.get_next_invoice_number()
            timestamp = datetime.now().isoformat()

            # Calculate hash
            current_hash = HashChain.calculate_hash(
                invoice_number=invoice_number,
                seller_id=seller_id,
                total=total,
                items=[item.to_dict() for item in invoice_items],
                timestamp=timestamp,
                previous_hash=previous_hash
            )

            # Generate QR code
            qr_data, qr_image = self.qr_generator.generate_for_invoice(
                invoice_number=invoice_number,
                total=total,
                hash_value=current_hash,
                timestamp=timestamp
            )

            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                seller_id=seller_id,
                store_name=store_name,
                subtotal=round(subtotal, 2),
                vat_amount=round(vat_total, 2),
                total=round(total, 2),
                payment_method=payment_method,
                customer_email=customer_email,
                previous_hash=previous_hash,
                current_hash=current_hash,
                qr_data=qr_data,
                created_at=timestamp,
                items=invoice_items
            )

            created = self.invoices.create(invoice)

            # Update product stock
            for item_data in items:
                self.products.update_stock(item_data['product_id'], -int(item_data['quantity']))

            # Log creation
            self.audit.log_invoice_created(invoice_number, total)

            # Add QR image to response
            response_data = created.to_dict()
            response_data['qr_image'] = qr_image
            response_data['currency_symbol'] = currency_symbol

            return self._response(True, response_data)

        except Exception as e:
            return self._response(False, error=str(e))

    def invoices_get_by_number(self, invoice_number: str) -> dict:
        """Get invoice by number."""
        try:
            invoice = self.invoices.get_by_number(invoice_number)
            if invoice:
                data = invoice.to_dict()
                # Regenerate QR image for display
                _, qr_image = self.qr_generator.generate_for_invoice(
                    invoice_number=invoice.invoice_number,
                    total=invoice.total,
                    hash_value=invoice.current_hash,
                    timestamp=invoice.created_at
                )
                data['qr_image'] = qr_image
                return self._response(True, data)
            return self._response(False, error="Invoice not found")
        except Exception as e:
            return self._response(False, error=str(e))

    def invoices_process_return(self, invoice_number: str, item_ids: list[int]) -> dict:
        """Process return for specific items."""
        try:
            invoice = self.invoices.get_by_number(invoice_number)
            if not invoice:
                return self._response(False, error="Invoice not found")

            refund_amount = 0

            for item in invoice.items:
                if item.id in item_ids:
                    if item.return_status == 'returned':
                        return self._response(False, error=f"Item {item.id} already returned")

                    # Mark as returned
                    self.invoices.mark_item_returned(item.id)

                    # Restore stock
                    self.products.update_stock(item.product_id, item.quantity)

                    refund_amount += item.line_total

            # Update invoice status
            all_returned = all(
                item.id in item_ids or item.return_status == 'returned'
                for item in invoice.items
            )

            new_status = 'returned' if all_returned else 'partial_return'
            self.invoices.update_status(invoice.id, new_status)

            # Log return
            self.audit.log_invoice_returned(invoice_number, item_ids, refund_amount)

            return self._response(True, {
                'invoice_number': invoice_number,
                'refund_amount': refund_amount,
                'new_status': new_status
            })

        except Exception as e:
            return self._response(False, error=str(e))

    # ============ Validation ============

    def qr_validate(self, qr_data: str) -> dict:
        """Validate a QR code."""
        try:
            result = self.qr_validator.validate(qr_data)
            return self._response(result.valid, result.to_dict(), result.error_message)
        except Exception as e:
            return self._response(False, error=str(e))

    def hash_chain_verify(self) -> dict:
        """Verify entire hash chain integrity."""
        try:
            # Get all invoices in order
            rows = self.db.fetchall(
                "SELECT * FROM invoices ORDER BY id ASC"
            )

            invoices = []
            for row in rows:
                items = self.invoices._get_items(row['id'])
                invoice = Invoice.from_row(row, items)
                invoices.append(invoice.to_dict())

            result = HashChain.verify_chain(invoices)

            return self._response(
                result.valid,
                {
                    'valid': result.valid,
                    'checked_count': result.checked_count,
                    'error_message': result.error_message,
                    'failed_invoice_id': result.failed_invoice_id
                }
            )
        except Exception as e:
            return self._response(False, error=str(e))

    # ============ Printing/Export ============

    def print_receipt(self, invoice_id: int) -> dict:
        """Print receipt to thermal printer."""
        try:
            invoice = self.invoices.get_by_id(invoice_id)
            if not invoice:
                return self._response(False, error="Invoice not found")

            # Generate QR image
            _, qr_image = self.qr_generator.generate_for_invoice(
                invoice_number=invoice.invoice_number,
                total=invoice.total,
                hash_value=invoice.current_hash,
                timestamp=invoice.created_at
            )

            self.printer.print_receipt(
                store_name=invoice.store_name,
                invoice_number=invoice.invoice_number,
                items=[item.to_dict() for item in invoice.items],
                subtotal=invoice.subtotal,
                vat_amount=invoice.vat_amount,
                total=invoice.total,
                payment_method=invoice.payment_method,
                qr_base64=qr_image,
                currency_symbol=self.settings.currency_symbol,
                seller_id=invoice.seller_id,
                timestamp=invoice.created_at
            )

            self.audit.log_receipt_printed(invoice.invoice_number)
            return self._response(True)

        except PrinterNotConnectedError as e:
            return self._response(False, error=str(e))
        except Exception as e:
            return self._response(False, error=str(e))

    def generate_pdf(self, invoice_id: int) -> dict:
        """Generate PDF receipt."""
        try:
            invoice = self.invoices.get_by_id(invoice_id)
            if not invoice:
                return self._response(False, error="Invoice not found")

            # Generate QR image
            _, qr_image = self.qr_generator.generate_for_invoice(
                invoice_number=invoice.invoice_number,
                total=invoice.total,
                hash_value=invoice.current_hash,
                timestamp=invoice.created_at
            )

            invoice_data = invoice.to_dict()
            invoice_data['qr_image'] = qr_image

            pdf_path = self.pdf_generator.save_receipt_pdf(
                invoice_number=invoice.invoice_number,
                store_name=invoice.store_name,
                seller_id=invoice.seller_id,
                items=[item.to_dict() for item in invoice.items],
                subtotal=invoice.subtotal,
                vat_amount=invoice.vat_amount,
                total=invoice.total,
                payment_method=invoice.payment_method,
                qr_base64=qr_image,
                currency_symbol=self.settings.currency_symbol,
                timestamp=invoice.created_at,
                customer_email=invoice.customer_email
            )

            return self._response(True, {'path': str(pdf_path)})

        except Exception as e:
            return self._response(False, error=str(e))

    def send_email(self, invoice_id: int, email: str) -> dict:
        """Send receipt via email."""
        try:
            invoice = self.invoices.get_by_id(invoice_id)
            if not invoice:
                return self._response(False, error="Invoice not found")

            # Configure email service
            smtp_config = self.settings.get_smtp_config()
            self.email_service.set_config(EmailConfig.from_dict(smtp_config))

            if not self.email_service.is_configured():
                return self._response(False, error="Email not configured")

            # Generate PDF
            _, qr_image = self.qr_generator.generate_for_invoice(
                invoice_number=invoice.invoice_number,
                total=invoice.total,
                hash_value=invoice.current_hash,
                timestamp=invoice.created_at
            )

            pdf_bytes = self.pdf_generator.generate_receipt_pdf(
                store_name=invoice.store_name,
                invoice_number=invoice.invoice_number,
                seller_id=invoice.seller_id,
                items=[item.to_dict() for item in invoice.items],
                subtotal=invoice.subtotal,
                vat_amount=invoice.vat_amount,
                total=invoice.total,
                payment_method=invoice.payment_method,
                qr_base64=qr_image,
                currency_symbol=self.settings.currency_symbol,
                timestamp=invoice.created_at
            )

            # Send email
            result = self.email_service.send_receipt(
                to_email=email,
                invoice_number=invoice.invoice_number,
                store_name=invoice.store_name,
                total=invoice.total,
                pdf_bytes=pdf_bytes,
                currency_symbol=self.settings.currency_symbol
            )

            if result.success:
                self.audit.log_receipt_emailed(invoice.invoice_number, email)
                return self._response(True, {'message': result.message})
            return self._response(False, error=result.error)

        except Exception as e:
            return self._response(False, error=str(e))

    # ============ Settings ============

    def settings_get_all(self) -> dict:
        """Get all settings."""
        try:
            settings = self.settings.get_all_typed()
            return self._response(True, settings)
        except Exception as e:
            return self._response(False, error=str(e))

    def settings_update(self, key: str, value: Any) -> dict:
        """Update a single setting."""
        try:
            old_value = self.settings.get(key)
            self.settings.set(key, value)
            self.audit.log_setting_changed(key, old_value, str(value))
            return self._response(True)
        except Exception as e:
            return self._response(False, error=str(e))

    def settings_update_many(self, settings: dict) -> dict:
        """Update multiple settings."""
        try:
            self.settings.set_many(settings)
            return self._response(True)
        except Exception as e:
            return self._response(False, error=str(e))

    def get_keyboard_layouts(self) -> dict:
        """Get available keyboard layouts."""
        try:
            layouts = KeyboardMapper.get_available_layouts()
            return self._response(True, layouts)
        except Exception as e:
            return self._response(False, error=str(e))

    # ============ Printer ============

    def printer_status(self) -> dict:
        """Get printer connection status."""
        try:
            status = self.printer.get_status()
            return self._response(True, {
                'connected': status.connected,
                'printer_name': status.printer_name,
                'error': status.error_message
            })
        except Exception as e:
            return self._response(False, error=str(e))

    def printer_test(self) -> dict:
        """Print test page."""
        try:
            self.printer.print_test_page()
            return self._response(True)
        except PrinterNotConnectedError as e:
            return self._response(False, error=str(e))
        except Exception as e:
            return self._response(False, error=str(e))

    # ============ Reports ============

    def reports_daily_sales(self, date: str) -> dict:
        """Get daily sales report."""
        try:
            report = self.reports.daily_sales(date)
            return self._response(True, report.to_dict())
        except Exception as e:
            return self._response(False, error=str(e))

    def reports_period_sales(self, start_date: str, end_date: str) -> dict:
        """Get sales report for date range."""
        try:
            report = self.reports.period_sales(start_date, end_date)
            return self._response(True, report.to_dict())
        except Exception as e:
            return self._response(False, error=str(e))

    def reports_top_products(self, limit: int = 10) -> dict:
        """Get top selling products."""
        try:
            products = self.reports.top_products(limit)
            return self._response(True, [p.to_dict() for p in products])
        except Exception as e:
            return self._response(False, error=str(e))

    def reports_export_csv(self, report_type: str, params: dict = None) -> dict:
        """Export report to CSV."""
        try:
            csv_content = self.reports.export_csv(report_type, params)
            return self._response(True, {'csv': csv_content})
        except Exception as e:
            return self._response(False, error=str(e))

    def reports_today_summary(self) -> dict:
        """Get today's sales summary."""
        try:
            summary = self.reports.get_today_summary()
            return self._response(True, summary)
        except Exception as e:
            return self._response(False, error=str(e))

    # ============ Email Test ============

    def email_test_connection(self) -> dict:
        """Test SMTP connection."""
        try:
            smtp_config = self.settings.get_smtp_config()
            self.email_service.set_config(EmailConfig.from_dict(smtp_config))
            result = self.email_service.test_connection()
            return self._response(result.success, error=result.error)
        except Exception as e:
            return self._response(False, error=str(e))
