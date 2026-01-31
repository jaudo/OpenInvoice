# Backend Tasks - Open Invoice POS

## Overview

This document contains prioritized backend tasks for the Open Invoice POS system. Each task includes acceptance criteria and implementation notes.

---

## B1: Project Setup

**Priority:** Critical (Foundation)

### Tasks
- [ ] Create folder structure (api/, core/, database/, services/)
- [ ] Create requirements.txt with all dependencies
- [ ] Create virtual environment setup script
- [ ] Create __init__.py files for all packages

### Acceptance Criteria
- Running `pip install -r requirements.txt` installs all dependencies
- All imports work correctly between modules
- Project runs without import errors

### Dependencies
```
pywebview>=5.0
qrcode[pil]>=7.4
python-escpos>=3.1
reportlab>=4.0
pydantic>=2.0
pyinstaller>=6.0
```

---

## B2: Database Layer

**Priority:** Critical (Data Foundation)

### Tasks
- [ ] Implement connection.py with SQLite connection manager
- [ ] Implement migrations.py with all table creation
- [ ] Implement repositories/products.py
- [ ] Implement repositories/invoices.py
- [ ] Implement repositories/settings.py
- [ ] Implement repositories/audit.py

### Acceptance Criteria
- Database file created automatically if not exists
- All tables created with correct schema
- CRUD operations work for all entities
- Foreign key constraints enforced

### Schema Reference
```sql
-- See docs/architecture.md for full schema
```

### Repository Interface Pattern
```python
class ProductRepository:
    def get_all() -> list[Product]
    def get_by_id(id: str) -> Product | None
    def get_by_barcode(barcode: str) -> Product | None
    def search(query: str) -> list[Product]
    def create(product: Product) -> Product
    def update(product: Product) -> Product
    def delete(id: str) -> bool
```

---

## B3: Hash Chain Implementation

**Priority:** Critical (Core Security)

### Tasks
- [ ] Implement hash_chain.py with SHA-256 hashing
- [ ] Create function to calculate invoice hash
- [ ] Create function to get previous hash
- [ ] Create function to verify single invoice
- [ ] Create function to verify entire chain

### Acceptance Criteria
- Hash calculation is deterministic (same input = same hash)
- Hash includes: invoice_number, seller_id, total, items, timestamp, previous_hash
- Chain verification detects any tampering
- First invoice has previous_hash = "GENESIS"

### Implementation
```python
import hashlib
import json

def calculate_hash(invoice_data: dict, previous_hash: str) -> str:
    """Calculate SHA-256 hash for invoice."""
    data_string = json.dumps({
        'invoice_number': invoice_data['invoice_number'],
        'seller_id': invoice_data['seller_id'],
        'total': invoice_data['total'],
        'items': invoice_data['items'],
        'timestamp': invoice_data['created_at'],
        'previous_hash': previous_hash
    }, sort_keys=True)
    return hashlib.sha256(data_string.encode()).hexdigest()

def verify_chain() -> tuple[bool, str | None]:
    """Verify entire hash chain. Returns (valid, error_message)."""
    pass
```

---

## B4: QR System

**Priority:** Critical (Core Feature)

### Tasks
- [ ] Implement qr_generator.py
- [ ] Create QR encoding format
- [ ] Generate QR as base64 PNG
- [ ] Implement qr_validator.py
- [ ] Parse and validate QR data

### Acceptance Criteria
- QR contains: version, invoice_number, total, hash_prefix, timestamp
- QR can be decoded and verified
- Invalid QR returns clear error message
- QR size suitable for thermal printer (small but scannable)

### QR Format
```
OPENINVOICE|v1|{invoice_number}|{total}|{hash_first_8}|{timestamp}
```

### Implementation
```python
import qrcode
import base64
from io import BytesIO

def generate_qr(invoice: Invoice) -> str:
    """Generate QR code as base64 PNG string."""
    qr_data = f"OPENINVOICE|v1|{invoice.invoice_number}|{invoice.total}|{invoice.current_hash[:8]}|{invoice.timestamp}"

    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def validate_qr(qr_data: str) -> dict:
    """Validate QR data against database."""
    pass
```

