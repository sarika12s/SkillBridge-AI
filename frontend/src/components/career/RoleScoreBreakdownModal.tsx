import React from 'react';
import type { CareerRoleMatch } from '../../types/career';
import { X, ShieldCheck, Info } from 'lucide-react';

interface RoleScoreBreakdownModalProps {
  role: CareerRoleMatch | null;
  onClose: () => void;
}

export const RoleScoreBreakdownModal: React.FC<RoleScoreBreakdownModalProps> = ({
  role,
  onClose,
}) => {
  if (!role) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-100 text-lg">
              {role.occupation_title} — Analytical Score Breakdown
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[75vh] overflow-y-auto space-y-6">
          {/* Summary Box */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 flex items-start gap-3">
            <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-xs uppercase tracking-wider font-semibold text-indigo-400 mb-1">
                Factual Compatibility Summary
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                {role.summary_explanation}
              </p>
            </div>
          </div>

          {/* Overall Score Banner */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/40 border border-slate-800">
            <div>
              <span className="text-xs font-medium text-slate-400 block">Overall Analytical Match</span>
              <span className="text-sm text-slate-300">Composite weighted readiness score</span>
            </div>
            <div className="text-3xl font-black text-indigo-400">
              {role.compatibility_score}%
            </div>
          </div>

          {/* Components Breakdown */}
          <div className="space-y-4">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Score Component Weights & Justification
            </h4>

            {role.components.map((comp, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 space-y-2"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="font-semibold text-slate-200">{comp.component_name}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400">Weight: {(comp.weight * 100).toFixed(0)}%</span>
                    <span className="font-bold text-slate-100">{comp.score}%</span>
                    <span className="text-xs text-indigo-400 font-medium">({comp.weighted_score} pts)</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, comp.score))}%` }}
                  />
                </div>

                <p className="text-xs text-slate-400 leading-relaxed pt-1">
                  {comp.explanation}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition"
          >
            Close Breakdown
          </button>
        </div>
      </div>
    </div>
  );
};
