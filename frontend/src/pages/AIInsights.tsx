import React from 'react';
import { Sparkles, Brain, Cpu, Bot } from 'lucide-react';

export const AIInsights: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold px-2.5 py-1 rounded bg-purple-950 text-purple-300 border border-purple-800 mb-2">
          ASSIGNED TO TEAM MEMBER 2 (AI & INSIGHTS)
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100">AI Data Lifecycle Insights</h1>
        <p className="text-slate-400 mt-1">LLM-assisted recommendations (KEEP, REVIEW, ANONYMIZE, DELETE) and risk reasoning.</p>
      </div>

      {/* Module Handoff Banner */}
      <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
        <div className="flex items-center gap-3 text-purple-400 font-semibold">
          <Sparkles className="w-5 h-5" />
          <span>Module Shell — Ready for Team Member 2 AI Module</span>
        </div>
        <p className="text-sm text-slate-400 leading-relaxed">
          Team Member 2 will connect this page to LLM endpoints to display automated lifecycle actions (`KEEP`, `REVIEW`, `ANONYMIZE`, `DELETE`) with natural language explanations.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-emerald-400">Recommendation</span>
            <h3 className="font-bold text-slate-200">KEEP</h3>
            <p className="text-xs text-slate-400">Valid retention period & compliant usage.</p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-amber-400">Recommendation</span>
            <h3 className="font-bold text-slate-200">REVIEW</h3>
            <p className="text-xs text-slate-400">Approaching expiry or minor usage ambiguity.</p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-purple-400">Recommendation</span>
            <h3 className="font-bold text-slate-200">ANONYMIZE</h3>
            <p className="text-xs text-slate-400">Strip PII while preserving analytical value.</p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-rose-400">Recommendation</span>
            <h3 className="font-bold text-slate-200">DELETE</h3>
            <p className="text-xs text-slate-400">Expired record or critical purpose violation.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
