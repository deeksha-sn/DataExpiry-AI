import React from 'react';
import { AlertTriangle, Sparkles, ShieldCheck } from 'lucide-react';

export const PurposeMismatch: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-purple-950 text-purple-300 border border-purple-800 mb-2">
          ASSIGNED TO TEAM MEMBER 2 (AI & PURPOSE GOVERNANCE)
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100">Purpose Mismatch Detection</h1>
        <p className="text-slate-400 mt-1">Identify data usage creep where active utilization diverges from original collection consent.</p>
      </div>

      {/* Module Handoff Banner */}
      <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
        <div className="flex items-center gap-3 text-purple-400 font-semibold">
          <AlertTriangle className="w-5 h-5" />
          <span>Module Shell — Ready for Team Member 2 AI Integration</span>
        </div>
        <p className="text-sm text-slate-400 leading-relaxed">
          Team Member 2 will connect the backend AI semantic analysis module to compare <code className="text-purple-300">collection_purpose</code> against <code className="text-purple-300">current_usage</code> and generate purpose divergence scores.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-slate-400">Target Feature 1</span>
            <h3 className="font-semibold text-slate-200">Semantic Divergence Scoring</h3>
            <p className="text-xs text-slate-400">Embedding vector comparison between consent and usage.</p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-slate-400">Target Feature 2</span>
            <h3 className="font-semibold text-slate-200">High-Risk Creep Alerts</h3>
            <p className="text-xs text-slate-400">Highlight monetization or unapproved AI training use cases.</p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-slate-400">Target Feature 3</span>
            <h3 className="font-semibold text-slate-200">Remediation Workflows</h3>
            <p className="text-xs text-slate-400">Flag for legal consent update or immediate usage halt.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
