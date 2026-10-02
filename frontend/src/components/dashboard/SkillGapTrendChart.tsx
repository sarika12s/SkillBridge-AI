import React from 'react';
import type { SkillGapTrendItem } from '../../types/dashboard';
import { AlertCircle, ArrowUpRight, Flame } from 'lucide-react';
import { Link } from 'react-router-dom';

interface SkillGapTrendChartProps {
  skillGaps: SkillGapTrendItem[];
}

export const SkillGapTrendChart: React.FC<SkillGapTrendChartProps> = ({ skillGaps }) => {
  if (!skillGaps || skillGaps.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col items-center justify-center min-h-[300px] text-center">
        <div className="p-3 bg-slate-800/50 rounded-2xl text-emerald-400 mb-3">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h3 className="text-base font-medium text-slate-300">No Critical Skill Gaps Detected</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Your profile currently satisfies the analyzed role requirements or no gaps were identified.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-400" />
            Top Skill Gaps & Criticality
          </h3>
          <p className="text-xs text-slate-400">
            High-impact competencies required by target roles with weighted importance
          </p>
        </div>
        <Link
          to="/career-compatibility"
          className="text-xs font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
        >
          Generate Roadmap <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="space-y-3 pt-2">
        {skillGaps.slice(0, 6).map((gap) => {
          const isRequired = gap.priority === 'REQUIRED';
          const weightPct = Math.round(gap.importance_weight * 100);

          return (
            <div
              key={gap.id}
              className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-white">{gap.skill_name}</span>
                  <span
                    className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${
                      isRequired
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}
                  >
                    {gap.priority}
                  </span>
                  <span className="text-[10px] text-slate-400 px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700">
                    {gap.difficulty_level}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-1">{gap.reason}</p>
              </div>

              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                <div className="text-right">
                  <div className="text-xs font-semibold text-slate-200">{weightPct}%</div>
                  <div className="text-[10px] text-slate-500">Weight</div>
                </div>
                <div className="w-16 bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${isRequired ? 'bg-rose-400' : 'bg-amber-400'}`}
                    style={{ width: `${Math.min(weightPct, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
