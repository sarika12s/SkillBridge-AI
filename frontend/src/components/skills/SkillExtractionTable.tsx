import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  ExternalLink, 
  Quote, 
  Sparkles, 
  ArrowUpDown
} from 'lucide-react';
import type { ExtractedSkillMatch } from '../../types/skill';
import { SkillDetailModal } from './SkillDetailModal';

interface SkillExtractionTableProps {
  skills: ExtractedSkillMatch[];
}

export const SkillExtractionTable: React.FC<SkillExtractionTableProps> = ({
  skills,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSection, setSelectedSection] = useState('ALL');
  const [selectedMethod, setSelectedMethod] = useState('ALL');
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null);

  // Filter skills
  const filteredSkills = skills.filter((item) => {
    const matchesSearch =
      item.canonical_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.original_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.evidence_sentence.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSection =
      selectedSection === 'ALL' || item.source_section.toUpperCase() === selectedSection;

    const matchesMethod =
      selectedMethod === 'ALL' || item.normalization_method.toUpperCase() === selectedMethod;

    return matchesSearch && matchesSection && matchesMethod;
  });

  const getMethodBadge = (method: string) => {
    switch (method?.toUpperCase()) {
      case 'EXACT':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'ALIAS':
      case 'ACRONYM':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'SYNONYM':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'SPELLING_VARIANT':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getSectionBadge = (section: string) => {
    switch (section?.toUpperCase()) {
      case 'SKILLS':
      case 'TECHNICAL_SKILLS':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'EXPERIENCE':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      case 'PROJECTS':
        return 'bg-violet-50 text-violet-700 border-violet-200';
      case 'CERTIFICATIONS':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-4">
      {/* Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search canonical skills, original mentions, or evidence..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 text-xs bg-white border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all placeholder:text-slate-400"
          />
        </div>

        <div className="flex items-center gap-2">
          {/* Section Filter */}
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 shadow-2xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              className="text-xs text-slate-700 font-medium bg-transparent focus:outline-hidden cursor-pointer"
            >
              <option value="ALL">All Sections</option>
              <option value="SKILLS">Skills</option>
              <option value="TECHNICAL_SKILLS">Technical Skills</option>
              <option value="EXPERIENCE">Experience</option>
              <option value="PROJECTS">Projects</option>
              <option value="CERTIFICATIONS">Certifications</option>
            </select>
          </div>

          {/* Normalization Method Filter */}
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 shadow-2xs">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedMethod}
              onChange={(e) => setSelectedMethod(e.target.value)}
              className="text-xs text-slate-700 font-medium bg-transparent focus:outline-hidden cursor-pointer"
            >
              <option value="ALL">All Methods</option>
              <option value="EXACT">Exact Match</option>
              <option value="ACRONYM">Acronym</option>
              <option value="ALIAS">Alias</option>
              <option value="SYNONYM">Synonym</option>
              <option value="SPELLING_VARIANT">Spelling Variant</option>
            </select>
          </div>
        </div>
      </div>

      {/* Skills Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">Canonical Skill</th>
                <th className="py-3 px-4">Detected Text</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Source Section</th>
                <th className="py-3 px-4">Evidence Sentence</th>
                <th className="py-3 px-4 text-center">Confidence</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredSkills.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <p className="text-sm font-medium">No skills found matching your filter criteria.</p>
                  </td>
                </tr>
              ) : (
                filteredSkills.map((item, idx) => (
                  <tr
                    key={idx}
                    className="hover:bg-slate-50/70 transition-colors group"
                  >
                    {/* Canonical Skill */}
                    <td className="py-3 px-4 font-bold text-slate-900">
                      <button
                        onClick={() => setSelectedSkillId(item.canonical_skill_id)}
                        className="text-left hover:text-blue-600 transition-colors flex items-center gap-1.5"
                      >
                        <span>{item.canonical_name}</span>
                        {item.taxonomy_sources && item.taxonomy_sources.length > 0 && (
                          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                            {item.taxonomy_sources.join('/')}
                          </span>
                        )}
                      </button>
                    </td>

                    {/* Original Mention */}
                    <td className="py-3 px-4 font-mono text-slate-700">
                      <span className="bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {item.original_text}
                      </span>
                    </td>

                    {/* Method */}
                    <td className="py-3 px-4">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getMethodBadge(
                          item.normalization_method
                        )}`}
                      >
                        {item.normalization_method}
                      </span>
                    </td>

                    {/* Section */}
                    <td className="py-3 px-4">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${getSectionBadge(
                          item.source_section
                        )}`}
                      >
                        {item.source_section}
                      </span>
                    </td>

                    {/* Evidence Sentence */}
                    <td className="py-3 px-4 max-w-xs text-slate-600 truncate" title={item.evidence_sentence}>
                      <span className="flex items-center gap-1 text-slate-500 italic">
                        <Quote className="w-3 h-3 text-slate-300 shrink-0" />
                        <span className="truncate">{item.evidence_sentence}</span>
                      </span>
                    </td>

                    {/* Confidence */}
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                        <Sparkles className="w-2.5 h-2.5 text-amber-500" />
                        {Math.round(item.confidence * 100)}%
                      </span>
                    </td>

                    {/* Details Action */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedSkillId(item.canonical_skill_id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-blue-700 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors"
                      >
                        <span>Ontology</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Skill Detail Modal */}
      {selectedSkillId && (
        <SkillDetailModal
          skillId={selectedSkillId}
          onClose={() => setSelectedSkillId(null)}
        />
      )}
    </div>
  );
};
