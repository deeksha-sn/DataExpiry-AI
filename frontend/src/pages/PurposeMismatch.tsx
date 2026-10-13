import React, { useEffect, useState, useMemo } from 'react';
import { apiService } from '../services/api';
import { DataRecord, PurposeMismatchResult } from '../types';
import {
  AlertTriangle,
  Sparkles,
  ShieldAlert,
  CheckCircle2,
  Search,
  Filter,
  RefreshCw,
  Play,
  ArrowRight,
  Info,
  X,
  SlidersHorizontal,
  Bot,
  Cpu,
  Layers,
  HelpCircle,
  FileText
} from 'lucide-react';

export const PurposeMismatch: React.FC = () => {
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzingBatch, setAnalyzingBatch] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [mismatchFilter, setMismatchFilter] = useState<string>('ALL'); // 'ALL', 'MISMATCH', 'COMPLIANT'
  const [riskFilter, setRiskFilter] = useState<string>('ALL');

  // Selected Record Modal / Drawer
  const [selectedRecord, setSelectedRecord] = useState<DataRecord | null>(null);
  const [analyzingSingleId, setAnalyzingSingleId] = useState<string | null>(null);

  // Playground / Sandbox state
  const [showPlayground, setShowPlayground] = useState<boolean>(false);
  const [playgroundPurpose, setPlaygroundPurpose] = useState<string>('Account Management & User Profile');
  const [playgroundUsage, setPlaygroundUsage] = useState<string>('Targeted Marketing Campaigns & Ad Retargeting');
  const [playgroundCategory, setPlaygroundCategory] = useState<string>('Customer');
  const [playgroundSensitivity, setPlaygroundSensitivity] = useState<string>('High');
  const [playgroundResult, setPlaygroundResult] = useState<PurposeMismatchResult | null>(null);
  const [playgroundLoading, setPlaygroundLoading] = useState<boolean>(false);

  // Fetch initial records
  const loadRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getDataRecords({ limit: 200 });
      setRecords(data);
    } catch (err: any) {
      console.error('Failed to load records:', err);
      setError(err.message || 'Failed to connect to backend API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, []);

  // Run Batch AI Analysis
  const handleRunBatchAudit = async () => {
    setAnalyzingBatch(true);
    setError(null);
    try {
      await apiService.runBatchAiAnalysis();
      await loadRecords();
    } catch (err: any) {
      console.error('Batch analysis failed:', err);
      setError(err.message || 'Batch analysis failed');
    } finally {
      setAnalyzingBatch(false);
    }
  };

  // Run Single Record Analysis
  const handleAnalyzeSingle = async (recordId: string) => {
    setAnalyzingSingleId(recordId);
    try {
      const result = await apiService.analyzeRecord(recordId);
      // Update local record state
      setRecords(prev =>
        prev.map(r =>
          r.record_id === recordId
            ? {
                ...r,
                purpose_mismatch: result.purpose_mismatch,
                risk_level: result.risk_level,
                ai_recommendation: result.ai_recommendation,
                ai_explanation: result.explanation
              }
            : r
        )
      );
      if (selectedRecord && selectedRecord.record_id === recordId) {
        setSelectedRecord(prev =>
          prev
            ? {
                ...prev,
                purpose_mismatch: result.purpose_mismatch,
                risk_level: result.risk_level,
                ai_recommendation: result.ai_recommendation,
                ai_explanation: result.explanation
              }
            : null
        );
      }
    } catch (err: any) {
      console.error(`Failed to analyze record ${recordId}:`, err);
      setError(err.message || 'Single record analysis failed');
    } finally {
      setAnalyzingSingleId(null);
    }
  };

  // Run Playground Analysis
  const handlePlaygroundSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playgroundPurpose.trim() || !playgroundUsage.trim()) return;

    setPlaygroundLoading(true);
    try {
      const result = await apiService.checkPurposeMismatch({
        collection_purpose: playgroundPurpose,
        current_usage: playgroundUsage,
        category: playgroundCategory,
        sensitivity: playgroundSensitivity,
        status: 'Active'
      });
      setPlaygroundResult(result);
    } catch (err: any) {
      console.error('Playground analysis error:', err);
    } finally {
      setPlaygroundLoading(false);
    }
  };

  // Derived metrics
  const totalAnalyzed = records.length;
  const mismatchCount = useMemo(() => records.filter(r => r.purpose_mismatch).length, [records]);
  const reviewCount = useMemo(
    () => records.filter(r => r.ai_recommendation === 'REVIEW' || r.status === 'Expiring Soon').length,
    [records]
  );
  const criticalCount = useMemo(
    () => records.filter(r => r.risk_level === 'Critical' || (r.purpose_mismatch && r.status === 'Expired')).length,
    [records]
  );

  // Filtered list
  const filteredRecords = useMemo(() => {
    return records.filter(r => {
      // Search
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        r.record_id.toLowerCase().includes(q) ||
        r.data_type.toLowerCase().includes(q) ||
        r.collection_purpose.toLowerCase().includes(q) ||
        r.current_usage.toLowerCase().includes(q) ||
        r.owner.toLowerCase().includes(q);

      // Category
      const matchesCategory = categoryFilter === 'ALL' || r.category === categoryFilter;

      // Mismatch
      const matchesMismatch =
        mismatchFilter === 'ALL' ||
        (mismatchFilter === 'MISMATCH' && r.purpose_mismatch) ||
        (mismatchFilter === 'COMPLIANT' && !r.purpose_mismatch);

      // Risk
      const matchesRisk = riskFilter === 'ALL' || r.risk_level === riskFilter;

      return matchesSearch && matchesCategory && matchesMismatch && matchesRisk;
    });
  }, [records, searchQuery, categoryFilter, mismatchFilter, riskFilter]);

  // Categories list
  const categories = useMemo(() => {
    const set = new Set(records.map(r => r.category).filter(Boolean));
    return Array.from(set);
  }, [records]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-purple-950 text-purple-300 border border-purple-800 mb-2">
            <Bot className="w-3.5 h-3.5 text-purple-400" />
            AI & PURPOSE GOVERNANCE ENGINE
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            Purpose Mismatch Detection
          </h1>
          <p className="text-slate-400 mt-1 max-w-2xl">
            Semantic intelligence engine monitoring data usage creep where active utilization diverges from lawful collection consent.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowPlayground(!showPlayground)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-purple-500/50 text-slate-200 text-sm font-medium transition-all"
          >
            <SlidersHorizontal className="w-4 h-4 text-purple-400" />
            <span>{showPlayground ? 'Hide Sandbox' : 'Interactive Sandbox'}</span>
          </button>

          <button
            onClick={handleRunBatchAudit}
            disabled={analyzingBatch || loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-sm font-medium transition-all shadow-lg shadow-purple-900/30"
          >
            <RefreshCw className={`w-4 h-4 ${analyzingBatch ? 'animate-spin' : ''}`} />
            <span>{analyzingBatch ? 'Running Global Audit...' : 'Scan All Records'}</span>
          </button>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="text-sm font-mono">{error}</span>
          </div>
          <button onClick={loadRecords} className="text-xs underline hover:text-rose-200">
            Retry
          </button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Analyzed */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-1 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-sky-500" />
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Total Records Analyzed</span>
            <Layers className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-3xl font-bold text-slate-100">{loading ? '...' : totalAnalyzed}</div>
          <p className="text-xs text-slate-500">Continuous enterprise data catalog monitoring</p>
        </div>

        {/* Flagged Mismatches */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-1 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-purple-500" />
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Potential Mismatches</span>
            <AlertTriangle className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-purple-400">{loading ? '...' : mismatchCount}</div>
          <p className="text-xs text-slate-500">Active utilization diverges from stated consent</p>
        </div>

        {/* Critical Risk Violations */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-1 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-rose-500" />
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Critical Violations</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-bold text-rose-400">{loading ? '...' : criticalCount}</div>
          <p className="text-xs text-slate-500">Expired records or high-risk secondary monetization</p>
        </div>

        {/* Requiring Review */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-1 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-amber-500" />
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Records In Review</span>
            <HelpCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-amber-400">{loading ? '...' : reviewCount}</div>
          <p className="text-xs text-slate-500">Pending compliance assessment or consent renewal</p>
        </div>
      </div>

      {/* Interactive Purpose Testing Sandbox (Collapsible) */}
      {showPlayground && (
        <div className="p-6 rounded-xl bg-slate-950 border border-purple-900/60 shadow-xl shadow-purple-950/20 space-y-4 transition-all">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-purple-950 border border-purple-800 text-purple-400">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-100">Interactive Purpose Sandbox</h3>
                <p className="text-xs text-slate-400">Test any collection purpose against active operational usage in real time</p>
              </div>
            </div>
            <button
              onClick={() => setShowPlayground(false)}
              className="text-slate-500 hover:text-slate-300 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handlePlaygroundSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  STATED COLLECTION PURPOSE (Consent Basis)
                </label>
                <textarea
                  rows={3}
                  value={playgroundPurpose}
                  onChange={e => setPlaygroundPurpose(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
                  placeholder="e.g. Order Processing & Delivery"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  CURRENT OPERATIONAL USAGE (Active Utilization)
                </label>
                <textarea
                  rows={3}
                  value={playgroundUsage}
                  onChange={e => setPlaygroundUsage(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
                  placeholder="e.g. Targeted Marketing Campaigns & Analytics"
                />
              </div>
            </div>

            {/* Presets and Options */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-500 font-mono">Quick Presets:</span>
                <button
                  type="button"
                  onClick={() => {
                    setPlaygroundPurpose('Customer Support Resolution');
                    setPlaygroundUsage('Helpdesk Inquiries & Ticket Assistance');
                  }}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300"
                >
                  Compatible Support
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPlaygroundPurpose('Account Management');
                    setPlaygroundUsage('Targeted Marketing Campaigns');
                  }}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300"
                >
                  Marketing Creep
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPlaygroundPurpose('Recruitment & Candidate Assessment');
                    setPlaygroundUsage('AI Resume Screening Training & Model Tuning');
                  }}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300"
                >
                  AI Training Creep
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPlaygroundPurpose('UI Experience Optimization');
                    setPlaygroundUsage('Third-Party Data Broker Monetization');
                  }}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300"
                >
                  Broker Monetization
                </button>
              </div>

              <button
                type="submit"
                disabled={playgroundLoading}
                className="flex items-center gap-2 px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-sm font-semibold transition-all shadow-md shadow-purple-900/40"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>{playgroundLoading ? 'Analyzing...' : 'Evaluate Mismatch'}</span>
              </button>
            </div>
          </form>

          {/* Playground Result Display */}
          {playgroundResult && (
            <div className="mt-4 p-4 rounded-xl bg-slate-900/90 border border-purple-800/60 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div className="flex items-center gap-3">
                  <span
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                      playgroundResult.purpose_mismatch
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    {playgroundResult.purpose_mismatch ? (
                      <>
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                        PURPOSE MISMATCH DETECTED
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        PURPOSE COMPLIANT
                      </>
                    )}
                  </span>

                  <span className="text-xs font-mono text-slate-400">
                    Mode:{' '}
                    <span className="text-purple-300 font-semibold uppercase">
                      {playgroundResult.analysis_mode}
                    </span>
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-slate-400">Risk:</span>
                  <span
                    className={`px-2 py-0.5 rounded font-semibold ${
                      playgroundResult.risk_level === 'Critical'
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : playgroundResult.risk_level === 'High'
                        ? 'bg-amber-950 text-amber-300 border border-amber-800'
                        : playgroundResult.risk_level === 'Medium'
                        ? 'bg-sky-950 text-sky-300 border border-sky-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    {playgroundResult.risk_level}
                  </span>

                  <span className="text-slate-400 ml-2">Action:</span>
                  <span className="px-2 py-0.5 rounded font-semibold bg-purple-950 text-purple-300 border border-purple-800">
                    {playgroundResult.ai_recommendation}
                  </span>
                </div>
              </div>

              <div className="text-xs text-slate-300 leading-relaxed font-mono">
                <span className="text-purple-400 font-semibold">Reasoning: </span>
                {playgroundResult.explanation}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by Record ID, Data Type, Purpose, Usage, or Owner..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Mismatch Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={mismatchFilter}
              onChange={e => setMismatchFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
            >
              <option value="ALL">All Mismatch Statuses</option>
              <option value="MISMATCH">Mismatches Only (Flagged)</option>
              <option value="COMPLIANT">Compliant Only</option>
            </select>
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={e => setCategoryFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
          >
            <option value="ALL">All Categories</option>
            {categories.map(c => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          {/* Risk Filter */}
          <select
            value={riskFilter}
            onChange={e => setRiskFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
          >
            <option value="ALL">All Risk Ratings</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {/* Main Records Table */}
      <div className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-16 text-center text-slate-400 font-mono space-y-3">
            <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p>Loading enterprise records from backend...</p>
          </div>
        ) : filteredRecords.length === 0 ? (
          <div className="p-16 text-center text-slate-500 font-mono space-y-2">
            <Info className="w-8 h-8 text-slate-600 mx-auto" />
            <p>No records found matching current search or filter criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-mono text-xs uppercase">
                <tr>
                  <th className="py-3 px-4">Record Identifier</th>
                  <th className="py-3 px-4">Category & Sensitivity</th>
                  <th className="py-3 px-4">Stated Purpose</th>
                  <th className="py-3 px-4">Active Current Usage</th>
                  <th className="py-3 px-4">Mismatch Status</th>
                  <th className="py-3 px-4">Risk & Action</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredRecords.map(record => {
                  const isAnalyzingThis = analyzingSingleId === record.record_id;
                  const isMismatch = record.purpose_mismatch;

                  return (
                    <tr
                      key={record.id}
                      className={`hover:bg-slate-900/60 transition-colors ${
                        isMismatch ? 'bg-purple-950/10' : ''
                      }`}
                    >
                      {/* Record ID */}
                      <td className="py-3.5 px-4 font-mono font-semibold text-slate-200">
                        <div className="flex flex-col">
                          <span className="text-purple-400 hover:underline cursor-pointer" onClick={() => setSelectedRecord(record)}>
                            {record.record_id}
                          </span>
                          <span className="text-xs text-slate-400 font-sans font-normal truncate max-w-[160px]">
                            {record.data_type}
                          </span>
                        </div>
                      </td>

                      {/* Category & Sensitivity */}
                      <td className="py-3.5 px-4">
                        <div className="flex flex-col gap-1 text-xs">
                          <span className="font-medium text-slate-300">{record.category}</span>
                          <span
                            className={`inline-block px-1.5 py-0.5 rounded w-fit font-mono text-[10px] ${
                              record.sensitivity === 'High'
                                ? 'bg-rose-950 text-rose-300 border border-rose-900'
                                : record.sensitivity === 'Medium'
                                ? 'bg-amber-950 text-amber-300 border border-amber-900'
                                : 'bg-slate-900 text-slate-400 border border-slate-800'
                            }`}
                          >
                            {record.sensitivity}
                          </span>
                        </div>
                      </td>

                      {/* Stated Purpose */}
                      <td className="py-3.5 px-4 max-w-[200px]">
                        <span className="text-xs text-slate-300 line-clamp-2" title={record.collection_purpose}>
                          {record.collection_purpose}
                        </span>
                      </td>

                      {/* Current Usage */}
                      <td className="py-3.5 px-4 max-w-[200px]">
                        <span
                          className={`text-xs line-clamp-2 ${
                            isMismatch ? 'text-purple-300 font-medium' : 'text-slate-300'
                          }`}
                          title={record.current_usage}
                        >
                          {record.current_usage}
                        </span>
                      </td>

                      {/* Mismatch Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {isMismatch ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-800">
                            <AlertTriangle className="w-3 h-3 text-rose-400" />
                            Mismatch
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            Compliant
                          </span>
                        )}
                      </td>

                      {/* Risk & Recommendation */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1 text-xs font-mono">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[10px]">RISK:</span>
                            <span
                              className={`font-semibold ${
                                record.risk_level === 'Critical'
                                  ? 'text-rose-400'
                                  : record.risk_level === 'High'
                                  ? 'text-amber-400'
                                  : record.risk_level === 'Medium'
                                  ? 'text-sky-400'
                                  : 'text-emerald-400'
                              }`}
                            >
                              {record.risk_level || 'Low'}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[10px]">ACTION:</span>
                            <span
                              className={`px-1.5 py-0.2 rounded text-[10px] font-semibold ${
                                record.ai_recommendation === 'DELETE'
                                  ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                  : record.ai_recommendation === 'ANONYMIZE'
                                  ? 'bg-sky-950 text-sky-300 border border-sky-800'
                                  : record.ai_recommendation === 'REVIEW'
                                  ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                  : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              }`}
                            >
                              {record.ai_recommendation || 'KEEP'}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleAnalyzeSingle(record.record_id)}
                            disabled={isAnalyzingThis}
                            className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-purple-300 transition-colors text-xs font-mono"
                            title="Re-run AI Analysis"
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzingThis ? 'animate-spin text-purple-400' : ''}`} />
                          </button>
                          <button
                            onClick={() => setSelectedRecord(record)}
                            className="px-2.5 py-1 rounded-lg bg-purple-950/60 hover:bg-purple-900 border border-purple-800/80 text-purple-300 text-xs font-medium transition-all"
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Record Inspection Modal / Detail Drawer */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-purple-400">RECORD INSPECTION</span>
                <h3 className="text-2xl font-bold font-mono text-slate-100 flex items-center gap-3">
                  {selectedRecord.record_id}
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-mono ${
                      selectedRecord.purpose_mismatch
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    {selectedRecord.purpose_mismatch ? 'MISMATCH DETECTED' : 'PURPOSE COMPLIANT'}
                  </span>
                </h3>
              </div>

              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Purpose vs Usage Side-by-Side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs font-mono text-slate-400">ORIGINAL COLLECTION PURPOSE</span>
                <p className="text-sm text-slate-200 font-medium">{selectedRecord.collection_purpose}</p>
                <span className="text-[11px] text-slate-500 font-mono">Stated Consent Basis</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-xs font-mono text-slate-400">ACTIVE CURRENT USAGE</span>
                <p
                  className={`text-sm font-medium ${
                    selectedRecord.purpose_mismatch ? 'text-purple-300' : 'text-slate-200'
                  }`}
                >
                  {selectedRecord.current_usage}
                </p>
                <span className="text-[11px] text-slate-500 font-mono">Active Utilization</span>
              </div>
            </div>

            {/* AI Explanation Box */}
            <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-800/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-purple-400 font-semibold flex items-center gap-1.5">
                  <Bot className="w-4 h-4" /> AI COMPLIANCE EXPLANATION
                </span>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                  Mode: Rule-Based Engine
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                {selectedRecord.ai_explanation || 'No explanation recorded. Run analysis to evaluate.'}
              </p>
            </div>

            {/* Metadata Summary Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">CATEGORY</span>
                <span className="text-slate-200 font-semibold">{selectedRecord.category}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">SENSITIVITY</span>
                <span
                  className={`font-semibold ${
                    selectedRecord.sensitivity === 'High' ? 'text-rose-400' : 'text-slate-200'
                  }`}
                >
                  {selectedRecord.sensitivity}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">EXPIRY DATE</span>
                <span className="text-slate-200">{selectedRecord.expiry_date}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">RECOMMENDATION</span>
                <span className="text-purple-400 font-bold">
                  {selectedRecord.ai_recommendation || 'KEEP'}
                </span>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800">
              <button
                onClick={() => handleAnalyzeSingle(selectedRecord.record_id)}
                disabled={analyzingSingleId === selectedRecord.record_id}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-2"
              >
                <RefreshCw
                  className={`w-3.5 h-3.5 ${
                    analyzingSingleId === selectedRecord.record_id ? 'animate-spin' : ''
                  }`}
                />
                Re-Analyze Record
              </button>
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
