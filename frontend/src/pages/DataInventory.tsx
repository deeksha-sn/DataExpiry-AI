import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, RefreshCw } from 'lucide-react';
import { apiService } from '../services/api';
import { DataRecord } from '../types';

const selectClass = 'rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200';
const badge = (value: string) => `inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${value === 'Expired' || value === 'High' || value === 'Critical' ? 'border-rose-800 bg-rose-950/60 text-rose-300' : value === 'Expiring Soon' || value === 'Medium' || value === 'REVIEW' ? 'border-amber-800 bg-amber-950/60 text-amber-300' : 'border-emerald-800 bg-emerald-950/50 text-emerald-300'}`;

export const DataInventory: React.FC = () => {
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({ category: '', sensitivity: '', status: '', expiry: '', mismatch: '', recommendation: '' });
  const load = () => { setLoading(true); setError(''); apiService.getDataRecords({ limit: 500 }).then(setRecords).catch(e => setError(e.message || 'Unable to load records.')).finally(() => setLoading(false)); };
  useEffect(load, []);
  const categories = [...new Set(records.map(r => r.category))];
  const visible = useMemo(() => records.filter(r => {
    const q = search.toLowerCase();
    return (!q || [r.record_id, r.data_type, r.category, r.collection_purpose, r.current_usage, r.owner].some(v => v?.toLowerCase().includes(q))) &&
      (!filters.category || r.category === filters.category) && (!filters.sensitivity || r.sensitivity === filters.sensitivity) && (!filters.status || r.status === filters.status) &&
      (!filters.expiry || (() => { const days = (Date.parse(r.expiry_date) - Date.now()) / 86400000; return filters.expiry === 'expired' ? days < 0 : filters.expiry === '30' ? days >= 0 && days <= 30 : days > 30 && days <= 90; })()) &&
      (!filters.mismatch || String(Boolean(r.purpose_mismatch)) === filters.mismatch) && (!filters.recommendation || r.ai_recommendation === filters.recommendation);
  }), [records, search, filters]);
  const setFilter = (key: keyof typeof filters, value: string) => setFilters(old => ({ ...old, [key]: value }));

  return <div className="space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="mb-2 text-xs font-semibold uppercase tracking-[.18em] text-sky-400">Governance · Catalog</p><h1 className="text-3xl font-bold text-white">Data inventory</h1><p className="mt-1 text-sm text-slate-400">Search and review data assets, their declared purpose, and retention state.</p></div><button onClick={load} className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"><RefreshCw size={15}/> Refresh</button></header>
    <section className="rounded-xl border border-slate-800 bg-slate-950 p-4"><div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6"><label className="relative md:col-span-3 xl:col-span-2"><Search size={16} className="absolute left-3 top-3 text-slate-500"/><input aria-label="Search records" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search ID, type, purpose, owner…" className="w-full rounded-lg border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-sm text-white placeholder:text-slate-500"/></label>
      <select aria-label="Filter category" className={selectClass} value={filters.category} onChange={e=>setFilter('category',e.target.value)}><option value="">All categories</option>{categories.map(c=><option key={c}>{c}</option>)}</select>
      <select aria-label="Filter sensitivity" className={selectClass} value={filters.sensitivity} onChange={e=>setFilter('sensitivity',e.target.value)}><option value="">All sensitivities</option>{['High','Medium','Low'].map(v=><option key={v}>{v}</option>)}</select>
      <select aria-label="Filter status" className={selectClass} value={filters.status} onChange={e=>setFilter('status',e.target.value)}><option value="">All statuses</option>{['Active','Expiring Soon','Expired'].map(v=><option key={v}>{v}</option>)}</select>
      <select aria-label="Filter expiry window" className={selectClass} value={filters.expiry} onChange={e=>setFilter('expiry',e.target.value)}><option value="">Any expiry date</option><option value="expired">Past due</option><option value="30">Within 30 days</option><option value="90">31–90 days</option></select>
      <select aria-label="Filter purpose mismatch" className={selectClass} value={filters.mismatch} onChange={e=>setFilter('mismatch',e.target.value)}><option value="">Any purpose status</option><option value="true">Mismatch flagged</option><option value="false">No mismatch</option></select>
      <select aria-label="Filter recommendation" className={selectClass} value={filters.recommendation} onChange={e=>setFilter('recommendation',e.target.value)}><option value="">All recommendations</option>{['KEEP','REVIEW','ANONYMIZE','DELETE'].map(v=><option key={v}>{v}</option>)}</select>
    </div><p className="mt-3 text-xs text-slate-500">{visible.length} of {records.length} records · filtering uses fields returned by the records API</p></section>
    <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">{loading ? <div className="p-14 text-center text-slate-400">Loading records…</div> : error ? <div role="alert" className="p-10 text-center text-rose-300">{error}<button onClick={load} className="ml-3 underline">Try again</button></div> : visible.length === 0 ? <div className="p-14 text-center text-slate-400">No records match these filters.</div> : <div className="overflow-x-auto"><table className="w-full min-w-[1150px] text-left text-sm"><thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase tracking-wide text-slate-400"><tr>{['Record','Category / type','Sensitivity','Collection purpose','Current usage','Created','Expiry','Status','Recommendation'].map(h=><th key={h} className="px-4 py-3 font-medium">{h}</th>)}</tr></thead><tbody className="divide-y divide-slate-800/80">{visible.map(r=><tr key={r.id} className="hover:bg-slate-900/60"><td className="px-4 py-4"><Link className="font-mono font-semibold text-sky-400 hover:underline" to={`/records?id=${encodeURIComponent(r.record_id)}`}>{r.record_id}</Link></td><td className="px-4 py-4"><div className="font-medium text-slate-200">{r.category}</div><div className="text-xs text-slate-500">{r.data_type}</div></td><td className="px-4 py-4"><span className={badge(r.sensitivity)}>{r.sensitivity}</span></td><td className="max-w-56 px-4 py-4 text-slate-300">{r.collection_purpose}</td><td className="max-w-56 px-4 py-4 text-slate-400">{r.current_usage}</td><td className="whitespace-nowrap px-4 py-4 text-slate-400">{r.created_date}</td><td className="whitespace-nowrap px-4 py-4 text-slate-300">{r.expiry_date}</td><td className="px-4 py-4"><span className={badge(r.status)}>{r.status}</span></td><td className="px-4 py-4">{r.ai_recommendation ? <span className={badge(r.ai_recommendation)}>{r.ai_recommendation}</span> : <span className="text-slate-500">Not provided</span>}</td></tr>)}</tbody></table></div>}</section>
  </div>;
};
