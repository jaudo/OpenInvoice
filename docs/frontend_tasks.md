# Frontend Tasks - Open Invoice POS

## Overview

This document contains prioritized frontend tasks for the Open Invoice POS system. Each task includes acceptance criteria and implementation notes.

**Important:** During development, use `mock.ts` for API calls. This allows frontend development without backend dependency.

---

## F1: Project Setup

**Priority:** Critical (Foundation)

### Tasks
- [ ] Initialize Vite + React + TypeScript project
- [ ] Configure Tailwind CSS
- [ ] Setup path aliases (@/ for src/)
- [ ] Configure ESLint + Prettier
- [ ] Create folder structure

### Commands
```bash
npm create vite@latest . -- --template react-ts
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install -D @types/node
```

### Folder Structure
```
src/
├── api/
│   ├── bridge.ts
│   └── mock.ts
├── components/
│   ├── ui/
│   └── common/
├── pages/
├── i18n/
│   └── locales/
├── stores/
├── types/
└── App.tsx
```

### Acceptance Criteria
- `npm run dev` starts development server
- Tailwind classes work
- TypeScript compiles without errors
- Path aliases resolve correctly (@/components/...)

---

## F2: API Bridge + Mock

**Priority:** Critical (Development Foundation)

### Tasks
- [ ] Create TypeScript types for all API responses
- [ ] Implement bridge.ts wrapper for pywebview.api
- [ ] Implement mock.ts with sample data
- [ ] Auto-detect environment (dev vs production)

### Types (src/types/api.ts)
```typescript
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  vat_rate: number;
  barcode: string;
  stock: number;
  status: 'active' | 'inactive';
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
  items: InvoiceItem[];
  qr_data: string;
  qr_image: string; // base64 PNG
  status: 'completed' | 'returned' | 'partial_return';
  created_at: string;
}

export interface InvoiceItem {
  id: number;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  vat_rate: number;
  line_total: number;
  return_status: 'none' | 'returned';
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface Settings {
  language: string;
  store_name: string;
  seller_id: string;
  printer_enabled: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  keyboard_layout: string;
}
```

### Bridge Implementation (src/api/bridge.ts)
```typescript
import { useMockApi } from './mock';

const isPyWebView = () => typeof window !== 'undefined' && 'pywebview' in window;

export const api = {
  products: {
    getAll: () => isPyWebView()
      ? window.pywebview.api.products_get_all()
      : useMockApi().products.getAll(),
    search: (query: string) => isPyWebView()
      ? window.pywebview.api.products_search(query)
      : useMockApi().products.search(query),
    // ...
  },
  // ...
};
```

### Acceptance Criteria
- TypeScript types for all API entities
- Mock API returns realistic sample data
- Auto-switches between mock and real API
- All API methods have TypeScript signatures

---

## F3: i18n Setup

**Priority:** High (User Experience)

### Tasks
- [ ] Install react-i18next
- [ ] Create translation files for 7 languages
- [ ] Implement language switcher
- [ ] Persist language preference

### Languages
- English (en) - Default
- Spanish (es)
- German (de)
- French (fr)
- Italian (it)
- Portuguese (pt)
- Dutch (nl)

### Setup
```bash
npm install react-i18next i18next i18next-browser-languagedetector
```

### Translation Structure (src/i18n/locales/en.json)
```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "search": "Search",
    "loading": "Loading..."
  },
  "nav": {
    "invoice": "Invoice",
    "scan": "Scan",
    "products": "Products",
    "reports": "Reports",
    "config": "Settings"
  },
  "invoice": {
    "title": "New Invoice",
    "addProduct": "Add Product",
    "cart": "Cart",
    "checkout": "Checkout",
    "total": "Total",
    "subtotal": "Subtotal",
    "vat": "VAT",
    "paymentMethod": "Payment Method",
    "cash": "Cash",
    "card": "Card",
    "print": "Print Receipt",
    "email": "Email Receipt"
  },
  "scan": {
    "title": "Validate Receipt",
    "scanQR": "Scan QR Code",
    "valid": "Valid Receipt",
    "invalid": "Invalid Receipt",
    "details": "Receipt Details"
  },
  "products": {
    "title": "Products",
    "addProduct": "Add Product",
    "importCSV": "Import CSV",
    "name": "Name",
    "price": "Price",
    "stock": "Stock",
    "barcode": "Barcode"
  },
  "reports": {
    "title": "Reports",
    "dailySales": "Daily Sales",
    "periodSales": "Period Sales",
    "topProducts": "Top Products",
    "export": "Export CSV"
  },
  "config": {
    "title": "Settings",
    "language": "Language",
    "store": "Store Settings",
    "printer": "Printer",
    "email": "Email Settings"
  }
}
```

