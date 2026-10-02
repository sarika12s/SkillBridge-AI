import React from 'react';
import type { StructuredAlignment } from '../../types/matching';
import { Briefcase, GraduationCap, Award, CheckCircle2, AlertTriangle, HelpCircle, XCircle } from 'lucide-react';

interface StructuredAlignmentCardProps {
  alignment: StructuredAlignment;
}

export const StructuredAlignmentCard: React.FC<StructuredAlignmentCardProps> = ({ alignment }) => {
  const getBadge = (status: string) => {
    switch (status) {
      case 'MEETS':
      case 'MATCHED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Satisfied
          </span>
        );
      case 'PARTIAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" />
            Partial Alignment
          </span>
        );
      case 'BELOW_REQUIREMENT':
      case 'MISSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" />
            Deficiency
          </span>
        );
      case 'UNKNOWN':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            <HelpCircle className="w-3.5 h-3.5" />
            Unspecified / Unstated
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
      <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
        Structured Entity Alignment (Experience, Education, Certifications)
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Experience Alignment */}
        <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-blue-400" />
                <span className="font-medium text-slate-200 text-sm">Experience Duration</span>
              </div>
              {getBadge(alignment.experience_status)}
            </div>
            <div className="text-xs text-slate-300 space-y-1 mb-2">
              <div>
                <span className="text-slate-400">Required:</span>{' '}
                <span className="font-semibold text-white">
                  {alignment.required_years ? `${alignment.required_years} years` : 'Unspecified'}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Demonstrated:</span>{' '}
                <span className="font-semibold text-white">
                  {alignment.resume_years ? `${alignment.resume_years} years` : 'Not explicitly stated'}
                </span>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed border-t border-slate-700/40 pt-2 mt-2">
            {alignment.experience_explanation}
          </p>
        </div>

        {/* Education Alignment */}
        <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-indigo-400" />
                <span className="font-medium text-slate-200 text-sm">Academic Degree</span>
              </div>
              {getBadge(alignment.education_status)}
            </div>
            <div className="text-xs text-slate-300 space-y-1 mb-2">
              <div>
                <span className="text-slate-400">Required:</span>{' '}
                <span className="font-semibold text-white">
                  {alignment.required_degree || 'Unspecified'}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Candidate:</span>{' '}
                <span className="font-semibold text-white">
                  {alignment.resume_degree || 'None identified'}
                </span>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed border-t border-slate-700/40 pt-2 mt-2">
            {alignment.education_explanation}
          </p>
        </div>

        {/* Certification Alignment */}
        <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-400" />
                <span className="font-medium text-slate-200 text-sm">Certifications</span>
              </div>
              {getBadge(alignment.certification_status)}
            </div>
            <div className="text-xs text-slate-300 space-y-1 mb-2">
              <div>
                <span className="text-slate-400">Verified:</span>{' '}
                <span className="font-semibold text-emerald-400">
                  {alignment.matched_certifications.length > 0
                    ? alignment.matched_certifications.join(', ')
                    : 'None required / none verified'}
                </span>
              </div>
              {alignment.missing_certifications.length > 0 && (
                <div>
                  <span className="text-slate-400">Missing:</span>{' '}
                  <span className="font-semibold text-rose-400">
                    {alignment.missing_certifications.join(', ') }
                  </span>
                </div>
              )}
            </div>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed border-t border-slate-700/40 pt-2 mt-2">
            {alignment.certification_explanation}
          </p>
        </div>
      </div>
    </div>
  );
};
