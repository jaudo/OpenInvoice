/**
 * API Bridge - Wrapper for pywebview API with fallback to mock
 */

import type {
  ApiResponse,
  Product,
  Invoice,
  Settings,
  ValidationResult,
  DailySales,
  PeriodReport,
  TopProduct,
  KeyboardLayout,
  PrinterStatus,
  ImportResult,
  ChainVerification,
} from '@/types/api';
import { mockApi } from './mock';

// Check if running in pywebview
const isPyWebView = (): boolean => {
  return typeof window !== 'undefined' && 'pywebview' in window && window.pywebview !== undefined;
};

// Get the appropriate API (real or mock)
const getApi = () => {
  if (isPyWebView()) {
    return window.pywebview!.api;
  }
  return mockApi;
};

// API wrapper with consistent interface
export const api = {
  // Products
  products: {
    getAll: (): Promise<ApiResponse<Product[]>> => getApi().products_get_all(),

    search: (query: string): Promise<ApiResponse<Product[]>> => getApi().products_search(query),

    getByBarcode: (barcode: string): Promise<ApiResponse<Product>> =>
      getApi().products_get_by_barcode(barcode),

    create: (data: Partial<Product>): Promise<ApiResponse<Product>> =>
      getApi().products_create(data),

    update: (data: Product): Promise<ApiResponse<Product>> => getApi().products_update(data),

    delete: (productId: string): Promise<ApiResponse<void>> => getApi().products_delete(productId),

    importCsv: (filePath: string): Promise<ApiResponse<ImportResult>> =>
      getApi().products_import_csv(filePath),
  },

  // Invoices
  invoices: {
    create: (
      items: Array<{ product_id: string; quantity: number }>,
      paymentMethod: string,
      customerEmail?: string
    ): Promise<ApiResponse<Invoice>> =>
      getApi().invoices_create(items, paymentMethod, customerEmail),

    getByNumber: (invoiceNumber: string): Promise<ApiResponse<Invoice>> =>
      getApi().invoices_get_by_number(invoiceNumber),

    processReturn: (
      invoiceNumber: string,
      itemIds: number[]
    ): Promise<ApiResponse<{ invoice_number: string; refund_amount: number; new_status: string }>> =>
      getApi().invoices_process_return(invoiceNumber, itemIds),
  },

  // Validation
  validation: {
    validateQr: (qrData: string): Promise<ApiResponse<ValidationResult>> =>
      getApi().qr_validate(qrData),

    verifyChain: (): Promise<ApiResponse<ChainVerification>> => getApi().hash_chain_verify(),
  },

  // Printing/Export
  printing: {
    printReceipt: (invoiceId: number): Promise<ApiResponse<void>> =>
      getApi().print_receipt(invoiceId),

    generatePdf: (invoiceId: number): Promise<ApiResponse<{ path: string }>> =>
      getApi().generate_pdf(invoiceId),

    sendEmail: (invoiceId: number, email: string): Promise<ApiResponse<{ message: string }>> =>
      getApi().send_email(invoiceId, email),
  },

  // Settings
  settings: {
    getAll: (): Promise<ApiResponse<Settings>> => getApi().settings_get_all(),

    update: (key: string, value: unknown): Promise<ApiResponse<void>> =>
      getApi().settings_update(key, value),

    updateMany: (settings: Partial<Settings>): Promise<ApiResponse<void>> =>
      getApi().settings_update_many(settings),

    getKeyboardLayouts: (): Promise<ApiResponse<KeyboardLayout[]>> =>
      getApi().get_keyboard_layouts(),
  },

  // Printer
  printer: {
    getStatus: (): Promise<ApiResponse<PrinterStatus>> => getApi().printer_status(),

    test: (): Promise<ApiResponse<void>> => getApi().printer_test(),
  },

  // Reports
  reports: {
    dailySales: (date: string): Promise<ApiResponse<DailySales>> =>
      getApi().reports_daily_sales(date),

    periodSales: (startDate: string, endDate: string): Promise<ApiResponse<PeriodReport>> =>
      getApi().reports_period_sales(startDate, endDate),

    topProducts: (limit: number = 10): Promise<ApiResponse<TopProduct[]>> =>
      getApi().reports_top_products(limit),

    exportCsv: (
      reportType: string,
      params?: Record<string, unknown>
    ): Promise<ApiResponse<{ csv: string }>> => getApi().reports_export_csv(reportType, params),

    todaySummary: (): Promise<ApiResponse<DailySales>> => getApi().reports_today_summary(),
  },

  // Email
  email: {
    testConnection: (): Promise<ApiResponse<void>> => getApi().email_test_connection(),
  },

  // Database debugging
  database: {
    listInvoices: (): Promise<ApiResponse<unknown>> =>
      getApi().database_list_invoices(),
    getInvoiceDebug: (invoiceNumber: string): Promise<ApiResponse<unknown>> =>
      getApi().database_get_invoice_debug(invoiceNumber),
  },
};

// Export helper to check environment
export { isPyWebView };
