import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/api/bridge';
import type { ValidationResult, Invoice } from '@/types/api';
import {
  QrCode,
  Search,
  Check,
  X,
  AlertCircle,
  RotateCcw,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

export default function ScanPage() {
  const { t } = useTranslation();
  const { settings } = useSettingsStore();
  const currency = settings.currency_symbol || '€';

  const [inputValue, setInputValue] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [isProcessingReturn, setIsProcessingReturn] = useState(false);
  const [returnResult, setReturnResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleValidate = async () => {
    if (!inputValue.trim()) return;

    setIsValidating(true);
    setResult(null);
    setInvoice(null);
    setReturnResult(null);

    try {
      // Check if input looks like a QR data string or invoice number
      if (inputValue.startsWith('OPENINVOICE|')) {
        // QR data
        const response = await api.validation.validateQr(inputValue);
        if (response.success && response.data) {
          setResult(response.data);
          if (response.data.invoice_data) {
            setInvoice(response.data.invoice_data);
          }
        }
      } else {
        // Invoice number
        const response = await api.invoices.getByNumber(inputValue);
        if (response.success && response.data) {
          setInvoice(response.data);
          setResult({
            valid: true,
            invoice_number: response.data.invoice_number,
            invoice_data: response.data,
            checks: {
              invoice_exists: true,
              hash_verified: true,
            },
          });
        } else {
          setResult({
            valid: false,
            error_message: response.error || t('errors.notFound'),
          });
        }
      }
    } catch (error) {
      setResult({
        valid: false,
        error_message: t('errors.generic'),
      });
    }

    setIsValidating(false);
  };

  const handleToggleItem = (itemId: number) => {
    setSelectedItems((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    );
  };

  const handleProcessReturn = async () => {
    if (!invoice || selectedItems.length === 0) return;

    setIsProcessingReturn(true);
    try {
      const response = await api.invoices.processReturn(invoice.invoice_number, selectedItems);
      if (response.success && response.data) {
        setReturnResult({
          success: true,
          message: `${t('scan.returnSuccess')} - ${currency}${response.data.refund_amount.toFixed(2)}`,
        });
        // Refresh invoice data
        const refreshed = await api.invoices.getByNumber(invoice.invoice_number);
        if (refreshed.success && refreshed.data) {
          setInvoice(refreshed.data);
        }
        setSelectedItems([]);
      } else {
        setReturnResult({
          success: false,
          message: response.error || t('errors.generic'),
        });
      }
    } catch (error) {
      setReturnResult({
        success: false,
        message: t('errors.generic'),
      });
    }
    setIsProcessingReturn(false);
  };

  const handleReset = () => {
    setInputValue('');
    setResult(null);
    setInvoice(null);
    setSelectedItems([]);
    setReturnResult(null);
  };

  const getRefundAmount = () => {
    if (!invoice) return 0;
    return invoice.items
      .filter((item) => selectedItems.includes(item.id!))
      .reduce((sum, item) => sum + item.line_total, 0);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('scan.title')}</h1>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <QrCode className="w-8 h-8 text-primary" />
          <div>
            <h2 className="font-semibold text-gray-900">{t('scan.scanQR')}</h2>
            <p className="text-sm text-gray-500">{t('scan.orEnter')}</p>
          </div>
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            placeholder={t('scan.invoiceNumber')}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleValidate()}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
          />
          <button
            onClick={handleValidate}
            disabled={isValidating || !inputValue.trim()}
            className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
          >
            {isValidating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            {t('scan.validate')}
          </button>
          {(result || invoice) && (
            <button
              onClick={handleReset}
              className="px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Return Result */}
      {returnResult && (
        <div
          className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
            returnResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}
        >
          {returnResult.success ? (
            <CheckCircle2 className="w-5 h-5" />
          ) : (
            <XCircle className="w-5 h-5" />
          )}
          {returnResult.message}
        </div>
      )}

      {/* Validation Result */}
      {result && (
        <div
          className={`bg-white rounded-lg shadow-sm border p-6 mb-6 ${
            result.valid ? 'border-green-300' : 'border-red-300'
          }`}
        >
          <div className="flex items-center gap-4 mb-4">
            {result.valid ? (
              <>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Check className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-green-700">{t('scan.valid')}</h3>
                  <p className="text-sm text-gray-600">#{result.invoice_number}</p>
                </div>
              </>
            ) : (
              <>
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                  <X className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-red-700">{t('scan.invalid')}</h3>
                  <p className="text-sm text-red-600">{result.error_message}</p>
                </div>
              </>
            )}
          </div>

          {/* Validation Checks */}
          {result.checks && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
              {Object.entries(result.checks).map(([key, value]) => (
                <div
                  key={key}
                  className={`flex items-center gap-2 text-sm px-3 py-2 rounded ${
                    value ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {value ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <XCircle className="w-4 h-4" />
                  )}
                  {t(`scan.checks.${key.replace('_valid', '').replace('_', '')}`)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Invoice Details */}
      {invoice && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('scan.details')}</h3>

          {/* Invoice Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-500">Invoice</p>
              <p className="font-medium">{invoice.invoice_number}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Date</p>
              <p className="font-medium">{new Date(invoice.created_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">{t('invoice.total')}</p>
              <p className="font-bold text-lg">{currency}{invoice.total.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">{t('products.status')}</p>
              <span
                className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
                  invoice.status === 'completed'
                    ? 'bg-green-100 text-green-700'
                    : invoice.status === 'returned'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}
              >
                {t(`scan.status.${invoice.status}`)}
              </span>
            </div>
          </div>

          {/* Items */}
          <div className="border rounded-lg overflow-hidden mb-6">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                    {invoice.status !== 'returned' && (
                      <input
                        type="checkbox"
                        checked={
                          selectedItems.length ===
                          invoice.items.filter((i) => i.return_status === 'none').length
                        }
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedItems(
                              invoice.items
                                .filter((i) => i.return_status === 'none')
                                .map((i) => i.id!)
                            );
                          } else {
                            setSelectedItems([]);
                          }
                        }}
                        className="rounded"
                      />
                    )}
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                    {t('products.name')}
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">
                    {t('invoice.quantity')}
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">
                    {t('invoice.price')}
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">
                    {t('invoice.total')}
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">
                    {t('products.status')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoice.items.map((item) => (
                  <tr
                    key={item.id}
                    className={item.return_status === 'returned' ? 'bg-gray-50 opacity-60' : ''}
                  >
                    <td className="px-4 py-3">
                      {item.return_status === 'none' && (
                        <input
                          type="checkbox"
                          checked={selectedItems.includes(item.id!)}
                          onChange={() => handleToggleItem(item.id!)}
                          className="rounded"
                        />
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium">{item.product_name}</td>
                    <td className="px-4 py-3 text-center">{item.quantity}</td>
                    <td className="px-4 py-3 text-right">{currency}{item.unit_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-medium">
                      {currency}{item.line_total.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {item.return_status === 'returned' ? (
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-700">
                          {t('scan.status.returned')}
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-700">
                          OK
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Return Action */}
          {invoice.status !== 'returned' && (
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm text-gray-600">{t('scan.selectItems')}</p>
                {selectedItems.length > 0 && (
                  <p className="font-semibold">
                    {t('scan.refundAmount')}: {currency}{getRefundAmount().toFixed(2)}
                  </p>
                )}
              </div>
              <button
                onClick={handleProcessReturn}
                disabled={selectedItems.length === 0 || isProcessingReturn}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isProcessingReturn ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <RotateCcw className="w-5 h-5" />
                )}
                {t('scan.processReturn')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
