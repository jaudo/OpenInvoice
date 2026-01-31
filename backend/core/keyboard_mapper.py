"""Keyboard layout mapper for barcode scanner support."""

from typing import Optional


class KeyboardMapper:
    """
    Maps keyboard input from barcode scanners with different layouts.

    Barcode scanners typically emulate keyboard input, but if the scanner
    is configured for a different keyboard layout than the system, the
    scanned characters may be incorrect.
    """

    # Layout definitions: maps QWERTY keys to other layout keys
    LAYOUTS = {
        'qwerty': {},  # No mapping needed (identity)
        'azerty': {
            'q': 'a', 'w': 'z', 'a': 'q', 'z': 'w',
            ';': 'm', 'm': ',', ',': ';',
            '1': '&', '2': 'é', '3': '"', '4': "'",
            '5': '(', '6': '-', '7': 'è', '8': '_',
            '9': 'ç', '0': 'à',
        },
        'qwertz': {
            'y': 'z', 'z': 'y',
            '-': 'ß', '=': '´',
            '[': 'ü', ']': '+',
            ';': 'ö', "'": 'ä',
        },
    }

    # Reverse mappings (other layout → QWERTY)
    REVERSE_LAYOUTS = {}

    def __init__(self, layout: str = 'qwerty'):
        """
        Initialize mapper with specified layout.

        Args:
            layout: The keyboard layout of the scanner ('qwerty', 'azerty', 'qwertz')
        """
        self.layout = layout.lower()
        self._build_reverse_mappings()

    def _build_reverse_mappings(self):
        """Build reverse mappings for all layouts."""
        for layout_name, mapping in self.LAYOUTS.items():
            self.REVERSE_LAYOUTS[layout_name] = {v: k for k, v in mapping.items()}

    def map_to_qwerty(self, text: str, source_layout: Optional[str] = None) -> str:
        """
        Map text from source layout to QWERTY.

        Args:
            text: Input text from scanner
            source_layout: Source keyboard layout (uses instance layout if not specified)

        Returns:
            Text mapped to QWERTY layout
        """
        layout = source_layout or self.layout
        if layout == 'qwerty':
            return text

        mapping = self.REVERSE_LAYOUTS.get(layout, {})
        return ''.join(mapping.get(c, c) for c in text)

    def map_from_qwerty(self, text: str, target_layout: Optional[str] = None) -> str:
        """
        Map text from QWERTY to target layout.

        Args:
            text: Input text in QWERTY
            target_layout: Target keyboard layout

        Returns:
            Text mapped to target layout
        """
        layout = target_layout or self.layout
        if layout == 'qwerty':
            return text

        mapping = self.LAYOUTS.get(layout, {})
        return ''.join(mapping.get(c, c) for c in text)

    @classmethod
    def get_available_layouts(cls) -> list[dict]:
        """Get list of available keyboard layouts with descriptions."""
        return [
            {'id': 'qwerty', 'name': 'QWERTY', 'description': 'US/UK Standard'},
            {'id': 'azerty', 'name': 'AZERTY', 'description': 'French'},
            {'id': 'qwertz', 'name': 'QWERTZ', 'description': 'German/Central European'},
        ]

    @staticmethod
    def is_likely_barcode(text: str) -> bool:
        """
        Check if text looks like a barcode input.

        Barcodes are typically:
        - All digits (EAN-13, UPC-A)
        - Alphanumeric without spaces (Code 128, Code 39)
        - Entered rapidly (but we can't detect timing here)

        Args:
            text: Input text to check

        Returns:
            True if text appears to be a barcode
        """
        if not text:
            return False

        # Common barcode lengths
        barcode_lengths = {8, 12, 13, 14}  # EAN-8, UPC-A, EAN-13, ITF-14

        # Check for numeric barcodes
        if text.isdigit() and len(text) in barcode_lengths:
            return True

        # Check for alphanumeric barcodes (Code 128, Code 39)
        if text.isalnum() and ' ' not in text and len(text) >= 4:
            return True

        return False

    @staticmethod
    def validate_ean13(barcode: str) -> bool:
        """
        Validate EAN-13 barcode checksum.

        Args:
            barcode: 13-digit barcode string

        Returns:
            True if checksum is valid
        """
        if len(barcode) != 13 or not barcode.isdigit():
            return False

        # Calculate checksum
        total = 0
        for i, digit in enumerate(barcode[:12]):
            multiplier = 1 if i % 2 == 0 else 3
            total += int(digit) * multiplier

        check_digit = (10 - (total % 10)) % 10
        return int(barcode[12]) == check_digit
