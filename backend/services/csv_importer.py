"""CSV importer for bulk product import."""

import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class ImportError:
    """Single import error."""
    row: int
    field: str
    message: str


@dataclass
class ImportResult:
    """Result of CSV import operation."""
    success: bool
    total_rows: int = 0
    imported: int = 0
    skipped: int = 0
    errors: list[ImportError] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'total_rows': self.total_rows,
            'imported': self.imported,
            'skipped': self.skipped,
            'errors': [
                {'row': e.row, 'field': e.field, 'message': e.message}
                for e in self.errors
            ],
            'message': self.message
        }


class CSVImporter:
    """Import products from CSV files."""

    # Required columns
    REQUIRED_COLUMNS = {'name', 'price'}

    # Optional columns with defaults
    OPTIONAL_COLUMNS = {
        'id': None,  # Auto-generate if missing
        'description': '',
        'vat_rate': 21.0,
        'barcode': None,
        'stock': 0,
        'status': 'active'
    }

    # Column aliases (alternative names)
    COLUMN_ALIASES = {
        'product_name': 'name',
        'product_id': 'id',
        'sku': 'id',
        'unit_price': 'price',
        'vat': 'vat_rate',
        'tax_rate': 'vat_rate',
        'qty': 'stock',
        'quantity': 'stock',
        'ean': 'barcode',
        'upc': 'barcode',
    }

    def __init__(self, product_repository):
        """
        Initialize importer.

        Args:
            product_repository: Repository for saving products
        """
        self.product_repo = product_repository

    def import_csv(
        self,
        file_path: str,
        skip_duplicates: bool = True,
        update_existing: bool = False
    ) -> ImportResult:
        """
        Import products from CSV file.

        Args:
            file_path: Path to CSV file
            skip_duplicates: Skip products with duplicate barcodes
            update_existing: Update existing products instead of skipping

        Returns:
            ImportResult with import statistics
        """
        path = Path(file_path)

        if not path.exists():
            return ImportResult(
                success=False,
                message=f"File not found: {file_path}"
            )

        try:
            # Detect encoding and delimiter
            with open(path, 'r', encoding='utf-8-sig') as f:
                sample = f.read(4096)
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                f.seek(0)
                reader = csv.DictReader(f, dialect=dialect)

                # Normalize column names
                if reader.fieldnames:
                    reader.fieldnames = [self._normalize_column(c) for c in reader.fieldnames]

                # Validate required columns
                missing = self.REQUIRED_COLUMNS - set(reader.fieldnames or [])
                if missing:
                    return ImportResult(
                        success=False,
                        message=f"Missing required columns: {', '.join(missing)}"
                    )

                return self._process_rows(reader, skip_duplicates, update_existing)

        except UnicodeDecodeError:
            # Try with latin-1 encoding
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        reader.fieldnames = [self._normalize_column(c) for c in reader.fieldnames]
                    return self._process_rows(reader, skip_duplicates, update_existing)
            except Exception as e:
                return ImportResult(
                    success=False,
                    message=f"Could not read file: {str(e)}"
                )

        except Exception as e:
            return ImportResult(
                success=False,
                message=f"Import failed: {str(e)}"
            )

    def _normalize_column(self, column: str) -> str:
        """Normalize column name to standard format."""
        col = column.lower().strip()
        return self.COLUMN_ALIASES.get(col, col)

    def _process_rows(
        self,
        reader: csv.DictReader,
        skip_duplicates: bool,
        update_existing: bool
    ) -> ImportResult:
        """Process CSV rows and import products."""
        result = ImportResult(success=True)
        errors = []

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            result.total_rows += 1

            # Validate and parse row
            product_data, row_errors = self._parse_row(row, row_num)

            if row_errors:
                errors.extend(row_errors)
                result.skipped += 1
                continue

            # Check for existing product
            existing = None
            if product_data.get('barcode'):
                existing = self.product_repo.get_by_barcode(product_data['barcode'])
            if not existing and product_data.get('id'):
                existing = self.product_repo.get_by_id(product_data['id'])

            if existing:
                if update_existing:
                    # Update existing product
                    from database.repositories.products import Product
                    product = Product(
                        id=existing.id,
                        name=product_data['name'],
                        description=product_data.get('description', ''),
                        price=product_data['price'],
                        vat_rate=product_data.get('vat_rate', 21.0),
                        barcode=product_data.get('barcode'),
                        stock=product_data.get('stock', 0),
                        status=product_data.get('status', 'active')
                    )
                    self.product_repo.update(product)
                    result.imported += 1
                elif skip_duplicates:
                    result.skipped += 1
                else:
                    errors.append(ImportError(
                        row=row_num,
                        field='barcode' if product_data.get('barcode') else 'id',
                        message='Duplicate product'
                    ))
                    result.skipped += 1
            else:
                # Create new product
                from database.repositories.products import Product

                product_id = product_data.get('id') or self._generate_id()

                product = Product(
                    id=product_id,
                    name=product_data['name'],
                    description=product_data.get('description', ''),
                    price=product_data['price'],
                    vat_rate=product_data.get('vat_rate', 21.0),
                    barcode=product_data.get('barcode'),
                    stock=product_data.get('stock', 0),
                    status=product_data.get('status', 'active')
                )

                try:
                    self.product_repo.create(product)
                    result.imported += 1
                except Exception as e:
                    errors.append(ImportError(
                        row=row_num,
                        field='',
                        message=str(e)
                    ))
                    result.skipped += 1

        result.errors = errors
        result.success = result.imported > 0 or result.total_rows == 0
        result.message = f"Imported {result.imported} of {result.total_rows} products"

        return result

    def _parse_row(self, row: dict, row_num: int) -> tuple[dict, list[ImportError]]:
        """Parse and validate a single row."""
        data = {}
        errors = []

        # Required: name
        name = row.get('name', '').strip()
        if not name:
            errors.append(ImportError(row_num, 'name', 'Name is required'))
        else:
            data['name'] = name

        # Required: price
        price_str = row.get('price', '').strip()
        try:
            price = float(price_str.replace(',', '.').replace('€', '').replace('$', ''))
            if price < 0:
                errors.append(ImportError(row_num, 'price', 'Price must be positive'))
            else:
                data['price'] = price
        except ValueError:
            errors.append(ImportError(row_num, 'price', f'Invalid price: {price_str}'))

        # Optional fields
        if 'id' in row and row['id'].strip():
            data['id'] = row['id'].strip()

        if 'description' in row:
            data['description'] = row['description'].strip()

        if 'vat_rate' in row and row['vat_rate'].strip():
            try:
                vat = float(row['vat_rate'].replace(',', '.').replace('%', ''))
                if 0 <= vat <= 100:
                    data['vat_rate'] = vat
            except ValueError:
                pass

        if 'barcode' in row and row['barcode'].strip():
            data['barcode'] = row['barcode'].strip()

        if 'stock' in row and row['stock'].strip():
            try:
                data['stock'] = int(row['stock'])
            except ValueError:
                pass

        if 'status' in row and row['status'].strip():
            status = row['status'].strip().lower()
            if status in ('active', 'inactive'):
                data['status'] = status

        return data, errors

    def _generate_id(self) -> str:
        """Generate a unique product ID."""
        return f"PROD-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def get_template() -> str:
        """Get CSV template content."""
        return """id,name,description,price,vat_rate,barcode,stock,status
PROD001,Widget,A useful widget,9.99,21.0,1234567890123,100,active
PROD002,Gadget,A cool gadget,19.99,21.0,1234567890124,50,active
PROD003,Thing,A thing,5.99,21.0,1234567890125,200,active"""

    def save_template(self, path: str) -> Path:
        """Save CSV template to file."""
        template_path = Path(path)
        template_path.write_text(self.get_template())
        return template_path
