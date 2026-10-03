import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Target,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Info,
  ShieldCheck,
  RotateCw,
  Award,
  Zap,
} from 'lucide-react';
import type {
  STARComponentDetail,
} from '../../types/resume';
import { getSTARGuidance } from '../../services/resumeService';

interface STARGuidanceViewProps {
  resumeId: string;
}

export function getSTARQualityBand(score: number): {
  label: 'Exemplary' | 'Proficient' | 'Developing' | 'Incomplete';
  color: string;
  badgeBg: string;
  badgeBorder: string;
} {
  if (score >= 85) {
    return {
      label: 'Exemplary',
      color: 'text-emerald-700',
      badgeBg: 'bg-emerald-50',
      badgeBorder: 'border-emerald-200',
    };
  }
  if (score >= 65) {
    return {
      label: 'Proficient',
      color: 'text-blue-700',
      badgeBg: 'bg-blue-50',
      badgeBorder: 'border-blue-200',
    };
  }
  if (score >= 35) {
    return {
      label: 'Developing',
      color: 'text-amber-700',
      badgeBg: 'bg-amber-50',
      badgeBorder: 'border-amber-200',
    };
  }
  return {
    label: 'Incomplete',
    color: 'text-rose-700',
    badgeBg: 'bg-rose-50',
    badgeBorder: 'border-rose-200',
  };
}

