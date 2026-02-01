"""Keyboard layout mapper for barcode scanner support."""

from typing import Optional


class KeyboardMapper:
    """
    Maps keyboard input from barcode scanners with different layouts.

    Barcode scanners typically emulate keyboard input, but if the scanner
    is configured for a different keyboard layout than the system, the
    scanned characters may be incorrect.

    Common scenario: Scanner sends US keyboard scancodes, but Windows
    interprets them using Spanish/German/French layout.
    """

    # Maps what you GET (Spanish layout interpretation) -> what you WANT (US original)
    # When scanner is US but system is Spanish (ES)
    ES_TO_US = {
        'Ñ': ':',   # Shift+Ñ position = Shift+; on US = :
        'ñ': ';',   # Ñ position = ; on US
        '-': '/',   # - key on Spanish = / on US (next to right shift)
        '_': '?',   # Shift+- on Spanish = ? on US
        '\'': '-',  # ' (apostrophe) on Spanish = - on US
        '´': '-',   # ´ (acute accent) on Spanish = - on US (Windows variant)
        '\u2019': '-',  # ' (right single quote U+2019) on Spanish = - on US (Unicode variant)
        '?': '_',   # Shift+' on Spanish = _ on US
        '¡': '=',   # ¡ on Spanish = = on US
        '¿': '+',   # Shift+¡ on Spanish = + on US
        '`': '[',   # ` on Spanish = [ on US
        '^': '{',   # Shift+` on Spanish = { on US
        '+': ']',   # + on Spanish = ] on US
        '*': '}',   # Shift++ on Spanish = } on US
        'ç': '\\',  # ç on Spanish = \ on US
        'Ç': '|',   # Shift+ç on Spanish = | on US
        'º': '`',   # º on Spanish = ` on US
        'ª': '~',   # Shift+º on Spanish = ~ on US
        # Numbers with shift (Spanish keyboard)
        '!': '!',   # Same
        '"': '@',   # Shift+2 on Spanish = @ on US
        '·': '#',   # Shift+3 on Spanish (middot) = # on US
        '$': '$',   # Same
        '%': '%',   # Same
        '&': '^',   # Shift+6 on Spanish = ^ on US
        '/': '&',   # Shift+7 on Spanish = & on US
        '(': '*',   # Shift+8 on Spanish = * on US
        ')': '(',   # Shift+9 on Spanish = ( on US
        '=': ')',   # Shift+0 on Spanish = ) on US
    }

    # Maps what you GET (US layout) -> Spanish layout
    US_TO_ES = {v: k for k, v in ES_TO_US.items() if k != v}

    # Layout definitions: physical layout mappings (QWERTY/AZERTY/QWERTZ)
    LAYOUTS = {
        'qwerty_us': {},  # No mapping needed (identity)
        'qwerty_es': ES_TO_US,  # Spanish interpretation → US original
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

    # Reverse mappings (other layout → original)
    REVERSE_LAYOUTS = {}

    def __init__(self, scanner_layout: str = 'qwerty_us', system_layout: str = 'qwerty_us'):
        """
        Initialize mapper with specified layouts.

        Args:
            scanner_layout: The keyboard layout the scanner is configured for
            system_layout: The keyboard layout Windows/OS is using
        """
        self.scanner_layout = scanner_layout.lower()
        self.system_layout = system_layout.lower()
        self._build_reverse_mappings()

    def _build_reverse_mappings(self):
        """Build reverse mappings for all layouts."""
        for layout_name, mapping in self.LAYOUTS.items():
            self.REVERSE_LAYOUTS[layout_name] = {v: k for k, v in mapping.items()}

    def convert_input(self, text: str) -> str:
        """
        Convert scanner input from system layout interpretation to original characters.

        This is the main method to use when the scanner sends US characters
        but Windows interprets them using a different keyboard layout.

        Args:
            text: Input text as received (with wrong characters)

        Returns:
            Corrected text
        """
        if self.system_layout == self.scanner_layout:
            return text

        # Get the mapping for converting system layout back to scanner layout
        if self.system_layout == 'qwerty_es' and self.scanner_layout == 'qwerty_us':
            mapping = self.ES_TO_US
        elif self.system_layout in self.LAYOUTS:
            mapping = self.REVERSE_LAYOUTS.get(self.system_layout, {})
        else:
            return text

        return ''.join(mapping.get(c, c) for c in text)

    def map_to_qwerty(self, text: str, source_layout: Optional[str] = None) -> str:
        """
        Map text from source layout to QWERTY US.

        Args:
            text: Input text from scanner
            source_layout: Source keyboard layout (uses system_layout if not specified)

        Returns:
            Text mapped to QWERTY US layout
        """
        layout = source_layout or self.system_layout

        if layout == 'qwerty_us':
            return text

        if layout == 'qwerty_es':
            mapping = self.ES_TO_US
        else:
            mapping = self.REVERSE_LAYOUTS.get(layout, {})

        return ''.join(mapping.get(c, c) for c in text)

    def map_from_qwerty(self, text: str, target_layout: Optional[str] = None) -> str:
        """
        Map text from QWERTY US to target layout.

        Args:
            text: Input text in QWERTY US
            target_layout: Target keyboard layout

        Returns:
            Text mapped to target layout
        """
        layout = target_layout or self.system_layout

        if layout == 'qwerty_us':
            return text

        if layout == 'qwerty_es':
            mapping = self.US_TO_ES
        else:
            mapping = self.LAYOUTS.get(layout, {})

        return ''.join(mapping.get(c, c) for c in text)

    @classmethod
    def get_available_layouts(cls) -> list[dict]:
        """Get list of available keyboard layouts with descriptions."""
        return [
            {'id': 'qwerty_us', 'name': 'QWERTY US', 'description': 'US English'},
            {'id': 'qwerty_es', 'name': 'QWERTY ES', 'description': 'Spanish'},
            {'id': 'azerty', 'name': 'AZERTY', 'description': 'French'},
            {'id': 'qwertz', 'name': 'QWERTZ', 'description': 'German/Central European'},
        ]

    @staticmethod
    def fix_spanish_barcode(text: str) -> str:
        """
        Quick fix for Spanish keyboard layout issue.

        Use this when scanner is US layout but Windows is Spanish.

        Example:
            Input:  "httpsÑ--www.blurams.com-app-1540795774407"
            Output: "https://www.blurams.com/app/1540795774407"

        Args:
            text: Barcode text with wrong characters

        Returns:
            Corrected barcode text
        """
        mapping = KeyboardMapper.ES_TO_US
        return ''.join(mapping.get(c, c) for c in text)

    @staticmethod
    def detect_layout_issue(text: str) -> Optional[str]:
        """
        Try to detect if text has keyboard layout issues.

        Args:
            text: Input text to analyze

        Returns:
            Suggested source layout if issue detected, None otherwise
        """
        # Spanish keyboard indicators - characters that appear when scanner
        # sends US scancodes but Windows uses Spanish layout
        spanish_indicators = {
            'Ñ': ':',   # Colon
            'ñ': ';',   # Semicolon
            'Ç': '|',   # Pipe
            'ç': '\\',  # Backslash
            '¿': '+',   # Plus
            '¡': '=',   # Equals
        }

        # Count Spanish keyboard artifacts
        spanish_count = sum(1 for c in text if c in spanish_indicators)

        # If we find any Spanish keyboard characters in what looks like
        # a barcode, URL, or structured data (has alphanumeric content)
        if spanish_count > 0:
            # Check if text has typical barcode/URL patterns when fixed
            has_alphanum = any(c.isalnum() for c in text)
            if has_alphanum:
                return 'qwerty_es'

        # Also check for specific patterns:
        # - Ç appearing as separator (like | in QR codes)
        # - ' appearing where - should be (Spanish keyboard)
        if 'Ç' in text and text.count('Ç') >= 2:
            # Multiple Ç suggests it's being used as a separator (|)
            return 'qwerty_es'

        # Check for URL pattern with Spanish keyboard issues
        if 'Ñ' in text and ('http' in text.lower() or 'www' in text.lower()):
            return 'qwerty_es'

        # Check for AZERTY indicators
        azerty_indicators = set('éèàù')
        azerty_count = sum(1 for c in text if c in azerty_indicators)
        if azerty_count > 0 and not text[0:1].isdigit():
            return 'azerty'

        return None

    @staticmethod
    def auto_fix(text: str) -> str:
        """
        Automatically detect and fix keyboard layout issues.

        Args:
            text: Input text that may have layout issues

        Returns:
            Fixed text if issue detected, original text otherwise
        """
        detected = KeyboardMapper.detect_layout_issue(text)

        if detected == 'qwerty_es':
            return KeyboardMapper.fix_spanish_barcode(text)
        elif detected == 'azerty':
            mapper = KeyboardMapper(system_layout='azerty')
            return mapper.map_to_qwerty(text)

        return text

    @staticmethod
    def fix_with_layout(text: str, layout: str) -> str:
        """
        Fix keyboard layout issues using a specific layout setting.

        Args:
            text: Input text that may have layout issues
            layout: The layout to use:
                - 'auto': Auto-detect and fix
                - 'qwerty_us': No conversion (scanner and system both US)
                - 'qwerty_es': Force Spanish to US conversion
                - 'azerty': Force AZERTY to US conversion
                - 'qwertz': Force QWERTZ to US conversion

        Returns:
            Fixed text
        """
        if not text:
            return text

        layout = layout.lower() if layout else 'auto'

        if layout == 'auto':
            return KeyboardMapper.auto_fix(text)
        elif layout == 'qwerty_us':
            # No conversion needed
            return text
        elif layout == 'qwerty_es':
            return KeyboardMapper.fix_spanish_barcode(text)
        elif layout == 'azerty':
            mapper = KeyboardMapper(system_layout='azerty')
            return mapper.map_to_qwerty(text)
        elif layout == 'qwertz':
            mapper = KeyboardMapper(system_layout='qwertz')
            return mapper.map_to_qwerty(text)
        else:
            # Unknown layout, try auto-fix
            return KeyboardMapper.auto_fix(text)

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
