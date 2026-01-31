# Open Invoice POS

A Point-of-Sale desktop application for small businesses, featuring thermal printer support, barcode scanner integration, and tamper-proof invoice verification via hash chains.

## Features

- **Invoice Management**: Create, view, and manage invoices with automatic numbering
- **Thermal Printer Support**: Print receipts on 58mm thermal printers (ESC/POS compatible)
- **Barcode Scanner Integration**: Scan product barcodes with automatic keyboard layout detection (US/Spanish/French/German)
- **QR Code Verification**: Each invoice includes a QR code for authenticity verification
- **Hash Chain Security**: Invoices are linked via SHA-256 hash chain to prevent tampering
- **PDF Generation**: Automatic PDF receipt generation saved to user's documents
- **Product Management**: Add, edit, and import products from CSV
- **Sales Reports**: Daily and period sales reports with CSV export
- **Multi-language Keyboard Support**: Automatic detection and correction of barcode scanner keyboard layout issues

## Tech Stack

- **Backend**: Python 3.11+ with pywebview
- **Frontend**: React + TypeScript + Vite
- **Database**: SQLite
- **Printing**: python-escpos + win32print (Windows native)
- **PDF**: ReportLab

## Requirements

- Windows 10/11
- Python 3.11 or higher
- Node.js 18+ (for frontend development)
- 58mm USB Thermal Printer (optional)
- USB Barcode Scanner (optional)

## Installation

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
npm run build
```

### Running the Application

```bash
# From project root
.venv\Scripts\python backend\main.py
```

## Thermal Printer Setup (Windows)

1. Connect your USB thermal printer
2. Open **Devices and Printers** in Windows
3. Add a new printer: **Generic / Text Only** driver pointing to **USB001** port
4. Name it **"POS Receipt Printer"** (auto-detected by the app)

## Project Structure

```
OpenInvoice/
├── backend/
│   ├── api/           # pywebview API bridge
│   ├── core/          # Hash chain, QR generation, keyboard mapper
│   ├── database/      # SQLite connection, migrations, repositories
│   ├── services/      # Printer, PDF, email, CSV import, reports
│   └── main.py        # Application entry point
├── frontend/
│   ├── src/           # React components and pages
│   └── dist/          # Built frontend (loaded by pywebview)
└── docs/              # Architecture and task documentation
```

## Configuration

Settings are stored in the SQLite database and can be configured via the Settings page:

- Store name and seller ID
- Currency symbol
- Default VAT rate
- SMTP settings for email receipts
- Printer selection

## Data Storage

- **Database**: `%APPDATA%/OpenInvoice/openinvoice.db`
- **PDF Receipts**: `%APPDATA%/OpenInvoice/receipts/`

## License

Apache License 2.0

## Contributing

Contributions are welcome! Please read the documentation in `/docs` for architecture details and task lists.