### Acceptance Criteria
- All UI text uses translation keys
- Language persists across sessions
- All 7 languages have complete translations
- Date/number formatting respects locale

---

## F4: Layout & Navigation

**Priority:** High (UI Foundation)

### Tasks
- [ ] Create main layout with tab navigation
- [ ] Implement responsive design
- [ ] Add header with store name + language selector
- [ ] Create tab components (Invoice, Scan, Products, Reports, Config)

### Layout Structure
```
┌─────────────────────────────────────────────────────┐
│  Store Name                    [EN ▼]               │
├─────────────────────────────────────────────────────┤
│  [Invoice] [Scan] [Products] [Reports] [Config]     │
├─────────────────────────────────────────────────────┤
│                                                     │
│                                                     │
│                   Tab Content                       │
│                                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Acceptance Criteria
- Tab navigation works correctly
- Active tab visually highlighted
- Responsive on different screen sizes
- Keyboard navigation supported

---

## F5: State Management (Zustand)

**Priority:** High (Data Layer)

### Tasks
- [ ] Install Zustand
- [ ] Create cart store
- [ ] Create settings store
- [ ] Create products store (cache)
- [ ] Persist settings to localStorage

### Cart Store (src/stores/cartStore.ts)
```typescript
import { create } from 'zustand';
import { CartItem, Product } from '@/types/api';

interface CartStore {
  items: CartItem[];
  addItem: (product: Product, quantity?: number) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  getTotal: () => number;
  getSubtotal: () => number;
  getVatAmount: () => number;
}

export const useCartStore = create<CartStore>((set, get) => ({
  items: [],
  addItem: (product, quantity = 1) => {
    const items = get().items;
    const existing = items.find(i => i.product.id === product.id);
    if (existing) {
      set({
        items: items.map(i =>
          i.product.id === product.id
            ? { ...i, quantity: i.quantity + quantity }
            : i
        )
      });
    } else {
      set({ items: [...items, { product, quantity }] });
    }
  },
  // ...
}));
```

### Settings Store (src/stores/settingsStore.ts)
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Settings } from '@/types/api';

interface SettingsStore {
  settings: Settings;
  updateSetting: (key: keyof Settings, value: any) => void;
  loadFromBackend: () => Promise<void>;
  saveToBackend: () => Promise<void>;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      settings: {
        language: 'en',
        store_name: 'My Store',
        // ...defaults
      },
      // ...
    }),
    { name: 'openinvoice-settings' }
  )
);
```

### Acceptance Criteria
- Cart persists during session
- Settings persist across sessions
- Store updates trigger re-renders
- Computed values (totals) work correctly

---

## F6: Invoice Tab

**Priority:** Critical (Core Feature)

### Tasks
- [ ] Product search/filter component
- [ ] Product grid/list with add button
- [ ] Cart sidebar with quantity controls
- [ ] Checkout modal with payment selection
- [ ] Receipt preview after checkout
- [ ] Print/Email buttons

### Layout
```
┌─────────────────────────────────┬─────────────────┐
│  [Search products...]           │     CART        │
├─────────────────────────────────┤                 │
│  ┌─────┐ ┌─────┐ ┌─────┐       │  Product 1  x2  │
│  │Prod1│ │Prod2│ │Prod3│       │  $19.98         │
│  │$9.99│ │$14.9│ │$5.99│       │  ─────────────  │
│  │[Add]│ │[Add]│ │[Add]│       │  Product 2  x1  │
│  └─────┘ └─────┘ └─────┘       │  $14.99         │
│                                 │                 │
│  ┌─────┐ ┌─────┐ ┌─────┐       │  ═════════════  │
│  │Prod4│ │Prod5│ │Prod6│       │  Subtotal: $34  │
│  └─────┘ └─────┘ └─────┘       │  VAT (21%): $7  │
│                                 │  TOTAL: $41.97  │
│                                 │                 │
│                                 │  [CHECKOUT]     │
└─────────────────────────────────┴─────────────────┘
```

