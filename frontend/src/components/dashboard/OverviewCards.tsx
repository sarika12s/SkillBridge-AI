import React from 'react';
import type { DashboardOverviewResponse } from '../../types/dashboard';
import {
  FileText,
  Target,
  Award,
  BookOpen,
  Sparkles,
  Clock,
} from 'lucide-react';

interface OverviewCardsProps {
  overview: DashboardOverviewResponse;
}

export const OverviewCards: React.FC<OverviewCardsProps> = ({ overview }) => {
  const getLifecycleStateBadge = (state: string) => {
    switch (state) {
      case 'COMPLETED_LEARNING':
        return { label: 'Roadmap Completed', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
      case 'ACTIVE_LEARNING':
        return { label: 'Active Upskilling', bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30' };
      case 'LEARNING_PATH_CREATED':
        return { label: 'Roadmap Ready', bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' };
      case 'RESUME_ANALYZED':
      case 'JOB_ANALYZED':
        return { label: 'Job Profile Analyzed', bg: 'bg-purple-500/10 text-purple-400 border-purple-500/30' };
      case 'CAREER_ANALYZED':
        return { label: 'Career Matched', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30' };
      case 'RESUME_ONLY':
        return { label: 'Resume Parsed', bg: 'bg-slate-500/10 text-slate-300 border-slate-500/30' };
      default:
        return { label: 'Getting Started', bg: 'bg-slate-700/50 text-slate-400 border-slate-600' };
    }
  };

  const badge = getLifecycleStateBadge(overview.state);

  return (
    <div className="space-y-6">
      {/* State & Insight Highlights */}
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 rounded-xl text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Career Intelligence Overview</h2>
              <p className="text-xs text-slate-400">Deterministic analytical state derived from backend intelligence engines</p>
            </div>
          </div>
          <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${badge.bg}`}>
            {badge.label}
          </span>
        </div>

        {/* Explainable AI Insights Banner */}
        {overview.insights && overview.insights.length > 0 && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            {overview.insights.map((insight, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/60 border border-slate-800/70 text-xs text-slate-300"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                <p className="leading-relaxed">{insight}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Active Resume & Version */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-medium uppercase tracking-wider">Active Resume</span>
            <FileText className="w-4 h-4 text-slate-400" />
          </div>
          {overview.latest_resume ? (
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white tracking-tight">
                  v{overview.latest_resume.version || 1}
                </span>
                <span className="text-xs text-emerald-400 font-medium">
                  {overview.resume_versions_count} total {overview.resume_versions_count === 1 ? 'version' : 'versions'}
                </span>
              </div>
              <p className="text-sm font-medium text-slate-200 truncate mt-1" title={overview.latest_resume.title}>
                {overview.latest_resume.title}
              </p>
              <div className="flex items-center gap-3 text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/60">
                <span>{overview.latest_resume.sections_count} sections</span>
                <span>•</span>
                <span>{overview.latest_resume.page_count} {overview.latest_resume.page_count === 1 ? 'page' : 'pages'}</span>
              </div>
            </div>
          ) : (
            <div className="py-2 text-xs text-slate-500 italic">No resume uploaded yet.</div>
          )}
        </div>

        {/* Card 2: ATS Readiness Score */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-medium uppercase tracking-wider">ATS Readiness</span>
            <Award className="w-4 h-4 text-indigo-400" />
          </div>
          {overview.latest_ats_readiness_score !== null && overview.latest_ats_readiness_score !== undefined ? (
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white tracking-tight">
                  {overview.latest_ats_readiness_score}%
                </span>
                <span className="text-xs text-slate-400">Readiness</span>
              </div>
              {/* Progress track */}
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-3">
                <div
                  className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(overview.latest_ats_readiness_score, 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-400 mt-3 pt-2 border-t border-slate-800/60 truncate">
                Engine: {overview.latest_job_analysis?.scoring_version || '1.0.0-heuristic'}
              </p>
            </div>
          ) : (
            <div className="py-2 text-xs text-slate-500 italic">Analyze a job description to calculate ATS score.</div>
          )}
        </div>

        {/* Card 3: Job Compatibility */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-medium uppercase tracking-wider">Role Compatibility</span>
            <Target className="w-4 h-4 text-emerald-400" />
          </div>
          {overview.latest_job_compatibility_score !== null && overview.latest_job_compatibility_score !== undefined ? (
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white tracking-tight">
                  {overview.latest_job_compatibility_score}%
                </span>
                <span className="text-xs text-emerald-400 font-medium">
                  {overview.required_skill_coverage !== null ? `${overview.required_skill_coverage}% req cov` : ''}
                </span>
              </div>
              <p className="text-sm font-medium text-slate-200 truncate mt-1" title={overview.latest_job_analysis?.job_title}>
                {overview.latest_job_analysis?.job_title || 'Target Role'}
              </p>
              <div className="flex items-center gap-2 text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/60">
                <span className="text-emerald-400 font-medium">{overview.matched_skills_count} matched</span>
                <span>•</span>
                <span className="text-amber-400">{overview.missing_required_skills_count} gaps</span>
              </div>
            </div>
          ) : (
            <div className="py-2 text-xs text-slate-500 italic">Run a role match analysis to measure fit.</div>
          )}
        </div>

        {/* Card 4: Learning Path Progress */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-3">
            <span className="font-medium uppercase tracking-wider">Learning Roadmap</span>
            <BookOpen className="w-4 h-4 text-blue-400" />
          </div>
          {overview.learning_overview && overview.learning_overview.total_items > 0 ? (
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white tracking-tight">
                  {overview.learning_overview.overall_completion_percentage}%
                </span>
                <span className="text-xs text-blue-400 font-medium">
                  {overview.learning_overview.completed_items}/{overview.learning_overview.total_items} modules
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-3">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(overview.learning_overview.overall_completion_percentage, 100)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs text-slate-400 mt-3 pt-2 border-t border-slate-800/60">
                <span>Stage {overview.learning_overview.current_stage}</span>
                <span className="flex items-center gap-1 text-slate-300">
                  <Clock className="w-3 h-3 text-slate-400" />
                  {overview.learning_overview.remaining_estimated_hours}h left
                </span>
              </div>
            </div>
          ) : (
            <div className="py-2 text-xs text-slate-500 italic">Generate a personalized learning path to track progress.</div>
          )}
        </div>
      </div>
    </div>
  );
};
