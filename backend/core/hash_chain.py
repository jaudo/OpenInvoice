"""Blockchain-style hash chain for receipt authenticity."""

import hashlib
import json
from typing import Optional
from dataclasses import dataclass


@dataclass
class HashVerificationResult:
    """Result of hash chain verification."""
    valid: bool
    error_message: Optional[str] = None
    failed_invoice_id: Optional[int] = None
    checked_count: int = 0


class HashChain:
    """Blockchain-style hash chain for invoice integrity."""

    GENESIS_HASH = "GENESIS"

    @staticmethod
    def calculate_hash(
        invoice_number: str,
        seller_id: str,
        total: float,
        items: list[dict],
        timestamp: str,
        previous_hash: str
    ) -> str:
        """
        Calculate SHA-256 hash for an invoice.

        The hash includes all critical invoice data plus the previous hash,
        creating an unbreakable chain where any modification is detectable.
        """
        # Normalize items to ensure consistent hashing
        normalized_items = [
            {
                'product_id': item.get('product_id'),
                'quantity': item.get('quantity'),
                'unit_price': item.get('unit_price'),
                'line_total': item.get('line_total'),
            }
            for item in items
        ]

        data = {
            'invoice_number': invoice_number,
            'seller_id': seller_id,
            'total': round(total, 2),
            'items': normalized_items,
            'timestamp': timestamp,
            'previous_hash': previous_hash
        }

        # Sort keys for deterministic output
        data_string = json.dumps(data, sort_keys=True, separators=(',', ':'))

        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    @staticmethod
    def calculate_hash_from_invoice(invoice: dict, previous_hash: str) -> str:
        """Calculate hash from an invoice dictionary."""
        items = invoice.get('items', [])
        if hasattr(items[0] if items else None, 'to_dict'):
            items = [item.to_dict() for item in items]

        return HashChain.calculate_hash(
            invoice_number=invoice['invoice_number'],
            seller_id=invoice['seller_id'],
            total=invoice['total'],
            items=items,
            timestamp=invoice['created_at'],
            previous_hash=previous_hash
        )

    @staticmethod
    def verify_single(
        invoice: dict,
        expected_hash: str,
        previous_hash: str
    ) -> bool:
        """Verify a single invoice's hash."""
        calculated = HashChain.calculate_hash_from_invoice(invoice, previous_hash)
        return calculated == expected_hash

    @classmethod
    def verify_chain(cls, invoices: list[dict]) -> HashVerificationResult:
        """
        Verify the entire hash chain.

        Args:
            invoices: List of invoices in chronological order (oldest first)

        Returns:
            HashVerificationResult with validation status
        """
        if not invoices:
            return HashVerificationResult(valid=True, checked_count=0)

        previous_hash = cls.GENESIS_HASH

        for i, invoice in enumerate(invoices):
            expected_hash = invoice.get('current_hash')

            # Calculate what the hash should be
            calculated_hash = cls.calculate_hash_from_invoice(invoice, previous_hash)

            if calculated_hash != expected_hash:
                return HashVerificationResult(
                    valid=False,
                    error_message=f"Hash mismatch at invoice {invoice.get('invoice_number')}",
                    failed_invoice_id=invoice.get('id'),
                    checked_count=i
                )

            # Verify the chain link
            stored_previous = invoice.get('previous_hash')
            if stored_previous != previous_hash:
                return HashVerificationResult(
                    valid=False,
                    error_message=f"Chain break at invoice {invoice.get('invoice_number')}",
                    failed_invoice_id=invoice.get('id'),
                    checked_count=i
                )

            previous_hash = expected_hash

        return HashVerificationResult(
            valid=True,
            checked_count=len(invoices)
        )

    @staticmethod
    def get_hash_prefix(full_hash: str, length: int = 8) -> str:
        """Get the first N characters of a hash for display/QR codes."""
        return full_hash[:length] if full_hash else ""
