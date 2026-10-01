import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { DataRecord } from '../types';
import { Database, AlertTriangle, Clock, ShieldCheck, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    apiService.getDataRecords()
      .then(data => {
        setRecords(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load dashboard records:', err);
        setLoading(false);
      });
  }, []);

  const totalCount = records.length;
  const expiredCount = records.filter(r => r.status === 'Expired').length;
  const expiringSoonCount = records.filter(r => r.status === 'Expiring Soon').length;
  const mismatchCount = records.filter(r => r.purpose_mismatch).length;

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div>
        <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-sky-950 text-sky-400 border border-sky-800 mb-2">
          FOUNDATION READY
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100">Governance Overview Dashboard</h1>
        <p className="text-slate-400 mt-1">Real-time enterprise data lifecycle tracking and purpose governance metrics.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-sm font-medium">Total Data Records</span>
            <Database className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-3xl font-bold text-slate-100">{loading ? '...' : totalCount}</div>
          <p className="text-xs text-slate-500 font-mono">Synced from SQLite / Postgres</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-sm font-medium">Expired Records</span>
            <Clock className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-bold text-rose-400">{loading ? '...' : expiredCount}</div>
          <p className="text-xs text-slate-500 font-mono">Action required (Anonymize / Delete)</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-sm font-medium">Expiring Soon</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-amber-400">{loading ? '...' : expiringSoonCount}</div>
          <p className="text-xs text-slate-500 font-mono">Within 30-day window</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-sm font-medium">Purpose Mismatches</span>
            <AlertTriangle className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-purple-400">{loading ? '...' : mismatchCount}</div>
          <p className="text-xs text-slate-500 font-mono">Flagged by governance schema</p>
        </div>
      </div>

      {/* Quick Navigation Cards for Team Members */}
      <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
        <h2 className="text-lg font-semibold text-slate-200">Team Module Handoff & Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/inventory" className="p-4 rounded-lg bg-slate-900 border border-slate-800 hover:border-sky-500/50 transition-all group">
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold text-sky-400 group-hover:underline">Data Inventory</span>
              <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400" />
            </div>
            <p className="text-xs text-slate-400">View and manage full synthetic records catalog.</p>
            <span className="inline-block mt-3 text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">Assigned to Team 3</span>
          </Link>

          <Link to="/purpose-mismatch" className="p-4 rounded-lg bg-slate-900 border border-slate-800 hover:border-purple-500/50 transition-all group">
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold text-purple-400 group-hover:underline">AI & Mismatch Engine</span>
              <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400" />
            </div>
            <p className="text-xs text-slate-400">Purpose divergence scoring and LLM recommendations.</p>
            <span className="inline-block mt-3 text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">Assigned to Team 2</span>
          </Link>

          <Link to="/policy" className="p-4 rounded-lg bg-slate-900 border border-slate-800 hover:border-amber-500/50 transition-all group">
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold text-amber-400 group-hover:underline">Policy & Audit Engine</span>
              <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400" />
            </div>
            <p className="text-xs text-slate-400">Automated retention rules, deletion triggers & logs.</p>
            <span className="inline-block mt-3 text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">Assigned to Team 4</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
