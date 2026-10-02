import React, { useEffect, useState } from 'react';
import { 
  X, 
  BookOpen, 
  GitBranch, 
  ShieldCheck, 
  Binary, 
  Loader2,
  Tag
} from 'lucide-react';
import type { CanonicalSkill, SkillRelationship } from '../../types/skill';
import { getSkillById, getSkillRelationships } from '../../services/skillService';

interface SkillDetailModalProps {
  skillId: string;
  onClose: () => void;
}

export const SkillDetailModal: React.FC<SkillDetailModalProps> = ({ skillId, onClose }) => {
  const [skill, setSkill] = useState<CanonicalSkill | null>(null);
  const [relationships, setRelationships] = useState<SkillRelationship[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        const [skillData, relsData] = await Promise.all([
          getSkillById(skillId),
          getSkillRelationships(skillId),
        ]);
        if (isMounted) {
          setSkill(skillData);
          setRelationships(relsData);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.response?.data?.detail || 'Failed to load skill details.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadDetails();
    return () => {
      isMounted = false;
    };
  }, [skillId]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-200">
      <div 
        className="bg-white border border-slate-200 rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-slate-50 border-b border-slate-100 p-6 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 uppercase tracking-wider">
                {skill?.taxonomy_source || 'TAXONOMY'}
              </span>
              <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                {skill?.category?.replace('_', ' ') || 'TECHNICAL SKILL'}
              </span>
            </div>
            <h3 className="text-2xl font-black text-slate-900 tracking-tight">
              {skill?.name || 'Loading Skill...'}
            </h3>
            {skill?.taxonomy_code && (
              <p className="text-xs text-slate-500 font-mono mt-0.5 truncate max-w-md">
                Ref: {skill.taxonomy_code}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 text-slate-500 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <p className="text-sm font-medium">Fetching taxonomy details & knowledge graph...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm">
              {error}
            </div>
          )}

          {!loading && skill && (
            <>
              {/* Description */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" />
                  Taxonomy Definition
                </h4>
                <p className="text-sm text-slate-700 leading-relaxed bg-slate-50/70 p-4 rounded-2xl border border-slate-100">
                  {skill.description || 'Standard technical skill defined in official labor market taxonomy.'}
                </p>
              </div>

              {/* Vector Embedding Status */}
              <div className="p-4 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-white rounded-2xl border border-blue-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-600 text-white rounded-xl shadow-xs">
                    <Binary className="w-5 h-5" />
                  </div>
                  <div>
                    <h5 className="text-sm font-bold text-slate-900">Dense Vector Embedding</h5>
                    <p className="text-xs text-slate-500">
                      384-dimensional dense representation (sentence-transformers/all-MiniLM-L6-v2)
                    </p>
                  </div>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Active
                </span>
              </div>

              {/* Aliases & Spelling Variations */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5" />
                  Recognized Aliases & Variations ({skill.aliases?.length || 0})
                </h4>
                {skill.aliases && skill.aliases.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {skill.aliases.map((al, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-mono bg-slate-100 text-slate-800 border border-slate-200"
                      >
                        <span className="font-semibold text-slate-900">{al.alias}</span>
                        <span className="text-[10px] text-slate-500">({al.alias_type})</span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No alternative aliases registered.</p>
                )}
              </div>

              {/* Skill Ontology & Relationships */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <GitBranch className="w-3.5 h-3.5" />
                  Skill Ontology & Relationships ({relationships.length})
                </h4>

                {relationships.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {relationships.map((rel, idx) => {
                      const isSource = rel.source_skill_id === skill.id;
                      const relLabel = rel.relationship_type.replace(/_/g, ' ');
                      const targetName = isSource ? rel.target_skill_name || 'Target Skill' : skill.name;

                      return (
                        <div
                          key={idx}
                          className="p-3 bg-white border border-slate-200 rounded-xl flex items-center justify-between text-xs hover:border-blue-200 transition-colors shadow-2xs"
                        >
                          <div className="space-y-0.5">
                            <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block">
                              {relLabel}
                            </span>
                            <span className="font-semibold text-slate-900">
                              {targetName}
                            </span>
                          </div>
                          <span className="text-[11px] font-mono font-medium text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                            w: {rel.strength_weight}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">
                    No ontology relationships linked for this skill in the knowledge graph.
                  </p>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 border-t border-slate-100 px-6 py-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-100 transition-colors shadow-2xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