### Barcode Scanner Support
- Listen for rapid keyboard input (scanner simulates typing)
- Detect barcode pattern (13 digits + Enter)
- Auto-add product to cart

### Acceptance Criteria
- Products searchable by name/barcode
- Cart updates in real-time
- Quantity adjustable (+/- buttons)
- Checkout creates invoice via API
- Receipt shown with QR code
- Print/Email options work

---

## F7: Config Tab

**Priority:** High (User Settings)

### Tasks
- [ ] Language selector dropdown
- [ ] Store name/seller ID inputs
- [ ] Printer toggle + test button
- [ ] SMTP configuration form
- [ ] Keyboard layout selector
- [ ] Save button with feedback

### Sections
1. **General**: Language, Store name, Seller ID
2. **Printer**: Enable/disable, Test print
3. **Email**: SMTP host, port, username, password, TLS toggle
4. **Scanner**: Keyboard layout selection

### Acceptance Criteria
- All settings editable
- Changes saved to backend
- Validation on required fields
- Test buttons for printer/email
- Success/error feedback

---

## F8: Scan Tab

**Priority:** High (Validation Feature)

### Tasks
- [ ] QR code scanner component (camera or manual input)
- [ ] Validation result display
- [ ] Invoice details when valid
- [ ] Return processing interface

### Scanner Options
1. **Camera**: Use device camera (if available)
2. **Manual**: Paste QR data or enter invoice number
3. **Hardware**: USB barcode scanner (keyboard input)

### Validation Display
```
┌─────────────────────────────────────────────┐
│           ✓ VALID RECEIPT                   │
│                                             │
│  Invoice: INV-2024-0001                     │
│  Date: 2024-01-31 14:30                     │
│  Total: €125.50                             │
│  Store: My Store                            │
│                                             │
│  Items:                                     │
│  - Widget x2         €19.98                 │
│  - Gadget x1         €14.99   [RETURNED]    │
│  - Thing x3          €89.97                 │
│                                             │
│  [Process Return]                           │
└─────────────────────────────────────────────┘
```

### Acceptance Criteria
- QR validation works via API
- Clear valid/invalid indication
- Full invoice details shown
- Return processing available for valid receipts
- Returned items visually marked

---

## F9: Products Tab

**Priority:** Medium (Inventory)

### Tasks
- [ ] Product list/table with sorting
- [ ] Add/Edit product modal
- [ ] Delete product with confirmation
- [ ] CSV import button + file picker
- [ ] Stock management
- [ ] Product status toggle (active/inactive)

### Layout
```
┌─────────────────────────────────────────────────────┐
│  Products              [Import CSV] [+ Add Product] │
├─────────────────────────────────────────────────────┤
│  [Search...]                                        │
├──────┬──────────────┬────────┬───────┬─────┬───────┤
│  ID  │ Name         │ Price  │ Stock │ VAT │ Status│
├──────┼──────────────┼────────┼───────┼─────┼───────┤
│ P001 │ Widget       │ €9.99  │  100  │ 21% │ Active│
│ P002 │ Gadget       │ €14.99 │   50  │ 21% │ Active│
│ P003 │ Old Product  │ €5.99  │    0  │ 21% │ Inact │
└──────┴──────────────┴────────┴───────┴─────┴───────┘
```

### Acceptance Criteria
- CRUD operations for products
- CSV import with progress/results
- Sortable columns
- Search/filter functionality
- Stock warnings for low inventory

---

## F10: Reports Tab

**Priority:** Medium (Analytics)

### Tasks
- [ ] Date picker for report period
- [ ] Daily sales chart (bar chart)
- [ ] Sales summary cards
- [ ] Top products list
- [ ] Export CSV button

