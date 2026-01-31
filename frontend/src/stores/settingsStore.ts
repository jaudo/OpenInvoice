/**
 * Settings Store - Zustand store for application settings
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Settings } from '@/types/api';
import { api } from '@/api/bridge';

interface SettingsStore {
  settings: Settings;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadSettings: () => Promise<void>;
  updateSetting: <K extends keyof Settings>(key: K, value: Settings[K]) => Promise<void>;
  updateSettings: (updates: Partial<Settings>) => Promise<void>;
  setLanguage: (language: string) => void;
}

const defaultSettings: Settings = {
  language: 'en',
  store_name: 'My Store',
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

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      settings: defaultSettings,
      isLoading: false,
      error: null,

      loadSettings: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.settings.getAll();
          if (response.success && response.data) {
            set({ settings: { ...defaultSettings, ...response.data }, isLoading: false });
          } else {
            set({ error: response.error || 'Failed to load settings', isLoading: false });
          }
        } catch (error) {
          set({ error: String(error), isLoading: false });
        }
      },

      updateSetting: async <K extends keyof Settings>(key: K, value: Settings[K]) => {
        const oldValue = get().settings[key];

        // Optimistic update
        set((state) => ({
          settings: { ...state.settings, [key]: value },
        }));

        try {
          const response = await api.settings.update(key, value);
          if (!response.success) {
            // Revert on failure
            set((state) => ({
              settings: { ...state.settings, [key]: oldValue },
              error: response.error || 'Failed to update setting',
            }));
          }
        } catch (error) {
          // Revert on error
          set((state) => ({
            settings: { ...state.settings, [key]: oldValue },
            error: String(error),
          }));
        }
      },

      updateSettings: async (updates: Partial<Settings>) => {
        const oldSettings = get().settings;

        // Optimistic update
        set((state) => ({
          settings: { ...state.settings, ...updates },
        }));

        try {
          const response = await api.settings.updateMany(updates);
          if (!response.success) {
            // Revert on failure
            set({
              settings: oldSettings,
              error: response.error || 'Failed to update settings',
            });
          }
        } catch (error) {
          // Revert on error
          set({
            settings: oldSettings,
            error: String(error),
          });
        }
      },

      setLanguage: (language: string) => {
        set((state) => ({
          settings: { ...state.settings, language },
        }));
        // Also update backend
        api.settings.update('language', language);
      },
    }),
    {
      name: 'openinvoice-settings',
      partialize: (state) => ({ settings: state.settings }),
    }
  )
);
