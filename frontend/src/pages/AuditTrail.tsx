import React from 'react';
import { History, FileCode, CheckCircle2, Lock } from 'lucide-react';

export const AuditTrail: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-amber-950 text-amber-300 border border-amber-800 mb-2">
          ASSIGNED TO TEAM MEMBER 4 (AUDIT LOGGING)
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100">Compliance Audit Trail</h1>
        <p className="text-slate-400 mt-1">Immutable logging of data lifecycle events, policy executions, and deletion proofs.</p>
      </div>

      {/* Module Handoff Banner */}
      <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
        <div className="flex items-center gap-3 text-amber-400 font-semibold">
          <History className="w-5 h-5" />
          <span>Module Shell — Ready for Team Member 4 Audit Logging</span>
        </div>
        <p className="text-sm text-slate-400 leading-relaxed">
          Team Member 4 will connect this page to backend audit event logs to display cryptographic signatures and time-stamped proof of deletion/anonymization for compliance auditors.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-slate-400">Target Feature 1</span>
            <h3 className="font-semibold text-slate-200">Lifecycle Event Logs</h3>
            <p className="text-xs text-slate-400">Track record creation, status transitions, and reviews.</p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-slate-400">Target Feature 2</span>
            <h3 className="font-semibold text-slate-200">Deletion Certificates</h3>
            <p className="text-xs text-slate-400">Generate verifiable cryptographic proof of data purging.</p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-slate-400">Target Feature 3</span>
            <h3 className="font-semibold text-slate-200">Auditor Export</h3>
            <p className="text-xs text-slate-400">Export compliance reports in CSV and JSON formats.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
