import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Database, 
  FileText, 
  Clock, 
  AlertTriangle, 
  Sparkles, 
  ShieldCheck, 
  History,
  Layers
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
}

interface NavigationProps {
  apiState: 'checking' | 'connected' | 'disconnected';
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Data Inventory', path: '/inventory', icon: Database },
  { name: 'Record Details', path: '/records', icon: FileText },
  { name: 'Expiry Management', path: '/expiry', icon: Clock },
  { name: 'Purpose Mismatch', path: '/purpose-mismatch', icon: AlertTriangle },
  { name: 'AI Insights', path: '/ai-insights', icon: Sparkles },
  { name: 'Policy Management', path: '/policy', icon: ShieldCheck },
  { name: 'Audit Trail', path: '/audit', icon: History },
];

export const Navigation: React.FC<NavigationProps> = ({ apiState }) => {
  return (
    <aside className="flex w-full shrink-0 flex-col justify-between border-b border-slate-800 bg-slate-950 lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
      <div>
        {/* Brand Header */}
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-100 tracking-wide">DATAEXPIRY</h1>
            <p className="text-xs text-slate-400 font-mono">Governance Platform</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex gap-1 overflow-x-auto p-3 lg:block lg:space-y-1.5 lg:p-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex shrink-0 items-center justify-between rounded-lg px-3.5 py-2.5 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </div>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer System Info */}
      <div className="m-3 hidden rounded-xl border border-slate-800 bg-slate-900/80 p-4 text-xs text-slate-400 lg:block">
        <div className="flex items-center justify-between">
          <span className="text-slate-500">System Mode</span>
            <span className="text-sky-400 font-mono">Governance</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">API Status</span>
          <span className={`inline-flex items-center gap-1.5 font-medium ${apiState === 'connected' ? 'text-emerald-400' : apiState === 'checking' ? 'text-amber-400' : 'text-rose-400'}`}>
            <span className={`w-2 h-2 rounded-full ${apiState === 'connected' ? 'bg-emerald-400' : apiState === 'checking' ? 'bg-amber-400 animate-pulse' : 'bg-rose-400'}`}></span>
            {apiState === 'connected' ? 'Connected' : apiState === 'checking' ? 'Checking' : 'Disconnected'}
          </span>
        </div>
      </div>
    </aside>
  );
};
