import React, { useState } from 'react';
import type { SkillMatch } from '../../types/matching';
import {
  CheckCircle,
  AlertCircle,
  Search,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface SkillComparisonTableProps {
  matches: SkillMatch[];
}

type FilterOption = 'ALL' | 'MATCHED' | 'MISSING' | 'PARTIAL' | 'REQUIRED' | 'PREFERRED';

export const SkillComparisonTable: React.FC<SkillComparisonTableProps> = ({ matches }) => {
  const [activeFilter, setActiveFilter] = useState<FilterOption>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);

  const filteredMatches = matches.filter((m) => {
    // 1. Text search
    if (
      searchQuery &&
      !m.canonical_skill_name.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !m.explanation.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }

    // 2. Filter category
    switch (activeFilter) {
      case 'MATCHED':
        return ['MATCHED_REQUIRED', 'MATCHED_PREFERRED'].includes(m.match_status);
      case 'MISSING':
        return ['MISSING_REQUIRED', 'MISSING_PREFERRED'].includes(m.match_status);
      case 'PARTIAL':
        return ['PARTIAL_REQUIRED', 'PARTIAL_PREFERRED', 'RELATED_SUPPORT'].includes(
          m.match_status
        );
      case 'REQUIRED':
        return m.priority === 'REQUIRED';
      case 'PREFERRED':
        return m.priority === 'PREFERRED';
      case 'ALL':
      default:
        return true;
    }
  });

  const getMatchTypeBadge = (type: string) => {
    switch (type) {
      case 'DIRECT_MATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            Direct Match
          </span>
        );
      case 'ALIAS_MATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">
            Alias Resolved
          </span>
        );
      case 'TAXONOMY_EQUIVALENT':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30">
            Ontology Equivalent
          </span>
        );
      case 'SEMANTIC_MATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            Dense Semantic
          </span>
        );
      case 'RELATED_SUPPORT':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            Supporting Relation
          </span>
        );
      case 'PARTIAL_MATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
            Partial Overlap
          </span>
        );
      case 'NO_MATCH':
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            Unsatisfied
          </span>
        );
    }
  };

  const getPriorityBadge = (priority: string) => {
    if (priority === 'REQUIRED') {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-950/60 text-rose-300 border border-rose-800/40">
          Required
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-950/60 text-purple-300 border border-purple-800/40">
        Preferred
      </span>
    );
  };

  const toggleExpand = (skillName: string) => {
    setExpandedSkill(expandedSkill === skillName ? null : skillName);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
            Granular Skill Comparison & Evidence Inspection
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Traceable justifications linking resume statements to job requirements.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
          {(['ALL', 'MATCHED', 'MISSING', 'PARTIAL', 'REQUIRED', 'PREFERRED'] as FilterOption[]).map(
            (f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  activeFilter === f
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                {f.charAt(0) + f.slice(1).toLowerCase()}
              </button>
            )
          )}
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
        <input
          type="text"
          placeholder="Filter skills by keyword (e.g. Python, Docker, SQL)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-9 pr-4 py-2 bg-slate-800/50 border border-slate-700/60 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
        />
      </div>

      {/* Skills Table List */}
      <div className="space-y-3">
        {filteredMatches.length === 0 ? (
          <div className="text-center py-10 text-slate-400 text-sm">
            No skills match the selected filter criteria.
          </div>
        ) : (
          filteredMatches.map((m) => {
            const isExpanded = expandedSkill === m.canonical_skill_name;
            return (
              <div
                key={m.canonical_skill_name}
                className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:border-slate-600 transition-colors cursor-pointer"
                onClick={() => toggleExpand(m.canonical_skill_name)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-white text-sm">
                      {m.canonical_skill_name}
                    </span>
                    {getPriorityBadge(m.priority)}
                    {getMatchTypeBadge(m.match_type)}
                  </div>

                  <div className="flex items-center gap-4">
                    {m.similarity_score !== undefined && m.similarity_score !== null && (
                      <span className="text-xs text-slate-400 font-mono hidden sm:inline">
                        Sim: {(m.similarity_score * 100).toFixed(0)}%
                      </span>
                    )}
                    <button className="text-slate-400 hover:text-white">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Explanation Snippet */}
                <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                  {m.explanation}
                </p>

                {/* Expandable Traceable Evidence */}
                {isExpanded && (
                  <div className="mt-4 pt-3 border-t border-slate-700/50 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <div className="font-semibold text-indigo-300 mb-1 flex items-center gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5" />
                        Candidate Resume Evidence
                      </div>
                      <p className="text-slate-300 italic">
                        {m.resume_evidence || 'No direct contextual sentence extracted.'}
                      </p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                      <div className="font-semibold text-amber-300 mb-1 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Target Job Requirement Evidence
                      </div>
                      <p className="text-slate-300 italic">
                        {m.job_evidence || 'Standard role requirement specification.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
