import React, { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { UploadCloud, X, AlertCircle, ArrowRight, Loader2 } from 'lucide-react';
import { uploadResume } from '../../services/resumeService';
import type { StructuredResume } from '../../types/resume';

interface ResumeUploaderProps {
  onUploadSuccess: (resume: StructuredResume) => void;
  onUploadStart?: () => void;
  onProgress?: (percent: number) => void;
}

const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({
  onUploadSuccess,
  onUploadStart,
  onProgress,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState<string>('');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      setErrorMessage(`Unsupported format .${ext}. Only PDF and DOCX files are supported.`);
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      setErrorMessage(
        `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the 10 MB maximum limit.`
      );
      return;
    }

    if (file.size === 0) {
      setErrorMessage('The selected file is empty (0 bytes). Please choose a valid document.');
      return;
    }

    setSelectedFile(file);
    if (!title.trim()) {
      const baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
      setTitle(baseName.replace(/[_-]/g, ' '));
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setTitle('');
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setErrorMessage(null);
    if (onUploadStart) onUploadStart();

    try {
      const result = await uploadResume(selectedFile, title, onProgress);
      onUploadSuccess(result);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        'Upload failed. Please ensure backend server is running.';
      setErrorMessage(detail);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
      <div className="space-y-1">
        <h3 className="text-lg font-bold text-slate-900">
          Upload Candidate Resume
        </h3>
        <p className="text-xs text-slate-500">
          Supported document formats: Standard PDF and Microsoft Word DOCX (Max 10 MB).
        </p>
      </div>

      {/* Drag & Drop Area */}
      {!selectedFile ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center space-y-4 ${
            isDragging
              ? 'border-blue-500 bg-blue-50/50 scale-[0.99]'
              : 'border-slate-300 hover:border-blue-400 bg-slate-50/60 hover:bg-blue-50/20'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="hidden"
          />

          <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 shadow-inner">
            <UploadCloud className="w-7 h-7" />
          </div>

          <div className="space-y-1">
            <p className="text-sm font-semibold text-slate-800">
              Drag & Drop your resume here, or <span className="text-blue-600 underline">browse files</span>
            </p>
            <p className="text-xs text-slate-500">
              Direct text extraction with automatic OCR fallback for scanned PDFs
            </p>
          </div>
        </div>
      ) : (
        /* Selected File Card */
        <div className="space-y-4">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
            <div className="flex items-center space-x-3 truncate">
              <div className="w-10 h-10 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs uppercase shadow-sm">
                {selectedFile.name.split('.').pop()}
              </div>
              <div className="truncate">
                <p className="text-sm font-semibold text-slate-900 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-slate-500">
                  {(selectedFile.size / 1024).toFixed(1)} KB &bull; Ready for ingestion
                </p>
              </div>
            </div>

            <button
              onClick={handleClearFile}
              disabled={isUploading}
              title="Remove file"
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Optional Title Input */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">
              Resume Title / Profile Label
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={isUploading}
              placeholder="e.g. Alex Carter SWE Resume 2026"
              className="w-full text-sm px-3.5 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-slate-900"
            />
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUploadSubmit}
            disabled={isUploading}
            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-semibold rounded-lg shadow-sm transition flex items-center justify-center space-x-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Parsing & Segmenting Document...</span>
              </>
            ) : (
              <>
                <span>Ingest & Parse Resume</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      )}

      {/* Error Callout */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start space-x-3 text-red-800 text-xs">
          <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <span className="font-bold">Upload Error: </span>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}
    </div>
  );
};
