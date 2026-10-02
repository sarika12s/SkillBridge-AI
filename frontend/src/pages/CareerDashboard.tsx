import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardService } from '../services/dashboardService';
import type {
  DashboardOverviewResponse,
  SkillHistoryResponse,
  SkillEvidenceChange,
  SkillHistoryItem,
} from '../types/dashboard';
import { OverviewCards } from '../components/dashboard/OverviewCards';
import { ScoreTrendChart } from '../components/dashboard/ScoreTrendChart';
import { SkillGapTrendChart } from '../components/dashboard/SkillGapTrendChart';
import { RoleComparisonModal } from '../components/dashboard/RoleComparisonModal';
import { EvidenceInspectionModal } from '../components/dashboard/EvidenceInspectionModal';
import {
  LayoutDashboard,
  GitCompare,
  Upload,
  RotateCw,
  Search,
  Briefcase,
  AlertCircle,
  Eye,
  CheckCircle2,
  PlusCircle,
  MinusCircle,
  Sparkles,
} from 'lucide-react';

export const CareerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<DashboardOverviewResponse | null>(null);
  const [skillHistory, setSkillHistory] = useState<SkillHistoryResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [showRoleModal, setShowRoleModal] = useState<boolean>(false);
  const [showEvidenceModal, setShowEvidenceModal] = useState<boolean>(false);
  const [selectedSkillEvidence, setSelectedSkillEvidence] = useState<SkillEvidenceChange[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewData, skillsData] = await Promise.all([
        dashboardService.getOverview(),
        dashboardService.getSkillHistory(),
      ]);
      setOverview(overviewData);
      setSkillHistory(skillsData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load career dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  const filteredSkills = skillHistory.filter((s) =>
    s.skill_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleInspectSkill = (skill: SkillHistoryResponse) => {
    const changes: SkillEvidenceChange[] = skill.history.map((h: SkillHistoryItem, idx: number) => {
      const prev = idx > 0 ? skill.history[idx - 1] : null;
      return {
        skill_name: skill.skill_name,
        previous_section: prev ? (prev.source_section || 'SKILLS') : 'NONE',
        new_section: h.source_section || 'SKILLS',
        previous_evidence: prev ? (prev.evidence_sentence || '') : '',
        new_evidence: h.evidence_sentence || '',
        strengthened: h.status === 'STRENGTHENED',
      };
    });
    setSelectedSkillEvidence(changes);
    setShowEvidenceModal(true);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'FIRST_DETECTED':
        return (
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            Initial
          </span>
        );
      case 'NEW':
        return (
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <PlusCircle className="w-3 h-3" /> New
          </span>
        );
      case 'STRENGTHENED':
        return (
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> Strengthened
          </span>
        );
      case 'RETAINED':
        return (
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Retained
          </span>
        );
      case 'WEAKENED':
        return (
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
            Weakened
          </span>
        );
      case 'REMOVED':
        return (
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
            <MinusCircle className="w-3 h-3" /> Removed
          </span>
        );
      default:
        return (
          <span className="text-[10px] text-slate-500">{status}</span>
        );
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl">
              <LayoutDashboard className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">Career Intelligence Dashboard</h1>
              <p className="text-sm text-slate-400">
                Unified analytics across resume iterations, ATS readiness, role compatibility, and skill progression
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setShowRoleModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all shadow-sm"
          >
            <Briefcase className="w-3.5 h-3.5 text-emerald-400" />
            Top Roles
          </button>
          <button
            onClick={() => navigate('/resume-versions')}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all shadow-sm"
          >
            <GitCompare className="w-3.5 h-3.5 text-indigo-400" />
            Compare Versions
          </button>
          <button
            onClick={() => navigate('/resumes')}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md shadow-indigo-600/20"
          >
            <Upload className="w-3.5 h-3.5" />
            New Version
          </button>
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors disabled:opacity-50"
            title="Refresh dashboard"
          >
            <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && !overview ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-500 space-y-3">
          <RotateCw className="w-8 h-8 animate-spin text-indigo-500" />
          <p className="text-sm font-medium">Aggregating career intelligence analytics...</p>
        </div>
      ) : overview ? (
        <div className="space-y-8">
          {/* Section 1: KPI Overview Cards */}
          <OverviewCards overview={overview} />

          {/* Section 2: Visual Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ScoreTrendChart scoreTrends={overview.score_trends} />
            <SkillGapTrendChart skillGaps={overview.skill_gap_trends} />
          </div>

          {/* Section 3: Historical Skill Trajectory */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-semibold text-white">Skill Trajectory & Evidence Evolution</h3>
                <p className="text-xs text-slate-400">
                  Track how individual competencies were introduced, retained, strengthened, or removed across versions
                </p>
              </div>

              {/* Search filter */}
              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="Filter skills..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>

            {/* Skills Table */}
            {filteredSkills.length === 0 ? (
              <div className="text-center py-10 text-xs text-slate-500">
                {searchQuery ? 'No skills matched your search query.' : 'No skill history records found.'}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                      <th className="pb-3 font-semibold">Skill Name</th>
                      <th className="pb-3 font-semibold">Category</th>
                      <th className="pb-3 font-semibold">Current Status</th>
                      <th className="pb-3 font-semibold">Versions Tracked</th>
                      <th className="pb-3 font-semibold text-right">Evidence Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredSkills.map((skill) => (
                      <tr key={skill.skill_name} className="hover:bg-slate-800/20 transition-colors">
                        <td className="py-3 font-semibold text-slate-200">{skill.skill_name}</td>
                        <td className="py-3 text-slate-400">{skill.category}</td>
                        <td className="py-3">{getStatusBadge(skill.current_status)}</td>
                        <td className="py-3 text-slate-400 font-mono text-[11px]">
                          {skill.history.map((h: SkillHistoryItem) => `v${h.resume_version}`).join(' → ')}
                        </td>
                        <td className="py-3 text-right">
                          <button
                            onClick={() => handleInspectSkill(skill)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-indigo-600/30 text-slate-300 hover:text-indigo-300 transition-colors"
                            title="Inspect extraction evidence sentence"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* Role Comparison Modal */}
      {overview && (
        <RoleComparisonModal
          isOpen={showRoleModal}
          onClose={() => setShowRoleModal(false)}
          roles={overview.top_career_roles}
        />
      )}

      {/* Evidence Inspection Modal */}
      <EvidenceInspectionModal
        isOpen={showEvidenceModal}
        onClose={() => setShowEvidenceModal(false)}
        changes={selectedSkillEvidence}
      />
    </div>
  );
};
