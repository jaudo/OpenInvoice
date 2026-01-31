import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useCartStore } from '@/stores/cartStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/api/bridge';
import type { Product, Invoice } from '@/types/api';
import {
  Search,
  Plus,
  Minus,
  Trash2,
  ShoppingCart,
  CreditCard,
  Banknote,
  Printer,
  Mail,
  Check,
  X,
  Loader2,
} from 'lucide-react';

export default function InvoicePage() {
  const { t } = useTranslation();
  const { settings } = useSettingsStore();
  const {
    items: cartItems,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    getSubtotal,
    getVatAmount,
    getTotal,
    getItemCount,
  } = useCartStore();

  const [products, setProducts] = useState<Product[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [completedInvoice, setCompletedInvoice] = useState<Invoice | null>(null);
  const [email, setEmail] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);

  const currency = settings.currency_symbol || '€';

  // Load products
  useEffect(() => {
    const loadProducts = async () => {
      setIsLoading(true);
      const response = await api.products.getAll();
      if (response.success && response.data) {
        setProducts(response.data);
      }
      setIsLoading(false);
    };
    loadProducts();
  }, []);

  // Search products
  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    if (query.length === 0) {
      const response = await api.products.getAll();
      if (response.success && response.data) {
        setProducts(response.data);
      }
    } else if (query.length >= 2) {
      const response = await api.products.search(query);
      if (response.success && response.data) {
        setProducts(response.data);
      }
    }
  }, []);

  // Handle barcode scanner input
  useEffect(() => {
    let buffer = '';
    let timeout: NodeJS.Timeout;

    const handleKeyPress = async (e: KeyboardEvent) => {
      // Ignore if in input field (except for barcode entry)
      if (
        document.activeElement?.tagName === 'INPUT' &&
        !(document.activeElement as HTMLInputElement).dataset.barcodeInput
      ) {
        return;
      }

      if (e.key === 'Enter' && buffer.length > 0) {
        // Try to find product by barcode
        const response = await api.products.getByBarcode(buffer);
        if (response.success && response.data) {
          addItem(response.data);
        }
        buffer = '';
      } else if (e.key.length === 1) {
        buffer += e.key;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          buffer = '';
        }, 100);
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => {
      window.removeEventListener('keypress', handleKeyPress);
      clearTimeout(timeout);
    };
  }, [addItem]);

  const handleCheckout = async (paymentMethod: 'cash' | 'card') => {
    if (cartItems.length === 0) return;

    setIsCheckingOut(true);
    try {
      const items = cartItems.map((item) => ({
        product_id: item.product.id,
        quantity: item.quantity,
      }));

      const response = await api.invoices.create(items, paymentMethod);

      if (response.success && response.data) {
        setCompletedInvoice(response.data);
        clearCart();
        setShowCheckout(false);
      }
    } catch (error) {
      console.error('Checkout failed:', error);
    }
    setIsCheckingOut(false);
  };

  const handlePrint = async () => {
    if (!completedInvoice) return;
    await api.printing.printReceipt(completedInvoice.id);
  };

  const handleSendEmail = async () => {
    if (!completedInvoice || !email) return;
    setSendingEmail(true);
    await api.printing.sendEmail(completedInvoice.id, email);
    setSendingEmail(false);
  };

  const handleNewSale = () => {
    setCompletedInvoice(null);
    setEmail('');
  };

  // Show completed invoice
  if (completedInvoice) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">{t('invoice.receiptReady')}</h2>
            <p className="text-gray-600">#{completedInvoice.invoice_number}</p>
          </div>

          {/* QR Code */}
          {completedInvoice.qr_image && (
            <div className="qr-container mb-6">
              <img
                src={`data:image/png;base64,${completedInvoice.qr_image}`}
                alt="QR Code"
                className="w-48 h-48"
              />
            </div>
          )}

          {/* Total */}
          <div className="text-center mb-6">
            <p className="text-gray-600">{t('invoice.total')}</p>
            <p className="text-3xl font-bold text-gray-900">
              {currency}{completedInvoice.total.toFixed(2)}
            </p>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            <button
              onClick={handlePrint}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90"
            >
              <Printer className="w-5 h-5" />
              {t('invoice.print')}
            </button>

            <div className="flex gap-2">
              <input
                type="email"
                placeholder={t('invoice.emailPlaceholder')}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
              <button
                onClick={handleSendEmail}
                disabled={!email || sendingEmail}
                className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                {sendingEmail ? <Loader2 className="w-5 h-5 animate-spin" /> : <Mail className="w-5 h-5" />}
              </button>
            </div>

            <button
              onClick={handleNewSale}
              className="w-full px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              {t('invoice.newSale')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-120px)]">
      {/* Products Section */}
      <div className="flex-1 p-4 overflow-auto">
        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder={t('invoice.searchProducts')}
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            data-barcode-input
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          />
        </div>

        {/* Product Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="product-grid">
            {products.map((product) => (
              <button
                key={product.id}
                onClick={() => addItem(product)}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-left hover:shadow-md hover:border-primary transition-all"
              >
                <h3 className="font-medium text-gray-900 truncate">{product.name}</h3>
                <p className="text-sm text-gray-500 truncate">{product.description}</p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-lg font-bold text-primary">
                    {currency}{product.price.toFixed(2)}
                  </span>
                  {product.stock <= 5 && (
                    <span className="text-xs text-orange-600 bg-orange-100 px-2 py-1 rounded">
                      {product.stock} left
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Cart Section */}
      <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
        {/* Cart Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900">{t('invoice.cart')}</h2>
            <span className="ml-auto bg-primary text-white text-sm px-2 py-0.5 rounded-full">
              {getItemCount()}
            </span>
          </div>
        </div>

        {/* Cart Items */}
        <div className="flex-1 overflow-auto p-4">
          {cartItems.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <ShoppingCart className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>{t('invoice.emptyCart')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {cartItems.map((item) => (
                <div key={item.product.id} className="cart-item bg-gray-50 rounded-lg p-3">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 truncate">{item.product.name}</h4>
                      <p className="text-sm text-gray-500">
                        {currency}{item.product.price.toFixed(2)} each
                      </p>
                    </div>
                    <button
                      onClick={() => removeItem(item.product.id)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                        className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300"
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                      <span className="w-8 text-center font-medium">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                        className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                    <span className="font-semibold text-gray-900">
                      {currency}{(item.product.price * item.quantity).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Cart Footer */}
        <div className="border-t border-gray-200 p-4">
          {/* Totals */}
          <div className="space-y-2 mb-4">
            <div className="flex justify-between text-sm text-gray-600">
              <span>{t('invoice.subtotal')}</span>
              <span>{currency}{getSubtotal().toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>{t('invoice.vat')}</span>
              <span>{currency}{getVatAmount().toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-lg font-bold text-gray-900">
              <span>{t('invoice.total')}</span>
              <span>{currency}{getTotal().toFixed(2)}</span>
            </div>
          </div>

          {/* Checkout Buttons */}
          {showCheckout ? (
            <div className="space-y-2">
              <button
                onClick={() => handleCheckout('cash')}
                disabled={isCheckingOut || cartItems.length === 0}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {isCheckingOut ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Banknote className="w-5 h-5" />
                )}
                {t('invoice.cash')}
              </button>
              <button
                onClick={() => handleCheckout('card')}
                disabled={isCheckingOut || cartItems.length === 0}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isCheckingOut ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <CreditCard className="w-5 h-5" />
                )}
                {t('invoice.card')}
              </button>
              <button
                onClick={() => setShowCheckout(false)}
                className="w-full px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                {t('common.cancel')}
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowCheckout(true)}
              disabled={cartItems.length === 0}
              className="w-full px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {t('invoice.checkout')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
