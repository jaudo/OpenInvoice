/**
 * Mock API for development without backend
 */

import type {
  ApiResponse,
  Product,
  Invoice,
  InvoiceItem,
  Settings,
  ValidationResult,
  DailySales,
  PeriodReport,
  TopProduct,
  KeyboardLayout,
  PrinterStatus,
  ImportResult,
  ChainVerification,
  PyWebViewAPI,
} from '@/types/api';

// Sample products
const sampleProducts: Product[] = [
  {
    id: 'PROD001',
    name: 'Espresso',
    description: 'Single shot espresso',
    price: 2.5,
    vat_rate: 21.0,
    barcode: '1234567890123',
    stock: 100,
    status: 'active',
  },
  {
    id: 'PROD002',
    name: 'Cappuccino',
    description: 'Espresso with steamed milk foam',
    price: 3.5,
    vat_rate: 21.0,
    barcode: '1234567890124',
    stock: 100,
    status: 'active',
  },
  {
    id: 'PROD003',
    name: 'Latte',
    description: 'Espresso with steamed milk',
    price: 4.0,
    vat_rate: 21.0,
    barcode: '1234567890125',
    stock: 100,
    status: 'active',
  },
  {
    id: 'PROD004',
    name: 'Croissant',
    description: 'Fresh butter croissant',
    price: 2.0,
    vat_rate: 21.0,
    barcode: '1234567890126',
    stock: 50,
    status: 'active',
  },
  {
    id: 'PROD005',
    name: 'Muffin',
    description: 'Chocolate chip muffin',
    price: 2.5,
    vat_rate: 21.0,
    barcode: '1234567890127',
    stock: 30,
    status: 'active',
  },
  {
    id: 'PROD006',
    name: 'Sandwich',
    description: 'Ham and cheese sandwich',
    price: 5.5,
    vat_rate: 21.0,
    barcode: '1234567890128',
    stock: 20,
    status: 'active',
  },
];

// Sample invoices
const sampleInvoices: Invoice[] = [
  {
    id: 1,
    invoice_number: 'INV-2024-0001',
    seller_id: 'SELLER001',
    store_name: 'Demo Store',
    subtotal: 10.0,
    vat_amount: 2.1,
    total: 12.1,
    payment_method: 'cash',
    current_hash: 'a1b2c3d4e5f6g7h8',
    qr_data: 'OPENINVOICE|v1|INV-2024-0001|12.10|a1b2c3d4|1706745600',
    status: 'completed',
    created_at: '2024-01-31T10:30:00',
    items: [
      {
        id: 1,
        invoice_id: 1,
        product_id: 'PROD001',
        product_name: 'Espresso',
        quantity: 2,
        unit_price: 2.5,
        vat_rate: 21.0,
        line_total: 5.0,
        return_status: 'none',
      },
      {
        id: 2,
        invoice_id: 1,
        product_id: 'PROD004',
        product_name: 'Croissant',
        quantity: 2,
        unit_price: 2.0,
        vat_rate: 21.0,
        line_total: 4.0,
        return_status: 'none',
      },
    ],
  },
];

// Mock settings
let mockSettings: Settings = {
  language: 'en',
  store_name: 'Demo Store',
  seller_id: 'SELLER001',
  printer_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true,
  keyboard_layout: 'qwerty',
  currency_symbol: '€',
  default_vat_rate: 21.0,
};

// Helper to simulate async delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Generate mock QR image (1x1 transparent PNG as base64)
const mockQrImage =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

// Invoice counter for generating new invoices
let invoiceCounter = sampleInvoices.length;

