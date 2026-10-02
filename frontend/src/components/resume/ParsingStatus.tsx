import React from 'react';
import { FileText, Cpu, CheckCircle, FileCheck, Layers } from 'lucide-react';

interface ParsingStatusProps {
  status: string;
  method: 'TEXT' | 'OCR';
  pageCount: number;
  characterCount: number;
  sectionsCount: number;
}

export const ParsingStatus: React.FC<ParsingStatusProps> = ({
  status,
  method,
  pageCount,
  characterCount,
  sectionsCount,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-2.5 text-xs">
      {/* Parsing Status Badge */}
      <span
        className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full font-semibold border ${
          status === 'COMPLETED'
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
            : status === 'FAILED'
            ? 'bg-red-50 text-red-700 border-red-200'
            : 'bg-amber-50 text-amber-700 border-amber-200'
        }`}
      >
        <CheckCircle className="w-3.5 h-3.5" />
        <span>Status: {status}</span>
      </span>

      {/* Extraction Method Badge */}
      <span
        className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full font-semibold border ${
          method === 'OCR'
            ? 'bg-purple-50 text-purple-700 border-purple-200'
            : 'bg-blue-50 text-blue-700 border-blue-200'
        }`}
      >
        <Cpu className="w-3.5 h-3.5" />
        <span>Extraction: {method === 'OCR' ? 'Tesseract OCR Fallback' : 'Direct Text (PyMuPDF / docx)'}</span>
      </span>

      {/* Pages Metric */}
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-medium">
        <FileText className="w-3.5 h-3.5 text-slate-500" />
        <span>{pageCount} {pageCount === 1 ? 'Page' : 'Pages'}</span>
      </span>

      {/* Characters Metric */}
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-medium">
        <FileCheck className="w-3.5 h-3.5 text-slate-500" />
        <span>{characterCount.toLocaleString()} Characters</span>
      </span>

      {/* Sections Metric */}
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-medium">
        <Layers className="w-3.5 h-3.5 text-slate-500" />
        <span>{sectionsCount} Sections Detected</span>
      </span>
    </div>
  );
};
