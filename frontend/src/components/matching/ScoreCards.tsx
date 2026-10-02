import React from 'react';
import type { ScoreBreakdown } from '../../types/matching';
import { Target, FileText, Info } from 'lucide-react';

interface ScoreCardsProps {
  compatibilityScore: number;
  atsReadinessScore: number;
  breakdowns: ScoreBreakdown[];
}

export const ScoreCards: React.FC<ScoreCardsProps> = ({
  compatibilityScore,
  atsReadinessScore,
  breakdowns,
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-950/20';
    if (score >= 60) return 'text-cyan-400 border-cyan-500/30 bg-cyan-950/20';
    if (score >= 40) return 'text-amber-400 border-amber-500/30 bg-amber-950/20';
    return 'text-rose-400 border-rose-500/30 bg-rose-950/20';
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-cyan-500';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-6">
      {/* Top Dual Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Job Compatibility Score */}
        <div className={`p-6 rounded-2xl border backdrop-blur-md transition-all ${getScoreColor(compatibilityScore)}`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <Target className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">Job Compatibility Score</h3>
                <p className="text-xs text-slate-400">Target role requirement alignment</p>
              </div>
            </div>
            <span className="text-3xl font-extrabold tracking-tight">
              {compatibilityScore.toFixed(1)}%
            </span>
          </div>

          <div className="w-full bg-slate-900/60 rounded-full h-2.5 mb-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${getProgressColor(compatibilityScore)}`}
              style={{ width: `${Math.min(100, Math.max(0, compatibilityScore))}%` }}
            />
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Analytical measure of how well demonstrated candidate skills, experience, and education align with mandatory and preferred role requirements.
          </p>
        </div>

        {/* SkillBridge ATS Readiness Score */}
        <div className={`p-6 rounded-2xl border backdrop-blur-md transition-all ${getScoreColor(atsReadinessScore)}`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                <FileText className="w-5 h-5 text-teal-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">SkillBridge ATS Readiness</h3>
                <p className="text-xs text-slate-400">Parsing clarity & keyword density</p>
              </div>
            </div>
            <span className="text-3xl font-extrabold tracking-tight">
              {atsReadinessScore.toFixed(1)}%
            </span>
          </div>

          <div className="w-full bg-slate-900/60 rounded-full h-2.5 mb-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${getProgressColor(atsReadinessScore)}`}
              style={{ width: `${Math.min(100, Math.max(0, atsReadinessScore))}%` }}
            />
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Internal analytical metric based on structured section readability, keyword exactness, and explicit verifiable evidence sentences.
          </p>
        </div>
      </div>

      {/* Component Breakdown Accordion / Grid */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Info className="w-4 h-4 text-cyan-400" />
          <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            Explainable Score Component Breakdown
          </h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {breakdowns.map((b) => (
            <div
              key={b.component_name}
              className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-300 capitalize">
                    {b.component_name.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs font-bold text-white">
                    {b.score.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700/60 rounded-full h-1.5 mb-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${getProgressColor(b.score)}`}
                    style={{ width: `${Math.min(100, Math.max(0, b.score))}%` }}
                  />
                </div>
              </div>
              <div className="mt-2 text-[11px] text-slate-400 leading-tight">
                {b.explanation}
                <div className="mt-1 text-[10px] text-slate-500">
                  Weight: {(b.weight * 100).toFixed(0)}% (Contributes +{b.weighted_score.toFixed(1)} pts)
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
