# Open Invoice POS System - Architecture

## Overview

Open Invoice is a lightweight Point of Sale (POS) system designed for small businesses. It features:

- **Thermal printer support** (ESC/POS protocol)
- **QR-based receipts** with blockchain-style hash chain for authenticity verification
- **Multi-language support** (EN, ES, DE, FR, IT, PT, NL)
- **Single executable distribution** via PyInstaller

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Single Executable                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    pywebview Window                        │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              React Frontend (Vite)                   │  │  │
│  │  │  ┌─────────┐ ┌──────┐ ┌──────────┐ ┌───────┐ ┌────┐ │  │  │
│  │  │  │ Invoice │ │ Scan │ │ Products │ │Reports│ │Conf│ │  │  │
│  │  │  └────┬────┘ └──┬───┘ └────┬─────┘ └───┬───┘ └─┬──┘ │  │  │
│  │  │       │         │          │           │       │     │  │  │
│  │  │       └─────────┴──────────┴───────────┴───────┘     │  │  │
│  │  │                        │                              │  │  │
│  │  │              window.pywebview.api                     │  │  │
│  │  └─────────────────────────┬─────────────────────────────┘  │  │
│  └────────────────────────────┼────────────────────────────────┘  │
│                               │                                    │
│  ┌────────────────────────────▼────────────────────────────────┐  │
│  │                   Python Backend                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │  │
│  │  │   API    │  │   Core   │  │ Services │  │ Database │    │  │
│  │  │  Bridge  │──│HashChain │──│ Printer  │──│  SQLite  │    │  │
│  │  │          │  │   QR     │  │   PDF    │  │          │    │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
Open Invoice/
├── backend/
│   ├── api/
│   │   └── bridge.py           # pywebview API exposed to JS
│   ├── core/
│   │   ├── hash_chain.py       # Blockchain-style receipt hashing
│   │   ├── qr_generator.py     # QR code generation
│   │   ├── qr_validator.py     # QR code validation
│   │   └── keyboard_mapper.py  # Scanner keyboard layouts
│   ├── database/
│   │   ├── connection.py       # SQLite connection manager
│   │   ├── migrations.py       # Schema creation
│   │   └── repositories/       # Data access layer
│   │       ├── products.py
│   │       ├── invoices.py
│   │       └── settings.py
│   ├── services/
│   │   ├── printer.py          # Thermal printer (ESC/POS)
│   │   ├── pdf_generator.py    # PDF receipts
│   │   ├── email_service.py    # SMTP email
│   │   └── csv_importer.py     # Product import
│   ├── main.py                 # Entry point with pywebview
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── bridge.ts       # pywebview API wrapper
│   │   │   └── mock.ts         # Mock API for development
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   └── common/         # Shared components
│   │   ├── pages/
│   │   │   ├── InvoicePage.tsx
│   │   │   ├── ScanPage.tsx
│   │   │   ├── ProductsPage.tsx
│   │   │   ├── ReportsPage.tsx
│   │   │   └── ConfigPage.tsx
│   │   ├── i18n/
│   │   │   └── locales/
│   │   ├── stores/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── architecture.md
│   ├── backend_tasks.md
│   └── frontend_tasks.md
└── data/
    └── openinvoice.db
```

## Data Flow

### Invoice Creation Flow

```
1. User adds products to cart (Frontend)
        │
        ▼
2. Checkout triggered → invoices_create() API call
        │
        ▼
3. Backend calculates totals, VAT
        │
        ▼
4. Hash chain: SHA-256(prev_hash + invoice_data)
        │
        ▼
5. QR code generated with verification data
        │
        ▼
6. Invoice stored in SQLite
        │
        ▼
7. Receipt printed/PDF generated
        │
        ▼
8. Response with invoice data + QR returned to frontend
```

### QR Validation Flow

```
1. User scans QR code (Scan tab)
        │
        ▼
2. qr_validate() API call with QR data
        │
        ▼
3. Backend decodes QR, extracts invoice_number + hash
        │
        ▼
4. Lookup invoice in database
        │
        ▼
5. Recalculate hash, compare with stored
        │
        ▼
