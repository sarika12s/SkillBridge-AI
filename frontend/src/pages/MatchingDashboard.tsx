import React, { useState, useEffect } from 'react';
import { listResumes } from '../services/resumeService';
import { listJobs } from '../services/jobService';
import { analyzeResumeJobMatch } from '../services/matchingService';
import type { ResumeSummary } from '../types/resume';
import type { JobSummary } from '../types/job';
import type { MatchAnalysisResponse } from '../types/matching';
import { ScoreCards } from '../components/matching/ScoreCards';
import { StructuredAlignmentCard } from '../components/matching/StructuredAlignmentCard';
import { SkillComparisonTable } from '../components/matching/SkillComparisonTable';
import { ExplainabilityBreakdown } from '../components/matching/ExplainabilityBreakdown';
import {
  GitCompare,
  FileText,
  Briefcase,
  Play,
  RotateCw,
  AlertCircle,
} from 'lucide-react';

export const MatchingDashboard: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [analysis, setAnalysis] = useState<MatchAnalysisResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [fetchingData, setFetchingData] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setFetchingData(true);
    setError(null);
    try {
      const [resumesData, jobsData] = await Promise.all([listResumes(), listJobs()]);
      setResumes(resumesData);
      setJobs(jobsData);

      if (resumesData.length > 0) setSelectedResumeId(resumesData[0].id);
      if (jobsData.length > 0) setSelectedJobId(jobsData[0].id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch candidate resumes or jobs.');
    } finally {
      setFetchingData(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedResumeId || !selectedJobId) {
      setError('Please select both a candidate resume and a target job description.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await analyzeResumeJobMatch(selectedResumeId, selectedJobId);
      setAnalysis(result);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || 'Failed to complete resume-to-job matching analysis.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Phase 5: Matching & Scoring Engine
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <GitCompare className="w-7 h-7 text-indigo-400" />
            Resume ↔ Job Matching & Skill Gap Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Execute hybrid skill matching (exact canonical, alias, ontology, dense embeddings),
            inspect granular required vs. preferred skill gaps, and examine explainable score breakdowns.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={fetchingData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700/60 border border-slate-700 transition-colors"
        >
          <RotateCw className={`w-3.5 h-3.5 ${fetchingData ? 'animate-spin' : ''}`} />
          Refresh Data
        </button>
      </div>

      {/* Selectors & Execution Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Resume Selection */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-cyan-400" />
              1. Select Candidate Resume
            </label>
            {resumes.length === 0 ? (
              <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-700/50 text-xs text-slate-400 italic">
                No resumes uploaded yet. Please upload a resume in the Resume Parser tab.
              </div>
            ) : (
              <select
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title || r.file_name} ({r.file_type.toUpperCase()})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Job Selection */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Briefcase className="w-4 h-4 text-purple-400" />
              2. Select Target Job Description
            </label>
            {jobs.length === 0 ? (
              <div className="p-3 bg-slate-800/40 rounded-xl border border-slate-700/50 text-xs text-slate-400 italic">
                No job descriptions ingested yet. Please add a job in the Job Descriptions tab.
              </div>
            ) : (
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} {j.company ? `— ${j.company}` : ''} ({j.normalized_role})
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
          <div className="text-xs text-slate-400">
            {resumes.length > 0 && jobs.length > 0
              ? 'Ready to execute explainable hybrid matching analysis.'
              : 'Add at least one resume and one job description to begin.'}
          </div>
          <button
            onClick={handleRunAnalysis}
            disabled={loading || !selectedResumeId || !selectedJobId}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <>
                <RotateCw className="w-4 h-4 animate-spin" />
                Analyzing Signals & Computing Scores...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Run Matching & Gap Analysis
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Analysis Results Display */}
      {analysis && (
        <div className="space-y-8 animate-fadeIn">
          {/* Dual Score Cards & Breakdown */}
          <ScoreCards
            compatibilityScore={analysis.compatibility_score}
            atsReadinessScore={analysis.ats_readiness_score}
            breakdowns={analysis.score_breakdowns}
          />

          {/* Structured Entity Alignment (Experience, Education, Certifications) */}
          <StructuredAlignmentCard alignment={analysis.alignment} />

          {/* Granular Skill Comparison Table with Filters */}
          <SkillComparisonTable matches={analysis.skill_matches} />

          {/* Dedicated Explainability Breakdown */}
          <ExplainabilityBreakdown
            explainability={analysis.explainability}
            summaryExplanation={analysis.summary_explanation}
          />
        </div>
      )}
    </div>
  );
};
