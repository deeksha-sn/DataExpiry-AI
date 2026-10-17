import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { DataRecord, LifecycleActionResponse } from '../types';
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Trash2,
  FileText,
  Eye,
  ExternalLink,
  X,
  Shield,
  LucideIcon,
} from 'lucide-react';

export const ExpiryManagement: React.FC = () => {
  const [records, setRecords] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // Action states
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<LifecycleActionResponse | null>(null);

  // Confirmation modal state
  const [pendingActionRecord, setPendingActionRecord] = useState<DataRecord | null>(null);
  const [pendingActionType, setPendingActionType] = useState<
    'REVIEW' | 'ANONYMIZE' | 'DELETE' | null
  >(null);
  const [actionReason, setActionReason] = useState<string>('');

  const load = () => {
    setLoading(true);
    setError('');
    apiService
      .getDataRecords({ limit: 500 })
      .then(setRecords)
      .catch((e) => setError(e.message || 'Unable to load records.'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  // Initiate action with confirmation
  const initiateAction = (
    record: DataRecord,
    action: 'REVIEW' | 'ANONYMIZE' | 'DELETE'
  ) => {
    setActionError(null);
    setPendingActionRecord(record);
    setPendingActionType(action);
    setActionReason('');
  };

  // Execute lifecycle action on single record
  const executeConfirmedAction = async () => {
    if (!pendingActionRecord || !pendingActionType) return;

    const recordId = pendingActionRecord.record_id;
    const action = pendingActionType;

    setActionLoadingId(recordId);
    setActionError(null);
    setActionSuccess(null);

    try {
      const response = await apiService.executeLifecycleAction(
        recordId,
        action,
        actionReason.trim() || null
      );
      setActionSuccess(response);
      setPendingActionRecord(null);
      setPendingActionType(null);
      setActionReason('');

      // Refresh records from backend
      await apiService.getDataRecords({ limit: 500 }).then(setRecords);
    } catch (err: any) {
      console.error('Lifecycle action failed:', err);
      setActionError(err.message || `Failed to execute action ${action} on ${recordId}.`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const isCompleted = (r: DataRecord) => {
    return (
      ['Complete', 'Completed', 'Approved'].includes(r.review_status || '') ||
      ['Complete', 'Completed', 'Deleted'].includes(r.deletion_status || '') ||
      ['Complete', 'Completed', 'Anonymized'].includes(r.anonymization_status || '')
    );
  };

  type LaneAction = 'REVIEW' | 'ANONYMIZE' | 'DELETE';
  type LaneTitle = 'Expiring soon' | 'Expired' | 'Review required' | 'Completed';

  /**
   * Deterministic, mutually exclusive lifecycle lane classification.
   * Priority order:
   * 1. Completed: Highest priority. Any approved, completed, anonymized, or deleted record.
   * 2. Expired: Records past retention expiry date (status === 'Expired').
   * 3. Expiring soon: Records approaching retention deadline (status === 'Expiring Soon').
   * 4. Review required: Remaining records needing governance review (e.g. Active with review_status 'In Review' or AI recommendation 'REVIEW').
   *
   * Ensures every record belongs to at most one lane. Non-matching records return null (0 lanes).
   */
  const getRecordLane = (r: DataRecord): LaneTitle | null => {
    // 1. Completed (Highest Priority)
    if (isCompleted(r)) {
      return 'Completed';
    }

    // 2. Expired (Overdue retention)
    if (r.status === 'Expired') {
      return 'Expired';
    }

    // 3. Expiring soon (Approaching deadline)
    if (r.status === 'Expiring Soon') {
      return 'Expiring soon';
    }

    // 4. Review required (Pending/In-review or AI flagged review on remaining records)
    const rev = r.review_status || '';
    if (
      r.ai_recommendation === 'REVIEW' ||
      rev === 'In Review' ||
      Boolean(rev && !['Complete', 'Completed', 'Approved', 'Pending', 'Not Required'].includes(rev))
    ) {
      return 'Review required';
    }

    return null;
  };

  interface LaneConfig {
    title: LaneTitle;
    description: string;
    icon: LucideIcon;
    tone: string;
    allowedActions: LaneAction[];
  }

  const lanes: LaneConfig[] = [
    {
      title: 'Expiring soon',
      description: 'Retention deadline approaching',
      icon: Clock,
      tone: 'text-amber-400',
      allowedActions: ['REVIEW'],
    },
    {
      title: 'Expired',
      description: 'Past the recorded expiry date',
      icon: AlertTriangle,
      tone: 'text-rose-400',
      allowedActions: ['REVIEW', 'ANONYMIZE', 'DELETE'],
    },
    {
      title: 'Review required',
      description: 'Review recommendation or pending review',
      icon: AlertTriangle,
      tone: 'text-sky-400',
      allowedActions: ['REVIEW'],
    },
    {
      title: 'Completed',
      description: 'Marked complete, approved, anonymized, or deleted by governance workflow',
      icon: CheckCircle2,
      tone: 'text-emerald-400',
      allowedActions: [],
    },
  ];


  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[.18em] text-sky-400">
            Lifecycle · Retention
          </p>
          <h1 className="text-3xl font-bold text-white">Expiry management</h1>
          <p className="mt-1 text-sm text-slate-400">
            Review retention deadlines and execute deterministic governance actions with atomic audit tracking.
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </header>

      {/* Success Feedback Banner */}
      {actionSuccess && (
        <div
          role="status"
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-emerald-900/80 bg-emerald-950/40 text-emerald-300 text-sm"
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
            <div>
              <p className="font-semibold">{actionSuccess.message}</p>
              <p className="text-xs text-emerald-400/80 mt-0.5">
                Record <strong className="font-mono">{actionSuccess.record_id}</strong> · Audit ID:{' '}
                <strong className="font-mono">#{actionSuccess.audit_id}</strong>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to={`/audit?record_id=${encodeURIComponent(actionSuccess.record_id)}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-700 bg-emerald-900/40 text-xs font-semibold text-emerald-200 hover:bg-emerald-900/80 transition-colors whitespace-nowrap"
            >
              <span>View in Audit Trail</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
            <button
              onClick={() => setActionSuccess(null)}
              className="text-emerald-400 hover:text-emerald-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Error Feedback Banner */}
      {actionError && (
        <div
          role="alert"
          className="flex items-start justify-between gap-3 p-4 rounded-xl border border-rose-900/80 bg-rose-950/40 text-rose-300 text-sm"
        >
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
            <div>
              <p className="font-semibold">Action Execution Failed</p>
              <p className="text-xs text-rose-300/90 mt-1">{actionError}</p>
            </div>
          </div>
          <button onClick={() => setActionError(null)} className="text-rose-400 hover:text-rose-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Lanes Grid */}
      {loading ? (
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-14 text-center text-slate-400 font-mono">
          <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-sky-400" />
          Loading retention records…
        </div>
      ) : error ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-900 bg-rose-950/30 p-10 text-center text-rose-300"
        >
          {error}
          <button onClick={load} className="ml-3 underline">
            Try again
          </button>
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {lanes.map((lane) => {
            const Icon = lane.icon;
            const items = records.filter((r) => getRecordLane(r) === lane.title);
            return (
              <section
                key={lane.title}
                className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950 flex flex-col"
              >
                <div className="flex items-center justify-between border-b border-slate-800 p-5">
                  <div className="flex items-center gap-3">
                    <Icon className={lane.tone} size={19} />
                    <div>
                      <h2 className="font-semibold text-white">{lane.title}</h2>
                      <p className="text-xs text-slate-500">{lane.description}</p>
                    </div>
                  </div>
                  <span className="rounded-full bg-slate-800 px-2.5 py-1 text-xs text-slate-300 font-mono">
                    {items.length}
                  </span>
                </div>

                {items.length ? (
                  <ul className="divide-y divide-slate-800/80 flex-1">
                    {items.map((r) => (
                      <li
                        key={r.id}
                        className="flex flex-wrap items-center justify-between gap-3 p-4 hover:bg-slate-900/40 transition-colors"
                      >
                        <div className="min-w-0">
                          <Link
                            to={`/records?id=${encodeURIComponent(r.record_id)}`}
                            className="font-mono text-sm font-semibold text-sky-400 hover:underline"
                          >
                            {r.record_id}
                          </Link>
                          <p className="truncate text-sm text-slate-200">
                            {r.data_type} <span className="text-slate-500">· {r.category}</span>
                          </p>
                          <p className="mt-1 text-xs text-slate-500">
                            Expiry {r.expiry_date} · {r.ai_recommendation || 'No recommendation'}
                          </p>
                        </div>

                        {/* Action buttons for non-completed lanes */}
                        {lane.title !== 'Completed' && (
                          <div className="flex flex-wrap items-center gap-2">
                            {lane.allowedActions.includes('REVIEW') && (
                              <button
                                disabled={actionLoadingId === r.record_id}
                                onClick={() => initiateAction(r, 'REVIEW')}
                                className="inline-flex items-center gap-1 rounded-lg border border-sky-800/60 bg-sky-950/40 px-2.5 py-1.5 text-xs text-sky-300 hover:bg-sky-900/60 disabled:opacity-50 transition-colors"
                                title="Queue record for retention review"
                              >
                                {actionLoadingId === r.record_id ? (
                                  <RefreshCw className="w-3 h-3 animate-spin" />
                                ) : (
                                  <Eye className="w-3 h-3" />
                                )}
                                <span>Queue review</span>
                              </button>
                            )}

                            {lane.allowedActions.includes('ANONYMIZE') && (
                              <button
                                disabled={actionLoadingId === r.record_id}
                                onClick={() => initiateAction(r, 'ANONYMIZE')}
                                className="inline-flex items-center gap-1 rounded-lg border border-purple-800/60 bg-purple-950/40 px-2.5 py-1.5 text-xs text-purple-300 hover:bg-purple-900/60 disabled:opacity-50 transition-colors"
                                title="Mark as Anonymized and Archived (simulated)"
                              >
                                <FileText className="w-3 h-3" />
                                <span>Anonymize</span>
                              </button>
                            )}

                            {lane.allowedActions.includes('DELETE') && (
                              <button
                                disabled={actionLoadingId === r.record_id}
                                onClick={() => initiateAction(r, 'DELETE')}
                                className="inline-flex items-center gap-1 rounded-lg border border-rose-800/60 bg-rose-950/40 px-2.5 py-1.5 text-xs text-rose-300 hover:bg-rose-900/60 disabled:opacity-50 transition-colors"
                                title="Mark as Deleted (simulated; Admin/Data Governance only)"
                              >
                                <Trash2 className="w-3 h-3" />
                                <span>Delete</span>
                              </button>
                            )}
                          </div>
                        )}

                        {lane.title === 'Completed' && (
                          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>
                              {r.deletion_status === 'Deleted'
                                ? 'Deleted'
                                : r.anonymization_status === 'Anonymized'
                                ? 'Anonymized'
                                : 'Approved'}
                            </span>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="p-8 text-center text-sm text-slate-500">
                    No records in this section.
                  </p>
                )}
              </section>
            );
          })}
        </div>
      )}

      {/* ACTION CONFIRMATION MODAL */}
      {pendingActionRecord && pendingActionType && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <Shield className="w-5 h-5 text-sky-400" />
                <h3 className="text-lg font-bold text-slate-100">
                  Confirm {pendingActionType} Action
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setPendingActionRecord(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <p className="text-slate-300">
                You are about to execute action{' '}
                <strong className="font-mono text-sky-400">{pendingActionType}</strong> on record{' '}
                <strong className="font-mono text-white">{pendingActionRecord.record_id}</strong>.
              </p>

              {/* Status Simulation Disclosure for Anonymize & Delete */}
              {(pendingActionType === 'DELETE' || pendingActionType === 'ANONYMIZE') && (
                <div className="p-3.5 rounded-lg border border-amber-900/60 bg-amber-950/30 text-xs text-amber-300 space-y-1 leading-relaxed">
                  <div className="font-semibold flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                    <span>Status-Only Simulation Notice</span>
                  </div>
                  {pendingActionType === 'DELETE' ? (
                    <p>
                      In the current system version, deletion is a <strong>simulated status update</strong>.
                      The database row is <strong>NOT physically purged</strong>, and sensitive fields remain intact
                      for compliance auditing. The record&apos;s status will update to <code>Expired</code> and
                      deletion status to <code>Deleted</code>.
                    </p>
                  ) : (
                    <p>
                      In the current system version, anonymization is a <strong>simulated status update</strong>.
                      Sensitive fields are <strong>NOT masked or scrubbed</strong>. The record&apos;s status will update
                      to <code>Archived</code> and anonymization status to <code>Anonymized</code>.
                    </p>
                  )}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Reason / Narrative (Optional)
                </label>
                <input
                  type="text"
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  placeholder="e.g. Scheduled retention review completed"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setPendingActionRecord(null)}
                className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={executeConfirmedAction}
                className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-sky-500 transition"
              >
                <span>Confirm & Execute {pendingActionType}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExpiryManagement;
