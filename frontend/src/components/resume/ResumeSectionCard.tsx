import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import type { ResumeSection } from '../../types/resume';

interface ResumeSectionCardProps {
  section: ResumeSection;
}

export const ResumeSectionCard: React.FC<ResumeSectionCardProps> = ({ section }) => {
  const [isOpen, setIsOpen] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  const copyContent = () => {
    navigator.clipboard.writeText(section.content_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case 'EDUCATION':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'EXPERIENCE':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PROJECTS':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'SKILLS':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'CERTIFICATIONS':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'SUMMARY':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm transition hover:border-slate-300">
      {/* Header bar */}
      <div className="p-4 flex items-center justify-between bg-slate-50/70 border-b border-slate-200/80">
        <div className="flex items-center space-x-3">
          <span
            className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${getBadgeStyle(
              section.section_type
            )}`}
          >
            {section.section_type}
          </span>
          <h4 className="text-sm font-semibold text-slate-800">
            {section.section_title}
          </h4>
          <span className="text-[11px] text-slate-400 font-mono hidden sm:inline">
            (order: #{section.order_index})
          </span>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={copyContent}
            title="Copy section content"
            className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-200/60 rounded-md transition"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-200/60 rounded-md transition"
          >
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Body Content */}
      {isOpen && (
        <div className="p-4 sm:p-5 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed font-sans bg-white">
          {section.content_text}
        </div>
      )}
    </div>
  );
};