export const STARGuidanceView: React.FC<STARGuidanceViewProps> = ({ resumeId }) => {
  const {
    data,
    isLoading: loading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['resume-star-guidance', resumeId],
    queryFn: () => getSTARGuidance(resumeId),
    enabled: Boolean(resumeId),
  });

  const [expandedBullets, setExpandedBullets] = useState<Record<string, boolean>>({});

  const toggleExpand = (bulletId: string) => {
    setExpandedBullets((prev) => ({
      ...prev,
      [bulletId]: !prev[bulletId],
    }));
  };

  let errorMessage: string | null = null;
  if (isError && error) {
    const status = (error as any)?.response?.status;
    if (status === 401) {
      errorMessage = 'Authentication session expired. Please sign in again.';
    } else if (status === 404) {
      errorMessage = 'Resume record not found or access denied.';
    } else {
      errorMessage = 'Failed to compute STAR quality guidance. Please try again.';
    }
  }

  // Loading State
  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-10 text-center shadow-sm space-y-4">
        <div className="inline-flex items-center justify-center p-3 bg-blue-50 text-blue-600 rounded-2xl animate-spin">
          <RotateCw className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-800">Evaluating Resume Achievement Bullets</h3>
          <p className="text-xs text-slate-500">
            Running deterministic rule-based STAR analysis across experience and projects...
          </p>
        </div>
      </div>
    );
  }

  // Error State
  if (isError) {
    return (
      <div className="bg-white border border-rose-200 rounded-2xl p-8 text-center shadow-sm space-y-4">
        <div className="inline-flex items-center justify-center p-3 bg-rose-50 text-rose-600 rounded-2xl">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div className="space-y-1 max-w-md mx-auto">
          <h3 className="text-base font-bold text-slate-800">Unable to Load STAR Guidance</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            {errorMessage || 'An error occurred while evaluating the resume.'}
          </p>
        </div>
        <div>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center space-x-2 text-xs font-semibold px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Retry Analysis</span>
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { summary, bullets, methodology } = data;
  const overallBand = getSTARQualityBand(summary.overall_completeness_percentage);

  // Empty State (Zero bullets detected)
  if (summary.total_bullets_analyzed === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-10 text-center shadow-sm space-y-4">
        <div className="inline-flex items-center justify-center p-3 bg-slate-100 text-slate-500 rounded-2xl">
          <Info className="w-6 h-6" />
        </div>
        <div className="space-y-1 max-w-lg mx-auto">
          <h3 className="text-base font-bold text-slate-800">No Achievement Bullets Available</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            No achievement statements or bullets were identified in the Experience or Project sections of this resume.
            Add detailed achievement bullets to your experience entries to receive STAR structural guidance.
          </p>
        </div>
        <div className="text-[11px] text-slate-400 font-mono">
          Methodology: {methodology}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Methodology & Context Disclaimer */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full">
              Phase 8.3 Quality Framework
            </span>
            <span className="text-xs text-slate-400">&bull;</span>
            <span className="text-xs text-slate-500 font-mono">Version {data.resume_version}</span>
          </div>
          <h3 className="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight">
            STAR Resume Guidance
          </h3>
          <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">
            Deterministic rule-based structural quality analysis evaluating achievement bullets across the{' '}
            <strong className="text-slate-800">Situation</strong>, <strong className="text-slate-800">Task</strong>,{' '}
            <strong className="text-slate-800">Action</strong>, and <strong className="text-slate-800">Result</strong> competencies.
          </p>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-right shrink-0">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Methodology</span>
          <span className="text-xs font-semibold text-slate-700 block">{methodology}</span>
          <span className="text-[10px] text-slate-400 block">Zero generative LLMs &bull; Rule-based</span>
        </div>
      </div>

      {/* Summary Score & Coverage Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Overall Score Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-2 flex flex-col justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
              Overall Completeness
            </span>
            <div className="flex items-baseline space-x-2 mt-1">
              <span className="text-3xl font-black text-slate-900 tracking-tight">
                {summary.overall_completeness_percentage}%
              </span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded-md border ${overallBand.badgeBg} ${overallBand.color} ${overallBand.badgeBorder}`}
              >
                {overallBand.label}
              </span>
            </div>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                summary.overall_completeness_percentage >= 85
                  ? 'bg-emerald-500'
                  : summary.overall_completeness_percentage >= 65
                  ? 'bg-blue-500'
                  : summary.overall_completeness_percentage >= 35
                  ? 'bg-amber-500'
                  : 'bg-rose-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, summary.overall_completeness_percentage))}%` }}
            />
          </div>
          <span className="text-[10px] text-slate-400 block">Project-defined heuristic quality band</span>
        </div>

        {/* Bullets Count Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Analyzed Statements
          </span>
          <div className="flex items-center space-x-3 mt-1">
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
              <Target className="w-5 h-5" />
            </div>
            <div>
              <span className="text-2xl font-black text-slate-900">{summary.total_bullets_analyzed}</span>
              <span className="text-xs text-slate-500 block">Experience & Project Bullets</span>
            </div>
          </div>
        </div>

        {/* Strong Bullets Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Strong Bullets
          </span>
          <div className="flex items-center space-x-3 mt-1">
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-baseline space-x-1">
                <span className="text-2xl font-black text-emerald-700">{summary.strong_bullets_count}</span>
                <span className="text-xs text-slate-400">/ {summary.total_bullets_analyzed}</span>
              </div>
              <span className="text-xs text-slate-500 block">Action + Result &bull; Score &ge; 65%</span>
            </div>
          </div>
        </div>

        {/* Needs Improvement Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Needs Improvement
          </span>
          <div className="flex items-center space-x-3 mt-1">
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <span className="text-2xl font-black text-amber-700">{summary.needs_improvement_count}</span>
              <span className="text-xs text-slate-500 block">Missing Action or Result</span>
            </div>
          </div>
        </div>
      </div>

      {/* Component Coverage Breakdown Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-blue-600" />
          <span>Competency Pillar Coverage</span>
        </h4>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          {/* Situation */}
          <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-bold">Situation (15%)</span>
              <span className="font-semibold text-slate-900">
                {summary.bullets_with_situation} / {summary.total_bullets_analyzed}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-indigo-600 h-full rounded-full"
                style={{
                  width: `${
                    summary.total_bullets_analyzed > 0
                      ? (summary.bullets_with_situation / summary.total_bullets_analyzed) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
            <span className="text-[10px] text-slate-400 block truncate">Operational scale & context</span>
          </div>

          {/* Task */}
          <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-bold">Task (20%)</span>
              <span className="font-semibold text-slate-900">
                {summary.bullets_with_task} / {summary.total_bullets_analyzed}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-sky-600 h-full rounded-full"
                style={{
                  width: `${
                    summary.total_bullets_analyzed > 0
                      ? (summary.bullets_with_task / summary.total_bullets_analyzed) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
            <span className="text-[10px] text-slate-400 block truncate">Objectives & assignments</span>
          </div>

          {/* Action */}
          <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-bold">Action (30%)</span>
              <span className="font-semibold text-slate-900">
                {summary.bullets_with_action} / {summary.total_bullets_analyzed}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-emerald-600 h-full rounded-full"
                style={{
                  width: `${
                    summary.total_bullets_analyzed > 0
                      ? (summary.bullets_with_action / summary.total_bullets_analyzed) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
            <span className="text-[10px] text-slate-400 block truncate">Active technical verbs</span>
          </div>

          {/* Result */}
          <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
            <div className="flex items-center justify-between text-slate-600">
              <span className="font-bold">Result (35%)</span>
              <span className="font-semibold text-slate-900">
                {summary.bullets_with_result} / {summary.total_bullets_analyzed}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-purple-600 h-full rounded-full"
                style={{
                  width: `${
                    summary.total_bullets_analyzed > 0
                      ? (summary.bullets_with_result / summary.total_bullets_analyzed) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
            <span className="text-[10px] text-slate-400 block truncate">Measurable metrics & impact</span>
          </div>
        </div>
      </div>

      {/* Per-Bullet Detailed Evaluations */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-900">
            Achievement Bullet Evaluations ({bullets.length})
          </h4>
          <span className="text-xs text-slate-500">Sorted by document appearance</span>
        </div>

        <div className="space-y-4">
          {bullets.map((bullet) => {
            const isExpanded = !!expandedBullets[bullet.bullet_id];
            const band = getSTARQualityBand(bullet.completeness_score);

            return (
              <div
                key={bullet.bullet_id}
                className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 transition hover:border-slate-300"
              >
                {/* Bullet Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                      {bullet.section_type}
                    </span>
                    <span className="text-xs text-slate-400">&bull;</span>
                    <span className="text-xs font-semibold text-slate-800">{bullet.parent_entry_title}</span>
                  </div>

                  <div className="flex items-center space-x-2 self-start sm:self-auto">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-md border ${band.badgeBg} ${band.color} ${band.badgeBorder}`}
                    >
                      {band.label} ({bullet.completeness_score}%)
                    </span>
                  </div>
                </div>

                {/* Original Bullet Statement */}
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100 text-xs font-medium text-slate-800 leading-relaxed">
                  <p>&ldquo;{bullet.raw_text}&rdquo;</p>
                </div>

                {/* STAR Pillars Quick Badges */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <ComponentBadge pillar="S" name="Situation" detail={bullet.situation} weight="15%" />
                  <ComponentBadge pillar="T" name="Task" detail={bullet.task} weight="20%" />
                  <ComponentBadge pillar="A" name="Action" detail={bullet.action} weight="30%" />
                  <ComponentBadge pillar="R" name="Result" detail={bullet.result} weight="35%" />
                </div>

                {/* Actionable Improvement Guidance */}
                {bullet.improvement_guidance.length > 0 && (
                  <div className="p-3.5 bg-blue-50/60 border border-blue-100 rounded-xl space-y-1.5 text-xs text-blue-900">
                    <div className="flex items-center space-x-1.5 font-bold text-blue-800 text-[11px] uppercase tracking-wider">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                      <span>Actionable Structural Guidance</span>
                    </div>
                    <ul className="space-y-1 text-slate-700 pl-4 list-disc text-xs">
                      {bullet.improvement_guidance.map((guide, gIdx) => (
                        <li key={gIdx} className="leading-relaxed">
                          {guide}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Expandable Evidence Details */}
                <div>
                  <button
                    onClick={() => toggleExpand(bullet.bullet_id)}
                    className="inline-flex items-center space-x-1 text-xs font-semibold text-slate-600 hover:text-slate-900 py-1 transition"
                  >
                    <span>{isExpanded ? 'Hide Structural Evidence' : 'Inspect Evidence & Signals'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <PillarDetailCard label="Situation Evidence" detail={bullet.situation} />
                      <PillarDetailCard label="Task Evidence" detail={bullet.task} />
                      <PillarDetailCard label="Action Evidence" detail={bullet.action} />
                      <PillarDetailCard label="Result Evidence" detail={bullet.result} />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

interface ComponentBadgeProps {
  pillar: string;
  name: string;
  detail: STARComponentDetail;
  weight: string;
}

const ComponentBadge: React.FC<ComponentBadgeProps> = ({ pillar, name, detail, weight }) => {
  return (
    <div
      className={`p-2.5 rounded-lg border flex items-center justify-between ${
        detail.detected
          ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800'
          : 'bg-slate-50 border-slate-200 text-slate-600'
      }`}
    >
      <div className="flex items-center space-x-2">
        <span
          className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
            detail.detected ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-700'
          }`}
        >
          {pillar}
        </span>
        <span className="font-semibold text-xs">{name}</span>
      </div>
      <div className="flex items-center space-x-1">
        <span className="text-[10px] text-slate-400 font-mono">{weight}</span>
        {detail.detected ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
        ) : (
          <HelpCircle className="w-4 h-4 text-slate-300 shrink-0" />
        )}
      </div>
    </div>
  );
};

interface PillarDetailCardProps {
  label: string;
  detail: STARComponentDetail;
}

const PillarDetailCard: React.FC<PillarDetailCardProps> = ({ label, detail }) => {
  return (
    <div className="p-3 bg-slate-50/80 border border-slate-100 rounded-lg space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="font-bold text-slate-700 text-[11px] uppercase tracking-wider">{label}</span>
        <span
          className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
            detail.detected ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'
          }`}
        >
          {detail.detected ? 'Detected' : 'Not Detected'}
        </span>
      </div>

      <p className="text-slate-600 text-xs leading-relaxed">{detail.explanation}</p>

      {detail.evidence_text && (
        <div className="text-[11px] text-slate-700 bg-white border border-slate-200 px-2 py-1 rounded font-mono">
          <span className="text-slate-400 select-none">Evidence: </span>&ldquo;{detail.evidence_text}&rdquo;
        </div>
      )}

      {detail.signals_detected && detail.signals_detected.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-0.5">
          {detail.signals_detected.map((sig, sIdx) => (
            <span
              key={sIdx}
              className="text-[10px] font-mono bg-blue-50 border border-blue-200 text-blue-700 px-1.5 py-0.5 rounded"
            >
              {sig}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
