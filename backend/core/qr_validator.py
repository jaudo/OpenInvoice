"""QR code validation for receipt authenticity verification."""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

from .qr_generator import QRGenerator
from .hash_chain import HashChain


@dataclass
class ValidationResult:
    """Result of QR code validation."""
    valid: bool
    invoice_number: Optional[str] = None
    error_message: Optional[str] = None
    invoice_data: Optional[dict] = None
    checks: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class QRValidator:
    """Validate QR codes against stored invoices."""

    def __init__(self, invoice_repository):
        """
        Initialize validator with invoice repository.

        Args:
            invoice_repository: Repository to lookup invoices
        """
        self.invoice_repo = invoice_repository
        self.qr_generator = QRGenerator()

    def validate(self, qr_data: str) -> ValidationResult:
        """
        Validate a QR code string.

        Performs the following checks:
        1. QR format is valid
        2. Invoice exists in database
        3. Hash prefix matches stored hash
        4. Total matches stored total
        5. Invoice hash is valid (recalculated)

        Args:
            qr_data: The scanned QR code data string

        Returns:
            ValidationResult with validation status and details
        """
        checks = {
            'format_valid': False,
            'invoice_exists': False,
            'hash_matches': False,
            'total_matches': False,
            'hash_verified': False
        }

        # Step 1: Parse QR data
        parsed = self.qr_generator.parse_qr_data(qr_data)
        if not parsed:
            return ValidationResult(
                valid=False,
                error_message="Invalid QR code format",
                checks=checks
            )
        checks['format_valid'] = True

        invoice_number = parsed['invoice_number']

        # Step 2: Look up invoice
        invoice = self.invoice_repo.get_by_number(invoice_number)
        if not invoice:
            return ValidationResult(
                valid=False,
                invoice_number=invoice_number,
                error_message=f"Invoice {invoice_number} not found",
                checks=checks
            )
        checks['invoice_exists'] = True

        # Step 3: Verify hash prefix
        stored_hash_prefix = invoice.current_hash[:8]
        if stored_hash_prefix != parsed['hash_prefix']:
            return ValidationResult(
                valid=False,
                invoice_number=invoice_number,
                error_message="Hash verification failed - receipt may be tampered",
                checks=checks
            )
        checks['hash_matches'] = True

        # Step 4: Verify total
        if abs(invoice.total - parsed['total']) > 0.01:
            return ValidationResult(
                valid=False,
                invoice_number=invoice_number,
                error_message="Total amount mismatch - receipt may be tampered",
                checks=checks
            )
        checks['total_matches'] = True

        # Step 5: Recalculate and verify full hash
        items = [item.to_dict() for item in invoice.items]
        recalculated_hash = HashChain.calculate_hash(
            invoice_number=invoice.invoice_number,
            seller_id=invoice.seller_id,
            total=invoice.total,
            items=items,
            timestamp=invoice.created_at,
            previous_hash=invoice.previous_hash or HashChain.GENESIS_HASH
        )

        if recalculated_hash != invoice.current_hash:
            return ValidationResult(
                valid=False,
                invoice_number=invoice_number,
                error_message="Invoice data integrity check failed",
                checks=checks
            )
        checks['hash_verified'] = True

        # All checks passed
        return ValidationResult(
            valid=True,
            invoice_number=invoice_number,
            invoice_data=invoice.to_dict(),
            checks=checks
        )

    def validate_by_invoice_number(self, invoice_number: str) -> ValidationResult:
        """
        Validate an invoice by its number (without QR code).

        Useful for manual verification when QR is not available.

        Args:
            invoice_number: The invoice number to validate

        Returns:
            ValidationResult with validation status
        """
        checks = {
            'invoice_exists': False,
            'hash_verified': False,
            'chain_valid': False
        }

        # Look up invoice
        invoice = self.invoice_repo.get_by_number(invoice_number)
        if not invoice:
            return ValidationResult(
                valid=False,
                invoice_number=invoice_number,
                error_message=f"Invoice {invoice_number} not found",
                checks=checks
            )
        checks['invoice_exists'] = True

        # Recalculate hash
        items = [item.to_dict() for item in invoice.items]
        recalculated_hash = HashChain.calculate_hash(
            invoice_number=invoice.invoice_number,
            seller_id=invoice.seller_id,
            total=invoice.total,
            items=items,
            timestamp=invoice.created_at,
            previous_hash=invoice.previous_hash or HashChain.GENESIS_HASH
        )

        if recalculated_hash != invoice.current_hash:
            return ValidationResult(
                valid=False,
                invoice_number=invoice_number,
                error_message="Invoice hash verification failed",
                checks=checks
            )
        checks['hash_verified'] = True

        # Verify chain link (previous hash)
        if invoice.previous_hash and invoice.previous_hash != HashChain.GENESIS_HASH:
            prev_invoice = self.invoice_repo.get_by_hash(invoice.previous_hash)
            if not prev_invoice:
                return ValidationResult(
                    valid=False,
                    invoice_number=invoice_number,
                    error_message="Hash chain broken - previous invoice not found",
                    checks=checks
                )
        checks['chain_valid'] = True

        return ValidationResult(
            valid=True,
            invoice_number=invoice_number,
            invoice_data=invoice.to_dict(),
            checks=checks
        )

    def get_invoice_status_text(self, invoice_data: dict) -> str:
        """Get human-readable status text for an invoice."""
        status = invoice_data.get('status', 'unknown')
        status_map = {
            'completed': 'Completed',
            'returned': 'Fully Returned',
            'partial_return': 'Partially Returned'
        }
        return status_map.get(status, status.title())
