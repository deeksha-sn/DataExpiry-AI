import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { apiService } from '../services/api';
import { DataRecord, LifecycleActionResponse } from '../types';
import {
  Search,
  Shield,
  Calendar,
  Tag,
  User,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Trash2,
  Eye,
  RefreshCw,
  ExternalLink,
  X,
  Lock,
} from 'lucide-react';

export const RecordDetails: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryId = searchParams.get('id') || '';

  const [inputRecordId, setInputRecordId] = useState<string>(queryId);
  const [record, setRecord] = useState<DataRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Lifecycle action states
  const [actionReason, setActionReason] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<LifecycleActionResponse | null>(null);
  const [confirmModalAction, setConfirmModalAction] = useState<
    'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE' | null
  >(null);

  const fetchRecord = (idToFetch: string) => {
    setLoading(true);
    setError(null);
    setActionError(null);
    setActionSuccess(null);
    apiService
      .getDataRecord(idToFetch)
      .then((data) => {
        setRecord(data);
        setLoading(false);
      })
      .catch((err) => {
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

  // Trigger confirmation or immediate execution
  const initiateAction = (action: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE') => {
    setActionError(null);
    // ANONYMIZE and DELETE strictly require explicit confirmation modal with disclosure
    if (action === 'ANONYMIZE' || action === 'DELETE') {
      setConfirmModalAction(action);
    } else {
      executeAction(action);
    }
  };

  // Execute lifecycle action via API
  const executeAction = async (action: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE') => {
    if (!record) return;

    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const response = await apiService.executeLifecycleAction(
        record.record_id,
        action,
        actionReason.trim() || null
      );
      setActionSuccess(response);
      setConfirmModalAction(null);
      setActionReason('');

      // Refresh record metadata from the backend
      const updatedRecord = await apiService.getDataRecord(record.record_id);
      setRecord(updatedRecord);
    } catch (err: any) {
      console.error('Lifecycle action failed:', err);
      setActionError(err.message || `Failed to execute action ${action}.`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[.18em] text-sky-400">
          Catalog · Record profile
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-white">Data record details</h1>
        <p className="text-slate-400 mt-1">
          Deep inspection of record metadata, collection purpose, and deterministic lifecycle actions.
        </p>
      </div>

      {/* Record Lookup Form */}
      <form onSubmit={handleSubmit} className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            aria-label="Record ID"
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
            {/* Record Identity & High-Level Badges */}
            <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-3">
              <div>
                <span className="text-xs font-mono text-slate-400">RECORD IDENTIFIER</span>
                <h2 className="text-2xl font-bold text-sky-400 font-mono">{record.record_id}</h2>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    record.status === 'Expired'
                      ? 'bg-rose-950 text-rose-300 border border-rose-800'
                      : record.status === 'Expiring Soon'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : record.status === 'Archived'
                      ? 'bg-purple-950 text-purple-300 border border-purple-800'
                      : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  }`}
                >
                  Status: {record.status}
                </span>

                {record.review_status && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-slate-900 border border-slate-700 text-slate-300">
                    Review: {record.review_status}
                  </span>
                )}
                {record.anonymization_status && record.anonymization_status !== 'Not Required' && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-purple-950/50 border border-purple-800 text-purple-300">
                    Anon: {record.anonymization_status}
                  </span>
                )}
                {record.deletion_status && record.deletion_status !== 'Not Required' && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-rose-950/50 border border-rose-800 text-rose-300">
                    Deletion: {record.deletion_status}
                  </span>
                )}
              </div>
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-slate-500" /> Data Type
                </span>
                <p className="font-semibold text-slate-200">{record.data_type}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-slate-500" /> Category
                </span>
                <p className="font-semibold text-slate-200">{record.category}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-slate-500" /> Sensitivity Level
                </span>
                <p className="font-semibold text-slate-200">{record.sensitivity}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-slate-500" /> Owner Department
                </span>
                <p className="font-semibold text-slate-200">{record.owner}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" /> Collection Date
                </span>
                <p className="font-mono text-slate-200">{record.created_date}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" /> Mandated Expiry Date
                </span>
                <p className="font-mono text-slate-200">
                  {record.expiry_date} ({record.retention_period})
                </p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" /> Last Accessed
                </span>
                <p className="font-mono text-slate-200">{record.last_accessed || 'Not provided'}</p>
              </div>

              <div className="space-y-1">
                <span className="text-slate-400 text-xs">Purpose Mismatch</span>
                <p className="font-semibold text-slate-200">
                  {record.purpose_mismatch === undefined
                    ? 'Not assessed'
                    : record.purpose_mismatch
                    ? '⚠️ Flagged'
                    : 'Not flagged'}
                </p>
              </div>

              <div className="space-y-1 md:col-span-2">
                <span className="text-slate-400 text-xs">Stated Collection Purpose</span>
                <p className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
                  {record.collection_purpose}
                </p>
              </div>

              <div className="space-y-3 md:col-span-2 border-t border-slate-800 pt-5">
                <h3 className="flex items-center gap-2 font-semibold text-slate-200">
                  <Sparkles className="h-4 w-4 text-violet-400" /> AI assessment
                </h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <span className="text-xs text-slate-400">Recommendation</span>
                    <p className="mt-1 font-semibold text-violet-200">
                      {record.ai_recommendation || 'Not provided by API'}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400">Risk level</span>
                    <p className="mt-1 text-slate-200">{record.risk_level || 'Not provided by API'}</p>
                  </div>
                  <div className="md:col-span-2">
                    <span className="text-xs text-slate-400">Explanation</span>
                    <p className="mt-1 text-slate-300">
                      {record.ai_explanation || 'No AI explanation is available for this record.'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-1 md:col-span-2">
                <span className="text-slate-400 text-xs">Current Usage</span>
                <p className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
                  {record.current_usage}
                </p>
              </div>
            </div>
          </div>

          {/* Lifecycle Action Execution Panel */}
          <section className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-slate-200 font-semibold">
                <Shield className="w-5 h-5 text-sky-400" />
                <span>Deterministic Lifecycle Actions</span>
              </div>
              <span className="text-xs text-slate-500 font-mono">
                API: POST /api/data/{record.record_id}/execute-action
              </span>
            </div>

            {/* Success Feedback */}
            {actionSuccess && (
              <div
                role="status"
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg border border-emerald-900/80 bg-emerald-950/40 text-emerald-300 text-sm"
              >
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
                  <div>
                    <p className="font-semibold">{actionSuccess.message}</p>
                    <p className="text-xs text-emerald-400/80 mt-0.5">
                      New Status: <strong>{actionSuccess.new_status}</strong> · Audit ID:{' '}
                      <strong className="font-mono">#{actionSuccess.audit_id}</strong>
                    </p>
                  </div>
                </div>
                <Link
                  to={`/audit?record_id=${encodeURIComponent(record.record_id)}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-700 bg-emerald-900/40 text-xs font-semibold text-emerald-200 hover:bg-emerald-900/80 transition-colors whitespace-nowrap self-start sm:self-auto"
                >
                  <span>View in Audit Trail</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}

            {/* Error Feedback */}
            {actionError && (
              <div
                role="alert"
                className="flex items-start justify-between gap-3 p-4 rounded-lg border border-rose-900/80 bg-rose-950/40 text-rose-300 text-sm"
              >
                <div className="flex items-start gap-2.5">
                  <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
                  <div>
                    <p className="font-semibold">Action Execution Failed</p>
                    <p className="text-xs text-rose-300/90 mt-1">{actionError}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setActionError(null)}
                  className="text-rose-400 hover:text-rose-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Optional Reason / Justification Input */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Action Justification / Narrative (Optional)
              </label>
              <input
                type="text"
                disabled={actionLoading}
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="e.g. Mandated retention reached; compliance review completed..."
                className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none disabled:opacity-50"
              />
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <button
                type="button"
                disabled={actionLoading}
                onClick={() => initiateAction('KEEP')}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-emerald-700/60 bg-emerald-950/40 px-3 py-2.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/60 hover:border-emerald-500 disabled:opacity-50 transition-colors"
                title="Approve continued retention (Admin, Data Governance)"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Keep Active</span>
              </button>

              <button
                type="button"
                disabled={actionLoading}
                onClick={() => initiateAction('REVIEW')}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-amber-700/60 bg-amber-950/40 px-3 py-2.5 text-xs font-semibold text-amber-300 hover:bg-amber-900/60 hover:border-amber-500 disabled:opacity-50 transition-colors"
                title="Queue for human review (Admin, Data Governance, Privacy Officer)"
              >
                <Eye className="w-4 h-4" />
                <span>Queue Review</span>
              </button>

              <button
                type="button"
                disabled={actionLoading}
                onClick={() => initiateAction('ANONYMIZE')}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-purple-700/60 bg-purple-950/40 px-3 py-2.5 text-xs font-semibold text-purple-300 hover:bg-purple-900/60 hover:border-purple-500 disabled:opacity-50 transition-colors"
                title="Mark as Anonymized and Archived (Admin, Data Governance, Privacy Officer)"
              >
                <FileText className="w-4 h-4" />
                <span>Anonymize</span>
              </button>

              <button
                type="button"
                disabled={actionLoading}
                onClick={() => initiateAction('DELETE')}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-700/60 bg-rose-950/40 px-3 py-2.5 text-xs font-semibold text-rose-300 hover:bg-rose-900/60 hover:border-rose-500 disabled:opacity-50 transition-colors"
                title="Mark as Deleted (simulated; Admin and Data Governance only)"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete</span>
              </button>
            </div>

            <p className="text-[11px] text-slate-500 leading-relaxed pt-1">
              Actions require authorized roles (<code className="text-slate-400">ADMIN</code>,{' '}
              <code className="text-slate-400">DATA_GOVERNANCE</code>, or{' '}
              <code className="text-slate-400">PRIVACY_OFFICER</code>; DELETE is restricted to Admin & Governance).
              Anonymize and Delete execute status simulations without physical row purging.
            </p>
          </section>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-10 text-center text-slate-400">
          Enter a record ID above, or open a record from the inventory to inspect its details.
        </div>
      )}

      {/* CONFIRMATION MODAL FOR ANONYMIZE & DELETE */}
      {confirmModalAction && record && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <AlertTriangle
                  className={`w-5 h-5 ${
                    confirmModalAction === 'DELETE' ? 'text-rose-400' : 'text-purple-400'
                  }`}
                />
                <h3 className="text-lg font-bold text-slate-100">
                  Confirm Simulated {confirmModalAction === 'DELETE' ? 'Deletion' : 'Anonymization'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => !actionLoading && setConfirmModalAction(null)}
                className="text-slate-400 hover:text-slate-200"
                disabled={actionLoading}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <p className="text-slate-300">
                You are about to execute action{' '}
                <strong
                  className={`font-mono ${
                    confirmModalAction === 'DELETE' ? 'text-rose-400' : 'text-purple-400'
                  }`}
                >
                  {confirmModalAction}
                </strong>{' '}
                on record <strong className="font-mono text-sky-400">{record.record_id}</strong>.
              </p>

              {/* Status Simulation Disclosure */}
              <div className="p-3.5 rounded-lg border border-amber-900/60 bg-amber-950/30 text-xs text-amber-300 space-y-1.5 leading-relaxed">
                <div className="font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                  <span>Status-Only Governance Simulation</span>
                </div>
                {confirmModalAction === 'DELETE' ? (
                  <p>
                    In the current system architecture, deletion is a <strong>simulated status update</strong>.
                    The database row will <strong>NOT be physically deleted</strong>, and sensitive data fields
                    are preserved intact for compliance auditing. The record&apos;s deletion status will update to{' '}
                    <code>Deleted</code> and status to <code>Expired</code>.
                  </p>
                ) : (
                  <p>
                    In the current system architecture, anonymization is a <strong>simulated status update</strong>.
                    Sensitive columns will <strong>NOT be masked or scrubbed</strong>. The record&apos;s anonymization
                    status will update to <code>Anonymized</code> and status to <code>Archived</code>.
                  </p>
                )}
              </div>

              {actionReason && (
                <div className="text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">Justification:</span> {actionReason}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                disabled={actionLoading}
                onClick={() => setConfirmModalAction(null)}
                className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={actionLoading}
                onClick={() => executeAction(confirmModalAction)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold text-white shadow transition disabled:opacity-50 ${
                  confirmModalAction === 'DELETE'
                    ? 'bg-rose-600 hover:bg-rose-500'
                    : 'bg-purple-600 hover:bg-purple-500'
                }`}
              >
                {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>
                  {actionLoading ? 'Executing...' : `Confirm & Execute ${confirmModalAction}`}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecordDetails;
