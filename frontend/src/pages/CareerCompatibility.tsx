import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listResumes } from '../services/resumeService';
import { careerService } from '../services/careerService';
import { learningService } from '../services/learningService';
import type { ResumeSummary } from '../types/resume';
import type { CareerRoleMatch, CareerCompatibilityResponse } from '../types/career';
import { CareerRoleCard } from '../components/career/CareerRoleCard';
import { RoleScoreBreakdownModal } from '../components/career/RoleScoreBreakdownModal';
import {
  Compass,
  FileText,
  Play,
  RotateCw,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

export const CareerCompatibility: React.FC = () => {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [compatibilityData, setCompatibilityData] = useState<CareerCompatibilityResponse | null>(null);
  const [selectedRoleForBreakdown, setSelectedRoleForBreakdown] = useState<CareerRoleMatch | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [fetchingResumes, setFetchingResumes] = useState<boolean>(true);
  const [generatingPathRoleId, setGeneratingPathRoleId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    setFetchingResumes(true);
    setError(null);
    try {
      const data = await listResumes();
      setResumes(data);
      if (data.length > 0) {
        setSelectedResumeId(data[0].id);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch candidate resumes.');
    } finally {
      setFetchingResumes(false);
    }
  };

  const handleComputeCompatibility = async () => {
    if (!selectedResumeId) {
      setError('Please select a resume to evaluate career role compatibility.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await careerService.getCareerCompatibility(selectedResumeId);
      setCompatibilityData(res);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || 'Failed to compute career compatibility scores.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateLearningPath = async (role: CareerRoleMatch) => {
    setGeneratingPathRoleId(role.occupation_id);
    setError(null);
    try {
      const newPath = await learningService.createLearningPath({
        resume_id: selectedResumeId,
        target_type: 'CAREER',
        target_occupation_id: role.occupation_id,
      });
      navigate(`/learning-paths/${newPath.id}`);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || 'Failed to generate personalized learning path for this role.'
      );
    } finally {
      setGeneratingPathRoleId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Title & Introduction */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5" />
            Phase 6 — Career Role Intelligence
          </span>
        </div>
        <h1 className="text-3xl font-black text-slate-100 tracking-tight">
          Career Role Compatibility Engine
        </h1>
        <p className="text-slate-400 mt-2 text-sm max-w-3xl leading-relaxed">
          Evaluate your candidate resume against standardized industry career pathways (ESCO & O*NET).
          Discover your highest-fit roles, explore explainable score breakdowns, and instantly generate
          prerequisite-aware personalized learning paths to close qualification gaps.
        </p>
      </div>

      {/* Control Bar: Resume Selection */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="flex-1 max-w-xl">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-indigo-400" />
              Candidate Resume
            </label>
            {fetchingResumes ? (
              <div className="h-10 bg-slate-800 animate-pulse rounded-lg" />
            ) : resumes.length === 0 ? (
              <div className="text-sm text-amber-400 bg-amber-500/10 border border-amber-500/20 p-3 rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>No parsed resumes found. Please upload a resume first.</span>
              </div>
            ) : (
              <select
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-indigo-500"
              >
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title} ({r.file_name})
                  </option>
                ))}
              </select>
            )}
          </div>

          <button
            onClick={handleComputeCompatibility}
            disabled={loading || fetchingResumes || resumes.length === 0}
            className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-sm shadow-lg shadow-indigo-600/20 transition self-stretch md:self-auto"
          >
            {loading ? (
              <>
                <RotateCw className="w-4 h-4 animate-spin" />
                <span>Evaluating Career Roles...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Compute Role Compatibility</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-8 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {compatibilityData && (
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div>
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                Ranked Occupational Fit
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Standardized roles ordered by multi-component analytical compatibility.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-500">
              Engine v{compatibilityData.matching_engine_version}
            </span>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {compatibilityData.roles.map((role) => (
              <CareerRoleCard
                key={role.occupation_id}
                role={role}
                onViewBreakdown={setSelectedRoleForBreakdown}
                onGenerateLearningPath={handleGenerateLearningPath}
                isGeneratingPath={generatingPathRoleId === role.occupation_id}
              />
            ))}
          </div>
        </div>
      )}

      {/* Score Breakdown Modal */}
      <RoleScoreBreakdownModal
        role={selectedRoleForBreakdown}
        onClose={() => setSelectedRoleForBreakdown(null)}
      />
    </div>
  );
};
