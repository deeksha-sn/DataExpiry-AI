import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiService } from '../services/api';
import { DataRecord } from '../types';
import { FileText, Search, Shield, ArrowLeft, Calendar, Tag, User, Server } from 'lucide-react';

export const RecordDetails: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryId = searchParams.get('id') || 'CUS-1001';

  const [inputRecordId, setInputRecordId] = useState<string>(queryId);
  const [record, setRecord] = useState<DataRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecord = (idToFetch: string) => {
    setLoading(true);
    setError(null);
    apiService.getDataRecord(idToFetch)
      .then(data => {
        setRecord(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setRecord(null);
        setLoading(false);
      });
  };

  useEffect(() => {
    if (queryId) {
      setInputRecordId(queryId);
      fetchRecord(queryId);
    }
  }, [queryId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputRecordId.trim()) {
      fetchRecord(inputRecordId.trim());
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 mb-2">
          ASSIGNED TO TEAM MEMBER 3
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100">Data Record Details</h1>
        <p className="text-slate-400 mt-1">Deep inspection of record metadata, collection purpose, and lifecycle status.</p>
      </div>

      {/* Record Lookup Form */}
      <form onSubmit={handleSubmit} className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={inputRecordId}
            onChange={(e) => setInputRecordId(e.target.value)}
            placeholder="Enter Record ID (e.g. CUS-1001, FIN-2001, EMP-3001)..."
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Lookup Record
        </button>
      </form>

      {/* Details Display Card */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 font-mono">Loading record metadata...</div>
      ) : error ? (
        <div className="p-8 rounded-xl bg-rose-950/40 border border-rose-900 text-rose-300 text-center font-mono">
          ⚠️ {error}
        </div>
      ) : record ? (
        <div className="space-y-6">
          <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-slate-400">RECORD IDENTIFIER</span>
                <h2 className="text-2xl font-bold text-sky-400 font-mono">{record.record_id}</h2>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                record.status === 'Expired' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                record.status === 'Expiring Soon' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                'bg-emerald-950 text-emerald-300 border border-emerald-800'
              }`}>
                {record.status}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5"><Tag className="w-3.5 h-3.5 text-slate-500" /> Data Type</span>
                <p className="font-semibold text-slate-200">{record.data_type}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5"><Tag className="w-3.5 h-3.5 text-slate-500" /> Category</span>
                <p className="font-semibold text-slate-200">{record.category}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-slate-500" /> Sensitivity Level</span>
                <p className="font-semibold text-slate-200">{record.sensitivity}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5"><User className="w-3.5 h-3.5 text-slate-500" /> Owner Department</span>
                <p className="font-semibold text-slate-200">{record.owner}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5 text-slate-500" /> Collection Date</span>
                <p className="font-mono text-slate-200">{record.created_date}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5 text-slate-500" /> Mandated Expiry Date</span>
                <p className="font-mono text-slate-200">{record.expiry_date} ({record.retention_period})</p>
              </div>

              <div className="space-y-1 md:col-span-2">
                <span className="text-slate-400 text-xs">Stated Collection Purpose</span>
                <p className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">{record.collection_purpose}</p>
              </div>

              <div className="space-y-1 md:col-span-2">
                <span className="text-slate-400 text-xs">Current Usage</span>
                <p className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">{record.current_usage}</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
