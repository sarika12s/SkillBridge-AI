import React, { useState } from 'react';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Globe, 
  Briefcase, 
  FolderGit2, 
  Award, 
  Layers,
  Calendar,
  ExternalLink,
  Code,
  Sparkles,
  Target
} from 'lucide-react';
import type { StructuredResume } from '../../types/resume';
import { ParsingStatus } from './ParsingStatus';
import { ResumeSectionCard } from './ResumeSectionCard';
import { SkillIntelligenceView } from '../skills/SkillIntelligenceView';
import { STARGuidanceView } from './STARGuidanceView';

const LinkedinIcon: React.FC<{ className?: string }> = ({ className = 'w-3 h-3' }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
  </svg>
);

const GithubIcon: React.FC<{ className?: string }> = ({ className = 'w-3 h-3' }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
  </svg>
);

interface ResumePreviewProps {
  resume: StructuredResume;
  onReset?: () => void;
}

export const ResumePreview: React.FC<ResumePreviewProps> = ({ resume, onReset }) => {
  const [activeTab, setActiveTab] = useState<'skills' | 'star' | 'sections' | 'experience' | 'projects' | 'certifications' | 'raw'>(
    'skills'
  );

  const contact = resume.personal_information;

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-full uppercase">
                {resume.file_type.toUpperCase()} Document
              </span>
              <span className="text-xs text-slate-400">&bull;</span>
              <span className="text-xs text-slate-500 font-mono">{resume.file_name}</span>
            </div>
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              {resume.title}
            </h2>
          </div>

          {onReset && (
            <button
              onClick={onReset}
              className="text-xs font-medium text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3.5 py-2 rounded-lg transition self-start md:self-auto"
            >
              Upload Another Resume
            </button>
          )}
        </div>

        {/* Diagnostics & Method Badges */}
        <ParsingStatus
          status={resume.parsing_status}
          method={resume.extraction_method}
          pageCount={resume.page_count}
          characterCount={resume.character_count}
          sectionsCount={resume.sections.length}
        />

        {/* Phase Boundary Disclaimer */}
        <div className="p-3 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-800 flex items-center justify-between">
          <p>
            <span className="font-semibold">Deterministic Ingestion Baseline: </span>
            Content is extracted, normalized, and segmented without generative guessing.
            Taxonomy matching and skill gap prioritization will execute in later phases.
          </p>
        </div>
      </div>

      {/* Contact Information Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <User className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
            Candidate Contact Details
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 text-xs">
          {/* Full Name */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
            <span className="text-[11px] font-semibold text-slate-400 uppercase">Candidate Name</span>
            <p className="font-bold text-slate-900 text-sm">{contact.name || 'Not detected'}</p>
          </div>

          {/* Email */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
            <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center space-x-1">
              <Mail className="w-3 h-3 text-slate-400" />
              <span>Email Address</span>
            </span>
            <p className="font-medium text-slate-800 truncate">{contact.email || 'Not detected'}</p>
          </div>

          {/* Phone */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
            <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center space-x-1">
              <Phone className="w-3 h-3 text-slate-400" />
              <span>Phone</span>
            </span>
            <p className="font-medium text-slate-800">{contact.phone || 'Not detected'}</p>
          </div>

          {/* Location */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
            <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center space-x-1">
              <MapPin className="w-3 h-3 text-slate-400" />
              <span>Location</span>
            </span>
            <p className="font-medium text-slate-800">{contact.location || 'Not detected'}</p>
          </div>

          {/* LinkedIn URL */}
          {contact.linkedin_url && (
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center space-x-1">
                <LinkedinIcon className="w-3 h-3 text-blue-600" />
                <span>LinkedIn</span>
              </span>
              <a
                href={contact.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-blue-600 hover:underline truncate block"
              >
                {contact.linkedin_url.replace('https://', '')}
              </a>
            </div>
          )}

          {/* GitHub URL */}
          {contact.github_url && (
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center space-x-1">
                <GithubIcon className="w-3 h-3 text-slate-800" />
                <span>GitHub</span>
              </span>
              <a
                href={contact.github_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-blue-600 hover:underline truncate block"
              >
                {contact.github_url.replace('https://', '')}
              </a>
            </div>
          )}

          {/* Portfolio URL */}
          {contact.portfolio_url && (
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 space-y-0.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center space-x-1">
                <Globe className="w-3 h-3 text-emerald-600" />
                <span>Portfolio</span>
              </span>
              <a
                href={contact.portfolio_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-blue-600 hover:underline truncate block"
              >
                {contact.portfolio_url}
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 space-x-2 overflow-x-auto pb-1 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('skills')}
          className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
            activeTab === 'skills'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Extracted Skills (Phase 3)</span>
        </button>

        <button
          onClick={() => setActiveTab('star')}
          className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
            activeTab === 'star'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Target className="w-4 h-4 text-emerald-400" />
          <span>STAR Quality Guidance</span>
        </button>

        <button
          onClick={() => setActiveTab('sections')}
          className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
            activeTab === 'sections'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Detected Sections ({resume.sections.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('experience')}
          className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
            activeTab === 'experience'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          <span>Experience ({resume.experience.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('projects')}
          className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
            activeTab === 'projects'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <FolderGit2 className="w-4 h-4" />
          <span>Projects ({resume.projects.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('certifications')}
          className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
            activeTab === 'certifications'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Certifications ({resume.certifications.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('raw')}
          className={`px-4 py-2.5 rounded-lg transition flex items-center space-x-2 ${
            activeTab === 'raw'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Code className="w-4 h-4" />
          <span>Raw Extracted Text</span>
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {/* Extracted Skills Tab */}
        {activeTab === 'skills' && (
          <SkillIntelligenceView resumeId={resume.id} />
        )}

        {/* STAR Quality Guidance Tab */}
        {activeTab === 'star' && (
          <STARGuidanceView resumeId={resume.id} />
        )}

        {/* Sections Tab */}
        {activeTab === 'sections' && (
          <div className="space-y-4">
            {resume.sections.map((section, idx) => (
              <ResumeSectionCard key={section.id || idx} section={section} />
            ))}
          </div>
        )}

        {/* Experience Tab */}
        {activeTab === 'experience' && (
          <div className="space-y-4">
            {resume.experience.length === 0 ? (
              <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-xs">
                No structured work experience entries extracted.
              </div>
            ) : (
              resume.experience.map((exp, idx) => (
                <div
                  key={exp.id || idx}
                  className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-2"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{exp.job_title}</h4>
                      <p className="text-xs font-semibold text-blue-700">{exp.company_name}</p>
                    </div>
                    {(exp.start_date || exp.end_date) && (
                      <span className="text-xs text-slate-500 font-medium flex items-center space-x-1">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>
                          {exp.start_date || ''} {exp.start_date && exp.end_date ? '-' : ''}{' '}
                          {exp.is_current ? 'Present' : exp.end_date || ''}
                        </span>
                      </span>
                    )}
                  </div>
                  {exp.description && (
                    <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed pt-2 border-t border-slate-100">
                      {exp.description}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === 'projects' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resume.projects.length === 0 ? (
              <div className="col-span-2 p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-xs">
                No structured projects extracted.
              </div>
            ) : (
              resume.projects.map((proj, idx) => (
                <div
                  key={proj.id || idx}
                  className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-bold text-slate-900">{proj.project_name}</h4>
                      {proj.url && (
                        <a
                          href={proj.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                    {proj.description && (
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {proj.description}
                      </p>
                    )}
                  </div>

                  {proj.technologies_used && proj.technologies_used.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                      {proj.technologies_used.map((tech, tIdx) => (
                        <span
                          key={tIdx}
                          className="text-[11px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Certifications Tab */}
        {activeTab === 'certifications' && (
          <div className="space-y-3">
            {resume.certifications.length === 0 ? (
              <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-xs">
                No structured certifications extracted.
              </div>
            ) : (
              resume.certifications.map((cert, idx) => (
                <div
                  key={cert.id || idx}
                  className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-purple-50 text-purple-600">
                      <Award className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-800">{cert.name}</h4>
                      {cert.issuing_organization && (
                        <p className="text-xs text-slate-500">Issued by {cert.issuing_organization}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Raw Text Tab */}
        {activeTab === 'raw' && (
          <div className="bg-slate-900 text-slate-100 rounded-xl p-5 shadow-inner overflow-x-auto text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-[600px]">
            {resume.raw_text || 'No raw text available.'}
          </div>
        )}
      </div>
    </div>
  );
};
