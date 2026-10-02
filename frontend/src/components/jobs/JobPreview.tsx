import React, { useState } from 'react';
import { 
  Building2, 
  MapPin, 
  Link as LinkIcon, 
  Sparkles, 
  Layers, 
  CheckCircle2, 
  Clock, 
  GraduationCap, 
  Award, 
  Briefcase, 
  Filter, 
  Quote, 
  Code
} from 'lucide-react';
import type { StructuredJob } from '../../types/job';

interface JobPreviewProps {
  job: StructuredJob;
  onReset?: () => void;
}

export const JobPreview: React.FC<JobPreviewProps> = ({ job, onReset }) => {
  const [activeTab, setActiveTab] = useState<'skills' | 'requirements' | 'experience' | 'sections' | 'raw'>('skills');
  const [selectedReqCategory, setSelectedReqCategory] = useState<string>('ALL');

  // Filter requirements
  const filteredRequirements = job.requirements.filter((r) => {
    return selectedReqCategory === 'ALL' || r.requirement_category === selectedReqCategory;
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority?.toUpperCase()) {
      case 'REQUIRED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PREFERRED':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category?.toUpperCase()) {
      case 'EXPERIENCE':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'EDUCATION':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'CERTIFICATION':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'RESPONSIBILITY':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      case 'SKILL':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'SOFT_SKILL':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  // Compute stats
  const minYears = job.experience_requirements.length > 0 && job.experience_requirements[0].minimum_years !== null
    ? `${job.experience_requirements[0].minimum_years}+ yrs`
    : 'Not Specified';

  const eduDegree = job.education_requirements.length > 0
    ? job.education_requirements[0].degree_level.replace('_', ' ')
    : 'Not Specified';

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner Card */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full uppercase">
                {job.ingestion_type} Ingestion
              </span>
              <span className="text-xs text-slate-400">&bull;</span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-500" />
                Role: {job.normalized_role} ({Math.round(job.role_confidence * 100)}%)
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {job.title}
            </h2>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
              {job.company && (
                <span className="flex items-center gap-1 font-medium text-slate-700">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  {job.company}
                </span>
              )}
              {job.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  {job.location}
                </span>
              )}
              {job.source_url && (
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-blue-600 hover:underline"
                >
                  <LinkIcon className="w-3.5 h-3.5" />
                  <span>View Original Posting</span>
                </a>
              )}
            </div>
          </div>

          {onReset && (
            <button
              onClick={onReset}
              className="text-xs font-medium text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-4 py-2 rounded-xl transition self-start md:self-auto cursor-pointer"
            >
              Analyze Another Job
            </button>
          )}
        </div>

        {/* Metric Cards Row */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-4 border-t border-slate-100">
          <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-500 block">Total Requirements</span>
            <span className="text-xl font-bold text-slate-900 mt-0.5 block">{job.requirements.length}</span>
          </div>

          <div className="bg-emerald-50/50 p-3.5 rounded-2xl border border-emerald-100">
            <span className="text-[11px] font-semibold text-emerald-700 block">Required Skills</span>
            <span className="text-xl font-bold text-emerald-900 mt-0.5 block">{job.required_skills.length}</span>
          </div>

          <div className="bg-blue-50/50 p-3.5 rounded-2xl border border-blue-100">
            <span className="text-[11px] font-semibold text-blue-700 block">Preferred Skills</span>
            <span className="text-xl font-bold text-blue-900 mt-0.5 block">{job.preferred_skills.length}</span>
          </div>

          <div className="bg-amber-50/50 p-3.5 rounded-2xl border border-amber-100">
            <span className="text-[11px] font-semibold text-amber-700 block">Experience Level</span>
            <span className="text-sm font-bold text-amber-900 mt-1 block truncate">{minYears}</span>
          </div>

          <div className="bg-purple-50/50 p-3.5 rounded-2xl border border-purple-100">
            <span className="text-[11px] font-semibold text-purple-700 block">Education Degree</span>
            <span className="text-sm font-bold text-purple-900 mt-1 block truncate">{eduDegree}</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 space-x-2 overflow-x-auto pb-1 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('skills')}
          className={`px-4 py-2.5 rounded-xl transition flex items-center space-x-2 ${
            activeTab === 'skills'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Extracted Skills ({job.all_skills.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('requirements')}
          className={`px-4 py-2.5 rounded-xl transition flex items-center space-x-2 ${
            activeTab === 'requirements'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>Structured Requirements ({job.requirements.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('experience')}
          className={`px-4 py-2.5 rounded-xl transition flex items-center space-x-2 ${
            activeTab === 'experience'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          <span>Experience & Education</span>
        </button>

        <button
          onClick={() => setActiveTab('sections')}
          className={`px-4 py-2.5 rounded-xl transition flex items-center space-x-2 ${
            activeTab === 'sections'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Detected Sections ({job.sections.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('raw')}
          className={`px-4 py-2.5 rounded-xl transition flex items-center space-x-2 ${
            activeTab === 'raw'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Code className="w-4 h-4" />
          <span>Normalized Text</span>
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {/* Tab 1: Skills (Required vs Preferred) */}
        {activeTab === 'skills' && (
          <div className="space-y-6">
            {/* Required Skills Section */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                    Required Skills ({job.required_skills.length})
                  </h3>
                  <p className="text-xs text-slate-500">Core mandatory competencies identified with explicit evidence</p>
                </div>
              </div>

              {job.required_skills.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No explicit required skills detected.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {job.required_skills.map((skill, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 bg-emerald-50/20 border border-emerald-100 rounded-2xl space-y-2 hover:border-emerald-300 transition"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sm text-slate-900">{skill.canonical_skill_name}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                          REQUIRED
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-slate-600 italic">
                        <Quote className="w-3 h-3 text-slate-400 shrink-0" />
                        <span className="truncate">{skill.evidence_text}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Preferred Skills Section */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                    Preferred / Nice-to-Have Skills ({job.preferred_skills.length})
                  </h3>
                  <p className="text-xs text-slate-500">Desirable skills identified through bonus / preferred linguistic cues</p>
                </div>
              </div>

              {job.preferred_skills.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No preferred skills detected.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {job.preferred_skills.map((skill, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 bg-blue-50/20 border border-blue-100 rounded-2xl space-y-2 hover:border-blue-300 transition"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sm text-slate-900">{skill.canonical_skill_name}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                          PREFERRED
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-slate-600 italic">
                        <Quote className="w-3 h-3 text-slate-400 shrink-0" />
                        <span className="truncate">{skill.evidence_text}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Structured Requirements */}
        {activeTab === 'requirements' && (
          <div className="space-y-4">
            {/* Filter Bar */}
            <div className="flex items-center gap-2 bg-white border border-slate-200 p-2.5 rounded-2xl">
              <Filter className="w-4 h-4 text-slate-400 ml-2" />
              <select
                value={selectedReqCategory}
                onChange={(e) => setSelectedReqCategory(e.target.value)}
                className="text-xs font-semibold text-slate-700 bg-transparent focus:outline-hidden cursor-pointer"
              >
                <option value="ALL">All Categories ({job.requirements.length})</option>
                <option value="SKILL">Skills</option>
                <option value="EXPERIENCE">Experience</option>
                <option value="EDUCATION">Education</option>
                <option value="CERTIFICATION">Certifications</option>
                <option value="RESPONSIBILITY">Responsibilities</option>
                <option value="SOFT_SKILL">Soft Skills</option>
                <option value="DOMAIN_KNOWLEDGE">Domain Knowledge</option>
              </select>
            </div>

            {/* Requirements Table */}
            <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3 px-4">Requirement</th>
                      <th className="py-3 px-4">Category</th>
                      <th className="py-3 px-4">Priority</th>
                      <th className="py-3 px-4">Source Section</th>
                      <th className="py-3 px-4">Evidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredRequirements.map((req, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/70 transition">
                        <td className="py-3 px-4 font-medium text-slate-900 max-w-sm">
                          {req.original_text}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getCategoryBadge(req.requirement_category)}`}>
                            {req.requirement_category}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getPriorityBadge(req.priority)}`}>
                            {req.priority}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                          {req.source_section}
                        </td>
                        <td className="py-3 px-4 text-slate-500 italic max-w-xs truncate" title={req.evidence_text}>
                          {req.evidence_text}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Experience & Education */}
        {activeTab === 'experience' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Experience Card */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs space-y-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-amber-600" />
                <span>Experience Requirements</span>
              </h3>

              {job.experience_requirements.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No structured experience requirements detected.</p>
              ) : (
                job.experience_requirements.map((exp, idx) => (
                  <div key={idx} className="p-4 bg-amber-50/30 border border-amber-200/60 rounded-2xl space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-900">
                        {exp.minimum_years !== null ? `${exp.minimum_years}+ Years Minimum` : 'Experience Required'}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 border border-amber-200">
                        {exp.classification}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 italic">"{exp.experience_text}"</p>
                  </div>
                ))
              )}
            </div>

            {/* Education Card */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs space-y-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-purple-600" />
                <span>Education Requirements</span>
              </h3>

              {job.education_requirements.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No structured education requirements detected.</p>
              ) : (
                job.education_requirements.map((edu, idx) => (
                  <div key={idx} className="p-4 bg-purple-50/30 border border-purple-200/60 rounded-2xl space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-900">
                        {edu.degree_level.replace('_', ' ')}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getPriorityBadge(edu.requirement_type)}`}>
                        {edu.requirement_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 font-medium">Field: {edu.field}</p>
                    <p className="text-xs text-slate-500 italic">"{edu.original_text}"</p>
                  </div>
                ))
              )}

              {/* Certifications Subsection */}
              {job.certifications.length > 0 && (
                <div className="pt-4 border-t border-slate-100 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-rose-500" />
                    <span>Certifications</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {job.certifications.map((c, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-rose-50 border border-rose-200 text-xs font-semibold text-rose-800"
                      >
                        <Award className="w-3 h-3 text-rose-600" />
                        <span>{c.name}</span>
                        <span className="text-[9px] text-rose-500">({c.requirement_type})</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Detected Sections */}
        {activeTab === 'sections' && (
          <div className="space-y-4">
            {job.sections.map((sec, idx) => (
              <div key={idx} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 font-mono">
                    #{sec.order_index + 1} &bull; {sec.section_title}
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                    {sec.section_type}
                  </span>
                </div>
                <div className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {sec.content_text}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 5: Raw Text */}
        {activeTab === 'raw' && (
          <div className="bg-slate-900 text-slate-100 rounded-2xl p-6 shadow-inner text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-[600px] overflow-y-auto">
            {job.raw_text}
          </div>
        )}
      </div>
    </div>
  );
};
