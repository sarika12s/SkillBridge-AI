import React from 'react';
import type { SkillEvidenceChange } from '../../types/dashboard';
import { X, CheckCircle, ArrowRight, ShieldCheck } from 'lucide-react';

interface EvidenceInspectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  changes: SkillEvidenceChange[];
}

export const EvidenceInspectionModal: React.FC<EvidenceInspectionModalProps> = ({
  isOpen,
  onClose,
  changes,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Skill Evidence & Trajectory</h3>
              <p className="text-xs text-slate-400">Verifiable extraction evidence across resume versions</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="p-5 overflow-y-auto space-y-4">
          {changes.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">
              No evidence modifications detected between these versions.
            </div>
          ) : (
            changes.map((item, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-3"
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">{item.skill_name}</span>
                    {item.strengthened && (
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Strengthened
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[11px]">
                      {item.previous_section}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                    <span className="px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/50 font-mono text-[11px]">
                      {item.new_section}
                    </span>
                  </div>
                </div>

                {item.previous_evidence && (
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold text-slate-500">Previous Evidence</span>
                    <p className="text-xs text-slate-400 italic bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                      "{item.previous_evidence}"
                    </p>
                  </div>
                )}

                {item.new_evidence && (
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold text-indigo-400">Current Evidence</span>
                    <p className="text-xs text-slate-200 bg-slate-900/90 p-2.5 rounded-lg border border-indigo-900/30">
                      "{item.new_evidence}"
                    </p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
