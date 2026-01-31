"""Thermal printer service using ESC/POS protocol."""

import base64
from io import BytesIO
from typing import Optional, Union
from dataclasses import dataclass
from datetime import datetime
import subprocess
import sys
import os
import struct

try:
    from escpos.printer import Usb
    from escpos.exceptions import USBNotFoundError
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False
    USBNotFoundError = Exception

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Try to import usb library for device discovery
try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False

# Windows-specific features
WIN_USB_AVAILABLE = sys.platform == 'win32'

# Try win32print for Windows raw printing
try:
    import win32print
    WIN32PRINT_AVAILABLE = True
except ImportError:
    WIN32PRINT_AVAILABLE = False


@dataclass
class PrinterStatus:
    """Printer connection status."""
    connected: bool
    printer_name: str = ""
    printer_type: str = ""  # 'usb', 'windows', 'none'
    vendor_id: int = 0
    product_id: int = 0
    error_message: str = ""


@dataclass
class USBDevice:
    """USB device info."""
    vendor_id: int
    product_id: int
    manufacturer: str = ""
    product: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return {
            'vendor_id': f"0x{self.vendor_id:04X}",
            'product_id': f"0x{self.product_id:04X}",
            'vendor_id_int': self.vendor_id,
            'product_id_int': self.product_id,
            'manufacturer': self.manufacturer,
            'product': self.product,
            'description': self.description or f"{self.manufacturer} {self.product}".strip()
        }


class PrinterNotConnectedError(Exception):
    """Raised when printer is not connected."""
    pass


