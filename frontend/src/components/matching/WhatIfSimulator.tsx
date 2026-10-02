import React, { useState } from 'react';
import type { SkillMatch, SimulationResponse } from '../../types/matching';
import { simulateMatch } from '../../services/matchingService';
import {
  Sliders,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Zap,
  Info,
  ShieldCheck,
} from 'lucide-react';

interface WhatIfSimulatorProps {
  analysisId: string;
  matches: SkillMatch[];
}

export const WhatIfSimulator: React.FC<WhatIfSimulatorProps> = ({
  analysisId,
  matches,
}) => {
  // Extract unique gap skills eligible for simulation
  const gapStatuses = [
    'MISSING_REQUIRED',
    'MISSING_PREFERRED',
    'PARTIAL_REQUIRED',
    'PARTIAL_PREFERRED',
    'RELATED_SUPPORT',
  ];

  // Map to distinct eligible skills with an ID
  const eligibleGaps = React.useMemo(() => {
    const seen = new Set<string>();
    const list: SkillMatch[] = [];

    matches.forEach((m) => {
      if (gapStatuses.includes(m.match_status) && m.canonical_skill_id) {
        if (!seen.has(m.canonical_skill_id)) {
          seen.add(m.canonical_skill_id);
          list.push(m);
        }
      }
    });

    // Sort: REQUIRED first, then PREFERRED
    return list.sort((a, b) => {
      if (a.priority === 'REQUIRED' && b.priority !== 'REQUIRED') return -1;
      if (a.priority !== 'REQUIRED' && b.priority === 'REQUIRED') return 1;
      return a.canonical_skill_name.localeCompare(b.canonical_skill_name);
    });
  }, [matches]);

  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const toggleSkill = (skillId: string) => {
    setSelectedSkillIds((prev) =>
      prev.includes(skillId) ? prev.filter((id) => id !== skillId) : [...prev, skillId]
    );
  };

  const handleSelectAllRequired = () => {
    const reqIds = eligibleGaps
      .filter((g) => g.priority === 'REQUIRED' && g.canonical_skill_id)
      .map((g) => g.canonical_skill_id!);
    setSelectedSkillIds(reqIds);
  };

  const handleSelectAll = () => {
    const allIds = eligibleGaps
      .map((g) => g.canonical_skill_id!)
      .filter(Boolean);
    setSelectedSkillIds(allIds);
  };

  const handleClearSelection = () => {
    setSelectedSkillIds([]);
    setSimulationResult(null);
    setError(null);
  };

  const handleRunSimulation = async () => {
    if (selectedSkillIds.length === 0) {
      setError('Please select at least one skill gap to simulate.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await simulateMatch({
        match_analysis_id: analysisId,
        simulated_skill_ids: selectedSkillIds,
      });
      setSimulationResult(result);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || 'Failed to execute counterfactual simulation.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (eligibleGaps.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 text-center space-y-2">
        <div className="inline-flex p-3 rounded-xl bg-emerald-500/10 text-emerald-400 mb-1">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-white">Full Skill Alignment Achieved</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          No missing or partial skill gaps were detected for this job match. The candidate profile already meets all required and preferred competencies!
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/20 flex items-center gap-1">
              <Zap className="w-3 h-3" />
              Phase 8.1: What-If Gap-Closure Simulator
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-violet-400" />
            Interactive Counterfactual Simulator
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Simulate acquiring missing competencies to project score improvements, coverage gains, and learning-hour ROI.
            Calculations are completely stateless and do not alter your profile.
          </p>
        </div>

        {/* Quick Selection Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleSelectAllRequired}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 transition-colors"
          >
            Select All Required
          </button>
          <button
            onClick={handleSelectAll}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            Select All ({eligibleGaps.length})
          </button>
          {selectedSkillIds.length > 0 && (
            <button
              onClick={handleClearSelection}
              className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Skill Gap Selection Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>
            Select eligible skill gaps to simulate ({selectedSkillIds.length} of {eligibleGaps.length} selected):
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-72 overflow-y-auto pr-1">
          {eligibleGaps.map((gap) => {
            const isSelected = selectedSkillIds.includes(gap.canonical_skill_id!);
            const isRequired = gap.priority === 'REQUIRED';

            return (
              <label
                key={gap.canonical_skill_id}
                className={`relative flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-violet-950/30 border-violet-500/50 shadow-md shadow-violet-950/20'
                    : 'bg-slate-800/40 border-slate-700/60 hover:bg-slate-800/70 hover:border-slate-600'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSkill(gap.canonical_skill_id!)}
                  className="mt-0.5 w-4 h-4 rounded border-slate-600 text-violet-600 focus:ring-violet-500 focus:ring-offset-slate-900"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1.5 mb-1">
                    <span className="text-xs font-semibold text-white truncate">
                      {gap.canonical_skill_name}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded border shrink-0 ${
                        isRequired
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                          : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
                      }`}
                    >
                      {gap.priority}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {gap.explanation}
                  </p>
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
        <span className="text-xs text-slate-400">
          {selectedSkillIds.length === 0
            ? 'Select at least one skill gap above to run simulation.'
            : `Ready to simulate acquisition of ${selectedSkillIds.length} competency${
                selectedSkillIds.length > 1 ? 'ies' : ''
              }.`}
        </span>

        <button
          onClick={handleRunSimulation}
          disabled={loading || selectedSkillIds.length === 0}
          className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-lg shadow-violet-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {loading ? (
            <>
              <RotateCcw className="w-3.5 h-3.5 animate-spin" />
              Computing Projections...
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5 fill-current" />
              Run What-If Simulation
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Simulation Results Display */}
      {simulationResult && (
        <div className="space-y-6 pt-4 border-t border-slate-800 animate-fadeIn">
          {/* Section Subtitle */}
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              Projected Simulation Results
            </h3>
            <span className="text-[11px] text-slate-400 flex items-center gap-1">
              <Info className="w-3.5 h-3.5 text-slate-500" />
              Hypothetical state (Zero DB Persistence)
            </span>
          </div>

          {/* 4 Score Metric Comparison Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Job Compatibility Score */}
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <span className="text-xs text-slate-400 font-medium">Job Compatibility</span>
              <div className="flex items-baseline justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-sm line-through">
                    {simulationResult.current_compatibility_score.toFixed(1)}%
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-xl font-bold text-white">
                    {simulationResult.projected_compatibility_score.toFixed(1)}%
                  </span>
                </div>
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    simulationResult.compatibility_score_delta >= 0
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {simulationResult.compatibility_score_delta >= 0 ? '+' : ''}
                  {simulationResult.compatibility_score_delta.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* ATS Readiness Score */}
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <span className="text-xs text-slate-400 font-medium">ATS Readiness</span>
              <div className="flex items-baseline justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-sm line-through">
                    {simulationResult.current_ats_score.toFixed(1)}%
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-xl font-bold text-white">
                    {simulationResult.projected_ats_score.toFixed(1)}%
                  </span>
                </div>
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    simulationResult.ats_score_delta >= 0
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {simulationResult.ats_score_delta >= 0 ? '+' : ''}
                  {simulationResult.ats_score_delta.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Required Skill Coverage */}
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <span className="text-xs text-slate-400 font-medium">Required Skill Coverage</span>
              <div className="flex items-baseline justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-sm line-through">
                    {simulationResult.current_required_coverage.toFixed(1)}%
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-xl font-bold text-white">
                    {simulationResult.projected_required_coverage.toFixed(1)}%
                  </span>
                </div>
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    simulationResult.required_coverage_delta >= 0
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {simulationResult.required_coverage_delta >= 0 ? '+' : ''}
                  {simulationResult.required_coverage_delta.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Preferred Skill Coverage */}
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <span className="text-xs text-slate-400 font-medium">Preferred Skill Coverage</span>
              <div className="flex items-baseline justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 text-sm line-through">
                    {simulationResult.current_preferred_coverage.toFixed(1)}%
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-xl font-bold text-white">
                    {simulationResult.projected_preferred_coverage.toFixed(1)}%
                  </span>
                </div>
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    simulationResult.preferred_coverage_delta >= 0
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {simulationResult.preferred_coverage_delta >= 0 ? '+' : ''}
                  {simulationResult.preferred_coverage_delta.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Learning Effort & ROI (if available) */}
          {simulationResult.total_estimated_learning_hours !== null &&
            simulationResult.total_estimated_learning_hours !== undefined && (
              <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-white">
                      Curriculum Learning Effort & Projected ROI
                    </h4>
                    <p className="text-[11px] text-slate-300">
                      Total estimated study effort across available learning resources:
                      <strong className="text-white ml-1">
                        {simulationResult.total_estimated_learning_hours.toFixed(1)} hours
                      </strong>
                    </p>
                  </div>
                </div>

                {simulationResult.learning_hour_roi !== null &&
                  simulationResult.learning_hour_roi !== undefined && (
                    <div className="text-right shrink-0">
                      <span className="text-xs text-slate-400 block">Projected Efficiency</span>
                      <span className="text-base font-extrabold text-emerald-400">
                        +{simulationResult.learning_hour_roi.toFixed(2)} pts / hour
                      </span>
                    </div>
                  )}
              </div>
            )}

          {/* Gap Resolution Analysis */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Closed Gaps */}
            <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50 space-y-2">
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                Gaps Closed by Simulation ({simulationResult.gap_state.closed_gaps.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {simulationResult.gap_state.closed_gaps.map((name) => (
                  <span
                    key={name}
                    className="px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                  >
                    ✓ {name}
                  </span>
                ))}
              </div>
            </div>

            {/* Remaining Gaps */}
            <div className="p-4 rounded-xl bg-slate-800/30 border border-slate-700/50 space-y-2">
              <span className="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                Remaining Gaps ({simulationResult.gap_state.total_remaining_gaps})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {simulationResult.gap_state.remaining_required_gaps.map((name) => (
                  <span
                    key={name}
                    className="px-2 py-0.5 rounded-md text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20"
                  >
                    {name} (Req)
                  </span>
                ))}
                {simulationResult.gap_state.remaining_preferred_gaps.map((name) => (
                  <span
                    key={name}
                    className="px-2 py-0.5 rounded-md text-xs font-medium bg-slate-700/50 text-slate-300 border border-slate-600/50"
                  >
                    {name} (Pref)
                  </span>
                ))}
                {simulationResult.gap_state.total_remaining_gaps === 0 && (
                  <span className="text-xs text-slate-400 italic">None — All identified gaps resolved!</span>
                )}
              </div>
            </div>
          </div>

          {/* Deterministic Explanation Narrative */}
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-1">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Simulation Explanation
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">
              {simulationResult.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
