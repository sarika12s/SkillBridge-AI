import React from 'react';
import { Tag, Sparkles } from 'lucide-react';
import type { ExtractedSkillMatch } from '../../types/skill';

interface SkillBadgeProps {
  skill: ExtractedSkillMatch;
  onClick?: () => void;
  showDetails?: boolean;
}

export const SkillBadge: React.FC<SkillBadgeProps> = ({
  skill,
  onClick,
  showDetails = true,
}) => {
  const getCategoryTheme = (category: string) => {
    switch (category?.toUpperCase()) {
      case 'PROGRAMMING_LANGUAGE':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100';
      case 'FRAMEWORK':
      case 'WEB_FRAMEWORK':
        return 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100';
      case 'DATABASE':
        return 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100';
      case 'CLOUD_DEVOPS':
      case 'CLOUD_COMPUTING':
      case 'CONTAINERIZATION':
        return 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100';
      case 'AI_ML':
      case 'MACHINE_LEARNING':
      case 'DATA_SCIENCE':
        return 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100';
      default:
        return 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100';
    }
  };

  const getMethodBadge = (method: string) => {
    switch (method?.toUpperCase()) {
      case 'EXACT':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'ALIAS':
      case 'ACRONYM':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'SYNONYM':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'SPELLING_VARIANT':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all shadow-xs ${
        onClick ? 'cursor-pointer hover:shadow-sm' : ''
      } ${getCategoryTheme(skill.source_section)}`}
    >
      <Tag className="w-3.5 h-3.5 opacity-70" />
      <span className="font-semibold text-slate-900">{skill.canonical_name}</span>

      {skill.original_text && skill.original_text !== skill.canonical_name && (
        <span className="text-[10px] text-slate-500 font-mono bg-white/70 px-1 py-0.5 rounded border border-slate-200">
          "{skill.original_text}"
        </span>
      )}

      {showDetails && (
        <>
          <span
            className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${getMethodBadge(
              skill.normalization_method
            )}`}
          >
            {skill.normalization_method}
          </span>
          <span className="text-[10px] font-bold text-slate-600 bg-white/80 px-1.5 py-0.5 rounded border border-slate-200 flex items-center gap-0.5">
            <Sparkles className="w-2.5 h-2.5 text-amber-500" />
            {Math.round(skill.confidence * 100)}%
          </span>
        </>
      )}
    </div>
  );
};
