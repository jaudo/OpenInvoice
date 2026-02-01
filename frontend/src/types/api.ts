// API Response types

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Product types
export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  vat_rate: number;
  barcode: string | null;
  stock: number;
  status: 'active' | 'inactive';
  created_at?: string;
}

// Invoice types
export interface InvoiceItem {
  id?: number;
  invoice_id?: number;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  vat_rate: number;
  line_total: number;
  return_status: 'none' | 'returned';
}

export interface Invoice {
  id: number;
  invoice_number: string;
  seller_id: string;
  store_name: string;
  subtotal: number;
  vat_amount: number;
  total: number;
  payment_method: string;
  customer_email?: string;
  previous_hash?: string;
  current_hash: string;
  qr_data: string;
  qr_image?: string;
  status: 'completed' | 'returned' | 'partial_return';
  created_at: string;
  items: InvoiceItem[];
  currency_symbol?: string;
}

// Cart types
export interface CartItem {
  product: Product;
  quantity: number;
}

// Settings types
export interface Settings {
  language: string;
  store_name: string;
  seller_id: string;
  printer_enabled: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_use_tls: boolean;
  keyboard_layout: string;
  currency_symbol: string;
  default_vat_rate: number;
}

// Validation types
export interface ValidationResult {
  valid: boolean;
  invoice_number?: string;
  error_message?: string;
  invoice_data?: Invoice;
  checks?: {
    format_valid?: boolean;
    invoice_exists?: boolean;
    hash_matches?: boolean;
    total_matches?: boolean;
    hash_verified?: boolean;
  };
}

// Report types
export interface DailySales {
  date: string;
  total_sales: number;
  invoice_count: number;
  average_sale: number;
  by_payment_method: Record<string, { total: number; count: number }>;
}

export interface TopProduct {
  product_id: string;
  product_name: string;
  quantity_sold: number;
  revenue: number;
}

export interface PeriodReport {
  start_date: string;
  end_date: string;
  total_sales: number;
  invoice_count: number;
  average_sale: number;
  daily_breakdown: DailySales[];
  top_products: TopProduct[];
  by_payment_method: Record<string, { total: number; count: number }>;
}

// Keyboard layout type
export interface KeyboardLayout {
  id: string;
  name: string;
  description: string;
}

// Printer status
export interface PrinterStatus {
  connected: boolean;
  printer_name: string;
  error?: string;
}

// Import result
export interface ImportResult {
  success: boolean;
  total_rows: number;
  imported: number;
  skipped: number;
  errors: Array<{ row: number; field: string; message: string }>;
  message: string;
}

// Hash chain verification
export interface ChainVerification {
  valid: boolean;
  checked_count: number;
  error_message?: string;
  failed_invoice_id?: number;
}

// Declare pywebview global
declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewAPI;
    };
  }
}

// pywebview API interface
export interface PyWebViewAPI {
  // Products
  products_get_all(): Promise<ApiResponse<Product[]>>;
  products_search(query: string): Promise<ApiResponse<Product[]>>;
  products_get_by_barcode(barcode: string): Promise<ApiResponse<Product>>;
  products_create(data: Partial<Product>): Promise<ApiResponse<Product>>;
  products_update(data: Product): Promise<ApiResponse<Product>>;
  products_delete(product_id: string): Promise<ApiResponse<void>>;
  products_import_csv(file_path: string): Promise<ApiResponse<ImportResult>>;

  // Invoices
  invoices_create(
    items: Array<{ product_id: string; quantity: number }>,
    payment_method: string,
    customer_email?: string
  ): Promise<ApiResponse<Invoice>>;
  invoices_get_by_number(invoice_number: string): Promise<ApiResponse<Invoice>>;
  invoices_process_return(
    invoice_number: string,
    item_ids: number[]
  ): Promise<ApiResponse<{ invoice_number: string; refund_amount: number; new_status: string }>>;

  // Validation
  qr_validate(qr_data: string): Promise<ApiResponse<ValidationResult>>;
  hash_chain_verify(): Promise<ApiResponse<ChainVerification>>;

  // Printing/Export
  print_receipt(invoice_id: number): Promise<ApiResponse<void>>;
  generate_pdf(invoice_id: number): Promise<ApiResponse<{ path: string }>>;
  send_email(invoice_id: number, email: string): Promise<ApiResponse<{ message: string }>>;

  // Settings
  settings_get_all(): Promise<ApiResponse<Settings>>;
  settings_update(key: string, value: unknown): Promise<ApiResponse<void>>;
  settings_update_many(settings: Partial<Settings>): Promise<ApiResponse<void>>;
  get_keyboard_layouts(): Promise<ApiResponse<KeyboardLayout[]>>;

  // Printer
  printer_status(): Promise<ApiResponse<PrinterStatus>>;
  printer_test(): Promise<ApiResponse<void>>;

  // Reports
  reports_daily_sales(date: string): Promise<ApiResponse<DailySales>>;
  reports_period_sales(start_date: string, end_date: string): Promise<ApiResponse<PeriodReport>>;
  reports_top_products(limit: number): Promise<ApiResponse<TopProduct[]>>;
  reports_export_csv(report_type: string, params?: Record<string, unknown>): Promise<ApiResponse<{ csv: string }>>;
  reports_today_summary(): Promise<ApiResponse<DailySales>>;

  // Email
  email_test_connection(): Promise<ApiResponse<void>>;

  // Database debug
  database_list_invoices(): Promise<ApiResponse<unknown>>;
  database_get_invoice_debug(invoice_number: string): Promise<ApiResponse<unknown>>;
}
