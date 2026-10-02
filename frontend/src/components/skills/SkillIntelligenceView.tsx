import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  RotateCw, 
  AlertCircle
} from 'lucide-react';
import type { ExtractedSkillMatch, ResumeSkillsResponse } from '../../types/skill';
import { getResumeSkills, extractResumeSkills } from '../../services/skillService';
import { SkillExtractionTable } from './SkillExtractionTable';

interface SkillIntelligenceViewProps {
  resumeId: string;
}

export const SkillIntelligenceView: React.FC<SkillIntelligenceViewProps> = ({ resumeId }) => {
  const [data, setData] = useState<ResumeSkillsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [extracting, setExtracting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSkills = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getResumeSkills(resumeId);
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load extracted skills.');
    } finally {
      setLoading(false);
    }
  };

  const handleReExtract = async () => {
    try {
      setExtracting(true);
      setError(null);
      const res = await extractResumeSkills(resumeId);
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Re-extraction failed.');
    } finally {
      setExtracting(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, [resumeId]);

  const skills: ExtractedSkillMatch[] = data?.skills || [];

  // Compute stats
  const totalSkills = skills.length;
  const escoCount = skills.filter((s) => s.taxonomy_sources?.includes('ESCO')).length;
  const onetCount = skills.filter((s) => s.taxonomy_sources?.includes('ONET')).length;
  const avgConfidence = totalSkills > 0
    ? Math.round((skills.reduce((acc, s) => acc + s.confidence, 0) / totalSkills) * 100)
    : 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner & Control */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                Phase 3 Intelligence
              </span>
              <span className="text-xs text-slate-400 font-mono">ESCO v1.2 &bull; O*NET 28.0</span>
            </div>
            <h3 className="text-2xl sm:text-3xl font-black tracking-tight">
              Skill Extraction & Normalization
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              Canonical skill mapping resolving aliases, acronyms, and variations with evidence sentences and 384-dimensional dense embeddings for downstream semantic matching.
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-3">
            <button
              onClick={handleReExtract}
              disabled={extracting || loading}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-slate-900 bg-white hover:bg-slate-100 rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              <RotateCw className={`w-3.5 h-3.5 ${extracting ? 'animate-spin' : ''}`} />
              <span>{extracting ? 'Re-extracting Skills...' : 'Re-extract Skills'}</span>
            </button>
          </div>
        </div>

        {/* Metric Cards Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-white/10">
          <div className="bg-white/5 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
            <span className="text-xs text-slate-400 font-medium block">Total Skills</span>
            <span className="text-2xl font-black text-white mt-1 block">{totalSkills}</span>
          </div>

          <div className="bg-white/5 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
            <span className="text-xs text-slate-400 font-medium block">ESCO Mapped</span>
            <span className="text-2xl font-black text-blue-400 mt-1 block">{escoCount}</span>
          </div>

          <div className="bg-white/5 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
            <span className="text-xs text-slate-400 font-medium block">O*NET Mapped</span>
            <span className="text-2xl font-black text-emerald-400 mt-1 block">{onetCount}</span>
          </div>

          <div className="bg-white/5 backdrop-blur-xs rounded-2xl p-4 border border-white/10">
            <span className="text-xs text-slate-400 font-medium block">Avg Confidence</span>
            <span className="text-2xl font-black text-amber-400 mt-1 block">{avgConfidence}%</span>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-500 space-y-3 shadow-xs">
          <RotateCw className="w-8 h-8 animate-spin mx-auto text-blue-600" />
          <p className="text-sm font-semibold text-slate-700">Extracting and normalizing skills from resume sections...</p>
          <p className="text-xs text-slate-400">Resolving aliases and looking up canonical taxonomy codes</p>
        </div>
      ) : (
        <SkillExtractionTable skills={skills} />
      )}
    </div>
  );
};
