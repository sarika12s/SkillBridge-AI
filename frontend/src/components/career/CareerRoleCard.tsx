import React from 'react';
import type { CareerRoleMatch } from '../../types/career';
import { BookOpen, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';

interface CareerRoleCardProps {
  role: CareerRoleMatch;
  onViewBreakdown: (role: CareerRoleMatch) => void;
  onGenerateLearningPath: (role: CareerRoleMatch) => void;
  isGeneratingPath?: boolean;
}

export const CareerRoleCard: React.FC<CareerRoleCardProps> = ({
  role,
  onViewBreakdown,
  onGenerateLearningPath,
  isGeneratingPath = false,
}) => {
  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    if (score >= 60) return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
    if (score >= 40) return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl hover:border-slate-700 transition duration-200 flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                {role.occupation_code}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                {role.category.replace('_', ' ')}
              </span>
            </div>
            <h3 className="text-xl font-bold text-slate-100">{role.occupation_title}</h3>
          </div>

          {/* Compatibility Score Pill */}
          <div className={`px-4 py-2 rounded-xl border flex flex-col items-center ${getScoreBadgeColor(role.compatibility_score)}`}>
            <span className="text-xs uppercase tracking-wider font-semibold">Match</span>
            <span className="text-2xl font-black">{role.compatibility_score}%</span>
          </div>
        </div>

        {/* Narrative */}
        <p className="text-sm text-slate-300 leading-relaxed mb-5 bg-slate-950/50 p-3 rounded-lg border border-slate-800/80">
          {role.summary_explanation}
        </p>

        {/* Competency Overview */}
        <div className="grid grid-cols-2 gap-2 mb-5 text-xs">
          <div className="bg-slate-800/40 p-2.5 rounded-lg border border-slate-800">
            <span className="text-slate-400 block mb-0.5">Matched Competencies</span>
            <span className="text-slate-200 font-semibold text-sm">
              {role.matched_skills_count} / {role.total_skills_count}
            </span>
          </div>
          <div className="bg-slate-800/40 p-2.5 rounded-lg border border-slate-800">
            <span className="text-slate-400 block mb-0.5">Gap Deficits</span>
            <span className="text-amber-400 font-semibold text-sm">
              {role.skill_gaps.length} Skills
            </span>
          </div>
        </div>

        {/* Strengths */}
        {role.strengths.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 mb-2">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Key Strengths & Demonstrated Skills</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {role.strengths.slice(0, 5).map((sk) => (
                <span
                  key={sk}
                  className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                >
                  {sk}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Skill Gaps */}
        {role.skill_gaps.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400 mb-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Priority Skill Gaps</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {role.skill_gaps.slice(0, 5).map((sk) => (
                <span
                  key={sk}
                  className="px-2 py-0.5 rounded text-xs bg-amber-500/10 text-amber-300 border border-amber-500/20"
                >
                  {sk}
                </span>
              ))}
              {role.skill_gaps.length > 5 && (
                <span className="text-xs text-slate-500 self-center">
                  +{role.skill_gaps.length - 5} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="pt-4 border-t border-slate-800 flex items-center justify-between gap-3">
        <button
          onClick={() => onViewBreakdown(role)}
          className="text-xs font-medium text-slate-400 hover:text-slate-200 transition py-2 px-3 rounded-lg hover:bg-slate-800"
        >
          View Breakdown
        </button>
        <button
          onClick={() => onGenerateLearningPath(role)}
          disabled={isGeneratingPath}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition"
        >
          <BookOpen className="w-4 h-4" />
          <span>{isGeneratingPath ? 'Building Path...' : 'Generate Learning Path'}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
