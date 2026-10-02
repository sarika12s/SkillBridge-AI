import React, { useState, useEffect } from 'react';
import { versionService } from '../services/versionService';
import type {
  ResumeVersionSummary,
  ResumeVersionComparison,
  SkillEvidenceChange,
} from '../types/dashboard';
import { EvidenceInspectionModal } from '../components/dashboard/EvidenceInspectionModal';
import {
  GitCompare,
  RotateCw,
  AlertCircle,
  CheckCircle,
  PlusCircle,
  MinusCircle,
  ArrowRight,
  TrendingUp,
  Sparkles,
  ShieldAlert,
} from 'lucide-react';

export const ResumeVersions: React.FC = () => {
  const [versions, setVersions] = useState<ResumeVersionSummary[]>([]);
  const [selectedV1, setSelectedV1] = useState<string>('');
  const [selectedV2, setSelectedV2] = useState<string>('');
  const [comparison, setComparison] = useState<ResumeVersionComparison | null>(null);

  const [loadingVersions, setLoadingVersions] = useState<boolean>(true);
  const [comparing, setComparing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [showEvidenceModal, setShowEvidenceModal] = useState<boolean>(false);

  useEffect(() => {
    fetchVersions();
  }, []);

  const fetchVersions = async () => {
    setLoadingVersions(true);
    setError(null);
    try {
      const data = await versionService.listVersions();
      setVersions(data);
      if (data.length >= 2) {
        setSelectedV1(data[data.length - 2].id);
        setSelectedV2(data[data.length - 1].id);
      } else if (data.length === 1) {
        setSelectedV1(data[0].id);
        setSelectedV2(data[0].id);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch resume versions.');
    } finally {
      setLoadingVersions(false);
    }
  };

  const handleCompare = async () => {
    if (!selectedV1 || !selectedV2) {
      setError('Please select two resume versions to compare.');
      return;
    }
    if (selectedV1 === selectedV2) {
      setError('Please select two different resume versions for comparison.');
      return;
    }

    setComparing(true);
    setError(null);
    try {
      const result = await versionService.compareVersions(selectedV1, selectedV2);
      setComparison(result);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Comparison failed between selected versions.');
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
            <GitCompare className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Resume Version Management</h1>
            <p className="text-sm text-slate-400">
              Audit skills, section content modifications, and analyze score deltas with comparability guards
            </p>
          </div>
        </div>
        <button
          onClick={fetchVersions}
          disabled={loadingVersions}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors disabled:opacity-50 self-start md:self-auto"
          title="Refresh versions"
        >
          <RotateCw className={`w-4 h-4 ${loadingVersions ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Version Selector Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <h2 className="text-base font-semibold text-white">Select Iterations to Compare</h2>

        {loadingVersions ? (
          <div className="py-6 text-center text-xs text-slate-500">Loading resume iterations...</div>
        ) : versions.length < 2 ? (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs">
            At least two resume uploads are required to compare iterations. You currently have {versions.length} uploaded version.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2">Base Version (v1)</label>
              <select
                value={selectedV1}
                onChange={(e) => setSelectedV1(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                {versions.map((v) => (
                  <option key={v.id} value={v.id}>
                    v{v.version} — {v.title} ({new Date(v.created_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2">Updated Version (v2)</label>
              <select
                value={selectedV2}
                onChange={(e) => setSelectedV2(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                {versions.map((v) => (
                  <option key={v.id} value={v.id}>
                    v{v.version} — {v.title} ({new Date(v.created_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <button
                onClick={handleCompare}
                disabled={comparing || selectedV1 === selectedV2}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all disabled:opacity-50 shadow-md shadow-indigo-600/20"
              >
                {comparing ? (
                  <RotateCw className="w-4 h-4 animate-spin" />
                ) : (
                  <GitCompare className="w-4 h-4" />
                )}
                Run Iteration Diff
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Score Comparability Guard & Deltas */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              Score Evolution & Comparability Guard
            </h3>

            {/* Comparability Guard Warning / Note */}
            <div
              className={`p-4 rounded-xl border text-xs flex items-start gap-3 ${
                comparison.is_same_job_comparison
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              }`}
            >
              {comparison.is_same_job_comparison ? (
                <CheckCircle className="w-5 h-5 shrink-0 text-emerald-400 mt-0.5" />
              ) : (
                <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
              )}
              <div>
                <p className="font-semibold">{comparison.comparability_notes}</p>
                {!comparison.is_same_job_comparison && (
                  <p className="text-[11px] text-amber-400/80 mt-1">
                    Quality Gate: Direct role compatibility delta is suppressed when target job profiles differ to ensure scientific integrity.
                  </p>
                )}
              </div>
            </div>

            {/* Score Delta Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {/* ATS Delta */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400">ATS Readiness Delta</span>
                <div className="flex items-baseline gap-3 mt-1">
                  <span className="text-2xl font-bold text-white">
                    {comparison.ats_score_v2 !== null ? `${comparison.ats_score_v2}%` : 'N/A'}
                  </span>
                  {typeof comparison.ats_score_delta === 'number' && (
                    <span
                      className={`text-xs font-bold ${
                        comparison.ats_score_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {comparison.ats_score_delta >= 0 ? `+${comparison.ats_score_delta}%` : `${comparison.ats_score_delta}%`}
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  v{comparison.resume_v1_version} ({comparison.ats_score_v1 ?? 'N/A'}%) → v{comparison.resume_v2_version} ({comparison.ats_score_v2 ?? 'N/A'}%)
                </p>
              </div>

              {/* Job Compatibility Delta */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400">Role Compatibility Delta</span>
                <div className="flex items-baseline gap-3 mt-1">
                  <span className="text-2xl font-bold text-white">
                    {comparison.job_compatibility_v2 !== null ? `${comparison.job_compatibility_v2}%` : 'N/A'}
                  </span>
                  {typeof comparison.job_compatibility_delta === 'number' ? (
                    <span
                      className={`text-xs font-bold ${
                        comparison.job_compatibility_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {comparison.job_compatibility_delta >= 0 ? `+${comparison.job_compatibility_delta}%` : `${comparison.job_compatibility_delta}%`}
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-500 italic">Target role changed</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Target: {comparison.target_job_title || 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Skill Diffs: New, Retained, Removed */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Added Skills */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white flex items-center gap-1.5">
                  <PlusCircle className="w-4 h-4 text-emerald-400" />
                  New Skills Added ({comparison.new_skills.length})
                </h4>
              </div>
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {comparison.new_skills.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No new skills added.</p>
                ) : (
                  comparison.new_skills.map((sk: string) => (
                    <div
                      key={sk}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 font-medium"
                    >
                      + {sk}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Retained Skills */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-blue-400" />
                  Retained Skills ({comparison.retained_skills.length})
                </h4>
              </div>
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {comparison.retained_skills.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No common skills.</p>
                ) : (
                  comparison.retained_skills.map((sk: string) => (
                    <div
                      key={sk}
                      className="px-3 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs text-slate-300"
                    >
                      {sk}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Removed Skills */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white flex items-center gap-1.5">
                  <MinusCircle className="w-4 h-4 text-rose-400" />
                  Removed Skills ({comparison.removed_skills.length})
                </h4>
              </div>
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {comparison.removed_skills.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No skills removed.</p>
                ) : (
                  comparison.removed_skills.map((sk: string) => (
                    <div
                      key={sk}
                      className="px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 font-medium"
                    >
                      - {sk}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Evidence Changes & Section Diff */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  Skill Evidence Upgrades ({comparison.skill_evidence_changes.length})
                </h3>
                <p className="text-xs text-slate-400">
                  Skills elevated from passive listings to active projects or experience sections
                </p>
              </div>
              {comparison.skill_evidence_changes.length > 0 && (
                <button
                  onClick={() => setShowEvidenceModal(true)}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition-colors"
                >
                  View Full Evidence Modal
                </button>
              )}
            </div>

            <div className="space-y-3 pt-2">
              {comparison.skill_evidence_changes.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No evidence shifts detected between these versions.</p>
              ) : (
                comparison.skill_evidence_changes.map((item: SkillEvidenceChange, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{item.skill_name}</span>
                        {item.strengthened && (
                          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            Strengthened
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-slate-400">
                        <span className="font-mono text-[11px]">{item.previous_section}</span>
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                        <span className="font-mono text-[11px] text-indigo-300 font-semibold">{item.new_section}</span>
                      </div>
                    </div>

                    {item.new_evidence && (
                      <p className="text-slate-300 italic text-[11px] max-w-md truncate">
                        "{item.new_evidence}"
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Evidence Inspection Modal */}
      {comparison && (
        <EvidenceInspectionModal
          isOpen={showEvidenceModal}
          onClose={() => setShowEvidenceModal(false)}
          changes={comparison.skill_evidence_changes}
        />
      )}
    </div>
  );
};
