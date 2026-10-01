import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { DataRecord } from '../types';
import { Database, Filter, Search, ShieldAlert, CheckCircle, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DataInventory: React.FC = () => {
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadData = () => {
    setLoading(true);
    apiService.getDataRecords({ category: selectedCategory || undefined })
      .then(data => {
        setRecords(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [selectedCategory]);

  const filteredRecords = records.filter(r => 
    r.record_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.data_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.owner.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 mb-2">
            ASSIGNED TO TEAM MEMBER 3
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">Enterprise Data Inventory</h1>
          <p className="text-slate-400 mt-1">Catalog of discoverable enterprise data assets, usage, and retention schedules.</p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by Record ID, Data Type, or Owner..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Categories</option>
            <option value="Customer">Customer</option>
            <option value="Financial">Financial</option>
            <option value="Employee">Employee</option>
            <option value="Identity">Identity</option>
            <option value="Transaction">Transaction</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 font-mono">Loading data records from API...</div>
        ) : error ? (
          <div className="p-12 text-center text-rose-400 font-mono">Error: {error}</div>
        ) : filteredRecords.length === 0 ? (
          <div className="p-12 text-center text-slate-500 font-mono">No data records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-mono text-xs uppercase">
                <tr>
                  <th className="py-3 px-4">Record ID</th>
                  <th className="py-3 px-4">Data Type</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Sensitivity</th>
                  <th className="py-3 px-4">Owner</th>
                  <th className="py-3 px-4">Expiry Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredRecords.map((record) => (
                  <tr key={record.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-semibold text-sky-400">{record.record_id}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">{record.data_type}</td>
                    <td className="py-3.5 px-4 text-slate-400">{record.category}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        record.sensitivity === 'High' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                        record.sensitivity === 'Medium' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                        'bg-slate-900 text-slate-400 border border-slate-800'
                      }`}>
                        {record.sensitivity}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{record.owner}</td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-300">{record.expiry_date}</td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        record.status === 'Expired' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        record.status === 'Expiring Soon' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                        'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      }`}>
                        {record.status === 'Expired' ? <ShieldAlert className="w-3 h-3" /> :
                         record.status === 'Expiring Soon' ? <Clock className="w-3 h-3" /> :
                         <CheckCircle className="w-3 h-3" />}
                        {record.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/records?id=${record.record_id}`}
                        className="text-xs font-mono text-sky-400 hover:text-sky-300 hover:underline"
                      >
                        View Record →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