6. Verify hash chain integrity
        │
        ▼
7. Return validation result + invoice details
```

## Database Schema

### Products Table
```sql
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    vat_rate REAL DEFAULT 21.0,
    barcode TEXT UNIQUE,
    stock INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Invoices Table (with Hash Chain)
```sql
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    seller_id TEXT NOT NULL,
    store_name TEXT NOT NULL,
    subtotal REAL NOT NULL,
    vat_amount REAL NOT NULL,
    total REAL NOT NULL,
    payment_method TEXT,
    customer_email TEXT,
    previous_hash TEXT,
    current_hash TEXT NOT NULL,
    qr_data TEXT NOT NULL,
    status TEXT DEFAULT 'completed',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (previous_hash) REFERENCES invoices(current_hash)
);
```

### Invoice Items Table
```sql
CREATE TABLE invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    vat_rate REAL NOT NULL,
    line_total REAL NOT NULL,
    return_status TEXT DEFAULT 'none',
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### Settings Table
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### Audit Log Table
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## API Contract

All API methods return: `{success: boolean, data?: any, error?: string}`

### Products
- `products_get_all()` - List all active products
- `products_search(query)` - Search by name/barcode
- `products_import_csv(path)` - Import products from CSV

### Invoices
- `invoices_create(items, payment_method, customer)` - Create new invoice
- `invoices_get_by_number(number)` - Retrieve specific invoice
- `invoices_process_return(invoice_number, item_ids)` - Process return

### Validation
- `qr_validate(qr_data)` - Validate receipt authenticity
- `hash_chain_verify()` - Full chain integrity check

### Printing/Export
- `print_receipt(invoice_id)` - Print to thermal printer
- `generate_pdf(invoice_id)` - Generate PDF receipt
- `send_email(invoice_id, email)` - Email receipt

### Settings
- `settings_get_all()` - Get all settings
- `settings_update(key, value)` - Update setting
- `get_keyboard_layouts()` - Get scanner layouts

### Reports
- `reports_daily_sales(date)` - Daily sales summary
- `reports_period_sales(start, end)` - Period sales
- `reports_top_products(limit)` - Best sellers
- `reports_export_csv(report_type, params)` - Export data

## Hash Chain Implementation

The hash chain ensures receipt authenticity and prevents tampering:

```python
def calculate_hash(invoice_data: dict, previous_hash: str) -> str:
    """
    Creates SHA-256 hash of invoice data linked to previous invoice.
    """
    data_string = json.dumps({
        'invoice_number': invoice_data['invoice_number'],
        'seller_id': invoice_data['seller_id'],
        'total': invoice_data['total'],
        'items': invoice_data['items'],
        'timestamp': invoice_data['created_at'],
        'previous_hash': previous_hash
    }, sort_keys=True)

    return hashlib.sha256(data_string.encode()).hexdigest()
```

### QR Code Content
```
OPENINVOICE|v1|{invoice_number}|{total}|{hash_first_8}|{timestamp}
```

Example: `OPENINVOICE|v1|INV-2024-0001|125.50|a3f2c891|1706745600`

## Security Considerations

1. **Hash Chain Integrity**: Each invoice links to previous, making tampering detectable
2. **QR Verification**: Hash in QR must match recalculated hash
3. **Audit Logging**: All significant actions logged for compliance
4. **Return Tracking**: Items marked as returned cannot be returned again

## Technology Stack

### Backend
- Python 3.11+
- pywebview 5.0+
- SQLite (file-based database)
- qrcode (QR generation)
- python-escpos (thermal printer)
- reportlab (PDF generation)
- PyInstaller (executable bundling)

### Frontend
- React 18
- TypeScript 5
- Vite 5
- Tailwind CSS 3
- Zustand (state management)
- react-i18next (internationalization)
- Recharts (analytics charts)
- Radix UI (accessible components)

## Deployment

Single executable via PyInstaller:
```bash
pyinstaller --onefile --windowed --add-data "frontend/dist:frontend/dist" main.py
```

The executable bundles:
- Python runtime
- All Python dependencies
- Built frontend assets
- Default configuration
