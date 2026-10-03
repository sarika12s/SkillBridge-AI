import React from 'react';
import type { NextBestSkill } from '../../types/learning';
import {
  Compass,
  Sparkles,
  Clock,
  TrendingUp,
  Unlock,
  CheckCircle2,
  AlertTriangle,
  Layers,
} from 'lucide-react';

interface NextBestSkillBannerProps {
  nextBestSkill?: NextBestSkill | null;
  overallProgress: number;
  totalSkillsCount: number;
  completedSkillsCount: number;
  onSelectSkill?: (skillId: string, itemId?: string | null) => void;
}

export const NextBestSkillBanner: React.FC<NextBestSkillBannerProps> = ({
  nextBestSkill,
  overallProgress,
  totalSkillsCount,
  completedSkillsCount,
  onSelectSkill,
}) => {
  if (overallProgress === 100 || (totalSkillsCount > 0 && completedSkillsCount === totalSkillsCount)) {
    return (
      <div className="bg-gradient-to-r from-emerald-950/60 via-slate-900 to-slate-900 border border-emerald-500/30 rounded-2xl p-6 mb-6 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-emerald-200">
              Curriculum Completed!
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              You have acquired or completed all prioritized milestones for this target. Keep your skills sharp with continuous practice.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!nextBestSkill) {
    return (
      <div className="bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border border-amber-500/30 rounded-2xl p-6 mb-6 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-amber-200">
              No Immediate Unlocked Skills
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              All remaining target competencies currently have unsatisfied prerequisites. Check your foundational knowledge graph below.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden bg-gradient-to-r from-indigo-950/60 via-slate-900/90 to-purple-950/40 border border-indigo-500/40 rounded-2xl p-6 mb-6 shadow-2xl backdrop-blur-sm">
      {/* Decorative accent background glow */}
      <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-3 max-w-3xl">
          {/* Header Badge Row */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 animate-pulse">
              <Sparkles className="w-3.5 h-3.5" />
              Recommended Next Best Skill
            </span>

            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
              {nextBestSkill.category.replace('_', ' ')}
            </span>

            {nextBestSkill.is_implicit_prerequisite && (
              <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                <Layers className="w-3 h-3" />
                Foundational Prerequisite
              </span>
            )}

            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-900/60 text-indigo-300 border border-indigo-700/60">
              Priority Score: {nextBestSkill.priority_score.toFixed(1)}/100
            </span>
          </div>

          {/* Skill Title */}
          <div>
            <h2 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
              <span>{nextBestSkill.skill_name}</span>
            </h2>
            <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
              {nextBestSkill.explanation}
            </p>
          </div>

          {/* Metrics Pill Grid */}
          <div className="flex flex-wrap items-center gap-3 pt-1 text-xs">
            <span className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300 font-medium">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              Est. {nextBestSkill.estimated_hours} Hours
            </span>

            {nextBestSkill.delta_compatibility > 0 && (
              <span className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-semibold">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                +{nextBestSkill.delta_compatibility.toFixed(1)}% Match Boost
              </span>
            )}

            {nextBestSkill.downstream_unlocked_count > 0 && (
              <span
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-300 font-medium"
                title={`Unlocks: ${nextBestSkill.downstream_unlocked_skills.join(', ')}`}
              >
                <Unlock className="w-3.5 h-3.5 text-purple-400" />
                Unlocks {nextBestSkill.downstream_unlocked_count} downstream skill{nextBestSkill.downstream_unlocked_count > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex flex-col sm:flex-row items-stretch lg:items-end justify-center shrink-0 gap-3">
          {onSelectSkill && (
            <button
              onClick={() => onSelectSkill(nextBestSkill.skill_id, nextBestSkill.item_id)}
              className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50 transition cursor-pointer"
            >
              <Compass className="w-4 h-4" />
              <span>Focus on this Skill</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
