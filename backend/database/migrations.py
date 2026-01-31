"""Database schema migrations for Open Invoice."""

from .connection import Database


SCHEMA_VERSION = 1

MIGRATIONS = [
    # Version 1: Initial schema
    """
    -- Products table
    CREATE TABLE IF NOT EXISTS products (
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

    -- Invoices table with hash chain
    CREATE TABLE IF NOT EXISTS invoices (
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
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Invoice items
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        vat_rate REAL NOT NULL,
        line_total REAL NOT NULL,
        return_status TEXT DEFAULT 'none',
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    -- Settings
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    -- Audit log
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Schema version tracking
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
    CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
    CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);
    CREATE INDEX IF NOT EXISTS idx_invoices_created ON invoices(created_at);
    CREATE INDEX IF NOT EXISTS idx_invoices_hash ON invoices(current_hash);
    CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
    CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
    """,
]


def get_current_version(db: Database) -> int:
    """Get current schema version from database."""
    try:
        result = db.fetchone("SELECT MAX(version) as version FROM schema_version")
        return result['version'] if result and result['version'] else 0
    except Exception:
        return 0


def run_migrations(db: Database = None) -> int:
    """Run pending database migrations."""
    if db is None:
        db = Database()

    current_version = get_current_version(db)

    for version, migration in enumerate(MIGRATIONS, start=1):
        if version > current_version:
            # Execute migration (may contain multiple statements)
            for statement in migration.split(';'):
                statement = statement.strip()
                if statement:
                    db.execute(statement)

            # Record version
            db.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (version,)
            )

    return len(MIGRATIONS)


def insert_default_settings(db: Database = None):
    """Insert default settings if not exist."""
    if db is None:
        db = Database()

    defaults = {
        'language': 'en',
        'store_name': 'My Store',
        'seller_id': 'SELLER001',
        'printer_enabled': 'false',
        'smtp_host': '',
        'smtp_port': '587',
        'smtp_username': '',
        'smtp_password': '',
        'smtp_use_tls': 'true',
        'keyboard_layout': 'qwerty',
        'currency_symbol': '€',
        'default_vat_rate': '21.0',
    }

    for key, value in defaults.items():
        db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )


def initialize_database(db: Database = None) -> None:
    """Initialize database with schema and default data."""
    if db is None:
        db = Database()

    run_migrations(db)
    insert_default_settings(db)
