import React from 'react';
import type { LearningStage, LearningPathItem, PrioritizedSkill } from '../../types/learning';
import {
  Clock,
  ExternalLink,
  CheckCircle2,
  CircleDashed,
  PlayCircle,
  Sparkles,
  Lock,
  Unlock,
  TrendingUp,
} from 'lucide-react';

interface LearningStageCardProps {
  stage: LearningStage;
  onUpdateItemStatus: (
    itemId: string,
    newStatus: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED'
  ) => void;
  updatingItemId?: string | null;
  prioritizedSkillsMap?: Record<string, PrioritizedSkill>;
}

export const LearningStageCard: React.FC<LearningStageCardProps> = ({
  stage,
  onUpdateItemStatus,
  updatingItemId,
  prioritizedSkillsMap,
}) => {
  const getStatusBadge = (item: LearningPathItem) => {
    switch (item.status) {
      case 'COMPLETED':
        if (item.verification_method === 'RESUME_EVIDENCE') {
          return (
            <span
              title={item.notes || 'Verified by resume evidence'}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 cursor-help"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Verified by Resume{item.verified_by_resume_version ? ` v${item.verified_by_resume_version}` : ''}
            </span>
          );
        }
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Completed
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/30 animate-pulse">
            <PlayCircle className="w-3.5 h-3.5" />
            In Progress
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <CircleDashed className="w-3.5 h-3.5" />
            Not Started
          </span>
        );
    }
  };

  const getDifficultyBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'BEGINNER':
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
      case 'INTERMEDIATE':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      case 'ADVANCED':
        return 'bg-purple-500/10 text-purple-300 border-purple-500/20';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      {/* Stage Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-black text-lg">
            {stage.stage_number}
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100">{stage.stage_title}</h3>
            <p className="text-xs text-slate-400">{stage.stage_description}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs font-medium text-slate-300">
          <Clock className="w-4 h-4 text-indigo-400" />
          <span>Est. {stage.stage_estimated_hours} Hours</span>
        </div>
      </div>

      {/* Stage Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {stage.items.map((item) => {
          const isUpdating = updatingItemId === item.id;
          return (
            <div
              key={item.id}
              className={`p-4 rounded-xl border transition flex flex-col justify-between ${
                item.status === 'COMPLETED'
                  ? 'bg-slate-950/40 border-emerald-900/40'
                  : item.status === 'IN_PROGRESS'
                  ? 'bg-slate-950/70 border-blue-900/40'
                  : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700'
              }`}
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-1.5 mb-1">
                      <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 inline-block">
                        {item.skill_category?.replace('_', ' ') || 'TECHNICAL'}
                      </span>
                      {(() => {
                        const prioritized =
                          prioritizedSkillsMap?.[item.skill_id] ||
                          prioritizedSkillsMap?.[item.skill_name.toLowerCase()];
                        if (!prioritized) return null;
                        return (
                          <>
                            {item.status !== 'COMPLETED' && prioritized.readiness_status === 'READY' && (
                              <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                                <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
                                Ready to Learn
                              </span>
                            )}
                            {item.status !== 'COMPLETED' && prioritized.readiness_status === 'BLOCKED' && (
                              <span
                                title={
                                  prioritized.unsatisfied_prerequisites.length > 0
                                    ? `Blocked by: ${prioritized.unsatisfied_prerequisites.join(', ')}`
                                    : 'Prerequisites required'
                                }
                                className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 cursor-help"
                              >
                                <Lock className="w-2.5 h-2.5 text-amber-400" />
                                Blocked ({prioritized.unsatisfied_prerequisites.length})
                              </span>
                            )}
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/40">
                              Priority {prioritized.priority_score.toFixed(1)}
                            </span>
                            {prioritized.delta_compatibility > 0 && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 flex items-center gap-0.5">
                                <TrendingUp className="w-2.5 h-2.5" />
                                +{prioritized.delta_compatibility.toFixed(1)}%
                              </span>
                            )}
                            {prioritized.downstream_unlocked_count > 0 && (
                              <span
                                title={`Unlocks: ${prioritized.downstream_unlocked_skills.join(', ')}`}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/40 flex items-center gap-0.5 cursor-help"
                              >
                                <Unlock className="w-2.5 h-2.5" />
                                Unlocks {prioritized.downstream_unlocked_count}
                              </span>
                            )}
                          </>
                        );
                      })()}
                    </div>
                    <h4 className="text-base font-bold text-slate-100">{item.skill_name}</h4>
                  </div>
                  <div>{getStatusBadge(item)}</div>
                </div>

                {/* Resume Evidence Verification Callout */}
                {item.verification_method === 'RESUME_EVIDENCE' && item.notes && (
                  <div className="text-xs text-emerald-300 bg-emerald-950/40 p-2.5 rounded-lg border border-emerald-800/50 mb-3 flex items-start gap-2 shadow-sm">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{item.notes}</span>
                  </div>
                )}

                {/* Prerequisites Explanation */}
                {item.prerequisites_summary && (
                  <p className="text-xs text-slate-400 mb-3 bg-slate-900/60 p-2 rounded border border-slate-800/80">
                    <span className="text-slate-300 font-medium">Context: </span>
                    {item.prerequisites_summary}
                  </p>
                )}

                {/* Resource Info */}
                {item.resource ? (
                  <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 mb-4 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400 font-medium">{item.resource.provider}</span>
                      <div className="flex items-center gap-1.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getDifficultyBadge(item.resource.difficulty_level)}`}>
                          {item.resource.difficulty_level}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {item.resource.cost_type}
                        </span>
                      </div>
                    </div>

                    <a
                      href={item.resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 transition group"
                    >
                      <span className="line-clamp-1 group-hover:underline">{item.resource.title}</span>
                      <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                    </a>

                    {item.resource.description && (
                      <p className="text-xs text-slate-400 line-clamp-2">
                        {item.resource.description}
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 italic mb-4">
                    Official technical documentation recommended for {item.skill_name}.
                  </div>
                )}
              </div>

              {/* Status Action Dropdown/Buttons */}
              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {item.estimated_hours}h estimated
                </span>

                <div className="flex items-center gap-1.5">
                  {item.status !== 'IN_PROGRESS' && item.status !== 'COMPLETED' && (
                    <button
                      onClick={() => onUpdateItemStatus(item.id, 'IN_PROGRESS')}
                      disabled={isUpdating}
                      className="px-2.5 py-1 text-xs font-semibold rounded bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 border border-blue-500/30 transition disabled:opacity-50"
                    >
                      Start
                    </button>
                  )}
                  {item.status !== 'COMPLETED' && (
                    <button
                      onClick={() => onUpdateItemStatus(item.id, 'COMPLETED')}
                      disabled={isUpdating}
                      className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-500 text-white shadow transition disabled:opacity-50 flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Mark Done
                    </button>
                  )}
                  {item.status === 'COMPLETED' && (
                    <button
                      onClick={() => onUpdateItemStatus(item.id, 'IN_PROGRESS')}
                      disabled={isUpdating}
                      className="px-2.5 py-1 text-xs font-semibold rounded bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700 transition"
                    >
                      Revisit
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
