"""Main entry point for Open Invoice POS application."""

import os
import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and PyInstaller.

    In development, returns path relative to this file.
    When bundled with PyInstaller, returns path in the temp extraction folder.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent

    return base_path / relative_path


def get_data_path() -> Path:
    """
    Get path for application data (database, etc).

    Uses:
    - Windows: %APPDATA%/OpenInvoice
    - macOS: ~/Library/Application Support/OpenInvoice
    - Linux: ~/.local/share/OpenInvoice
    """
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home()))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

    data_path = base / 'OpenInvoice'
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def main():
    """Run the Open Invoice POS application."""
    import webview

    # Import API after setting up paths
    from api.bridge import API

    # Set database path to user data directory
    from database.connection import Database
    db_path = get_data_path() / 'openinvoice.db'
    Database._instance = None  # Reset singleton
    Database(db_path)

    # Initialize API
    api = API()

    # Determine frontend path
    frontend_path = get_resource_path('frontend/dist/index.html')

    # Fallback for development
    if not frontend_path.exists():
        # Try development server
        frontend_url = 'http://localhost:5173'
        print(f"Development mode: Loading from {frontend_url}")
    else:
        frontend_url = f'file://{frontend_path}'
        print(f"Production mode: Loading from {frontend_path}")

    # Create window
    window = webview.create_window(
        title='Open Invoice POS',
        url=frontend_url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600),
        text_select=False,
    )

    # Start webview
    webview.start(
        debug=not hasattr(sys, '_MEIPASS'),  # Enable debug in development
        http_server=not frontend_path.exists(),  # Use HTTP server for dev
    )


if __name__ == '__main__':
    main()