// Mock API implementation
export const mockApi: PyWebViewAPI = {
  // Products
  async products_get_all(): Promise<ApiResponse<Product[]>> {
    await delay(100);
    return { success: true, data: sampleProducts.filter((p) => p.status === 'active') };
  },

  async products_search(query: string): Promise<ApiResponse<Product[]>> {
    await delay(100);
    const q = query.toLowerCase();
    const results = sampleProducts.filter(
      (p) =>
        p.status === 'active' &&
        (p.name.toLowerCase().includes(q) ||
          p.id.toLowerCase().includes(q) ||
          p.barcode?.includes(q))
    );
    return { success: true, data: results };
  },

  async products_get_by_barcode(barcode: string): Promise<ApiResponse<Product>> {
    await delay(100);
    const product = sampleProducts.find((p) => p.barcode === barcode);
    if (product) {
      return { success: true, data: product };
    }
    return { success: false, error: 'Product not found' };
  },

  async products_create(data: Partial<Product>): Promise<ApiResponse<Product>> {
    await delay(100);
    const newProduct: Product = {
      id: data.id || `PROD${String(sampleProducts.length + 1).padStart(3, '0')}`,
      name: data.name || 'New Product',
      description: data.description || '',
      price: data.price || 0,
      vat_rate: data.vat_rate || 21.0,
      barcode: data.barcode || null,
      stock: data.stock || 0,
      status: 'active',
    };
    sampleProducts.push(newProduct);
    return { success: true, data: newProduct };
  },

  async products_update(data: Product): Promise<ApiResponse<Product>> {
    await delay(100);
    const index = sampleProducts.findIndex((p) => p.id === data.id);
    if (index >= 0) {
      sampleProducts[index] = { ...sampleProducts[index], ...data };
      return { success: true, data: sampleProducts[index] };
    }
    return { success: false, error: 'Product not found' };
  },

  async products_delete(productId: string): Promise<ApiResponse<void>> {
    await delay(100);
    const index = sampleProducts.findIndex((p) => p.id === productId);
    if (index >= 0) {
      sampleProducts[index].status = 'inactive';
      return { success: true };
    }
    return { success: false, error: 'Product not found' };
  },

  async products_import_csv(_filePath: string): Promise<ApiResponse<ImportResult>> {
    await delay(500);
    return {
      success: true,
      data: {
        success: true,
        total_rows: 5,
        imported: 5,
        skipped: 0,
        errors: [],
        message: 'Imported 5 of 5 products',
      },
    };
  },

  // Invoices
  async invoices_create(
    items: Array<{ product_id: string; quantity: number }>,
    paymentMethod: string,
    customerEmail?: string
  ): Promise<ApiResponse<Invoice>> {
    await delay(200);

    invoiceCounter++;
    const invoiceNumber = `INV-2024-${String(invoiceCounter).padStart(4, '0')}`;

    let subtotal = 0;
    let vatTotal = 0;
    const invoiceItems: InvoiceItem[] = [];

    for (const item of items) {
      const product = sampleProducts.find((p) => p.id === item.product_id);
      if (!product) {
        return { success: false, error: `Product ${item.product_id} not found` };
      }

      const lineTotal = product.price * item.quantity;
      const vatAmount = lineTotal * (product.vat_rate / 100);
      subtotal += lineTotal;
      vatTotal += vatAmount;

      invoiceItems.push({
        id: invoiceItems.length + 1,
        invoice_id: invoiceCounter,
        product_id: product.id,
        product_name: product.name,
        quantity: item.quantity,
        unit_price: product.price,
        vat_rate: product.vat_rate,
        line_total: lineTotal,
        return_status: 'none',
      });
    }

    const total = subtotal + vatTotal;
    const timestamp = new Date().toISOString();
    const hash = `mock${Date.now().toString(16)}`;

    const invoice: Invoice = {
      id: invoiceCounter,
      invoice_number: invoiceNumber,
      seller_id: mockSettings.seller_id,
      store_name: mockSettings.store_name,
      subtotal: Math.round(subtotal * 100) / 100,
      vat_amount: Math.round(vatTotal * 100) / 100,
      total: Math.round(total * 100) / 100,
      payment_method: paymentMethod,
      customer_email: customerEmail,
      current_hash: hash,
      qr_data: `OPENINVOICE|v1|${invoiceNumber}|${total.toFixed(2)}|${hash.slice(0, 8)}|${Math.floor(Date.now() / 1000)}`,
      qr_image: mockQrImage,
      status: 'completed',
      created_at: timestamp,
      items: invoiceItems,
      currency_symbol: mockSettings.currency_symbol,
    };

    sampleInvoices.push(invoice);
    return { success: true, data: invoice };
  },

  async invoices_get_by_number(invoiceNumber: string): Promise<ApiResponse<Invoice>> {
    await delay(100);
    const invoice = sampleInvoices.find((i) => i.invoice_number === invoiceNumber);
    if (invoice) {
      return { success: true, data: { ...invoice, qr_image: mockQrImage } };
    }
    return { success: false, error: 'Invoice not found' };
  },

  async invoices_process_return(
    invoiceNumber: string,
    itemIds: number[]
  ): Promise<ApiResponse<{ invoice_number: string; refund_amount: number; new_status: string }>> {
    await delay(200);
    const invoice = sampleInvoices.find((i) => i.invoice_number === invoiceNumber);
    if (!invoice) {
      return { success: false, error: 'Invoice not found' };
    }

    let refundAmount = 0;
    for (const item of invoice.items) {
      if (itemIds.includes(item.id!)) {
        item.return_status = 'returned';
        refundAmount += item.line_total;
      }
    }

    const allReturned = invoice.items.every((i) => i.return_status === 'returned');
    invoice.status = allReturned ? 'returned' : 'partial_return';

    return {
      success: true,
      data: {
        invoice_number: invoiceNumber,
        refund_amount: refundAmount,
        new_status: invoice.status,
      },
    };
  },

  // Validation
  async qr_validate(qrData: string): Promise<ApiResponse<ValidationResult>> {
    await delay(200);

    // Parse QR data
    const parts = qrData.split('|');
    if (parts.length !== 6 || parts[0] !== 'OPENINVOICE') {
      return {
        success: false,
        data: { valid: false, error_message: 'Invalid QR code format' },
      };
    }

    const invoiceNumber = parts[2];
    const invoice = sampleInvoices.find((i) => i.invoice_number === invoiceNumber);

    if (!invoice) {
      return {
        success: false,
        data: { valid: false, invoice_number: invoiceNumber, error_message: 'Invoice not found' },
      };
    }

    return {
      success: true,
      data: {
        valid: true,
        invoice_number: invoiceNumber,
        invoice_data: { ...invoice, qr_image: mockQrImage },
        checks: {
          format_valid: true,
          invoice_exists: true,
          hash_matches: true,
          total_matches: true,
          hash_verified: true,
        },
      },
    };
  },

  async hash_chain_verify(): Promise<ApiResponse<ChainVerification>> {
    await delay(300);
    return {
      success: true,
      data: {
        valid: true,
        checked_count: sampleInvoices.length,
      },
    };
  },

  // Printing/Export
  async print_receipt(_invoiceId: number): Promise<ApiResponse<void>> {
    await delay(500);
    console.log('Mock: Printing receipt for invoice', _invoiceId);
    return { success: true };
  },

  async generate_pdf(_invoiceId: number): Promise<ApiResponse<{ path: string }>> {
    await delay(300);
    return { success: true, data: { path: '/tmp/receipt.pdf' } };
  },

  async send_email(_invoiceId: number, email: string): Promise<ApiResponse<{ message: string }>> {
    await delay(500);
    return { success: true, data: { message: `Receipt sent to ${email}` } };
  },

  // Settings
  async settings_get_all(): Promise<ApiResponse<Settings>> {
    await delay(100);
    return { success: true, data: { ...mockSettings } };
  },

  async settings_update(key: string, value: unknown): Promise<ApiResponse<void>> {
    await delay(100);
    (mockSettings as Record<string, unknown>)[key] = value;
    return { success: true };
  },

  async settings_update_many(settings: Partial<Settings>): Promise<ApiResponse<void>> {
    await delay(100);
    mockSettings = { ...mockSettings, ...settings };
    return { success: true };
  },

  async get_keyboard_layouts(): Promise<ApiResponse<KeyboardLayout[]>> {
    await delay(100);
    return {
      success: true,
      data: [
        { id: 'qwerty', name: 'QWERTY', description: 'US/UK Standard' },
        { id: 'azerty', name: 'AZERTY', description: 'French' },
        { id: 'qwertz', name: 'QWERTZ', description: 'German/Central European' },
      ],
    };
  },

  // Printer
  async printer_status(): Promise<ApiResponse<PrinterStatus>> {
    await delay(100);
    return {
      success: true,
      data: {
        connected: false,
        printer_name: '',
        error: 'No printer found (mock mode)',
      },
    };
  },

  async printer_test(): Promise<ApiResponse<void>> {
    await delay(300);
    return { success: false, error: 'No printer connected (mock mode)' };
  },

  // Reports
  async reports_daily_sales(date: string): Promise<ApiResponse<DailySales>> {
    await delay(200);
    return {
      success: true,
      data: {
        date,
        total_sales: 156.5,
        invoice_count: 12,
        average_sale: 13.04,
        by_payment_method: {
          cash: { total: 89.5, count: 7 },
          card: { total: 67.0, count: 5 },
        },
      },
    };
  },

  async reports_period_sales(startDate: string, endDate: string): Promise<ApiResponse<PeriodReport>> {
    await delay(300);
    return {
      success: true,
      data: {
        start_date: startDate,
        end_date: endDate,
        total_sales: 1234.5,
        invoice_count: 89,
        average_sale: 13.87,
        daily_breakdown: [
          { date: startDate, total_sales: 156.5, invoice_count: 12, average_sale: 13.04, by_payment_method: {} },
          { date: endDate, total_sales: 189.0, invoice_count: 15, average_sale: 12.6, by_payment_method: {} },
        ],
        top_products: [
          { product_id: 'PROD002', product_name: 'Cappuccino', quantity_sold: 45, revenue: 157.5 },
          { product_id: 'PROD003', product_name: 'Latte', quantity_sold: 38, revenue: 152.0 },
        ],
        by_payment_method: {
          cash: { total: 678.5, count: 52 },
          card: { total: 556.0, count: 37 },
        },
      },
    };
  },

  async reports_top_products(limit: number): Promise<ApiResponse<TopProduct[]>> {
    await delay(200);
    return {
      success: true,
      data: sampleProducts.slice(0, limit).map((p, i) => ({
        product_id: p.id,
        product_name: p.name,
        quantity_sold: 50 - i * 5,
        revenue: (50 - i * 5) * p.price,
      })),
    };
  },

  async reports_export_csv(
    _reportType: string,
    _params?: Record<string, unknown>
  ): Promise<ApiResponse<{ csv: string }>> {
    await delay(200);
    return {
      success: true,
      data: {
        csv: 'Date,Total Sales,Invoice Count,Average Sale\n2024-01-31,156.50,12,13.04',
      },
    };
  },

  async reports_today_summary(): Promise<ApiResponse<DailySales>> {
    await delay(100);
    const today = new Date().toISOString().split('T')[0];
    return this.reports_daily_sales(today);
  },

  // Email
  async email_test_connection(): Promise<ApiResponse<void>> {
    await delay(500);
    if (!mockSettings.smtp_host) {
      return { success: false, error: 'SMTP not configured' };
    }
    return { success: true };
  },
};
