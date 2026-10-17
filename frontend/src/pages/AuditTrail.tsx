import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  Shield,
  Search,
  Filter,
  RefreshCw,
  Download,
  AlertCircle,
  Lock,
  X,
  FileText,
  Clock,
  User,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { apiService } from '../services/api';
import { AuditLog, AuditFilterParams } from '../types';

const AUDIT_ACTIONS = ['ALL', 'KEEP', 'REVIEW', 'ANONYMIZE', 'DELETE'] as const;
const DEV_ROLES = ['AUDITOR', 'DATA_GOVERNANCE', 'ADMIN', 'PRIVACY_OFFICER', 'VIEWER'] as const;

export const AuditTrail: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [is403Error, setIs403Error] = useState<boolean>(false);

  // Filters state
  const [recordIdFilter, setRecordIdFilter] = useState<string>('');
  const [actionFilter, setActionFilter] = useState<string>('ALL');
  const [userFilter, setUserFilter] = useState<string>('');
  const [limit, setLimit] = useState<number>(50);
  const [offset, setOffset] = useState<number>(0);

  // Details Modal
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  // Single Record History Search
  const [searchRecordId, setSearchRecordId] = useState<string>('');
  const [recordHistoryMode, setRecordHistoryMode] = useState<boolean>(false);

  // Role simulation & Dev Headers
  const [currentRole, setCurrentRole] = useState<string>(() => apiService.getDevRole());
  const [authHeaderEnabled, setAuthHeaderEnabled] = useState<boolean>(() =>
    apiService.isDevAuthHeaderEnabled()
  );

  // Fetch Audit Logs
  const fetchAuditLogs = async (customOffset?: number) => {
    setLoading(true);
    setError(null);
    setIs403Error(false);

    const targetOffset = customOffset !== undefined ? customOffset : offset;

    try {
      if (recordHistoryMode && searchRecordId.trim()) {
        const data = await apiService.getRecordAuditLogs(searchRecordId.trim());
        setLogs(data);
      } else {
        const params: AuditFilterParams = {
          limit,
          offset: targetOffset,
        };
        if (recordIdFilter.trim()) params.record_id = recordIdFilter.trim();
        if (actionFilter !== 'ALL') params.action = actionFilter;
        if (userFilter.trim()) params.user = userFilter.trim();

        const data = await apiService.getAuditLogs(params);
        setLogs(data);
      }
    } catch (err: any) {
      console.error('Failed to load audit logs:', err);
      const msg = err.message || 'Unable to retrieve audit logs.';
      setError(msg);
      if (msg.includes('403') || msg.toLowerCase().includes('not authorized') || msg.toLowerCase().includes('disabled outside development')) {
        setIs403Error(true);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [actionFilter, limit, offset, recordHistoryMode]);

  // Handle Role Change
  const handleRoleChange = (role: string) => {
    setCurrentRole(role);
    apiService.setDevRole(role);
  };

  const handleAuthHeaderToggle = (enabled: boolean) => {
    setAuthHeaderEnabled(enabled);
    apiService.setDevAuthHeaderEnabled(enabled);
  };

  // Search filter submit
  const handleApplyFilter = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    setRecordHistoryMode(false);
    fetchAuditLogs(0);
  };

  // Single record history search submit
  const handleRecordHistorySearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchRecordId.trim()) {
      setRecordHistoryMode(false);
      fetchAuditLogs(0);
      return;
    }
    setRecordHistoryMode(true);
    setOffset(0);
    fetchAuditLogs(0);
  };

  // Reset filters
  const handleResetFilters = () => {
    setRecordIdFilter('');
    setActionFilter('ALL');
    setUserFilter('');
    setSearchRecordId('');
    setRecordHistoryMode(false);
    setOffset(0);
  };

  // Export to CSV
  const handleExportCSV = () => {
    if (logs.length === 0) return;

    const headers = [
      'Audit ID',
      'Timestamp',
      'Record ID',
      'Action',
      'Previous Status',
      'New Status',
      'User',
      'Reason',
      'AI Recommendation',
      'Policy Rule',
    ];

    const rows = logs.map((log) => [
      log.audit_id,
      log.timestamp,
      `"${log.record_id}"`,
      `"${log.action}"`,
      `"${log.previous_status || ''}"`,
      `"${log.new_status || ''}"`,
      `"${log.user}"`,
      `"${(log.reason || '').replace(/"/g, '""')}"`,
      `"${log.ai_recommendation || ''}"`,
      `"${log.policy_rule || ''}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `dataexpiry-audit-trail-${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Badges
  const actionBadge = (action: string) => {
    switch (action.toUpperCase()) {
      case 'KEEP':
        return 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-400';
      case 'REVIEW':
        return 'border border-amber-500/30 bg-amber-500/10 text-amber-400';
      case 'ANONYMIZE':
        return 'border border-purple-500/30 bg-purple-500/10 text-purple-400';
      case 'DELETE':
        return 'border border-rose-500/30 bg-rose-500/10 text-rose-400';
      default:
        return 'border border-slate-700 bg-slate-800 text-slate-300';
    }
  };

  const statusBadge = (status?: string | null) => {
    if (!status) return 'text-slate-500';
    switch (status.toLowerCase()) {
      case 'active':
        return 'text-emerald-400 font-medium';
      case 'archived':
      case 'anonymized':
        return 'text-purple-400 font-medium';
      case 'deleted':
        return 'text-rose-400 font-medium';
      case 'in review':
      case 'expiring soon':
        return 'text-amber-400 font-medium';
      default:
        return 'text-slate-300';
    }
  };

  // Metrics
  const stats = useMemo(() => {
    return {
      total: logs.length,
      deletions: logs.filter((l) => l.action.toUpperCase() === 'DELETE').length,
      anonymizations: logs.filter((l) => l.action.toUpperCase() === 'ANONYMIZE').length,
      reviews: logs.filter((l) => l.action.toUpperCase() === 'REVIEW').length,
      keeps: logs.filter((l) => l.action.toUpperCase() === 'KEEP').length,
    };
  }, [logs]);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[.18em] text-amber-400">
            Governance · Audit
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">
            Compliance Audit Trail
          </h1>
          <p className="text-slate-400 mt-1">
            Immutable log of enterprise lifecycle actions, policy executions, and disposal events.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleExportCSV}
            disabled={logs.length === 0}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-700 disabled:opacity-50"
            title="Download CSV report of currently displayed audit events"
          >
            <Download className="h-4 w-4 text-sky-400" />
            <span>Export CSV</span>
          </button>

          <button
            type="button"
            onClick={() => fetchAuditLogs()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Logs</span>
          </button>
        </div>
      </div>

      {/* Role & Auth Simulator Notice */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-950/80 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <Lock className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong className="text-slate-200">RBAC Identity Header:</strong> Audit access requires{' '}
            <code className="text-sky-300">AUDITOR</code>, <code className="text-sky-300">DATA_GOVERNANCE</code>,{' '}
            <code className="text-sky-300">ADMIN</code>, or <code className="text-sky-300">PRIVACY_OFFICER</code>.
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={authHeaderEnabled}
              onChange={(e) => handleAuthHeaderToggle(e.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-sky-500 focus:ring-sky-400"
            />
            <span className="text-slate-300">Send Dev Header</span>
          </label>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Acting Role:</span>
            <select
              value={currentRole}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-slate-200 focus:border-sky-500 focus:outline-none"
            >
              {DEV_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Access Denied (403) or Error Banner */}
      {is403Error ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-900/80 bg-rose-950/30 p-6 text-sm text-rose-200 space-y-3"
        >
          <div className="flex items-center gap-3 text-rose-400 font-semibold text-base">
            <AlertCircle className="w-6 h-6 shrink-0" />
            <span>Authorization Required (HTTP 403 Forbidden)</span>
          </div>
          <p className="text-rose-300/90 leading-relaxed">
            The Audit Trail endpoint is strictly restricted by role-based access control (RBAC). Your current identity does not possess the required permissions.
          </p>
          <div className="rounded-lg bg-rose-950/60 p-3.5 border border-rose-900/40 text-xs font-mono space-y-1">
            <div><strong>Permitted Roles:</strong> AUDITOR, DATA_GOVERNANCE, ADMIN, PRIVACY_OFFICER</div>
            <div><strong>Acting Role:</strong> {currentRole} (Dev Header: {authHeaderEnabled ? 'Enabled' : 'Disabled'})</div>
            <div><strong>Backend Error:</strong> {error}</div>
          </div>
          <p className="text-xs text-rose-300/70">
            💡 In local development, ensure the backend server was started with{' '}
            <code className="bg-rose-900/40 px-1 py-0.5 rounded text-rose-200 font-mono">ALLOW_DEV_HEADER_AUTH=True</code>,{' '}
            and select an authorized role like <strong className="text-white">AUDITOR</strong> or <strong className="text-white">DATA_GOVERNANCE</strong> above.
          </p>
          <button
            type="button"
            onClick={() => fetchAuditLogs()}
            className="mt-2 inline-flex items-center gap-2 rounded-lg bg-rose-900/60 hover:bg-rose-900 px-3.5 py-1.5 text-xs font-semibold text-rose-100 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Access Check</span>
          </button>
        </div>
      ) : error ? (
        <div
          role="alert"
          className="flex items-center justify-between rounded-lg border border-rose-900/60 bg-rose-950/40 p-4 text-sm text-rose-300"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-rose-400 hover:text-rose-200"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : null}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-slate-400">Total Events</div>
          <div className="mt-1 text-2xl font-bold text-slate-100">{stats.total}</div>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-rose-400">Deletions</div>
          <div className="mt-1 text-2xl font-bold text-rose-400">{stats.deletions}</div>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-purple-400">Anonymizations</div>
          <div className="mt-1 text-2xl font-bold text-purple-400">{stats.anonymizations}</div>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-amber-400">Reviews</div>
          <div className="mt-1 text-2xl font-bold text-amber-400">{stats.reviews}</div>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950">
          <div className="text-xs uppercase tracking-wider text-emerald-400">Kept Active</div>
          <div className="mt-1 text-2xl font-bold text-emerald-400">{stats.keeps}</div>
        </div>
      </div>

      {/* Filters & History Search Section */}
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Main Filter Form */}
          <form onSubmit={handleApplyFilter} className="flex flex-wrap items-center gap-3 text-sm flex-1">
            <div className="relative min-w-[180px] flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Filter by Record ID..."
                value={recordIdFilter}
                onChange={(e) => setRecordIdFilter(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-sm text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div className="relative min-w-[140px]">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Filter by User..."
                value={userFilter}
                onChange={(e) => setUserFilter(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-sm text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-500" />
              <select
                value={actionFilter}
                onChange={(e) => {
                  setActionFilter(e.target.value);
                  setOffset(0);
                }}
                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-slate-300 focus:border-sky-500 focus:outline-none"
              >
                {AUDIT_ACTIONS.map((a) => (
                  <option key={a} value={a}>
                    {a === 'ALL' ? 'All Actions' : a}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-sky-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-50"
            >
              Filter
            </button>

            {(recordIdFilter || actionFilter !== 'ALL' || userFilter || recordHistoryMode) && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700"
              >
                Clear
              </button>
            )}
          </form>

          {/* Single Record Dedicated History Lookup */}
          <form
            onSubmit={handleRecordHistorySearch}
            className="flex items-center gap-2 text-sm border-t lg:border-t-0 lg:border-l border-slate-800 pt-3 lg:pt-0 lg:pl-4"
          >
            <span className="text-xs text-slate-400 whitespace-nowrap">Record History:</span>
            <input
              type="text"
              placeholder="e.g. CUS-1001"
              value={searchRecordId}
              onChange={(e) => setSearchRecordId(e.target.value)}
              className="w-36 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 font-mono focus:border-sky-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg border border-sky-600/50 bg-sky-950/40 px-3 py-1.5 text-xs font-medium text-sky-300 hover:bg-sky-900/50 disabled:opacity-50"
            >
              Trace
            </button>
          </form>
        </div>

        {recordHistoryMode && (
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-sky-950/30 border border-sky-900/50 text-xs text-sky-300">
            <span>
              Showing chronological audit history for record <strong className="font-mono">{searchRecordId}</strong> via{' '}
              <code className="text-slate-200">GET /api/audit/{searchRecordId}</code>
            </span>
            <button
              type="button"
              onClick={handleResetFilters}
              className="text-sky-400 hover:underline"
            >
              Show All Audit Logs
            </button>
          </div>
        )}
      </div>

      {/* Main Audit Records Table */}
      <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
        {loading ? (
          <div className="p-16 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-sky-400" />
            <p className="font-medium text-slate-200">Loading audit trail records...</p>
            <p className="text-xs text-slate-500 mt-1">Fetching immutable event logs from backend</p>
          </div>
        ) : is403Error ? (
          <div className="p-14 text-center text-slate-400">
            <Lock className="w-10 h-10 mx-auto mb-3 text-amber-500/60" />
            <h3 className="text-base font-semibold text-slate-200">Access Restricted</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
              Please authenticate as an AUDITOR, DATA_GOVERNANCE, ADMIN, or PRIVACY_OFFICER to view audit entries.
            </p>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-16 text-center">
            <ShieldCheck className="w-12 h-12 mx-auto mb-4 text-slate-600" />
            <h3 className="text-lg font-semibold text-slate-200">No Audit Events Found</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto mt-1 leading-relaxed">
              {recordHistoryMode
                ? `No audit events found for record '${searchRecordId}'.`
                : 'There are currently no lifecycle audit events recorded in the system. Audit entries are generated when retention actions (KEEP, REVIEW, ANONYMIZE, DELETE) are executed.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[950px] text-left text-sm">
              <thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Event ID & Time</th>
                  <th className="px-4 py-3 font-medium">Record ID</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Status Transition</th>
                  <th className="px-4 py-3 font-medium">Actor</th>
                  <th className="px-4 py-3 font-medium">Reason & Policy</th>
                  <th className="px-4 py-3 text-right font-medium">Inspection</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {logs.map((log) => (
                  <tr key={log.audit_id} className="hover:bg-slate-900/60 transition-colors">
                    {/* Timestamp & ID */}
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="flex items-center gap-1.5 font-mono text-xs text-sky-400">
                        <span>#{log.audit_id}</span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </td>

                    {/* Record ID */}
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <Link
                        to={`/records?id=${encodeURIComponent(log.record_id)}`}
                        className="font-mono text-xs font-semibold text-sky-400 hover:underline"
                        title="View data record details"
                      >
                        {log.record_id}
                      </Link>
                    </td>

                    {/* Action */}
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${actionBadge(log.action)}`}>
                        {log.action}
                      </span>
                    </td>

                    {/* Status Transition */}
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs">
                      <div className="flex items-center gap-1.5">
                        <span className={statusBadge(log.previous_status)}>
                          {log.previous_status || 'None'}
                        </span>
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                        <span className={statusBadge(log.new_status)}>
                          {log.new_status || 'Unchanged'}
                        </span>
                      </div>
                    </td>

                    {/* Actor */}
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-300">
                      <div className="flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        <span className="font-mono">{log.user}</span>
                      </div>
                    </td>

                    {/* Reason & Policy */}
                    <td className="px-4 py-3.5 max-w-xs text-xs">
                      <div className="text-slate-300 truncate" title={log.reason || 'No narrative'}>
                        {log.reason || <span className="text-slate-500 italic">No narrative</span>}
                      </div>
                      {log.policy_rule && (
                        <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                          Policy: {log.policy_rule}
                        </div>
                      )}
                    </td>

                    {/* Inspect button */}
                    <td className="px-4 py-3.5 whitespace-nowrap text-right">
                      <button
                        type="button"
                        onClick={() => setSelectedLog(log)}
                        className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-200 hover:border-sky-600 hover:text-sky-300 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {!recordHistoryMode && logs.length > 0 && (
          <div className="flex items-center justify-between border-t border-slate-800 bg-slate-900/60 px-4 py-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span>Page Size:</span>
              <select
                value={limit}
                onChange={(e) => {
                  setLimit(Number(e.target.value));
                  setOffset(0);
                }}
                className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-slate-200 focus:outline-none"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <span className="ml-2">
                Showing {offset + 1} – {offset + logs.length}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={offset === 0 || loading}
                onClick={() => setOffset(Math.max(0, offset - limit))}
                className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-slate-300 hover:bg-slate-700 disabled:opacity-40"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
              <button
                type="button"
                disabled={logs.length < limit || loading}
                onClick={() => setOffset(offset + limit)}
                className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800 px-2.5 py-1 text-slate-300 hover:bg-slate-700 disabled:opacity-40"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </section>

      {/* INSPECT LOG DETAILS MODAL */}
      {selectedLog && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-5 animate-in fade-in duration-200">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <History className="w-5 h-5 text-sky-400" />
                <div>
                  <h3 className="text-lg font-bold text-slate-100">
                    Audit Entry #{selectedLog.audit_id}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Immutable Record of Lifecycle Event Execution
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content Details */}
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl border border-slate-800 bg-slate-950">
                <div>
                  <span className="text-slate-500 block">Record Identifier</span>
                  <Link
                    to={`/records?id=${encodeURIComponent(selectedLog.record_id)}`}
                    className="font-mono text-sm font-bold text-sky-400 hover:underline inline-flex items-center gap-1 mt-0.5"
                  >
                    <span>{selectedLog.record_id}</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>

                <div>
                  <span className="text-slate-500 block">Lifecycle Action</span>
                  <span className={`inline-flex rounded-full px-2.5 py-0.5 font-semibold mt-0.5 ${actionBadge(selectedLog.action)}`}>
                    {selectedLog.action}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block">Event Timestamp</span>
                  <span className="text-slate-200 font-medium">
                    {new Date(selectedLog.timestamp).toUTCString()}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block">Persisted At</span>
                  <span className="text-slate-200 font-medium">
                    {new Date(selectedLog.created_at).toUTCString()}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block">Actor / User</span>
                  <span className="text-slate-200 font-mono font-medium">
                    {selectedLog.user}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block">Governing Policy</span>
                  <span className="text-slate-200 font-mono font-medium">
                    {selectedLog.policy_rule || 'None'}
                  </span>
                </div>
              </div>

              {/* Status Transition Card */}
              <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 space-y-1">
                <span className="text-slate-500 block">Status Transition</span>
                <div className="flex items-center gap-2 text-sm pt-1">
                  <span className={`px-2 py-0.5 rounded bg-slate-900 border border-slate-800 ${statusBadge(selectedLog.previous_status)}`}>
                    {selectedLog.previous_status || 'Initial'}
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                  <span className={`px-2 py-0.5 rounded bg-slate-900 border border-slate-800 ${statusBadge(selectedLog.new_status)}`}>
                    {selectedLog.new_status || 'Current'}
                  </span>
                </div>
              </div>

              {/* Reason / Narrative */}
              <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 space-y-1">
                <span className="text-slate-500 block">Action Narrative & Justification</span>
                <p className="text-slate-200 leading-relaxed text-xs">
                  {selectedLog.reason || 'No written narrative was recorded for this lifecycle action.'}
                </p>
              </div>

              {/* AI Recommendation State */}
              <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950 space-y-1">
                <span className="text-slate-500 block">AI Recommendation State at Execution</span>
                <p className="text-slate-200 font-medium">
                  {selectedLog.ai_recommendation ? (
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ${actionBadge(selectedLog.ai_recommendation)}`}>
                      {selectedLog.ai_recommendation}
                    </span>
                  ) : (
                    <span className="text-slate-500 italic">No AI recommendation recorded</span>
                  )}
                </p>
              </div>

              {/* Raw JSON Record */}
              <div className="p-3 rounded-lg border border-slate-800 bg-slate-950 font-mono text-[11px] text-slate-400 overflow-x-auto">
                <span className="text-slate-500 block mb-1">Raw Immutable Audit Record</span>
                <pre>{JSON.stringify(selectedLog, null, 2)}</pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setSelectedLog(null)}
                className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
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

export default AuditTrail;
