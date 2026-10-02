import React, { useState } from 'react';
import { 
  FileText, 
  Upload, 
  Sparkles, 
  AlertCircle, 
  Loader2, 
  Building2, 
  MapPin, 
  Link as LinkIcon,
  FileCheck
} from 'lucide-react';
import { createJobPasted, uploadJobFile } from '../../services/jobService';
import type { StructuredJob } from '../../types/job';

interface JobUploaderProps {
  onSuccess: (job: StructuredJob) => void;
}

export const JobUploader: React.FC<JobUploaderProps> = ({ onSuccess }) => {
  const [activeMode, setActiveMode] = useState<'paste' | 'file'>('paste');

  // Form states
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [pastedText, setPastedText] = useState('');

  // File states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // Status states
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelected = (file: File) => {
    setErrorMessage(null);
    const validExtensions = ['.pdf', '.docx'];
    const lowerName = file.name.toLowerCase();
    const isValidExt = validExtensions.some((ext) => lowerName.endsWith(ext));

    if (!isValidExt) {
      setErrorMessage('Please upload a PDF (.pdf) or Word document (.docx).');
      setSelectedFile(null);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage('File size exceeds the 10MB limit.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    if (!title) {
      const defaultTitle = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      setTitle(defaultTitle);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (activeMode === 'paste') {
      if (!title.trim()) {
        setErrorMessage('Please provide a job title.');
        return;
      }
      if (!pastedText.trim() || pastedText.trim().length < 30) {
        setErrorMessage('Please provide a meaningful job description (at least 30 characters).');
        return;
      }

      try {
        setIsLoading(true);
        const job = await createJobPasted({
          title: title.trim(),
          raw_text: pastedText.trim(),
          company: company.trim() || undefined,
          location: location.trim() || undefined,
          source_url: sourceUrl.trim() || undefined,
        });
        onSuccess(job);
      } catch (err: any) {
        setErrorMessage(err.response?.data?.detail || 'Failed to process job description.');
      } finally {
        setIsLoading(false);
      }
    } else {
      if (!selectedFile) {
        setErrorMessage('Please select a PDF or DOCX file to upload.');
        return;
      }

      try {
        setIsLoading(true);
        const job = await uploadJobFile(
          selectedFile,
          title.trim() || undefined,
          company.trim() || undefined,
          location.trim() || undefined,
          sourceUrl.trim() || undefined
        );
        onSuccess(job);
      } catch (err: any) {
        setErrorMessage(err.response?.data?.detail || 'Failed to parse and ingest job file.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-3xl shadow-sm p-6 sm:p-8 space-y-6">
      {/* Mode Switcher */}
      <div className="flex border-b border-slate-200 space-x-4 pb-2">
        <button
          type="button"
          onClick={() => setActiveMode('paste')}
          className={`flex items-center space-x-2 pb-2 text-sm font-semibold transition border-b-2 -mb-2.5 ${
            activeMode === 'paste'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Paste Job Description</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveMode('file')}
          className={`flex items-center space-x-2 pb-2 text-sm font-semibold transition border-b-2 -mb-2.5 ${
            activeMode === 'file'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Upload className="w-4 h-4" />
          <span>Upload PDF / DOCX</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Metadata Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Job Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Senior Backend Engineer"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Company (Optional)</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Acme Cloud Systems"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-slate-400" />
              <span>Location (Optional)</span>
            </label>
            <input
              type="text"
              placeholder="e.g. San Francisco / Remote"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1">
              <LinkIcon className="w-3.5 h-3.5 text-slate-400" />
              <span>Posting URL (Optional)</span>
            </label>
            <input
              type="url"
              placeholder="https://company.com/job/123"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
            />
          </div>
        </div>

        {/* Mode 1: Pasted Text */}
        {activeMode === 'paste' && (
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold text-slate-700">
                Job Description Text <span className="text-red-500">*</span>
              </label>
              <span className="text-[11px] font-mono text-slate-400">
                {pastedText.length} characters
              </span>
            </div>
            <textarea
              rows={10}
              placeholder="Paste the complete job description here, including responsibilities, required qualifications, and tech stack..."
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              className="w-full text-xs font-sans px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:bg-white transition leading-relaxed"
            />
          </div>
        )}

        {/* Mode 2: File Upload */}
        {activeMode === 'file' && (
          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-700 block">
              Job Description Document <span className="text-red-500">*</span>
            </label>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              className={`border-2 border-dashed rounded-2xl p-8 text-center transition cursor-pointer ${
                dragOver
                  ? 'border-blue-500 bg-blue-50/50'
                  : selectedFile
                  ? 'border-emerald-400 bg-emerald-50/20'
                  : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
              }`}
              onClick={() => document.getElementById('job-file-input')?.click()}
            >
              <input
                id="job-file-input"
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileSelected(e.target.files[0]);
                  }
                }}
                className="hidden"
              />

              {selectedFile ? (
                <div className="flex flex-col items-center space-y-2">
                  <div className="p-3 bg-emerald-100 text-emerald-700 rounded-2xl">
                    <FileCheck className="w-8 h-8" />
                  </div>
                  <p className="text-sm font-bold text-slate-800">{selectedFile.name}</p>
                  <p className="text-xs text-slate-500 font-mono">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }}
                    className="text-xs text-red-600 hover:underline pt-1"
                  >
                    Change Document
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center space-y-2 text-slate-500">
                  <div className="p-3 bg-white border border-slate-200 rounded-2xl shadow-xs">
                    <Upload className="w-7 h-7 text-blue-600" />
                  </div>
                  <p className="text-sm font-semibold text-slate-800">
                    Drag and drop job document, or <span className="text-blue-600">browse</span>
                  </p>
                  <p className="text-xs text-slate-400">Supported formats: PDF, DOCX (Max 10MB)</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Feedback */}
        {errorMessage && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Action Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-6 py-3 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl transition shadow-sm active:scale-95 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing Job Description...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-blue-200" />
                <span>Analyze Job Description</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
