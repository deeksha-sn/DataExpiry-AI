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
  owner: string;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard, owner: 'Foundation' },
  { name: 'Data Inventory', path: '/inventory', icon: Database, owner: 'Team 3' },
  { name: 'Record Details', path: '/records', icon: FileText, owner: 'Team 3' },
  { name: 'Expiry Management', path: '/expiry', icon: Clock, owner: 'Team 3' },
  { name: 'Purpose Mismatch', path: '/purpose-mismatch', icon: AlertTriangle, owner: 'Team 2' },
  { name: 'AI Insights', path: '/ai-insights', icon: Sparkles, owner: 'Team 2' },
  { name: 'Policy Management', path: '/policy', icon: ShieldCheck, owner: 'Team 4' },
  { name: 'Audit Trail', path: '/audit', icon: History, owner: 'Team 4' },
];

export const Navigation: React.FC = () => {
  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between min-h-screen">
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
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
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
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                  item.owner === 'Foundation' ? 'bg-sky-950 text-sky-300 border border-sky-800' :
                  item.owner === 'Team 2' ? 'bg-purple-950 text-purple-300 border border-purple-800' :
                  item.owner === 'Team 3' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                  'bg-amber-950 text-amber-300 border border-amber-800'
                }`}>
                  {item.owner}
                </span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer System Info */}
      <div className="p-4 m-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-400 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-slate-500">System Mode</span>
          <span className="text-sky-400 font-mono">Demo / Synthetic</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">API Status</span>
          <span className="inline-flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Connected
          </span>
        </div>
      </div>
    </aside>
  );
};
