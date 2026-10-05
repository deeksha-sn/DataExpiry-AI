import React, { useEffect, useState, useMemo } from 'react';
import { apiService } from '../services/api';
import { DataRecord, AIGovernanceSummary } from '../types';
import {
  Sparkles,
  Brain,
  ShieldCheck,
  AlertTriangle,
  Trash2,
  Eye,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  BarChart3,
  Layers,
  Lock,
  Clock,
  X,
  FileText,
  ShieldAlert,
  Bot,
  Activity,
  ArrowRight
} from 'lucide-react';

export const AIInsights: React.FC = () => {
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [summary, setSummary] = useState<AIGovernanceSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzingBatch, setAnalyzingBatch] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [activeRecommendationTab, setActiveRecommendationTab] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [selectedRecord, setSelectedRecord] = useState<DataRecord | null>(null);

  // Load Data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [recordsData, summaryData] = await Promise.all([
        apiService.getDataRecords({ limit: 200 }),
        apiService.getAIGovernanceSummary().catch(() => null)
      ]);
      setRecords(recordsData);
      setSummary(summaryData);
    } catch (err: any) {
      console.error('Failed to load AI Insights data:', err);
      setError(err.message || 'Failed to load records from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Run Batch AI Analysis
  const handleRunGlobalAudit = async () => {
    setAnalyzingBatch(true);
    setError(null);
    try {
      await apiService.runBatchAiAnalysis();
      await fetchData();
    } catch (err: any) {
      console.error('Global AI Audit failed:', err);
      setError(err.message || 'Global AI Audit failed');
    } finally {
      setAnalyzingBatch(false);
    }
  };

  // Re-analyze single record
  const handleAnalyzeRecord = async (recordId: string) => {
    try {
      const res = await apiService.analyzeRecord(recordId);
      setRecords(prev =>
        prev.map(r =>
          r.record_id === recordId
            ? {
                ...r,
                purpose_mismatch: res.purpose_mismatch,
                risk_level: res.risk_level,
                ai_recommendation: res.ai_recommendation,
                ai_explanation: res.explanation
              }
            : r
        )
      );
      if (selectedRecord && selectedRecord.record_id === recordId) {
        setSelectedRecord(prev =>
          prev
            ? {
                ...prev,
                purpose_mismatch: res.purpose_mismatch,
                risk_level: res.risk_level,
                ai_recommendation: res.ai_recommendation,
                ai_explanation: res.explanation
              }
            : null
        );
      }
    } catch (err: any) {
      console.error(`Analyze failed for ${recordId}:`, err);
    }
  };

  // Exact API-derived counts
  const totalCount = records.length;
  const mismatchCount = useMemo(() => records.filter(r => r.purpose_mismatch).length, [records]);
  const highSensitivityCount = useMemo(() => records.filter(r => r.sensitivity === 'High').length, [records]);
  const reviewCount = useMemo(
    () => records.filter(r => r.ai_recommendation === 'REVIEW' || r.status === 'Expiring Soon').length,
    [records]
  );
  const keepCount = useMemo(() => records.filter(r => r.ai_recommendation === 'KEEP').length, [records]);
  const anonymizeCount = useMemo(() => records.filter(r => r.ai_recommendation === 'ANONYMIZE').length, [records]);
  const deleteCount = useMemo(() => records.filter(r => r.ai_recommendation === 'DELETE').length, [records]);

  // Risk breakdown
  const riskCounts = useMemo(() => {
    return {
      Critical: records.filter(r => r.risk_level === 'Critical').length,
      High: records.filter(r => r.risk_level === 'High').length,
      Medium: records.filter(r => r.risk_level === 'Medium').length,
      Low: records.filter(r => r.risk_level === 'Low').length
    };
  }, [records]);

  // Category breakdown
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of records) {
      counts[r.category] = (counts[r.category] || 0) + 1;
    }
    return counts;
  }, [records]);

  // Sensitivity breakdown
  const sensitivityCounts = useMemo(() => {
    return {
      High: records.filter(r => r.sensitivity === 'High').length,
      Medium: records.filter(r => r.sensitivity === 'Medium').length,
      Low: records.filter(r => r.sensitivity === 'Low').length
    };
  }, [records]);

  // Filtered Records
  const filteredRecords = useMemo(() => {
    return records.filter(r => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        r.record_id.toLowerCase().includes(q) ||
        r.data_type.toLowerCase().includes(q) ||
        r.collection_purpose.toLowerCase().includes(q) ||
        r.current_usage.toLowerCase().includes(q);

      const matchesCategory = categoryFilter === 'ALL' || r.category === categoryFilter;

      const rec = r.ai_recommendation || 'KEEP';
      const matchesTab = activeRecommendationTab === 'ALL' || rec === activeRecommendationTab;

      return matchesSearch && matchesCategory && matchesTab;
    });
  }, [records, searchQuery, categoryFilter, activeRecommendationTab]);

  return (
    <div className="space-y-6">
      {/* Page Title & Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-purple-950 text-purple-300 border border-purple-800 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            AI LIFECYCLE REASONING PLATFORM
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            AI Data Lifecycle Insights
          </h1>
          <p className="text-slate-400 mt-1 max-w-2xl">
            Automated lifecycle intelligence prescribing compliant actions (KEEP, REVIEW, ANONYMIZE, DELETE) with explainable risk reasoning.
          </p>
        </div>

        <button
          onClick={handleRunGlobalAudit}
          disabled={analyzingBatch || loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-purple-900/30 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${analyzingBatch ? 'animate-spin' : ''}`} />
          <span>{analyzingBatch ? 'Running Global AI Audit...' : 'Run Global AI Audit'}</span>
        </button>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="text-sm font-mono">{error}</span>
          </div>
          <button onClick={fetchData} className="text-xs underline hover:text-rose-200">
            Retry
          </button>
        </div>
      )}

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-slate-400">TOTAL ENTERPRISE ASSETS</span>
          <div className="text-2xl font-bold text-slate-100">{loading ? '...' : totalCount}</div>
          <p className="text-[11px] text-slate-500 font-mono">Catalog records under AI surveillance</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-purple-400">POTENTIAL MISMATCHES</span>
          <div className="text-2xl font-bold text-purple-400">{loading ? '...' : mismatchCount}</div>
          <p className="text-[11px] text-slate-500 font-mono">
            {totalCount ? Math.round((mismatchCount / totalCount) * 100) : 0}% of inventory flagged
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-rose-400">HIGH-SENSITIVITY ASSETS</span>
          <div className="text-2xl font-bold text-rose-400">{loading ? '...' : highSensitivityCount}</div>
          <p className="text-[11px] text-slate-500 font-mono">PII / Financial tier classifications</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-amber-400">RECORDS IN REVIEW</span>
          <div className="text-2xl font-bold text-amber-400">{loading ? '...' : reviewCount}</div>
          <p className="text-[11px] text-slate-500 font-mono">Pending compliance signoff</p>
        </div>
      </div>

      {/* 4 Primary AI Recommendation Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KEEP */}
        <div
          onClick={() => setActiveRecommendationTab(activeRecommendationTab === 'KEEP' ? 'ALL' : 'KEEP')}
          className={`p-5 rounded-xl border transition-all cursor-pointer group ${
            activeRecommendationTab === 'KEEP'
              ? 'bg-emerald-950/40 border-emerald-500 ring-2 ring-emerald-500/20 shadow-lg shadow-emerald-950/50'
              : 'bg-slate-950 border-slate-800 hover:border-emerald-500/50'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-bold text-emerald-400">ACTION: KEEP</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-300 font-mono">
            {loading ? '...' : keepCount}
          </div>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            Active retention schedule and compliant collection purpose. No action needed.
          </p>
          <div className="mt-3 text-[11px] font-mono text-emerald-400 flex items-center gap-1 group-hover:underline">
            <span>Filter KEEP records</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>

        {/* REVIEW */}
        <div
          onClick={() => setActiveRecommendationTab(activeRecommendationTab === 'REVIEW' ? 'ALL' : 'REVIEW')}
          className={`p-5 rounded-xl border transition-all cursor-pointer group ${
            activeRecommendationTab === 'REVIEW'
              ? 'bg-amber-950/40 border-amber-500 ring-2 ring-amber-500/20 shadow-lg shadow-amber-950/50'
              : 'bg-slate-950 border-slate-800 hover:border-amber-500/50'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-bold text-amber-400">ACTION: REVIEW</span>
            <Clock className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-amber-300 font-mono">
            {loading ? '...' : reviewCount}
          </div>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            Approaching expiration deadline or detected active usage drift requiring consent renewal.
          </p>
          <div className="mt-3 text-[11px] font-mono text-amber-400 flex items-center gap-1 group-hover:underline">
            <span>Filter REVIEW records</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>

        {/* ANONYMIZE */}
        <div
          onClick={() => setActiveRecommendationTab(activeRecommendationTab === 'ANONYMIZE' ? 'ALL' : 'ANONYMIZE')}
          className={`p-5 rounded-xl border transition-all cursor-pointer group ${
            activeRecommendationTab === 'ANONYMIZE'
              ? 'bg-sky-950/40 border-sky-500 ring-2 ring-sky-500/20 shadow-lg shadow-sky-950/50'
              : 'bg-slate-950 border-slate-800 hover:border-sky-500/50'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-bold text-sky-400">ACTION: ANONYMIZE</span>
            <Lock className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-sky-300 font-mono">
            {loading ? '...' : anonymizeCount}
          </div>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            Expired high-sensitivity data. Scrub personal identifiers while retaining aggregate utility.
          </p>
          <div className="mt-3 text-[11px] font-mono text-sky-400 flex items-center gap-1 group-hover:underline">
            <span>Filter ANONYMIZE records</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>

        {/* DELETE */}
        <div
          onClick={() => setActiveRecommendationTab(activeRecommendationTab === 'DELETE' ? 'ALL' : 'DELETE')}
          className={`p-5 rounded-xl border transition-all cursor-pointer group ${
            activeRecommendationTab === 'DELETE'
              ? 'bg-rose-950/40 border-rose-500 ring-2 ring-rose-500/20 shadow-lg shadow-rose-950/50'
              : 'bg-slate-950 border-slate-800 hover:border-rose-500/50'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-bold text-rose-400">ACTION: DELETE</span>
            <Trash2 className="w-5 h-5 text-rose-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-rose-300 font-mono">
            {loading ? '...' : deleteCount}
          </div>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            Retention period lapsed and unlawful purpose mismatch. Mandatory data purge required.
          </p>
          <div className="mt-3 text-[11px] font-mono text-rose-400 flex items-center gap-1 group-hover:underline">
            <span>Filter DELETE records</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>
      </div>

      {/* Visual Analytics Strip: Category & Sensitivity & Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Matrix */}
        <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-purple-400" />
              Risk Level Distribution
            </h3>
            <span className="text-xs font-mono text-slate-500">API Derived</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {/* Critical */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-rose-400 font-bold">Critical Risk</span>
                <span className="text-slate-300 font-semibold">{riskCounts.Critical}</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-rose-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${totalCount ? (riskCounts.Critical / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* High */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-amber-400 font-bold">High Risk</span>
                <span className="text-slate-300 font-semibold">{riskCounts.High}</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${totalCount ? (riskCounts.High / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Medium */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sky-400 font-bold">Medium Risk</span>
                <span className="text-slate-300 font-semibold">{riskCounts.Medium}</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-sky-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${totalCount ? (riskCounts.Medium / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Low */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-emerald-400 font-bold">Low Risk</span>
                <span className="text-slate-300 font-semibold">{riskCounts.Low}</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${totalCount ? (riskCounts.Low / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Category Breakdown Chart */}
        <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-sky-400" />
              Category Inventory
            </h3>
            <span className="text-xs font-mono text-slate-500">Asset Types</span>
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            {Object.entries(categoryCounts).map(([cat, count]) => {
              const pct = totalCount ? Math.round((count / totalCount) * 100) : 0;
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex justify-between text-slate-300">
                    <span>{cat}</span>
                    <span className="text-slate-400">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-sky-500 to-indigo-500 h-1.5 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Sensitivity & Purpose Compliance Ring */}
        <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Governance Health Ratio
            </h3>
            <span className="text-xs font-mono text-slate-500">GDPR Compliance</span>
          </div>

          <div className="flex items-center justify-center py-2">
            <div className="relative flex items-center justify-center">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="48"
                  className="stroke-slate-800"
                  strokeWidth="10"
                  fill="transparent"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="48"
                  className="stroke-emerald-400 transition-all duration-1000 ease-out"
                  strokeWidth="10"
                  strokeDasharray={2 * Math.PI * 48}
                  strokeDashoffset={
                    2 * Math.PI * 48 * (1 - (totalCount ? (totalCount - mismatchCount) / totalCount : 1))
                  }
                  strokeLinecap="round"
                  fill="transparent"
                />
              </svg>
              <div className="absolute text-center">
                <div className="text-2xl font-bold font-mono text-slate-100">
                  {totalCount ? Math.round(((totalCount - mismatchCount) / totalCount) * 100) : 100}%
                </div>
                <div className="text-[10px] font-mono text-slate-400 uppercase">Compliant</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono pt-2 border-t border-slate-900">
            <div className="p-2 rounded bg-slate-900/60">
              <span className="text-slate-500 block text-[10px]">COMPLIANT USAGE</span>
              <span className="text-emerald-400 font-bold">{totalCount - mismatchCount} Records</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60">
              <span className="text-slate-500 block text-[10px]">PURPOSE CREEP</span>
              <span className="text-rose-400 font-bold">{mismatchCount} Records</span>
            </div>
          </div>
        </div>
      </div>

      {/* Record-Level AI Insights Explorer */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Bot className="w-5 h-5 text-purple-400" />
              Prescriptive Record Recommendations
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
              {filteredRecords.length} records matching
            </span>
          </div>

          {/* Action Tabs */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono">
            {['ALL', 'KEEP', 'REVIEW', 'ANONYMIZE', 'DELETE'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveRecommendationTab(tab)}
                className={`px-3 py-1 rounded transition-all ${
                  activeRecommendationTab === tab
                    ? 'bg-purple-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="relative flex-1 min-w-[240px]">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search records by ID, purpose, usage, or explanation..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
            >
              <option value="ALL">All Categories</option>
              {Object.keys(categoryCounts).map(cat => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Records Card Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading ? (
            <div className="col-span-2 p-12 text-center text-slate-400 font-mono">
              Loading AI records...
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="col-span-2 p-12 text-center text-slate-500 font-mono border border-slate-800 rounded-xl bg-slate-950">
              No records found for the selected recommendation or search filter.
            </div>
          ) : (
            filteredRecords.map(record => {
              const rec = record.ai_recommendation || 'KEEP';
              const isMismatch = record.purpose_mismatch;

              return (
                <div
                  key={record.id}
                  className="p-5 rounded-xl bg-slate-950 border border-slate-800 hover:border-purple-500/40 transition-all space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Header Row */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono font-bold text-slate-200 text-sm">{record.record_id}</span>
                        <span className="text-xs text-slate-400">({record.category})</span>
                      </div>

                      {/* Recommendation Badge */}
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                          rec === 'DELETE'
                            ? 'bg-rose-950 text-rose-300 border-rose-800'
                            : rec === 'ANONYMIZE'
                            ? 'bg-sky-950 text-sky-300 border-sky-800'
                            : rec === 'REVIEW'
                            ? 'bg-amber-950 text-amber-300 border-amber-800'
                            : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                        }`}
                      >
                        {rec}
                      </span>
                    </div>

                    {/* Purpose vs Usage Snippet */}
                    <div className="space-y-1.5 text-xs font-mono bg-slate-900/60 p-3 rounded-lg border border-slate-800/80">
                      <div>
                        <span className="text-slate-500 block text-[10px]">COLLECTION PURPOSE:</span>
                        <span className="text-slate-300">{record.collection_purpose}</span>
                      </div>
                      <div className="pt-1 border-t border-slate-800">
                        <span className="text-slate-500 block text-[10px]">CURRENT USAGE:</span>
                        <span className={isMismatch ? 'text-purple-300 font-semibold' : 'text-slate-300'}>
                          {record.current_usage}
                        </span>
                      </div>
                    </div>

                    {/* AI Explanation Text */}
                    <div className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-3">
                      <span className="text-purple-400 font-mono font-semibold">AI Rationale: </span>
                      {record.ai_explanation || 'Awaiting deep AI evaluation. Click Analyze to process.'}
                    </div>
                  </div>

                  {/* Footer Meta & Inspect */}
                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500">RISK:</span>
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

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleAnalyzeRecord(record.record_id)}
                        className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800"
                        title="Re-run AI evaluation"
                      >
                        Re-evaluate
                      </button>
                      <button
                        onClick={() => setSelectedRecord(record)}
                        className="px-3 py-1 rounded bg-purple-950/80 hover:bg-purple-900 text-purple-300 border border-purple-800"
                      >
                        Details
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Record Details Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-purple-400">AI LIFECYCLE AUDIT REPORT</span>
                <h3 className="text-2xl font-bold font-mono text-slate-100 flex items-center gap-3">
                  {selectedRecord.record_id}
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-bold ${
                      selectedRecord.ai_recommendation === 'DELETE'
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : selectedRecord.ai_recommendation === 'ANONYMIZE'
                        ? 'bg-sky-950 text-sky-300 border border-sky-800'
                        : selectedRecord.ai_recommendation === 'REVIEW'
                        ? 'bg-amber-950 text-amber-300 border border-amber-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    ACTION: {selectedRecord.ai_recommendation || 'KEEP'}
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

            {/* AI Explanation Deep Dive */}
            <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-800/50 space-y-2">
              <span className="text-xs font-mono text-purple-400 font-semibold flex items-center gap-1.5">
                <Brain className="w-4 h-4" /> REASONING & COMPLIANCE JUSTIFICATION
              </span>
              <p className="text-xs text-slate-200 leading-relaxed font-mono">
                {selectedRecord.ai_explanation || 'No detailed explanation recorded.'}
              </p>
            </div>

            {/* Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-500">COLLECTION PURPOSE</span>
                <p className="text-slate-200 font-sans text-sm">{selectedRecord.collection_purpose}</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-slate-500">CURRENT USAGE</span>
                <p
                  className={`font-sans text-sm ${
                    selectedRecord.purpose_mismatch ? 'text-purple-300 font-semibold' : 'text-slate-200'
                  }`}
                >
                  {selectedRecord.current_usage}
                </p>
              </div>
            </div>

            {/* Lifecycle Details */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">STATUS</span>
                <span
                  className={
                    selectedRecord.status === 'Expired'
                      ? 'text-rose-400 font-bold'
                      : selectedRecord.status === 'Expiring Soon'
                      ? 'text-amber-400 font-bold'
                      : 'text-emerald-400 font-bold'
                  }
                >
                  {selectedRecord.status}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">SENSITIVITY</span>
                <span className="text-slate-200">{selectedRecord.sensitivity}</span>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">EXPIRY DATE</span>
                <span className="text-slate-200">{selectedRecord.expiry_date}</span>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block">RISK LEVEL</span>
                <span
                  className={`font-bold ${
                    selectedRecord.risk_level === 'Critical'
                      ? 'text-rose-400'
                      : selectedRecord.risk_level === 'High'
                      ? 'text-amber-400'
                      : 'text-sky-400'
                  }`}
                >
                  {selectedRecord.risk_level || 'Low'}
                </span>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
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
