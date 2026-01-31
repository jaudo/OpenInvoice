"""Settings repository for database operations."""

from typing import Optional, Any
import json

from ..connection import Database


class SettingsRepository:
    """Repository for application settings."""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def get(self, key: str) -> Optional[str]:
        """Get a single setting value."""
        row = self.db.fetchone(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        return row['value'] if row else None

    def get_typed(self, key: str, type_func: callable = str, default: Any = None) -> Any:
        """Get a setting with type conversion."""
        value = self.get(key)
        if value is None:
            return default
        try:
            if type_func == bool:
                return value.lower() in ('true', '1', 'yes')
            return type_func(value)
        except (ValueError, TypeError):
            return default

    def get_all(self) -> dict[str, str]:
        """Get all settings as a dictionary."""
        rows = self.db.fetchall("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in rows}

    def get_all_typed(self) -> dict[str, Any]:
        """Get all settings with appropriate type conversion."""
        raw = self.get_all()

        # Define type mappings
        type_map = {
            'printer_enabled': bool,
            'smtp_port': int,
            'smtp_use_tls': bool,
            'default_vat_rate': float,
        }

        result = {}
        for key, value in raw.items():
            if key in type_map:
                type_func = type_map[key]
                if type_func == bool:
                    result[key] = value.lower() in ('true', '1', 'yes')
                else:
                    try:
                        result[key] = type_func(value)
                    except (ValueError, TypeError):
                        result[key] = value
            else:
                result[key] = value

        return result

    def set(self, key: str, value: Any) -> None:
        """Set a single setting value."""
        # Convert non-string values
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif not isinstance(value, str):
            value = str(value)

        self.db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )

    def set_many(self, settings: dict[str, Any]) -> None:
        """Set multiple settings at once."""
        for key, value in settings.items():
            self.set(key, value)

    def delete(self, key: str) -> bool:
        """Delete a setting."""
        self.db.execute(
            "DELETE FROM settings WHERE key = ?",
            (key,)
        )
        return True

    # Convenience methods for common settings
    @property
    def language(self) -> str:
        return self.get('language') or 'en'

    @language.setter
    def language(self, value: str):
        self.set('language', value)

    @property
    def store_name(self) -> str:
        return self.get('store_name') or 'My Store'

    @store_name.setter
    def store_name(self, value: str):
        self.set('store_name', value)

    @property
    def seller_id(self) -> str:
        return self.get('seller_id') or 'SELLER001'

    @seller_id.setter
    def seller_id(self, value: str):
        self.set('seller_id', value)

    @property
    def printer_enabled(self) -> bool:
        return self.get_typed('printer_enabled', bool, False)

    @printer_enabled.setter
    def printer_enabled(self, value: bool):
        self.set('printer_enabled', value)

    @property
    def currency_symbol(self) -> str:
        return self.get('currency_symbol') or '€'

    @currency_symbol.setter
    def currency_symbol(self, value: str):
        self.set('currency_symbol', value)

    @property
    def default_vat_rate(self) -> float:
        return self.get_typed('default_vat_rate', float, 21.0)

    @default_vat_rate.setter
    def default_vat_rate(self, value: float):
        self.set('default_vat_rate', value)

    def get_smtp_config(self) -> dict:
        """Get SMTP configuration as a dictionary."""
        return {
            'host': self.get('smtp_host') or '',
            'port': self.get_typed('smtp_port', int, 587),
            'username': self.get('smtp_username') or '',
            'password': self.get('smtp_password') or '',
            'use_tls': self.get_typed('smtp_use_tls', bool, True),
        }

    def set_smtp_config(self, config: dict) -> None:
        """Set SMTP configuration from a dictionary."""
        if 'host' in config:
            self.set('smtp_host', config['host'])
        if 'port' in config:
            self.set('smtp_port', config['port'])
        if 'username' in config:
            self.set('smtp_username', config['username'])
        if 'password' in config:
            self.set('smtp_password', config['password'])
        if 'use_tls' in config:
            self.set('smtp_use_tls', config['use_tls'])
