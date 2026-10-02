import React from 'react';
import type { TopCareerRole } from '../../types/dashboard';
import { X, Briefcase, Award, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface RoleComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  roles: TopCareerRole[];
}

export const RoleComparisonModal: React.FC<RoleComparisonModalProps> = ({
  isOpen,
  onClose,
  roles,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Career Role Alignments</h3>
              <p className="text-xs text-slate-400">Cross-occupation compatibility derived from canonical skills</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Roles List */}
        <div className="p-5 overflow-y-auto space-y-3">
          {roles.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">
              No career compatibility analyses available. Run a career match to compare roles.
            </div>
          ) : (
            roles.map((role) => (
              <div
                key={role.id}
                className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">{role.title}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {role.code}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{role.category}</p>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-center">
                  <div className="text-right">
                    <div className="text-base font-bold text-emerald-400 flex items-center gap-1 justify-end">
                      <Award className="w-3.5 h-3.5" />
                      {role.compatibility_score}%
                    </div>
                    <div className="text-[10px] text-slate-500">Role Fit</div>
                  </div>
                  <Link
                    to="/career-compatibility"
                    className="p-2 rounded-xl bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white transition-colors"
                    title="View role details and learning roadmap"
                  >
                    <ArrowUpRight className="w-4 h-4" />
                  </Link>
                </div>
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
