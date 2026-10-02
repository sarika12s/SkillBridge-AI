import React from 'react';
import { CheckCircle2, Loader2 } from 'lucide-react';

interface UploadProgressProps {
  stage: 'uploading' | 'validating' | 'extracting' | 'segmenting' | 'completed';
  progressPercent: number;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({ stage, progressPercent }) => {
  const steps = [
    { key: 'uploading', label: 'Uploading Document' },
    { key: 'validating', label: 'Validating Format & Magic Bytes' },
    { key: 'extracting', label: 'Extracting Text (Direct / OCR)' },
    { key: 'segmenting', label: 'Detecting Sections & Entities' },
    { key: 'completed', label: 'Parsing Complete' },
  ];

  const getStepIndex = (key: string) => steps.findIndex((s) => s.key === key);
  const currentIdx = getStepIndex(stage);

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
          Ingestion & Parsing Pipeline
        </h4>
        <span className="text-xs font-semibold text-blue-600 font-mono">
          {stage === 'uploading' ? `${progressPercent}%` : 'Processing'}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
        <div
          className="bg-blue-600 h-2 transition-all duration-300 ease-out"
          style={{
            width:
              stage === 'completed'
                ? '100%'
                : stage === 'uploading'
                ? `${Math.max(10, progressPercent)}%`
                : `${Math.min(95, 20 + currentIdx * 20)}%`,
          }}
        />
      </div>

      {/* Step List */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 pt-2">
        {steps.map((step, idx) => {
          const isDone = idx < currentIdx || stage === 'completed';
          const isCurrent = idx === currentIdx && stage !== 'completed';

          return (
            <div
              key={step.key}
              className={`p-3 rounded-lg border text-xs flex flex-col justify-between space-y-2 transition-all ${
                isDone
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : isCurrent
                  ? 'bg-blue-50 border-blue-300 text-blue-900 shadow-sm'
                  : 'bg-white border-slate-200 text-slate-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold">Step {idx + 1}</span>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
                ) : (
                  <div className="w-3.5 h-3.5 rounded-full border border-slate-300" />
                )}
              </div>
              <p className="font-medium text-[11px] leading-tight">{step.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
