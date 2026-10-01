import React, { useEffect, useState } from 'react';
import { Navigation } from './Navigation';
import { apiService } from '../services/api';
import { HealthStatus } from '../types';
import { Activity, Shield } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

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
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      <Navigation />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-slate-800 bg-slate-950/60 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-sky-400" />
            <span className="font-semibold text-slate-200">AI-Assisted Data Lifecycle & Purpose Governance</span>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
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
        <main className="flex-1 p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