---

## B5: Thermal Printer Service

**Priority:** High (Hardware Integration)

### Tasks
- [ ] Implement printer.py with ESC/POS support
- [ ] Auto-detect USB printer
- [ ] Format receipt for 58mm paper
- [ ] Print QR code on receipt
- [ ] Handle printer errors gracefully

### Acceptance Criteria
- Printer detected automatically via USB
- Receipt formatted correctly for Bisofice 58mm
- QR code prints clearly and is scannable
- Graceful fallback if printer not connected

### Implementation
```python
from escpos.printer import Usb

class ThermalPrinter:
    def __init__(self):
        self.printer = None
        self._connect()

    def _connect(self):
        try:
            # Bisofice typical VID/PID
            self.printer = Usb(0x0416, 0x5011)
        except Exception:
            self.printer = None

    def print_receipt(self, invoice: Invoice, qr_base64: str):
        if not self.printer:
            raise PrinterNotConnectedError()

        self.printer.set(align='center')
        self.printer.text(f"{invoice.store_name}\n")
        self.printer.text("=" * 32 + "\n")
        # ... format items
        self.printer.image(qr_image)
        self.printer.cut()
```

---

## B6: PDF Generation

**Priority:** High (Export Feature)

### Tasks
- [ ] Implement pdf_generator.py with ReportLab
- [ ] Create receipt template
- [ ] Embed QR code in PDF
- [ ] Support A4 and receipt formats
- [ ] Return PDF as bytes or save to temp file

### Acceptance Criteria
- PDF includes all invoice details
- QR code embedded and scannable
- Professional appearance
- File size reasonable (<500KB)

---

## B7: Email Service

**Priority:** Medium (Communication)

### Tasks
- [ ] Implement email_service.py with SMTP
- [ ] Support TLS/SSL
- [ ] Attach PDF receipt
- [ ] Use HTML email template
- [ ] Store SMTP config in settings

### Acceptance Criteria
- Email sent successfully via SMTP
- PDF attached correctly
- HTML email renders properly
- Failed sends logged with error

### Configuration
```python
SMTP_SETTINGS = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'username': '',
    'password': '',  # App password
    'use_tls': True,
    'from_name': 'Open Invoice',
    'from_email': ''
}
```

---

## B8: CSV Importer

**Priority:** Medium (Data Import)

### Tasks
- [ ] Implement csv_importer.py
- [ ] Define CSV template format
- [ ] Validate CSV data
- [ ] Handle duplicates (update vs skip)
- [ ] Return import summary

### Acceptance Criteria
- CSV with headers: id, name, description, price, vat_rate, barcode, stock
- Validation errors reported per row
- Duplicate barcodes handled gracefully
- Import summary shows success/failed counts

### CSV Template
```csv
id,name,description,price,vat_rate,barcode,stock
PROD001,Widget,A useful widget,9.99,21.0,1234567890123,100
PROD002,Gadget,A cool gadget,19.99,21.0,1234567890124,50
```

---

## B9: Keyboard Mapper

**Priority:** Low (Scanner Support)

### Tasks
- [ ] Implement keyboard_mapper.py
- [ ] Define layout configurations
- [ ] Support QWERTY, AZERTY, QWERTZ
- [ ] Map scanner output to correct characters

### Acceptance Criteria
- Scanner with non-QWERTY layout detected correctly
- Barcode characters mapped properly
- User can select layout in settings

---

## B10: API Bridge

**Priority:** Critical (Frontend Integration)

### Tasks
- [ ] Implement bridge.py with API class
- [ ] All methods return {success, data, error} format
- [ ] Proper error handling for all endpoints
- [ ] Type hints for all parameters

### Acceptance Criteria
- All API methods from contract implemented
- Consistent response format
- Errors caught and returned properly
- No unhandled exceptions reach frontend

