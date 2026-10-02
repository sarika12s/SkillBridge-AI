import React from 'react';
import type { ExplainabilitySummary } from '../../types/matching';
import { CheckCircle2, HelpCircle, ShieldAlert, Sparkles } from 'lucide-react';

interface ExplainabilityBreakdownProps {
  explainability: ExplainabilitySummary;
  summaryExplanation?: string;
}

export const ExplainabilityBreakdown: React.FC<ExplainabilityBreakdownProps> = ({
  explainability,
  summaryExplanation,
}) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-indigo-400" />
        <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
          Explainability Engine Narrative & Assessment Drivers
        </h4>
      </div>

      {/* Summary Narrative */}
      {summaryExplanation && (
        <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 text-slate-200 text-sm leading-relaxed">
          {summaryExplanation}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Positive Factors & Strengths */}
        <div className="space-y-3">
          <h5 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            Demonstrated Strengths & Verified Drivers
          </h5>
          <div className="space-y-2">
            {explainability.positive_factors.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No significant positive drivers identified.</p>
            ) : (
              explainability.positive_factors.map((p, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/40 text-xs text-slate-300 flex items-start gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                  <span>{p}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Bottlenecks & Critical Gaps */}
        <div className="space-y-3">
          <h5 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4" />
            Critical Gaps & Score Penalties
          </h5>
          <div className="space-y-2">
            {explainability.negative_factors.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No critical deficiencies detected.</p>
            ) : (
              explainability.negative_factors.map((n, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/40 text-xs text-slate-300 flex items-start gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 shrink-0" />
                  <span>{n}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Uncertainties (if any) */}
      {explainability.uncertainties.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700 text-xs space-y-1">
          <div className="font-semibold text-slate-300 flex items-center gap-1.5 mb-1">
            <HelpCircle className="w-4 h-4 text-amber-400" />
            Factual Uncertainties & Unstated Profile Information
          </div>
          {explainability.uncertainties.map((u, idx) => (
            <p key={idx} className="text-slate-400">
              • {u}
            </p>
          ))}
        </div>
      )}

      {/* Methodology Transparency Disclosure */}
      <div className="border-t border-slate-800 pt-4 text-[11px] text-slate-500 space-y-1">
        <p className="font-semibold text-slate-400">Scoring Methodology Transparency Note:</p>
        <p>
          Weights used: Required Skills (40%), Preferred Skills (15%), Experience (15%), Education (10%), Certifications (5%), Evidence Sentences (10%), Semantic Proximity (5%).
          Scores are analytical metrics calibrated for academic decision transparency and do not guarantee interview or employment outcomes.
        </p>
      </div>
    </div>
  );
};
