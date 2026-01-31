"""Product repository for database operations."""

from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from database.connection import Database


@dataclass
class Product:
    """Product entity."""
    id: str
    name: str
    price: float
    description: str = ""
    vat_rate: float = 21.0
    barcode: Optional[str] = None
    stock: int = 0
    status: str = "active"
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_row(cls, row) -> 'Product':
        """Create Product from database row."""
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'] or "",
            price=row['price'],
            vat_rate=row['vat_rate'],
            barcode=row['barcode'],
            stock=row['stock'],
            status=row['status'],
            created_at=row['created_at']
        )


class ProductRepository:
    """Repository for product database operations."""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def get_all(self, include_inactive: bool = False) -> list[Product]:
        """Get all products, optionally including inactive."""
        if include_inactive:
            query = "SELECT * FROM products ORDER BY name"
            rows = self.db.fetchall(query)
        else:
            query = "SELECT * FROM products WHERE status = 'active' ORDER BY name"
            rows = self.db.fetchall(query)
        return [Product.from_row(row) for row in rows]

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        row = self.db.fetchone(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
        return Product.from_row(row) if row else None

    def get_by_barcode(self, barcode: str) -> Optional[Product]:
        """Get product by barcode."""
        row = self.db.fetchone(
            "SELECT * FROM products WHERE barcode = ?",
            (barcode,)
        )
        return Product.from_row(row) if row else None

    def search(self, query: str) -> list[Product]:
        """Search products by name or barcode."""
        search_term = f"%{query}%"
        rows = self.db.fetchall(
            """
            SELECT * FROM products
            WHERE status = 'active'
            AND (name LIKE ? OR barcode LIKE ? OR id LIKE ?)
            ORDER BY name
            LIMIT 50
            """,
            (search_term, search_term, search_term)
        )
        return [Product.from_row(row) for row in rows]

    def create(self, product: Product) -> Product:
        """Create a new product."""
        self.db.execute(
            """
            INSERT INTO products (id, name, description, price, vat_rate, barcode, stock, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product.id,
                product.name,
                product.description,
                product.price,
                product.vat_rate,
                product.barcode,
                product.stock,
                product.status
            )
        )
        return self.get_by_id(product.id)

    def update(self, product: Product) -> Product:
        """Update an existing product."""
        self.db.execute(
            """
            UPDATE products
            SET name = ?, description = ?, price = ?, vat_rate = ?,
                barcode = ?, stock = ?, status = ?
            WHERE id = ?
            """,
            (
                product.name,
                product.description,
                product.price,
                product.vat_rate,
                product.barcode,
                product.stock,
                product.status,
                product.id
            )
        )
        return self.get_by_id(product.id)

    def delete(self, product_id: str) -> bool:
        """Soft delete a product by setting status to inactive."""
        self.db.execute(
            "UPDATE products SET status = 'inactive' WHERE id = ?",
            (product_id,)
        )
        return True

    def hard_delete(self, product_id: str) -> bool:
        """Permanently delete a product."""
        self.db.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        )
        return True

    def update_stock(self, product_id: str, quantity_change: int) -> Optional[Product]:
        """Update product stock by a delta amount."""
        self.db.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (quantity_change, product_id)
        )
        return self.get_by_id(product_id)

    def bulk_create(self, products: list[Product]) -> int:
        """Bulk create products, returns count of created."""
        created = 0
        for product in products:
            try:
                self.create(product)
                created += 1
            except Exception:
                # Skip duplicates
                pass
        return created