### Implementation
```python
class API:
    def __init__(self):
        self.db = Database()
        self.printer = ThermalPrinter()
        self.pdf = PDFGenerator()
        self.email = EmailService()

    def _response(self, success: bool, data=None, error=None) -> dict:
        return {'success': success, 'data': data, 'error': error}

    # Products
    def products_get_all(self) -> dict:
        try:
            products = self.db.products.get_all()
            return self._response(True, [p.to_dict() for p in products])
        except Exception as e:
            return self._response(False, error=str(e))

    # ... implement all methods
```

---

## B11: Main Entry Point

**Priority:** Critical (Application Launch)

### Tasks
- [ ] Implement main.py with pywebview
- [ ] Load frontend from dist folder
- [ ] Initialize API and expose to JS
- [ ] Handle window events
- [ ] Setup data directory

### Acceptance Criteria
- Application window opens correctly
- Frontend loads from bundled files
- API accessible via window.pywebview.api
- Graceful shutdown on close

### Implementation
```python
import webview
import os
import sys

def get_resource_path(relative_path):
    """Get path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

def main():
    api = API()

    frontend_path = get_resource_path('frontend/dist/index.html')

    window = webview.create_window(
        'Open Invoice',
        frontend_path,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600)
    )

    webview.start()

if __name__ == '__main__':
    main()
```

---

## B12: Anti-fraud / Return Tracking

**Priority:** High (Business Logic)

### Tasks
- [ ] Track item return status in invoice_items
- [ ] Prevent double returns
- [ ] Update invoice status on return
- [ ] Log all return actions

### Acceptance Criteria
- Items can only be returned once
- Partial returns supported
- Invoice status updated (completed → partial_return → returned)
- Audit log entry created for each return

---

## B13: Audit Logging

**Priority:** Medium (Compliance)

### Tasks
- [ ] Implement audit logging in repositories
- [ ] Log: invoice_create, invoice_return, settings_change
- [ ] Include user/timestamp/details
- [ ] Query audit log by entity

### Acceptance Criteria
- All significant actions logged
- Timestamps in ISO format
- Details stored as JSON
- Queryable by entity type/id

---

## B14: Reports Service

**Priority:** Medium (Analytics)

### Tasks
- [ ] Implement reports service
- [ ] Daily sales summary (total, count, by payment method)
- [ ] Period sales (date range aggregation)
- [ ] Top selling products
- [ ] Export to CSV

### Acceptance Criteria
- Daily report shows: total sales, invoice count, breakdown by payment
- Period report aggregates by day
- Top products shows quantity and revenue
- CSV export for all report types

### Implementation
```python
class ReportsService:
    def daily_sales(self, date: str) -> dict:
        """Get sales summary for specific date."""
        pass

    def period_sales(self, start: str, end: str) -> dict:
        """Get sales summary for date range."""
        pass

    def top_products(self, limit: int = 10) -> list:
        """Get top selling products."""
        pass

    def export_csv(self, report_type: str, params: dict) -> str:
        """Export report to CSV, return file path."""
        pass
```

---

## B15: PyInstaller Build

**Priority:** Low (Deployment)

### Tasks
- [ ] Create PyInstaller spec file
- [ ] Bundle frontend dist folder
- [ ] Include all Python dependencies
- [ ] Test on clean Windows install
- [ ] Create build script

### Acceptance Criteria
- Single .exe file generated
- Runs on Windows without Python installed
- Frontend loads correctly
- Database created in user data folder

### Build Command
```bash
pyinstaller --onefile --windowed \
    --add-data "frontend/dist;frontend/dist" \
    --add-data "data;data" \
    --name "OpenInvoice" \
    --icon "assets/icon.ico" \
    backend/main.py
```

---

## Testing Checklist

### Unit Tests
- [ ] Hash chain calculation
- [ ] QR generation/validation
- [ ] Repository CRUD operations
- [ ] CSV import validation

### Integration Tests
- [ ] Create invoice → verify hash chain
- [ ] Print receipt → verify output
- [ ] Generate PDF → verify content
- [ ] Send email → verify delivery

### Manual Tests
- [ ] Full purchase flow with thermal printer
- [ ] QR scan and validation
- [ ] Return processing
- [ ] Settings persistence
