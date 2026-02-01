import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '@/api/bridge';
import {
  Database,
  Loader2,
  CheckCircle2,
  XCircle,
  Copy,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';

interface InvoiceListItem {
  id: number;
  invoice_number: string;
  total: number;
  status: string;
  created_at: string;
  hash_prefix: string;
}

interface InvoiceDebugData {
  invoice_number: string;
  seller_id: string;
  store_name: string;
  subtotal: number;
  vat_amount: number;
  total: number;
  payment_method: string;
  customer_email: string | null;
  previous_hash: string | null;
  current_hash: string;
  qr_data: string;
  status: string;
  created_at: string;
  items: Array<{
    id: number;
    product_id: string;
    product_name: string;
    quantity: number;
    unit_price: number;
    vat_rate: number;
    line_total: number;
    return_status: string;
  }>;
  // Debug fields
  recalculated_hash?: string;
  hash_matches?: boolean;
  hash_input?: string;
}

export default function DatabasePage() {
  const { t } = useTranslation();
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [invoiceData, setInvoiceData] = useState<InvoiceDebugData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load invoice list on mount
  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    setIsLoadingList(true);
    try {
      const response = await api.database.listInvoices();
      if (response.success && response.data) {
        setInvoices(response.data as InvoiceListItem[]);
      }
    } catch (err) {
      console.error('Failed to load invoices:', err);
    }
    setIsLoadingList(false);
  };

  const handleSearch = async (searchNumber?: string) => {
    const numToSearch = searchNumber || invoiceNumber.trim();
    if (!numToSearch) return;

    setIsLoading(true);
    setError(null);
    setInvoiceData(null);
    setInvoiceNumber(numToSearch);

    try {
      const response = await api.database.getInvoiceDebug(numToSearch);
      if (response.success && response.data) {
        setInvoiceData(response.data as InvoiceDebugData);
      } else {
        setError(response.error || 'Invoice not found');
      }
    } catch (err) {
      setError('Failed to fetch invoice data');
    }

    setIsLoading(false);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const Field = ({ label, value, mono = false }: { label: string; value: string | number | null; mono?: boolean }) => (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-gray-500 uppercase">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`text-sm ${mono ? 'font-mono bg-gray-100 px-2 py-1 rounded' : ''}`}>
          {value ?? 'null'}
        </span>
        {mono && value && (
          <button
            onClick={() => copyToClipboard(String(value))}
            className="p-1 hover:bg-gray-200 rounded"
            title="Copy"
          >
            <Copy className="w-3 h-3 text-gray-500" />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Database className="w-8 h-8 text-primary" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('database.title')}</h1>
          <p className="text-sm text-gray-500">{t('database.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Invoice List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">{t('database.invoiceList')}</h2>
              <button
                onClick={loadInvoices}
                disabled={isLoadingList}
                className="p-2 hover:bg-gray-100 rounded-lg"
                title={t('common.refresh')}
              >
                <RefreshCw className={`w-4 h-4 ${isLoadingList ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {isLoadingList ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : invoices.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">{t('database.noInvoices')}</p>
            ) : (
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {invoices.map((inv) => (
                  <button
                    key={inv.id}
                    onClick={() => handleSearch(inv.invoice_number)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors flex items-center justify-between ${
                      invoiceNumber === inv.invoice_number
                        ? 'border-primary bg-primary/5'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div>
                      <p className="font-medium text-sm">{inv.invoice_number}</p>
                      <p className="text-xs text-gray-500">
                        {inv.total.toFixed(2)} - {inv.created_at}
                      </p>
                      <p className="text-xs font-mono text-gray-400">{inv.hash_prefix}...</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-2">
          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* No Selection */}
          {!invoiceData && !error && !isLoading && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-500">
              <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>{t('database.selectInvoice')}</p>
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <Loader2 className="w-8 h-8 mx-auto animate-spin text-primary" />
            </div>
          )}

          {/* Invoice Data */}
          {invoiceData && (
        <div className="space-y-6">
          {/* Hash Verification Status */}
          <div className={`p-4 rounded-lg border ${invoiceData.hash_matches ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            <div className="flex items-center gap-3">
              {invoiceData.hash_matches ? (
                <CheckCircle2 className="w-6 h-6 text-green-600" />
              ) : (
                <XCircle className="w-6 h-6 text-red-600" />
              )}
              <div>
                <p className={`font-semibold ${invoiceData.hash_matches ? 'text-green-700' : 'text-red-700'}`}>
                  {invoiceData.hash_matches ? t('database.hashValid') : t('database.hashInvalid')}
                </p>
                <p className="text-sm text-gray-600">
                  {invoiceData.hash_matches
                    ? t('database.hashValidDesc')
                    : t('database.hashInvalidDesc')}
                </p>
              </div>
            </div>
          </div>

          {/* Invoice Info */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">{t('database.invoiceInfo')}</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Field label="Invoice Number" value={invoiceData.invoice_number} mono />
              <Field label="Status" value={invoiceData.status} />
              <Field label="Payment Method" value={invoiceData.payment_method} />
              <Field label="Created At" value={invoiceData.created_at} mono />
              <Field label="Seller ID" value={invoiceData.seller_id} mono />
              <Field label="Store Name" value={invoiceData.store_name} />
              <Field label="Customer Email" value={invoiceData.customer_email} />
              <Field label="Subtotal" value={invoiceData.subtotal} />
              <Field label="VAT Amount" value={invoiceData.vat_amount} />
              <Field label="Total" value={invoiceData.total} />
            </div>
          </div>

          {/* Hash Data */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">{t('database.hashInfo')}</h2>
            <div className="space-y-4">
              <Field label="Previous Hash" value={invoiceData.previous_hash} mono />
              <Field label="Current Hash (Stored)" value={invoiceData.current_hash} mono />
              <Field label="Recalculated Hash" value={invoiceData.recalculated_hash || 'N/A'} mono />
              <Field label="QR Data" value={invoiceData.qr_data} mono />
            </div>
          </div>

          {/* Hash Input (for debugging) */}
          {invoiceData.hash_input && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold mb-4">{t('database.hashInput')}</h2>
              <div className="bg-gray-100 p-4 rounded-lg overflow-x-auto">
                <pre className="text-xs font-mono whitespace-pre-wrap break-all">
                  {invoiceData.hash_input}
                </pre>
              </div>
            </div>
          )}

          {/* Items */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">{t('database.items')}</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">Product ID</th>
                    <th className="px-3 py-2 text-left">Name</th>
                    <th className="px-3 py-2 text-right">Qty</th>
                    <th className="px-3 py-2 text-right">Unit Price</th>
                    <th className="px-3 py-2 text-right">VAT %</th>
                    <th className="px-3 py-2 text-right">Line Total</th>
                    <th className="px-3 py-2 text-left">Return Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {invoiceData.items.map((item) => (
                    <tr key={item.id}>
                      <td className="px-3 py-2 font-mono text-xs">{item.id}</td>
                      <td className="px-3 py-2 font-mono text-xs">{item.product_id}</td>
                      <td className="px-3 py-2">{item.product_name}</td>
                      <td className="px-3 py-2 text-right">{item.quantity}</td>
                      <td className="px-3 py-2 text-right font-mono">{item.unit_price}</td>
                      <td className="px-3 py-2 text-right">{item.vat_rate}%</td>
                      <td className="px-3 py-2 text-right font-mono">{item.line_total}</td>
                      <td className="px-3 py-2">{item.return_status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
