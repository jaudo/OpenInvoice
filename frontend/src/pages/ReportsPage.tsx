import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/api/bridge';
import type { DailySales, PeriodReport, TopProduct } from '@/types/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Calendar,
  Download,
  TrendingUp,
  Receipt,
  DollarSign,
  Loader2,
  BarChart3,
} from 'lucide-react';

export default function ReportsPage() {
  const { t } = useTranslation();
  const { settings } = useSettingsStore();
  const currency = settings.currency_symbol || '€';

  const [isLoading, setIsLoading] = useState(false);
  const [reportType, setReportType] = useState<'daily' | 'period'>('period');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [startDate, setStartDate] = useState(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  const [dailyReport, setDailyReport] = useState<DailySales | null>(null);
  const [periodReport, setPeriodReport] = useState<PeriodReport | null>(null);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    setIsLoading(true);
    try {
      if (reportType === 'daily') {
        const response = await api.reports.dailySales(selectedDate);
        if (response.success && response.data) {
          setDailyReport(response.data);
        }
      } else {
        const response = await api.reports.periodSales(startDate, endDate);
        if (response.success && response.data) {
          setPeriodReport(response.data);
          setTopProducts(response.data.top_products || []);
        }
      }
    } catch (error) {
      console.error('Failed to load report:', error);
    }
    setIsLoading(false);
  };

  const handleExport = async () => {
    try {
      const params =
        reportType === 'daily'
          ? { date: selectedDate }
          : { start_date: startDate, end_date: endDate };

      const response = await api.reports.exportCsv(reportType, params);
      if (response.success && response.data?.csv) {
        // Create download
        const blob = new Blob([response.data.csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${reportType}_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const report = reportType === 'daily' ? dailyReport : periodReport;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('reports.title')}</h1>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap items-end gap-4">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Report Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as 'daily' | 'period')}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            >
              <option value="daily">{t('reports.dailySales')}</option>
              <option value="period">{t('reports.periodSales')}</option>
            </select>
          </div>

          {/* Date Selection */}
          {reportType === 'daily' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('reports.date')}
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('reports.startDate')}
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('reports.endDate')}
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                />
              </div>
            </>
          )}

          {/* Actions */}
          <button
            onClick={loadReport}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calendar className="w-4 h-4" />}
            {t('reports.generate')}
          </button>

          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            <Download className="w-4 h-4" />
            {t('reports.export')}
          </button>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      )}

      {/* Report Content */}
      {!isLoading && report && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{t('reports.totalSales')}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {currency}{report.total_sales.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Receipt className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{t('reports.invoiceCount')}</p>
                  <p className="text-2xl font-bold text-gray-900">{report.invoice_count}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{t('reports.averageSale')}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {currency}{report.average_sale.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Payment Method Breakdown */}
          {report.by_payment_method && Object.keys(report.by_payment_method).length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
              <h3 className="font-semibold text-gray-900 mb-4">{t('reports.byPaymentMethod')}</h3>
              <div className="flex gap-6">
                {Object.entries(report.by_payment_method).map(([method, data]) => (
                  <div key={method} className="text-center">
                    <p className="text-sm text-gray-500 capitalize">{method}</p>
                    <p className="text-lg font-bold text-gray-900">
                      {currency}{data.total.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500">{data.count} invoices</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Chart for Period Report */}
          {reportType === 'period' && periodReport?.daily_breakdown && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
              <h3 className="font-semibold text-gray-900 mb-4">{t('reports.dailySales')}</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={periodReport.daily_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis />
                    <Tooltip
                      formatter={(value: number) => [`${currency}${value.toFixed(2)}`, 'Sales']}
                      labelFormatter={(label) => new Date(label).toLocaleDateString()}
                    />
                    <Bar dataKey="total_sales" fill="hsl(142.1, 76.2%, 36.3%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Top Products */}
          {topProducts.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-900 mb-4">{t('reports.topProducts')}</h3>
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">#</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
                      {t('products.name')}
                    </th>
                    <th className="px-4 py-2 text-right text-sm font-medium text-gray-700">
                      {t('reports.quantitySold')}
                    </th>
                    <th className="px-4 py-2 text-right text-sm font-medium text-gray-700">
                      {t('reports.revenue')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {topProducts.map((product, index) => (
                    <tr key={product.product_id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-500">{index + 1}</td>
                      <td className="px-4 py-2 font-medium">{product.product_name}</td>
                      <td className="px-4 py-2 text-right">{product.quantity_sold}</td>
                      <td className="px-4 py-2 text-right font-medium">
                        {currency}{product.revenue.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* No Data */}
      {!isLoading && !report && (
        <div className="text-center py-12">
          <BarChart3 className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">{t('reports.noData')}</p>
        </div>
      )}
    </div>
  );
}