### Layout
```
┌─────────────────────────────────────────────────────┐
│  Reports                                            │
├─────────────────────────────────────────────────────┤
│  Period: [2024-01-01] to [2024-01-31]  [Generate]  │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ €12,450  │  │   156    │  │  €79.81  │          │
│  │  Total   │  │ Invoices │  │ Average  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
├─────────────────────────────────────────────────────┤
│  Daily Sales                                        │
│  ▄▄▄                                               │
│  ███ ▄▄▄     ▄▄▄                                   │
│  ███ ███ ▄▄▄ ███ ▄▄▄                               │
│  ─────────────────────                              │
│  Mon Tue Wed Thu Fri                                │
├─────────────────────────────────────────────────────┤
│  Top Products              [Export CSV]             │
│  1. Widget      - 234 sold - €2,339.66              │
│  2. Gadget      - 156 sold - €2,337.44              │
└─────────────────────────────────────────────────────┘
```

### Charts Library
Use Recharts for charting:
```bash
npm install recharts
```

### Acceptance Criteria
- Date range selection works
- Charts render correctly
- Data updates on period change
- CSV export downloads file
- Summary cards show correct totals

---

## F11: Common Components

**Priority:** Medium (Reusability)

### Tasks
- [ ] Receipt display component
- [ ] Loading spinner
- [ ] Error message component
- [ ] Confirmation modal
- [ ] Toast notifications
- [ ] Empty state component

### UI Components (shadcn/ui)
```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card dialog input label select tabs toast
```

### Acceptance Criteria
- Consistent styling across app
- Accessible components (ARIA)
- Keyboard navigation support
- Loading states for async operations

---

## F12: Integration

**Priority:** Critical (Final Step)

### Tasks
- [ ] Remove mock API dependency
- [ ] Connect all components to real backend
- [ ] Test all API endpoints
- [ ] Handle offline/error states
- [ ] Performance optimization

### Acceptance Criteria
- All features work with real backend
- Errors handled gracefully
- Loading states shown during API calls
- No console errors

---

## F13: Testing

**Priority:** Medium (Quality)

### Tasks
- [ ] Setup Playwright for E2E tests
- [ ] Test invoice creation flow
- [ ] Test QR validation flow
- [ ] Test settings persistence
- [ ] Test language switching

### Setup
```bash
npm install -D @playwright/test
npx playwright install
```

### Test Cases
```typescript
test('create invoice and print receipt', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="product-add-P001"]');
  await page.click('[data-testid="checkout-button"]');
  await page.click('[data-testid="payment-cash"]');
  await page.click('[data-testid="confirm-checkout"]');
  await expect(page.locator('[data-testid="receipt-qr"]')).toBeVisible();
});
```

### Acceptance Criteria
- E2E tests pass consistently
- All critical flows tested
- Tests run in CI pipeline

---

## F14: Build Configuration

**Priority:** Low (Deployment)

### Tasks
- [ ] Configure production build
- [ ] Optimize bundle size
- [ ] Setup environment variables
- [ ] Create build script

### Vite Config (vite.config.ts)
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
  },
});
```

### Acceptance Criteria
- `npm run build` creates production bundle
- Bundle size reasonable (<1MB)
- No development dependencies in build
- Works when loaded by pywebview

---

## Component Checklist

### UI Components (src/components/ui/)
- [ ] Button
- [ ] Card
- [ ] Dialog/Modal
- [ ] Input
- [ ] Label
- [ ] Select
- [ ] Tabs
- [ ] Toast
- [ ] Table
- [ ] Badge
- [ ] Dropdown Menu

### Common Components (src/components/common/)
- [ ] Receipt
- [ ] ProductCard
- [ ] CartItem
- [ ] SearchInput
- [ ] LanguageSelector
- [ ] LoadingSpinner
- [ ] ErrorMessage
- [ ] EmptyState
- [ ] ConfirmDialog
- [ ] DatePicker

### Page Components (src/pages/)
- [ ] InvoicePage
- [ ] ScanPage
- [ ] ProductsPage
- [ ] ReportsPage
- [ ] ConfigPage
