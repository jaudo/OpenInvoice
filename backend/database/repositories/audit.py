"""Audit log repository for tracking actions."""

from typing import Optional
from dataclasses import dataclass, asdict
import json

from ..connection import Database


@dataclass
class AuditEntry:
    """Audit log entry."""
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Optional[dict] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        return data

    @classmethod
    def from_row(cls, row) -> 'AuditEntry':
        """Create AuditEntry from database row."""
        details = None
        if row['details']:
            try:
                details = json.loads(row['details'])
            except json.JSONDecodeError:
                details = {'raw': row['details']}

        return cls(
            id=row['id'],
            action=row['action'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            details=details,
            created_at=row['created_at']
        )


class AuditRepository:
    """Repository for audit log operations."""

    # Action constants
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_RETURN = 'return'
    ACTION_PRINT = 'print'
    ACTION_EMAIL = 'email'
    ACTION_EXPORT = 'export'
    ACTION_IMPORT = 'import'
    ACTION_SETTING_CHANGE = 'setting_change'

    # Entity type constants
    ENTITY_INVOICE = 'invoice'
    ENTITY_PRODUCT = 'product'
    ENTITY_SETTING = 'setting'
    ENTITY_REPORT = 'report'

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditEntry:
        """Create an audit log entry."""
        details_json = json.dumps(details) if details else None

        cursor = self.db.connection.cursor()
        cursor.execute(
            """
            INSERT INTO audit_log (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
            """,
            (action, entity_type, entity_id, details_json)
        )
        entry_id = cursor.lastrowid
        self.db.connection.commit()
        cursor.close()

        return self.get_by_id(entry_id)

    def get_by_id(self, entry_id: int) -> Optional[AuditEntry]:
        """Get audit entry by ID."""
        row = self.db.fetchone(
            "SELECT * FROM audit_log WHERE id = ?",
            (entry_id,)
        )
        return AuditEntry.from_row(row) if row else None

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100
    ) -> list[AuditEntry]:
        """Get audit entries for a specific entity."""
        rows = self.db.fetchall(
            """
            SELECT * FROM audit_log
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (entity_type, entity_id, limit)
        )
        return [AuditEntry.from_row(row) for row in rows]

    def get_by_action(self, action: str, limit: int = 100) -> list[AuditEntry]:
        """Get audit entries for a specific action."""
        rows = self.db.fetchall(
            """
            SELECT * FROM audit_log
            WHERE action = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (action, limit)
        )
        return [AuditEntry.from_row(row) for row in rows]

    def get_recent(self, limit: int = 100) -> list[AuditEntry]:
        """Get most recent audit entries."""
        rows = self.db.fetchall(
            """
            SELECT * FROM audit_log
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        return [AuditEntry.from_row(row) for row in rows]

    def get_by_date_range(
        self,
        start_date: str,
        end_date: str,
        entity_type: Optional[str] = None
    ) -> list[AuditEntry]:
        """Get audit entries within a date range."""
        if entity_type:
            rows = self.db.fetchall(
                """
                SELECT * FROM audit_log
                WHERE DATE(created_at) BETWEEN DATE(?) AND DATE(?)
                AND entity_type = ?
                ORDER BY created_at DESC
                """,
                (start_date, end_date, entity_type)
            )
        else:
            rows = self.db.fetchall(
                """
                SELECT * FROM audit_log
                WHERE DATE(created_at) BETWEEN DATE(?) AND DATE(?)
                ORDER BY created_at DESC
                """,
                (start_date, end_date)
            )
        return [AuditEntry.from_row(row) for row in rows]

    # Convenience methods for common logging
    def log_invoice_created(self, invoice_number: str, total: float) -> AuditEntry:
        """Log invoice creation."""
        return self.log(
            self.ACTION_CREATE,
            self.ENTITY_INVOICE,
            invoice_number,
            {'total': total}
        )

    def log_invoice_returned(
        self,
        invoice_number: str,
        item_ids: list[int],
        refund_amount: float
    ) -> AuditEntry:
        """Log invoice return."""
        return self.log(
            self.ACTION_RETURN,
            self.ENTITY_INVOICE,
            invoice_number,
            {'item_ids': item_ids, 'refund_amount': refund_amount}
        )

    def log_receipt_printed(self, invoice_number: str) -> AuditEntry:
        """Log receipt print."""
        return self.log(
            self.ACTION_PRINT,
            self.ENTITY_INVOICE,
            invoice_number
        )

    def log_receipt_emailed(self, invoice_number: str, email: str) -> AuditEntry:
        """Log receipt email."""
        return self.log(
            self.ACTION_EMAIL,
            self.ENTITY_INVOICE,
            invoice_number,
            {'recipient': email}
        )

    def log_product_imported(self, count: int, filename: str) -> AuditEntry:
        """Log product import."""
        return self.log(
            self.ACTION_IMPORT,
            self.ENTITY_PRODUCT,
            None,
            {'count': count, 'filename': filename}
        )

    def log_setting_changed(self, key: str, old_value: str, new_value: str) -> AuditEntry:
        """Log setting change."""
        return self.log(
            self.ACTION_SETTING_CHANGE,
            self.ENTITY_SETTING,
            key,
            {'old_value': old_value, 'new_value': new_value}
        )
