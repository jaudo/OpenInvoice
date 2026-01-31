import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '@/stores/settingsStore';
import { api } from '@/api/bridge';
import { languages } from '@/i18n';
import type { KeyboardLayout, PrinterStatus } from '@/types/api';
import {
  Globe,
  Store,
  Printer,
  Mail,
  Keyboard,
  Save,
  Check,
  X,
  Loader2,
  AlertCircle,
  TestTube,
} from 'lucide-react';

export default function ConfigPage() {
  const { t, i18n } = useTranslation();
  const { settings, loadSettings, updateSettings } = useSettingsStore();

  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [printerStatus, setPrinterStatus] = useState<PrinterStatus | null>(null);
  const [keyboardLayouts, setKeyboardLayouts] = useState<KeyboardLayout[]>([]);
  const [testingPrinter, setTestingPrinter] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);

  // Local form state
  const [formData, setFormData] = useState({
    language: settings.language,
    store_name: settings.store_name,
    seller_id: settings.seller_id,
    currency_symbol: settings.currency_symbol,
    default_vat_rate: settings.default_vat_rate.toString(),
    printer_enabled: settings.printer_enabled,
    smtp_host: settings.smtp_host,
    smtp_port: settings.smtp_port.toString(),
    smtp_username: settings.smtp_username,
    smtp_password: settings.smtp_password,
    smtp_use_tls: settings.smtp_use_tls,
    keyboard_layout: settings.keyboard_layout,
  });

  // Load data on mount
  useEffect(() => {
    loadSettings();
    loadPrinterStatus();
    loadKeyboardLayouts();
  }, [loadSettings]);

  // Sync form with settings
  useEffect(() => {
    setFormData({
      language: settings.language,
      store_name: settings.store_name,
      seller_id: settings.seller_id,
      currency_symbol: settings.currency_symbol,
      default_vat_rate: settings.default_vat_rate.toString(),
      printer_enabled: settings.printer_enabled,
      smtp_host: settings.smtp_host,
      smtp_port: settings.smtp_port.toString(),
      smtp_username: settings.smtp_username,
      smtp_password: settings.smtp_password,
      smtp_use_tls: settings.smtp_use_tls,
      keyboard_layout: settings.keyboard_layout,
    });
  }, [settings]);

  const loadPrinterStatus = async () => {
    const response = await api.printer.getStatus();
    if (response.success && response.data) {
      setPrinterStatus(response.data);
    }
  };

  const loadKeyboardLayouts = async () => {
    const response = await api.settings.getKeyboardLayouts();
    if (response.success && response.data) {
      setKeyboardLayouts(response.data);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');

    try {
      await updateSettings({
        language: formData.language,
        store_name: formData.store_name,
        seller_id: formData.seller_id,
        currency_symbol: formData.currency_symbol,
        default_vat_rate: parseFloat(formData.default_vat_rate),
        printer_enabled: formData.printer_enabled,
        smtp_host: formData.smtp_host,
        smtp_port: parseInt(formData.smtp_port),
        smtp_username: formData.smtp_username,
        smtp_password: formData.smtp_password,
        smtp_use_tls: formData.smtp_use_tls,
        keyboard_layout: formData.keyboard_layout,
      });

      // Change language if needed
      if (formData.language !== i18n.language) {
        i18n.changeLanguage(formData.language);
      }

      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      setSaveStatus('error');
    }

    setIsSaving(false);
  };

  const handleTestPrinter = async () => {
    setTestingPrinter(true);
    await api.printer.test();
    setTestingPrinter(false);
  };

  const handleTestEmail = async () => {
    setTestingEmail(true);
    const response = await api.email.testConnection();
    setTestingEmail(false);
    if (response.success) {
      alert('Email connection successful!');
    } else {
      alert(`Email test failed: ${response.error}`);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('config.title')}</h1>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            saveStatus === 'success'
              ? 'bg-green-600 text-white'
              : saveStatus === 'error'
              ? 'bg-red-600 text-white'
              : 'bg-primary text-white hover:bg-primary/90'
          } disabled:opacity-50`}
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : saveStatus === 'success' ? (
            <Check className="w-4 h-4" />
          ) : saveStatus === 'error' ? (
            <X className="w-4 h-4" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {saveStatus === 'success'
            ? t('config.saved')
            : saveStatus === 'error'
            ? t('config.saveError')
            : t('common.save')}
        </button>
      </div>

      <div className="space-y-6">
        {/* General Settings */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Globe className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-gray-900">{t('config.general')}</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.language')}
              </label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* Store Settings */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Store className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-gray-900">{t('config.store')}</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.storeName')}
              </label>
              <input
                type="text"
                value={formData.store_name}
                onChange={(e) => setFormData({ ...formData, store_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.sellerId')}
              </label>
              <input
                type="text"
                value={formData.seller_id}
                onChange={(e) => setFormData({ ...formData, seller_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.currency')}
              </label>
              <input
                type="text"
                value={formData.currency_symbol}
                onChange={(e) => setFormData({ ...formData, currency_symbol: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.defaultVat')} (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.default_vat_rate}
                onChange={(e) => setFormData({ ...formData, default_vat_rate: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          </div>
        </section>

        {/* Printer Settings */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Printer className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-gray-900">{t('config.printer')}</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{t('config.printerEnabled')}</p>
                <p className="text-sm text-gray-500">{t('config.printerStatus')}: {' '}
                  <span className={printerStatus?.connected ? 'text-green-600' : 'text-red-600'}>
                    {printerStatus?.connected ? t('config.connected') : t('config.disconnected')}
                  </span>
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.printer_enabled}
                  onChange={(e) =>
                    setFormData({ ...formData, printer_enabled: e.target.checked })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            <button
              onClick={handleTestPrinter}
              disabled={testingPrinter || !formData.printer_enabled}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {testingPrinter ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <TestTube className="w-4 h-4" />
              )}
              {t('config.testPrint')}
            </button>
          </div>
        </section>

        {/* Email Settings */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Mail className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-gray-900">{t('config.email')}</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.smtpHost')}
              </label>
              <input
                type="text"
                value={formData.smtp_host}
                onChange={(e) => setFormData({ ...formData, smtp_host: e.target.value })}
                placeholder="smtp.gmail.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.smtpPort')}
              </label>
              <input
                type="number"
                value={formData.smtp_port}
                onChange={(e) => setFormData({ ...formData, smtp_port: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.smtpUsername')}
              </label>
              <input
                type="text"
                value={formData.smtp_username}
                onChange={(e) => setFormData({ ...formData, smtp_username: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.smtpPassword')}
              </label>
              <input
                type="password"
                value={formData.smtp_password}
                onChange={(e) => setFormData({ ...formData, smtp_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.smtp_use_tls}
                onChange={(e) => setFormData({ ...formData, smtp_use_tls: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm text-gray-700">{t('config.smtpTls')}</span>
            </label>

            <button
              onClick={handleTestEmail}
              disabled={testingEmail || !formData.smtp_host}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {testingEmail ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <TestTube className="w-4 h-4" />
              )}
              {t('config.testEmail')}
            </button>
          </div>
        </section>

        {/* Scanner Settings */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Keyboard className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-gray-900">{t('config.scanner')}</h2>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('config.keyboardLayout')}
            </label>
            <select
              value={formData.keyboard_layout}
              onChange={(e) => setFormData({ ...formData, keyboard_layout: e.target.value })}
              className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            >
              {keyboardLayouts.map((layout) => (
                <option key={layout.id} value={layout.id}>
                  {layout.name} - {layout.description}
                </option>
              ))}
            </select>
          </div>
        </section>
      </div>
    </div>
  );
}