class WindowsRawPrinter:
    """
    Windows raw printer for sending ESC/POS commands via Windows spooler.

    This works with printers using the standard Windows USB Print driver,
    without needing libusb.
    """

    # ESC/POS command constants
    ESC = b'\x1B'
    GS = b'\x1D'

    # Commands
    INIT = ESC + b'@'  # Initialize printer
    CUT = GS + b'V\x00'  # Full cut
    PARTIAL_CUT = GS + b'V\x01'  # Partial cut

    # Text formatting
    ALIGN_LEFT = ESC + b'a\x00'
    ALIGN_CENTER = ESC + b'a\x01'
    ALIGN_RIGHT = ESC + b'a\x02'
    BOLD_ON = ESC + b'E\x01'
    BOLD_OFF = ESC + b'E\x00'
    DOUBLE_HEIGHT = ESC + b'!\x10'
    DOUBLE_WIDTH = ESC + b'!\x20'
    NORMAL = ESC + b'!\x00'

    def __init__(self, printer_name: str = None, usb_port: str = None):
        """
        Initialize Windows raw printer.

        Args:
            printer_name: Windows printer name (auto-detect if not specified)
            usb_port: Direct USB port (e.g., 'USB001') for raw USB printing
        """
        self.printer_name = printer_name
        self.usb_port = usb_port
        self._buffer = bytearray()
        self._use_direct_port = False

        if usb_port:
            # Try direct USB port access
            self.usb_port = usb_port
            self._use_direct_port = True
        elif not printer_name:
            # Try to find a printer or USB port
            self.printer_name = self._find_pos_printer()
            if not self.printer_name:
                # Try to find USB port
                self.usb_port = self._find_usb_port()
                if self.usb_port:
                    self._use_direct_port = True

    def _find_usb_port(self) -> Optional[str]:
        """Find a USB printer port."""
        try:
            # Check for USB001-USB009
            for i in range(1, 10):
                port = f"USB{i:03d}"
                # Try to open the port to verify it exists
                try:
                    # Check if port exists via printer ports
                    result = subprocess.run(
                        ['powershell', '-NoProfile', '-Command',
                         f"Get-PrinterPort -Name '{port}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and port in result.stdout:
                        return port
                except:
                    pass
        except:
            pass
        return None

    def _find_pos_printer(self) -> Optional[str]:
        """Find a POS/thermal printer in Windows."""
        if not WIN32PRINT_AVAILABLE:
            return None

        try:
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )

            # First priority: Look for our recommended printer name
            for flags, desc, name, comment in printers:
                if name == 'POS Receipt Printer':
                    return name

            # Second priority: Look for typical POS printer names
            pos_keywords = ['pos', 'thermal', 'receipt', 'esc', '58mm', '80mm']

            for flags, desc, name, comment in printers:
                name_lower = name.lower()
                if any(kw in name_lower for kw in pos_keywords):
                    return name

            # Third priority: Generic printer (but not virtual ones)
            virtual_printers = ['pdf', 'onenote', 'fax', 'xps', 'document writer']
            for flags, desc, name, comment in printers:
                name_lower = name.lower()
                if 'generic' in name_lower:
                    if not any(vp in name_lower for vp in virtual_printers):
                        return name

        except Exception:
            pass

        return None

    def is_available(self) -> bool:
        """Check if printer is available."""
        if self._use_direct_port and self.usb_port:
            return True
        return self.printer_name is not None and WIN32PRINT_AVAILABLE

    def _write(self, data: bytes):
        """Add data to buffer."""
        self._buffer.extend(data)

    def _text(self, text: str):
        """Add text to buffer."""
        # Replace characters not supported in CP437
        # Euro symbol (€) is not in CP437, replace with "EUR" or use code page 858
        replacements = {
            '€': 'EUR',  # Euro symbol -> EUR text
            '£': chr(156),  # Pound sign exists in CP437
            '¥': chr(157),  # Yen sign exists in CP437
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        # Encode as CP437 (common for ESC/POS printers)
        try:
            encoded = text.encode('cp437')
        except UnicodeEncodeError:
            # Try CP858 which has Euro symbol at position 213
            try:
                encoded = text.encode('cp858')
            except UnicodeEncodeError:
                # Final fallback - replace unknown chars
                encoded = text.encode('cp437', errors='replace')
        self._buffer.extend(encoded)

    def set(self, align: str = 'left', text_type: str = 'NORMAL'):
        """Set text formatting."""
        if align == 'center':
            self._write(self.ALIGN_CENTER)
        elif align == 'right':
            self._write(self.ALIGN_RIGHT)
        else:
            self._write(self.ALIGN_LEFT)

        if text_type == 'B':
            self._write(self.BOLD_ON)
        else:
            self._write(self.BOLD_OFF)

    def text(self, txt: str):
        """Print text."""
        self._text(txt)

    def image(self, img: Image.Image):
        """Print image (simplified raster graphics)."""
        if not PIL_AVAILABLE:
            return

        try:
            # Convert to 1-bit
            img = img.convert('1')

            # Resize for printer width (384 pixels for 58mm at 203dpi)
            max_width = 384
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            # Make width multiple of 8
            width = (img.width + 7) // 8 * 8
            if width != img.width:
                new_img = Image.new('1', (width, img.height), 1)
                new_img.paste(img, (0, 0))
                img = new_img

            # Convert to raster format
            width_bytes = width // 8

            # GS v 0 - Print raster bit image
            self._write(self.GS + b'v0\x00')
            self._write(struct.pack('<H', width_bytes))
            self._write(struct.pack('<H', img.height))

            pixels = img.load()
            for y in range(img.height):
                for x_byte in range(width_bytes):
                    byte = 0
                    for bit in range(8):
                        x = x_byte * 8 + bit
                        if x < img.width and pixels[x, y] == 0:  # Black pixel
                            byte |= (1 << (7 - bit))
                    self._write(bytes([byte]))

        except Exception:
            self._text("[Image]\n")

    def cut(self):
        """Cut paper."""
        self._write(b'\n\n\n')  # Feed paper
        self._write(self.CUT)

    def flush(self) -> bool:
        """Send buffer to printer."""

        # Method 1: Direct USB port access (works with usbprint driver)
        if self._use_direct_port and self.usb_port:
            return self._flush_to_port()

        # Method 2: Windows spooler
        if not self.printer_name or not WIN32PRINT_AVAILABLE:
            return False

        try:
            # Open printer
            hPrinter = win32print.OpenPrinter(self.printer_name)

            try:
                # Start document
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Receipt", None, "RAW"))

                try:
                    win32print.StartPagePrinter(hPrinter)

                    # Initialize printer
                    win32print.WritePrinter(hPrinter, self.INIT)

                    # Send buffer
                    win32print.WritePrinter(hPrinter, bytes(self._buffer))

                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)

            self._buffer.clear()
            return True

        except Exception as e:
            raise PrinterNotConnectedError(f"Print failed: {str(e)}")

    def _flush_to_port(self) -> bool:
        """Send buffer directly to USB port using Windows API."""
        if not WIN32PRINT_AVAILABLE:
            return False

        try:
            import win32file
            import win32con

            # Open the USB port directly
            port_path = f"\\\\.\\{self.usb_port}"

            handle = win32file.CreateFile(
                port_path,
                win32con.GENERIC_WRITE,
                0,  # No sharing
                None,
                win32con.OPEN_EXISTING,
                0,
                None
            )

            try:
                # Write initialize command
                win32file.WriteFile(handle, self.INIT)

                # Write buffer
                win32file.WriteFile(handle, bytes(self._buffer))
            finally:
                win32file.CloseHandle(handle)

            self._buffer.clear()
            return True

        except ImportError:
            # win32file not available, try subprocess
            return self._flush_via_copy()
        except Exception as e:
            raise PrinterNotConnectedError(f"Direct port write failed: {str(e)}")

    def _flush_via_copy(self) -> bool:
        """Send buffer to port via copy command (fallback method)."""
        try:
            import tempfile

            # Write buffer to temp file
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.prn') as f:
                f.write(self.INIT)
                f.write(bytes(self._buffer))
                temp_path = f.name

            try:
                # Copy to USB port
                result = subprocess.run(
                    ['cmd', '/c', f'copy /b "{temp_path}" "{self.usb_port}:"'],
                    capture_output=True,
                    timeout=30
                )

                if result.returncode != 0:
                    raise PrinterNotConnectedError(f"Copy to port failed")
            finally:
                os.unlink(temp_path)

            self._buffer.clear()
            return True

        except Exception as e:
            raise PrinterNotConnectedError(f"Port write failed: {str(e)}")

    def close(self):
        """Close printer (no-op for Windows)."""
        pass


class ThermalPrinter:
    """
    Thermal printer service for 58mm receipt printers.

    Supports ESC/POS compatible printers via:
    1. Direct USB (requires libusb)
    2. Windows raw printing (uses Windows USB Print driver)
    """

    # Common USB Vendor/Product IDs for thermal printers
    KNOWN_PRINTERS = [
        (0x6868, 0x0200, "Generic POS Printer"),  # Added from user's system
        (0x0416, 0x5011, "Bisofice / Generic 58mm"),
        (0x04B8, 0x0E15, "Epson TM-T20II"),
        (0x0519, 0x0001, "Star TSP100"),
        (0x0DD4, 0x0200, "Custom Printer"),
        (0x0483, 0x5720, "Generic POS Printer"),
        (0x1504, 0x0006, "POS-58"),
        (0x0FE6, 0x811E, "Generic USB Printer"),
        (0x1A86, 0x7523, "CH340 Serial (some printers)"),
    ]

    # Receipt formatting
    LINE_WIDTH = 32  # Characters for 58mm paper

    def __init__(self, vendor_id: int = None, product_id: int = None, windows_printer: str = None):
        """
        Initialize printer connection.

        Args:
            vendor_id: USB vendor ID (for direct USB mode)
            product_id: USB product ID (for direct USB mode)
            windows_printer: Windows printer name (for Windows raw mode)
        """
        self.printer = None
        self.windows_printer = None
        self.vendor_id = vendor_id
        self.product_id = product_id
        self._last_error = ""
        self._printer_type = "none"

        # Try to connect
        self._connect(windows_printer)

    def _connect(self, windows_printer: str = None) -> bool:
        """Attempt to connect to printer using best available method."""

        # Method 1: Try direct USB via python-escpos
        if ESCPOS_AVAILABLE and self._connect_usb():
            self._printer_type = "usb"
            return True

        # Method 2: Try Windows raw printing
        if WIN32PRINT_AVAILABLE:
            self.windows_printer = WindowsRawPrinter(windows_printer)
            if self.windows_printer.is_available():
                self._printer_type = "windows"
                self._last_error = ""
                return True
            else:
                self._last_error = "No Windows printer found"

        return False

    def _connect_usb(self) -> bool:
        """Attempt to connect via direct USB."""
        if not ESCPOS_AVAILABLE:
            self._last_error = "ESC/POS library not installed"
            return False

        # Try specified IDs first
        if self.vendor_id and self.product_id:
            try:
                printer = Usb(self.vendor_id, self.product_id)
                # Verify we can actually communicate
                printer.set(align='center')
                self.printer = printer
                self._last_error = ""
                return True
            except USBNotFoundError:
                self._last_error = f"Printer 0x{self.vendor_id:04X}:0x{self.product_id:04X} not found"
            except Exception as e:
                self._last_error = str(e)

        # Auto-detect from known printers
        for vid, pid, name in self.KNOWN_PRINTERS:
            try:
                printer = Usb(vid, pid)
                # Verify we can actually communicate
                printer.set(align='center')
                self.printer = printer
                self.vendor_id = vid
                self.product_id = pid
                self._last_error = ""
                return True
            except USBNotFoundError:
                continue
            except Exception as e:
                self._last_error = str(e)
                continue

        if not self._last_error:
            self._last_error = "No USB printer found (libusb may be missing)"
        return False

    def set_printer(self, vendor_id: int = None, product_id: int = None, windows_printer: str = None) -> bool:
        """
        Set specific printer.

        Args:
            vendor_id: USB Vendor ID (for direct USB)
            product_id: USB Product ID (for direct USB)
            windows_printer: Windows printer name

        Returns:
            True if connection successful
        """
        self.printer = None
        self.windows_printer = None
        self.vendor_id = vendor_id
        self.product_id = product_id
        return self._connect(windows_printer)

    def set_windows_printer(self, printer_name: str) -> bool:
        """Set a specific Windows printer by name."""
        self.printer = None
        self.windows_printer = WindowsRawPrinter(printer_name)
        if self.windows_printer.is_available():
            self._printer_type = "windows"
            self._last_error = ""
            return True
        self._last_error = f"Printer '{printer_name}' not found"
        return False

    @staticmethod
    def list_windows_printers() -> list[dict]:
        """List available Windows printers."""
        printers = []

        if not WIN32PRINT_AVAILABLE:
            return printers

        try:
            for flags, desc, name, comment in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            ):
                printers.append({
                    'name': name,
                    'description': desc,
                    'comment': comment
                })
        except Exception:
            pass

        return printers

    @staticmethod
    def discover_usb_devices() -> list[USBDevice]:
        """
        Discover all USB devices that might be printers.

        Returns:
            List of USBDevice objects
        """
        devices = []

        if USB_AVAILABLE:
            try:
                all_devices = usb.core.find(find_all=True)

                for dev in all_devices:
                    try:
                        manufacturer = ""
                        product = ""

                        try:
                            if dev.iManufacturer:
                                manufacturer = usb.util.get_string(dev, dev.iManufacturer) or ""
                        except Exception:
                            pass

                        try:
                            if dev.iProduct:
                                product = usb.util.get_string(dev, dev.iProduct) or ""
                        except Exception:
                            pass

                        # Filter for likely printers
                        is_printer_class = False
                        for cfg in dev:
                            for intf in cfg:
                                if intf.bInterfaceClass == 7:
                                    is_printer_class = True
                                    break

                        known_vid = dev.idVendor in [0x6868, 0x0416, 0x04B8, 0x0519, 0x0DD4, 0x0483, 0x1504, 0x0FE6]
                        has_printer_name = 'printer' in (product or '').lower() or 'pos' in (product or '').lower()

                        if is_printer_class or known_vid or has_printer_name:
                            devices.append(USBDevice(
                                vendor_id=dev.idVendor,
                                product_id=dev.idProduct,
                                manufacturer=manufacturer,
                                product=product,
                                description=f"{manufacturer} {product}".strip() or f"USB Device {dev.idVendor:04X}:{dev.idProduct:04X}"
                            ))

                    except Exception:
                        continue

                if devices:
                    return devices
            except Exception:
                pass

        # Fallback: Windows-specific discovery
        if WIN_USB_AVAILABLE:
            devices = ThermalPrinter._list_usb_devices_windows()

        return devices

    @staticmethod
    def list_all_usb_devices() -> list[USBDevice]:
        """List ALL USB devices (for troubleshooting)."""
        devices = []

        if USB_AVAILABLE:
            try:
                all_devices = usb.core.find(find_all=True)
                for dev in all_devices:
                    try:
                        manufacturer = ""
                        product = ""
                        try:
                            if dev.iManufacturer:
                                manufacturer = usb.util.get_string(dev, dev.iManufacturer) or ""
                        except:
                            pass
                        try:
                            if dev.iProduct:
                                product = usb.util.get_string(dev, dev.iProduct) or ""
                        except:
                            pass
                        devices.append(USBDevice(
                            vendor_id=dev.idVendor,
                            product_id=dev.idProduct,
                            manufacturer=manufacturer,
                            product=product,
                            description=f"{manufacturer} {product}".strip() or f"USB Device {dev.idVendor:04X}:{dev.idProduct:04X}"
                        ))
                    except:
                        continue
                if devices:
                    return devices
            except:
                pass

        if WIN_USB_AVAILABLE:
            devices = ThermalPrinter._list_usb_devices_windows()

        return devices

    @staticmethod
    def _list_usb_devices_windows() -> list[USBDevice]:
        """List USB devices using Windows PowerShell/WMI."""
        devices = []

        try:
            ps_command = '''
            Get-PnpDevice -Class USB, Printer, USBDevice -Status OK | ForEach-Object {
                $id = $_.InstanceId
                if ($id -match 'VID_([0-9A-Fa-f]{4}).*PID_([0-9A-Fa-f]{4})') {
                    [PSCustomObject]@{
                        VID = $matches[1]
                        PID = $matches[2]
                        Name = $_.FriendlyName
                        Manufacturer = $_.Manufacturer
                        Class = $_.Class
                    }
                }
            } | ConvertTo-Json
            '''

            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)

                if isinstance(data, dict):
                    data = [data]

                for item in data:
                    try:
                        vid = int(item.get('VID', '0'), 16)
                        pid = int(item.get('PID', '0'), 16)
                        name = item.get('Name', '')
                        manufacturer = item.get('Manufacturer', '')

                        devices.append(USBDevice(
                            vendor_id=vid,
                            product_id=pid,
                            manufacturer=manufacturer,
                            product=name,
                            description=f"{name}" if name else f"USB Device {vid:04X}:{pid:04X}"
                        ))
                    except:
                        continue

        except Exception:
            pass

        return devices

    def get_status(self) -> PrinterStatus:
        """Get current printer status."""
        if self._printer_type == "usb" and self.printer:
            return PrinterStatus(
                connected=True,
                printer_name=f"USB Printer",
                printer_type="usb",
                vendor_id=self.vendor_id or 0,
                product_id=self.product_id or 0
            )

        if self._printer_type == "windows" and self.windows_printer and self.windows_printer.is_available():
            return PrinterStatus(
                connected=True,
                printer_name=self.windows_printer.printer_name,
                printer_type="windows"
            )

        error = self._last_error
        if not error:
            if not ESCPOS_AVAILABLE and not WIN32PRINT_AVAILABLE:
                error = "No printing library available"
            else:
                error = "No printer found"

        return PrinterStatus(
            connected=False,
            error_message=error
        )

    def is_connected(self) -> bool:
        """Check if printer is connected."""
        if self._printer_type == "usb":
            return self.printer is not None
        if self._printer_type == "windows":
            return self.windows_printer is not None and self.windows_printer.is_available()
        return False

    def reconnect(self) -> bool:
        """Attempt to reconnect to printer."""
        self.printer = None
        self.windows_printer = None
        self._printer_type = "none"
        return self._connect()

    def test_connection(self) -> tuple[bool, str]:
        """Test if printer can actually communicate."""
        if self._printer_type == "usb" and self.printer:
            try:
                self.printer.set(align='center')
                return True, "USB printer communication OK"
            except Exception as e:
                return False, f"USB communication failed: {str(e)}"

        if self._printer_type == "windows" and self.windows_printer:
            if self.windows_printer.is_available():
                return True, f"Windows printer '{self.windows_printer.printer_name}' available"
            return False, "Windows printer not available"

        return False, "No printer connected"

    def _get_printer_interface(self):
        """Get the appropriate printer interface."""
        if self._printer_type == "usb" and self.printer:
            return self.printer
        if self._printer_type == "windows" and self.windows_printer:
            return self.windows_printer
        return None

    def print_receipt(
        self,
        store_name: str,
        invoice_number: str,
        items: list[dict],
        subtotal: float,
        vat_amount: float,
        total: float,
        payment_method: str,
        qr_base64: str,
        currency_symbol: str = "€",
        seller_id: str = "",
        timestamp: str = None
    ) -> bool:
        """Print a formatted receipt."""
        p = self._get_printer_interface()
        if not p:
            raise PrinterNotConnectedError("Printer not connected")

        timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Header
            p.set(align='center', text_type='B')
            p.text(f"{store_name}\n")
            p.set(align='center', text_type='NORMAL')
            p.text("=" * self.LINE_WIDTH + "\n")

            # Invoice info
            p.set(align='left')
            p.text(f"Invoice: {invoice_number}\n")
            p.text(f"Date: {timestamp}\n")
            if seller_id:
                p.text(f"Seller: {seller_id}\n")
            p.text("-" * self.LINE_WIDTH + "\n")

            # Items
            for item in items:
                name = item.get('product_name', item.get('name', 'Item'))
                qty = item.get('quantity', 1)
                price = item.get('unit_price', 0)
                line_total = item.get('line_total', qty * price)

                max_name_len = self.LINE_WIDTH - 15
                if len(name) > max_name_len:
                    name = name[:max_name_len-2] + ".."

                p.text(f"{name}\n")
                p.text(f"  {qty} x {currency_symbol}{price:.2f}")
                total_str = f"{currency_symbol}{line_total:.2f}"
                padding = self.LINE_WIDTH - 4 - len(f"{qty} x {currency_symbol}{price:.2f}") - len(total_str)
                p.text(" " * max(1, padding) + total_str + "\n")

            p.text("-" * self.LINE_WIDTH + "\n")

            # Totals
            p.set(align='right')
            p.text(f"Subtotal: {currency_symbol}{subtotal:.2f}\n")
            p.text(f"VAT: {currency_symbol}{vat_amount:.2f}\n")
            p.set(text_type='B')
            p.text(f"TOTAL: {currency_symbol}{total:.2f}\n")
            p.set(text_type='NORMAL')

            p.text("-" * self.LINE_WIDTH + "\n")

            # Payment method
            p.set(align='center')
            p.text(f"Paid by: {payment_method.upper()}\n")

            # QR Code
            if qr_base64 and PIL_AVAILABLE:
                p.text("\n")
                try:
                    qr_bytes = base64.b64decode(qr_base64)
                    qr_image = Image.open(BytesIO(qr_bytes))
                    p.image(qr_image)
                except Exception:
                    p.text("[QR Code]\n")
            p.text("\n")

            # Footer
            p.text("Thank you for your purchase!\n")
            p.text("Verify receipt at:\n")
            p.text("openinvoice.app/verify\n")
            p.text("\n\n\n")

            # Cut paper
            p.cut()

            # For Windows printer, we need to flush the buffer
            if self._printer_type == "windows":
                p.flush()

            return True

        except Exception as e:
            raise PrinterNotConnectedError(f"Print failed: {str(e)}")

    def print_test_page(self) -> bool:
        """Print a test page to verify printer connection."""
        p = self._get_printer_interface()
        if not p:
            raise PrinterNotConnectedError("Printer not connected")

        try:
            p.set(align='center', text_type='B')
            p.text("PRINTER TEST\n")
            p.set(text_type='NORMAL')
            p.text("=" * self.LINE_WIDTH + "\n")
            p.text("Open Invoice POS\n")
            p.text(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

            if self._printer_type == "usb":
                p.text(f"Type: Direct USB\n")
                if self.vendor_id and self.product_id:
                    p.text(f"VID:PID = {self.vendor_id:04X}:{self.product_id:04X}\n")
            else:
                p.text(f"Type: Windows Printer\n")
                p.text(f"Name: {self.windows_printer.printer_name}\n")

            p.text("-" * self.LINE_WIDTH + "\n")
            p.text("Characters: ABCDEFGHIJKLMNOP\n")
            p.text("Numbers: 0123456789\n")
            p.text("Symbols: !@#$%^&*()+-=\n")
            p.text("=" * self.LINE_WIDTH + "\n")
            p.text("If you can read this,\n")
            p.text("your printer is working!\n")
            p.text("\n\n\n")
            p.cut()

            # For Windows printer, flush the buffer
            if self._printer_type == "windows":
                p.flush()

            return True

        except Exception as e:
            raise PrinterNotConnectedError(f"Test print failed: {str(e)}")

    def close(self):
        """Close printer connection."""
        if self.printer:
            try:
                self.printer.close()
            except Exception:
                pass
            self.printer = None
        if self.windows_printer:
            self.windows_printer.close()
            self.windows_printer = None
