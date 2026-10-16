import React, { useEffect, useState } from 'react';
import { Navigation } from './Navigation';
import { apiService } from '../services/api';
import { HealthStatus } from '../types';
import { Activity, Moon, Shield, Sun } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [darkMode, setDarkMode] = useState<boolean>(() => localStorage.getItem('dataexpiry-theme') === 'dark');

  useEffect(() => {
    localStorage.setItem('dataexpiry-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  useEffect(() => {
    apiService.getHealth()
      .then(res => {
        setHealth(res);
        setLoading(false);
      })
      .catch(err => {
        console.error("API Healthcheck failed:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className={`flex min-h-screen flex-col bg-slate-900 text-slate-100 lg:flex-row${darkMode ? ' theme-dark' : ''}`}>
      <Navigation apiState={loading ? 'checking' : health?.status === 'ok' ? 'connected' : 'disconnected'} />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="min-h-16 border-b border-slate-800 bg-slate-950/60 backdrop-blur px-4 sm:px-8 py-3 flex items-center justify-between gap-3 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-sky-400" />
            <span className="hidden sm:inline font-semibold text-slate-200">AI-Assisted Data Lifecycle & Purpose Governance</span>
            <span className="sm:hidden font-semibold text-slate-200">Data governance</span>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            <button
              type="button"
              onClick={() => setDarkMode(mode => !mode)}
              aria-label={`Switch to ${darkMode ? 'light' : 'dark'} mode`}
              aria-pressed={darkMode}
              className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-slate-300 transition hover:border-sky-500 hover:text-sky-500"
            >
              {darkMode ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
              <span>{darkMode ? 'Light mode' : 'Dark mode'}</span>
            </button>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800">
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              <span className="text-slate-400">Backend API:</span>
              {loading ? (
                <span className="text-amber-400">Checking...</span>
              ) : health?.status === 'ok' ? (
                <span className="text-emerald-400 font-semibold">{health.service} (v{health.version})</span>
              ) : (
                <span className="text-rose-400">Disconnected</span>
              )}
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
