import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSettingsStore } from '@/stores/settingsStore';
import { languages } from '@/i18n';

// Pages
import InvoicePage from '@/pages/InvoicePage';
import ScanPage from '@/pages/ScanPage';
import ProductsPage from '@/pages/ProductsPage';
import ReportsPage from '@/pages/ReportsPage';
import ConfigPage from '@/pages/ConfigPage';
import DatabasePage from '@/pages/DatabasePage';

// Icons
import {
  Receipt,
  QrCode,
  Package,
  BarChart3,
  Settings,
  Database,
  ChevronDown,
} from 'lucide-react';

type TabId = 'invoice' | 'scan' | 'products' | 'reports' | 'database' | 'config';

interface Tab {
  id: TabId;
  labelKey: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  { id: 'invoice', labelKey: 'nav.invoice', icon: <Receipt className="w-5 h-5" /> },
  { id: 'scan', labelKey: 'nav.scan', icon: <QrCode className="w-5 h-5" /> },
  { id: 'products', labelKey: 'nav.products', icon: <Package className="w-5 h-5" /> },
  { id: 'reports', labelKey: 'nav.reports', icon: <BarChart3 className="w-5 h-5" /> },
  { id: 'database', labelKey: 'nav.database', icon: <Database className="w-5 h-5" /> },
  { id: 'config', labelKey: 'nav.config', icon: <Settings className="w-5 h-5" /> },
];

function App() {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabId>('invoice');
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const { settings, loadSettings } = useSettingsStore();

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  // Sync language with settings
  useEffect(() => {
    if (settings.language && settings.language !== i18n.language) {
      i18n.changeLanguage(settings.language);
    }
  }, [settings.language, i18n]);

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode);
    useSettingsStore.getState().setLanguage(langCode);
    setShowLangDropdown(false);
  };

  const currentLang = languages.find((l) => l.code === i18n.language) || languages[0];

  const renderPage = () => {
    switch (activeTab) {
      case 'invoice':
        return <InvoicePage />;
      case 'scan':
        return <ScanPage />;
      case 'products':
        return <ProductsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'database':
        return <DatabasePage />;
      case 'config':
        return <ConfigPage />;
      default:
        return <InvoicePage />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">
          {settings.store_name || 'Open Invoice'}
        </h1>

        {/* Language Selector */}
        <div className="relative">
          <button
            onClick={() => setShowLangDropdown(!showLangDropdown)}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <span>{currentLang.flag}</span>
            <span>{currentLang.code.toUpperCase()}</span>
            <ChevronDown className="w-4 h-4" />
          </button>

          {showLangDropdown && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowLangDropdown(false)}
              />
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => handleLanguageChange(lang.code)}
                    className={`w-full flex items-center gap-3 px-4 py-2 text-sm text-left hover:bg-gray-100 first:rounded-t-lg last:rounded-b-lg ${
                      lang.code === i18n.language ? 'bg-gray-50 font-medium' : ''
                    }`}
                  >
                    <span>{lang.flag}</span>
                    <span>{lang.name}</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="flex">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'text-primary border-primary bg-primary/5'
                  : 'text-gray-600 border-transparent hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {tab.icon}
              <span>{t(tab.labelKey)}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
