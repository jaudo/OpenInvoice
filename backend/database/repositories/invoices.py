"""Invoice repository for database operations."""

from typing import Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

from ..connection import Database


@dataclass
class InvoiceItem:
    """Invoice item entity."""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    vat_rate: float
    line_total: float
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    return_status: str = "none"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row) -> 'InvoiceItem':
        """Create InvoiceItem from database row."""
        return cls(
            id=row['id'],
            invoice_id=row['invoice_id'],
            product_id=row['product_id'],
            product_name=row['product_name'],
            quantity=row['quantity'],
            unit_price=row['unit_price'],
            vat_rate=row['vat_rate'],
            line_total=row['line_total'],
            return_status=row['return_status']
        )


@dataclass
class Invoice:
    """Invoice entity."""
    invoice_number: str
    seller_id: str
    store_name: str
    subtotal: float
    vat_amount: float
    total: float
    current_hash: str
    qr_data: str
    id: Optional[int] = None
    payment_method: Optional[str] = None
    customer_email: Optional[str] = None
    previous_hash: Optional[str] = None
    status: str = "completed"
    created_at: Optional[str] = None
    items: list[InvoiceItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['items'] = [item.to_dict() for item in self.items]
        return data

    @classmethod
    def from_row(cls, row, items: list[InvoiceItem] = None) -> 'Invoice':
        """Create Invoice from database row."""
        return cls(
            id=row['id'],
            invoice_number=row['invoice_number'],
            seller_id=row['seller_id'],
            store_name=row['store_name'],
            subtotal=row['subtotal'],
            vat_amount=row['vat_amount'],
            total=row['total'],
            payment_method=row['payment_method'],
            customer_email=row['customer_email'],
            previous_hash=row['previous_hash'],
            current_hash=row['current_hash'],
            qr_data=row['qr_data'],
            status=row['status'],
            created_at=row['created_at'],
            items=items or []
        )


class InvoiceRepository:
    """Repository for invoice database operations."""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID with items."""
        row = self.db.fetchone(
            "SELECT * FROM invoices WHERE id = ?",
            (invoice_id,)
        )
        if not row:
            return None

        items = self._get_items(invoice_id)
        return Invoice.from_row(row, items)

    def get_by_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number with items."""
        row = self.db.fetchone(
            "SELECT * FROM invoices WHERE invoice_number = ?",
            (invoice_number,)
        )
        if not row:
            return None

        items = self._get_items(row['id'])
        return Invoice.from_row(row, items)

    def get_by_hash(self, current_hash: str) -> Optional[Invoice]:
        """Get invoice by its hash."""
        row = self.db.fetchone(
            "SELECT * FROM invoices WHERE current_hash = ?",
            (current_hash,)
        )
        if not row:
            return None

        items = self._get_items(row['id'])
        return Invoice.from_row(row, items)

    def _get_items(self, invoice_id: int) -> list[InvoiceItem]:
        """Get items for an invoice."""
        rows = self.db.fetchall(
            "SELECT * FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,)
        )
        return [InvoiceItem.from_row(row) for row in rows]

    def get_latest(self) -> Optional[Invoice]:
        """Get the most recent invoice."""
        row = self.db.fetchone(
            "SELECT * FROM invoices ORDER BY id DESC LIMIT 1"
        )
        if not row:
            return None

        items = self._get_items(row['id'])
        return Invoice.from_row(row, items)

    def get_latest_hash(self) -> str:
        """Get the hash of the most recent invoice, or GENESIS if none."""
        row = self.db.fetchone(
            "SELECT current_hash FROM invoices ORDER BY id DESC LIMIT 1"
        )
        return row['current_hash'] if row else "GENESIS"

    def create(self, invoice: Invoice) -> Invoice:
        """Create a new invoice with items."""
        # Insert invoice
        cursor = self.db.connection.cursor()
        cursor.execute(
            """
            INSERT INTO invoices (
                invoice_number, seller_id, store_name, subtotal, vat_amount,
                total, payment_method, customer_email, previous_hash,
                current_hash, qr_data, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice.invoice_number,
                invoice.seller_id,
                invoice.store_name,
                invoice.subtotal,
                invoice.vat_amount,
                invoice.total,
                invoice.payment_method,
                invoice.customer_email,
                invoice.previous_hash,
                invoice.current_hash,
                invoice.qr_data,
                invoice.status
            )
        )
        invoice_id = cursor.lastrowid

        # Insert items
        for item in invoice.items:
            cursor.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id, product_id, product_name, quantity,
                    unit_price, vat_rate, line_total, return_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item.product_id,
                    item.product_name,
                    item.quantity,
                    item.unit_price,
                    item.vat_rate,
                    item.line_total,
                    item.return_status
                )
            )

        self.db.connection.commit()
        cursor.close()

        return self.get_by_id(invoice_id)

    def update_status(self, invoice_id: int, status: str) -> Optional[Invoice]:
        """Update invoice status."""
        self.db.execute(
            "UPDATE invoices SET status = ? WHERE id = ?",
            (status, invoice_id)
        )
        return self.get_by_id(invoice_id)

    def mark_item_returned(self, item_id: int) -> bool:
        """Mark an invoice item as returned."""
        self.db.execute(
            "UPDATE invoice_items SET return_status = 'returned' WHERE id = ?",
            (item_id,)
        )
        return True

    def get_all_hashes(self) -> list[tuple[int, str, str]]:
        """Get all invoice hashes for chain verification."""
        rows = self.db.fetchall(
            """
            SELECT id, previous_hash, current_hash
            FROM invoices
            ORDER BY id ASC
            """
        )
        return [(row['id'], row['previous_hash'], row['current_hash']) for row in rows]

    def get_next_invoice_number(self) -> str:
        """Generate next invoice number."""
        year = datetime.now().year
        prefix = f"INV-{year}-"

        row = self.db.fetchone(
            """
            SELECT invoice_number FROM invoices
            WHERE invoice_number LIKE ?
            ORDER BY id DESC LIMIT 1
            """,
            (f"{prefix}%",)
        )

        if row:
            # Extract number and increment
            current_num = int(row['invoice_number'].split('-')[-1])
            next_num = current_num + 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"

    def get_by_date_range(self, start_date: str, end_date: str) -> list[Invoice]:
        """Get invoices within a date range."""
        rows = self.db.fetchall(
            """
            SELECT * FROM invoices
            WHERE DATE(created_at) BETWEEN DATE(?) AND DATE(?)
            ORDER BY created_at DESC
            """,
            (start_date, end_date)
        )
        invoices = []
        for row in rows:
            items = self._get_items(row['id'])
            invoices.append(Invoice.from_row(row, items))
        return invoices

    def count_by_date(self, date: str) -> int:
        """Count invoices for a specific date."""
        row = self.db.fetchone(
            "SELECT COUNT(*) as count FROM invoices WHERE DATE(created_at) = DATE(?)",
            (date,)
        )
        return row['count'] if row else 0

    def sum_by_date(self, date: str) -> float:
        """Sum total sales for a specific date."""
        row = self.db.fetchone(
            """
            SELECT COALESCE(SUM(total), 0) as total
            FROM invoices
            WHERE DATE(created_at) = DATE(?) AND status != 'returned'
            """,
            (date,)
        )
        return row['total'] if row else 0.0
