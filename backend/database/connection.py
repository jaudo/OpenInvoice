"""SQLite connection manager for Open Invoice."""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "openinvoice.db"


class Database:
    """SQLite database connection manager."""

    _instance: Optional['Database'] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls, db_path: Optional[Path] = None):
        """Singleton pattern for database connection."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db_path = db_path or DEFAULT_DB_PATH
            cls._instance._ensure_directory()
        return cls._instance

    def _ensure_directory(self):
        """Ensure the data directory exists."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    @contextmanager
    def cursor(self):
        """Context manager for database cursor."""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor."""
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """Execute a query with multiple parameter sets."""
        with self.cursor() as cur:
            cur.executemany(query, params_list)
            return cur

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result

    def fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute query and fetch all results."""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing)."""
        if cls._instance and cls._instance._connection:
            cls._instance._connection.close()
        cls._instance = None
        cls._connection = None
